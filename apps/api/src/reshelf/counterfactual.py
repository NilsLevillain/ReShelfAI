"""Counterfactual: what does one binding rule cost, in euro and in units destroyed.

Explainability is a re solve, not a dual (war plan 5.6). One instance of one named rule is relaxed
(`plus_10pct` or `off`), the plan of the original solve warm starts phase 2, and the answer is the
difference in net value and in destroyed units.

The relaxation edits the `SolverInput` bound the rule reads, so the model and the checker see the
same change. Relaxing only widens the feasible set, so the original plan stays feasible and gives
the warm start. The score floor stays the phase 1 optimum of the original solve: the answer is the
value the rule costs at that SKU score, not a new lexicographic optimum.

`supply` is a physical limit, not a rule a planner can relax, so it is not relaxable. The link
constraints are tight by construction and are never traced.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, replace
from typing import Literal, get_args

from reshelf.ids import mc_label
from reshelf.solver import PulpSolver, SolveResult, SolveStatus
from reshelf.solver_input import SolverInput
from reshelf.trace import TRACED_RULES, RuleTrace

Relaxation = Literal["plus_10pct", "off"]
RELAXATIONS: tuple[Relaxation, ...] = get_args(Relaxation)

RELAXABLE_RULES = tuple(name for name in TRACED_RULES if name != "supply")

# A re solve that ends this far under the original plan did not improve it within the limit.
NOISE = 1e-6


@dataclass(frozen=True)
class CounterfactualResult:
    """`cost_eur` is what the rule costs: net value gained when it is relaxed, never negative.

    `units_destroyed_by_rule` is the destroyed units the rule adds, original minus relaxed.
    `status`, `mip_gap`, `time_s` and `time_limit_s` come from the re solve, unchanged.
    """

    constraint: str
    instance: str
    mode: Relaxation
    status: SolveStatus
    cost_eur: float
    units_destroyed_by_rule: int
    base_objective: float
    relaxed_objective: float
    base_destroyed: int
    relaxed_destroyed: int
    mip_gap: float | None
    time_s: float
    time_limit_s: float
    message: str
    plan: SolveResult


def _constraint_of(instance: str) -> str:
    name, bracket, _ = instance.partition("[")
    if not bracket or not instance.endswith("]"):
        raise ValueError(f"{instance!r} is not a rule instance such as cap[OUT_PL]")
    return name


def _more(bound: int, mode: Relaxation, off: int) -> int:
    """Relaxed upper bound: 10 percent more (at least one unit more), or the `off` ceiling."""
    if mode == "off":
        return max(bound, off)
    return max(math.ceil(bound * 1.1 - 1e-9), bound + 1) if bound > 0 else bound


def _less(bound: int, mode: Relaxation) -> int:
    """Relaxed lower bound: 10 percent less, or zero."""
    return 0 if mode == "off" else math.floor(bound * 0.9 + 1e-9)


def relax(data: SolverInput, instance: str, mode: Relaxation) -> SolverInput:
    """The input with one rule instance relaxed. Raises ValueError for an unknown instance."""
    if mode not in RELAXATIONS:
        raise ValueError(f"unknown relaxation {mode!r}, expected one of {RELAXATIONS}")
    name = _constraint_of(instance)
    if name not in RELAXABLE_RULES:
        raise ValueError(f"{name} cannot be relaxed. Relaxable rules: {', '.join(RELAXABLE_RULES)}")
    index = instance[len(name) + 1 : -1]
    total_units = sum(lot.qty for lot in data.lots.values())

    if name in ("cap", "sku"):
        channel = data.channels.get(index)
        if channel is None:
            raise ValueError(f"unknown channel in {instance}")
        if name == "cap":
            update = {"capacity_units": _more(channel.capacity_units, mode, total_units)}
        else:
            update = {"max_skus": _more(channel.max_skus, mode, len(data.lots_of))}
        return replace(data, channels={**data.channels, index: channel.model_copy(update=update)})

    if name in ("asrt", "asrt_units"):
        found = {
            key: limit
            for key, limit in data.group_limits.items()
            if f"{key[1][0]}/{key[1][1]},{key[0]}" == index
        }
        if not found:
            raise ValueError(f"unknown assortment group in {instance}")
        ((key, limit),) = found.items()
        if name == "asrt":
            update = {"max_skus": _more(limit.max_skus, mode, len(data.lots_of))}
        else:
            update = {"max_units": _more(limit.max_units, mode, total_units)}
        return replace(
            data, group_limits={**data.group_limits, key: limit.model_copy(update=update)}
        )

    matches = [mc for mc in data.lots_of if mc_label(mc) == index]
    if not matches:
        raise ValueError(f"unknown SKU and channel in {instance}")
    (mc,) = matches
    if name == "cov_hi":
        return replace(data, upper={**data.upper, mc: _more(data.upper[mc], mode, data.supply[mc])})
    return replace(data, lower={**data.lower, mc: _less(data.lower[mc], mode)})


def counterfactual(
    data: SolverInput,
    base: SolveResult,
    instance: str,
    mode: Relaxation = "plus_10pct",
    solver: PulpSolver | None = None,
    time_limit_s: float | None = None,
) -> CounterfactualResult:
    """Relax `instance`, re solve phase 2 from the plan `base`, report the difference."""
    relaxed_data = relax(data, instance, mode)
    if not base.has_plan:
        raise ValueError("a counterfactual needs the original solve to have a plan")
    solver = solver or PulpSolver()
    relaxed = solver.improve(relaxed_data, base, time_limit_s)

    cost = relaxed.objective - base.objective
    status: SolveStatus = relaxed.status
    message = relaxed.message
    if not relaxed.has_plan:
        cost, kept = 0.0, base
    elif cost < -NOISE:
        # The re solve stopped under the original plan. The original plan is still valid under
        # the relaxed rule, so keep it and say so.
        cost, kept, status = 0.0, base, "feasible"
        message = (
            "The re solve did not beat the original plan within the time limit, "
            "so the cost shown is zero. Raise the time limit to see the full effect."
        )
    else:
        cost, kept = max(cost, 0.0), relaxed
    return CounterfactualResult(
        constraint=_constraint_of(instance),
        instance=instance,
        mode=mode,
        status=status,
        cost_eur=cost,
        units_destroyed_by_rule=base.units_destroyed - kept.units_destroyed,
        base_objective=base.objective,
        relaxed_objective=kept.objective,
        base_destroyed=base.units_destroyed,
        relaxed_destroyed=kept.units_destroyed,
        mip_gap=relaxed.mip_gap,
        time_s=relaxed.time_s,
        time_limit_s=relaxed.time_limit_s,
        message=message,
        plan=kept,
    )


def rank_binding_rules(trace: RuleTrace) -> list[tuple[str, int]]:
    """Relaxable binding instances, most lines first, ties by name. Pairs of (instance, lines)."""
    counts = Counter(
        rule.instance
        for line in trace.lines
        for rule in line.binding
        if rule.constraint in RELAXABLE_RULES
    )
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def top_counterfactuals(
    data: SolverInput,
    base: SolveResult,
    trace: RuleTrace,
    n: int = 5,
    modes: tuple[Relaxation, ...] = RELAXATIONS,
    solver: PulpSolver | None = None,
    time_limit_s: float | None = None,
) -> list[CounterfactualResult]:
    """Counterfactuals of the `n` binding rules that touch most lines, for the precompute."""
    solver = solver or PulpSolver()
    return [
        counterfactual(data, base, instance, mode, solver, time_limit_s)
        for instance, _ in rank_binding_rules(trace)[:n]
        for mode in modes
    ]
