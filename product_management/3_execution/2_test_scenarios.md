# Test Scenarios: Reshelf v1

**Date**: 2026-10-24
**Status**: Draft
**Source**: P0 and P1 requirements FR-01 to FR-21 in `1_backlog.md`, plus the risks from its red team and pre mortem (K1 to K5, T1 to T8).
**Total scenarios**: 163 (162 numbered rows plus the hero flow H1). TS-198 to TS-210 cover invariants, defaults and hygiene, see section 14.
**Coverage**: happy path, edge cases, error handling, performance, clean room and integrity checks. Security is limited to mocked roles and input validation, because v1 has no real authentication.

> Evidence level: scenarios are derived from documents, not from running code. Pre code, every status is `planned`. Expected values that depend on the seed (for example the euro cost of luxury protection) are written as "recorded from the seeded run" and frozen in a snapshot once the generator exists. No value here is a real figure.

## How to use this file

| Column | Meaning |
|---|---|
| Level | `unit` (pytest), `prop` (hypothesis property test), `api` (pytest against FastAPI), `ui` (Vitest and Testing Library), `e2e` (Playwright), `ci` (a CI step or script), `manual` (human walkthrough) |
| Priority | Critical: blocks release. High: fix before release unless cut. Medium: fix if time. Low: nice to have |
| Rule from the war plan | Every constraint gets a feasible and a violating test (`CLAUDE.md`, working agreements) |

**Environments and mocks needed**: the seeded dataset (`make demo-data`), precomputed JSON (`make precompute`), the API running locally, a browser with and without WebGL. No third party service is mocked, except the analytics tool in FR-21, which is stubbed.

---

## 1. Data and clean room (FR-01, FR-02)

| ID | Scenario | Steps | Expected | Priority | Level |
|---|---|---|---|---|---|
| TS-001 | Generator is reproducible | Run `make demo-data` twice with the same seed | Output files have identical hashes | Critical | ci |
| TS-002 | Different seed gives different data | Run with two seeds | Hashes differ, schema identical | Medium | unit |
| TS-003 | A class share follows the Pareto skew | Generate default dataset | Share of A class lots within the documented band | High | unit |
| TS-004 | Aging histogram has the documented shape | Generate default dataset | Histogram of remaining shelf life passes the shape test | High | unit |
| TS-005 | Brand tier mix matches the scenario file | Generate default dataset | Luxury, premium, mass shares within tolerance of `data/scenarios/default.yaml` | High | unit |
| TS-006 | Seasonality present | Compare demand by month | Seasonal factor varies as configured | Medium | unit |
| TS-007 | Every lot has a plausible expiry | Scan `MCHB` style table | `VFDAT` is after `HSDAT` for every lot, none null | High | unit |
| TS-008 | Canonical load accepts the seeded data | Run `CsvAdapter.load()` | Returns a `CanonicalDataset` with no validation error | Critical | unit |
| TS-009 | Pandera rejects a negative quantity | Corrupt one `qty` to -1 | Validation error names the field and row | Critical | unit |
| TS-010 | Pandera rejects an unknown tier | Set a tier to "gold" | Validation error | High | unit |
| TS-011 | Pandera rejects a missing channel rule | Remove one `ZCHANNEL_RULE` row | Validation error names the channel | High | unit |
| TS-012 | Empty source tables | Load header only files | Clear error or empty canonical dataset, never a crash with a stack trace | High | unit |
| TS-013 | Solver cannot take raw tables | Pass a raw dataframe to `Solver.solve` | Type check fails (mypy) and a runtime guard rejects it | High | unit |
| TS-014 | Only standard SAP names and invented Z tables | Scan table and column names against an allowlist | No name outside the allowlist | Critical | ci |
| TS-015 | Clean room scan | Run a script over the repo for forbidden terms (employer, product and system names kept in a local ignored list) | Zero hits in code, docs, data, screenshots metadata | Critical | ci |
| TS-016 | Every rule value is tagged illustrative | Scan scenario yaml and `ZPARAM` | Each value has an "illustrative default" tag or comment | High | ci |
| TS-017 | `_private/` never committed | Check `.gitignore` and `git ls-files` | `_private/` absent from the index | Critical | ci |
| TS-018 | Parquet adapter parity (P1) | Load the same data from CSV and Parquet | Canonical datasets are equal | Medium | unit |

