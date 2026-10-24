# Discovery Plan: Reshelf

**Date**: 2026-10-24
**Product stage**: New (no validated demand yet, synthetic demo data only)
**Discovery question**: Is there a reachable, painful and payable need for explainable, rule driven allocation of stock that would otherwise be destroyed? Does "tighten a rule, see what it costs, see why" set Reshelf apart?
**Second question (portfolio)**: Does this repo convince a hiring manager in 5 minutes that its author can build products and manage them?
**Decisions this informs**: what the MVP hero flow is, which segment the GTM targets first, what the README and video lead with.

> Clean room note: nothing here uses real employer data, targets or names. Every figure below is a hypothesis or a success threshold, not a claim of impact.

---

## 1. Ideas explored (10)

| # | Idea | Perspective | Rationale |
|---|---|---|---|
| 1 | Scenario compare with euro deltas | PM | Planners value comparison; makes trade offs visible |
| 2 | "Why this allocation" panel with counterfactual cost per rule | PM + Eng | Trust and traceability; turns a black box into a negotiation tool |
| 3 | Brand protection as a first class objective (brand risk index) | PM | Real tension between supply chain and brand teams |
| 4 | Optimizer vs greedy baseline on every run | Eng | Proves value in the first minute, with a fair comparison |
| 5 | Excel round trip (import inputs, export order creation file) | Designer | Users live in Excel; no export means no adoption |
| 6 | Manual override with live rule validation | Designer | Expert judgment must beat the algorithm when needed |
| 7 | Expiry early warning: value at risk timeline | PM | Moves upstream, before stock becomes "bad" |
| 8 | Impact and ESG report (units saved, donation records) | PM | Gives the sustainability budget owner a reason to buy |
| 9 | ERP mapping wizard and connector library | Eng | Portability is the path from demo to product |
| 10 | Two sided marketplace where liquidators and NGOs bid on lots | PM | Large upside, but needs liquidity on both sides |

## 2. Selected for validation (5)

| Idea | Why carried forward |
|---|---|
| 1 + 2 Compare and Why panel | This is the hero. Everything else supports it |
| 4 Greedy baseline | Cheap, and it carries the proof of value |
| 5 Excel round trip | Adoption gate for the target user |
| 3 Brand protection | Likely the sharpest differentiator against generic optimizers |
| 7 Early warning | Candidate for the roadmap; tests whether the problem starts earlier |

Parked: 6 (already planned, second wave), 8 (needs a buyer first), 9 (after first pilot), 10 (two sided risk, too early).

## 3. Critical assumptions

Impact and uncertainty are rated H, M or L. Leap of faith = H impact and H uncertainty.

| # | Assumption | Category | Impact | Uncertainty | Priority |
|---|---|---|---|---|---|
| A1 | Planners allocate this stock manually or in spreadsheets, and the pain is strong enough to change tools | Value | H | H | **1 (leap of faith)** |
| A2 | Knowing what a rule costs in euros is a top 3 trust driver for planners | Value | H | M | **2** |
| A3 | A budget owner exists (supply chain, finance or sustainability) and would pay | Viability | H | H | **1 (leap of faith)** |
| A4 | Mid size consumer goods firms with dated stock can be reached through professional channels | Go to market | H | H | **1 (leap of faith)** |
| A5 | Hiring managers read the product_management folder and the demo within 5 minutes | Portfolio | H | M | **2** |
| A6 | Brand versus recovery trade off is a real recurring conflict between teams | Value | M | H | 3 |
| A7 | Planners accept optimizer output only if they can override it | Usability | M | M | 4 |
| A8 | Non OR users can read a rule trace and a counterfactual | Usability | H | M | **2** |
| A9 | HiGHS solves 2,000 SKUs in seconds; counterfactual re solve stays under 10 s | Feasibility | H | L | 5 (test in week 3) |
| A10 | A company can map its ERP data to the canonical schema with small effort | Feasibility | M | M | 4 |
| A11 | Existing planning suites and liquidation platforms do not offer rule level cost explanation | Value | H | M | **2 (verify by desk research)** |

Grouped tests: A1, A3, A6 go into the same interviews. A2, A7, A8 go into the same walkthrough.

