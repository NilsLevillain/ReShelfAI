# Backlog and Roadmap: Reshelf

**Date**: 2026-10-24
**Status**: Draft for review
**Author**: Nils
**Stage**: Pre code. Week 0 has not started.
**Evidence level**: Hypotheses. Nothing here is validated by a user yet. Every number is a target or an illustrative default, never a claim of business impact.

> This file is the single place for the build roadmap. It turns discovery (`../1_discovery/`) and strategy (`../2_strategy/`) into an ordered backlog, then attacks that order with a red team and a pre mortem. Architecture stays in `docs/war_plan.md`, which remains the source of truth for the model and the stack.

## How to read this file

| Part | Question it answers |
|---|---|
| 1. PRD | What do we build in v1, for whom, and how do we know it worked? |
| 2. OKRs | What outcomes do the 9 weeks aim at? |
| 3. Roadmap and sprint plan | In what order, with what capacity, with which gates? |
| 4. Red team | Which assumptions would kill the plan, and what is the cheapest test for each? |
| 5. Pre mortem | If v1 failed, what is the most likely story? |
| 6. Changes to the plan | What did parts 4 and 5 change, and what needs your decision? |

**Traceability keys used below**: `R#` feature request (`../1_discovery/3_feature_triage.md`), `A#` assumption and `E#` experiment (`../1_discovery/1_discovery_plan.md`), `FR` requirement in this PRD, `RS` backlog story.

---

# Part 1. Product Requirements Document: Reshelf v1

### 1. Executive Summary

Reshelf v1 is a public, portfolio grade demo of a decision support tool that allocates stock that cannot sell through primary retail to second life channels, under business rules, and explains each decision. It serves supply planners first, with brand and finance reviewers as the people who challenge the result. It is built now because two goals run in parallel: a public repo that proves product and engineering skill, and a commercial option that stays open only if discovery finds a reachable and painful need.

The hero flow is one sentence: **tighten a rule, see what it costs in euros, see why.**

### 2. Background and Context

* **Problem (H)**: lots near expiry, discontinued or overproduced are placed by hand across spreadsheets. Rules are applied unevenly. When brand or finance asks what a protective rule costs, nobody can answer fast, so decisions follow habit and units are destroyed (`2_strategy/1_strategy.md`, sections 2 and 3).
* **Why now (H)**: rules on destroying unsold goods are moving in some markets. Verify before quoting (`2_strategy/4_market_scan.md`).
* **What discovery decided** (`3_feature_triage.md`): four of the five top asks are about trust, not speed. Priority 1 is explainability and scenario work, on top of a table first UI. Excel export is the adoption gate. Override, import, multi period, theme and BigQuery wait. An AI that chooses allocations is declined.
* **What strategy decided**: explainable over fastest, tables first with the globe as a filter, human in the loop, solver decides and AI only drafts, explains and checks, one period in the MVP, allocation only (no marketplace).
* **Evidence gap**: A1, A3, A4 and A15 are leaps of faith still untested. v1 is built in parallel with the experiments that test them, with gates in Part 3.

### 3. Objectives and Success Metrics

**Goals**
1. Prove the hero flow end to end on a seeded scenario, reproducible byte for byte.
2. Show a fair, visible comparison against a planner proxy baseline (what a manual process does, audited against the full rules) on every run.
3. Make every allocation line explainable: rule trace instantly, counterfactual cost in euros on demand.
4. Give a stranger the story in 5 minutes: README, live demo, 75 second video, and this folder.
5. Learn whether the commercial option is real (E2, E3, E4) without letting the answer block the build.

**Non Goals (and why)**
1. No real data, no real rule values, no real channel names: clean room.
2. No manual override, Excel import, multi period model, theme switch, BigQuery connector or MILP duals in v1: each is triaged to a later wave.
3. No AI feature in v1: gated by E7 and E8 and built after the hero flow.
4. No authentication beyond mocked roles, no multi tenancy, no billing.
5. No running of the sale or marketplace: Reshelf decides where stock should go.
6. No claim of real business impact: KPIs are simulated and always shown against the greedy baseline.

**Success Metrics** (all targets are hypotheses; baselines are empty because nothing exists yet)

| Metric | Current | Target | Measurement |
|---|---|---|---|
| Optimizer uplift vs greedy, default scenario | none | Positive on 100% of seeded datasets, and at or above an illustrative minimum gap (set in week 2, see red team K2) | pytest property test, CI |
| Allocation coverage, default scenario | none | Above 85% | `data/precomputed/*.json`, CI |
| Solve time p95, 2,000 SKUs | none | Under 10 s | CI benchmark (E6) |
| Counterfactual re solve p95 | none | Under 5 s, hard limit 10 s | CI |
| Explained decisions (planners explaining a line unaided) | none | 4 of 5 (E3) | Walkthrough |
| Demo cold start to first screen | none | Under 3 s cached | Weekly check |
| 5 minute review pass rate | none | 4 of 5 (E5) | Peer reviews |
| Counter metric: brand risk index | none | Visible in compare, never hidden behind value | Compare view test |

### 4. Target Users and Segments

| User | Role in v1 | Need | Evidence |
|---|---|---|---|
| Supply planner (primary persona, H) | Builds and runs scenarios | Defensible allocation in minutes | Untested until E2 |
| Brand and finance reviewer (secondary, H) | Reads compare and Why panel | Price of each protective rule | Untested until E3 |
| Hiring manager or peer (project user) | Reads repo, demo, video, this folder | Understand problem, user and differentiator in 5 minutes | Untested until E5 |
| Sustainability lead (tertiary) | Not served in v1 | Traceable units diverted | Later |