## 2. Elimination before modeling (FR-03)

| ID | Scenario | Steps | Expected | Priority | Level |
|---|---|---|---|---|---|
| TS-020 | Lot passes remaining shelf life | Lot with RSL above `min_rsl_pct` of channel | Pair stays admissible | Critical | unit |
| TS-021 | Lot fails remaining shelf life | Lot with RSL below `min_rsl_pct` | Pair dropped with reason `RSL` | Critical | unit |
| TS-022 | RSL exactly on the threshold | RSL equals `min_rsl_pct` | Pair stays admissible (boundary documented) | High | unit |
| TS-023 | Tier allowed | Mass lot, channel allows mass | Admissible | Critical | unit |
| TS-024 | Tier blocked | Luxury lot to clearance channel | Dropped with reason `TIER` | Critical | unit |
| TS-025 | Both reasons apply | Luxury lot with short RSL to clearance | Both codes stored, the first is shown in the Why panel | Medium | unit |
| TS-026 | All pairs of a lot eliminated | Lot fails every channel | Lot has zero admissible pairs, units counted as destroyed, reasons kept | Critical | unit |
| TS-027 | Delivery date shifts RSL | Add transit days to a channel | RSL computed at delivery, not at today | High | unit |
| TS-028 | Reason codes survive to the API | Request results for a blocked lot | Response lists the reason code per dropped channel | High | api |

## 3. Optimizer: one test per constraint (FR-04)

Each constraint needs a feasible and a violating case. A violating case means a hand built solution that breaks the constraint must be rejected by the checker, and the solver must never return it.

| ID | Constraint | Feasible case | Violating case | Priority |
|---|---|---|---|---|
| TS-030 | `supply[l]` | Allocate exactly the available units | Allocate more than `q_l` | Critical |
| TS-031 | `link_xy[l,c]` | Positive x with y = 1 | Positive x with y = 0 | Critical |
| TS-032 | `link_yz[l,c]` | y = 1 with its SKU selected | y = 1 with z = 0 | Critical |
| TS-033 | `link_zy[m,c]` | z = 1 backed by at least one lot | z = 1 with no lot allocated | Critical |
| TS-034 | `cap[c]` | Total at capacity | One unit above `K_c` | Critical |
| TS-035 | `sku[c]` | `S_c` SKUs selected | `S_c + 1` SKUs | Critical |
| TS-036 | `asrt[g,c]` | `A_{g,c}` SKUs of the group | One more in the same group | Critical |
| TS-037 | `cov_hi[m,c]` | Quantity at the coverage need | Quantity above `D_{m,c}` | Critical |
| TS-038 | `cov_lo[m,c]` | Quantity at the lower bound | Selected SKU below `alpha * min(D, Q)` | Critical |
| TS-039 | `push[m,c]` | NEW material at the push quantity | NEW material below `min(P, Q_m)` when selected | Critical |

Level for all ten: `unit`. Also check that constraint names are stable.

