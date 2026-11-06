"""One run of a scenario: optimizer, planner baseline, KPIs, rule trace, top counterfactuals.

Shared by the precompute command and the live API, so both produce the same `ScenarioResult`.
"""

from __future__ import annotations

from reshelf.api_models import (
    ScenarioResult,
    allocation_lines,
    baseline_out,
    counterfactual_out,
    kpi_out,
    solve_out,
    trace_out,
)
from reshelf.baseline import baseline_planner
from reshelf.constraints import Solution
from reshelf.counterfactual import top_counterfactuals
from reshelf.kpis import compute_kpis
from reshelf.solver import PulpSolver, SolveResult
from reshelf.solver_input import SolverInput
from reshelf.stock import stock_out
from reshelf.trace import RuleTrace, build_trace

DEFAULT_TIME_LIMIT_S = 60.0
COUNTERFACTUAL_TIME_LIMIT_S = 10.0


def solution_of(result: SolveResult) -> Solution:
    return Solution(x=result.x, y=result.y, z=result.z)


def solve_and_trace(
    data: SolverInput, time_limit_s: float = DEFAULT_TIME_LIMIT_S
) -> tuple[SolveResult, RuleTrace]:
    """Solve, then trace the plan. A result without a plan gets an empty trace."""
    result = PulpSolver().solve(data, time_limit_s)
    trace = (
        build_trace(data, solution_of(result))
        if result.has_plan
        else RuleTrace(lines=(), binding=(), lines_per_rule={})
    )
    return result, trace


def run_scenario(
    data: SolverInput,
    scenario: str,
    time_limit_s: float = DEFAULT_TIME_LIMIT_S,
    n_counterfactuals: int = 5,
    seed: int | None = None,
    n_skus: int | None = None,
    n_channels: int | None = None,
) -> ScenarioResult:
    result, trace = solve_and_trace(data, time_limit_s)
    counterfactuals = (
        top_counterfactuals(
            data, result, trace, n=n_counterfactuals, time_limit_s=COUNTERFACTUAL_TIME_LIMIT_S
        )
        if result.has_plan
        else []
    )
    return ScenarioResult(
        scenario=scenario,
        seed=seed,
        n_skus=n_skus,
        n_channels=n_channels,
        solve=solve_out(result),
        optimizer=kpi_out(compute_kpis(data, result.x)),
        lines=allocation_lines(data, result.x),
        baseline=baseline_out(data, baseline_planner(data)),
        trace=trace_out(trace),
        counterfactuals=[counterfactual_out(c) for c in counterfactuals],
        stock=stock_out(data, result.x),
    )