Segment sizes are not stated: no market sizing has been done yet.

### 5. User Stories and Requirements

**P0: Must have** (v1 does not ship without these)

| ID | User story | Acceptance criteria |
|---|---|---|
| FR-01 | As a reviewer, I want a reproducible synthetic world (Kestrel Beauty Group), so every run and screenshot matches. | `make demo-data` run twice gives identical file hashes. Tests assert the share of A class, the aging histogram shape and the tier mix. No real name or value anywhere. |
| FR-02 | As an engineer, I want source tables mapped to a canonical dataset, so the solver never reads raw ERP tables. | Pandera rejects invalid data. A test proves the solver input type is canonical only. CSV adapter works. Standard SAP names only. |
| FR-03 | As a planner, I want pairs that break shelf life or brand tier rules removed up front, with a reason. | Each dropped pair carries a reason code (RSL or TIER). One feasible and one violating test per rule. |
| FR-04 | As a planner, I want an optimizer that respects all rules at once. | Two phase lexicographic model with named, stable constraints. One pytest per constraint (feasible and violating). Edge tests: infeasible, empty input, single channel, all lots eliminated. `SolveResult` returns status, objective, MIP gap, time and limit unchanged through the API. |
| FR-05 | As a reviewer, I want a baseline that resembles what a planner does by hand, so the comparison is fair and the rules a manual process misses become visible. | Baseline follows ADR 005: applies shelf life, brand tier and channel capacity only (configurable list), ordered by value at risk. The full checker audits it and lists violations per named constraint. KPIs show raw value, violations and compliant value. Property test over 50 neutral seeds uses the ADR 005 statement. |
| FR-06 | As a planner, I want KPIs per scenario. | Value recovered, units destroyed, brand risk index, SKUs per channel, fill rate, solver status and gap, each next to the greedy value. |
| FR-07 | As a planner, I want a rule trace on every line. | Each line lists binding constraints (slack within tolerance) and the elimination reasons that blocked other channels. A snapshot test locks constraint names. |
| FR-08 | As a brand reviewer, I want the euro cost of one rule. | One click relaxes one rule (+10% or off) and reports "costs X euros, Y more units destroyed". Works for model constraints and for elimination rules such as the luxury tier ban. Warm start where supported, 10 s limit, p95 under 5 s. Top rules precomputed per seeded scenario. |
| FR-09 | As a frontend engineer, I want a typed API. | Endpoints from `docs/war_plan.md` section 6.2 appear in OpenAPI. TypeScript types are generated. CI fails on drift. |
| FR-10 | As a planner, I want a sortable, filterable, virtualized stock table as the main surface. | 10,000 rows scroll without lag. Filters by plant, brand, tier, expiry bucket, stock reason. Column group toggles, group by with subtotals, allocation share and remaining units per row, filter state in the URL. Every hero element has a stable `data-testid`. |
| FR-11 | As a planner, I want to edit parameters and run. | Editor for rule values with documented defaults. Run returns results table, charts and KPIs vs greedy. In cached mode the rule dial moves on a precomputed grid (see FR-14). |
| FR-12 | As a planner, I want to save, load and compare scenarios. | Compare shows KPI deltas, including brand risk index. Parameter impact is the same view between two scenarios. |
| FR-13 | As a brand or finance reviewer, I want a Why panel in plain language. | Opens from any line. Shows blocked channels with reasons, binding rules, counterfactual cost in euros. Text readable by a non OR user (tested in E3). |
| FR-14 | As a visitor, I want the demo to load instantly and be honest. | Precomputed JSON by default. Switches to live when `VITE_API_URL` answers a health check. Banner always says "Cached results" or "Live solver". The rule dial uses a precomputed grid so any dial position shows a real result. |
| FR-15 | As a reviewer, I want to trust the repo. | CI gates (ruff, mypy, pytest, ESLint, Vitest, build). One Playwright test of the hero flow. README with limitations stated. One ADR per major choice. |

**P1: Should have** (cut in this order if late: deep dive, Excel polish, live API, 10k benchmark row)

| ID | Story | Acceptance criteria |
|---|---|---|
| FR-16 | Globe on the stock overview that filters the table (R1 tension resolved). | Lazy loaded. Table fallback without WebGL or on small screens. Click on a plant or country filters the table. |
| FR-17 | Excel export in a generic order creation format (R2). | File opens, columns documented, export success 100% on seeded scenarios. |
| FR-18 | Material deep dive page. | Lots, allocations and trace for one material. |
| FR-19 | Benchmark matrix in `docs/benchmark.md`. | 300 and 2,000 SKUs on HiGHS and CBC with time and gap. The 10k row is first to cut. |
| FR-20 | 75 second video (Remotion, hybrid). | Storyboard locked end of week 6, MP4 embedded in README. |
| FR-21 | Usage events for input metrics. | `scenario_run`, `why_opened`, `compare_opened`, `export_clicked` on a privacy friendly tool. |

**P2: Later, gated by evidence** (not scheduled)