| ID | Scenario | Steps | Expected | Priority | Level |
|---|---|---|---|---|---|
| TS-040 | Constraint names snapshot | Build the default model | Names match the stored snapshot, a rename fails the test | Critical | unit |
| TS-041 | `cov_hi` and `cov_lo` inactive when SKU not selected | z = 0 for a material | No quantity required, no quantity allowed | High | unit |
| TS-042 | Phase 1 maximizes the SKU score | Solve a small known instance | `S*` equals the hand computed optimum | Critical | unit |
| TS-043 | Phase 2 holds phase 1 within epsilon | Solve the same instance | Score at least `(1 - epsilon) * S*`, net value is maximal under that bound | Critical | unit |
| TS-044 | Epsilon zero and epsilon large | Set epsilon to 0, then to 1 | No numerical deadlock at 0, value only at 1 | Medium | unit |
| TS-045 | Unallocated units count as destroyed | Capacity too small | Destroyed units equal supply minus allocated | Critical | unit |
| TS-046 | Infeasible scenario | Contradicting rules (push above capacity) | Status `infeasible` returned, no exception, API passes it unchanged | Critical | unit |
| TS-047 | Empty input | No lots | Status and empty result, no crash | High | unit |
| TS-048 | Single channel | One channel only | Valid allocation, no division by zero in KPIs | High | unit |
| TS-049 | All lots eliminated | Rules block everything | All units destroyed, KPIs defined (value zero, brand risk index defined as zero) | Critical | unit |
| TS-050 | Time limit reached | Set a 1 s limit on a large instance | Status says limit reached, gap and time reported, best solution returned | High | unit |
| TS-051 | `SolveResult` carries all fields | Solve any instance | `status`, `objective`, `mip_gap`, `time_s`, `time_limit_s` present | Critical | unit |
| TS-052 | CBC fallback | Make HiGHS unavailable | CBC solves the small instance with the same objective | Medium | unit |
| TS-053 | Zero or negative net value lines | Brand penalty above recovered value | Line is not forced beyond what `cov_lo` requires, behavior documented | High | unit |
| TS-054 | Score weights from `ZPARAM` | Change a class weight in yaml | Result changes without a code change | High | unit |

## 4. Planner proxy baseline and uplift (FR-05, ADR 005)

| ID | Scenario | Steps | Expected | Priority | Level |
|---|---|---|---|---|---|
| TS-060 | Baseline applies only its configured rules | Run the baseline on the default dataset with rules shelf life, tier, capacity | Output respects those three rules and may break assortment, coverage and push | Critical | unit |
| TS-061 | Baseline order and capacity | Three lots with different value at risk, one channel nearly full | Highest value at risk placed first, the next lot goes to the next best channel with capacity | High | unit |
| TS-062 | Audit finds a violation the baseline ignored | Instance where the baseline puts more SKUs of one group in a channel than `asrt[g,c]` allows | Audit lists `asrt[g,c]` with the excess SKUs and units | Critical | unit |
| TS-063 | Audit finds nothing on a clean plan | Instance where the baseline happens to satisfy every rule | Zero violations, raw value equals compliant value | High | unit |
| TS-064 | Deterministic repair | Repair a plan with violations twice | Same compliant plan both times, it passes the full checker, lowest net value per unit dropped first | Critical | unit |
| TS-065 | Optimizer vs compliant baseline on the default seed | Compare both | ADR 005 statement holds and the gap is at or above the illustrative minimum | Critical | unit |
| TS-066 | Property on 50 neutral seeds | Run 50 seeds drawn before any tuning | Optimizer score at least the compliant baseline score, and when the baseline score is within epsilon of the optimizer's, optimizer net value at least the baseline's, within the reported MIP gap | Critical | prop |
| TS-067 | Raw, violations and compliant value all shown | Open the results KPIs | Three baseline numbers sit next to the optimizer, none hidden | Critical | e2e |
| TS-068 | Distribution and sensitivity | Run the 50 seeds, and run `baseline_expert` (all rules plus one pass of local swaps) | Median, minimum and maximum uplift written to a file for the README, expert gap recorded, CI fails below the minimum gap | High | ci |
| TS-069 | Baseline on an infeasible scenario | Contradicting rules | Defined empty or partial plan, audit still runs, no exception | Medium | unit |

## 5. KPIs (FR-06)

