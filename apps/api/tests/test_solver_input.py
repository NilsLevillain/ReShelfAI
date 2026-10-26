"""Class, score and bounds in the solver input (TS-013, TS-198 to TS-205, TS-054)."""

from __future__ import annotations

import factory as f
import pandas as pd
import pytest

from reshelf.schema import Abc, CanonicalDataset
from reshelf.scoring import classify_pairs, score_weight
from reshelf.solver_input import build_solver_input

MC = ("M1", "C1")


def test_solver_rejects_a_raw_dataframe() -> None:
    with pytest.raises(TypeError, match="CanonicalDataset"):
        build_solver_input(pd.DataFrame({"MATNR": ["1"]}))  # type: ignore[arg-type]


# Class per material and channel


def test_pair_with_sales_keeps_the_abc_class() -> None:
    data = f.dataset(abc=[Abc(material="M1", abc_class="A", rank=1)])
    assert classify_pairs(data)[MC] == "A"


def test_pair_without_sales_in_the_channel_is_new_even_for_a_class_a_material() -> None:
    data = f.dataset(
        abc=[Abc(material="M1", abc_class="A", rank=1)],
        channels=[f.channel("C1"), f.channel("C2")],
        demands=[f.demand("M1", "C1")],
    )
    classes = classify_pairs(data)
    assert classes[("M1", "C1")] == "A"
    assert classes[("M1", "C2")] == "NEW"


def test_pair_with_sales_but_no_abc_row_is_class_c() -> None:
    data = f.dataset(abc=[])
    assert classify_pairs(data)[MC] == "C"


def test_stock_in_the_channel_without_sales_does_not_make_a_pair_known() -> None:
    data = f.dataset(demands=[f.demand("M1", "C1", stock=500, history=False)])
    assert classify_pairs(data)[MC] == "NEW"


# Score weight


def _score(abc_class: str, rank: int | None, n: int = 100) -> float:
    return score_weight(f.params(), abc_class, rank, n)  # type: ignore[arg-type]


def test_class_a_beats_class_c_and_new_on_the_best_and_worst_rank() -> None:
    worst_a = _score("A", 100)
    assert worst_a > _score("C", 1)
    assert worst_a > _score("NEW", 1)


def test_rank_breaks_ties_only_inside_a_class() -> None:
    assert _score("B", 1) > _score("B", 50) > _score("B", 100)
    assert _score("A", 100) > _score("B", 1)


def test_missing_rank_counts_as_the_lowest() -> None:
    assert _score("B", None) == _score("B", 100)
    assert _score("B", None) == pytest.approx(0.7)


def test_score_is_deterministic() -> None:
    assert len({_score("A", 7) for _ in range(5)}) == 1


def test_score_weights_come_from_params() -> None:
    changed = f.params(score_base={"A": 2.0, "B": 0.7, "C": 0.4, "NEW": 0.55})
    assert score_weight(changed, "A", 1, 10) > score_weight(f.params(), "A", 1, 10)


def test_solver_input_scores_each_pair() -> None:
    data = f.solver_input(abc=[Abc(material="M1", abc_class="A", rank=1)])
    assert data.score[MC] == pytest.approx(1.0 + 0.25 * (1 - 1 / 1))
    assert data.classes[MC] == "A"


def test_material_without_abc_row_but_with_sales_is_scored_as_c_with_lowest_rank() -> None:
    data = f.solver_input(abc=[])
    assert data.score[MC] == pytest.approx(0.4)


# Coverage need


def test_coverage_need_is_demand_times_days_minus_stock() -> None:
    data = f.solver_input(demands=[f.demand("M1", "C1", daily=2.0, stock=30)])
    assert data.upper[MC] == 150  # 2 per day x 90 days - 30


def test_in_transit_stock_lowers_the_need() -> None:
    data = f.solver_input(demands=[f.demand("M1", "C1", daily=2.0, stock=30, in_transit=20)])
    assert data.upper[MC] == 130