| ID | Item | Gate |
|---|---|---|
| FR-22 | Manual override with live validation (R10, R11). Override is saved as its own scenario (triage conflict). | E3 and a pilot |
| FR-23 | Excel or CSV import (R3). | E2 shows the real input format |
| FR-24 | AI rule drafting (R18): plain language to validated rule diff, planner approves, step logged. | E7 passes |
| FR-25 | AI scenario narrative (R19), numbers checked automatically. | E7 passes and E8 passes (100% numbers match) |
| FR-26 | Decision log with owner, reason, approver (R22) and AI input checks (R20). | E9 passes (A15) |
| FR-27 | Expiry early warning (R17), multi period (R13), theme (R14), BigQuery adapter (R15), duals as advanced mode (R16). | Pilot demand |

### 6. Solution Overview

* Data flows source tables, then `SourceAdapter`, then canonical dataset, then solver input. Decision index is the lot (material by plant by expiry month), per ADR 003.
* Elimination before modeling, then a two phase lexicographic MILP (PuLP, HiGHS default, CBC fallback). Coverage and push use the tight form (ADR 004). Score weights and rule values live in `ZPARAM` and scenario yaml.
* Explainability is rule trace plus on demand counterfactual re solve, not duals.
* Frontend is React and TypeScript, table first. Demo mode reads precomputed JSON, live mode reads the API.
* Full detail: `docs/war_plan.md` sections 4 to 6.

### 7. Open Questions

| # | Question | Owner | Deadline |
|---|---|---|---|
| Q1 | ADR 005 (proposed) defines the baseline as a planner proxy audited by the full checker, and states the property precisely. Remaining: confirm in E2 which rules planners really check by hand and in which order, then accept the ADR. | Nils | Week 1 (accept), week 2 (E2) |
| Q2 | Resolved 2026-10-24: 15 hours per week. Log actuals from week 0 (red team K5). | Nils | Done |
| Q3 | Does a warm start work through the PuLP and HiGHS path used, or does the counterfactual need `highspy` directly? | Nils | Week 2 spike |
| Q4 | Name lock: Reshelf trademark, domain, GitHub org. | Nils | Week 0 |
| Q5 | Cloud Run billing account or go straight to Render? | Nils | Week 6 |
| Q6 | Who are the 8 interviewees, and how are they reached without any confidential data changing hands? | Nils | Week 0 |
| Q7 | Is the illustrative minimum uplift gap 3%? Needs a neutral seed run before it is fixed. | Nils | Week 2 |
| Q8 | Does the assortment rule need a cap on units per category in a channel? The model today caps SKUs per group and channel (`asrt`, `sku`) and total units per channel (`cap`), not units per group. Decide before the generator, because it adds a constraint and a test. | Nils | Week 1 |

### 8. Timeline and Phasing

| Phase | Weeks | Scope | Release |
|---|---|---|---|
| Phase 1a: foundations | 0 to 3 | Repo, data, model, trace, counterfactual, API | Checkpoint 1 (go or pivot on segment) |
| Phase 1b: hero slice | 4 to 6 | UI, parameters, save, compare, Why panel, globe, e2e | Checkpoint 2 (hero decision from E3) |
| Phase 1c: ship | 7 to 8 | Deploy, demo mode, README, ADRs, video | `v0.1.0` live link week 7, `v1.0.0` with video week 8 |
| Phase 2: evidence | 8 to 9 and after | E4 pretotype, E7, then gated P2 items | Decision on pilot |

---

# Part 2. OKRs: build weeks 0 to 9

**Team**: one person with AI pair coding. **Period**: 9 weeks (the 8 week build plus the E4 week).
**Aligned to**: there are no company OKRs. They are derived from the two goals in `2_strategy/1_strategy.md` (prove product and engineering skill, keep a commercial option open) and the metrics trees in `../1_discovery/4_metrics_dashboard.md`.

### Objective 1: Make the hero flow so clear that a stranger can defend an allocation after one click

| # | Key Result | Baseline | Target | Owner |
|---|---|---|---|---|
| KR1.1 | Seeded datasets where optimizer beats greedy under the ADR 005 definition | 0 of 50 | 50 of 50, with median gap at or above the illustrative minimum | Nils |
| KR1.2 | Counterfactual re solve p95 on the 2,000 SKU default scenario | none | Under 5 s | Nils |
| KR1.3 | Planners who explain a line in their own words with the Why panel (E3) | none | 4 of 5 | Nils |
| KR1.4 | Hero flow Playwright test (rule dial, compare, Why panel) | none | Green on every CI run from week 6 | Nils |

### Objective 2: Ship a repo that earns trust in 5 minutes and runs from a cold start

| # | Key Result | Baseline | Target | Owner |
|---|---|---|---|---|
| KR2.1 | Peer reviewers who state problem, user and differentiator correctly (E5) | none | 4 of 5 | Nils |
| KR2.2 | Constraints with a feasible and a violating pytest | 0 of 10 | 10 of 10 | Nils |
| KR2.3 | Live demo cold start to first screen | none | Under 3 s cached | Nils |
| KR2.4 | Video published in README and watched to 75% by viewers | none | Video live week 8; 50% view through in the first 30 days | Nils |

### Objective 3: Find out, with evidence, whether the commercial option is real

| # | Key Result | Baseline | Target | Owner |
|---|---|---|---|---|
| KR3.1 | Problem interviews completed (E2) | 0 | 8, with 5 of 8 describing a manual or Excel process | Nils |
| KR3.2 | Interviews naming a budget owner and 3 or more teams on one allocation (A3, A15) | 0 | 4 of 8 name an owner; 5 of 8 name 3 or more teams | Nils |
| KR3.3 | Practitioners who leave a contact on the pretotype (E4) | 0 | 10% of 200 (floor 3%, below it means rework the message) | Nils |
| KR3.4 | Decision recorded: segment, hero, AI go or no go | none | Written by end of week 9 using the decision table in the discovery plan | Nils |