## 4. Validation experiments

| # | Tests | Method | Success criteria | Effort | Timeline |
|---|---|---|---|---|---|
| E1 | A11 | Desk research: 10 tools across planning suites, returns and liquidation platforms, spreadsheet baseline | Feature matrix done; each competitor claim has a public source | S | Week 0 to 1 |
| E2 | A1, A3, A6 | 8 problem interviews with supply planners and ops leads (use `/interview`) | 5 of 8 describe a manual or Excel process; 4 of 8 name an owner for the budget; 3 of 8 describe a brand versus recovery conflict unprompted | M | Week 1 to 2 |
| E3 | A2, A7, A8 | Clickable walkthrough of the precomputed demo with 5 planners, Why panel on and off | 4 of 5 explain in their own words why a line was allocated; 3 of 5 ask to try their own data | M | Week 5 to 6 |
| E4 | A4 | XYZ pretotype: landing page with the 75 s video, shared in 3 practitioner communities | At least 10% of 200 visitors leave a contact for a pilot | M | Week 8 to 9 |
| E5 | A5 | 5 peer reviews of the repo (PMs, tech leads), 5 minutes each, think aloud | 4 of 5 state problem, user and differentiator correctly; 4 of 5 would take the call | S | Week 7 |
| E6 | A9 | Automated benchmark in CI (already in the war plan) | 2,000 SKUs under 10 s, gap reported | S | Week 3 |

### Experiment details

**E2 Problem interviews**
* Hypothesis: we believe planners handle second life allocation manually. We will know it is true when 5 of 8 describe a spreadsheet or manual process unprompted.
* Setup: 30 minute calls, past behavior questions only ("tell me about the last time you decided where to send near expiry stock"). No pitch.
* Measure: coded notes per interview; count of pain, workaround and owner mentions.
* Rule: never ask for or accept confidential data from any employer.
* Decision: below 3 of 8 means the problem is not painful or not mine to reach; pivot the segment (see section 6).

**E3 Walkthrough**
* Setup: same scenario, two variants. Variant A shows results and compare. Variant B adds the Why panel.
* Measure: can the person explain a line unaided; do they volunteer a rule change; do they ask about their own data.
* Decision: if variant B does not beat A, the Why panel is not the hero and the video story changes.

**E4 Landing page pretotype**
* XYZ hypothesis: at least 10% of 200 supply chain practitioners who see the page will leave an email for a pilot.
* Below 3% means positioning or segment is wrong, not the product.

**E5 Hiring manager read**
* Treat the repo as a product with its own user. Test the first screen of the README and the product_management index.

## 5. Timeline (parallel to the 8 week build)

| Window | Discovery work |
|---|---|
| Week 0 to 1 | E1 desk research; recruit interviewees; write interview script |
| Week 1 to 2 | E2 interviews; update assumptions A1, A3, A6 |
| Week 3 | E6 benchmark; checkpoint: go or pivot on segment |
| Week 5 to 6 | E3 walkthrough with precomputed demo |
| Week 7 | E5 repo peer review |
| Week 8 to 9 | E4 landing page after the video exists; final decision |

## 6. Decision framework

| If | Then |
|---|---|
| E2 passes | Keep supply planner as the first persona; GTM targets mid size consumer goods |
| E2 fails on pain | Test the nearest segment: returns and reverse logistics teams, or sustainability leads |
| E2 fails on budget owner | Position as a planner productivity tool first, sell to the sustainability budget later |
| E3 variant B beats A | Keep the Why panel as the hero; the video centers on it |
| E3 shows no difference | Promote scenario compare to the hero; the Why panel becomes a supporting feature |
| E4 above 10% | Draft a pilot offer and pricing hypothesis |
| E4 below 3% | Rework the message with the value proposition and positioning skills before changing the product |
| E5 fails | Rewrite the README top and the product_management index before adding features |

## 7. Next steps

1. Brainstorm second wave ideas and experiments (`/brainstorm`).
2. Triage the known request list (`/triage-requests`).
3. Define the metrics and the North Star (`/setup-metrics`).
4. Then move to strategy, GTM and differentiators.
