"""Counterfactual: relax one binding rule, re solve from the plan, report the cost."""

from __future__ import annotations

from dataclasses import replace

import factory as f
import pytest

from reshelf.constraints import Solution, violations
from reshelf.counterfactual import (
    RELAXABLE_RULES,
    counterfactual,
    rank_binding_rules,
    relax,
    top_counterfactuals,
)
from reshelf.schema import GroupLimit
from reshelf.solver import PulpSolver, SolveResult
from reshelf.solver_input import SolverInput
from reshelf.trace import build_trace

SOLVER = PulpSolver()


def solve(data: SolverInput) -> SolveResult:
    result = SOLVER.solve(data)
    assert result.status == "optimal"
    return result


def mc(data: SolverInput, material: str, channel: str = "C1") -> tuple[str, str]:
    assert (material, channel) in data.lots_of
    return (material, channel)


# One SKU, 100 units at 10 euro, recovery 0.5, so 5 euro a unit. Need is 180 a channel.
def capped(capacity: int = 50) -> SolverInput:
    return f.solver_input(channels=[f.channel("C1", capacity=capacity)])


def test_cap_plus_10_percent_gains_five_units() -> None:
    data = capped(50)
    base = solve(data)
    assert base.units_destroyed == 50
    out = counterfactual(data, base, "cap[C1]", "plus_10pct")
    assert out.status == "optimal"
    assert out.cost_eur == pytest.approx(25.0)  # 5 more units at 5 euro
    assert out.units_destroyed_by_rule == 5
    assert out.base_objective == pytest.approx(250.0)
    assert out.relaxed_objective == pytest.approx(275.0)


def test_cap_off_frees_the_whole_lot() -> None:
    data = capped(50)
    out = counterfactual(data, solve(data), "cap[C1]", "off")
    assert out.cost_eur == pytest.approx(250.0)
    assert out.units_destroyed_by_rule == 50
    assert out.relaxed_destroyed == 0


def test_cov_hi_relaxation_raises_the_need() -> None:
    # 1 unit a day over 90 days: need 90, supply 100
    data = f.solver_input(demands=[f.demand("M1", "C1", daily=1.0)])
    base = solve(data)
    assert base.units_allocated == 90
    plus = counterfactual(data, base, "cov_hi[M1,C1]", "plus_10pct")
    assert plus.units_destroyed_by_rule == 9  # need 99
    off = counterfactual(data, base, "cov_hi[M1,C1]", "off")
    assert off.units_destroyed_by_rule == 10  # ceiling is the supply
    assert off.cost_eur == pytest.approx(50.0)


def test_sku_limit_relaxation_admits_another_sku() -> None:
    data = f.solver_input(
        materials=[f.material("M1"), f.material("M2")],
        lots=[f.lot("M1", qty=30), f.lot("M2", qty=30)],
        channels=[f.channel("C1", max_skus=1)],
    )
    base = solve(data)
    assert base.units_allocated == 30
    out = counterfactual(data, base, "sku[C1]", "plus_10pct")
    assert out.cost_eur == pytest.approx(150.0)  # a second SKU of 30 units at 5 euro
    assert out.units_destroyed_by_rule == 30


def _group_data() -> SolverInput:
    return f.solver_input(
        materials=[f.material("M1"), f.material("M2")],
        lots=[f.lot("M1"), f.lot("M2")],
        group_limits=[
            GroupLimit(
                channel="C1", brand="Brightleaf", category="Haircare", max_skus=2, max_units=100
            )
        ],
    )


def test_asrt_units_relaxation_raises_the_group_unit_limit() -> None:
    data = _group_data()
    base = solve(data)
    assert base.units_allocated == 100
    out = counterfactual(data, base, "asrt_units[Brightleaf/Haircare,C1]", "plus_10pct")
    assert out.units_destroyed_by_rule == 10
    assert out.cost_eur == pytest.approx(50.0)


def test_asrt_relaxation_changes_the_group_sku_limit() -> None:
    data = _group_data()
    relaxed = relax(data, "asrt[Brightleaf/Haircare,C1]", "plus_10pct")
    ((_, limit),) = relaxed.group_limits.items()
    assert limit.max_skus == 3
    ((_, original),) = data.group_limits.items()
    assert original.max_skus == 2  # the input is not mutated


def test_lower_bound_relaxation_lowers_the_bound() -> None:
    # need 180, supply 100, alpha 0.5: lower bound 50
    data = f.solver_input()
    key = mc(data, "M1")
    assert relax(data, "cov_lo[M1,C1]", "plus_10pct").lower[key] == 45
    assert relax(data, "cov_lo[M1,C1]", "off").lower[key] == 0


def test_push_relaxation_lowers_the_push_bound() -> None:
    data = f.solver_input(demands=[f.demand("M1", "C1", history=False)])
    key = mc(data, "M1")
    assert data.lower[key] == 50
    assert relax(data, "push[M1,C1]", "plus_10pct").lower[key] == 45
    assert relax(data, "push[M1,C1]", "off").lower[key] == 0