**Quality check**
* Outcomes, not outputs: no KR counts features shipped.
* Gaming risks and counters: KR1.1 can be gamed by tuning the generator, so the 50 seeds are fixed and published before tuning (red team K2). KR1.3 is counted only when the planner does not see the label text first. KR3.3 is counted per unique visitor from outside the author's network.
* Calibration: 70% is the target zone. KR1.3 at 3 of 5 and KR3.3 at 7% would be a well calibrated result, not a failure.
* The North Star (exported net recovery rate) is not an OKR in v1, because with no real users it only exists as simulated value. It stays the guiding metric for a pilot.

**Alignment map**

```
Prove product thinking     -> O3 (evidence) + O2 (5 minute trust)  -> KR3.x, KR2.1, KR2.4
Prove engineering quality  -> O1 (hero) + O2 (tests, cold start)   -> KR1.x, KR2.2, KR2.3
Keep commercial option     -> O3 (interviews, pretotype, decision) -> KR3.1 to KR3.4
```

**Scoring guide**: 0.0 to 0.3 significant miss, investigate. 0.4 to 0.6 progress but short. 0.7 to 0.9 well calibrated. 1.0 nailed it or too easy.
**Check in cadence**: weekly traffic light on each KR at the end of each sprint, mid period review at the end of week 4 (checkpoint 1 has already happened), score at the end of week 9.

---

# Part 3. Roadmap and sprint plan

### Capacity assumption (confirm in Q2)

| Item | Value | Note |
|---|---|---|
| Hours per week | 15 | Confirmed 2026-10-24. The war plan says "part time" without a number |
| Planning ratio | 12 committed, 3 buffer | 80% rule for solo work, with a hard 20% buffer |
| Method | Hours, not story points | One person, no velocity history yet |
| Measure | Log actual hours per story in weeks 0 and 1, then recompute a velocity factor | If actuals exceed estimates by more than 30%, apply the cut order at once, not in week 7 |

Build and discovery share the same 15 hours. Discovery hours are shown in their own lane.

### Ordering logic

1. Foundations that every later week depends on (data, model, constraints).
2. The Why panel and compare reach a thin working slice by week 4, not week 6. They are the hero and are "never cut", so they should not be the last thing built (change C1 in Part 6).
3. Hook and polish (globe, deep dive, Excel polish) come after the hero works, because they are on the cut list.
4. Discovery runs in parallel and gates the roadmap at three checkpoints.
5. AI and process features (R18 to R22) are gated by E7, E8, E9 and are not scheduled.

### Ordered backlog (the roadmap)

Hours are estimates, plus or minus 50%. Status is `todo` for all.

**Sprint 0 (week 0): Repo and discovery kick off.** Goal: repo public, CI green, interviews booked.

| Story | What | FR | Hours | Depends on |
|---|---|---|---|---|
| RS-001 | Fresh repo, `uv` and `pnpm` tooling, Makefile skeleton | FR-15 | 2 | none |
| RS-002 | ADR 001 (stack), license and provenance note | FR-15 | 1 | RS-001 |
| RS-003 | Empty CI: lint, type check, test, build | FR-15 | 1.5 | RS-001 |
| RS-004 | Name lock checks (GitHub org, domain, trademark) | none | 0.5 | none |
| D-01 | E1 desk research started, E2 script and recruit list (Q6) | none | 5 | none |

Build 5, discovery 5. Done when: repo public, CI green.

**Sprint 1 (week 1): Data.** Goal: a reproducible synthetic world with tuned story hooks.

| Story | What | FR | Hours | Depends on |
|---|---|---|---|---|
| RS-010 | `docs/erd.md` and `docs/mapping.md` | FR-02 | 2 | RS-002 |
| RS-011 | Rule defaults in `ZPARAM` style yaml, scenarios `default` and `luxury_protection` | FR-01 | 1.5 | RS-010 |
| RS-012 | Seeded generator with aging, ABC skew, seasonality, tier mix, and distribution tests | FR-01 | 4 | RS-011 |
| RS-013 | `make demo-data` hash test | FR-01 | 0.5 | RS-012 |
| RS-014 | ADR 005: planner proxy baseline and comparison rule (Q1), review the draft | FR-05 | 1 | none |
| D-02 | E2 interviews, 4 of 8 (includes E9 process questions) | none | 4 | D-01 |

Build 9, discovery 4 (13, one hour into the buffer). Done when: `make demo-data` reproducible, distribution tests pass.

**Sprint 2 (week 2): Model.** Goal: the optimizer beats greedy under the agreed definition on neutral seeds.

| Story | What | FR | Hours | Depends on |
|---|---|---|---|---|
| RS-020 | Canonical Pydantic and pandera schema, CSV adapter | FR-02 | 2.5 | RS-012 |
| RS-021 | Elimination with reason codes | FR-03 | 1.5 | RS-020 |
| RS-022 | Solver core: `Solver` protocol, named constraints, two phase objective | FR-04 | 3.5 | RS-021 |
| RS-023 | Planner proxy baseline, audit by the full checker, deterministic repair | FR-05 | 2 | RS-021 |
| RS-024 | One pytest per constraint, feasible and violating | FR-04 | 1.5 | RS-022 |
| RS-025 | Spike: neutral seed uplift run on 50 seeds, fix the minimum gap (Q7); warm start check (Q3) | FR-05, FR-08 | 1.5 | RS-022, RS-023 |
| D-03 | E2 interviews, remaining 4, coding of notes | none | 3 | D-02 |

