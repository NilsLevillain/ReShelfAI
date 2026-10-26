"""Solver input: the only thing the solver and the constraint checker read.

Built from a `CanonicalDataset` after class derivation and elimination. All bounds are plain
numbers here, so the model and the checker cannot disagree about them.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from reshelf.elimination import Reason, delivery_date, eliminate
from reshelf.ids import Group, LotKey, MatChan, Pair
from reshelf.schema import (
    AbcClass,
    CanonicalDataset,
    Channel,
    ChannelRule,
    Demand,
    GroupLimit,
    Lot,
    Material,
    Params,
)
from reshelf.scoring import classify_pairs, rank_table, score_weight


@dataclass(frozen=True)
class SolverInput:
    as_of: date
    params: Params
    lots: dict[LotKey, Lot]
    materials: dict[str, Material]
    channels: dict[str, Channel]
    rules: dict[str, ChannelRule]
    admissible: tuple[Pair, ...]
    dropped: dict[Pair, tuple[Reason, ...]]
    # Per selectable (material, channel) pair, that is a pair with at least one admissible lot.
    classes: dict[MatChan, AbcClass]
    score: dict[MatChan, float]
    upper: dict[MatChan, int]  # cov_hi bound: coverage need D, or the push quantity P for NEW
    lower: dict[MatChan, int]  # cov_lo bound: ceil(alpha x min(D, Q)), or min(P, Q) for NEW (push)
    supply: dict[MatChan, int]  # Q: units of the material in admissible lots for the channel
    lots_of: dict[MatChan, tuple[LotKey, ...]]
    group_of: dict[str, Group]
    group_limits: dict[tuple[str, Group], GroupLimit]
    net_value: dict[Pair, float]  # euro per unit: unit cost x recovery factor - brand penalty


def _need(
    dataset: CanonicalDataset, demand_of: dict[MatChan, Demand], material: str, channel: Channel
) -> int:
    """Coverage need D in whole units: what the channel should still receive."""
    demand = demand_of.get((material, channel.channel))
    if demand is None:
        return 0
    month = delivery_date(dataset.as_of, channel).month
    target = demand.daily_demand * dataset.params.coverage_days * demand.seasonality[month - 1]
    return max(0, math.floor(target - (demand.channel_stock + demand.in_transit) + 1e-9))


def build_solver_input(dataset: CanonicalDataset) -> SolverInput:
    if not isinstance(dataset, CanonicalDataset):
        raise TypeError(
            f"the solver reads a CanonicalDataset, not {type(dataset).__name__}. "
            "Load source tables with a SourceAdapter first."
        )
    params = dataset.params
    materials = {m.material: m for m in dataset.materials}
    channels = {c.channel: c for c in dataset.channels}
    rules = {r.channel: r for r in dataset.rules}
    lots = {lot.key: lot for lot in dataset.lots}
    demand_of = {(d.material, d.channel): d for d in dataset.demand}

    classes_all = classify_pairs(dataset)
    elimination = eliminate(dataset, classes_all)
    ranks, n_ranked = rank_table(dataset)

    lots_of: dict[MatChan, list[LotKey]] = defaultdict(list)
    for lot_key, channel_id in elimination.admissible:
        lots_of[(lot_key[0], channel_id)].append(lot_key)

    classes: dict[MatChan, AbcClass] = {}
    score: dict[MatChan, float] = {}
    upper: dict[MatChan, int] = {}
    lower: dict[MatChan, int] = {}
    supply: dict[MatChan, int] = {}
    for mc in sorted(lots_of):
        material, channel_id = mc
        abc_class = classes_all[mc]
        classes[mc] = abc_class
        score[mc] = score_weight(params, abc_class, ranks.get(material), n_ranked)
        supply[mc] = sum(lots[k].qty for k in lots_of[mc])
        if abc_class == "NEW":
            push = params.push_quantity_units[materials[material].category]
            upper[mc] = push
            lower[mc] = min(push, supply[mc])
        else:
            need = _need(dataset, demand_of, material, channels[channel_id])
            upper[mc] = need
            lower[mc] = math.ceil(params.coverage_alpha * min(need, supply[mc]) - 1e-9)

    net_value = {
        (lot_key, channel_id): (
            lots[lot_key].unit_cost * rules[channel_id].recovery_factor
            - rules[channel_id].brand_penalty.get(materials[lot_key[0]].tier, 0.0)
        )
        for lot_key, channel_id in elimination.admissible
    }
    return SolverInput(
        as_of=dataset.as_of,
        params=params,
        lots=lots,
        materials=materials,
        channels=channels,
        rules=rules,
        admissible=elimination.admissible,
        dropped=elimination.dropped,
        classes=classes,
        score=score,
        upper=upper,
        lower=lower,
        supply=supply,
        lots_of={mc: tuple(keys) for mc, keys in lots_of.items()},
        group_of={m.material: (m.brand, m.category) for m in dataset.materials},
        group_limits={(g.channel, (g.brand, g.category)): g for g in dataset.group_limits},
        net_value=net_value,
    )