def test_need_never_goes_below_zero() -> None:
    data = f.solver_input(demands=[f.demand("M1", "C1", daily=1.0, stock=500)])
    assert data.upper[MC] == 0
    assert data.lower[MC] == 0


def test_need_uses_the_seasonality_of_the_delivery_month() -> None:
    # as_of 1 October plus 10 days of transit is October, index 9. Plus 40 days is November.
    season = [1.0] * 12
    season[9], season[10] = 2.0, 0.5
    near = f.solver_input(
        channels=[f.channel("C1", transit_days=10)],
        demands=[f.demand("M1", "C1", daily=1.0, seasonality=season)],
    )
    far = f.solver_input(
        channels=[f.channel("C1", transit_days=40)],
        demands=[f.demand("M1", "C1", daily=1.0, seasonality=season)],
    )
    assert near.upper[MC] == 180
    assert far.upper[MC] == 45


def test_missing_demand_row_means_no_coverage_need() -> None:
    data = f.solver_input(demands=[])
    assert data.classes[MC] == "NEW"  # no sales history at all
    data = f.solver_input(
        abc=[Abc(material="M1", abc_class="A", rank=1)],
        demands=[f.demand("M2", "C1")],
        materials=[f.material("M1"), f.material("M2")],
        lots=[f.lot("M1"), f.lot("M2")],
    )
    assert data.classes[MC] == "NEW"


def test_lower_bound_is_alpha_times_the_smaller_of_need_and_supply() -> None:
    data = f.solver_input(demands=[f.demand("M1", "C1", daily=2.0)])  # need 180, supply 100
    assert data.supply[MC] == 100
    assert data.lower[MC] == 50
    small = f.solver_input(demands=[f.demand("M1", "C1", daily=0.5)])  # need 45
    assert small.lower[MC] == 23  # ceil(0.5 x 45)


# NEW SKUs


def test_new_pair_is_bounded_by_the_push_quantity_of_its_category() -> None:
    haircare = f.solver_input(demands=[f.demand("M1", "C1", history=False)])
    assert (haircare.upper[MC], haircare.lower[MC]) == (50, 50)
    fragrance = f.solver_input(
        materials=[f.material("M1", category="Fragrance")],
        demands=[f.demand("M1", "C1", history=False)],
    )
    assert (fragrance.upper[MC], fragrance.lower[MC]) == (5, 5)


def test_push_lower_bound_is_capped_by_the_supply() -> None:
    data = f.solver_input(lots=[f.lot("M1", qty=20)], demands=[f.demand("M1", "C1", history=False)])
    assert (data.upper[MC], data.lower[MC]) == (50, 20)


def test_new_pair_without_push_quantity_is_not_selectable_and_says_why() -> None:
    data = f.solver_input(
        materials=[f.material("M1", category="Skincare")],
        demands=[f.demand("M1", "C1", history=False)],
    )
    assert MC not in data.classes
    assert data.dropped[(data.lots[next(iter(data.lots))].key, "C1")] == ("NO_PUSH",)


# Net value


def test_net_value_is_cost_times_recovery_minus_brand_penalty() -> None:
    data = f.solver_input(
        materials=[f.material("M1", tier="luxury")],
        lots=[f.lot("M1", unit_cost=20.0)],
        channels=[f.channel("C1", recovery=0.5, penalty={"luxury": 6.0, "premium": 0, "mass": 0})],
    )
    (pair,) = data.admissible
    assert data.net_value[pair] == pytest.approx(4.0)


def test_solver_input_only_holds_admissible_pairs_in_selectable_sets() -> None:
    data: CanonicalDataset = f.dataset(
        channels=[f.channel("C1"), f.channel("C2", allowed=frozenset({"premium"}))],
        demands=[f.demand("M1", "C1"), f.demand("M1", "C2")],
    )
    built = build_solver_input(data)
    assert set(built.classes) == {("M1", "C1")}
