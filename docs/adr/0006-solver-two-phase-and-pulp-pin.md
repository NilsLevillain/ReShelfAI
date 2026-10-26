# ADR 006: Two phase solver on PuLP 3

**Status**: Accepted (2026-10-26)
**Deciders**: Nils
**Related**: `docs/war_plan.md` sections 5.1 and 5.5, `reshelf/solver.py`, `reshelf/model.py`, ADR 004

> Evidence level: design decision, checked on small instances and on one 300 SKU instance (4 channels, 1,200 admissible pairs, HiGHS proved optimality in about 8 s). The full benchmark is week 3 work.

## Context

The solver must read only a `SolverInput`, build its rows from the named constraint registry, and return a `SolveResult` the API can pass on unchanged. Two facts about the tooling shaped the choices below.

* `uv.lock` resolved two PuLP versions, 3.3.2 for Python below 3.12 and 4.2.0 above. PuLP 4 changed the variable API, so the same code failed on one machine and ran on another.
* PuLP 3.3.2 ships a CBC binary and a HiGHS interface. After a solve, `problem.solverModel` is the `highspy.Highs` object, which holds the status and the MIP gap.

## Decisions

| Topic | Choice | Reason |
|---|---|---|
| PuLP version | `pulp>=3.3,<4` | One API on every Python version. Moving to 4 is a change in `model.py` only |
| Model source | One builder per registry name, a test compares both lists | A constraint cannot be in the docs and missing from the model |
| Row labels | Rows are kept by registry label, for example `cap[OUT_PL]`, not by PuLP name | PuLP rewrites some characters in names. The rule trace reads slack by the same label the checker prints |
| Phase 1 | Maximize the SKU score, gap 1e-6 | S* must be close to exact, since phase 2 is bound to it |
| Phase 2 | Score at least (1 - epsilon) S* minus 1e-6, then maximize net value, gap 1e-4, warm start from phase 1 | The small slack keeps epsilon 0 from turning rounding noise into an infeasible model |
| Time | One budget for both phases. Phase 2 gets what phase 1 left | The total never exceeds the limit by design |
| Threads and seed | One thread, seed 0 | Same input gives the same plan |
| Backend | HiGHS, CBC when HiGHS cannot load or when asked | The result names the backend that ran. CBC reports no gap, so its gap is `None` and it runs without warm start (on Windows it needs `keepFiles`, which leaves files behind) |

## Status values

| Status | Meaning |
|---|---|
| `optimal` | Both phases proven optimal within their gaps |
| `feasible` | Time limit reached with a valid plan. If phase 2 found nothing, the phase 1 plan is returned with no value gap |
| `time_limit` | Time limit reached with no plan |
| `infeasible` | Guard only, see below |
| `error` | The backend failed. The message says so in plain words |

Every result that is not `optimal` carries a plain sentence in `message`.

## Consequences

* **The model cannot be infeasible.** With z = 0 every coverage and push row is off (ADR 004), so the empty plan always satisfies the model. Rules that cannot be met, such as a push quantity above the channel capacity, produce a valid plan that leaves the units destroyed. Test scenario TS-046 is tested in that form. The `infeasible` status stays as a guard, with a sentence that names contradicting rules as the likely cause.
* The `mip_gap` of a result is the gap of the last phase solved. It says how far the net value can be from the best value inside the score band, not how far the score is from S*.
* The deprecation warnings that PuLP 3.3 prints about version 4 are expected until the pin is lifted.
