# Product Strategy: Reshelf

**Date**: 2026-10-24
**Stage**: MVP in planning (no code yet, no validated demand, synthetic data only)
**Author**: Nils
**Evidence level**: Hypotheses. Anything marked (H) is untested. Discovery experiments are in `../1_discovery/1_discovery_plan.md`.

> Two layers, kept apart on purpose. **The product** is what Reshelf would be if sold. **The project** is the portfolio goal: a public repo and demo that prove product thinking. Sections 1 to 9 are about the product. The last section states how the project serves it.

---

## 1. Vision

Every sellable unit finds a second shelf, and every allocation decision can be defended.

Today, stock that misses primary retail is destroyed or discounted by habit, because nobody can show which rule forces which outcome. Reshelf makes the cost of every rule visible in euros, so planners, brand teams and finance can agree on the trade off in minutes instead of arguing in spreadsheets.

## 2. Target segments

| Segment | Pain level | Current alternative | Priority |
|---|---|---|---|
| Supply planners at consumer goods makers with dated stock (beauty and personal care first) (H) | High: manual choice, many rules, brand risk | Excel, ad hoc rules, write off | **Primary** |
| Sustainability and ESG leads | Medium: need proof that destruction is falling | Manual reporting | Secondary (influencer, possible budget owner) |
| Finance and brand managers | Medium: they own write offs and brand image | Email approvals | Secondary (veto power) |
| Reverse logistics and returns teams | Medium | Returns platforms | Later (Ansoff market development) |

**Primary segment, and why beauty first (H)**: shelf life is long (months, not days), so allocation is a planning decision, not a race. Brand tiers (luxury, premium, mass) are a hard constraint that generic optimizers ignore. Regulation on destroying unsold goods is moving in some markets (see `4_market_scan.md`, verify before use).

**Explicitly not serving**
* Fresh food and very short shelf life goods: different clock, different logistics.
* Returns processing and warehouse resale: served by returns platforms.
* Marketplaces and auctions: Reshelf decides where stock should go, it does not run the sale.
* Real time pricing and markdown engines.

Segment sizes are not stated because no sizing has been done. Next step is market sizing with sourced data.

## 3. Pain points and value created

| Segment | Problem | Current cost (H) | Value delivered |
|---|---|---|---|
| Supply planner | Allocation across many lots, channels and rules is slow and inconsistent | Hours per cycle; value lost to wrong channel; units destroyed | Optimal allocation under all rules, in minutes, with a baseline comparison |
| Brand and finance | Cannot see what a protective rule costs | Endless back and forth; decisions made by habit | Euro cost of each rule, scenario compare |
| Sustainability lead | No traceable proof of avoided destruction | Manual, unaudited figures | Traceable units diverted per scenario |

Costs are placeholders to be measured in interviews. No real figure is claimed.

**Process value (added 2026-10-24, H)**: in large companies the real cost is not only the allocation itself. Planners can spend days reallocating stock about to expire, and the inputs come from other teams: stock from S&OP, sales forecasts from demand planners, which are often late or inconsistent. Reshelf therefore also serves as a defined process: one place where inputs, rules, decisions and approvals are recorded. The value is fewer FTE days per cycle, an audit trail for every decision, and better collaboration across planning, brand, finance and sustainability. This must be tested in interviews: who supplies each input, how late it arrives, and how many people touch one allocation.

## 4. Value propositions

* **Supply planner**: When I have lots approaching expiry and many rules to respect, I want a defensible allocation I can adjust, so I can decide in minutes and explain it to anyone.
* **Brand and finance**: When a rule blocks a channel, I want to see its price in euros, so I can choose to keep it or relax it on facts.
* **Sustainability lead**: When I report on waste, I want each unit's destination traced, so I can show what was diverted and why.

Detail in `3_value_proposition.md`.

## 5. Strategic trade-offs

