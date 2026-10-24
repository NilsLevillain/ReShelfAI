# Stakeholder Map: Reshelf

**Date**: 2026-10-24
**Phase**: Planning, pre code
**Evidence level**: Hypotheses (H). No interview has run. Power, interest and stance are guesses to update after E2 and E9 (`../1_discovery/1_discovery_plan.md`). Nobody named here is a real person. Roles are generic.

> Two layers, as in `1_strategy.md`. **The product layer** maps the people a commercial Reshelf would have to win. **The project layer** maps the people who judge the repo and the demo. They want different messages, so they are kept apart.

## Stakeholder grid

Power is the ability to approve, block or fund. Interest is how much the person is affected by the result.

### Product layer (H)

| Stakeholder | Role in an allocation decision | Power | Interest | Quadrant | Stance (H) |
|---|---|---|---|---|---|
| Supply planner | Builds and runs the allocation. Primary user | Medium | High | Manage closely | Supportive if the result is defensible, resistant if it adds work |
| Planning lead | Owns the process, signs the plan, likely champion in a pilot | High | High | Manage closely | Neutral, wants fewer escalations |
| Brand manager | Protects tier and image, can veto a channel | High | High | Manage closely | Resistant to anything that sends premium stock to clearance, supportive when the cost is visible |
| Finance partner | Owns write offs, can veto or fund | High | Medium | Keep satisfied | Neutral, cares about euros |
| Budget owner (supply chain, finance or sustainability, unknown) | Pays for a pilot (assumption A3) | High | Low to medium | Keep satisfied | Unknown |
| IT and data owner | Provides the ERP extract, gate for any pilot with real data | High | Low | Keep satisfied | Neutral to resistant (security, effort) |
| Legal, compliance and procurement | Data agreement, pilot contract | High | Low | Keep satisfied | Neutral, can slow everything |
| Sustainability lead | Needs proof of avoided destruction | Medium | High | Keep informed | Supportive |
| S&OP and demand planners | Supply stock and forecast inputs, often late (A15) | Low | Medium | Keep informed | Neutral, wary of more input checks |
| Reverse logistics and returns teams | Possible later segment | Low | Medium | Keep informed | Unknown |
| Channel partners (liquidators, NGOs, outlet operators) | Receive the stock, not users in v1 | Low | Low | Monitor | Neutral |
| Planning suite and returns platform vendors | Possible competitors (A11) | Low | Low | Monitor | Unknown, could add this as a module |
| Regulators and policy makers | Rules on destroying unsold goods (verify, see `4_market_scan.md`) | High | Low | Monitor (high power, indirect) | Not engaged |

### Project layer (H)

| Stakeholder | Role | Power | Interest | Quadrant | Stance (H) |
|---|---|---|---|---|---|
| Nils | Owner, sole builder | High | High | Manage closely (self) | Committed |
| Hiring managers and recruiters | Judge the repo and the folder in 5 minutes (A5) | High | Medium | Keep satisfied | Neutral until convinced |
| Peer PMs and tech leads | Reviewers in E5, source of referrals | Medium | Medium | Keep informed | Supportive when asked |
| Problem interviewees (E2) | Give evidence, possible pilot contacts | Medium | Medium | Keep informed | Unknown |
| Practitioner communities | Audience for the E4 pretotype | Low | Medium | Keep informed | Unknown |
| Walkthrough participants (E3, E7) | Test the Why panel and the AI wizard of Oz | Low | Medium | Keep informed | Unknown |
| Open source maintainers and hosting providers | Tools the build depends on (HiGHS, PuLP, free tiers) | Low | Low | Monitor | Neutral |

### Grid view

```
                         HIGH INTEREST
                              |
  KEEP SATISFIED              |        MANAGE CLOSELY
  finance, budget owner,      |        planner, planning lead,
  IT, legal, hiring           |        brand manager, Nils
  managers                    |
------------------------------+----------------------------------
                              |
  MONITOR                     |        KEEP INFORMED
  channel partners, vendors,  |        sustainability, S&OP,
  regulators, tool providers  |        reverse logistics, peers,
                              |        interviewees, communities
                         LOW INTEREST
```

Regulators have high power over the market but no direct power over a pilot decision, so they sit in monitor. Revisit if the market scan confirms a binding rule.

## Communication plan

### Manage closely (high power, high interest)

| Stakeholder | Channel | Frequency | Content | Owner |
|---|---|---|---|---|
| Supply planner | Interview (E2), then walkthrough (E3) | Once each, then per pilot cycle | Past behavior questions first, then the Why panel with and without text | Nils |
| Planning lead | Interview, then pilot kickoff meeting | Once, then every two weeks in a pilot | Process and approval questions (E9), scenario results in euros | Nils |
| Brand manager | Walkthrough of the luxury protection scenario | Once before the hero is locked, then per pilot cycle | The euro cost of a protective rule, brand risk index | Nils |

