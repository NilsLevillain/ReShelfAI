# Progress

Last updated: 2026-11-06 (week 4 built, slices 1 to 3 committed). Source of truth for the schedule is `docs/war_plan.md` section 7.

## Status at a glance

| Week | Scope | Status |
|---|---|---|
| 0 | Repo, tooling, ADR 001, CI | Done |
| 1 | ERD, mapping, rule defaults, seeded generator, 50 neutral seeds | Done |
| Design system and product management | Tokens, spec, discovery, strategy, metrics | Done |
| 2, slice 1 | Canonical schema, CsvAdapter | Done (`5b0e297`) |
| 2, slice 2 | Elimination, solver input, constraint registry and checker, ADR 003 and 004 | Done (`4bf9ea8`) |
| 2, slice 3 | Solver core, ADR 006 | Done (`04946d9`) |
| 2, slice 4 | KPIs, baseline, seed property test, Parquet adapter | Done (`0171d6d`, `e470b6b`). Tuning skipped and `baseline_expert` not built, see "Left from week 2" |
| 3, slice 1 | Rule trace, generated `docs/model.md` and CI drift check | Done (`c3ad521`, `7e00215`) |
| 3, slice 2 | Counterfactual re solve, ADR 007 | Done (`a049078`) |
| 3, slice 3 | Benchmark | Code and tests done (`3ec266d`). Full run skipped on purpose (see "Week 3, slice 3"), `docs/benchmark.md` not written |
| 3, slice 4 | Response models, precompute, scenario and results API, ADR 008 | Done (commits after `5973d55`). Stock endpoints go to week 4, Excel export to week 5 |
| 4 | Web shell, stock endpoints and overview, hero slice on precomputed JSON | Done (`edf98b8`, `55258af`, `7eac9eb`). Not checked in a browser, see "Week 4 built" |
| 5 to 8 | Parameter editor, Docker, video | Not started |

Test state after week 3 slice 2: 236 fast tests green in about 25 s (`-m "not slow"`), ruff and mypy strict clean. The slow 50 seed test was not rerun since slice 4 (the solver change is a refactor, `solve` behavior is unchanged and `test_solver.py` passes). Earlier, slice 4: 246 tests in about 3.5 minutes. The 50 seed test is marked `slow` (`-m "not slow"` skips it, CI runs everything). Commits are local, not pushed.

## Done

### Weeks 0 and 1
* Repo, uv tooling, CI, ADR 001 (stack), ADR 005 (planner proxy baseline).
* `docs/erd.md`, `docs/mapping.md`, glossary, war plan, test scenarios (`product_management/3_execution/2_test_scenarios.md`).
* Seeded generator (`data/generator/reshelf_datagen`), scenarios `default`, `luxury_protection`, 50 neutral seeds, distribution tests.

### Week 2, slice 1: schema and CsvAdapter
* `apps/api/src/reshelf/schema.py`: Pydantic entities (`Material`, `Plant`, `Lot`, `Channel`, `ChannelRule`, `GroupLimit`, `Demand`, `Abc`, `Params`, `CanonicalDataset`) with validation and a referential integrity check.
* `adapters/`: `SourceAdapter` Protocol, `DatasetError`, pandera source schemas, SAP mapping (`sap.py`, the only module that knows SAP names), `CsvAdapter`.
* Data changes: `ZCHANNEL.TRANSITD` (transit days per channel), `ZPARAM.AS_OF`, push quantity per product category (Fragrance 5, Skincare 30, Makeup 30, Haircare 50).
* Dependencies added: pandas, pandera, highspy, pandas-stubs, hypothesis.

