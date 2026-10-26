"""KPIs of a plan. Pure functions of the solver input and the quantities, so the optimizer plan,
the raw baseline plan and the repaired baseline plan are measured the same way.

Value is read from the lots and channel rules, not from `SolverInput.net_value`, because a raw
baseline plan may use pairs that elimination dropped.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass

from reshelf.ids import Pair
from reshelf.solver_input import SolverInput


@dataclass(frozen=True)
class Kpis:
    value_recovered: float  # euro: sum of (unit cost x recovery factor - brand penalty) x units
    units_allocated: int
    units_destroyed: int  # all stock that is not allocated
    brand_risk_index: float  # sum of penalty x units over sum of unit cost x units, 0 when empty
    skus_per_channel: dict[str, int]
    fill_rate: dict[str, float]  # units allocated over capacity, per channel
    score: float  # sum of the SKU score over the selected (material, channel) pairs


def unit_penalty(data: SolverInput, pair: Pair) -> float:
    lot_key, channel_id = pair
    tier = data.materials[lot_key[0]].tier
    return data.rules[channel_id].brand_penalty.get(tier, 0.0)


def unit_value(data: SolverInput, pair: Pair) -> float:
    lot_key, channel_id = pair
    return data.lots[lot_key].unit_cost * data.rules[channel_id].recovery_factor - unit_penalty(
        data, pair
    )


def compute_kpis(data: SolverInput, x: Mapping[Pair, int]) -> Kpis:
    lines = {pair: units for pair, units in x.items() if units > 0}
    materials: dict[str, set[str]] = defaultdict(set)
    channel_units: dict[str, int] = defaultdict(int)
    value = penalty = cost = 0.0
    for pair, units in lines.items():
        lot_key, channel_id = pair
        materials[channel_id].add(lot_key[0])
        channel_units[channel_id] += units
        value += unit_value(data, pair) * units
        penalty += unit_penalty(data, pair) * units
        cost += data.lots[lot_key].unit_cost * units
    allocated = sum(lines.values())
    supply = sum(lot.qty for lot in data.lots.values())
    selected = {(lot_key[0], channel_id) for (lot_key, channel_id) in lines}
    return Kpis(
        value_recovered=value,
        units_allocated=allocated,
        units_destroyed=supply - allocated,
        brand_risk_index=penalty / cost if cost > 0 else 0.0,
        skus_per_channel={c: len(materials[c]) for c in data.channels},
        fill_rate={
            c: channel_units[c] / ch.capacity_units if ch.capacity_units > 0 else 0.0
            for c, ch in data.channels.items()
        },
        score=sum(data.score.get(mc, 0.0) for mc in selected),
    )
