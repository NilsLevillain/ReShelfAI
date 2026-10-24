# Metrics Dashboard: Reshelf

**Date**: 2026-10-24
**Stage**: Pre launch. The demo runs on synthetic data, so every baseline and target below is a hypothesis to calibrate, not a measured value and not a claim of business impact.

Reshelf has two "users", so it has two metric trees:

1. **The product**: a planner who allocates stock at risk.
2. **The repo as a product**: a hiring manager or peer who evaluates the work.

---

## 1. Product metrics

### North Star

**Exported net recovery rate**

* Definition: for each scenario a planner exports, `net recovered value / value at risk`, where net recovered value = Σ (unit cost × channel recovery factor − brand penalty) × units allocated. Reported as the median across exported scenarios in a planning cycle.
* Why this one: it measures value delivered (euros recovered from stock that would be destroyed), it counts only decisions the planner trusted enough to export, and it is net of brand cost so it cannot be inflated by dumping luxury stock.
* Data source: scenario results table plus export events.
* Window: per planning cycle (weekly in the demo).
* Target hypothesis: beats the greedy baseline by a visible margin on every seeded scenario (CI asserts a minimum gap).
* Business game: productivity and transaction hybrid. Value is created at the moment a decision is exported to the system of record.

### Input metrics

| Metric | Definition | Lever | Target hypothesis |
|---|---|---|---|
| Allocation coverage | Value at risk covered by an allocation / total value at risk | Rule defaults, channel capacity, solver quality | Above 85% on the default scenario |
| Optimizer uplift | Optimizer net value minus greedy net value, in euros and in % | Model quality, score weights | Positive on 100% of seeded datasets (property test) |
| Explained decisions | Exported scenarios where at least one Why panel was opened / exported scenarios | Why panel design, plain language traces | Above 60% |
| Scenarios compared per cycle | Compare views opened per planner per cycle | Compare UX, rule dial | 2 or more |
| Time to first export | Minutes from opening a dataset to the first export | Defaults, parameter editor, table UX | Under 10 minutes |

The five inputs are close to MECE: coverage and uplift explain the size of the value; explained decisions and compare explain trust; time to export explains effort.

### Health metrics

| Metric | Healthy | Yellow | Red | Check |
|---|---|---|---|---|
| Solve time, p95, 2,000 SKUs | Under 10 s | 10 to 30 s | Over 30 s | Every CI run |
| Solver status "optimal or gap within limit" | 99% or more | 95 to 99% | Under 95% | Every CI run |
| Counterfactual re solve time, p95 | Under 5 s | 5 to 10 s | Over 10 s (limit hit) | Every CI run |
| Infeasible or empty result rate | 0% on seeded scenarios | Any on a seeded scenario | More than one | Every CI run |
| Export success rate | 100% | 98 to 100% | Under 98% | Weekly |
| Demo cold start to first screen | Under 3 s (cached) | 3 to 8 s | Over 8 s | Weekly |

### Counter metrics

| Metric | Why it matters | Watch for |
|---|---|---|
| Brand risk index (Σ β·x / Σ v·x) | Net recovery can rise by pushing premium or luxury stock into low image channels | Index rising while the North Star rises |
| Manual override rate | A high rate means planners do not trust the optimizer; a zero rate may mean they never review | Above 40% or exactly 0% over many exports |

### Metrics tree

```
North Star: Exported net recovery rate
├── Input: Allocation coverage        → driven by rules, capacity, solver
├── Input: Optimizer uplift vs greedy → driven by model and score weights
├── Input: Explained decisions        → driven by Why panel and plain language traces
├── Input: Scenarios compared         → driven by compare view and rule dial
├── Input: Time to first export       → driven by defaults and table UX
├── Counter: Brand risk index         → watch for recovery bought with brand damage
└── Counter: Override rate            → watch for distrust or rubber stamping
```

### Implementation notes

* Demo: results are precomputed JSON, so the solver KPIs (coverage, uplift, net recovery, brand risk) come from `data/precomputed/*.json` and CI.
* Usage metrics (explained decisions, compare views, time to export) need event tracking. In the demo, use a lightweight privacy friendly tool (for example Plausible or PostHog free tier) with named events: `scenario_run`, `why_opened`, `compare_opened`, `export_clicked`.
* Honest limit: with no real users, input metrics 3 to 5 stay empty until the walkthrough experiment (E3) and the first pilot. Say so in the README.
* Refresh: CI metrics on each run; usage metrics daily.

### Review cadence

* Weekly: CI health metrics and benchmark table.
* Per build week: check the gap between optimizer and greedy.
* After each discovery experiment: update the input targets.
* Quarterly: reassess whether the North Star still reflects user value.

---

## 2. Portfolio metrics (the repo as a product)

### North Star

**Qualified conversations per month**: contacts (recruiter, hiring manager, peer) who reference the project or the product_management folder and lead to a call or an interview.

### Input metrics

| Metric | Definition | Lever | Target hypothesis |
|---|---|---|---|
| Repo and demo visitors | Unique visitors per month from LinkedIn, CV, profile | Posts, pinned repo, social preview | 200 or more in the first month after launch |
| Hero flow completion | Visitors who open compare and the Why panel / demo visitors | Story mode, landing view | Above 30% |
| Video view through | Viewers who watch 75% of the 75 s video | Video storyboard | Above 50% |
| 5 minute review pass rate | Reviewers who state problem, user and differentiator correctly (experiment E5) | README top, product_management index | 4 of 5 |

### Health metrics

| Metric | Healthy | Yellow | Red | Check |
|---|---|---|---|---|
| CI status on main | Green | Flaky | Red for over 1 day | Daily |
| Live demo uptime | Loads in under 3 s | 3 to 8 s | Down | Weekly |
| README broken links or images | 0 | 1 | 2 or more | Weekly |

### Counter metric

| Metric | Why it matters | Watch for |
|---|---|---|
| Stars and likes versus conversations | Vanity attention does not prove PM value | Visitors rising with zero conversations means the story or audience is off |

### Metrics tree

```
North Star: Qualified conversations per month
├── Input: Repo and demo visitors
├── Input: Hero flow completion
├── Input: Video view through
├── Input: 5 minute review pass rate
└── Counter: Stars and likes without conversations
```

## Next steps

* Write SQL or event specs for the usage events (`/write-query`).
* Turn the targets into OKRs for the 8 week build (`/plan-okrs`).
* Run `/pm-marketing-growth:north-star` later to challenge this North Star.
