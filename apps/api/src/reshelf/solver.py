"""Solver protocol, result type and the PuLP implementation (HiGHS default, CBC fallback).

Two phase lexicographic objective (war plan 5.5):
  phase 1 maximizes the SKU score, giving S*;
  phase 2 keeps the score at or above (1 - epsilon) * S* and maximizes net value.
Units not allocated count as destroyed.

The empty plan is always feasible: with z = 0 every coverage and push row is switched off (tight
form, ADR 004). A rule set that cannot be met therefore shows up as a plan that leaves units
destroyed, not as an infeasible model. `infeasible` stays in the status list as a guard.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Literal, Protocol

import pulp

from reshelf.ids import MatChan, Pair
from reshelf.model import Model, build_model
from reshelf.solver_input import SolverInput

SolveStatus = Literal["optimal", "feasible", "infeasible", "time_limit", "error"]

# Phase 2 may not undercut S* by more than epsilon. The small slack keeps epsilon = 0 from
# turning solver rounding noise into an infeasible model.
SCORE_SLACK = 1e-6


@dataclass(frozen=True)
class SolveResult:
    """What the API returns unchanged.

    `objective` is the net value in euro of the plan, `score` its SKU score, `best_score` the
    phase 1 optimum S*. `mip_gap` is the relative gap of the last phase solved, None when the
    backend does not report one.
    """

    status: SolveStatus
    objective: float
    score: float
    best_score: float
    mip_gap: float | None
    time_s: float
    time_limit_s: float
    solver: str
    message: str
    x: dict[Pair, int]
    y: dict[Pair, bool]
    z: dict[MatChan, bool]
    units_allocated: int
    units_destroyed: int

    @property
    def has_plan(self) -> bool:
        return self.status in ("optimal", "feasible")


class Solver(Protocol):
    def solve(self, data: SolverInput, time_limit_s: float | None = None) -> SolveResult: ...


@dataclass(frozen=True)
class _Phase:
    status: SolveStatus
    gap: float | None
    has_solution: bool


def _highs_available() -> bool:
    try:
        return bool(pulp.HiGHS().available())
    except Exception:  # any import or load failure means HiGHS cannot be used
        return False


def explain(status: SolveStatus, time_limit_s: float) -> str:
    """Plain sentence for a result that is not proven optimal. Empty for optimal."""
    if status == "optimal":
        return ""
    if status == "feasible":
        return (
            f"The solver reached the time limit of {time_limit_s:g} s with a valid plan "
            "that is not proven optimal. Raise the time limit or relax a rule to close the gap."
        )
    if status == "time_limit":
        return (
            f"The solver reached the time limit of {time_limit_s:g} s before it found any plan. "
            "Raise the time limit or reduce the number of SKUs or channels."
        )
    if status == "infeasible":
        return (
            "No plan satisfies every rule. The most likely cause is two rules that contradict "
            "each other, for example a push quantity above the channel capacity."
        )
    return "The solver stopped with an error and returned no plan."


class PulpSolver:
    """HiGHS by default. With `backend="cbc"`, or when HiGHS cannot load, CBC."""

    def __init__(self, backend: Literal["highs", "cbc"] = "highs") -> None:
        self.backend = backend

    def _backend_name(self) -> Literal["highs", "cbc"]:
        if self.backend == "highs" and not _highs_available():
            return "cbc"
        return self.backend

    def _run(
        self, model: Model, backend: str, limit_s: float, warm: bool, phase_gap: float
    ) -> _Phase:
        problem = model.problem
        if backend == "highs":
            solver = pulp.HiGHS(
                msg=False,
                timeLimit=limit_s,
                gapRel=phase_gap,
                threads=1,
                warmStart=warm,
                random_seed=0,
            )
        else:
            # No warm start: CBC on Windows only honors it with keepFiles, which leaves files behind.
            solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=limit_s, gapRel=phase_gap, threads=1)
        try:
            problem.solve(solver)
        except pulp.PulpSolverError:
            return _Phase("error", None, False)
        if backend == "highs":
            return _read_highs(problem)
        return _read_cbc(problem)

    def solve(self, data: SolverInput, time_limit_s: float | None = None) -> SolveResult:
        limit = time_limit_s if time_limit_s is not None else data.params.solver_time_limit_s
        backend = self._backend_name()
        started = time.perf_counter()
        supply = sum(lot.qty for lot in data.lots.values())

        def elapsed() -> float:
            return time.perf_counter() - started

        def result(
            status: SolveStatus, model: Model | None, best: float, gap: float | None
        ) -> SolveResult:
            x: dict[Pair, int] = {}
            y: dict[Pair, bool] = {}
            z: dict[MatChan, bool] = {}
            if model is not None and status in ("optimal", "feasible"):
                x = {p: round(v.value() or 0) for p, v in model.x.items()}
                x = {p: q for p, q in x.items() if q > 0}
                y = {p: p in x for p in model.x}
                z = {mc: any((lot, mc[1]) in x for lot in data.lots_of[mc]) for mc in model.z}
            allocated = sum(x.values())
            return SolveResult(
                status=status,
                objective=sum(data.net_value[p] * q for p, q in x.items()),
                score=sum(data.score[mc] for mc, on in z.items() if on),
                best_score=best,
                mip_gap=gap,
                time_s=elapsed(),
                time_limit_s=limit,
                solver=backend,
                message=explain(status, limit),
                x=x,
                y=y,
                z=z,
                units_allocated=allocated,
                units_destroyed=supply - allocated,
            )

        if not data.admissible:
            return result("optimal", None, 0.0, 0.0)

        model = build_model(data)

        model.problem.setObjective(model.score_expr())
        phase1 = self._run(model, backend, limit, warm=False, phase_gap=1e-6)
        if not phase1.has_solution:
            return result(phase1.status if phase1.status != "optimal" else "error", None, 0.0, None)
        best = pulp.value(model.score_expr()) or 0.0

        remaining = limit - elapsed()
        if remaining <= 0:
            # Phase 1 used the whole budget. Its plan is valid, its value was not optimized.
            return result("feasible", model, best, None)
        model.problem.setObjective(model.value_expr())
        # Not a registry row: it ties phase 2 to phase 1 and exists only inside the solver.
        model.problem += (
            model.score_expr() >= (1 - data.params.epsilon) * best - SCORE_SLACK,
            "phase1_score",
        )
        phase2 = self._run(model, backend, remaining, warm=True, phase_gap=1e-4)
        if not phase2.has_solution:
            # Keep the phase 1 plan: it is valid, only its value was not improved. No value gap.
            return result("feasible", model, best, None)
        status: SolveStatus = (
            "optimal" if phase1.status == "optimal" and phase2.status == "optimal" else "feasible"
        )
        return result(status, model, best, phase2.gap)


def _read_highs(problem: pulp.LpProblem) -> _Phase:
    import highspy

    highs = problem.solverModel
    model_status = highs.getModelStatus()
    info = highs.getInfo()
    has_solution = info.primal_solution_status == 2
    gap = info.mip_gap if has_solution and info.mip_gap < float("inf") else None
    kind = highspy.HighsModelStatus
    if model_status == kind.kOptimal:
        return _Phase("optimal", gap, True)
    if model_status in (kind.kInfeasible, kind.kUnboundedOrInfeasible):
        return _Phase("infeasible", None, False)
    if model_status == kind.kTimeLimit:
        return _Phase("feasible" if has_solution else "time_limit", gap, has_solution)
    return _Phase("error", None, False)


def _read_cbc(problem: pulp.LpProblem) -> _Phase:
    if problem.status == pulp.LpStatusInfeasible:
        return _Phase("infeasible", None, False)
    if problem.sol_status == pulp.LpSolutionOptimal:
        return _Phase("optimal", None, True)
    if problem.sol_status == pulp.LpSolutionIntegerFeasible:
        return _Phase("feasible", None, True)
    if problem.status == pulp.LpStatusNotSolved:
        return _Phase("time_limit", None, False)
    return _Phase("error", None, False)
