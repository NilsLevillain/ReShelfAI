# ADR 005: Planner proxy baseline and the optimizer comparison

**Status**: Accepted (2026-10-25)
**Deciders**: Nils
**Related**: `docs/war_plan.md` sections 5.7 to 5.9, `product_management/3_execution/1_backlog.md` (FR-05, red team K2, pre mortem T1)

> Evidence level: the description of what a planner does by hand is a hypothesis (H). Interview experiment E2 must confirm which rules planners really check and in which order. Nothing here claims a measured result.

## Context

The product claim is "the optimizer does better than the manual way". The first version of the plan defined the baseline as a greedy algorithm that uses the same constraint checker as the optimizer, plus a test that optimizer value is at least greedy value.

Two problems:

1. **It is not what a planner does.** A planner works in Excel, applies a few rules by hand (is the stock still sellable in that channel, is the brand allowed there, is there room), and does not hold assortment limits, coverage needs and push quantities in mind at once. Manual work is slow and errors slip in. A baseline that obeys every rule is a stronger opponent than reality and hides the value of the optimizer, which is to respect all rules together.
2. **The test is ambiguous.** The optimizer maximizes the SKU score first and net value second, within a tolerance. A baseline plan can have higher raw net value while breaking rules, or lower score. "Value at least greedy value" can fail on a valid optimizer result or pass for the wrong reason.

## Options

| Option | Upside | Downside |
|---|---|---|
| A. Greedy with the full rule set (original plan) | Simple. Provably feasible | Not a planner. Understates the benefit. Ambiguous test |
| **B. Planner proxy with fewer rules, audited by the full checker** | Resembles manual work. Violations become visible and countable. Fair because the audit uses the same rules as the optimizer | The list of rules a planner applies is a hypothesis. Needs a repair step to get a comparable compliant plan |
| C. Simulate random human errors | Looks realistic | Not reproducible, easy to call rigged, no evidence for the error rate |
| D. Expert baseline (all rules plus local swaps) only | Hard opponent, hard to accuse of a straw man | Not what a planner does. Used as a sensitivity check, not as the headline |

## Decision

Choose **B** as the headline baseline, with **D** as a sensitivity check.

### 1. The planner proxy (`baseline_planner`)

* Orders lots by value at risk (units times unit cost times urgency).
* Sends each lot to the admissible channel with the best recovery factor that still has capacity.
* **Rules applied by hand (default, illustrative):** remaining shelf life, brand tier, channel capacity in units.
* **Rules not applied:** SKU limit per channel, assortment limit per group, coverage bounds, push quantities. These are exactly the rules that are hard to hold in a spreadsheet.
* The list of applied rules is a parameter in the scenario yaml (`planner_rules`), so the demo can show a stricter planner and the sensitivity of the uplift to it.
* No random errors are simulated. Errors appear as violations found by the audit.

### 2. The audit

The full constraint checker used by the optimizer runs on the baseline plan and returns, for each named constraint, the number of violating lines and the units concerned. The audit is a pure function of the plan, so it is reproducible and testable.

### 3. Three baseline numbers, always shown

| Number | Meaning |
|---|---|
| Raw value | Net value of the plan as the planner would sign it, including lines that break rules |
| Violations | Count and units per named constraint, from the audit |
| Compliant value | Net value after a deterministic repair that drops violating lines, lowest net value per unit first, until the full checker accepts the plan |

The compliant value is what survives review. The raw value is shown beside it so that the comparison cannot hide that a plan looks better on paper.

### 4. The property test

On 50 neutral seeds (the seed list is committed before any tuning and never edited), for each seed with optimizer score `S_opt`, net value `V_opt`, and compliant baseline score `S_b`, net value `V_b`:

1. `S_opt >= S_b` (up to the phase 1 MIP gap).
2. If `S_b >= (1 - epsilon) * S_opt`, then `V_opt >= V_b` (up to the phase 2 MIP gap), because the baseline is then feasible for phase 2.

The test never compares the optimizer to the raw value. The raw value is reported, not asserted.

### 5. Sensitivity check (`baseline_expert`)

All rules applied plus one pass of local swaps. Run on the same 50 seeds in CI. The result is recorded in the uplift distribution file used by the README. If the median gap over `baseline_expert` is zero, the story is reframed around explainability and brand cost, not around uplift (red team K2).

### 6. Reporting

The README and compare view show the median, minimum and maximum uplift over the 50 seeds, not only the hero seed. The text states that the planner proxy is a model of manual work, not a measurement of real planners.

## Consequences

* `CLAUDE.md` and `docs/war_plan.md` sections 5.7 and 5.9 change from "same constraint checker, optimizer value at least greedy value" to this decision.
* FR-05 and test scenarios TS-060 to TS-069 follow this ADR.
* The seeded story gets a second source of drama: the baseline plan breaks assortment and coverage rules, and the audit shows how many units. This needs the generator to produce enough assortment pressure (a week 1 task).
* No claim of time saved is made. Time and error rate would need a pilot measurement.
* Open: which rules planners really apply by hand, and in what order. Check in E2 and update `planner_rules` defaults.
* Open: the repair order (lowest net value per unit first) is a choice. Document the alternative of dropping whole lots.
