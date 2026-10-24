# Brainstorm: Reshelf

**Mode**: Ideas and experiments for a new product
**Date**: 2026-10-24
**Context**: Reshelf allocates stock that cannot go through primary retail to second life channels, under business rules, and explains every decision. The first discovery round is in `discovery_plan.md`. This round adds ideas that are not yet in it.

---

## Ideas

### PM perspective
1. **Rule cost leaderboard** | A ranked list of the rules that cost the most value in a scenario ("min shelf life of 60% costs 41k"). Turns the Why panel into a negotiation agenda. | Impact: H | Effort: M
2. **Decision log and approvals** | Each saved scenario carries an owner, a reason and an approver. Gives audit trails to compliance and finance. | Impact: M | Effort: M
3. **Stock health score per material** | One number mixing remaining shelf life, demand and channel fit, so planners triage fast. | Impact: M | Effort: L
4. **Pilot in a box** | A guided import of one month of real data with a prefilled report. Shortens the path from demo to first pilot. | Impact: H | Effort: H

### Designer perspective
1. **Rule dial with live cost** | Drag a rule slider and see the euro delta update on a small chart, without leaving the page. Makes the hero flow tactile. | Impact: H | Effort: M
2. **Story mode** | A guided tour that walks through the seeded story in 5 steps. Doubles as the demo for recruiters. | Impact: H | Effort: L
3. **Table first with a globe as a lens** | The globe filters the table and never replaces it. Keeps the Excel mindset of the user. | Impact: M | Effort: L
4. **Plain language explanations** | Each trace line reads as a sentence ("Blocked from donation because it is a luxury tier item"). Lowers the barrier for non OR users. | Impact: H | Effort: L

### Engineer perspective
1. **Reason codes on every elimination** | Already planned. Make them a public, versioned vocabulary so every UI and export uses the same words. | Impact: H | Effort: L
2. **Warm started counterfactuals** | Re solve from the current solution; precompute the top rules in CI. Keeps the Why panel instant. | Impact: H | Effort: M
3. **Deterministic scenario hash** | Same inputs and seed give the same hash and the same result. Enables caching, sharing links and reproducible tests. | Impact: M | Effort: L
4. **Solver and adapter protocols as the public contract** | Lets contributors add a connector or a solver without touching the core. Shows platform thinking in the repo. | Impact: M | Effort: M

## Top 5 recommendations

| Rank | Idea | Why | Quick win? |
|---|---|---|---|
| 1 | Rule dial with live cost (Designer 1) | It is the hero flow in one gesture: tighten a rule, see the cost | No, plan for week 6 |
| 2 | Plain language explanations (Designer 4) | Lowest effort way to make explainability real for non technical users | Yes |
| 3 | Rule cost leaderboard (PM 1) | Gives the Why panel a "so what" at scenario level | No |
| 4 | Story mode (Designer 2) | Serves both discovery goals: planners and hiring managers | Yes |
| 5 | Warm started counterfactuals (Engineer 2) | The feasibility risk behind the hero; must hold | No |

Parked: Pilot in a box (needs a first customer), Decision log (after the first pilot).

---

## Experiments (new product, XYZ hypotheses)

### Hypotheses
1. At least 60% of 5 planners will explain a line allocation correctly after reading a plain language trace, within a 10 minute session.
2. At least 4 of 8 interviewees will name a rule they would tighten or loosen if they saw its euro cost.
3. At least 10% of 200 practitioners who see the 75 s video will leave a contact for a pilot within 2 weeks.
4. At least 4 of 5 reviewers will find the product_management index useful within 5 minutes of opening the repo.

### Recommended experiments

| # | Experiment | Tests | Method | Effort | Timeline |
|---|---|---|---|---|---|
| 1 | Paper trace test | H1 | Print 5 trace sentences, ask planners to explain the decision | S | Week 1 |
| 2 | Rule cost card sort | H2 | Show 6 rules with fake euro costs, ask which they would change | S | Week 2 |
| 3 | Concierge run | H2 | Run the solver by hand on a planner's anonymized example and present the result in a call | M | Week 3 |
| 4 | Video plus landing page | H3 | Publish after week 8; track conversion | M | Week 8 to 9 |
| 5 | Repo 5 minute review | H4 | Think aloud sessions with 5 peers | S | Week 7 |

Ranked by learning per effort: 1, 2, 5, 3, 4.

### Experiment details
* **Paper trace test**: success is 3 of 5 correct explanations. A failure means the wording, not the engine, needs work. Cheapest signal in the plan.
* **Rule cost card sort**: the cost values are invented and labelled illustrative. Learn which rules planners treat as negotiable.
* **Concierge run**: only on data the participant is free to share. Never accept employer confidential data (clean room rule).
* **Video plus landing page**: wait until the video exists. Under 3% conversion points to message or segment, not product.

## Next steps
Triage the known request list next (`/triage-requests`), then set up metrics (`/setup-metrics`).