### Week 2, slice 2: elimination, solver input, constraints
* `ZCHSTOCK` (on hand and in transit stock at the second life channel) replaces `ZSELLIN`. Generator, adapter, docs updated.
* `elimination.py`: reason codes `RSL`, `TIER`, `NO_PUSH`. Remaining shelf life measured at `as_of` plus channel transit days.
* `scoring.py`: class per (material, channel). No sellout history in the channel means NEW. Score `base[class] + rank_weight * (1 - rank / N)`.
* `solver_input.py`: coverage need D (delivery month seasonality, minus on hand and in transit), bounds `upper` and `lower`, supply per pair, net value per unit, group limits. Rejects anything but a `CanonicalDataset`.
* `constraints.py`: registry of 12 named constraints (the 11 of the war plan plus `link_yx`), `evaluate` with slack per instance, `violations`, planner rule filter.
* ADR 003 (lot decision index), ADR 004 (tight form). War plan sections 5.3 and 5.4 and the test scenario table updated.

### Week 2, slice 3: solver core
* `model.py`: MILP built from the registry, one builder per constraint name, rows kept by registry label.
* `solver.py`: `Solver` Protocol, `SolveResult`, `PulpSolver` (HiGHS default, CBC fallback), two phase objective, plain sentences for results that are not optimal.
* PuLP pinned to `>=3.3,<4`: the lock held 3.3.2 and 4.2.0 with different APIs (ADR 006).
* Tests: TS-030 to 039, 040 to 054, 206 (hypothesis, 40 random worlds). The checker audits every plan.
* Measured once: 300 SKUs, 4 channels, 1,200 admissible pairs, HiGHS optimal in about 8 s.

### Week 2, slice 4: KPIs, baseline, seeds, Parquet
Code:
* `kpis.py`: `compute_kpis` returns value recovered, units allocated and destroyed, brand risk index (penalty over unit cost, 0 when empty), SKUs per channel, fill rate per channel, score. One function for the optimizer plan, the raw baseline and the compliant baseline. Value is read from lots and channel rules, not from `SolverInput.net_value`, because a raw baseline plan can use pairs that elimination dropped.
* `baseline.py`:
  * `plan_by_hand`: lots sorted by value at risk, each sent to the planner admissible channel with the best recovery factor that still has capacity, split over channels when capacity runs out. Ties break on ids, so the plan is deterministic.
  * Planner admissible pairs are the solver's admissible pairs plus pairs dropped only by a rule the planner does not apply (default: `NO_PUSH`).
  * `audit`: count and excess per named constraint, from the full checker.
  * `repair`: deterministic, loops until the full checker accepts the plan.
  * `baseline_planner`: raw plan, raw KPIs, audit, compliant plan, compliant KPIs.
* `adapters/parquet.py` and `adapters/folder.py` (loader shared with `CsvAdapter`). `pyarrow` added. Parquet frames are cast to text before the SAP mapping, so both paths feed the same frames.
* `pyproject.toml`: `slow` pytest marker registered.

Tests:
* `test_kpis.py`: TS-048, 049, 070 to 074 on a hand built three line plan.
* `test_baseline.py`: TS-060 to 064 and 069 (order and capacity, rules not applied, assortment audit, clean plan has equal raw and compliant value, repair is deterministic and passes the checker, coverage trim, lower bound drop, all lots eliminated).
* `test_baseline_property.py`: TS-066 (ADR 005 on the 50 neutral seeds). Per seed: status optimal, compliant baseline and optimizer plans pass the full checker, optimizer score at least the compliant baseline score, and optimizer net value at least the baseline value when the baseline score is within epsilon of the optimizer's, up to the reported MIP gap. All 50 pass.
* `test_parquet_adapter.py`: TS-018 parity with CSV, with all text columns and with integer columns stored as integers. Missing folder and missing table are reported.

Docs:
* ADR 005 has an "Implementation notes" section (urgency, repair, audit unit, property test size).

Measured (throwaway script in `tmp/`, not committed):

| World | Result |
|---|---|
| 50 seeds, 20 SKUs | Optimizer optimal on all. Value against compliant baseline: median 2.6 times, minimum 1.56 times, maximum 68 times |
| 4 seeds, 40 SKUs, scaled SKU limits | Optimal in 4 to 15 s. Optimizer score about 150, compliant baseline about 40 |
| 4 seeds, 30 SKUs, unscaled SKU limits | One solve hit the 60 s limit. Others 10 to 53 s |
| 3 seeds, 150 SKUs | Two of three hit the 60 s limit (status feasible). On one seed phase 1 returned a score of 0 |

