# Reshelf

Tighten a rule. See what it costs. See why.

Reshelf allocates stock that cannot sell through primary retail (near expiry, discontinued, overproduction) to second life channels, under business rules, and explains each decision. It is a portfolio demo. All data is simulated by a seeded generator for an invented company, "Kestrel Beauty Group". Every KPI is shown against a greedy baseline, and none of it claims real business impact. Code is all rights reserved.

## Hero flow
1. Open the results of a scenario. The optimizer plan sits next to a greedy planner baseline.
2. Open the Why panel on a line. It shows the binding rules, the channels blocked by elimination (with reason codes) and the euro cost of relaxing a rule.
3. Change a rule on the Parameters page, run the solver, compare.

## How to read Reshelf (for planners)
The goal is a plan the brand can accept, so that stock is not destroyed. Comparing plans is only a means.

1. **Stock.** The lots that cannot sell the normal way, with the value at risk. No plan is applied yet. The globe and the tables show where the stock sits, by country and by plant.
2. **Rules and run.** Change the rules, review what you changed, run the plan. Every number has an info button that says what it does, what happens if you raise or lower it, and how to choose a value. The same words are on the Glossary page.
3. **Plan.** The result, with one panel you should read first: **Why is stock destroyed?** It splits every unit that is not placed into one cause, and each cause has a button to the rule that moves it.
4. **Compare.** Two scenarios side by side. Each change has an arrow and the word better or worse, and one sentence says what changed from A to B.

What moves the destruction in the demo world (30 SKUs, 5 channels, default rules):

| Cause | Share of destroyed units | What a planner can change |
|---|---|---|
| Channels already hold enough stock (coverage ceiling) | 68 percent | Days of sales a channel should hold |
| New products stop at their push quantity | 29 percent | Push quantity for new products |
| No channel accepts these lots | 1 percent | Shelf life, brand tier and push rules of the world |
| Channels are full in number of products | 1 percent | Channel limit on products |
| Not worth sending | 1 percent | Nothing to change, the brand cost is higher than the price |

Ready made scenarios (same stock, other rules): **Default**, **Luxury protection** (luxury is never discounted, small cost because little luxury stock is placed), **Max recovery** (180 days of sales and twice the push quantity, about three times the units placed) and **Strict shelf life** (channels ask for 30 more points of shelf life, so more is refused at the door).

**Brand risk index.** For every euro of stock cost the plan sends out, the part that counts as brand image cost. Lower is better. It is a ratio, so it can fall when a plan places more low risk stock even if the total brand cost grows.

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
* Every unit that is not placed gets one cause (coverage ceiling, push ceiling, channel limits and so on), see ADR 010.

## Run it
Python 3.11 or newer and uv, Node 20 and pnpm 9.

```
cd apps/api && uv sync --all-extras && PYTHONPATH=../../data/generator uv run uvicorn main:app --port 8000   # on Windows with OneDrive first: export UV_LINK_MODE=copy
cd apps/web && pnpm install && pnpm dev
```
The app shows cached results from `data/precomputed/*.json`. Set `VITE_API_URL=/api` in `apps/web/.env.local` (plain UTF-8, the dev server proxies `/api` to the API on port 8000) to use the live solver and the parameter editor. Banner text says "Cached results" or "Live solver".

With Docker (web on http://localhost:8080, API on http://localhost:8000):
```
docker compose -f infra/docker-compose.yml up --build
```
See ADR 009 for the deployment shape. Nothing is deployed yet.

## Tests and checks
* API, from `apps/api`: `uv run pytest -q -m "not slow"`, `uv run ruff check . ../../data/generator`, `uv run mypy . ../../data/generator`. The slow 50 seed property test runs in CI.
* Web, from `apps/web`: `pnpm type-check`, `pnpm lint`, `pnpm exec vitest run`, `pnpm build`.
* End to end: `pnpm exec playwright test` (one hero flow test, always on cached results, whatever `.env.local` says). Set `PW_CHANNEL=msedge` if the Chromium download is blocked. CI does not run it yet.
* Design system audit, from the repo root: `node design_system/scripts/audit.mjs`. It fails when a page uses an unknown `rs-` class, a raw color, an inline style, a pixel value or a raw currency format. CI runs it.
* Regenerate cached results with `make precompute`. After an API change run `uv run python scripts/dump_openapi.py` then `pnpm gen:api`.

## Documents
* `docs/war_plan.md`: execution plan and architecture.
* `docs/adr/`: decisions (ADR 010: why a unit is destroyed). The Glossary page of the app lists every word. `docs/model.md`: constraint model. `docs/benchmark.md`: partial benchmark. `docs/erd.md`, `docs/mapping.md`: data.
* `product_management/`: discovery, strategy, metrics. `design_system/`: tokens and components.
* `progress.md`: status and open points.

## Status
Weeks 0 to 7 of the plan are built (week 7 without a live deploy of the app, only the product recap goes to GitHub Pages), plus three UX batches. Batch 3 (2026-11-17) added the glossary and tooltips, the destruction causes, four scenarios, a compare page that reads as a story, globe numbers, a result cache and the design system audit. The demo video (week 8) is not made. Known gaps: no deep dive page, partial benchmark, Docker images only built in CI, no database migrations.
