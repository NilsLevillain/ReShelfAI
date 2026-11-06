# Benchmark (partial)

Status: partial. The full run (`python -m reshelf.benchmark`) was stopped by the system for low memory on its first 20 channel CBC row, and the benchmark was skipped on purpose on 2026-11-05. The 2,000 and 10,000 SKU rows are not measured. These numbers come from the checkpoint in `tmp/benchmark_rows.jsonl`. All data is simulated.

Setup: default scenario, one thread, 60 s time limit per solve, every plan audited with the full constraint checker.

| SKUs | Channels | Backend | Status | Time | Violations |
|---|---|---|---|---|---|
| 300 | 5 | HiGHS | optimal | 18 s | 0 |
| 300 | 5 | CBC | optimal | 2.4 s | 0 |
| 300 | 20 | HiGHS | optimal | 40 s | 0 |

Earlier measures on the 20 to 150 SKU worlds (not part of the benchmark file):

| World | Result |
|---|---|
| 30 SKUs, 4 channels | HiGHS optimal in 4 to 15 s with scaled SKU limits |
| 150 SKUs, 20 channels | Two of three seeds hit the 60 s limit, one returned a phase 1 score of 0 |

## Reading the numbers
* The demo world (30 SKUs, 5 channels) solves in under a second, so the demo does not depend on these limits.
* CBC was faster than HiGHS on both 300 SKU worlds. Worth a look before a larger default world picks a backend.
* Solve time at 2,000 SKUs is unproven. A solve that hits the limit returns the best plan found and reports it as feasible, not optimal.

## Rerun
Run from `apps/api` on a machine with enough memory: `uv run python -m reshelf.benchmark`. The run resumes from the checkpoint. Cut order puts the 10,000 SKU row first.