Raw baseline plans break many rules: about 60 to 80 violated instances per world at 40 SKUs.

### Week 3, slice 1: rule trace and model doc
* `trace.py`: `build_trace(data, solution, tolerance=1e-6)` returns a `RuleTrace`. Per allocation line: binding instances with slack, and channels blocked by elimination with their reason codes. Works on any plan, optimizer or baseline. Line id is `lot label,channel`.
* The four link constraints are not traced. They are tight by construction and carry no planner meaning (my call).
* `ConstraintSpec.reads` names the source table or parameter of each bound. `model_doc.py` renders `docs/model.md` from the registry. `make model-doc` writes it, `python -m reshelf.model_doc --check` fails on drift and runs in CI (python job).
* Tests: `test_trace.py` (one binding case per traced constraint, tolerance, blocked reasons, solved plan), `test_model_doc.py`. 217 fast tests green, ruff and mypy clean. The 50 seed test was not rerun.

### Week 3, slice 2: counterfactual
* `PulpSolver.improve(data, start, time_limit_s)`: phase 2 only, warm started from a plan, score floor is the original S*. The result builder moved out of `solve` into `_result`, shared by both.
* `counterfactual.py`:
  * `relax(data, instance, mode)` edits the `SolverInput` bound of one instance (`cap`, `sku`, `asrt`, `asrt_units`, `cov_hi`, `cov_lo`, `push`). Modes `plus_10pct` and `off`. `supply` and link rules raise a `ValueError`.
  * `counterfactual(...)` returns `CounterfactualResult`: euro cost, units destroyed by the rule, base and relaxed objective, status, MIP gap, time and limit, plain message, the plan.
  * `rank_binding_rules(trace)` and `top_counterfactuals(...)` for the precompute (slice 4).
* ADR 007 records the choices. `tests/test_counterfactual.py`: 19 tests with exact euro and unit answers per rule, input not mutated, relaxed and original plan pass the checker, limit hit under the original plan, re solve without a plan, determinism, ranking.
* Measured once (throwaway `tmp/cf_smoke.py`, 30 SKUs, scaled SKU limits, seed 0): base solve 3.8 s optimal. Top four binding rules were all `sku[...]` of liquidation and clearance channels. Re solves took 1 to 5 s, all optimal. Costs: `plus_10pct` about 1,200 to 1,750 euro, `off` about 3,500 to 4,300 euro, on a plan worth about 201,000 euro.

### Week 3, slice 3: benchmark
* `benchmark.py`: `python -m reshelf.benchmark` solves the default scenario at chosen SKU and channel counts with HiGHS and CBC, audits each plan with the full checker, writes `docs/benchmark.md`. Rows are appended to `tmp/benchmark_rows.jsonl` (checkpoint), so a killed run resumes.
* `tests/test_benchmark.py`: channel picking, scaling of `max_skus`, render, scale smoke test (30 SKUs, both backends), checkpoint resume. 7 tests green.
* Partial results in the checkpoint (60 s limit, one thread): 300 SKUs x 5 channels HiGHS optimal in 18 s, CBC optimal in 2.4 s. 300 x 20 HiGHS optimal in 40 s. All with 0 violations.
* The full run was stopped by the system for low memory on the first new row (300 x 20 CBC). Nils decided on 2026-11-05 to skip the benchmark for now. `docs/benchmark.md` does not exist. The war plan names it in the README, so write it before week 7. Cut order puts the 10k row first.
* CBC was faster than HiGHS on both 300 SKU worlds. Worth a look before the demo picks a default backend.

