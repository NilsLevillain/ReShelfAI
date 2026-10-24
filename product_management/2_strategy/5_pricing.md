# Pricing Strategy: Reshelf

**Date**: 2026-10-24
**Current pricing**: None. The demo is free and uses synthetic data.
**Trigger**: New product; deciding what to test with a first design partner.
**Evidence level**: Hypotheses only. No competitor price was found: enterprise vendors checked publish none (Optoro: no public pricing, Good360: no fees stated). All figures are illustrative placeholders to be replaced by interview data. None is a market fact.

---

## Recommended model: pilot, then tiered annual subscription

**Why**
* The buyer is an enterprise team with a long cycle; a paid pilot proves willingness to pay (assumption A3) faster than a free trial.
* The size of the problem grows with active SKUs and plants, so a tier on those two metrics tracks the value delivered and is easy to measure.
* Outcome based pricing (share of uplift) aligns incentives but needs an audit method the customer trusts. Keep it as a later option.

## Pricing structure (placeholders)

| Tier | Illustrative price | Includes | Target | Key limit |
|---|---|---|---|---|
| Demo | Free | Seeded synthetic scenarios, cached results | Evaluators, hiring managers, curious planners | Synthetic data only |
| Reference pilot | Free, 8 to 12 weeks | One plant, own data mapped, 3 scenarios, handover report | First design partner | One plant; in exchange for feedback and a reference (decided) |
| Paid pilot | Fixed fee, 8 to 12 weeks | Same scope | Following design partners | One plant, credited to year one if converted |
| Team | Monthly or annual | Up to about 2,000 active SKUs, 3 plants, 10 channels, 5 seats | One business unit | SKUs and plants |
| Business | Monthly or annual | Up to about 10,000 SKUs, more plants and channels, SSO, audit log | Several regions | SKUs, plants, seats |
| Enterprise | Custom | Custom connectors, hosting region, support terms | Group wide | Negotiated |

Numeric prices are deliberately left empty. To fill them, use the willingness to pay method below and the interview results; guessing now would give a false sense of precision.

## Model comparison

| Model | Fit | Pros | Cons |
|---|---|---|---|
| Flat rate | Low | Simple | Ignores very different customer sizes |
| Per seat | Low | Common | Value is not tied to the number of planners |
| Usage based (per solve) | Medium | Aligned with compute | Unpredictable bills discourage exploration of scenarios, which is the core behavior we want |
| **Tiered by SKUs and plants** | **High** | Tracks problem size; predictable | Needs clear tier limits |
| Freemium | Low | Reach | No network effect; free users bring no value to the product |
| Outcome based | Medium (later) | Strong alignment | Hard to attribute and audit uplift |

Avoid per solve pricing: it would tax the very behavior (comparing scenarios) that drives the North Star.

## Free and trial strategy

* The public demo is the free tier. It runs on synthetic data and cached results, so it costs almost nothing.
* The gated step is real data: that is where setup effort and support cost appear, so that is where payment starts (the pilot).
* Conversion trigger: after the pilot, the customer has a mapped dataset and a decision history in the tool.

## Competitive benchmark

| Competitor | Model | Price range | Positioning |
|---|---|---|---|
| Optoro | Enterprise software, contact sales **[V]** | Not published **[V]** | Returns management for retailers, brands, 3PLs |
| Good360 | Donation network **[V]** | No fees stated on homepage **[V]** | Corporate donation and ESG |
| Planning suites (SAP IBP, Kinaxis, o9, Blue Yonder) | Enterprise licensing **[K]** | Not found **[K]** | Broad planning |
| Liquidation marketplaces (B-Stock, Liquidity Services) | Marketplace fees **[K]** | Not found **[K]** | Selling surplus goods |
| Excel and in house solvers | Internal cost | Staff time | Free tools plus analysts |

Takeaway: there is no public price to anchor to. The real anchor is the cost of the current process (analyst time plus value lost), found in interviews.

## Willingness to pay

No data yet, so no estimate is made. Method:

1. **Value anchor**: price should be a fraction of the extra value recovered. Formula: `annual price <= share x (value at risk x recovery uplift)`. Share is the part of the gain the customer is willing to pay, to be tested at 5 to 20%.
2. **Van Westendorp questions**, added to the E2 interviews: at what annual price is it so cheap you doubt quality, a bargain, getting expensive, too expensive.
3. **Budget owner question**: who signs for a tool like this, and what is the usual threshold that avoids a long procurement process.
4. **Paid pilot ask**: the most honest signal of willingness to pay. Since the first pilot is free by decision, only the second and later pilots give this signal. In interviews, ask "would you pay for a second site?" as a proxy.

## Revenue scenarios (illustrative arithmetic, not a forecast)

Contract value placeholders: pilot P, annual subscription S.

| Scenario | Assumption | Year 1 | Year 2 |
|---|---|---|---|
| Conservative | 1 paid pilot, 0 conversions | P | 0 or S if converted |
| Expected | 2 pilots, 1 conversion | 2P | S plus new pilot |
| Optimistic | 3 pilots, 2 conversions | 3P | 2S plus new pilots |

No numbers are shown because P and S are not known. The value of this table is the structure: few customers, long cycles, so the first goal is evidence, not revenue.

## Pricing experiments

| Experiment | What we test | Method | Duration |
|---|---|---|---|
| Van Westendorp in interviews | Price acceptance range | 4 questions, 8 interviews | Weeks 1 to 2 |
| Paid pilot ask | Willingness to pay and buyer | Ask in the last 5 minutes of each interview | Weeks 1 to 2 |
| Tier limit test | Whether SKUs and plants are the right limits | Show two packaging options to 5 planners | Week 5 to 6 |
| Landing page price anchor | Interest by price band | Two versions of a pilot offer page | Weeks 8 to 9 |

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Buyer will not pay before seeing real data results | High | High | Short pilot with a clear report; credit fee to year one |
| Price set too low and anchors the market | Medium | Medium | Anchor on value recovered, not on effort |
| Open license weakens a paid offer | Medium | Medium | License decision recorded as an ADR before the public push (see `2_business_model.md`) |
| Outcome pricing creates disputes | Medium | Medium | Postpone; use only with a design partner |

## Metrics to track

* Pilot conversion rate and sales cycle length.
* Price acceptance range from interviews.
* ARPU by tier once there are customers.
* Pilot to subscription conversion drivers: data mapped, scenarios saved, scenarios exported.

## Next steps

1. Add the Van Westendorp and paid pilot questions to the interview script (`/pm-product-discovery:interview-script`).
2. Decide the repo license and record it as an ADR.
3. After competitive analysis, update the benchmark table with verified data.