Build 12.5, discovery 3 (15.5, no buffer left: this is the most loaded week with the model). Done when: pytest green, uplift gap fixed on neutral seeds.

**Sprint 3 (week 3): Trust engine and API.** Goal: every line explainable, endpoints in OpenAPI, benchmark written. Checkpoint 1.

| Story | What | FR | Hours | Depends on |
|---|---|---|---|---|
| RS-030 | Property test and edge tests (infeasible, empty, single channel, all eliminated) | FR-04, FR-05 | 2 | RS-025 |
| RS-031 | KPIs including brand risk index | FR-06 | 1.5 | RS-022 |
| RS-032 | Rule trace from constraint slack and elimination codes | FR-07 | 2.5 | RS-022 |
| RS-033 | Counterfactual re solve, including elimination rule relaxation | FR-08 | 3 | RS-032, RS-025 |
| RS-034 | Benchmark 300 and 2,000 SKUs on HiGHS (CBC and 10k if time) | FR-19 | 1 | RS-022 |
| RS-035 | FastAPI endpoints, minimal SQLite persistence, generated TS types, drift check | FR-09 | 2.5 | RS-031 |
| D-04 | Checkpoint 1: E6 result and E2 decision (go or pivot on segment) | none | 1 | D-03 |

Build 12.5, discovery 1. Done when: endpoints in OpenAPI, benchmark table written, checkpoint 1 decision written in `../1_discovery/`.
**Gate**: if the model, trace, counterfactual or API is not green here, apply the cut order now and drop the live API from the plan (static only).

**Sprint 4 (week 4): Hero slice.** Goal: a thin but real hero flow on precomputed JSON.

| Story | What | FR | Hours | Depends on |
|---|---|---|---|---|
| RS-040 | Web shell, generated types, demo mode loader, banner | FR-14 | 3 | RS-035 |
| RS-041 | `make precompute`: seeded scenarios, top counterfactuals, rule dial grid | FR-08, FR-14 | 2.5 | RS-033 |
| RS-042 | Stock overview: KPI tiles and virtualized lot table with filters | FR-10 | 3 | RS-040 |
| RS-043 | Thin hero slice: results table, compare of two scenarios, Why panel (plain styling allowed) | FR-12, FR-13 | 3.5 | RS-041, RS-042 |

Build 12. Done when: a person can dial a rule, see the euro delta and open a Why panel on precomputed JSON.

**Sprint 5 (week 5): Planner flow.** Goal: full planner flow runs end to end locally. E3 starts on the week 4 slice.

| Story | What | FR | Hours | Depends on |
|---|---|---|---|---|
| RS-050 | Parameter editor and run, rule dial on the precomputed grid | FR-11 | 3.5 | RS-043 |
| RS-051 | Results charts: inflow and outflow waterfall, KPIs vs greedy | FR-11 | 3 | RS-043 |
| RS-052 | Scenario save and load | FR-12 | 2 | RS-050 |
| RS-053 | Excel export, generic order creation format | FR-17 | 2 | RS-051 |
| D-05 | E3 walkthrough, 5 planners, Why panel off and on | none | 2.5 | RS-043 |

Build 10.5, discovery 2.5 (13). Done when: planner flow runs end to end locally.

**Sprint 6 (week 6): Hero polish and hook.** Goal: hero flow works, Playwright passes, storyboard locked. Checkpoint 2.

| Story | What | FR | Hours | Depends on |
|---|---|---|---|---|
| RS-060 | Why panel full: plain language reasons, blocked channels, counterfactual euros | FR-13 | 3.5 | RS-043 |
| RS-061 | Compare polish: KPI deltas, parameter impact, brand risk always visible | FR-12 | 2 | RS-052 |
| RS-062 | Globe with table filter, lazy loaded, fallback | FR-16 | 3 | RS-042 |
| RS-063 | Playwright test of the hero flow | FR-15 | 1.5 | RS-060, RS-061 |
| D-06 | E3 readout, hero decision, E7 wizard of Oz, storyboard lock | none | 2.5 | D-05 |
| RS-064 | Material deep dive (stretch, first to cut) | FR-18 | 2 | RS-060 |

Build 10 plus 2 stretch, discovery 2.5. Done when: hero flow works, e2e green, checkpoint 2 decision written.

**Sprint 7 (week 7): Ship.** Goal: live link works from a cold start. Release `v0.1.0`.

| Story | What | FR | Hours | Depends on |
|---|---|---|---|---|
| RS-070 | Docker, compose, devcontainer | FR-15 | 2 | RS-063 |
| RS-071 | CI/CD deploy: static frontend, API on Cloud Run or Render (Q5) | FR-14 | 2.5 | RS-070 |
| RS-072 | Live switch with health check, cold start test | FR-14 | 1.5 | RS-071 |
| RS-073 | README with hero GIF, 3 commands, limitations, roadmap | FR-15 | 2.5 | RS-063 |
| RS-074 | ADRs finalized, `docs/model.md`, `docs/benchmark.md` | FR-15, FR-19 | 2 | RS-034 |
| RS-075 | Screenshots, GIF, social preview | FR-15 | 1 | RS-073 |
| D-07 | E5: 5 peer reviews, README fixes | none | 1.5 | RS-073 |

