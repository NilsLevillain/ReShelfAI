"""Elimination before modeling (ADR 003).

A (lot, channel) pair that breaks a hard rule is dropped from the admissible set. Each drop
keeps its reason codes, which the Why panel reads.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

from reshelf.ids import MatChan, Pair
from reshelf.schema import AbcClass, CanonicalDataset, Channel, ChannelRule, Lot, Material

Reason = Literal["RSL", "TIER", "NO_PUSH"]

DAYS_PER_MONTH = 30.4375


@dataclass(frozen=True)
class Elimination:
    admissible: tuple[Pair, ...]
    dropped: dict[Pair, tuple[Reason, ...]]


def delivery_date(as_of: date, channel: Channel) -> date:
    return as_of + timedelta(days=channel.transit_days)


def remaining_shelf_days(lot: Lot, channel: Channel, as_of: date) -> int:
    return (lot.expiry_date - delivery_date(as_of, channel)).days


def rsl_ok(lot: Lot, material: Material, channel: Channel, rule: ChannelRule, as_of: date) -> bool:
    """Remaining shelf life at delivery is at least `min_rsl_pct` of the total life.

    Equal is admissible. A lot that expires on or before its delivery day is never admissible.
    Compared without division so the boundary is exact.
    """
    remaining = remaining_shelf_days(lot, channel, as_of)
    if remaining <= 0:
        return False
    return remaining * 100 >= rule.min_rsl_pct * material.shelf_life_months * DAYS_PER_MONTH


def eliminate(dataset: CanonicalDataset, classes: dict[MatChan, AbcClass]) -> Elimination:
    materials = {m.material: m for m in dataset.materials}
    channels = {c.channel: c for c in dataset.channels}
    rules = {r.channel: r for r in dataset.rules}
    push = dataset.params.push_quantity_units

    admissible: list[Pair] = []
    dropped: dict[Pair, tuple[Reason, ...]] = {}
    for lot in sorted(dataset.lots, key=lambda x: x.key):
        material = materials[lot.material]
        for channel_id in sorted(channels):
            channel, rule = channels[channel_id], rules[channel_id]
            reasons: list[Reason] = []
            if not rsl_ok(lot, material, channel, rule, dataset.as_of):
                reasons.append("RSL")
            if material.tier not in rule.allowed_tiers:
                reasons.append("TIER")
            if classes[(lot.material, channel_id)] == "NEW" and material.category not in push:
                reasons.append("NO_PUSH")
            pair = (lot.key, channel_id)
            if reasons:
                dropped[pair] = tuple(reasons)
            else:
                admissible.append(pair)
    return Elimination(admissible=tuple(admissible), dropped=dropped)
