"""Why stock is destroyed: every unit the plan does not place gets one cause.

Read after a solve. The causes tell a planner which rule to change, so they are named after the
lever, not after a constraint (see ADR 010). Units are split per material, because the coverage
ceiling `upper` is a material and channel bound, and the split always adds up to the units destroyed.

Causes, in the order a unit meets them:

* `blocked`: no channel can take the lot at all (shelf life, brand tier or push rule removed every channel).
* `no_demand`: the lot can go to some channels, but none of them sells the product, so their ceiling is 0.
* `coverage_ceiling`: channels already hold the days of sales they should (`coverage_days`).
* `push_ceiling`: new products are capped at their push quantity (`push_quantity_units`).
* `sku_limit`, `capacity`, `group_limit`: there was room under the ceiling, but a channel limit was tight.
* `not_worth`: there was room and no limit was tight. The plan chose not to send more.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping

from pydantic import BaseModel

from reshelf.constraints import Solution, evaluate
from reshelf.ids import LotKey, MatChan, Pair
from reshelf.solver_input import SolverInput
from reshelf.trace import BINDING_TOLERANCE

CAUSES = (
    "blocked",
    "no_demand",
    "coverage_ceiling",
    "push_ceiling",
    "sku_limit",
    "capacity",
    "group_limit",
    "not_worth",
)

# The scenario parameter a planner can change to move this cause, or None when the cause comes from the world.
LEVER: dict[str, str | None] = {
    "blocked": None,
    "no_demand": None,
    "coverage_ceiling": "coverage_days",
    "push_ceiling": "push_quantity_units",
    "sku_limit": "channel_sku_limit_scale",
    "capacity": None,
    "group_limit": None,
    "not_worth": None,
}

TOP_MATERIALS = 3


class DestroyedMaterial(BaseModel):
    material: str
    description: str
    units: int


class DestructionCause(BaseModel):
    cause: str
    lever: str | None
    units: int
    value_at_risk: float
    share: float
    top_materials: list[DestroyedMaterial]


class DestructionOut(BaseModel):
    units_at_risk: int
    units_placed: int
    units_destroyed: int
    value_destroyed: float
    causes: list[DestructionCause]


def apportion(total: int, weights: Mapping[str, float]) -> dict[str, int]:
    """Split a whole number by weights, largest remainder first. The parts add up to `total`."""
    weight_sum = sum(weights.values())
    if total <= 0 or weight_sum <= 0:
        return {k: 0 for k in weights}
    raw = {k: total * w / weight_sum for k, w in weights.items()}
    out = {k: int(v) for k, v in raw.items()}
    left = total - sum(out.values())
    for key in sorted(raw, key=lambda k: (-(raw[k] - out[k]), k))[:left]:
        out[key] += 1
    return out


def _tight_instances(data: SolverInput, x: Mapping[Pair, int]) -> set[str]:
    results = evaluate(data, Solution(x=x), only=("cap", "sku", "asrt", "asrt_units"))
    return {r.instance for r in results if r.slack <= BINDING_TOLERANCE}


def _limit_cause(data: SolverInput, tight: set[str], mc: MatChan, used: bool) -> str:
    """Which channel limit, if any, held back a pair that still had room under its ceiling."""
    material, channel = mc
    brand, category = data.group_of[material]
    group = f"{brand}/{category},{channel}"
    group_tight = f"asrt[{group}]" in tight or f"asrt_units[{group}]" in tight
    sku_tight = f"sku[{channel}]" in tight
    cap_tight = f"cap[{channel}]" in tight
    order = ("capacity", "group_limit") if used else ("sku_limit", "group_limit", "capacity")
    flags = {"capacity": cap_tight, "group_limit": group_tight, "sku_limit": sku_tight and not used}
    for cause in order:
        if flags[cause]:
            return cause
    return "not_worth"


def explain_destruction(data: SolverInput, x: Mapping[Pair, int]) -> DestructionOut:
    """Split the units the plan does not place by cause. The causes add up to the units destroyed."""
    open_channels: dict[LotKey, set[str]] = defaultdict(set)
    for lot_key, channel in data.admissible:
        open_channels[lot_key].add(channel)
    placed_lot: dict[LotKey, int] = defaultdict(int)
    placed_mc: dict[MatChan, int] = defaultdict(int)
    for (lot_key, channel), n_units in x.items():
        if n_units > 0:
            placed_lot[lot_key] += n_units
            placed_mc[(lot_key[0], channel)] += n_units

    tight = _tight_instances(data, x)
    units: dict[str, int] = dict.fromkeys(CAUSES, 0)
    value: dict[str, float] = dict.fromkeys(CAUSES, 0.0)
    by_material: dict[str, dict[str, int]] = {c: defaultdict(int) for c in CAUSES}

    def book(cause: str, material: str, n: int, unit_cost: float) -> None:
        if n <= 0:
            return
        units[cause] += n
        value[cause] += n * unit_cost
        by_material[cause][material] += n

    open_lots: dict[str, list[LotKey]] = defaultdict(list)
    for lot_key, lot in sorted(data.lots.items()):
        unplaced = lot.qty - placed_lot.get(lot_key, 0)
        if lot_key in open_channels:
            open_lots[lot_key[0]].append(lot_key)
        elif unplaced > 0:
            book("blocked", lot_key[0], unplaced, lot.unit_cost)

    for material, keys in sorted(open_lots.items()):
        supply = sum(data.lots[k].qty for k in keys)
        placed = sum(placed_lot.get(k, 0) for k in keys)
        unplaced = supply - placed
        if unplaced <= 0:
            continue
        cost = (
            sum((data.lots[k].qty - placed_lot.get(k, 0)) * data.lots[k].unit_cost for k in keys)
            / unplaced
        )

        pairs = sorted(mc for mc in data.upper if mc[0] == material)
        ceiling_new = sum(data.upper[mc] for mc in pairs if data.classes[mc] == "NEW")
        ceiling_est = sum(data.upper[mc] for mc in pairs if data.classes[mc] != "NEW")
        ceiling = ceiling_new + ceiling_est
        above = max(0, supply - ceiling)
        if ceiling == 0:
            book("no_demand", material, above, cost)
        else:
            parts = apportion(above, {"push_ceiling": ceiling_new, "coverage_ceiling": ceiling_est})
            for cause, n in parts.items():
                book(cause, material, n, cost)

        room = unplaced - above
        weights: dict[str, float] = defaultdict(float)
        for mc in pairs:
            headroom = max(0, data.upper[mc] - placed_mc.get(mc, 0))
            if headroom:
                weights[_limit_cause(data, tight, mc, placed_mc.get(mc, 0) > 0)] += headroom
        for cause, n in apportion(room, weights).items():
            book(cause, material, n, cost)

    total_units = sum(lot.qty for lot in data.lots.values())
    placed_units = sum(placed_lot.values())
    destroyed = total_units - placed_units
    causes = [
        DestructionCause(
            cause=cause,
            lever=LEVER[cause],
            units=units[cause],
            value_at_risk=value[cause],
            share=units[cause] / destroyed if destroyed else 0.0,
            top_materials=[
                DestroyedMaterial(material=m, description=data.materials[m].description, units=n)
                for m, n in sorted(by_material[cause].items(), key=lambda kv: (-kv[1], kv[0]))[
                    :TOP_MATERIALS
                ]
            ],
        )
        for cause in CAUSES
        if units[cause] > 0
    ]
    causes.sort(key=lambda c: (-c.units, c.cause))
    return DestructionOut(
        units_at_risk=total_units,
        units_placed=placed_units,
        units_destroyed=destroyed,
        value_destroyed=sum(value.values()),
        causes=causes,
    )
