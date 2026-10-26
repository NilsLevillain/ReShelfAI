# Progress

Last updated: 2026-10-26. Source of truth for the schedule is `docs/war_plan.md` section 7.

## Status at a glance

| Week | Scope | Status |
|---|---|---|
| 0 | Repo, tooling, ADR 001, CI | Done |
| 1 | ERD, mapping, rule defaults, seeded generator, 50 neutral seeds | Done |
| Design system and product management | Tokens, spec, discovery, strategy, metrics | Done |
| 2, slice 1 | Canonical schema, CsvAdapter | Done (`5b0e297`) |
| 2, slice 2 | Elimination, solver input, constraint registry and checker, ADR 003 and 004 | Done (`4bf9ea8`) |
| 2, slice 3 | Solver core, ADR 006 | Done |
| 2, slice 4 | Baseline, KPIs, seed property test, tuning, Parquet adapter | To do |
| 3 to 8 | Rule trace, API, web app, Docker, video | Not started |

Test state after slice 3: 174 tests green, ruff and mypy strict clean. Commits are local, not pushed.

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

### Decisions taken with Nils
* Push quantity depends on product category.
* Class A, B, C, NEW is per (material, channel) and driven by sellout in that channel. Score weight is per (material, channel).
* Transit time is per channel. Delivery date is `as_of` plus transit days.
* Channel stock is read directly from a stock table, not derived.
* Skincare push quantity is 30.
* Four slices for week 2.

### My calls awaiting a check
* `link_yx` (y <= x) added so a selected SKU cannot earn score without receiving a unit.
* A lot expiring exactly on its delivery day is dropped.
* NEW pairs get bounds `[min(P, Q), P]`. Q is the supply in lots admissible for the channel, not total stock.
* With default weights a NEW pair at the worst rank can score below a class C pair at the best rank.

## To do

### Week 2, slice 4: baseline, KPIs, seeds
* `baseline_planner` (rules from `planner_rules`, default rsl, tier, capacity), audited by the checker.
* Deterministic repair to a compliant plan. KPIs: value recovered, units destroyed, brand risk index, SKUs per channel, fill rate, raw value, violations, compliant value.
* ADR 005 property test on the 50 neutral seeds (reduced `n_skus`), minimum gap assertion.
* Tune the scenario parameters marked "tune" (`coverage_days`, `second_life_share`, `total_capacity_ratio`). Never edit the neutral seeds. Rerun generator tests after any change.
* Parquet adapter (P1). `baseline_expert` sensitivity check if time allows.
* Week 2 done when: tests green and the optimizer beats the greedy baseline on the seeds.

### Weeks 3 to 8 (from the war plan)
| Week | Build |
|---|---|
| 3 | Rule trace, counterfactual, benchmark, FastAPI endpoints, persistence, generated `docs/model.md` |
| 4 | Web shell, stock overview and table, thin hero slice on precomputed JSON |
| 5 | Parameter editor, run, charts, scenario save and load, Excel export |
| 6 | Why panel full, compare polish, globe, Playwright e2e |
| 7 | Docker, CI/CD, deploy, demo mode, README, ADRs, screenshots |
| 8 | Remotion video |

## Open points and risks
* TS-046 as written (infeasible status for a push above capacity) cannot happen: z = 0 switches every coverage and push row off, so the empty plan is always feasible. The solver returns a valid plan with all units destroyed. Test scenario wording to update (ADR 006).
* A solve that hits the time limit with only the phase 1 plan reports no MIP gap, since no value gap exists.
* 72% of selectable pairs in the default scenario are NEW (20,650 of 28,826). Push quantities will drive much of the result. Review in slice 4 tuning, possibly adjust generator carry probabilities.
* HiGHS solve time at 2,000 SKUs is unproven. The benchmark is week 3. Property tests use fewer SKUs.
* ADR 005 open point: which rules planners really apply by hand (interview experiment E2).
* `docs/model.md` generation and its CI drift check are week 3. The registry is ready for it.

## Working notes
* On this machine run uv with `UV_LINK_MODE=copy` (OneDrive blocks hardlinks).
* Run from `apps/api`: `uv run pytest -q`, `uv run ruff check . ../../data/generator`, `uv run ruff format --check . ../../data/generator`, `uv run mypy . ../../data/generator`.
* Commits: conventional, no `Co-Authored-By` lines (CLAUDE.md). Your `.gitignore` edit is still uncommitted and has never been staged by me.
