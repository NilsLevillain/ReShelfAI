# ADR 004: Tight form for coverage and push constraints

**Status**: Accepted (2026-10-26)
**Deciders**: Nils
**Related**: `docs/war_plan.md` section 5.4, `reshelf/constraints.py`

> Evidence level: design decision. No benchmark yet. The solve time comparison is week 3 work.

## Context

Coverage and push rules apply only when a SKU is selected in a channel (binary `z[m,c]` is 1). The textbook way to write "if z then bound" is a Big M constraint with a generic large constant. A loose M gives a weak relaxation, slow solves and numerical trouble.

## Options

| Option | Upside | Downside |
|---|---|---|
| A. Generic Big M (one large constant) | Simple to write | Weak relaxation, slow, numerical risk |
| **B. Tight form: the binary multiplies the smallest valid bound** | Strong relaxation, no free constant, bound is explainable | Each bound must be computed and proven valid |

## Decision

Choose **B**. Constraints 8 to 10 are written as `sum x <= U * z` and `sum x >= B * z`:

* `cov_hi`: `sum x <= U[m,c] * z[m,c]`. U is the coverage need D, or the push quantity P for a NEW SKU.
* `cov_lo`: `sum x >= B[m,c] * z[m,c]` with `B = ceil(alpha * min(D, Q))`.
* `push`: same shape for NEW SKUs, with `B = min(P, Q)`.
* Q is the supply of the material in lots admissible for that channel, not the total stock. It is the smallest valid bound: units in eliminated lots can never reach the channel.
* D is rounded down to whole units, B is rounded up. Both are integers, so the bounds are valid for integer x.
* `link_yx` (y <= x) is added to the war plan list. Without it a selected SKU with a coverage need of 0 would earn assortment score without receiving a unit.

Where a Big M is unavoidable, M is the tightest available bound, never a generic constant. The link constraints use `q[l]`, the lot quantity.

## Consequences

* The bounds live in the solver input (`SolverInput.upper`, `lower`, `supply`). The model and the checker read the same numbers and cannot disagree.
* A NEW SKU never sold in a channel has no coverage need. Its upper bound is the push quantity, so a push is a bounded test quantity and not an open ended allocation.
* Changing coverage days, alpha or a push quantity changes only the bounds, not the model structure.