| ID | Scenario | Steps | Expected | Priority | Level |
|---|---|---|---|---|---|
| TS-070 | Value recovered | Hand built three line allocation | Equals the sum of `v * r - beta` times units | Critical | unit |
| TS-071 | Units destroyed | Same | Equals supply minus allocated | Critical | unit |
| TS-072 | Brand risk index | Same | Equals sum of `beta * x` over sum of `v * x` | Critical | unit |
| TS-073 | Brand risk index with zero value | No allocation | Defined (zero), no division by zero | High | unit |
| TS-074 | SKUs per channel and fill rate | Default result | Match counts from the allocation lines | High | unit |
| TS-075 | KPIs shown next to greedy | Open the results page | Every KPI has the baseline value beside it, and the baseline violations are listed | Critical | e2e |
| TS-076 | Allocation coverage on the default scenario | Read precomputed KPIs | Above 85% (target hypothesis, recorded if lower) | High | ci |

## 6. Rule trace (FR-07)

| ID | Scenario | Steps | Expected | Priority | Level |
|---|---|---|---|---|---|
| TS-080 | Binding constraint detected | Instance where `cap[c]` is full | Allocation lines into c list `cap[c]` | Critical | unit |
| TS-081 | Non binding constraint not listed | Constraint with large slack | Not listed in the trace | Critical | unit |
| TS-082 | Tolerance edge | Slack just under and just over the tolerance | Binding only under it | High | unit |
| TS-083 | Elimination reasons attached | Line whose other channels were dropped for TIER | Trace shows the reasons for each blocked channel | Critical | unit |
| TS-084 | Trace for a destroyed lot | Lot with no allocation | Trace explains why (all eliminated, or capacity binding) | High | unit |
| TS-085 | Trace served by API | Call `/results/{id}/lines/{line}/explain` | Response matches the unit result | High | api |
| TS-086 | Unknown line | Request a line that does not exist | 404 with a clear message | High | api |

## 7. Counterfactual (FR-08)

| ID | Scenario | Steps | Expected | Priority | Level |
|---|---|---|---|---|---|
| TS-090 | Relax a model constraint by 10% | Relax `cap[c]` on the default scenario | Reports euro change and units change, both consistent with a full re solve | Critical | unit |
| TS-091 | Switch a constraint off | Remove `sku[c]` | Value is not lower than before (relaxing cannot hurt), a violation fails the test | Critical | prop |
| TS-092 | Elimination rule relaxed (T2) | Allow luxury in clearance | Admissible set rebuilt, result shows the euro value luxury protection costs | Critical | unit |
| TS-093 | Non binding rule | Relax a rule with large slack | Cost reported as zero, panel says the rule is not limiting | High | unit |
| TS-094 | Time limit | Counterfactual on 2,000 SKUs | Finishes under 10 s, p95 under 5 s, status reported if the limit is hit | Critical | unit |
| TS-095 | Warm start usable (Q3) | Solve cold and warm | Same objective, warm start not slower, or the spike records that it is unsupported | High | unit |
| TS-096 | Counterfactual does not mutate the stored result | Run it, then read results | Original results unchanged | Critical | api |
| TS-097 | Precomputed counterfactuals present | Run `make precompute` | Top binding rules per seeded scenario have a stored counterfactual | High | ci |
| TS-098 | Infeasible after relaxing | Relax into a contradiction | Clear message, no crash | Medium | unit |

## 8. API and contract (FR-09)

| ID | Scenario | Steps | Expected | Priority | Level |
|---|---|---|---|---|---|
| TS-100 | OpenAPI lists every endpoint | Read `/openapi.json` | All nine endpoints from war plan 6.2 present | Critical | api |
| TS-101 | TypeScript type drift | Regenerate types, run diff | CI fails when generated types differ from the committed ones | Critical | ci |
| TS-102 | Create, solve, read | POST `/scenarios`, POST solve, GET results | Results contain lines, KPIs and `SolveResult` fields unchanged | Critical | api |
| TS-103 | Malformed body | POST a scenario with a string where a number is expected | 422 with field level detail | High | api |
| TS-104 | Unknown scenario id | GET results for a missing id | 404 | High | api |
| TS-105 | Compare with a missing id | `/scenarios/compare?ids=1,999` | 404 naming the missing id | High | api |
| TS-106 | Compare needs at least two ids | Only one id | 422 | Medium | api |
| TS-107 | Solve twice | POST solve twice on the same scenario | Second call is idempotent or returns the stored result, documented | Medium | api |
| TS-108 | Concurrent solves | Two solves at once | Both complete with correct results, no shared state leak | Medium | api |
| TS-109 | Health check | GET health | Answers fast, used by the frontend to switch to live mode | Critical | api |
| TS-110 | Mocked roles | Call with roles planner, viewer, admin | Viewer cannot create or solve, planner can, admin can, 403 otherwise | Medium | api |
| TS-111 | Export endpoint | GET `/scenarios/{id}/export.xlsx` | Valid file, correct content type | High | api |
| TS-112 | Persistence | Save a scenario, restart the API | Scenario still loads | High | api |

