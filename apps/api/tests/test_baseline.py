"""Greedy baseline: planner proxy, audit and repair. TS-060 to TS-064 and TS-069."""

from __future__ import annotations

import factory as f
import pytest

from reshelf.baseline import AuditLine, baseline_planner, repair
from reshelf.constraints import Solution, violations
from reshelf.schema import GroupLimit
from reshelf.solver_input import SolverInput


def assortment_world(costs: dict[str, float], max_skus: int = 1) -> SolverInput:
    codes = sorted(costs)
    return f.solver_input(
        materials=[f.material(code) for code in codes],
        lots=[f.lot(code, unit_cost=costs[code]) for code in codes],
        group_limits=[
            GroupLimit(
                channel="C1",
                brand="Brightleaf",
                category="Haircare",
                max_skus=max_skus,
                max_units=10_000,
            )
        ],
    )


def test_baseline_orders_by_value_at_risk_and_fills_capacity() -> None:
    data = f.solver_input(
        materials=[f.material("M1"), f.material("M2")],
        lots=[f.lot("M1", unit_cost=10.0), f.lot("M2", unit_cost=100.0)],
        channels=[f.channel("C1", capacity=100, recovery=0.6), f.channel("C2", recovery=0.4)],
    )
    m1, m2 = sorted(data.lots)
    plan = baseline_planner(data).raw_x
    assert plan == {(m2, "C1"): 100, (m1, "C2"): 100}


def test_lot_splits_over_channels_when_capacity_runs_out() -> None:
    data = f.solver_input(
        channels=[f.channel("C1", capacity=30, recovery=0.6), f.channel("C2", recovery=0.4)],
    )
    (lot_key,) = data.lots
    assert baseline_planner(data).raw_x == {(lot_key, "C1"): 30, (lot_key, "C2"): 70}


def test_baseline_ignores_assortment_and_the_audit_finds_it() -> None:
    data = assortment_world({"M1": 10.0, "M2": 20.0, "M3": 30.0})
    result = baseline_planner(data)
    assert result.raw.skus_per_channel["C1"] == 3
    assert result.audit["asrt"] == AuditLine(count=1, excess=2)


def test_baseline_applies_only_the_configured_rules() -> None:
    world = {
        "materials": [f.material("M1", category="Fragrance", brand="Atelier Sable", tier="luxury")],
        "lots": [f.lot("M1")],
        "channels": [f.channel("C1", allowed=frozenset({"mass"}))],
    }
    applied = f.solver_input(**world)
    assert baseline_planner(applied).raw_x == {}
    ignored = f.solver_input(**world, parameters=f.params(planner_rules=["rsl", "capacity"]))
    result = baseline_planner(ignored)
    assert sum(result.raw_x.values()) == 100
    assert "TIER" in result.audit
    assert result.compliant_x == {}


def test_clean_plan_has_equal_raw_and_compliant_value() -> None:
    result = baseline_planner(f.solver_input())
    assert result.audit == {}
    assert result.compliant_x == result.raw_x
    assert result.compliant.value_recovered == result.raw.value_recovered


def test_repair_is_deterministic_and_passes_the_full_checker() -> None:
    data = assortment_world({"M1": 10.0, "M2": 30.0, "M3": 20.0})
    raw = baseline_planner(data).raw_x
    first, second = repair(data, raw), repair(data, raw)
    assert first == second
    assert violations(data, Solution(x=first)) == []
    kept = {lot_key[0] for lot_key, _ in first}
    assert kept == {"M2"}  # lowest net value per unit dropped first


def test_repair_trims_units_above_the_coverage_need() -> None:
    data = f.solver_input(lots=[f.lot("M1", qty=500)])
    result = baseline_planner(data)
    assert result.audit["cov_hi"] == AuditLine(count=1, excess=320)
    assert sum(result.compliant_x.values()) == 180  # 2 a day over 90 days


def test_repair_drops_a_sku_that_falls_under_its_lower_bound() -> None:
    data = f.solver_input(
        channels=[f.channel("C1", capacity=20)],
        parameters=f.params(planner_rules=[]),
    )
    result = baseline_planner(data)
    assert sum(result.raw_x.values()) == 100
    assert result.audit["cap"] == AuditLine(count=1, excess=80)
    assert result.compliant_x == {}
    assert result.compliant.units_destroyed == 100


def test_all_lots_eliminated_gives_a_defined_empty_plan() -> None:
    data = f.solver_input(channels=[f.channel("C1", min_rsl_pct=100.0)])
    result = baseline_planner(data)
    assert result.raw_x == {}
    assert result.audit == {}
    assert result.compliant_x == {}
    assert result.raw.brand_risk_index == pytest.approx(0.0)
