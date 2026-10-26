"""Greedy baseline: a planner proxy (ADR 005).

The planner applies the rules in `params.planner_rules` by hand (default shelf life, brand tier,
channel capacity) and ignores the rest. The full constraint checker audits that plan. Three
numbers come out: the raw plan, its violations, and the compliant plan after a deterministic
repair. The optimizer is only ever compared with the compliant one.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from reshelf.constraints import REASON_RULE, ConstraintResult, Solution, violations
from reshelf.ids import LotKey, MatChan, Pair, mc_label, pair_label
from reshelf.kpis import Kpis, compute_kpis, unit_value
from reshelf.solver_input import SolverInput

MAX_REPAIR_PASSES = 100


@dataclass(frozen=True)
class AuditLine:
    """What the checker found for one named constraint.

    `excess` is in the unit of the constraint: units for cap, cov_hi, asrt_units, cov_lo, push and
    eliminated pairs, SKUs for sku and asrt.
    """

    count: int
    excess: int


@dataclass(frozen=True)
class BaselineResult:
    raw_x: dict[Pair, int]
    raw: Kpis
    audit: dict[str, AuditLine]
    compliant_x: dict[Pair, int]
    compliant: Kpis


def baseline_planner(data: SolverInput) -> BaselineResult:
    raw_x = plan_by_hand(data)
    compliant_x = repair(data, raw_x)
    return BaselineResult(
        raw_x=raw_x,
        raw=compute_kpis(data, raw_x),
        audit=audit(violations(data, Solution(x=raw_x))),
        compliant_x=compliant_x,
        compliant=compute_kpis(data, compliant_x),
    )


def audit(found: list[ConstraintResult]) -> dict[str, AuditLine]:
    count: dict[str, int] = defaultdict(int)
    excess: dict[str, float] = defaultdict(float)
    for r in found:
        if r.violated:
            count[r.constraint] += 1
            excess[r.constraint] += -r.slack
    return {name: AuditLine(count[name], round(excess[name])) for name in sorted(count)}


def _planner_pairs(data: SolverInput) -> dict[LotKey, list[str]]:
    """Channels a planner considers per lot: admissible, plus pairs dropped only by a rule the
    planner does not apply."""
    applied = set(data.params.planner_rules)
    channels: dict[LotKey, set[str]] = defaultdict(set)
    for lot_key, channel_id in data.admissible:
        channels[lot_key].add(channel_id)
    for (lot_key, channel_id), reasons in data.dropped.items():
        if all(REASON_RULE[r] is None or REASON_RULE[r] not in applied for r in reasons):
            channels[lot_key].add(channel_id)
    ranked = sorted(data.channels, key=lambda c: (-data.rules[c].recovery_factor, c))
    return {lot: [c for c in ranked if c in ok] for lot, ok in channels.items()}


def plan_by_hand(data: SolverInput) -> dict[Pair, int]:
    """Lots by value at risk, each to the best recovery channel that still has capacity."""

    def value_at_risk(lot_key: LotKey) -> float:
        lot = data.lots[lot_key]
        days = max((lot.expiry_date - data.as_of).days, 1)
        return lot.qty * lot.unit_cost / days  # urgency is 1 / days to expiry

    options = _planner_pairs(data)
    capacity_applies = "capacity" in data.params.planner_rules
    left = {c: ch.capacity_units for c, ch in data.channels.items()}
    plan: dict[Pair, int] = {}
    for lot_key in sorted(data.lots, key=lambda k: (-value_at_risk(k), k)):
        remaining = data.lots[lot_key].qty
        for channel_id in options.get(lot_key, []):
            if remaining == 0:
                break
            qty = min(remaining, left[channel_id]) if capacity_applies else remaining
            if qty <= 0:
                continue
            plan[(lot_key, channel_id)] = qty
            left[channel_id] -= qty
            remaining -= qty
    return plan


def _lines_by_mc(plan: dict[Pair, int]) -> dict[MatChan, list[Pair]]:
    lines: dict[MatChan, list[Pair]] = defaultdict(list)
    for pair in plan:
        lines[(pair[0][0], pair[1])].append(pair)
    return lines


def _trim(data: SolverInput, plan: dict[Pair, int], pairs: list[Pair], excess: int) -> None:
    """Remove `excess` units from the lines with the lowest net value per unit first."""
    for pair in sorted(pairs, key=lambda p: (unit_value(data, p), pair_label(p))):
        if excess <= 0:
            return
        cut = min(plan[pair], excess)
        excess -= cut
        if plan[pair] == cut:
            del plan[pair]
        else:
            plan[pair] -= cut


def _drop_lowest(
    data: SolverInput, plan: dict[Pair, int], lines: dict[MatChan, list[Pair]], keep: int
) -> None:
    """Drop whole SKUs (material, channel) with the lowest net value per unit until `keep` stay."""

    def per_unit(mc: MatChan) -> float:
        units = sum(plan[p] for p in lines[mc])
        return sum(unit_value(data, p) * plan[p] for p in lines[mc]) / units

    for mc in sorted(lines, key=lambda m: (per_unit(m), mc_label(m)))[: max(len(lines) - keep, 0)]:
        for pair in lines[mc]:
            del plan[pair]


def _repair_pass(data: SolverInput, plan: dict[Pair, int]) -> None:
    for mc, pairs in sorted(_lines_by_mc(plan).items()):
        units = sum(plan[p] for p in pairs)
        if units > data.upper[mc]:
            _trim(data, plan, pairs, units - data.upper[mc])
            units = data.upper[mc]
        if 0 < units < data.lower[mc]:
            for pair in pairs:
                plan.pop(pair, None)

    by_mc = _lines_by_mc(plan)
    for (channel_id, group), limit in sorted(data.group_limits.items()):
        in_group = {
            mc: pairs
            for mc, pairs in by_mc.items()
            if mc[1] == channel_id and data.group_of[mc[0]] == group
        }
        _drop_lowest(data, plan, in_group, limit.max_skus)
    by_mc = _lines_by_mc(plan)
    for channel_id, channel in sorted(data.channels.items()):
        in_channel = {mc: pairs for mc, pairs in by_mc.items() if mc[1] == channel_id}
        _drop_lowest(data, plan, in_channel, channel.max_skus)

    by_mc = _lines_by_mc(plan)
    for (channel_id, group), limit in sorted(data.group_limits.items()):
        pairs = [
            p
            for mc, mc_pairs in by_mc.items()
            if mc[1] == channel_id and data.group_of[mc[0]] == group
            for p in mc_pairs
            if p in plan
        ]
        _trim(data, plan, pairs, sum(plan[p] for p in pairs) - limit.max_units)
    for channel_id, channel in sorted(data.channels.items()):
        pairs = [p for p in plan if p[1] == channel_id]
        _trim(data, plan, pairs, sum(plan[p] for p in pairs) - channel.capacity_units)


def repair(data: SolverInput, raw_x: dict[Pair, int]) -> dict[Pair, int]:
    """Deterministic repair to a plan the full checker accepts.

    Lines on eliminated pairs go first. Units above a bound are trimmed from the lowest net value
    per unit. A SKU that falls under its lower bound, or breaks a SKU count limit, is dropped
    whole, lowest net value per unit first. Every change removes units, so the loop ends.
    """
    plan = {p: q for p, q in raw_x.items() if q > 0 and p not in data.dropped}
    for _ in range(MAX_REPAIR_PASSES):
        before = dict(plan)
        _repair_pass(data, plan)
        if not violations(data, Solution(x=plan)):
            return plan
        if plan == before:
            break
    raise RuntimeError("baseline repair did not reach a compliant plan")