| We choose | Over | Because |
|---|---|---|
| Explainable decisions | Fastest possible solve | Trust is what planners buy; a black box gets overridden |
| Tables first, globe as a filter | A chart heavy dashboard | Users work in Excel; the globe is the hook, not the workflow |
| Decision support with a human in the loop | Full autopilot | Experts hold knowledge the model lacks (H) |
| The solver decides, AI drafts, explains and checks | An AI that chooses allocations | Hard rules must always hold and every decision must be explainable; an LLM can guarantee neither |
| AI behind guardrails (validated diff, human approval, step log, faithfulness checks) | AI as a headline feature | AI must earn its place through tests (E7, E8); otherwise it reads as hype and weakens trust |
| Rule trace plus counterfactual re solve | MILP dual values | Exact, readable, in euros; duals are local and degenerate |
| One planning period in the MVP | Multi period model | Keeps the model small and the demo sharp |
| Portable canonical schema with standard ERP names | Deep integration with one ERP | Portability is the path to a first pilot |
| Brand risk as a visible trade off | Pure value maximization | Recovery bought with brand damage is not a win |
| Allocation decision only | Running the sale or marketplace | Avoids two sided liquidity risk and a different business |

## 6. Key metrics

Full tree in `../1_discovery/4_metrics_dashboard.md`.

* **North Star**: exported net recovery rate (net recovered value / value at risk, for exported scenarios).
* **Inputs**: allocation coverage, optimizer uplift vs greedy, explained decisions, scenarios compared per cycle, time to first export.
* **Guardrails**: solve time p95, solver status, counterfactual time, brand risk index, override rate.

## 7. Growth engine (H)

Phase 1, demo led (now to week 9): the demo, the 75 s video and the written strategy attract practitioners and hiring managers. Goal: conversations, not signups.

Phase 2, design partner pilots: one or two pilots with planners in the beachhead segment, using their own data after a clean agreement. Entry offer: a fixed fee pilot (see `5_pricing.md`).

Phase 3, sales assisted: enterprise buying cycles are long. A shareable scenario link is the expansion loop: a planner shares an explained scenario with brand, finance and sustainability, who then ask for access.

```
Planner runs scenario -> shares explained result -> brand/finance see the euro cost
-> they request seats or ask for another scenario -> more scenarios -> richer rule library
```

This loop is a hypothesis. It needs a first customer to test.

## 8. Core capabilities

| Capability | Build / Buy / Partner | Investment | Timeline |
|---|---|---|---|
| MILP model, greedy baseline, constraint tests | Build | High | Weeks 2 to 3 |
| Explainability (rule trace, counterfactual) | Build | High | Week 3, UI week 6 |
| Canonical schema and ERP adapters | Build | Medium | Weeks 1 to 2 |
| Synthetic data generator | Build | Medium | Week 1 |
| Web UI (tables, compare, Why panel, globe) | Build | High | Weeks 4 to 6 |
| Solver engine (HiGHS, CBC) | Buy (open source) | Low | Week 2 |
| Hosting (static plus Cloud Run) | Buy | Low | Week 7 |
| Data warehouse connectors | Partner or build after a pilot | Medium | After pilot |
| Channel network (liquidators, NGOs) | Partner | Medium | After pilot |

## 9. Defensibility

Honest answer: today there is none. An optimizer can be rebuilt by a consultancy or by a planning suite vendor.

What could become a moat (H):
* **Switching costs**: a customer's encoded rules, channels and decision history live in Reshelf.
* **Rule library**: with several customers, anonymized rule templates per category and region become a starting point no newcomer has.
* **Trust through explainability**: a trace that finance and brand teams accept is slow to replicate in culture and in design.

What is not a moat: the solver, the globe, the UI.

## Strategic risks

1. **The problem is too small or too well solved by Excel** (H). Test: E2 interviews, success when 5 of 8 describe a manual process.
2. **Planning suites or consultancies add this as a module.** Mitigation: stay narrow and fast on explainability and brand risk, and keep the repo and docs as proof of depth.
3. **Data readiness**: lots, channel rules and demand per channel are hard to get clean. Mitigation: canonical schema, adapters, and a pilot scope that starts with one plant.

## The project layer

| Goal | How the product strategy serves it |
|---|---|
| Prove product thinking | Discovery, strategy and GTM are public documents, each with explicit hypotheses and kill criteria |
| Prove engineering quality | Tests per constraint, ADRs, benchmark, CI |
| Keep a commercial option open | Portable schema, clean room data, license decision before publishing (see `2_business_model.md`) |

## Next steps

1. Run E1 and E2 from the discovery plan to replace hypotheses with evidence.
2. Size the market with sourced data.
3. Go to GTM: beachhead segment, ideal customer profile, launch plan.
