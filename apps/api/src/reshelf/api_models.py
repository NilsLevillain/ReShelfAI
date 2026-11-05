"""Response models of the API and the precomputed JSON (one contract for both).

Pydantic v2 models with converters from the solver dataclasses. Plain dicts keyed by tuples cannot
be written as JSON, so every allocation line carries a stable string id (`lot label,channel`, the
id used by the trace). Solver fields are passed on unchanged: status, objective, MIP gap, time and
time limit.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from reshelf.baseline import BaselineResult
from reshelf.counterfactual import CounterfactualResult
from reshelf.ids import Pair, lot_label, pair_label
from reshelf.kpis import Kpis, unit_value
from reshelf.solver import SolveResult
from reshelf.solver_input import SolverInput
from reshelf.trace import LineTrace, RuleTrace


class KpiOut(BaseModel):
    value_recovered: float
    units_allocated: int
    units_destroyed: int
    brand_risk_index: float
    skus_per_channel: dict[str, int]
    fill_rate: dict[str, float]
    score: float


class SolveOut(BaseModel):
    status: str
    objective: float
    score: float
    best_score: float
    mip_gap: float | None
    time_s: float
    time_limit_s: float
    solver: str
    message: str


class AllocationLine(BaseModel):
    line: str = Field(description="lot label, then channel, for example M1/P1/2027-03,C1")
    lot: str
    channel: str
    quantity: int
    lot_supply: int
    net_value_eur: float


class AuditLineOut(BaseModel):
    count: int
    excess: int


class BaselineOut(BaseModel):
    """The greedy planner proxy: raw plan, what the checker found, and the compliant plan."""

    raw: KpiOut
    audit: dict[str, AuditLineOut]
    compliant: KpiOut
    compliant_lines: list[AllocationLine]


class BindingRuleOut(BaseModel):
    constraint: str
    instance: str
    slack: float


class BlockedChannelOut(BaseModel):
    channel: str
    reasons: list[str]


class LineTraceOut(BaseModel):
    line: str
    lot: str
    channel: str
    quantity: int
    binding: list[BindingRuleOut]
    blocked: list[BlockedChannelOut]


class TraceOut(BaseModel):
    lines: list[LineTraceOut]
    binding: list[BindingRuleOut]
    lines_per_rule: dict[str, int]


class CounterfactualOut(BaseModel):
    """Lead with `cost_eur`: `units_destroyed_by_rule` can be negative (ADR 007)."""

    constraint: str
    instance: str
    mode: str
    status: str
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


class ScenarioResult(BaseModel):
    """Everything a results screen needs, from one source."""

    scenario: str
    seed: int | None = None
    n_skus: int | None = None
    n_channels: int | None = None
    label: str = "Simulated data"
    solve: SolveOut
    optimizer: KpiOut
    lines: list[AllocationLine]
    baseline: BaselineOut
    trace: TraceOut
    counterfactuals: list[CounterfactualOut]


def kpi_out(kpis: Kpis) -> KpiOut:
    return KpiOut(
        value_recovered=kpis.value_recovered,
        units_allocated=kpis.units_allocated,
        units_destroyed=kpis.units_destroyed,
        brand_risk_index=kpis.brand_risk_index,
        skus_per_channel=dict(kpis.skus_per_channel),
        fill_rate=dict(kpis.fill_rate),
        score=kpis.score,
    )


def solve_out(result: SolveResult) -> SolveOut:
    return SolveOut(
        status=result.status,
        objective=result.objective,
        score=result.score,
        best_score=result.best_score,
        mip_gap=result.mip_gap,
        time_s=result.time_s,
        time_limit_s=result.time_limit_s,
        solver=result.solver,
        message=result.message,
    )


def allocation_lines(data: SolverInput, x: dict[Pair, int]) -> list[AllocationLine]:
    return [
        AllocationLine(
            line=pair_label(pair),
            lot=lot_label(pair[0]),
            channel=pair[1],
            quantity=units,
            lot_supply=data.lots[pair[0]].qty,
            net_value_eur=unit_value(data, pair) * units,
        )
        for pair, units in sorted(x.items())
        if units > 0
    ]


def baseline_out(data: SolverInput, baseline: BaselineResult) -> BaselineOut:
    return BaselineOut(
        raw=kpi_out(baseline.raw),
        audit={k: AuditLineOut(count=v.count, excess=v.excess) for k, v in baseline.audit.items()},
        compliant=kpi_out(baseline.compliant),
        compliant_lines=allocation_lines(data, baseline.compliant_x),
    )


def line_trace_out(item: LineTrace) -> LineTraceOut:
    return LineTraceOut(
        line=item.line,
        lot=item.lot,
        channel=item.channel,
        quantity=item.quantity,
        binding=[BindingRuleOut(**vars(b)) for b in item.binding],
        blocked=[
            BlockedChannelOut(channel=b.channel, reasons=list(b.reasons)) for b in item.blocked
        ],
    )


def trace_out(trace: RuleTrace) -> TraceOut:
    return TraceOut(
        lines=[line_trace_out(line) for line in trace.lines],
        binding=[BindingRuleOut(**vars(b)) for b in trace.binding],
        lines_per_rule=dict(trace.lines_per_rule),
    )


def counterfactual_out(result: CounterfactualResult) -> CounterfactualOut:
    return CounterfactualOut(
        constraint=result.constraint,
        instance=result.instance,
        mode=result.mode,
        status=result.status,
        cost_eur=result.cost_eur,
        units_destroyed_by_rule=result.units_destroyed_by_rule,
        base_objective=result.base_objective,
        relaxed_objective=result.relaxed_objective,
        base_destroyed=result.base_destroyed,
        relaxed_destroyed=result.relaxed_destroyed,
        mip_gap=result.mip_gap,
        time_s=result.time_s,
        time_limit_s=result.time_limit_s,
        message=result.message,
    )