### Week 3, slice 4: contract, precompute, API
* `api_models.py`: Pydantic `ScenarioResult` (solve, optimizer KPIs, lines, baseline raw, audit and compliant, trace, counterfactuals) with converters from the solver dataclasses. `pipeline.py`: `run_scenario`, shared by precompute and API.
* `precompute.py` (`make precompute`): writes `data/precomputed/default.json` and `luxury_protection.json` on a 30 SKU, 5 channel world. Both solved to optimal in under a second, with 10 counterfactuals each (5 rules, 2 modes). Rerun gives identical output apart from `time_s`.
* `db.py` and `api.py`: SQLite persistence, endpoints `POST /scenarios`, `POST /scenarios/{id}/solve`, `GET /scenarios/{id}/results`, `GET /scenarios/compare?ids=`, `GET /results/{id}/lines/{line}/explain`, `POST /results/{id}/lines/{line}/counterfactual`. Errors are plain sentences. `apps/api/main.py` now builds the app with `create_app()`.
* `openapi.json` is checked in, `scripts/dump_openapi.py` regenerates it, `tests/test_openapi.py` fails on drift.
* ADR 008. Tests: `test_api_models.py`, `test_precompute.py`, `test_api.py`, `test_openapi.py`. 269 fast tests green in about 33 s, ruff and mypy clean. The slow 50 seed test was not rerun.

### Week 4 built (2026-11-06)
Slice 1, shell (`edf98b8`):
* `apps/web`: design system CSS import (`@ds` alias), React Router, theme switch (`data-theme`, stored as `reshelf-theme`), nav, "Simulated data" badge, data source banner, stepper on process pages, `InlineError` with Retry.
* Data layer `src/data/source.ts`: precomputed JSON by default, live API when `VITE_API_URL` answers `/health`. Failed requests become a `RequestError` with the endpoint, shown inline.
* `pnpm gen:api` writes `src/api/schema.d.ts` from `apps/api/openapi.json`. CI web job fails on drift.
* `tsc` had no `noEmit`, so `pnpm build` wrote stray `.js` files next to the sources. Fixed in `tsconfig.json`.
* `.rs-btn` added to the design system (it had no plain button).

Slice 2, stock (`55258af`):
* `stock.py`: `StockLot`, summary by reason, brand and brand/category. `ScenarioResult.stock` is built in `run_scenario`, so stock and results come from one source. `GET /stock/summary` and `GET /stock/lots` (filters brand, category, reason) read the latest stored result of a scenario. Tests in `test_stock.py`. 274 fast API tests green.
* Web: stock overview (KPI tiles, reason bars, brand to category drill with crumbs, filter chips) and stock table (column groups, group by with subtotals, share cell, totals row).
* Design system: `rs-hbars`, `rs-chip`, `rs-toolbar`, `rs-num`.

Slice 3, hero (`7eac9eb`):
* Results page: solver chip, KPI tiles against the compliant greedy baseline, rule dial, lines table with a Why button.
* Why panel: binding rules as chips with slack, blocked channels with reason codes, "Relax this rule" shows the precomputed euro cost.
* Rule dial: read only, three positions (current, relax by 10 percent, switch off) on the precomputed grid. Compare page: baseline raw, baseline compliant and optimizer columns, euro delta against the compliant plan, baseline audit list.
* Web tests: 28 green (Vitest), type check, lint and `pnpm build` clean.

Not done in week 4:
* Nothing was opened in a browser. Tests run in jsdom, so layout, theme colors and the sprite icons are unchecked. Run `pnpm dev` and look.
* The home page and Parameters page are placeholders. Live mode runs create and solve, but the Why panel does not call the counterfactual endpoint, it shows a sentence when a cost is not cached.
* The precomputed counterfactuals cover `sku[...]` rules only, so Why panels of lines bound by other rules say the cost is not cached.
* No Playwright e2e yet (week 6).

### Decisions taken with Nils
* Demo world is 30 SKUs by 5 channels (2026-11-05). Slice 4 scope is precompute plus scenario and results API (2026-11-05). The benchmark run is skipped for now.
* Push quantity depends on product category.
* Class A, B, C, NEW is per (material, channel) and driven by sellout in that channel. Score weight is per (material, channel).
* Transit time is per channel. Delivery date is `as_of` plus transit days.
* Channel stock is read directly from a stock table, not derived.
* Skincare push quantity is 30.
* Four slices for week 2.
* Plan for slice 4 approved as written (plan mode, 2026-10-26).

