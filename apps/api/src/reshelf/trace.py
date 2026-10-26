"""Rule trace: which named rules bind each allocation line, and what blocked the other channels.

Read after a solve. The slack of every instance of every named constraint comes from the full
checker (`constraints.evaluate`), so the trace never disagrees with the audit. An instance is
binding when its slack is at most `BINDING_TOLERANCE`.

The four link constraints are left out. They tie the binary variables to the units and are tight
by construction (a used pair with x = q, an unused pair with x = 0), so they say nothing a planner
can act on. Every other named constraint is traced.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass

from reshelf.constraints import SPECS, ConstraintResult, Solution, evaluate
from reshelf.elimination import Reason
from reshelf.ids import LotKey, Pair, lot_label, mc_label, pair_label
from reshelf.solver_input import SolverInput

BINDING_TOLERANCE = 1e-6

LINK_RULES = frozenset({"link_xy", "link_yx", "link_yz", "link_zy"})
TRACED_RULES = tuple(name for name in SPECS if name not in LINK_RULES)


@dataclass(frozen=True)
class BindingRule:
    """One tight instance, for example cap[OUT_PL] with slack 0."""

    constraint: str  # registry name, for example cap
    instance: str  # for example cap[OUT_PL]
    slack: float


@dataclass(frozen=True)
class BlockedChannel:
    """A channel the lot could not go to, and why (elimination reason codes)."""

    channel: str
    reasons: tuple[Reason, ...]


@dataclass(frozen=True)
class LineTrace:
    line: str  # stable id: lot label, then channel, for example M1/P1/2027-03,C1
    lot: str
    channel: str
    quantity: int
    binding: tuple[BindingRule, ...]
    blocked: tuple[BlockedChannel, ...]


@dataclass(frozen=True)
class RuleTrace:
    lines: tuple[LineTrace, ...]
    binding: tuple[BindingRule, ...]  # every tight traced instance of the plan
    lines_per_rule: dict[str, int]  # registry name to the number of lines it binds

    def line(self, line_id: str) -> LineTrace:
        for item in self.lines:
            if item.line == line_id:
                return item
        raise KeyError(f"no allocation line {line_id}")


def _instances_for(data: SolverInput, pair: Pair) -> list[str]:
    """Instance labels of the traced constraints that involve this line."""
    lot_key, channel = pair
    material = lot_key[0]
    group = data.group_of[material]
    group_label = f"{group[0]}/{group[1]},{channel}"
    mc = mc_label((material, channel))
    lower = "push" if data.classes[(material, channel)] == "NEW" else "cov_lo"
    labels = [
        f"supply[{lot_label(lot_key)}]",
        f"cap[{channel}]",
        f"sku[{channel}]",
        f"cov_hi[{mc}]",
        f"{lower}[{mc}]",
    ]
    if (channel, group) in data.group_limits:
        labels += [f"asrt[{group_label}]", f"asrt_units[{group_label}]"]
    return labels


def build_trace(
    data: SolverInput,
    solution: Solution,
    tolerance: float = BINDING_TOLERANCE,
) -> RuleTrace:
    """Trace an allocation. Works for any plan the checker accepts, optimizer or baseline."""
    tight: dict[str, BindingRule] = {}
    for result in evaluate(data, solution, only=TRACED_RULES):
        if result.slack <= tolerance:
            tight[result.instance] = _binding(result)

    blocked = _blocked_index(data)
    lines: list[LineTrace] = []
    used: set[str] = set()
    for pair in sorted(p for p, qty in solution.x.items() if qty > 0):
        binding = tuple(tight[i] for i in _instances_for(data, pair) if i in tight)
        used.update(rule.instance for rule in binding)
        lines.append(
            LineTrace(
                line=pair_label(pair),
                lot=lot_label(pair[0]),
                channel=pair[1],
                quantity=solution.x[pair],
                binding=binding,
                blocked=tuple(b for b in blocked.get(pair[0], ()) if b.channel != pair[1]),
            )
        )

    counts = Counter(rule.constraint for line in lines for rule in line.binding)
    return RuleTrace(
        lines=tuple(lines),
        binding=tuple(tight[i] for i in sorted(used)),
        lines_per_rule=dict(sorted(counts.items())),
    )


def _binding(result: ConstraintResult) -> BindingRule:
    return BindingRule(result.constraint, result.instance, max(result.slack, 0.0))


def _blocked_index(data: SolverInput) -> dict[LotKey, list[BlockedChannel]]:
    index: dict[LotKey, list[BlockedChannel]] = defaultdict(list)
    for (lot_key, channel), reasons in sorted(data.dropped.items()):
        index[lot_key].append(BlockedChannel(channel, reasons))
    return index
