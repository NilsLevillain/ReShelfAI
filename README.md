# Reshelf

Tighten a rule. See what it costs. See why.

Reshelf allocates stock that cannot sell through primary retail (near expiry, discontinued, overproduction) to second life channels, under business rules, and explains each decision. It is a portfolio demo. All data is simulated by a seeded generator for an invented company, "Kestrel Beauty Group". Every KPI is shown against a greedy baseline, and none of it claims real business impact. Code is all rights reserved.

## Hero flow
1. Open the results of a scenario. The optimizer plan sits next to a greedy planner baseline.
2. Open the Why panel on a line. It shows the binding rules, the channels blocked by elimination (with reason codes) and the euro cost of relaxing a rule.
3. Change a rule on the Parameters page, run the solver, compare.

## How it works
```
Source tables (SAP style CSV or Parquet) -> SourceAdapter -> Canonical dataset -> Solver input
                                                                                     |
                                    elimination (reason codes) -> MILP (HiGHS, two phase objective)
                                                                                     |
                               KPIs, rule trace, counterfactual re solve -> FastAPI -> React app
```
* Decision index is the lot (material, plant, expiry month), see ADR 003.
* Two phase objective: maximize SKU score, then net value with phase 1 held within 1 percent.
* Explanations are a rule trace plus an on demand counterfactual re solve, see ADR 007.
* The baseline is a planner proxy audited by the full constraint checker, see ADR 005.
* The model is documented from code in `docs/model.md` and CI fails on drift.

## Run it
Python 3.11 or newer and uv, Node 20 and pnpm 9.

```
cd apps/api && uv sync --all-extras && uv run uvicorn main:app --port 8000
cd apps/web && pnpm install && pnpm dev
```
The app shows cached results from `data/precomputed/*.json`. Set `VITE_API_URL=http://localhost:8000` in `apps/web/.env.local` to use the live solver and the parameter editor. Banner text says "Cached results" or "Live solver".

With Docker (web on http://localhost:8080, API on http://localhost:8000):
```
docker compose -f infra/docker-compose.yml up --build
```
See ADR 009 for the deployment shape. Nothing is deployed yet.

## Tests and checks
* API, from `apps/api`: `uv run pytest -q -m "not slow"`, `uv run ruff check . ../../data/generator`, `uv run mypy . ../../data/generator`. The slow 50 seed property test runs in CI.
* Web, from `apps/web`: `pnpm type-check`, `pnpm lint`, `pnpm exec vitest run`, `pnpm build`.
* End to end: `pnpm exec playwright test` (one hero flow test). Set `PW_CHANNEL=msedge` if the Chromium download is blocked.
* Regenerate cached results with `make precompute`. After an API change run `uv run python scripts/dump_openapi.py` then `pnpm gen:api`.

## Documents
* `docs/war_plan.md`: execution plan and architecture.
* `docs/adr/`: decisions. `docs/model.md`: constraint model. `docs/benchmark.md`: partial benchmark. `docs/erd.md`, `docs/mapping.md`: data.
* `product_management/`: discovery, strategy, metrics. `design_system/`: tokens and components.
* `progress.md`: status and open points.

## Status
Weeks 0 to 7 of the plan are built (week 7 without a live deploy). The demo video (week 8) is not made. Known gaps: no deep dive page, partial benchmark, Docker images only built in CI, no database migrations.
