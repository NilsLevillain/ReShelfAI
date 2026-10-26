"""KPIs: TS-048, TS-049, TS-070 to TS-074. Instances are small enough to check by hand."""

from __future__ import annotations

import factory as f
import pytest

from reshelf.ids import LotKey, Pair
from reshelf.kpis import compute_kpis
from reshelf.solver import PulpSolver
from reshelf.solver_input import SolverInput


def world() -> tuple[SolverInput, LotKey, LotKey]:
    data = f.solver_input(
        materials=[f.material("M1"), f.material("M2")],
        lots=[f.lot("M1", qty=100, unit_cost=10.0), f.lot("M2", qty=50, unit_cost=20.0)],
        channels=[
            f.channel("C1", capacity=80, recovery=0.5, penalty={"mass": 2.0}),
            f.channel("C2", capacity=40, recovery=0.4, penalty={"mass": 1.0}),
        ],
    )
    m1, m2 = sorted(data.lots)
    return data, m1, m2


def three_lines(m1: LotKey, m2: LotKey) -> dict[Pair, int]:
    return {(m1, "C1"): 30, (m1, "C2"): 20, (m2, "C1"): 10}


def test_value_recovered_is_sum_of_unit_value_times_units() -> None:
    data, m1, m2 = world()
    kpis = compute_kpis(data, three_lines(m1, m2))
    # (10 * 0.5 - 2) * 30 + (10 * 0.4 - 1) * 20 + (20 * 0.5 - 2) * 10
    assert kpis.value_recovered == pytest.approx(230.0)


def test_units_destroyed_is_supply_minus_allocated() -> None:
    data, m1, m2 = world()
    kpis = compute_kpis(data, three_lines(m1, m2))
    assert kpis.units_allocated == 60
    assert kpis.units_destroyed == 90


def test_brand_risk_index_is_penalty_over_cost() -> None:
    data, m1, m2 = world()
    kpis = compute_kpis(data, three_lines(m1, m2))
    # penalty 60 + 20 + 20 = 100, cost 300 + 200 + 200 = 700
    assert kpis.brand_risk_index == pytest.approx(100 / 700)


def test_empty_plan_is_defined() -> None:
    data, _, _ = world()
    kpis = compute_kpis(data, {})
    assert kpis.value_recovered == 0.0
    assert kpis.brand_risk_index == 0.0
    assert kpis.units_destroyed == 150
    assert kpis.score == 0.0
    assert set(kpis.skus_per_channel) == {"C1", "C2"}
    assert set(kpis.skus_per_channel.values()) == {0}


def test_skus_per_channel_and_fill_rate_match_lines() -> None:
    data, m1, m2 = world()
    kpis = compute_kpis(data, three_lines(m1, m2))
    assert kpis.skus_per_channel == {"C1": 2, "C2": 1}
    assert kpis.fill_rate == {"C1": pytest.approx(0.5), "C2": pytest.approx(0.5)}


def test_zero_lines_are_ignored() -> None:
    data, m1, _ = world()
    kpis = compute_kpis(data, {(m1, "C1"): 0})
    assert kpis.skus_per_channel["C1"] == 0


def test_score_counts_each_selected_pair_once() -> None:
    data, m1, m2 = world()
    kpis = compute_kpis(data, three_lines(m1, m2))
    expected = data.score[("M1", "C1")] + data.score[("M1", "C2")] + data.score[("M2", "C1")]
    assert kpis.score == pytest.approx(expected)


def test_single_channel_world_has_no_division_by_zero() -> None:
    data = f.solver_input()
    result = PulpSolver().solve(data)
    kpis = compute_kpis(data, result.x)
    assert kpis.units_allocated == result.units_allocated
    assert kpis.value_recovered == pytest.approx(result.objective)
    assert kpis.score == pytest.approx(result.score)


def test_all_lots_eliminated_destroys_everything() -> None:
    data = f.solver_input(channels=[f.channel("C1", min_rsl_pct=100.0)])
    result = PulpSolver().solve(data)
    kpis = compute_kpis(data, result.x)
    assert kpis.units_destroyed == 100
    assert kpis.brand_risk_index == 0.0