## 9. UI: stock overview, parameters, results (FR-10, FR-11)

| ID | Scenario | Steps | Expected | Priority | Level |
|---|---|---|---|---|---|
| TS-120 | Table renders 10,000 rows | Load the 10k dataset | Scrolling stays smooth (virtualized), first paint under 3 s | High | ui |
| TS-121 | Sort and filter | Sort by value at risk, filter by plant and tier | Rows and counts match the filter | Critical | ui |
| TS-122 | Empty filter result | Filter to nothing | Empty state with a way to clear the filter | Medium | ui |
| TS-123 | KPI tiles match the data | Compare tiles to the table totals | Equal | High | ui |
| TS-124 | Parameter editor shows documented defaults | Open the editor | Every value has its illustrative default and a reset button | High | ui |
| TS-125 | Invalid parameter | Enter a negative capacity or a percent above 100 | Inline error, run button disabled | Critical | ui |
| TS-126 | Run with changed parameters (live) | Change a value, run | Results update, banner says "Live solver" | High | e2e |
| TS-127 | Results table | Open results | One row per allocation line, sortable, with channel, units, value | Critical | ui |
| TS-128 | Waterfall chart | Open results | Inflow minus outflow equals the stock summary | High | ui |
| TS-129 | Run while the API is down | Stop the API after load | Message and fallback to cached results, no blank screen | High | e2e |
| TS-130 | Small screen | 375 px wide | Layout usable, globe replaced by table | Medium | e2e |

## 10. Scenarios, compare and the hero flow (FR-12, FR-13)

### Scenario H1: Hero flow, "tighten a rule, see what it costs, see why" (critical, e2e)

**Tests**: FR-11, FR-12, FR-13, FR-14, success metric "explained decisions" (K1, K4)
**Preconditions**: seeded `default` and `luxury_protection` scenarios, precomputed JSON, no API running (cached mode)
**User role**: planner

| Step | Action | Expected Result |
|---|---|---|
| 1 | Open the app | First screen under 3 s, banner reads "Cached results", stock overview visible |
| 2 | Open Parameters, tighten the luxury rule to "not allowed in clearance" using the dial | A result exists for that dial position (precomputed grid), no blank state |
| 3 | Run | Results table updates, KPIs show value recovered, units destroyed, brand risk index, each next to greedy |
| 4 | Open Compare against the default scenario | Deltas show lower brand risk index and lower value recovered, the cost in euros equals the recorded snapshot |
| 5 | Open the Why panel on a line that moved | Panel lists the blocked channels with reasons in plain language, the binding rules, and the counterfactual euro cost |
| 6 | Read the cost of luxury protection | Value matches the compare delta within rounding |
| 7 | Press "Export" (P1) | An Excel file downloads, the columns match the documented format |

**Postconditions**: nothing persisted in cached mode, scenarios list unchanged
**Priority**: Critical. Elements used must carry stable `data-testid` values.

