"""Constraint registry and checker: a feasible and a violating case per constraint.

TS-030 to TS-041, plus the two constraints added after the war plan table: `asrt_units`
(decision Q8) and `link_yx`.
"""

from __future__ import annotations

import factory as f
import pytest

from reshelf.constraints import (
    CONSTRAINT_LABELS,
    CONSTRAINTS,
    ConstraintResult,
    Solution,
    evaluate,
    violation_counts,
    violations,
)
from reshelf.ids import Pair
from reshelf.schema import Abc, GroupLimit
from reshelf.solver_input import SolverInput


def pair(data: SolverInput, material: str, channel: str, plant: str = "P1") -> Pair:
    (key,) = [k for k in data.lots if k[0] == material and k[1] == plant]
    return (key, channel)


def names(results: list[ConstraintResult]) -> set[str]:
    return {r.constraint for r in results}


def test_constraint_names_are_stable() -> None:  # TS-040
    assert CONSTRAINT_LABELS == (
        "supply[l]",
        "link_xy[l,c]",
        "link_yx[l,c]",
        "link_yz[l,c]",
        "link_zy[m,c]",
        "cap[c]",
        "sku[c]",
        "asrt[g,c]",
        "cov_hi[m,c]",
        "cov_lo[m,c]",
        "push[m,c]",
        "asrt_units[g,c]",
    )
    assert len({c.name for c in CONSTRAINTS}) == len(CONSTRAINTS)


def test_empty_allocation_violates_nothing() -> None:
    data = f.solver_input()
    assert violations(data, Solution(x={})) == []


def test_every_instance_has_a_named_slack() -> None:
    data = f.solver_input()
    results = evaluate(data, Solution(x={pair(data, "M1", "C1"): 60}))
    assert {r.constraint for r in results} >= {"supply", "cap", "sku", "cov_hi", "cov_lo"}
    assert all(r.instance.startswith(r.constraint + "[") for r in results)
    cap = next(r for r in results if r.instance == "cap[C1]")
    assert (cap.lhs, cap.rhs, cap.slack) == (60, 10_000, 9_940)


# supply[l]


def test_supply_feasible_and_violating() -> None:
    data = f.solver_input(channels=[f.channel("C1"), f.channel("C2")])
    ok = Solution(x={pair(data, "M1", "C1"): 50, pair(data, "M1", "C2"): 50})
    bad = Solution(x={pair(data, "M1", "C1"): 60, pair(data, "M1", "C2"): 60})
    assert "supply" not in names(violations(data, ok))
    assert "supply" in names(violations(data, bad))


# links


def test_link_xy_units_need_a_used_pair() -> None:
    data = f.solver_input()
    p = pair(data, "M1", "C1")
    bad = Solution(x={p: 60}, y={p: False}, z={("M1", "C1"): True})
    assert "link_xy" in names(violations(data, bad))
    good = Solution(x={p: 60}, y={p: True}, z={("M1", "C1"): True})
    assert "link_xy" not in names(violations(data, good))


def test_link_yx_a_used_pair_carries_a_unit() -> None:
    data = f.solver_input()
    p = pair(data, "M1", "C1")
    bad = Solution(x={}, y={p: True}, z={("M1", "C1"): True})
    assert "link_yx" in names(violations(data, bad))
    good = Solution(x={p: 60}, y={p: True}, z={("M1", "C1"): True})
    assert "link_yx" not in names(violations(data, good))


def test_link_yz_a_used_lot_needs_its_sku_selected() -> None:
    data = f.solver_input()
    p = pair(data, "M1", "C1")
    bad = Solution(x={p: 60}, y={p: True}, z={("M1", "C1"): False})
    assert "link_yz" in names(violations(data, bad))
    good = Solution(x={p: 60}, y={p: True}, z={("M1", "C1"): True})
    assert "link_yz" not in names(violations(data, good))


def test_link_zy_a_selected_sku_uses_a_lot() -> None:
    data = f.solver_input()
    p = pair(data, "M1", "C1")
    bad = Solution(x={}, y={p: False}, z={("M1", "C1"): True})
    assert "link_zy" in names(violations(data, bad))
    good = Solution(x={p: 60}, y={p: True}, z={("M1", "C1"): True})
    assert "link_zy" not in names(violations(data, good))


# channel limits


def test_cap_channel_capacity() -> None:
    data = f.solver_input(channels=[f.channel("C1", capacity=50)])
    p = pair(data, "M1", "C1")
    assert "cap" not in names(violations(data, Solution(x={p: 50})))
    assert "cap" in names(violations(data, Solution(x={p: 51})))


def test_sku_limit_per_channel() -> None:
    data = f.solver_input(
        materials=[f.material("M1"), f.material("M2")],
        lots=[f.lot("M1"), f.lot("M2")],
        channels=[f.channel("C1", max_skus=1)],
    )
    one = Solution(x={pair(data, "M1", "C1"): 60})
    two = Solution(x={pair(data, "M1", "C1"): 60, pair(data, "M2", "C1"): 60})
    assert "sku" not in names(violations(data, one))
    assert "sku" in names(violations(data, two))


# assortment groups


def _group_data() -> SolverInput:
    return f.solver_input(
        materials=[f.material("M1"), f.material("M2")],
        lots=[f.lot("M1"), f.lot("M2")],
        group_limits=[
            GroupLimit(
                channel="C1", brand="Brightleaf", category="Haircare", max_skus=1, max_units=100
            )
        ],
    )


