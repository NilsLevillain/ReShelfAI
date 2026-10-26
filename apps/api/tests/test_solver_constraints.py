"""Solver side of TS-030 to TS-039 and TS-041: each rule binds in the optimum and holds.

The checker audits every plan, so a rule the model dropped would show up as a violation.
"""

from __future__ import annotations

import factory as f
import pytest

from reshelf.constraints import Solution, violations
from reshelf.schema import GroupLimit
from reshelf.solver import PulpSolver, SolveResult
from reshelf.solver_input import SolverInput


def solve(data: SolverInput) -> SolveResult:
    result = PulpSolver().solve(data)
    assert result.status == "optimal"
    assert violations(data, Solution(x=result.x, y=result.y, z=result.z)) == []
    return result


def units(result: SolveResult, material: str | None = None, channel: str | None = None) -> int:
    return sum(
        q
        for ((m, _, _), c), q in result.x.items()
        if (material is None or m == material) and (channel is None or c == channel)
    )


def many(n: int, **kwargs: object) -> dict[str, object]:
    codes = [f"M{i}" for i in range(n)]
    return {
        "materials": [f.material(c) for c in codes],
        "lots": [f.lot(c) for c in codes],
        **kwargs,
    }


def test_supply_caps_a_lot_across_channels() -> None:  # TS-030
    data = f.solver_input(
        channels=[f.channel("C1"), f.channel("C2")],
        demands=[f.demand("M1", "C1", daily=5), f.demand("M1", "C2", daily=5)],
    )
    assert units(solve(data)) == 100  # demand is 450 per channel, the lot holds 100


def test_x_needs_y_and_y_needs_z() -> None:  # TS-031, TS-032, TS-033
    result = solve(f.solver_input())
    assert result.x
    for pair, qty in result.x.items():
        assert qty > 0 and result.y[pair]
        assert result.z[(pair[0][0], pair[1])]
    selected = {mc for mc, on in result.z.items() if on}
    assert selected == {(pair[0][0], pair[1]) for pair in result.x}  # z backed by a used lot


def test_capacity_binds() -> None:  # TS-034
    data = f.solver_input(
        channels=[f.channel("C1", capacity=60)], parameters=f.params(coverage_alpha=0.2)
    )
    assert units(solve(data)) == 60


def test_sku_limit_binds() -> None:  # TS-035
    data = f.solver_input(**many(3), channels=[f.channel("C1", max_skus=2)])
    result = solve(data)
    assert sum(result.z.values()) == 2


def test_assortment_sku_limit_binds() -> None:  # TS-036
    data = f.solver_input(
        **many(3),
        group_limits=[
            GroupLimit(
                channel="C1", brand="Brightleaf", category="Haircare", max_skus=1, max_units=10_000
            )
        ],
    )
    assert sum(solve(data).z.values()) == 1


def test_assortment_unit_limit_binds() -> None:
    data = f.solver_input(
        **many(2),
        group_limits=[
            GroupLimit(
                channel="C1", brand="Brightleaf", category="Haircare", max_skus=5, max_units=120
            )
        ],
        parameters=f.params(coverage_alpha=0.2),
    )
    assert units(solve(data)) == 120


def test_coverage_upper_bound_binds() -> None:  # TS-037
    data = f.solver_input(demands=[f.demand("M1", "C1", daily=0.5)])  # need 45, lot holds 100
    assert units(solve(data)) == data.upper[("M1", "C1")] == 45


def test_coverage_lower_bound_holds_or_the_sku_is_skipped() -> None:  # TS-038
    # Lower bound is 50 but the channel holds 40: the SKU cannot be selected at all.
    data = f.solver_input(channels=[f.channel("C1", capacity=40)])
    assert data.lower[("M1", "C1")] == 50
    result = solve(data)
    assert result.x == {} and not any(result.z.values())


def test_push_quantity_binds_for_a_new_sku() -> None:  # TS-039
    data = f.solver_input(
        materials=[f.material("M1", category="Fragrance")],
        demands=[f.demand("M1", "C1", history=False)],
    )
    assert data.classes[("M1", "C1")] == "NEW"
    assert units(solve(data)) == 5  # push quantity of Fragrance, lower and upper bound both 5


def test_coverage_rows_are_off_when_the_sku_is_not_selected() -> None:  # TS-041
    # One slot for two SKUs: the unselected one gets nothing, and nothing is demanded of it.
    data = f.solver_input(**many(2), channels=[f.channel("C1", max_skus=1)])
    result = solve(data)
    assert sorted(units(result, m) for m in ("M0", "M1")) == [0, 100]


@pytest.mark.parametrize("alpha", [0.0, 0.5, 1.0])
def test_alpha_changes_the_lower_bound(alpha: float) -> None:
    data = f.solver_input(parameters=f.params(coverage_alpha=alpha))
    assert units(solve(data)) >= data.lower[("M1", "C1")]