| ID | Scenario | Steps | Expected | Priority | Level |
|---|---|---|---|---|---|
| TS-140 | Save a scenario | Name and save after a run | Appears in the saved list with its KPIs | Critical | e2e |
| TS-141 | Load a scenario | Load a saved one | Parameters and results restored exactly | Critical | e2e |
| TS-142 | Duplicate name | Save with an existing name | Prompt to overwrite or rename | Medium | ui |
| TS-143 | Compare two scenarios | Select two | Table of KPI deltas with sign and color, brand risk index always shown | Critical | ui |
| TS-144 | Parameter impact is compare | Change only one parameter, compare with the base | Same view shows that parameter as the diff, no second feature | High | ui |
| TS-145 | Compare a scenario with itself | Select the same one twice | Zero deltas or a polite block, no error | Low | ui |
| TS-146 | Why panel opens on a destroyed lot | Open on a lot with no allocation | Explains why every channel failed | High | e2e |
| TS-147 | Why panel wording | Give the text to a non OR reader (E3) | 4 of 5 explain the line in their own words | High | manual |
| TS-148 | Counterfactual button in cached mode | Press it | Returns the precomputed result instantly, or a clear note that the rule has no precomputed value | Critical | e2e |
| TS-149 | Counterfactual button in live mode | Press it | Spinner, result under 5 s p95, timeout message at 10 s | High | e2e |
| TS-150 | Override and compare (deferred, FR-22) | Not in v1 | Placeholder test marked `skip` with the rule: an overridden allocation must be its own scenario | Low | e2e |

## 11. Demo mode and honesty (FR-14, K4)

| ID | Scenario | Steps | Expected | Priority | Level |
|---|---|---|---|---|---|
| TS-160 | Default is cached | Open with no `VITE_API_URL` | Banner "Cached results", no network error in the console | Critical | e2e |
| TS-161 | Switch to live | Set `VITE_API_URL` to a healthy API | Banner "Live solver" | Critical | e2e |
| TS-162 | API unhealthy | Health check fails or times out | Stay on cached, no flicker between modes | Critical | e2e |
| TS-163 | API recovers | Start the API after load | Switch is offered, not forced mid task | Medium | e2e |
| TS-164 | Every dial position has a result | Walk the dial through all grid steps | No empty state, each step shows a real precomputed result | Critical | e2e |
| TS-165 | Click test of an outsider (K4) | 3 reviewers, 30 seconds each | None asks "is this real?" without finding the answer in the banner or the "run it yourself" link | High | manual |
| TS-166 | Precompute is deterministic | Run `make precompute` twice | Identical JSON | Critical | ci |
| TS-167 | Cold start | Open the deployed site from a cold cache | First screen under 3 s | High | manual |
| TS-168 | Stale precomputed data | Change a scenario yaml without recomputing | CI fails with a message to rerun `make precompute` | High | ci |

## 12. Globe, export and extras (FR-16 to FR-21)

| ID | Scenario | Steps | Expected | Priority | Level |
|---|---|---|---|---|---|
| TS-170 | Globe shows plants and channel arcs | Open overview after a solve | Plant points sized by value at risk, arcs to channels | Medium | e2e |
| TS-171 | Globe click filters the table | Click a plant | Table filtered on that plant | High | e2e |
| TS-172 | No WebGL | Disable WebGL | Table fallback, no crash | High | e2e |
| TS-173 | Globe is lazy loaded | Check the network panel | Globe chunk loads only when the view opens | Medium | ci |
| TS-174 | Excel opens | Export the default scenario, open it | Columns and sheet names match the documented format | High | api |
| TS-175 | Excel with zero lines | Export an all eliminated scenario | Valid file with a header and a note, no crash | Medium | api |
| TS-176 | Excel special characters | Material descriptions with accents | Characters preserved | Medium | api |
| TS-177 | Benchmark table | Run the benchmark | `docs/benchmark.md` shows time and gap per size and solver, p95 at 2,000 SKUs under 10 s | High | ci |
| TS-178 | Benchmark red | Time above 30 s | CI marks it red, README states the reduced demo size | Medium | ci |
| TS-179 | Usage events fire | Run, open Why, open compare, export | `scenario_run`, `why_opened`, `compare_opened`, `export_clicked` sent to the stub | Low | ui |
| TS-180 | Events carry no personal data | Inspect payloads | No user identifier, no free text | Medium | ui |
| TS-181 | Material deep dive (stretch) | Open one material | Lots, allocations and trace shown, consistent with the results table | Low | e2e |

