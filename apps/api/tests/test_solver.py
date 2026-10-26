"""Solver: phases, edge cases and the result contract.

TS-042 to TS-054. Instances are small enough to check by hand.
"""

from __future__ import annotations

import random
from dataclasses import fields

import factory as f
import pytest

from reshelf import solver as solver_module
from reshelf.constraints import Solution, violations
from reshelf.schema import Abc, Params
from reshelf.solver import PulpSolver, SolveResult, explain
from reshelf.solver_input import SolverInput


def selected(result: SolveResult) -> set[str]:
    return {material for (material, _), on in result.z.items() if on}


def clean(data: SolverInput, result: SolveResult) -> None:
    """The checker, which the model does not use, finds nothing wrong with the plan."""
    assert violations(data, Solution(x=result.x, y=result.y, z=result.z)) == []


def two_materials(
    abc: list[Abc],
    cost_second: float = 100.0,
    parameters: Params | None = None,
    max_skus: int = 1,
) -> SolverInput:
    return f.solver_input(
        materials=[f.material("M1"), f.material("M2")],
        lots=[f.lot("M1", unit_cost=10.0), f.lot("M2", unit_cost=cost_second)],
        channels=[f.channel("C1", max_skus=max_skus)],
        abc=abc,
        parameters=parameters,
    )


def test_single_sku_takes_all_it_can() -> None:
    data = f.solver_input()
    result = PulpSolver().solve(data)
    assert result.status == "optimal"
    assert result.units_allocated == 100
    assert result.units_destroyed == 0
    assert result.objective == pytest.approx(100 * 10.0 * 0.5)
    clean(data, result)


def test_phase_1_score_beats_value() -> None:  # TS-042
    # One slot. M2 is worth ten times more per unit, but M1 is class A and M2 class C.
    data = two_materials(
        [Abc(material="M1", abc_class="A", rank=1), Abc(material="M2", abc_class="C", rank=2)]
    )
    result = PulpSolver().solve(data)
    assert selected(result) == {"M1"}
    assert result.best_score == pytest.approx(data.score[("M1", "C1")])
    assert result.score == pytest.approx(result.best_score)
    clean(data, result)


def test_phase_2_trades_score_within_epsilon() -> None:  # TS-043
    abc = [Abc(material="M1", abc_class="B", rank=1), Abc(material="M2", abc_class="B", rank=2)]
    s1, s2 = 0.7 + 0.25 * 0.5, 0.7  # by hand: base + 0.25 x (1 - rank / 2)
    strict = two_materials(abc, parameters=f.params(epsilon=0.01))
    loose = two_materials(abc, parameters=f.params(epsilon=0.2))
    r_strict = PulpSolver().solve(strict)
    r_loose = PulpSolver().solve(loose)
    assert r_strict.best_score == pytest.approx(s1)
    assert selected(r_strict) == {"M1"}  # M2 scores 15% less, outside 1%
    assert selected(r_loose) == {"M2"}  # inside 20%, so value decides
    assert r_loose.score >= (1 - 0.2) * r_loose.best_score
    assert r_loose.objective > r_strict.objective
    assert r_loose.score == pytest.approx(s2)


def test_epsilon_zero_and_one() -> None:  # TS-044
    abc = [Abc(material="M1", abc_class="B", rank=1), Abc(material="M2", abc_class="B", rank=2)]
    zero = PulpSolver().solve(two_materials(abc, parameters=f.params(epsilon=0)))
    assert zero.status == "optimal"
    assert zero.score == pytest.approx(zero.best_score)
    one = PulpSolver().solve(two_materials(abc, parameters=f.params(epsilon=1)))
    assert one.status == "optimal"
    assert selected(one) == {"M2"}  # score no longer constrains, value decides


def test_unallocated_units_are_destroyed() -> None:  # TS-045
    data = f.solver_input(
        channels=[f.channel("C1", capacity=40)], parameters=f.params(coverage_alpha=0.2)
    )
    result = PulpSolver().solve(data)
    assert result.units_allocated == 40
    assert result.units_destroyed == 60


def test_rules_that_cannot_be_met_leave_everything_destroyed() -> None:  # TS-046
    # A NEW SKU needs its push quantity of 50 but the channel holds 10. The model is not
    # infeasible: the SKU is simply not selected, so the stock is destroyed.
    data = f.solver_input(
        channels=[f.channel("C1", capacity=10)],
        demands=[f.demand("M1", "C1", history=False)],
    )
    result = PulpSolver().solve(data)
    assert result.status == "optimal"
    assert result.x == {}
    assert result.units_destroyed == 100


def test_infeasible_status_has_a_plain_sentence() -> None:  # TS-046
    sentence = explain("infeasible", 60)
    assert "contradict" in sentence and "push quantity" in sentence
    assert "Traceback" not in sentence


def test_empty_input() -> None:  # TS-047
    data = f.solver_input(lots=[])
    result = PulpSolver().solve(data)
    assert result.status == "optimal"
    assert result.x == {}
    assert result.units_allocated == result.units_destroyed == 0
    assert result.objective == 0


def test_single_channel() -> None:  # TS-048
    data = f.solver_input(channels=[f.channel("ONLY")])
    result = PulpSolver().solve(data)
    assert result.status == "optimal"
    assert {c for (_, c) in result.x} == {"ONLY"}


