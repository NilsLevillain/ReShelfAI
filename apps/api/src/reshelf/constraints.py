"""Named constraint registry and the full constraint checker.

The registry is the single list of constraint names. The solver builds its model from it, the
checker audits any allocation against it, the rule trace reads the slack of each instance, and
`docs/model.md` is generated from it. Keep names stable and meaningful.

Variables: x[l,c] units of lot l sent to channel c, y[l,c] lot l used in channel c,
z[m,c] material m selected in channel c.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from typing import Literal

from reshelf.elimination import Reason
from reshelf.ids import MatChan, Pair, lot_label, mc_label, pair_label
from reshelf.schema import PlannerRule
from reshelf.solver_input import SolverInput

Sense = Literal["<=", ">="]
TOLERANCE = 1e-9


@dataclass(frozen=True)
class ConstraintSpec:
    name: str
    index: str
    formula: str
    sense: Sense
    description: str
    planner_rule: PlannerRule | None = None
    reads: str = ""  # source tables and parameters the bounds come from, for docs/model.md

    @property
    def label(self) -> str:
        return f"{self.name}[{self.index}]"


CONSTRAINTS: tuple[ConstraintSpec, ...] = (
    ConstraintSpec(
        "supply",
        "l",
        "sum_c x[l,c] <= q[l]",
        "<=",
        "A lot cannot ship more than it holds",
        reads="MCHB.CLABS",
    ),
    ConstraintSpec(
        "link_xy",
        "l,c",
        "x[l,c] <= q[l] * y[l,c]",
        "<=",
        "Units only flow on a used lot and channel pair",
    ),
    ConstraintSpec(
        "link_yx", "l,c", "y[l,c] <= x[l,c]", "<=", "A used pair carries at least one unit"
    ),
    ConstraintSpec(
        "link_yz",
        "l,c",
        "y[l,c] <= z[m(l),c]",
        "<=",
        "A used lot needs its SKU selected in the channel",
    ),
    ConstraintSpec(
        "link_zy",
        "m,c",
        "z[m,c] <= sum_{l in L(m)} y[l,c]",
        "<=",
        "A selected SKU uses at least one lot",
    ),
    ConstraintSpec(
        "cap",
        "c",
        "sum_l x[l,c] <= K[c]",
        "<=",
        "Channel capacity in units",
        "capacity",
        reads="ZCHANNEL.CAPUNITS",
    ),
    ConstraintSpec(
        "sku",
        "c",
        "sum_m z[m,c] <= S[c]",
        "<=",
        "Channel limit on distinct SKUs",
        reads="ZCHANNEL.MAXSKU",
    ),
    ConstraintSpec(
        "asrt",
        "g,c",
        "sum_{m in g} z[m,c] <= A[g,c]",
        "<=",
        "Assortment limit: SKUs of a brand and category in a channel",
        reads="ZCHANNEL_ASRT.MAXSKU",
    ),
    ConstraintSpec(
        "cov_hi",
        "m,c",
        "sum_{l in L(m)} x[l,c] <= U[m,c] * z[m,c]",
        "<=",
        "Do not exceed the coverage need (push quantity for NEW)",
        reads="ZPARAM.COVERAGE_DAYS, ZSELLOUT, ZCHSTOCK, ZPARAM.PUSH_QUANTITY_UNITS_*",
    ),
    ConstraintSpec(
        "cov_lo",
        "m,c",
        "sum_{l in L(m)} x[l,c] >= B[m,c] * z[m,c]",
        ">=",
        "A selected SKU covers at least alpha of its need",
        reads="ZPARAM.COVERAGE_ALPHA, ZPARAM.COVERAGE_DAYS",
    ),
    ConstraintSpec(
        "push",
        "m,c",
        "sum_{l in L(m)} x[l,c] >= B[m,c] * z[m,c]",
        ">=",
        "A selected NEW SKU gets its push quantity",
        reads="ZPARAM.PUSH_QUANTITY_UNITS_*",
    ),
    ConstraintSpec(
        "asrt_units",
        "g,c",
        "sum_{l: m(l) in g} x[l,c] <= V[g,c]",
        "<=",
        "Assortment limit: units of a brand and category in a channel",
        reads="ZCHANNEL_ASRT.MAXUNITS",
    ),
)

SPECS: dict[str, ConstraintSpec] = {c.name: c for c in CONSTRAINTS}
CONSTRAINT_LABELS: tuple[str, ...] = tuple(c.label for c in CONSTRAINTS)

# Elimination reason code to the planner rule that applies it by hand. None: the planner ignores it.
REASON_RULE: dict[Reason, PlannerRule | None] = {"RSL": "rsl", "TIER": "tier", "NO_PUSH": None}


@dataclass(frozen=True)
class Solution:
    """An allocation. y and z are derived from x when not given: used means x > 0."""

    x: Mapping[Pair, int]
    y: Mapping[Pair, bool] | None = None
    z: Mapping[MatChan, bool] | None = None


@dataclass(frozen=True)
class ConstraintResult:
    constraint: str  # registry name, or an elimination reason code such as RSL
    instance: str  # for example cap[OUT_PL]
    lhs: float
    rhs: float
    sense: Sense
    planner_rule: PlannerRule | None

    @property
    def slack(self) -> float:
        return self.rhs - self.lhs if self.sense == "<=" else self.lhs - self.rhs

    @property
    def violated(self) -> bool:
        return self.slack < -TOLERANCE


def evaluate(
    data: SolverInput, solution: Solution, only: Iterable[str] | None = None
) -> list[ConstraintResult]:
    """lhs, rhs and slack of every instance of every named constraint (or of those in `only`).

    A unit sent on an eliminated pair is reported as a breach with its reason code.
    """
    return list(_evaluate(data, solution, None if only is None else frozenset(only)))


def violations(
    data: SolverInput,
    solution: Solution,
    rules: Iterable[PlannerRule] | None = None,
) -> list[ConstraintResult]:
    """Violated instances. With `rules`, only those a planner applying these rules would catch."""
    keep = None if rules is None else frozenset(rules)
    return [
        r
        for r in _evaluate(data, solution, None)
        if r.violated and (keep is None or r.planner_rule in keep)
    ]


def violation_counts(results: Iterable[ConstraintResult]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for r in results:
        if r.violated:
            counts[r.constraint] += 1
    return dict(sorted(counts.items()))


def _evaluate(
    data: SolverInput, solution: Solution, only: frozenset[str] | None
) -> Iterator[ConstraintResult]:
    x: dict[Pair, int] = defaultdict(int)
    for pair, qty in solution.x.items():
        x[pair] += qty

    lot_out: dict[tuple[str, str, str], int] = defaultdict(int)
    channel_out: dict[str, int] = defaultdict(int)
    group_units: dict[tuple[str, tuple[str, str]], int] = defaultdict(int)
    mc_units: dict[MatChan, int] = defaultdict(int)
    for (lot_key, channel), qty in x.items():
        lot_out[lot_key] += qty
        channel_out[channel] += qty
        group_units[(channel, data.group_of[lot_key[0]])] += qty
        mc_units[(lot_key[0], channel)] += qty

    admissible = data.admissible
    y: Mapping[Pair, bool] = (
        solution.y if solution.y is not None else {p: x.get(p, 0) > 0 for p in admissible}
    )
    z: Mapping[MatChan, bool] = (
        solution.z
        if solution.z is not None
        else {
            mc: any(y.get((lot, mc[1]), False) for lot in lots) for mc, lots in data.lots_of.items()
        }
    )

    def wanted(name: str) -> bool:
        return only is None or name in only

    def result(name: str, instance: str, lhs: float, rhs: float) -> ConstraintResult:
        spec = SPECS[name]
        return ConstraintResult(
            name, f"{name}[{instance}]", lhs, rhs, spec.sense, spec.planner_rule
        )

    if wanted("supply"):
        for lot_key, lot in data.lots.items():
            yield result("supply", lot_label(lot_key), lot_out.get(lot_key, 0), lot.qty)

    for pair in admissible:
        lot = data.lots[pair[0]]
        mc = (pair[0][0], pair[1])
        used = 1 if y.get(pair, False) else 0
        label = pair_label(pair)
        if wanted("link_xy"):
            yield result("link_xy", label, x.get(pair, 0), lot.qty * used)
        if wanted("link_yx"):
            yield result("link_yx", label, used, x.get(pair, 0))
        if wanted("link_yz"):
            yield result("link_yz", label, used, 1 if z.get(mc, False) else 0)

    if wanted("link_zy"):
        for mc, lots in data.lots_of.items():
            yield result(
                "link_zy",
                mc_label(mc),
                1 if z.get(mc, False) else 0,
                sum(1 for lot in lots if y.get((lot, mc[1]), False)),
            )

    for channel_id, spec_channel in data.channels.items():
        if wanted("cap"):
            yield result(
                "cap", channel_id, channel_out.get(channel_id, 0), spec_channel.capacity_units
            )
        if wanted("sku"):
            selected = sum(1 for mc, on in z.items() if on and mc[1] == channel_id)
            yield result("sku", channel_id, selected, spec_channel.max_skus)

    for (channel_id, group), limit in data.group_limits.items():
        label = f"{group[0]}/{group[1]},{channel_id}"
        if wanted("asrt"):
            selected = sum(
                1
                for mc, on in z.items()
                if on and mc[1] == channel_id and data.group_of[mc[0]] == group
            )
            yield result("asrt", label, selected, limit.max_skus)
        if wanted("asrt_units"):
            yield result(
                "asrt_units", label, group_units.get((channel_id, group), 0), limit.max_units
            )

    for mc in data.lots_of:
        on = 1 if z.get(mc, False) else 0
        units = mc_units.get(mc, 0)
        if wanted("cov_hi"):
            yield result("cov_hi", mc_label(mc), units, data.upper[mc] * on)
        lower_name = "push" if data.classes[mc] == "NEW" else "cov_lo"
        if wanted(lower_name):
            yield result(lower_name, mc_label(mc), units, data.lower[mc] * on)

    # Units on a pair that elimination removed. Reported with the reason code (ADR 003).
    for pair, qty in x.items():
        if qty > 0 and pair in data.dropped:
            for reason in data.dropped[pair]:
                yield ConstraintResult(
                    constraint=reason,
                    instance=f"{reason}[{pair_label(pair)}]",
                    lhs=qty,
                    rhs=0,
                    sense="<=",
                    planner_rule=REASON_RULE[reason],
                )
