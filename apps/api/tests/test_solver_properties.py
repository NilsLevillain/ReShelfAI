"""TS-206: result invariants on every solve, over many small random worlds."""

from __future__ import annotations

from collections import defaultdict

import factory as f
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from reshelf.constraints import Solution, violations
from reshelf.schema import Abc
from reshelf.solver import PulpSolver
from reshelf.solver_input import SolverInput, build_solver_input

TIERS = ["luxury", "premium", "mass"]


@st.composite
def worlds(draw: st.DrawFn) -> SolverInput:
    n_materials = draw(st.integers(1, 4))
    n_channels = draw(st.integers(1, 3))
    codes = [f"M{i}" for i in range(n_materials)]
    materials = [
        f.material(
            code,
            category=draw(st.sampled_from(["Haircare", "Fragrance"])),
            brand=draw(st.sampled_from(["Brightleaf", "Northfield"])),
            tier=draw(st.sampled_from(TIERS)),
        )
        for code in codes
    ]
    lots = [
        f.lot(
            code,
            qty=draw(st.integers(1, 300)),
            unit_cost=draw(st.floats(0, 50)),
            expiry_in_days=draw(st.integers(200, 800)),
        )
        for code in codes
    ]
    channels = [
        f.channel(
            f"C{j}",
            capacity=draw(st.integers(0, 500)),
            max_skus=draw(st.integers(0, 4)),
            allowed=frozenset(draw(st.lists(st.sampled_from(TIERS), min_size=1, unique=True))),
            recovery=draw(st.floats(0, 1)),
            penalty={t: draw(st.floats(0, 20)) for t in TIERS},
        )
        for j in range(n_channels)
    ]
    demands = [
        f.demand(
            code,
            ch.channel,
            daily=draw(st.floats(0, 4)),
            stock=draw(st.integers(0, 50)),
            history=draw(st.booleans()),
        )
        for code in codes
        for ch, _ in channels
    ]
    abc = [
        Abc(material=code, abc_class=draw(st.sampled_from(["A", "B", "C"])), rank=i + 1)
        for i, code in enumerate(codes)
    ]
    alpha = draw(st.sampled_from([0.0, 0.3, 1.0]))
    return build_solver_input(
        f.dataset(
            materials=materials,
            lots=lots,
            channels=channels,
            demands=demands,
            abc=abc,
            parameters=f.params(coverage_alpha=alpha),
        )
    )


@settings(max_examples=40, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(worlds())
def test_result_invariants(data: SolverInput) -> None:
    result = PulpSolver().solve(data)
    assert result.status == "optimal"

    assert all(q > 0 for q in result.x.values())  # no negative or empty line
    per_lot: dict[tuple[str, str, str], int] = defaultdict(int)
    for (lot, _), qty in result.x.items():
        per_lot[lot] += qty
    assert all(per_lot[lot] <= data.lots[lot].qty for lot in per_lot)  # no line above supply

    supply = sum(lot.qty for lot in data.lots.values())
    assert result.units_allocated == sum(result.x.values())
    assert result.units_allocated + result.units_destroyed == supply  # totals reconcile
    assert result.objective == sum(data.net_value[p] * q for p, q in result.x.items())

    assert set(result.x) <= set(data.admissible)  # nothing on an eliminated pair
    assert violations(data, Solution(x=result.x, y=result.y, z=result.z)) == []
    assert result.score >= (1 - data.params.epsilon) * result.best_score - 1e-6
