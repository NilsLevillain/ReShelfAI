"""MILP model built from the constraint registry.

One builder per registry name, so a constraint cannot exist in the registry and be missing from the
model (a test compares both). Rows are kept by their registry label, for example `cap[OUT_PL]`, the
same label `constraints.evaluate` reports, so the rule trace can read the slack of a solved row.

x[l,c] units, y[l,c] used pair, z[m,c] selected SKU, over the admissible pairs only.
Coverage and push use the tight form: the binary multiplies the bound directly (ADR 004).
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field

import pulp

from reshelf.constraints import CONSTRAINTS, SPECS
from reshelf.ids import MatChan, Pair, lot_label, mc_label, pair_label
from reshelf.solver_input import SolverInput


@dataclass
class Model:
    data: SolverInput
    problem: pulp.LpProblem
    x: dict[Pair, pulp.LpVariable]
    y: dict[Pair, pulp.LpVariable]
    z: dict[MatChan, pulp.LpVariable]
    rows: dict[str, pulp.LpConstraint] = field(default_factory=dict)

    def score_expr(self) -> pulp.LpAffineExpression:
        return pulp.lpSum(self.data.score[mc] * var for mc, var in self.z.items())

    def value_expr(self) -> pulp.LpAffineExpression:
        return pulp.lpSum(self.data.net_value[p] * var for p, var in self.x.items())

    def add(self, name: str, instance: str, constraint: pulp.LpConstraint) -> None:
        label = f"{name}[{instance}]"
        self.rows[label] = constraint
        # PuLP rewrites some characters in names, so the registry label is only a key here.
        self.problem += constraint, f"{name}_{len(self.rows)}"


Builder = Callable[[Model], None]


def _supply(m: Model) -> None:
    by_lot: dict[tuple[str, str, str], list[pulp.LpVariable]] = defaultdict(list)
    for (lot, _), var in m.x.items():
        by_lot[lot].append(var)
    for lot, xs in by_lot.items():
        m.add("supply", lot_label(lot), pulp.lpSum(xs) <= m.data.lots[lot].qty)


def _link_xy(m: Model) -> None:
    for pair, var in m.x.items():
        m.add("link_xy", pair_label(pair), var <= m.data.lots[pair[0]].qty * m.y[pair])


def _link_yx(m: Model) -> None:
    for pair, var in m.y.items():
        m.add("link_yx", pair_label(pair), var <= m.x[pair])


def _link_yz(m: Model) -> None:
    for pair, var in m.y.items():
        m.add("link_yz", pair_label(pair), var <= m.z[(pair[0][0], pair[1])])


def _link_zy(m: Model) -> None:
    for mc, lots in m.data.lots_of.items():
        m.add("link_zy", mc_label(mc), m.z[mc] <= pulp.lpSum(m.y[(lot, mc[1])] for lot in lots))


def _cap(m: Model) -> None:
    for channel_id, channel in m.data.channels.items():
        xs = [var for (_, c), var in m.x.items() if c == channel_id]
        if xs:
            m.add("cap", channel_id, pulp.lpSum(xs) <= channel.capacity_units)


def _sku(m: Model) -> None:
    for channel_id, channel in m.data.channels.items():
        zs = [var for (_, c), var in m.z.items() if c == channel_id]
        if zs:
            m.add("sku", channel_id, pulp.lpSum(zs) <= channel.max_skus)


def _asrt(m: Model) -> None:
    for (channel_id, group), limit in m.data.group_limits.items():
        zs = [
            var
            for (material, c), var in m.z.items()
            if c == channel_id and m.data.group_of[material] == group
        ]
        if zs:
            m.add("asrt", f"{group[0]}/{group[1]},{channel_id}", pulp.lpSum(zs) <= limit.max_skus)


def _asrt_units(m: Model) -> None:
    for (channel_id, group), limit in m.data.group_limits.items():
        xs = [
            var
            for ((material, _, _), c), var in m.x.items()
            if c == channel_id and m.data.group_of[material] == group
        ]
        if xs:
            m.add(
                "asrt_units",
                f"{group[0]}/{group[1]},{channel_id}",
                pulp.lpSum(xs) <= limit.max_units,
            )


def _units(m: Model, mc: MatChan) -> pulp.LpAffineExpression:
    return pulp.lpSum(m.x[(lot, mc[1])] for lot in m.data.lots_of[mc])


def _cov_hi(m: Model) -> None:
    for mc in m.data.lots_of:
        m.add("cov_hi", mc_label(mc), _units(m, mc) <= m.data.upper[mc] * m.z[mc])


def _lower(name: str, is_new: bool) -> Builder:
    def build(m: Model) -> None:
        for mc in m.data.lots_of:
            if (m.data.classes[mc] == "NEW") == is_new:
                m.add(name, mc_label(mc), _units(m, mc) >= m.data.lower[mc] * m.z[mc])

    return build


BUILDERS: dict[str, Builder] = {
    "supply": _supply,
    "link_xy": _link_xy,
    "link_yx": _link_yx,
    "link_yz": _link_yz,
    "link_zy": _link_zy,
    "cap": _cap,
    "sku": _sku,
    "asrt": _asrt,
    "cov_hi": _cov_hi,
    "cov_lo": _lower("cov_lo", is_new=False),
    "push": _lower("push", is_new=True),
    "asrt_units": _asrt_units,
}


def build_model(data: SolverInput) -> Model:
    """Variables and every registry constraint. The objective is set by the solver, per phase."""
    problem = pulp.LpProblem("reshelf", pulp.LpMaximize)
    x = {
        pair: pulp.LpVariable(f"x_{i}", 0, data.lots[pair[0]].qty, "Integer")
        for i, pair in enumerate(data.admissible)
    }
    y = {pair: pulp.LpVariable(f"y_{i}", 0, 1, "Binary") for i, pair in enumerate(data.admissible)}
    z = {mc: pulp.LpVariable(f"z_{i}", 0, 1, "Binary") for i, mc in enumerate(data.lots_of)}
    model = Model(data, problem, x, y, z)
    for spec in CONSTRAINTS:
        BUILDERS[spec.name](model)
    return model


assert set(BUILDERS) == set(SPECS), "every registry constraint needs a builder"