def test_asrt_limits_skus_of_a_brand_and_category() -> None:
    data = _group_data()
    one = Solution(x={pair(data, "M1", "C1"): 60})
    two = Solution(x={pair(data, "M1", "C1"): 60, pair(data, "M2", "C1"): 40})
    assert "asrt" not in names(violations(data, one))
    assert "asrt" in names(violations(data, two))


def test_asrt_units_limits_units_of_a_brand_and_category() -> None:
    data = _group_data()
    ok = Solution(x={pair(data, "M1", "C1"): 100})
    bad = Solution(x={pair(data, "M1", "C1"): 100, pair(data, "M2", "C1"): 1})
    assert "asrt_units" not in names(violations(data, ok))
    assert "asrt_units" in names(violations(data, bad))


def test_missing_group_row_means_no_group_limit() -> None:
    data = f.solver_input()
    assert not [r for r in evaluate(data, Solution(x={})) if r.constraint.startswith("asrt")]


# coverage and push


def test_cov_hi_never_exceeds_the_coverage_need() -> None:
    data = f.solver_input(
        lots=[f.lot("M1", qty=500)], demands=[f.demand("M1", "C1", daily=1.0)]
    )  # need 90
    p = pair(data, "M1", "C1")
    assert "cov_hi" not in names(violations(data, Solution(x={p: 90})))
    assert "cov_hi" in names(violations(data, Solution(x={p: 91})))


def test_cov_lo_a_selected_sku_gets_alpha_of_its_need() -> None:
    data = f.solver_input(
        lots=[f.lot("M1", qty=500)], demands=[f.demand("M1", "C1", daily=1.0)]
    )  # need 90, lower 45
    p = pair(data, "M1", "C1")
    assert "cov_lo" not in names(violations(data, Solution(x={p: 45})))
    assert "cov_lo" in names(violations(data, Solution(x={p: 44})))


def test_cov_inactive_when_the_sku_is_not_selected() -> None:  # TS-041
    data = f.solver_input(lots=[f.lot("M1", qty=500)], demands=[f.demand("M1", "C1", daily=1.0)])
    results = evaluate(data, Solution(x={}))
    for r in results:
        if r.constraint in {"cov_hi", "cov_lo"}:
            assert (r.lhs, r.rhs) == (0, 0)
    assert violations(data, Solution(x={})) == []


def test_push_a_selected_new_sku_gets_its_push_quantity() -> None:
    data = f.solver_input(demands=[f.demand("M1", "C1", history=False)])  # haircare push 50
    p = pair(data, "M1", "C1")
    assert "push" not in names(violations(data, Solution(x={p: 50})))
    assert "push" in names(violations(data, Solution(x={p: 49})))
    assert "cov_lo" not in {r.constraint for r in evaluate(data, Solution(x={p: 49}))}


def test_new_sku_cannot_exceed_its_push_quantity() -> None:
    data = f.solver_input(demands=[f.demand("M1", "C1", history=False)])
    p = pair(data, "M1", "C1")
    assert "cov_hi" in names(violations(data, Solution(x={p: 51})))


def test_push_is_capped_by_the_supply() -> None:
    data = f.solver_input(lots=[f.lot("M1", qty=20)], demands=[f.demand("M1", "C1", history=False)])
    p = pair(data, "M1", "C1")
    assert violations(data, Solution(x={p: 20})) == []


# eliminated pairs


def test_units_on_an_eliminated_pair_are_reported_with_the_reason_code() -> None:
    data = f.solver_input(
        materials=[f.material("M1", tier="luxury")],
        channels=[f.channel("C1"), f.channel("C2", allowed=frozenset({"mass"}))],
        demands=[f.demand("M1", "C1"), f.demand("M1", "C2")],
        abc=[Abc(material="M1", abc_class="A", rank=1)],
    )
    (key,) = data.lots
    found = violations(data, Solution(x={(key, "C2"): 10}))
    assert [r.constraint for r in found if r.constraint == "TIER"] == ["TIER"]
    assert violation_counts(found)["TIER"] == 1


def test_planner_rules_filter_what_a_planner_would_catch() -> None:
    data = f.solver_input(
        materials=[f.material("M1", tier="luxury")],
        channels=[f.channel("C1", capacity=5), f.channel("C2", allowed=frozenset({"mass"}))],
        demands=[f.demand("M1", "C1"), f.demand("M1", "C2")],
        abc=[Abc(material="M1", abc_class="A", rank=1)],
    )
    (key,) = data.lots
    solution = Solution(x={(key, "C1"): 10, (key, "C2"): 10})
    assert names(violations(data, solution, rules=["capacity"])) == {"cap"}
    assert names(violations(data, solution, rules=["tier"])) == {"TIER"}
    assert {"cap", "TIER", "cov_lo"} <= names(violations(data, solution))


def test_only_filters_the_constraints_evaluated() -> None:
    data = f.solver_input()
    results = evaluate(data, Solution(x={}), only=["cap"])
    assert names(results) == {"cap"}


@pytest.mark.parametrize("spec", CONSTRAINTS, ids=lambda s: s.name)
def test_every_constraint_is_evaluated_on_a_rich_instance(spec: object) -> None:
    data = f.solver_input(
        materials=[f.material("M1"), f.material("M2")],
        lots=[f.lot("M1"), f.lot("M2")],
        demands=[f.demand("M1", "C1"), f.demand("M2", "C1", history=False)],
        group_limits=[
            GroupLimit(
                channel="C1", brand="Brightleaf", category="Haircare", max_skus=5, max_units=500
            )
        ],
    )
    solution = Solution(x={pair(data, "M1", "C1"): 60, pair(data, "M2", "C1"): 50})
    assert spec.name in names(evaluate(data, solution))  # type: ignore[attr-defined]
    assert violations(data, solution) == []