Build 11.5, discovery 1.5 (13). Done when: live link works from a cold start.

**Sprint 8 (week 8): Video and pretotype.** Goal: 75 second MP4 embedded in README. Release `v1.0.0`.

| Story | What | FR | Hours | Depends on |
|---|---|---|---|---|
| RS-080 | Remotion project, hybrid shots from real components with fixture JSON | FR-20 | 4 | RS-075 |
| RS-081 | Scenes from the locked storyboard, Playwright captures | FR-20 | 4 | RS-080 |
| RS-082 | Render and embed in README | FR-20 | 1 | RS-081 |
| D-08 | Build E4 landing page with the video | none | 2 | RS-082 |

Build 9, discovery 2. Done when: MP4 embedded in README.

**Sprint 9 (week 9): Evidence.** Goal: E4 result and the written decision. No new features.

| Story | What | Hours |
|---|---|---|
| D-09 | Run E4 in 3 practitioner communities, record results | 3 |
| D-10 | Decision memo: segment, hero, AI go or no go, pilot go or no go | 2 |
| RS-090 | Sprint retro and release notes for v1.0.0 | 1.5 |

**Definition of done (every story)**
- [ ] Tests written and green, with a feasible and a violating case for any new constraint
- [ ] Lint, type check and build green in CI
- [ ] No real name, value or figure (clean room check)
- [ ] Reproducible: seeds fixed, hero elements carry stable `data-testid`
- [ ] Docs and ADR updated where a major choice was made

**Gates and decisions** (from the discovery plan, section 6)

| When | Gate | Outcome that changes the roadmap |
|---|---|---|
| End of week 3 | E2 and E6 (checkpoint 1) | E2 below 3 of 8 means test the nearest segment before more UI. Build over capacity means cut order now |
| End of week 6 | E3 and E7 (checkpoint 2) | Variant B not better than A promotes compare to hero and demotes the Why panel. E7 pass schedules FR-24 |
| End of week 7 | E5 | Fail means rewrite README top and this folder's index before adding anything |
| End of week 9 | E4 and the decision memo | Above 10% drafts a pilot offer. Below 3% reworks the message first |

### Later (not scheduled, in evidence order)

| Order | Item | Needs |
|---|---|---|
| 1 | FR-24 AI rule drafting | E7 pass |
| 2 | FR-26 decision log, AI input checks | E9 pass |
| 3 | FR-25 AI narrative | E7 and E8 pass |
| 4 | FR-23 Excel import | E2 shows the real format |
| 5 | FR-22 manual override with live validation | Pilot |
| 6 | FR-27 early warning, multi period, theme, BigQuery, duals | Pilot demand |

**Declined**: an AI that chooses allocations (R21).

### Capacity check

| Item | Hours |
|---|---|
| Available (9 weeks at 15) | 135 |
| Committed build, sprints 0 to 8 | 5 + 9 + 12.5 + 12.5 + 12 + 10.5 + 10 + 11.5 + 9 = 92 |
| Committed discovery, sprints 0 to 9 | 5 + 4 + 3 + 1 + 0 + 2.5 + 2.5 + 1.5 + 2 + 5 = 26.5 |
| Stretch (deep dive) and retro | 3.5 |
| Total | 122 |
| Remaining buffer | 13 (10%) |

The buffer is thinner than the 20% rule because weeks 1 and 2 run hot. This is the main schedule risk and it is why the week 3 gate exists.

---

# Part 4. Red team

**Plan attacked**: v1 is a table first demo whose hero is the euro cost of a rule explained by a Why panel, built in 8 part time weeks on synthetic data, while discovery runs in parallel.

### Top kill assumptions (ranked)

**K1. The Why panel and the euro cost of a rule are what planners and reviewers value (A2, A8).**
* **Claim**: four of five top asks are about trust, so the Why panel is the hero.
* **Steelman**: trust is the usual blocker for optimizer adoption, and a euro figure is the one thing a spreadsheet cannot give fast.
* **Fails if**: planners already know roughly what their rules cost and the real pain is data cleaning, late inputs or the hand off to the system of record. Then the Why panel is a nice demo and the product is the process (A15).
* **Evidence to get this week**: all five "top asks" come from one source, the author. Signal count is 1 for every request.
* **Kill criterion**: in E2, fewer than 3 of 8 mention being challenged on a rule, or fewer than 3 of 8 say they would want the cost, then the Why panel is demoted and compare or the process becomes the hero.
* **Cheapest test**: add a static mock of the Why panel and the compare table to interviews 5 to 8 in week 2 (about 2 hours), instead of waiting for E3 in week 5 to 6. Ask "what would you do with this?" and watch for questions about data instead.

