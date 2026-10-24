# Feature Request Triage Report: Reshelf

**Date**: 2026-10-24
**Requests analyzed**: 17
**Themes identified**: 5

> Evidence level: all requests come from the founder's product experience and the war plan. None is validated by an interview yet. The "signal" column therefore means "how many independent sources mention it", which is 1 for everything until `discovery_plan.md` experiment E2 runs. Treat priorities as a starting order, to be re ranked after interviews.

**Strategic goals used for alignment**
1. Prove the hero flow: tighten a rule, see the cost, see why.
2. Ship the MVP in 8 weeks, part time, with tests and docs.
3. Keep the design portable and the repo credible for hiring managers.

## Request list

| ID | Request | Theme |
|---|---|---|
| R1 | Sortable, filterable tables as the main UI, charts secondary | Table first workflow |
| R2 | Excel export in an order creation format | Excel round trip |
| R3 | Excel or CSV import of inputs | Excel round trip |
| R4 | Explanation for each recommendation | Trust and explainability |
| R5 | Counterfactual cost of each binding rule | Trust and explainability |
| R6 | Plain language reason for each blocked channel | Trust and explainability |
| R7 | Save and load scenarios | Scenario work |
| R8 | Compare scenarios with KPI deltas | Scenario work |
| R9 | Show the effect of a parameter on the solution | Scenario work |
| R10 | Manual override of the proposed allocation | Expert control |
| R11 | Live rule validation during override | Expert control |
| R12 | Brand protection as a first class objective | Expert control |
| R13 | Allocation over several time periods | Scale and breadth |
| R14 | Light and dark theme | Scale and breadth |
| R15 | BigQuery adapter | Scale and breadth |
| R16 | MILP duals as an advanced explain mode | Trust and explainability |
| R17 | Expiry early warning timeline | Scale and breadth |

## Theme summary

| # | Theme | Requests | Top ask | Alignment | Impact | Effort | Priority |
|---|---|---|---|---|---|---|---|
| 1 | Trust and explainability | 4 (R4, R5, R6, R16) | Counterfactual cost per rule | High | H | M | **P1** |
| 2 | Scenario work | 3 (R7, R8, R9) | Compare with KPI deltas | High | H | M | **P1** |
| 3 | Table first workflow | 1 (R1) | Sortable filterable tables | High | M | S | **P1** (foundation) |
| 4 | Excel round trip | 2 (R2, R3) | Excel export | Medium | H for adoption, L for the demo | S for export, M for import | **P2** |
| 5 | Expert control | 3 (R10, R11, R12) | Manual override | Medium | M | L | **P2** |
| 6 | Scale and breadth | 4 (R13, R14, R15, R17) | Several periods | Low for MVP | M | L to XL | **P3 / P4** |

Counts: 17 requests in 6 groups. The five themes named in the header merge Table first into the MVP baseline; it stays listed separately because it shapes every screen.

## Priority 1: Act now

* **Trust and explainability** (4 requests). It is the hero and the main differentiator.
  * Build R4 (rule trace), R5 (counterfactual, warm started, top rules precomputed) and R6 (plain language wording).
  * Defer R16 (duals): rejected for v1, kept as an advanced toggle.
  * Action: build.
* **Scenario work** (3 requests). R9 comes free once R8 exists, because parameter impact is a compare between two scenarios.
  * Action: build R7, R8, R9 together.
* **Table first workflow** (R1). Not a feature, a design rule. Virtualized tables are the primary surface; the globe filters them.
  * Action: build, as the UI baseline.

## Priority 2: Plan next

* **Excel round trip**. Export (R2) is cheap and is the adoption gate for the target user, so keep it in the MVP. Import (R3) waits until interviews confirm the input format people really use. Action: build R2; investigate R3.
* **Expert control**. Manual override (R10) with live validation (R11) is a strong trust feature but the largest effort in the set. R12 (brand protection) already exists as the brand risk index and the "luxury protection" scenario; promoting it to a full objective is second wave. Action: prototype R12 in the seeded story; plan R10 and R11 after week 8.

## Priority 3: Collect more signal

* **R17 Expiry early warning**. Tests whether the problem starts upstream. Run the interview question in E2 before building.
* **R13 Several periods**. Valuable for real use, expensive in model size. Wait for pilot demand.

## Priority 4: Decline or defer

| Request | Reason |
|---|---|
| R14 Light and dark theme | Cosmetic, zero effect on the hero. Roadmap |
| R15 BigQuery adapter | Keep the interface and an ADR; a working connector has no value without a user |
| R16 Duals explain mode | Rejected for v1 in the war plan (locally valid, degenerate, hard to explain) |

## Notable conflicts and tensions

* R1 (tables first) versus the globe as the visual hook: resolved by making the globe a filter on the table, with a table fallback.
* R12 (brand protection) versus recovery value: not a bug, it is the product's central trade off. It has to stay visible in compare.
* R10 (override) versus R8 (compare): an overridden allocation must be a saved scenario with its own KPIs, or the comparison loses meaning.

## Patterns and insights

* Four of the five top asks are about **trust**, not speed. Planners decide faster only when they can defend the decision.
* The need behind "Excel export" is **hand off to the system of record**, not Excel as such. Keep the order creation format generic and documented.
* "Parameter impact" and "scenario compare" are one capability seen from two sides. Do not build them twice.
* Next evidence step: interviews E2 should ask about the last allocation decision, who challenged it, and in which tool the result ended up.

## Next steps

Set up the metrics and the North Star (`/setup-metrics`). Then user stories for P1 themes.
