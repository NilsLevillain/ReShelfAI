# ADR 003: The lot is the decision index

**Status**: Accepted (2026-10-26)
**Deciders**: Nils
**Related**: `docs/war_plan.md` sections 4 and 5.3, `docs/mapping.md` (Lot), `docs/erd.md`

> Evidence level: design decision. Sizes quoted are from the seeded default scenario, not from a benchmark.

## Context

Stock sits in batches (`MCHB`), each with its own expiry date. The model must decide how many units go to each channel. The index of that decision sets the size of the model, and it must keep the remaining shelf life rule exact.

## Options

| Option | Upside | Downside |
|---|---|---|
| A. Material by plant | Smallest model | Cannot apply remaining shelf life per expiry date. One lot with mixed ages gets one verdict |
| B. One variable per batch | Exact | Very large model. Batches are an ERP detail with no planning meaning |
| **C. Lot: material by plant by expiry month** | Exact rule at month grain, small model, easy to explain | Batches in one month share one verdict |

## Decision

Choose **C**. A lot groups all batches of one material in one plant that expire in the same calendar month (`yyyy-mm`).

* Lot quantity is the sum of `CLABS` over batches and storage locations.
* Lot `expiry_date` is the **earliest** batch expiry in the bucket. Remaining shelf life is never overstated, so a lot that passes the rule has no batch that fails it.
* Remaining shelf life is measured at delivery: `as_of` plus the channel transit days.
* Elimination (`reshelf/elimination.py`) works per (lot, channel) pair and keeps reason codes `RSL`, `TIER` and `NO_PUSH`.

## Consequences

* The default scenario has about 4,700 lots and 20 channels, so about 94,600 pairs before elimination and about 54,000 after.
* Using the earliest expiry is conservative: a few units of a lot with a later batch may be held back. The loss is small because batches inside one lot differ by weeks, not months.
* Storage location is not part of the key. Two locations in one plant are one lot.
* A finer grain (week, or batch) stays possible later without changing the solver, because the solver only sees lots.