**K2. "The optimizer clearly beats the greedy baseline" is evidence of value.**
* **Claim**: the seeded story shows a visible gap, and a property test asserts the optimizer is at least as good as greedy.
* **Steelman**: a fair baseline with the same checker is exactly how credible demos work, and a CI assertion is stronger than a screenshot.
* **Fails if**: (a) the generator is tuned until the gap appears, so a reviewer sees circular proof; (b) greedy is a straw man (one pass by value at risk) that nobody uses; (c) the property is false by construction: phase 1 maximizes the SKU score with a 1% tolerance, and greedy ignores the score, so net value of the optimizer can be lower than greedy while still "winning" on score. As written in CLAUDE.md and the war plan ("optimizer value at least greedy value") the test is ambiguous and may fail on valid solutions or pass trivially.
* **Evidence to get this week**: none in the plan yet.
* **Kill criterion**: on 50 neutral seeds drawn before any tuning, median uplift below the illustrative minimum (proposed 3%), or any seed where the chosen comparison fails.
* **Resolution (2026-10-24)**: ADR 005 defines the baseline as a planner proxy that applies fewer rules, audited by the full checker, and states the property precisely. The stronger baseline below becomes the sensitivity check `baseline_expert`.
* **Cheapest test**: write ADR 005 in week 1 (Q1). In week 2 run the spike RS-025 with a stronger baseline (all rules plus one pass of local swaps) as a second reference. If the gap over the stronger baseline shrinks to nothing, reframe the story around explainability and brand cost, not around uplift.

**K3. A reachable, painful, payable need exists (A1, A3, A4, A15).**
* **Claim**: planners handle this by hand and someone would pay.
* **Steelman**: the leap of faith is named, gated and has a kill criterion (E2, 5 of 8).
* **Fails if**: the 8 interviewees come from one personal network and one company type, so the sample says "yes" for the wrong reason, or the stock is handled by a returns or liquidation team and not by planners. Also fails if the portfolio goal quietly overrides a no from the market.
* **Kill criterion**: below 3 of 8 describing a manual process, or none naming a budget owner.
* **Cheapest test**: recruit 2 of the 8 outside beauty (other dated goods) and 2 from reverse logistics to test the segment boundary. Write the decision rule down before the first call. Record the portfolio versus product conclusion separately, so a product "no" is not read as a project failure.

**K4. A static, precomputed demo shows the hero flow honestly.**
* **Claim**: reading JSON by default gives an instant demo and the banner keeps it honest.
* **Steelman**: always instant, no cold start, and a banner states what is cached.
* **Fails if**: a reviewer tightens a rule to a value that was not precomputed and nothing changes, or concludes the demo is a video of a fake. The hero is exactly "tighten a rule", which is the interaction a static site handles worst.
* **Kill criterion**: in a click test, any of 3 reviewers asks "is this real?" and cannot get an answer in 30 seconds, or any dial position returns no result.
* **Cheapest test**: precompute a dial grid (FR-14, RS-041), then run a 3 person click test at the end of week 4 on the thin slice. Add "Run it yourself in 3 commands" next to the banner.

**K5. Eight part time weeks cover the MVP.**
* **Claim**: each week is a vertical slice that ends green.
* **Steelman**: the plan has a cut order, a "not built" column and a never cut list, which is better than most solo plans.
* **Fails if**: weeks 2 and 3 (model, trace, counterfactual, API, benchmark) run over, because every later week depends on them, and the hero slice then gets built in a rush at week 6. The war plan has no hour figure, so over commitment is invisible.
* **Kill criterion**: at the end of week 3, any of model, trace, counterfactual or API not green, or actual hours more than 30% over estimates in weeks 0 and 1.
* **Cheapest test**: log actual hours per story from week 0 (zero cost). Apply the cut order at the week 3 gate instead of week 7.

### What is well reasoned

* The AI stance: the solver decides, AI drafts, explains and checks, with a validated diff, human approval, a log and gated experiments (E7, E8). Declining R21 protects the explainability that is the product.
* Rule trace plus counterfactual instead of duals: exact, readable, in euros, and it avoids a local and degenerate explanation.
* Tight form constraints (ADR 004), elimination with reason codes, `Solver` and `SourceAdapter` protocols: a sound, portable design.
* Evidence discipline: every experiment has a success criterion and a decision table, and tags separate verified claims from hypotheses.
* Clean room rules and a fixed cut order with a "never cut" list.
* The strategy is honest that today there is no defensibility.

### What I could not assess

* Competitor claims (A11): E1 desk research has not run, so the value curve is unverified.
* Whether a warm start works through the PuLP and HiGHS path, which drives counterfactual speed (Q3).
* The real hours available (Q2) and whether AI pair coding keeps estimates within 50%.
* Whether the 5 minute reviewer exists in the numbers that A5 assumes.

---

# Part 5. Pre mortem

**Launch defined as**: `v1.0.0` public repo, live demo and 75 second video at the end of week 8.
**Imagined failure**: three months after launch there are few visits, no conversations, and the people who did look said "nice demo, I do not get why".

### Risk summary
* **Tigers**: 8 (4 launch blocking, 3 fast follow, 1 track)
* **Paper tigers**: 5
* **Elephants**: 5

### Launch blocking tigers

| # | Risk | Likelihood | Impact | Mitigation | Owner | Deadline |
|---|---|---|---|---|---|---|
| T1 | The optimizer vs greedy gap looks rigged or is false by definition (red team K2) | High | High | ADR 005 (planner proxy baseline, audited by the full checker), 50 neutral seeds published, expert baseline as sensitivity check, report the full uplift distribution and the violations in README | Nils | Week 2 |
| T2 | Counterfactual does not work for elimination rules, the exact rule used in the hero ("luxury protection costs X euros"). Tier and shelf life are removed before modeling, so there is no constraint slack to read | Medium | High | Counterfactual rebuilds the admissible set for elimination rules. Add as an explicit acceptance criterion in FR-08 and a test on the luxury scenario | Nils | Week 3 |
| T3 | Static demo breaks the hero (red team K4) | High | High | Dial grid precompute, click test on the week 4 slice, banner, "run it yourself" | Nils | Week 4 |
| T4 | Clean room breach: a figure, name, column or structure that echoes something real appears in code, data, screenshots or docs | Low | Very high | Clean room check in the definition of done, one scan of the repo for forbidden terms before each release, `_private/` never read into committed text, a rule that every value is tagged "illustrative default" | Nils | Every PR, before v0.1.0 |