## 13. Quality gates and release (FR-15)

| ID | Scenario | Steps | Expected | Priority | Level |
|---|---|---|---|---|---|
| TS-190 | CI blocks on failure | Break a test on a branch | CI red, merge blocked | Critical | ci |
| TS-191 | One command start | Follow README "Try it in 3 commands" on a clean machine or Codespace | App runs, hero flow works | Critical | manual |
| TS-192 | README limitations present | Read README | States synthetic data, simulated KPIs, no real impact claim | Critical | manual |
| TS-193 | README links and images | Run a link check | Zero broken links or images | Medium | ci |
| TS-194 | ADR coverage | List major choices (stack, lot index, tight form, explainability, comparison) | One ADR each | High | manual |
| TS-195 | Peer review (E5) | 5 reviewers, 5 minutes each | 4 of 5 state problem, user and differentiator | High | manual |
| TS-196 | Rollback | Redeploy the previous tag | Previous demo serves, precomputed data intact | Medium | manual |
| TS-197 | Reproducibility of screenshots | Rerun the capture script | Images identical apart from timestamps | Medium | ci |

## 14. Invariants, defaults and hygiene (FR-02, FR-04, FR-10, FR-15)

| ID | Scenario | Steps | Expected | Priority | Level |
|---|---|---|---|---|---|
| TS-198 | Class A beats C and NEW | One scarce channel slot, one material of each class with the best possible rank in C and NEW | Class A is selected | Critical | unit |
| TS-199 | Rank breaks ties only inside a class | Two materials of one class, different rank | Better rank wins, class order never flips | High | unit |
| TS-200 | Tie break is deterministic | Solve the same tied input 5 times | Identical allocation each time | High | unit |
| TS-201 | Missing rank | Remove the rank of one material | Treated as lowest rank, no crash | Medium | unit |
| TS-202 | Unranked material class | One unranked material with channel stock, one without | `C` and `NEW` respectively | High | unit |
| TS-203 | Missing demand row | Remove demand for one material and channel | No coverage need, documented default applies | High | unit |
| TS-204 | NEW without push rule | Remove the push rule of a NEW material | Not allocated, reason shown in the trace | High | unit |
| TS-205 | In transit counts as stock | Add units in transit to a channel | Coverage need drops by that amount | High | unit |
| TS-206 | Result invariants | After every solve in the suite | No negative quantity, no line above supply, totals equal KPIs | Critical | prop |
| TS-207 | Parameter validation | Negative capacity, negative coverage days, percent above 100, unknown class | Rejected with a field level error before any solve | Critical | unit |
| TS-208 | Generated model doc is current | Run `make model-doc`, diff against the committed file | No diff, CI fails otherwise | High | ci |
| TS-209 | Errors are visible | Make an endpoint return 500 | Inline error with endpoint and Retry, no blank panel, no silent catch (lint rule on empty catch) | Critical | ui |
| TS-210 | No generated artifacts committed | Scan `git ls-files` for LP files, logs, machine suffixed copies | None found | Medium | ci |

---

## Coverage matrix

