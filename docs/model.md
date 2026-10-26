# Model

Generated from the constraint registry (`apps/api/src/reshelf/constraints.py`).
Do not edit by hand. Run `make model-doc`. CI fails when this file drifts.

All rule values are invented illustrative defaults. They live in `ZPARAM` and in
the scenario yaml, never in code.

## Variables

| Symbol | Meaning |
|---|---|
| `x[l,c]` | Units of lot l sent to channel c (integer, at least 0) |
| `y[l,c]` | Lot l is used in channel c (binary) |
| `z[m,c]` | Material m is selected in channel c (binary) |

Variables exist only for admissible pairs, those that survive elimination.

## Elimination reason codes

Dropped before modeling. Each dropped pair keeps its code for the Why panel.

| Code | Meaning |
|---|---|
| `RSL` | Remaining shelf life at delivery is below the channel minimum, or the lot expires first |
| `TIER` | The brand tier of the material is not allowed in the channel |
| `NO_PUSH` | The material is new in the channel and its category has no push quantity |

## Named constraints

| Name | Index | Formula | Sense | Meaning | Reads | Planner rule |
|---|---|---|---|---|---|---|
| `supply` | `l` | `sum_c x[l,c] <= q[l]` | `<=` | A lot cannot ship more than it holds | `MCHB.CLABS` | none |
| `link_xy` | `l,c` | `x[l,c] <= q[l] * y[l,c]` | `<=` | Units only flow on a used lot and channel pair | none | none |
| `link_yx` | `l,c` | `y[l,c] <= x[l,c]` | `<=` | A used pair carries at least one unit | none | none |
| `link_yz` | `l,c` | `y[l,c] <= z[m(l),c]` | `<=` | A used lot needs its SKU selected in the channel | none | none |
| `link_zy` | `m,c` | `z[m,c] <= sum_{l in L(m)} y[l,c]` | `<=` | A selected SKU uses at least one lot | none | none |
| `cap` | `c` | `sum_l x[l,c] <= K[c]` | `<=` | Channel capacity in units | `ZCHANNEL.CAPUNITS` | `capacity` |
| `sku` | `c` | `sum_m z[m,c] <= S[c]` | `<=` | Channel limit on distinct SKUs | `ZCHANNEL.MAXSKU` | none |
| `asrt` | `g,c` | `sum_{m in g} z[m,c] <= A[g,c]` | `<=` | Assortment limit: SKUs of a brand and category in a channel | `ZCHANNEL_ASRT.MAXSKU` | none |
| `cov_hi` | `m,c` | `sum_{l in L(m)} x[l,c] <= U[m,c] * z[m,c]` | `<=` | Do not exceed the coverage need (push quantity for NEW) | `ZPARAM.COVERAGE_DAYS, ZSELLOUT, ZCHSTOCK, ZPARAM.PUSH_QUANTITY_UNITS_*` | none |
| `cov_lo` | `m,c` | `sum_{l in L(m)} x[l,c] >= B[m,c] * z[m,c]` | `>=` | A selected SKU covers at least alpha of its need | `ZPARAM.COVERAGE_ALPHA, ZPARAM.COVERAGE_DAYS` | none |
| `push` | `m,c` | `sum_{l in L(m)} x[l,c] >= B[m,c] * z[m,c]` | `>=` | A selected NEW SKU gets its push quantity | `ZPARAM.PUSH_QUANTITY_UNITS_*` | none |
| `asrt_units` | `g,c` | `sum_{l: m(l) in g} x[l,c] <= V[g,c]` | `<=` | Assortment limit: units of a brand and category in a channel | `ZCHANNEL_ASRT.MAXUNITS` | none |

Coverage and push rows use the tight form: the binary multiplies the smallest valid
bound (ADR 004). The rule trace reads the slack of each instance, so names stay stable.