## Assumptions and decisions to check

### From earlier slices
* `link_yx` (y <= x) added so a selected SKU cannot earn score without receiving a unit.
* A lot expiring exactly on its delivery day is dropped.
* NEW pairs get bounds `[min(P, Q), P]`. Q is the supply in lots admissible for the channel, not total stock.
* With default weights a NEW pair at the worst rank can score below a class C pair at the best rank.

### From slice 4 (my calls, not yet confirmed by Nils)
* Urgency in the baseline order is `1 / max(days to expiry at as_of, 1)`, so value at risk is units times unit cost divided by days. ADR 005 left urgency undefined.
* Repair trims units instead of always dropping whole lines. Units above `cov_hi`, `asrt_units` or `cap` are cut from the lines with the lowest net value per unit. ADR 005 says "drops violating lines", so this is a small departure. Dropping whole lines would weaken the baseline further.
* Repair drops a whole SKU (material, channel) when it ends under a lower bound (`cov_lo`, `push`) or breaks `sku` or `asrt`, lowest net value per unit first. Adding units to reach a lower bound is never tried.
* The planner picks the channel by recovery factor only. It ignores brand penalty, so it can send a unit at negative net value. The repair does not remove such lines.
* A planner also uses pairs dropped only by a rule it does not apply. The audit reports those units under the reason code (`NO_PUSH`, or `TIER` and `RSL` if those rules leave `planner_rules`).
* Audit `excess` is in the unit of the constraint: units, or SKUs for `sku` and `asrt`.
* Brand risk index is the sum of penalty times units over the sum of unit cost times units (war plan 5.8). The index is 0 for an empty plan.
* Fill rate is units allocated over channel capacity.
* The property test tolerates 1e-6 on score and the reported MIP gap on value. It only asserts the value rule when the baseline score is within epsilon of the optimizer's.
* The property test uses 20 SKU worlds and scales every channel type `max_skus` by `n_skus / 2000` (rounded up, at least 1). Otherwise the assortment rules never bind on a small world and the test would not exercise them.
* The seed test is marked `slow` and not excluded from CI.
* The minimum gap (TS-065) is recorded here, not asserted.
* Tuning of the generator was skipped on purpose. The optimizer wins on all 50 seeds, and changing the generator risks the distribution tests.
* `pyarrow` is a required dependency, not an optional extra. Parquet adapter is P1 but the cost is one wheel.

### From week 3 slice 2 (my calls, not yet confirmed by Nils)
* The counterfactual keeps the original S* as score floor and runs phase 2 only. It does not redo phase 1, so a relaxation that would raise the best SKU score shows no score gain.
* `units_destroyed_by_rule` can be negative (seen: `sku[LIQ_AE]` off, minus 147). The value maximizer may send fewer but better units once a rule is relaxed. The UI has to lead with the euro figure.
* `plus_10pct` on an upper bound is at least one unit more. On a zero bound it changes nothing. On a lower bound it is 10 percent less, rounded down.
* A re solve that ends under the original plan keeps the original and reports cost 0 and status `feasible`.
* Ranking for the precompute is by lines touched, not by measured cost.
* The trace and the counterfactual skip `supply` and the link rules.

### From week 3 slice 4 (my calls, not yet confirmed by Nils)
* Tables come from `create_all`, not an Alembic migration (plan said Alembic). Add a migration before any deployed database.
* The counterfactual endpoint repeats the base solve instead of storing solver state. Fine at 30 SKUs, too slow at scale.
* `POST /scenarios` accepts `params` edits of the scenario `params` block and rejects unknown keys. Stock endpoints and the rule dial grid are not built.
* The 30 SKU demo world solves in under a second, so the 60 s limit and the earlier slow measures (scaled limits at 30 to 150 SKUs) do not apply to it. A bigger demo world is still open.
* `reshelf.db` is gitignored and created in the working directory unless `RESHELF_DB` is set.

