# Strategic Market Scan: Second Life Allocation of Surplus Stock

**Date**: 2026-10-24
**Purpose**: Test the product strategy against the environment before GTM work.
**Scope**: Software that decides where surplus or near expiry consumer goods should go. Beachhead hypothesis: beauty and personal care, Europe first.

## Evidence status (read first)

Web search was blocked in this session, and many vendor pages are not public. So this scan mixes three kinds of statements. Each is tagged.

| Tag | Meaning |
|---|---|
| **[V]** | Verified on a public page during this session |
| **[K]** | Background knowledge, not re checked. Verify before using in a public document |
| **[H]** | Hypothesis or judgment |

Verified so far: Optoro sells a returns management system for retailers, brands and 3PLs, and publishes no pricing **[V]**. Good360 routes donated goods to nonprofits for corporate partners and states no fees on its homepage **[V]**.

---

## Executive summary

The need is real in principle: stock that misses primary retail has to go somewhere, and several rules (shelf life, brand tier, capacity) constrain where. **[H]** Three categories of tools sit around it: planning suites, returns and liquidation platforms, and donation intermediaries. None of the ones checked is positioned on "explain what each allocation rule costs" **[H, to verify]**. The main threats are not other startups but Excel being good enough and planning suites adding a module. Regulation on destruction of unsold goods is a tailwind in some markets **[K]**. The best risk adjusted move is narrow: win planners in beauty and personal care with explainability and brand risk, in Europe, before widening.

## SWOT

| Strengths                                                             | Weaknesses                               |
| --------------------------------------------------------------------- | ---------------------------------------- |
| Hero flow is specific: rule cost in euros plus a reason for each line | No users, no customer data, no real data |
| Brand tier as a first class constraint                                | Solo builder, part time, 8 week budget   |
| Portable, tested model with a fair greedy baseline                    | The solver itself is easy to copy        |
| Cheap to run: open source solver, static demo                         | No distribution or brand yet             |

| Opportunities | Threats |
|---|---|
| Rules on unsold goods in some markets **[K]** | Excel is free and familiar |
| Companies need audit trails for sustainability reporting **[H]** | Planning suites add an allocation module **[H]** |
| Cloud warehouses make data access easier **[H]** | Long enterprise sales cycles |
| Few tools focus on explanation of rule cost **[H]** | Data readiness blocks pilots |

**Actions**
* Leverage S+O: lead with brand risk and traceability in the beauty segment.
* Mitigate W+T: get one design partner early; keep the model portable so a pilot needs only a mapping, not a rewrite.

## PESTLE

| Factor | Current state | Impact | Trend | Timeframe |
|---|---|---|---|---|
| Political / Legal | France bans destruction of unsold non food consumer goods and requires donation or reuse, in force since 2022 **[K]**. EU Ecodesign Regulation (ESPR) adds disclosure of destroyed unsold goods and powers to ban destruction by product group **[K]** | High for the beachhead | Tightening | 2026 onward |
| Economic | Write offs hit margin; pressure on working capital and inventory levels **[H]** | Medium | Stable | Ongoing |
| Social | Customers and employees expect less waste; luxury brands fear discount image **[H]** | Medium | Growing | Ongoing |
| Technological | Open source solvers (HiGHS) lower build cost; cloud warehouses ease integration; AI assistants may commoditize basic optimization **[H]** | High (double edged) | Fast | 1 to 3 years |
| Legal (data) | Customers will not share confidential data without agreements; clean room needed for the demo | Medium | Stable | Ongoing |
| Environmental | Destruction of sellable goods carries emissions and waste cost **[H]** | Medium | Growing | Ongoing |

Action: verify the French and EU provisions against primary sources (law text, EU Official Journal) before quoting them. Check whether cosmetics are in scope of a future EU ban by delegated act.

## Porter's Five Forces

| Force | Intensity | Key drivers | Implication |
|---|---|---|---|
| Competitive rivalry | Medium | Fragmented: planning suites, returns platforms, donation intermediaries, consultancies. Few are focused on this exact decision **[H]** | Pick a narrow niche; stay out of head to head with suites |
| Supplier power | Low | Open source solvers, commodity cloud | Healthy margin potential |
| Buyer power | High | Enterprise buyers, long cycles, in house alternatives | Need a paid pilot and proof of value to hold price |
| Threat of substitutes | High | Excel, write off, in house OR team, off the shelf solver with an analyst | Win on explainability and speed to change a rule |
| Threat of new entrants | Medium to high | Low cost to build an optimizer; trust and data access are the real barriers | Moat has to come from rule library and decision history |

**Industry attractiveness**: Medium. Low supplier power and regulatory tailwind, offset by strong substitutes and enterprise buyers.

### Competitor map (to verify in the competitive analysis)

| Category | Examples | Status |
|---|---|---|
| Returns and resale platforms | Optoro | Checked **[V]**: returns focus, no public pricing |
| Liquidation marketplaces | B-Stock, Liquidity Services | **[K]**, page not reachable in this session |
| Donation intermediaries | Good360 | Checked **[V]**: no fees stated |
| Planning suites | SAP IBP, Kinaxis, o9, Blue Yonder | **[K]**, to verify scope and pricing |
| Spreadsheet and in house solvers | Excel, Gurobi or similar with analysts | **[H]** |

## Ansoff growth matrix

| Strategy | Opportunity | Risk | Investment | Priority |
|---|---|---|---|---|
| Market penetration | Beauty and personal care planners in Europe, via design partners | Low to medium | Low (time) | **High** |
| Market development | Other dated goods (household, supplements, pet); North America and Asia | Medium | Medium | Medium, after first pilot |
| Product development | Expiry early warning, multi period, manual override, brand protection objective | Medium | Medium | **High** for override and early warning |
| Diversification | Marketplace for channels, returns processing | High | High | Low, avoid before liquidity is proven |

## Cross framework synthesis

* **Converging signals**: explainability and brand safety (SWOT strength, Porter substitute defense, PESTLE regulation) are the differentiating bet.
* **Strategic imperatives**: (1) get one real conversation in the beachhead; (2) prove the explanation advantage with the competitive analysis; (3) keep the product portable.
* **Key risks**: Excel is good enough; planning suites close the gap; data readiness.
* **Best opportunities**: penetration of beauty and personal care in Europe; override and early warning as the next features.

## Strategic recommendations

1. **Stay narrow**: beauty and personal care in Europe, planners first. Evidence: Porter (substitutes high), Ansoff (penetration lowest risk).
2. **Verify the regulatory tailwind** against primary sources before it goes in the README or a pitch. Evidence: PESTLE.
3. **Do the competitive analysis next**, checking suites and marketplaces on their own public documentation. Evidence: the differentiation claim is still a hypothesis.
4. **Treat the paid pilot as the validation device**, not a revenue plan. Evidence: buyer power high.

## Monitoring plan

| Signal | What to watch | Source | Frequency |
|---|---|---|---|
| Regulation | EU ESPR delegated acts; French rules on unsold goods | EU Official Journal, French legal portal | Quarterly |
| Competitor moves | New allocation or surplus modules in planning suites | Vendor release notes | Quarterly |
| Buyer signal | Pain and budget owner in interviews | E2 notes | After each interview |
| AI commoditization | Tools that offer solver plus explanation out of the box | Product directories, communities | Quarterly |

## Next steps

1. Competitive analysis and differentiators (`/pm-market-research:competitive-analysis`).
2. Market sizing with sourced data.
3. Pricing hypotheses (`5_pricing.md`).
