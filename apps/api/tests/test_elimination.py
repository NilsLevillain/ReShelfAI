"""Elimination before modeling (TS-020 to TS-027, NO_PUSH)."""

from __future__ import annotations

import factory as f

from reshelf.elimination import DAYS_PER_MONTH, eliminate, rsl_ok
from reshelf.schema import Abc
from reshelf.scoring import classify_pairs

# A 32 month shelf life is exactly 974 days, so 50 percent is exactly 487 days.
HALF = round(32 * DAYS_PER_MONTH / 2)


def _reasons(
    expiry_in_days: int,
    transit_days: int = 0,
    min_rsl_pct: float = 50.0,
    allowed: frozenset[str] = f.ALL_TIERS,
    tier: str = "mass",
) -> tuple[str, ...] | None:
    data = f.dataset(
        materials=[f.material("M1", tier=tier)],
        lots=[f.lot("M1", expiry_in_days=expiry_in_days)],
        channels=[
            f.channel("C1", transit_days=transit_days, min_rsl_pct=min_rsl_pct, allowed=allowed)
        ],
    )
    result = eliminate(data, classify_pairs(data))
    pair = (data.lots[0].key, "C1")
    return result.dropped.get(pair)


def test_half_a_shelf_life_is_a_whole_number_of_days() -> None:
    assert HALF == 487


def test_lot_above_the_threshold_is_admissible() -> None:
    assert _reasons(expiry_in_days=HALF + 100) is None


def test_lot_below_the_threshold_is_dropped_with_rsl() -> None:
    assert _reasons(expiry_in_days=HALF - 1) == ("RSL",)


def test_exactly_the_threshold_stays_admissible() -> None:
    assert _reasons(expiry_in_days=HALF) is None


def test_remaining_shelf_life_is_measured_at_delivery() -> None:
    assert _reasons(expiry_in_days=HALF + 5, transit_days=0) is None
    assert _reasons(expiry_in_days=HALF + 5, transit_days=10) == ("RSL",)


def test_threshold_zero_admits_any_lot_still_alive_at_delivery() -> None:
    assert _reasons(expiry_in_days=11, transit_days=10, min_rsl_pct=0) is None


def test_lot_that_expires_before_or_on_delivery_is_dropped_even_at_threshold_zero() -> None:
    assert _reasons(expiry_in_days=10, transit_days=10, min_rsl_pct=0) == ("RSL",)
    assert _reasons(expiry_in_days=5, transit_days=10, min_rsl_pct=0) == ("RSL",)


def test_tier_not_allowed_is_dropped_with_tier() -> None:
    allowed = frozenset({"premium", "mass"})
    assert _reasons(expiry_in_days=900, allowed=allowed, tier="luxury") == ("TIER",)
    assert _reasons(expiry_in_days=900, allowed=allowed, tier="mass") is None


def test_both_reasons_are_stored() -> None:
    allowed = frozenset({"mass"})
    assert _reasons(expiry_in_days=HALF - 1, allowed=allowed, tier="luxury") == ("RSL", "TIER")


def test_rsl_ok_uses_the_material_shelf_life() -> None:
    data = f.dataset(
        materials=[f.material("M1", shelf_life_months=12)],
        lots=[f.lot("M1", expiry_in_days=100)],
        channels=[f.channel("C1", min_rsl_pct=30)],
    )
    lot, mat = data.lots[0], data.materials[0]
    channel, rule = data.channels[0], data.rules[0]
    assert not rsl_ok(lot, mat, channel, rule, data.as_of)  # 100 of 365 days is 27 percent


def test_new_sku_without_a_push_quantity_for_its_category_is_dropped() -> None:
    data = f.dataset(
        materials=[f.material("M1", category="Skincare")],
        demands=[f.demand("M1", "C1", history=False)],
    )
    result = eliminate(data, classify_pairs(data))
    assert result.dropped[(data.lots[0].key, "C1")] == ("NO_PUSH",)
    assert result.admissible == ()


def test_new_sku_with_a_push_quantity_is_admissible() -> None:
    data = f.dataset(demands=[f.demand("M1", "C1", history=False)])
    result = eliminate(data, classify_pairs(data))
    assert result.admissible == ((data.lots[0].key, "C1"),)


def test_class_c_sku_without_push_quantity_is_not_affected() -> None:
    data = f.dataset(materials=[f.material("M1", category="Skincare")])
    assert eliminate(data, classify_pairs(data)).dropped == {}


def test_admissible_and_dropped_partition_all_pairs() -> None:
    data = f.dataset(
        materials=[f.material("M1", tier="luxury"), f.material("M2")],
        lots=[f.lot("M1"), f.lot("M2", expiry_in_days=30)],
        channels=[
            f.channel("C1", min_rsl_pct=50, allowed=frozenset({"mass"})),
            f.channel("C2"),
        ],
        abc=[Abc(material="M1", abc_class="A", rank=1), Abc(material="M2", abc_class="B", rank=2)],
    )
    result = eliminate(data, classify_pairs(data))
    everything = {(lot.key, c.channel) for lot in data.lots for c in data.channels}
    assert set(result.admissible) | set(result.dropped) == everything
    assert not set(result.admissible) & set(result.dropped)
    assert all(result.dropped.values())