## To do

### Left from week 2
* `baseline_expert` sensitivity check (TS-068): all rules plus one pass of local swaps, median, minimum and maximum uplift written to a file, CI fails below the minimum gap.
* Minimum gap assertion (TS-065) once the gap is settled.
* TS-076 (allocation coverage above 85% on the default scenario) not checked.
* TS-067 and TS-075 are e2e and belong to the web weeks.
* Decide whether to tune `coverage_days`, `second_life_share`, `total_capacity_ratio` (see open points).

### Weeks 3 to 8 (from the war plan)
| Week | Build |
|---|---|
| 3 | All four slices done. Still open: benchmark run and `docs/benchmark.md`, Alembic migration |
| 4 | Done: web shell, stock overview and table, hero slice on precomputed JSON |
| 5 | Parameter editor, run, charts, scenario save and load, Excel export |
| 6 | Why panel full, compare polish, globe, Playwright e2e |
| 7 | Docker, CI/CD, deploy, demo mode, README, ADRs, screenshots |
| 8 | Remotion video |

## Open points and risks

Story and baseline:
* **The gap against the compliant baseline is large** (median 2.6 times in value, maximum 68 times). The repair removes much of the raw plan, since lots are far bigger than channel coverage needs. A reviewer may call the baseline a strawman. Options: raise `second_life_share` so needs match lot sizes (upside: smaller gap, downside: changes the generator and its tests), or build `baseline_expert` and show the gap against a stronger opponent (upside: honest range, downside: more code). Needs a decision from Nils.
* ADR 005 open point: which rules planners really apply by hand (interview experiment E2). The `planner_rules` default is a hypothesis.
* ADR 005 open point: the repair order is a choice. The alternative is dropping whole lots.
* 72% of selectable pairs in the default scenario are NEW (20,650 of 28,826). Push quantities drive much of the result. Not reviewed in slice 4, since tuning was skipped. Possibly adjust generator carry probabilities.

Solver scale:
* HiGHS solve time at 2,000 SKUs is unproven. At 150 SKUs and 20 channels two of three seeds hit the 60 s limit, and one returned a phase 1 score of 0 (the time limit came before a plan). The benchmark in week 3 must cover this, and the demo may need a smaller default world, a larger time limit, or a warm start.
* A solve that hits the time limit with only the phase 1 plan reports no MIP gap, since no value gap exists.
* The property test would be unreliable on a world that does not solve to optimal, so it stays at 20 SKUs.

Tests and docs:
* TS-046 as written (infeasible status for a push above capacity) cannot happen: z = 0 switches every coverage and push row off, so the empty plan is always feasible. The solver returns a valid plan with all units destroyed. Test scenario wording to update (ADR 006).
* Channel `max_skus` is absolute in the scenario and only binds near 2,000 SKUs. Any other test on small worlds has to scale it the same way.
* `docs/model.md` generation and its CI drift check are done (week 3 slice 1). Run `make model-doc` after any registry change.
* The uplift figures come from a throwaway script. No test or file records them yet (TS-068 would).

## Working notes
* On this machine run uv with `UV_LINK_MODE=copy` (OneDrive blocks hardlinks).
* Run from `apps/api`: `uv run pytest -q`, `uv run ruff check . ../../data/generator`, `uv run ruff format --check . ../../data/generator`, `uv run mypy . ../../data/generator`.
* Commits: conventional, no `Co-Authored-By` lines (CLAUDE.md). Your `.gitignore` edit (`.mcp.json`) is still uncommitted and has never been staged by me.
* Run the throwaway scripts in `tmp/` with `PYTHONPATH=../../data/generator uv run python ../../tmp/<file>.py` from `apps/api`.
* `tmp/` is gitignored. It holds `measure.py`, the throwaway script that prints score and value per seed.