### Fast follow tigers

| # | Risk | Likelihood | Impact | Planned response | Owner |
|---|---|---|---|---|---|
| T5 | Why panel text is jargon for non OR users (A8) | Medium | High | E3 wording test, rewrite templates, add plain language glossary | Nils |
| T6 | Week 2 and 3 overrun pushes hero work to the end (red team K5) | High | High | Week 3 gate with cut order, log actual hours | Nils |
| T7 | Free tier cold start or solver time makes live mode flaky | Medium | Medium | Cached mode is the default, health check before switching, time limit and gap shown | Nils |

### Track tigers

| # | Risk | Trigger condition |
|---|---|---|
| T8 | Reviewers conclude "synthetic data means no proof of value" | E5 shows 2 or more of 5 voicing this: add a "what a pilot would measure" section to the README and a clear limitations block |

### Paper tigers

| Concern | Why it is manageable | Becomes real if |
|---|---|---|
| HiGHS cannot solve 2,000 SKUs in seconds | Lot level model with monthly buckets and tight constraints keeps size small, and E6 tests it in week 3 | Benchmark p95 over 30 s, then cut the demo to 300 SKUs and report the gap |
| Globe is slow on low end laptops | Lazy loaded with a table fallback, and the globe is a filter not the workflow | The fallback is hit by most reviewers |
| Name collision or weak trademark | Working name only, renaming a repo is cheap | A paid pilot appears |
| Cloud Run billing | Static plus cached mode needs no backend, Render is the fallback | The live API is promised as a feature |
| BigQuery is only a stub | It is documented as a stub and portability is shown through the adapter protocol | A pilot uses BigQuery |

### Elephants in the room

| # | Elephant | Conversation starter |
|---|---|---|
| E-1 | Nobody may want this. The project can succeed as a portfolio piece while the product fails, and the two can blur | "If E2 says no, what do we write in the decision memo, and does the project change?" |
| E-2 | All 22 requests come from one person's experience. Signal is 1 everywhere | "Which three requests would I drop if the first two interviews disagree?" |
| E-3 | The video and the globe are the strongest attention hooks, and also the easiest places to overspend time | "What is the cap, in hours, on the video before the Why panel is considered done?" |
| E-4 | Synthetic data tuned by the author can be read as marketing, not evidence | "Would a skeptical reader trust the story if they had only the generator and the seeds?" |
| E-5 | Solo bus factor and motivation over 9 weeks: if two weeks are lost, the plan has no slack | "What is the smallest shippable v1 if only 5 weeks are real?" The answer is the cut order plus the thin slice from week 4 |

### Go / no go checklist (for v1.0.0)
- [ ] T1, T2, T3, T4 mitigated and each has a test or a written check
- [ ] Fast follow plan documented (T5, T6, T7)
- [ ] Monitoring: weekly CI health, cold start check, README link check
- [ ] Rollback: previous tag stays live, the static demo can be redeployed from `data/precomputed`
- [ ] README states limitations: synthetic data, simulated KPIs, no real impact claimed
- [ ] The five red team kill criteria have recorded results or a written reason for being skipped

---

# Part 6. Changes to the plan

| # | Change | Why | Source | Needs your decision |
|---|---|---|---|---|
| C1 | Move a thin Why panel and compare slice from week 6 to week 4. Globe moves from week 4 to week 6 | The hero and the "never cut" items should not be the last thing built. E3 needs something to show in week 5 | K5, T6 | Decided 2026-10-24, war plan section 7 updated |
| C2 | Write ADR 005 in week 1 to define the optimizer vs greedy comparison | The property test in CLAUDE.md is ambiguous with a lexicographic objective | K2, T1 | Decided 2026-10-24, ADR 005 drafted, CLAUDE.md and war plan 5.7 updated |
| C3 | Precompute a rule dial grid, not only named scenarios | The hero interaction must work on a static site | K4, T3 | No, adds 1 hour to RS-041 |
| C4 | Counterfactual must support elimination rules (tier, shelf life) | The hero example is an elimination rule | T2 | No, becomes a FR-08 criterion |
| C5 | Add a static Why panel mock to interviews 5 to 8 in week 2 | Tests K1 three weeks before E3 | K1 | No |
| C6 | Add a stronger second baseline and 50 neutral seeds before tuning | Removes the circular proof reading | K2 | No |
| C7 | Log actual hours and add the week 3 capacity gate | Capacity is the biggest silent risk | K5 | No |
| C8 | Recruit 2 interviewees outside beauty and 2 from reverse logistics | Tests the segment boundary | K3 | No |

## Next steps

1. Review ADR 005 (`docs/adr/0005-planner-proxy-baseline.md`). C1, C2 and the 15 hours per week are decided (2026-10-24). Decide Q8 (units per category cap).
2. Write the test scenarios (`2_test_scenarios.md`) for the P0 requirements, starting with the constraints and the hero flow.
3. Stakeholder map is written in `../2_strategy/6_stakeholder_map.md` (hypotheses, update after E2).
4. Update `../README.md` with the `3_execution/` folder row.
