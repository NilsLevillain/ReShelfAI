# Business Model: Reshelf

**Date**: 2026-10-24
**Framework**: Startup Canvas (recommended for new products: it keeps strategy and business model apart). Strategy detail lives in `1_strategy.md`; this document focuses on how Reshelf would make money and what it would cost.
**Evidence level**: Hypotheses. All figures are illustrative defaults, not market data and not claims of real impact.

---

## Part 1: Strategy summary

| Vision | Market segments | Relative costs |
|---|---|---|
| Every sellable unit finds a second shelf, and every decision can be defended | Supply planners at consumer goods makers with dated stock, beauty and personal care first | Not the cheapest option; competes on trust and brand safety, not on price |

| Value proposition | Trade-offs | Key metrics |
|---|---|---|
| Before: manual, inconsistent allocation. How: rule driven optimizer with a euro cost per rule. After: defensible decisions in minutes. Alternatives: Excel, planning suites, write off | Explainable over fastest; human in the loop over autopilot; allocation only, no marketplace | North Star: exported net recovery rate. One metric that matters now: explained decisions in the walkthrough test |

| Growth | Capabilities | Can't / won't (why others cannot copy) |
|---|---|---|
| Demo led, then design partner pilots, then sales assisted | Build the model and explainability; buy hosting and solver; partner for connectors and channels | Cannot copy quickly: customers' encoded rules and decision history. Can copy easily: the solver (so we do not rely on it) |

## Part 2: Business model

### Revenue streams (H)

| Stream | Model | Timing | Notes |
|---|---|---|---|
| Free reference pilot | No fee, 8 to 12 weeks, one plant, in exchange for feedback and a named or anonymized reference | First step (decided) | Buys evidence and a case study, not revenue |
| Paid pilot | Fixed fee, 8 to 12 weeks, one plant | After the reference pilot (decided) | Credited against year one if the customer converts |
| Annual subscription | Tiered by active SKUs and plants | After a successful pilot | Detail in `5_pricing.md` |
| Implementation and mapping | Day rate or fixed fee | With the pilot | Mapping the customer's ERP tables to the canonical schema |
| Outcome linked component | Share of verified uplift | Later, optional | Attractive but hard to audit; test only with a trusting design partner |

### Cost structure (H)

| Type | Item | How it scales |
|---|---|---|
| Fixed | Founder time, design and legal | Flat until the first hire |
| Fixed | Hosting baseline, domain, monitoring | Low and flat |
| Variable | Cloud compute for solves | Grows with SKUs and scenarios per customer |
| Variable | Support and onboarding per customer | Grows with number of customers and data readiness |
| Variable | Security and compliance (SSO, audit, hosting region) | Step cost per enterprise requirement |

The model is cheap to run and expensive to sell: the main cost is time to reach and convince a buyer.

### Unit economics sketch (illustrative, not data)

* Contract value per customer per year = subscription + mapping fees.
* Margin driver: solve time. A 10,000 SKU run must stay cheap, so the benchmark in the war plan doubles as a cost model.
* Payback driver: sales cycle length, not product cost. Design partners shorten it.

### Key partners

* Data warehouse and ERP ecosystems, for connectors (BigQuery first).
* Second life channel operators (outlets, clearance, NGO, recyclers) for the channel master and rule templates.
* Implementation partners or consultancies, as a possible channel and a possible competitor.

### Channels

* Demo, video and written strategy (hiring managers and practitioners).
* Founder led outreach in supply chain communities.
* Design partner introductions.

## Open decisions

| Decision | Options | Recommendation |
|---|---|---|
| Repo license | Permissive (MIT) / source available (BSL) / all rights reserved | **Decided: all rights reserved.** The code is visible for evaluation but not reusable, which protects the commercial path. Record it as an ADR and add a `LICENSE` file before the first public push. Consequence: contributions and forks are not allowed, so say so in the README |
| First revenue model | Paid pilot / free pilot for a reference / none | **Decided: free pilot for a reference, then paid pilots.** The reference pilot lowers the barrier for the first customer; paid pilots then test willingness to pay (A3) |
| Who is the buyer | Supply chain / sustainability / finance | Test in interviews; start by selling to the planning lead |

## Strategy coherence check

| Check | Result |
|---|---|
| Does pricing follow the value delivered? | Yes: tiers follow SKUs and plants, which track the size of the allocation problem |
| Do trade-offs fit the model? | Yes: no marketplace means no liquidity risk and no commission model |
| Does the growth plan match the sales cycle? | Partly: enterprise cycles are long; the paid pilot is the shortcut |
| Is there a weak link? | Defensibility: the moat only exists after several customers |

## Riskiest assumptions

| # | Assumption | Cheapest test |
|---|---|---|
| 1 | A buyer will pay for allocation decision support | Ask for a paid pilot in interviews (E2) |
| 2 | One plant is a big enough pilot to prove value | Check in interviews who owns the allocation decision and at which level |
| 3 | Customers can supply clean lots, channels and demand | Data readiness checklist in the first call |
| 4 | Design partners will share data under a clean agreement | Ask early; if blocked, the concierge run uses their anonymized example |

## Next steps

1. Value proposition per segment (`3_value_proposition.md`).
2. Market scan to test the environment (`4_market_scan.md`).
3. Pricing hypotheses to test (`5_pricing.md`).
