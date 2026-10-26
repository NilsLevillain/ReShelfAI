# Progress

Last updated: 2026-10-27. Source of truth for the schedule is `docs/war_plan.md` section 7.

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
| 3 to 8 | Rule trace, API, web app, Docker, video | Not started |

Test state after slice 4: 246 tests green in about 3.5 minutes, ruff and mypy strict clean. The 50 seed test is marked `slow` (`-m "not slow"` skips it, CI runs everything). Commits are local, not pushed.

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

### Decisions taken with Nils
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
| 3 | Rule trace, counterfactual, benchmark, FastAPI endpoints, persistence, generated `docs/model.md` |
| 4 | Web shell, stock overview and table, thin hero slice on precomputed JSON |
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
* `docs/model.md` generation and its CI drift check are week 3. The registry is ready for it.
* The uplift figures come from a throwaway script. No test or file records them yet (TS-068 would).

## Working notes
* On this machine run uv with `UV_LINK_MODE=copy` (OneDrive blocks hardlinks).
* Run from `apps/api`: `uv run pytest -q`, `uv run ruff check . ../../data/generator`, `uv run ruff format --check . ../../data/generator`, `uv run mypy . ../../data/generator`.
* Commits: conventional, no `Co-Authored-By` lines (CLAUDE.md). Your `.gitignore` edit is still uncommitted and has never been staged by me.
* `tmp/` is gitignored. It holds `measure.py`, the throwaway script that prints score and value per seed.
