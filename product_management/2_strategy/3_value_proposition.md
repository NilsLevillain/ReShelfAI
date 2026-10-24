# Value Proposition: Reshelf

**Date**: 2026-10-24
**Framework**: 6 part JTBD template (Who, Why, What before, How, What after, Alternatives), one per segment.
**Evidence level**: Hypotheses to be tested in interviews and the walkthrough (`../1_discovery/1_discovery_plan.md`, E2 and E3).

---

## For the supply planner (primary)

1. **Who**: A supply or demand planner at a consumer goods maker, in charge of stock that cannot go through primary retail (near expiry, packaging change, discontinued, overproduction). Works in Excel. Reports to a planning lead and answers to brand and finance.
2. **Why**: Send each lot to the channel where it recovers the most value, within the rules (shelf life, brand tier, capacity, assortment, coverage), and be able to defend the choice.
3. **What before**: The allocation is built by hand across spreadsheets. Rules are applied unevenly between regions. When brand or finance challenges a decision, there is no quick way to show what a rule costs. Units are destroyed because the rule check is slower than the expiry date.
4. **How**:
   * An optimizer that respects every rule at once and compares itself with a simple baseline on each run.
   * A "Why this allocation" panel: which rules were binding, which channels were blocked and why, and what relaxing one rule would gain, in euros.
   * Scenario save and compare, so a rule change shows its effect on value, destroyed units and brand risk.
   * Sortable tables first, Excel export for the order creation step, manual override.
5. **What after**: Allocation takes minutes, not days. The planner can answer "why did this lot go there?" and "what if we relax this rule?" in the meeting. Less sellable stock is destroyed.
6. **Alternatives**:

| Alternative | Why it falls short |
|---|---|
| Excel and manual rules | Slow, inconsistent, no rule cost, no scenario history |
| Planning suites | Built for forecasting and replenishment; second life allocation with brand rules is rarely the focus (H, verify in `4_market_scan.md`) |
| Returns and liquidation platforms | Strong at processing and selling goods; they do not explain a rule based allocation across plants and channels (H) |
| In house optimization team | Works, but is slow to change and hard for planners to read |
| Write off and destroy | Fast, but loses value and, in some markets, breaks the rules |

**Statement**: For supply planners who must place stock that cannot sell through primary retail, Reshelf is a decision support tool that allocates each lot to the best second life channel and shows what every rule costs. Unlike spreadsheets or black box optimizers, it lets you defend each decision in euros.

## For brand and finance reviewers (secondary)

1. **Who**: Brand managers and finance partners who approve or challenge allocation decisions.
2. **Why**: Protect brand image and limit write offs, without becoming a bottleneck.
3. **What before**: Decisions arrive as a spreadsheet with no reasoning. Approval is slow and driven by habit ("luxury never goes to clearance").
4. **How**: Brand risk index, "luxury protection" scenario, and the euro cost of each protective rule next to the alternatives.
5. **What after**: The trade off is a number both sides can read. Approval takes one meeting.
6. **Alternatives**: Email threads, blanket bans, trust in the planner. They are cheap and opaque.

**Statement**: For brand and finance teams who approve second life decisions, Reshelf is an approval aid that prices every protective rule. Unlike blanket bans, it shows what protection costs so you can choose it deliberately.

## For sustainability leads (tertiary)

1. **Who**: Sustainability or ESG lead who reports on waste.
2. **Why**: Show that sellable goods are not destroyed and prove where each unit went.
3. **What before**: Manual figures, hard to audit.
4. **How**: Units diverted per scenario and a traceable destination per line.
5. **What after**: A traceable figure for the report, tied to a decision log.
6. **Alternatives**: Manual tracking and donation partner reports.

Not a lead segment yet: it adds a reason to buy but is not the first user.

## Reusable statements

| Use | Statement |
|---|---|
| Marketing | Tighten a rule. See what it costs. See why. |
| Sales | Reshelf shows planners, brand and finance the euro cost of every allocation rule, so decisions take minutes and hold up in review. |
| Onboarding | Start with the seeded scenario, change one rule, and open the Why panel on the line that moved. |
| README top line | Reshelf allocates stock that can't sell through primary retail to second life channels, and shows what every rule costs. |

## Value curve (to validate in competitive analysis)

| Factor | Excel | Planning suite | Returns platform | Reshelf |
|---|---|---|---|---|
| Handles all rules at once | Low | High | Low | High |
| Rule cost explanation in euros | None | Low | None | **High** |
| Brand tier as a constraint | Manual | Low | Low | **High** |
| Setup effort | None | High | Medium | Medium |
| Familiar to planners | High | Medium | Low | Medium (table first) |

The ratings are hypotheses, not research. They become facts only after the competitive analysis that feeds the differentiators folder.

## The project value proposition

For hiring managers and peers who want to judge product skill, this repo shows the whole path from problem to metrics to strategy to a working, tested demo, with hypotheses and kill criteria stated in the open.

## Next steps

1. Test the planner statement in E2 and E3.
2. Turn the value curve into the differentiators document after competitive analysis.
3. Use the reusable statements for README, video and the landing page.