| Requirement | Happy path | Edge cases | Error handling | Notes |
|---|---|---|---|---|
| FR-01 Seeded data | TS-001, 003 to 005 | TS-002, 006, 007 | TS-012 | Seed story needs the generator tuned in week 1 |
| FR-02 Canonical and adapter | TS-008, 018 | TS-012, 202, 203, 205 | TS-009 to 011, 013, 204 | Parquet is P1. TS-202 to 205 cover class derivation and missing data defaults |
| FR-03 Elimination | TS-020, 023 | TS-022, 025, 027 | TS-021, 024, 026, 028 | Reason codes feed FR-13 |
| FR-04 Optimizer | TS-030 to 039, 042, 043, 198 | TS-041, 044, 048 to 050, 053, 199 to 201, 206 | TS-046, 047, 051, 052, 207 | Constraint names are stable. TS-208 keeps `docs/model.md` in sync |
| FR-05 Baseline and uplift | TS-060, 065 | TS-061, 063, 068 | TS-062, 064, 066, 067, 069 | Needs ADR 005 accepted first (Q1) |
| FR-06 KPIs | TS-070 to 072, 074 | TS-073 | TS-075, 076 | Brand risk index is a counter metric |
| FR-07 Rule trace | TS-080, 083 | TS-081, 082, 084 | TS-085, 086 | |
| FR-08 Counterfactual | TS-090, 091, 092 | TS-093, 095 | TS-094, 096, 098 | T2 covered by TS-092 |
| FR-09 API | TS-100, 102, 109 | TS-107, 108 | TS-101, 103 to 106, 110 to 112 | |
| FR-10 Stock table | TS-120, 121, 123 | TS-122 | none beyond empty state | |
| FR-11 Parameters and run | TS-124, 126, 127, 128 | TS-130 | TS-125, 129 | |
| FR-12 Save and compare | TS-140, 141, 143, 144 | TS-142, 145 | none | Override test skipped (FR-22) |
| FR-13 Why panel | H1 step 5, TS-146, 147 | TS-146 | TS-148, 149 | K1 test is TS-147 |
| FR-14 Demo mode | TS-160, 161, 164 | TS-163, 168 | TS-162, 165, 166, 167 | K4 tests |
| FR-15 Quality | TS-190, 191, 208 | TS-197, 210 | TS-192 to 196, 209 | T4 covered by TS-014 to 017 |
| FR-16 Globe (P1) | TS-170, 171 | TS-173 | TS-172 | |
| FR-17 Export (P1) | TS-174, H1 step 7 | TS-175, 176 | TS-111 | |
| FR-18 Deep dive (P1) | TS-181 | none | none | First to cut |
| FR-19 Benchmark (P1) | TS-177 | none | TS-178 | |
| FR-20 Video (P1) | none | none | none | Manual review against the storyboard, no automated test |
| FR-21 Events (P1) | TS-179 | none | TS-180 | |

## Risk to scenario map

| Risk (from `1_backlog.md`) | Scenarios |
|---|---|
| K1, A8 Why panel not understood | TS-147, H1 |
| K2, T1 uplift rigged or false by definition | TS-065 to 068 |
| K3 Market need | Not a software test: experiment E2, see the discovery plan |
| K4, T3 Static demo breaks the hero | TS-160 to 168, H1 |
| K5, T6 Capacity | Not a test: week 3 gate |
| T2 Counterfactual and elimination rules | TS-092 |
| T4 Clean room breach | TS-014 to 017 |
| T5 Plain language | TS-147 |
| T7 Free tier flakiness | TS-162, 167 |
| T8 "Synthetic means no proof" | TS-192, 195 |

## Test data requirements

| Data | Used by | How produced |
|---|---|---|
| Default seeded dataset (about 2,000 SKUs) | Most scenarios | `make demo-data`, seed in `data/scenarios/default.yaml` |
| Small hand built instances (3 lots, 2 channels) | Constraint, KPI, trace and greedy unit tests | Fixtures in `apps/api/tests/fixtures/` with expected values computed by hand in the test |
| 50 neutral seeds drawn before tuning | TS-066 to 068 | Seed list committed in a file, never edited after the first run |
| Luxury protection scenario | H1, TS-092 | `data/scenarios/luxury_protection.yaml` |
| 10,000 row dataset | TS-120, 177 | Generator with a size parameter |
| Contradicting rules instance | TS-046, 068, 098 | Fixture |
| Corrupted source tables | TS-009 to 012 | Fixtures that break one field each |
| Precomputed JSON including the rule dial grid | UI, e2e | `make precompute` |
| Accented material descriptions | TS-176 | Generator option |

## Open points

* Seed dependent expected values (the cost of luxury protection, the minimum uplift gap) are fixed only after the generator and the spike RS-025 exist. Until then they are recorded, not asserted.
* TS-050, TS-094 and TS-095 depend on how the solver is called (Q3 in `1_backlog.md`).
* FR-20 has no automated test. Its check is manual against the locked storyboard.