def test_all_lots_eliminated() -> None:  # TS-049
    data = f.solver_input(channels=[f.channel("C1", allowed=frozenset({"luxury"}))])
    assert data.admissible == ()
    result = PulpSolver().solve(data)
    assert result.status == "optimal"
    assert result.units_destroyed == 100
    assert result.objective == 0
    assert result.score == 0


def large_input() -> SolverInput:
    """300 SKUs, 4 channels, about 1,200 admissible pairs. Takes HiGHS several seconds."""
    rng = random.Random(1)
    codes = [f"M{i:03d}" for i in range(300)]
    return f.solver_input(
        materials=[f.material(code, brand=f"B{i % 6}") for i, code in enumerate(codes)],
        lots=[
            f.lot(
                code,
                qty=rng.randint(50, 500),
                unit_cost=rng.uniform(2, 40),
                expiry_in_days=rng.randint(300, 700),
            )
            for code in codes
        ],
        channels=[
            f.channel(f"C{j}", capacity=8000, max_skus=60, recovery=0.2 + 0.1 * j) for j in range(4)
        ],
        demands=[
            f.demand(code, f"C{j}", daily=rng.uniform(0.2, 3)) for code in codes for j in range(4)
        ],
        abc=[
            Abc(material=code, abc_class=rng.choice(["A", "B", "C"]), rank=i + 1)
            for i, code in enumerate(codes)
        ],
    )


def test_time_limit_returns_the_best_plan_found() -> None:  # TS-050
    data = large_input()
    result = PulpSolver().solve(data, time_limit_s=0.05)
    assert result.status in ("feasible", "time_limit")
    assert result.time_limit_s == 0.05
    assert result.time_s < 5
    assert "time limit" in result.message
    if result.has_plan:
        assert result.mip_gap is None or result.mip_gap >= 0
        clean(data, result)
    else:
        assert result.x == {}


def test_time_limit_sentences() -> None:  # TS-050
    assert "time limit of 1 s" in explain("time_limit", 1)
    assert "valid plan" in explain("feasible", 1)
    assert explain("optimal", 1) == ""


def test_result_has_every_field() -> None:  # TS-051
    result = PulpSolver().solve(f.solver_input(), time_limit_s=30)
    names = {fld.name for fld in fields(result)}
    assert {"status", "objective", "mip_gap", "time_s", "time_limit_s"} <= names
    assert result.time_limit_s == 30
    assert result.time_s >= 0
    assert result.mip_gap is not None and result.mip_gap >= 0
    assert result.solver == "highs"
    assert result.message == ""


def test_default_time_limit_comes_from_params() -> None:
    result = PulpSolver().solve(f.solver_input(parameters=f.params(solver_time_limit_s=17)))
    assert result.time_limit_s == 17


def test_cbc_gives_the_same_plan() -> None:  # TS-052
    data = two_materials(
        [Abc(material="M1", abc_class="B", rank=1), Abc(material="M2", abc_class="B", rank=2)],
        parameters=f.params(epsilon=0.2),
    )
    highs = PulpSolver("highs").solve(data)
    cbc = PulpSolver("cbc").solve(data)
    assert cbc.solver == "cbc"
    assert cbc.objective == pytest.approx(highs.objective)
    assert cbc.score == pytest.approx(highs.score)


def test_falls_back_to_cbc_when_highs_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:  # TS-052
    monkeypatch.setattr(solver_module, "_highs_available", lambda: False)
    result = PulpSolver().solve(f.solver_input())
    assert result.solver == "cbc"
    assert result.status == "optimal"
    assert result.units_allocated == 100


def test_negative_net_value_is_not_forced_beyond_the_lower_bound() -> None:  # TS-053
    # Recovery 5 euro a unit, brand penalty 20, so every unit loses 15. The SKU scores, so it is
    # selected, and it receives only the 50 units cov_lo asks for.
    data = f.solver_input(
        channels=[f.channel("C1", penalty={"luxury": 0.0, "premium": 0.0, "mass": 20.0})]
    )
    result = PulpSolver().solve(data)
    assert selected(result) == {"M1"}
    assert result.units_allocated == data.lower[("M1", "C1")] == 50
    assert result.objective == pytest.approx(-15 * 50)
    clean(data, result)


def test_score_weights_come_from_params() -> None:  # TS-054
    abc = [Abc(material="M1", abc_class="B", rank=1), Abc(material="M2", abc_class="C", rank=2)]
    default = PulpSolver().solve(two_materials(abc))
    boosted = PulpSolver().solve(
        two_materials(
            abc,
            parameters=f.params(score_base={"A": 1.0, "B": 0.7, "C": 2.0, "NEW": 0.55}),
        )
    )
    assert selected(default) == {"M1"}
    assert selected(boosted) == {"M2"}


def test_same_input_gives_the_same_plan() -> None:
    data = two_materials(
        [Abc(material="M1", abc_class="B", rank=1), Abc(material="M2", abc_class="B", rank=2)],
        parameters=f.params(epsilon=0.2),
    )
    a, b = PulpSolver().solve(data), PulpSolver().solve(data)
    assert a.x == b.x and a.objective == b.objective
