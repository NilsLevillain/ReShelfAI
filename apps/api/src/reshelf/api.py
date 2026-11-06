"""FastAPI app: scenarios, solve, results, compare, explain and counterfactual (war plan 6.2).

The Excel export belongs to week 5. Every error is a plain sentence in
`detail` with a matching status code, never a stack trace.
"""

from __future__ import annotations

import copy
import os
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Literal

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, sessionmaker

from reshelf.adapters import DatasetError
from reshelf.api_models import (
    CounterfactualOut,
    KpiOut,
    LineTraceOut,
    ScenarioResult,
    counterfactual_out,
)
from reshelf.benchmark import build_world
from reshelf.counterfactual import counterfactual
from reshelf.db import ResultRow, ScenarioRow, make_engine, make_session_factory
from reshelf.pipeline import COUNTERFACTUAL_TIME_LIMIT_S, run_scenario, solve_and_trace
from reshelf.stock import StockLot, StockSummary, filter_lots

REPO_ROOT = Path(__file__).resolve().parents[4]


def scenarios_dir() -> Path:
    return Path(os.environ.get("RESHELF_SCENARIOS", REPO_ROOT / "data" / "scenarios"))


class ScenarioSpec(BaseModel):
    """What it takes to rebuild a world: a seeded base scenario, its size and parameter edits."""

    name: str = Field(min_length=1, max_length=120)
    base: str = "default"
    n_skus: int = Field(default=30, ge=1, le=2000)
    n_channels: int = Field(default=5, ge=1, le=20)
    time_limit_s: float = Field(default=60.0, gt=0, le=600)
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="Edits of the scenario `params` block. Unknown keys are rejected.",
    )


class ScenarioOut(BaseModel):
    id: int
    spec: ScenarioSpec


class StoredResult(BaseModel):
    result_id: int
    scenario_id: int
    result: ScenarioResult


class CounterfactualIn(BaseModel):
    instance: str = Field(description="A binding instance of the line, for example cap[OUT_PL]")
    mode: Literal["plus_10pct", "off"] = "plus_10pct"


class CompareRow(BaseModel):
    scenario_id: int
    name: str
    optimizer: KpiOut
    baseline_compliant: KpiOut
    value_delta_vs_first: float
    value_delta_vs_baseline: float


class CompareOut(BaseModel):
    label: str = "Simulated data"
    comparison: str = "Optimizer against the greedy baseline (compliant plan)"
    rows: list[CompareRow]


def _config(spec: ScenarioSpec) -> dict[str, Any]:
    from reshelf_datagen import load_scenario

    path = scenarios_dir() / f"{spec.base}.yaml"
    if not path.is_file():
        known = sorted(p.stem for p in scenarios_dir().glob("*.yaml"))
        raise HTTPException(404, f"Unknown base scenario {spec.base!r}. Known: {', '.join(known)}.")
    cfg = copy.deepcopy(load_scenario(path))
    unknown = sorted(set(spec.params) - set(cfg["params"]))
    if unknown:
        raise HTTPException(422, f"Unknown parameter(s): {', '.join(unknown)}.")
    cfg["params"].update(spec.params)
    return cfg