### Keep satisfied (high power, low interest)

| Stakeholder | Channel | Frequency | Content | Owner |
|---|---|---|---|---|
| Finance partner | One page summary | Before a pilot, then per cycle | Value recovered and destroyed units against the baseline, labeled simulated | Nils |
| Budget owner | Pilot offer (see `5_pricing.md`) | Once, after E4 or E2 signals | Fixed fee pilot scope, outcome and exit criteria | Nils |
| IT and data owner | Short data request with the canonical schema | Once per pilot | Which tables and fields are needed, standard SAP names, no write access | Nils |
| Legal, compliance and procurement | Standard data agreement | Once per pilot | Clean data handling, no confidential data in the demo repo | Nils |
| Hiring managers and recruiters | README top, video, folder index | At launch, then on request | Problem, user, differentiator, limitations | Nils |

### Keep informed (low power, high interest)

| Stakeholder | Channel | Frequency | Content | Owner |
|---|---|---|---|---|
| Sustainability lead | Short note | Once per pilot cycle | Units diverted per scenario, traceable destination per line | Nils |
| S&OP and demand planners | Short question set inside E2 | Once | Who supplies what, how late (E9) | Nils |
| Peer reviewers (E5) | Review request, then thanks and changes made | Once, week 7 | README first screen and folder index | Nils |
| Interviewees (E2) | Thank you note and a summary of what was learned | Once after the round | Findings, no confidential data | Nils |
| Practitioner communities (E4) | Landing page and video | Once at launch | The 75 second story and a pilot contact form | Nils |

### Monitor

Channel partners, vendors, regulators and tool providers get no direct communication. Include them in the market scan refresh and note changes in `4_market_scan.md`.

## Potential conflicts

| Conflict | Between | Mitigation |
|---|---|---|
| Recovery value against brand protection | Finance and planner against brand manager | This is the product's central trade off. Show the euro cost in compare, never decide for them |
| Trust in the optimizer against ownership of the decision | Planner against the tool | Rule trace, counterfactual, and override later (FR-22), with an override saved as its own scenario |
| Pilot timeline against data access | Pilot sponsor against IT and legal | Start with one plant, the canonical schema, and a data request that needs read access only |
| Sustainability reporting against the "no real impact claim" rule | Sustainability lead against the clean room rule | Report simulated units in the demo only. Real figures wait for a pilot with a signed agreement |
| Late inputs from other teams | Planner against S&OP and demand planners | Test in E9. An input check feature (R20) waits for evidence |
| Two audiences, two messages | Hiring managers against pilot customers | Keep the README for the project layer and a separate pilot page for the product layer |
| Interview candor against confidentiality | Interviewees against the clean room rule | Never ask for or accept confidential data. Past behavior questions only |

## Escalation path

Solo project, so decisions escalate to rules, not people.

| Blocked decision | Resolved by |
|---|---|
| Which segment to target | Decision table in the discovery plan, section 6, after E2 |
| What the hero is | E3 result, same table |
| Whether to build an AI feature | E7 and E8 results |
| Scope against time | Cut order in `docs/war_plan.md` section 7 and the week 3 gate in `../3_execution/1_backlog.md` |
| In a pilot: a block between planning lead and brand or finance | Planning lead takes it to the budget owner, with the euro cost from compare |

## RACI (decision areas, product layer, H)

R is responsible, A accountable, C consulted, I informed. Roles are those of a pilot customer. In the demo, Nils holds every role.

| Decision area | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| Rule defaults and brand tier restrictions | Planner | Brand manager | Planning lead, finance | Sustainability |
| Scenario approval before export | Planner | Planning lead | Brand manager, finance | Sustainability, S&OP |
| Data extract for a pilot | IT and data owner | Planning lead | Legal, planner | Finance |
| Pilot scope and fee | Nils | Budget owner | Planning lead, finance, legal | Brand manager |
| Impact figures used in reports | Sustainability lead | Finance partner | Planner | Planning lead |
| Public claims about results | Nils | Nils | Peer reviewers | Hiring managers |

## Update triggers

* After E2: re rate power, interest and stance of planner, planning lead, brand, finance and budget owner. Replace guesses with what interviewees said.
* After E9: confirm or remove S&OP, demand planners and IT as stakeholders in the process.
* After E4: add or remove the practitioner community group.
* Before a pilot: name real roles, and move the RACI from a hypothesis to an agreement.

## Next steps

1. Add stakeholder questions to the E2 script: who challenged the last decision, who approved it, who paid for the tool they use.
2. Update the grid after E2.
3. Use the manage closely and keep satisfied rows to shape the GTM plan.