def test_relaxing_a_zero_bound_changes_nothing() -> None:
    data = capped(0)
    out = relax(data, "cap[C1]", "plus_10pct")
    assert out.channels["C1"].capacity_units == 0


def test_relaxation_never_loses_value_and_stays_feasible() -> None:
    data = capped(50)
    base = solve(data)
    for name, instance in [("cap", "cap[C1]"), ("cov_hi", "cov_hi[M1,C1]")]:
        assert name in RELAXABLE_RULES
        for mode in ("plus_10pct", "off"):
            out = counterfactual(data, base, instance, mode)
            assert out.cost_eur >= 0
            relaxed_data = relax(data, instance, mode)
            assert violations(relaxed_data, Solution(x=out.plan.x)) == []
            # the original plan is feasible in the relaxed model
            assert violations(relaxed_data, Solution(x=base.x)) == []


def test_supply_and_link_rules_cannot_be_relaxed() -> None:
    data = capped(50)
    for instance in ("supply[M1/P1/2028-05]", "link_xy[M1/P1/2028-05,C1]"):
        with pytest.raises(ValueError, match="cannot be relaxed"):
            relax(data, instance, "off")


def test_unknown_instances_and_modes_are_rejected() -> None:
    data = capped(50)
    with pytest.raises(ValueError, match="unknown channel"):
        relax(data, "cap[NOPE]", "off")
    with pytest.raises(ValueError, match="unknown SKU"):
        relax(data, "cov_hi[M9,C1]", "off")
    with pytest.raises(ValueError, match="not a rule instance"):
        relax(data, "cap", "off")
    with pytest.raises(ValueError, match="unknown relaxation"):
        relax(data, "cap[C1]", "half")  # type: ignore[arg-type]


def test_a_missing_original_plan_is_refused() -> None:
    data = capped(50)
    broken = replace(solve(data), status="error", x={})
    with pytest.raises(ValueError, match="needs the original solve to have a plan"):
        counterfactual(data, broken, "cap[C1]", "off")


class _WorseSolver(PulpSolver):
    """Stands in for a re solve that hit its limit under the original plan."""

    def improve(
        self, data: SolverInput, start: SolveResult, time_limit_s: float | None = None
    ) -> SolveResult:
        return replace(start, status="feasible", objective=start.objective - 100)


def test_a_re_solve_under_the_original_plan_keeps_the_original() -> None:
    data = capped(50)
    base = solve(data)
    out = counterfactual(data, base, "cap[C1]", "off", solver=_WorseSolver())
    assert out.cost_eur == 0.0
    assert out.units_destroyed_by_rule == 0
    assert out.status == "feasible"
    assert "did not beat the original plan" in out.message
    assert out.plan is base


class _NoPlanSolver(PulpSolver):
    def improve(
        self, data: SolverInput, start: SolveResult, time_limit_s: float | None = None
    ) -> SolveResult:
        return replace(start, status="time_limit", x={}, y={}, z={}, message="out of time")


def test_a_re_solve_without_a_plan_reports_the_status_and_message() -> None:
    data = capped(50)
    out = counterfactual(data, solve(data), "cap[C1]", "off", solver=_NoPlanSolver())
    assert out.status == "time_limit"
    assert out.message == "out of time"
    assert out.cost_eur == 0.0


def test_result_carries_the_solver_figures() -> None:
    data = capped(50)
    out = counterfactual(data, solve(data), "cap[C1]", "off", time_limit_s=7)
    assert out.time_limit_s == 7
    assert out.time_s >= 0
    assert out.mip_gap is None or out.mip_gap >= 0


def test_counterfactual_is_deterministic() -> None:
    data = capped(50)
    base = solve(data)
    first = counterfactual(data, base, "cap[C1]", "plus_10pct")
    second = counterfactual(data, base, "cap[C1]", "plus_10pct")
    assert (first.cost_eur, first.plan.x) == (second.cost_eur, second.plan.x)


def test_ranking_orders_by_lines_then_name_and_skips_supply() -> None:
    data = f.solver_input(
        materials=[f.material("M1"), f.material("M2")],
        lots=[f.lot("M1", qty=30), f.lot("M2", qty=30)],
        channels=[f.channel("C1", capacity=40)],
    )
    base = solve(data)
    trace = build_trace(data, Solution(x=base.x))
    ranked = rank_binding_rules(trace)
    assert ranked, "the capacity of 40 binds"
    assert ranked[0][0] == "cap[C1]"
    assert all(not name.startswith("supply") for name, _ in ranked)
    counts = [n for _, n in ranked]
    assert counts == sorted(counts, reverse=True)


def test_top_counterfactuals_runs_each_mode_for_the_top_rules() -> None:
    data = capped(50)
    base = solve(data)
    trace = build_trace(data, Solution(x=base.x))
    results = top_counterfactuals(data, base, trace, n=1)
    assert [(r.instance, r.mode) for r in results] == [
        ("cap[C1]", "plus_10pct"),
        ("cap[C1]", "off"),
    ]
    assert results[1].cost_eur >= results[0].cost_eur