def create_app(db_url: str | None = None) -> FastAPI:
    holder: dict[str, sessionmaker[Any]] = {}

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        holder["factory"] = make_session_factory(make_engine(db_url))
        yield

    app = FastAPI(title="Reshelf API", version="0.1.0", lifespan=lifespan)

    def session() -> Iterator[Session]:
        with holder["factory"]() as db:
            yield db

    Db = Depends(session)

    def scenario_row(db: Session, scenario_id: int) -> ScenarioRow:
        row = db.get(ScenarioRow, scenario_id)
        if row is None:
            raise HTTPException(404, f"No scenario with id {scenario_id}.")
        return row

    def latest_result(db: Session, scenario_id: int) -> ResultRow:
        row = (
            db.query(ResultRow)
            .filter(ResultRow.scenario_id == scenario_id)
            .order_by(ResultRow.id.desc())
            .first()
        )
        if row is None:
            raise HTTPException(404, f"Scenario {scenario_id} has no result yet. Solve it first.")
        return row

    def stored(row: ResultRow) -> StoredResult:
        return StoredResult(
            result_id=row.id,
            scenario_id=row.scenario_id,
            result=ScenarioResult.model_validate_json(row.payload),
        )

    @app.exception_handler(DatasetError)
    async def dataset_error(_: Request, exc: DatasetError) -> Any:
        from fastapi.responses import JSONResponse

        return JSONResponse({"detail": f"The scenario data is not valid: {exc}"}, status_code=422)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/scenarios", response_model=ScenarioOut, status_code=201)
    def create_scenario(spec: ScenarioSpec, db: Session = Db) -> ScenarioOut:
        _config(spec)  # validates the base and the parameter names now, not at solve time
        row = ScenarioRow(name=spec.name, spec=spec.model_dump())
        db.add(row)
        db.commit()
        return ScenarioOut(id=row.id, spec=spec)

    @app.post("/scenarios/{scenario_id}/solve", response_model=StoredResult)
    def solve(scenario_id: int, db: Session = Db) -> StoredResult:
        row = scenario_row(db, scenario_id)
        spec = ScenarioSpec(**row.spec)
        cfg = _config(spec)
        data = build_world(cfg, spec.n_skus, spec.n_channels)
        result = run_scenario(
            data,
            spec.name,
            time_limit_s=spec.time_limit_s,
            seed=cfg.get("seed"),
            n_skus=spec.n_skus,
            n_channels=spec.n_channels,
        )
        saved = ResultRow(scenario_id=scenario_id, payload=result.model_dump_json())
        db.add(saved)
        db.commit()
        return stored(saved)

    @app.get("/scenarios/compare", response_model=CompareOut)
    def compare(
        ids: str = Query(description="Comma separated scenario ids"), db: Session = Db
    ) -> CompareOut:
        try:
            wanted = [int(i) for i in ids.split(",") if i.strip()]
        except ValueError:
            raise HTTPException(422, "ids must be whole numbers separated by commas.") from None
        if len(wanted) < 2:
            raise HTTPException(422, "Give at least two scenario ids to compare.")
        rows: list[CompareRow] = []
        first_value = 0.0
        for index, scenario_id in enumerate(wanted):
            current = stored(latest_result(db, scenario_id)).result
            if index == 0:
                first_value = current.optimizer.value_recovered
            rows.append(
                CompareRow(
                    scenario_id=scenario_id,
                    name=scenario_row(db, scenario_id).name,
                    optimizer=current.optimizer,
                    baseline_compliant=current.baseline.compliant,
                    value_delta_vs_first=current.optimizer.value_recovered - first_value,
                    value_delta_vs_baseline=current.optimizer.value_recovered
                    - current.baseline.compliant.value_recovered,
                )
            )
        return CompareOut(rows=rows)

    @app.get("/scenarios/{scenario_id}/results", response_model=StoredResult)
    def results(scenario_id: int, db: Session = Db) -> StoredResult:
        scenario_row(db, scenario_id)
        return stored(latest_result(db, scenario_id))

    @app.get("/stock/summary", response_model=StockSummary)
    def stock_summary_endpoint(
        scenario_id: int = Query(description="Scenario whose latest result carries the stock"),
        db: Session = Db,
    ) -> StockSummary:
        scenario_row(db, scenario_id)
        return stored(latest_result(db, scenario_id)).result.stock.summary

    @app.get("/stock/lots", response_model=list[StockLot])
    def stock_lots_endpoint(
        scenario_id: int = Query(description="Scenario whose latest result carries the stock"),
        brand: str | None = None,
        category: str | None = None,
        reason: str | None = None,
        db: Session = Db,
    ) -> list[StockLot]:
        scenario_row(db, scenario_id)
        lots = stored(latest_result(db, scenario_id)).result.stock.lots
        return filter_lots(lots, brand, category, reason)

    def result_row(db: Session, result_id: int) -> ResultRow:
        row = db.get(ResultRow, result_id)
        if row is None:
            raise HTTPException(404, f"No result with id {result_id}.")
        return row

    def line_trace(result: ScenarioResult, line: str) -> LineTraceOut:
        for item in result.trace.lines:
            if item.line == line:
                return item
        raise HTTPException(404, f"No allocation line {line!r} in this result.")

    @app.get("/results/{result_id}/lines/{line:path}/explain", response_model=LineTraceOut)
    def explain(result_id: int, line: str, db: Session = Db) -> LineTraceOut:
        return line_trace(stored(result_row(db, result_id)).result, line)

    @app.post(
        "/results/{result_id}/lines/{line:path}/counterfactual", response_model=CounterfactualOut
    )
    def what_if(
        result_id: int, line: str, body: CounterfactualIn, db: Session = Db
    ) -> CounterfactualOut:
        row = result_row(db, result_id)
        item = line_trace(stored(row).result, line)
        if body.instance not in {b.instance for b in item.binding}:
            raise HTTPException(
                422, f"{body.instance!r} does not bind this line. Choose one of its binding rules."
            )
        spec = ScenarioSpec(**scenario_row(db, row.scenario_id).spec)
        data = build_world(_config(spec), spec.n_skus, spec.n_channels)
        # The world is seeded, so this solve reproduces the stored plan, and the re solve starts from it.
        base, _ = solve_and_trace(data, spec.time_limit_s)
        try:
            found = counterfactual(
                data, base, body.instance, body.mode, time_limit_s=COUNTERFACTUAL_TIME_LIMIT_S
            )
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        return counterfactual_out(found)

    return app
