# ADR 007: Counterfactual as a phase 2 re solve

**Status**: Accepted (2026-10-27)
**Deciders**: Nils
**Related**: `docs/war_plan.md` section 5.6, `reshelf/counterfactual.py`, `PulpSolver.improve`, ADR 006

> Evidence level: design decision, checked on hand built worlds (exact euro and unit answers) and on one seeded 30 SKU world (re solves of 1 to 5 s, all optimal). Behavior at 2,000 SKUs is unmeasured, see the week 3 benchmark.

## Context

The Why panel answers "what does this rule cost". The war plan chose rule trace plus an on demand re solve over MILP duals. This ADR fixes what the re solve changes and what it reports.

## Decisions

| Topic | Choice | Reason |
|---|---|---|
| What is relaxed | One instance of one traced rule, by editing the `SolverInput` bound it reads | The model and the checker read the same bound, so both see the same change |
| Modes | `plus_10pct` (10 percent more, at least one unit more, for an upper bound; 10 percent less for a lower bound) and `off` | Matches the war plan. `off` is a ceiling at total supply for upper bounds and zero for lower bounds |
| Not relaxable | `supply` and the four link constraints | Supply is physical, links are tight by construction |
| Phase | Phase 2 only, warm started from the original plan | Relaxing widens the feasible set, so the original plan is a valid start |
| Score floor | The original phase 1 optimum S*, with the same epsilon | The answer is the value the rule costs at the same SKU score. A new lexicographic optimum could trade score for value and blur the message |
| Cost | `max(0, relaxed value - original value)` in euro | A negative figure would only be solver noise or a time limit |
| Time limit | `counterfactual_time_limit_s` (10 s default) | Keeps the panel responsive |
| Limit hit under the original plan | Keep the original plan, report cost 0, status `feasible` and a plain sentence | Never show a figure the solver did not reach |
| Ranking for the precompute | Binding instances by number of lines they touch, ties by name | Cheap, deterministic, needs no extra solve |

## Consequences

* `units_destroyed_by_rule` is original minus relaxed destroyed units. It can be negative: when a rule is relaxed the value maximizer may send fewer but better units. The UI must show the euro cost first and the unit figure as context.
* Ranking by lines touched is a heuristic. A rule that binds one large line can cost more than one that binds many. The precompute may rank by measured cost later, at the price of one re solve per binding rule.
* Relaxing a rule can raise the best reachable SKU score. That gain is not counted here by design.
