"""Benchmark of the solver on seeded worlds of growing size (war plan 5.9).

`python -m reshelf.benchmark` solves the default scenario at several SKU counts and channel
counts, with HiGHS and CBC, and writes the table to `docs/benchmark.md`. The numbers depend on the
machine, so the file records the environment and the time limit. Nothing here runs in CI: the
fast scale smoke test lives in `tests/test_benchmark.py`.

World rules, so a row can be reproduced:
* The default scenario with `n_skus` replaced. The seed stays the one of the scenario.
* Channels are taken round robin over the channel types (one per type first), so 5 channels hold
  every type once.
* `max_skus` of every channel type scales with `n_skus / 2000`, as in the seed property test.
  Capacities already follow the total stock, so they need no scaling.
"""

from __future__ import annotations

import argparse
import copy
import json
import platform
import sys
import tempfile
import time
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from reshelf.adapters import CsvAdapter
from reshelf.constraints import Solution, violations
from reshelf.solver import PulpSolver, SolveStatus
from reshelf.solver_input import SolverInput, build_solver_input

Backend = Literal["highs", "cbc"]

FULL_SIZE = 2000
DEFAULT_SIZES = (300, 2000, 10000)
DEFAULT_CHANNELS = (5, 20)
DEFAULT_BACKENDS: tuple[Backend, ...] = ("highs", "cbc")
DEFAULT_TIME_LIMIT_S = 60.0


@dataclass(frozen=True)
class BenchRow:
    n_skus: int
    n_channels: int
    backend: Backend
    lots: int
    pairs: int
    status: SolveStatus
    time_s: float
    time_limit_s: float
    mip_gap: float | None
    objective: float
    score: float
    violations: int


def pick_channels(channels: Sequence[dict[str, Any]], n: int) -> list[dict[str, Any]]:
    """First `n` channels, round robin over channel types in order of first appearance."""
    by_type: dict[str, list[dict[str, Any]]] = {}
    for channel in channels:
        by_type.setdefault(channel["type"], []).append(channel)
    picked: list[dict[str, Any]] = []
    rank = 0
    while len(picked) < min(n, len(channels)):
        for group in by_type.values():
            if rank < len(group) and len(picked) < n:
                picked.append(group[rank])
        rank += 1
    return picked


def benchmark_config(base: dict[str, Any], n_skus: int, n_channels: int) -> dict[str, Any]:
    cfg = copy.deepcopy(base)
    cfg["generator"]["n_skus"] = n_skus
    cfg["generator"]["channels"] = pick_channels(cfg["generator"]["channels"], n_channels)
    used = {channel["type"] for channel in cfg["generator"]["channels"]}
    cfg["generator"]["channel_types"] = {
        name: spec for name, spec in cfg["generator"]["channel_types"].items() if name in used
    }
    for spec in cfg["generator"]["channel_types"].values():
        spec["max_skus"] = max(1, -(-spec["max_skus"] * n_skus // FULL_SIZE))
    return cfg


def build_world(base: dict[str, Any], n_skus: int, n_channels: int) -> SolverInput:
    # The generator is a data tool outside the package, imported here so `reshelf` loads without it.
    from reshelf_datagen import generate, write_tables

    cfg = benchmark_config(base, n_skus, n_channels)
    with tempfile.TemporaryDirectory() as folder:
        write_tables(generate(cfg), cfg, Path(folder))
        return build_solver_input(CsvAdapter(Path(folder)).load())


def run_row(
    data: SolverInput, n_skus: int, n_channels: int, backend: Backend, time_limit_s: float
) -> BenchRow:
    result = PulpSolver(backend).solve(data, time_limit_s)
    broken = (
        violations(data, Solution(x=result.x, y=result.y, z=result.z)) if result.has_plan else []
    )
    return BenchRow(
        n_skus=n_skus,
        n_channels=n_channels,
        backend=backend,
        lots=len(data.lots),
        pairs=len(data.admissible),
        status=result.status,
        time_s=result.time_s,
        time_limit_s=time_limit_s,
        mip_gap=result.mip_gap,
        objective=result.objective,
        score=result.score,
        violations=len(broken),
    )


def _key(row: BenchRow) -> tuple[int, int, str, float]:
    return (row.n_skus, row.n_channels, row.backend, row.time_limit_s)


def load_rows(path: Path) -> list[BenchRow]:
    """Rows saved by an earlier run. An unreadable line raises, it is never skipped."""
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [BenchRow(**json.loads(line)) for line in lines if line.strip()]


def run_benchmark(
    base: dict[str, Any],
    sizes: Sequence[int] = DEFAULT_SIZES,
    channels: Sequence[int] = DEFAULT_CHANNELS,
    backends: Sequence[Backend] = DEFAULT_BACKENDS,
    time_limit_s: float = DEFAULT_TIME_LIMIT_S,
    log: bool = False,
    checkpoint: Path | None = None,
) -> list[BenchRow]:
    """Rows in the order sizes, channels, backends.

    With a `checkpoint` file every finished row is appended to it (one JSON object per line), and
    rows already in it for the same size, channels, backend and limit are reused. A run that is
    killed can be started again and continues where it stopped.
    """
    saved = {_key(r): r for r in load_rows(checkpoint)} if checkpoint else {}
    rows: list[BenchRow] = []
    for n_skus in sizes:
        for n_channels in channels:
            todo = [b for b in backends if (n_skus, n_channels, b, time_limit_s) not in saved]
            data: SolverInput | None = None
            if todo:
                started = time.perf_counter()
                data = build_world(base, n_skus, n_channels)
                if log:
                    print(
                        f"world {n_skus} SKUs x {n_channels} channels: {len(data.admissible)} "
                        f"pairs, built in {time.perf_counter() - started:.1f} s",
                        flush=True,
                    )
            for backend in backends:
                known = saved.get((n_skus, n_channels, backend, time_limit_s))
                if known is not None:
                    rows.append(known)
                    if log:
                        print(
                            f"  {n_skus} x {n_channels} {backend}: reused from checkpoint",
                            flush=True,
                        )
                    continue
                assert data is not None
                row = run_row(data, n_skus, n_channels, backend, time_limit_s)
                rows.append(row)
                if checkpoint:
                    with checkpoint.open("a", encoding="utf-8", newline="\n") as handle:
                        handle.write(json.dumps(asdict(row)) + "\n")
                if log:
                    print(f"  {backend}: {row.status} in {row.time_s:.1f} s", flush=True)
    return rows


def _gap(row: BenchRow) -> str:
    return "n/a" if row.mip_gap is None else f"{row.mip_gap * 100:.2f}%"


def render(rows: Sequence[BenchRow], environment: str) -> str:
    """Markdown of `docs/benchmark.md`."""
    limit = rows[0].time_limit_s if rows else DEFAULT_TIME_LIMIT_S
    lines = [
        "# Benchmark",
        "",
        "Generated by `python -m reshelf.benchmark`. Do not edit by hand.",
        "",
        "Solve time of the full model (both phases, model build included) on seeded worlds of the",
        "default scenario. Times depend on the machine, so read them as orders of magnitude.",
        "",
        f"* Environment: {environment}",
        f"* Time limit per solve: {limit:g} s, one thread, fixed random seed.",
        "* Status `optimal` means both phases were proven optimal inside the limit. `feasible` means",
        "  the limit came first and the plan is valid but not proven optimal. `time_limit` means no",
        "  plan was found. Gap is the relative MIP gap of phase 2, `n/a` when none was reported.",
        "* Channels are taken one per channel type first. `max_skus` scales with SKUs divided by 2,000.",
        "* Every plan with a result was audited by the full constraint checker (column Violations).",
        "",
        "| SKUs | Channels | Solver | Lots | Admissible pairs | Status | Time (s) | Gap | "
        "Net value (EUR) | Score | Violations |",
        "|---:|---:|---|---:|---:|---|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r.n_skus:,} | {r.n_channels} | {r.backend} | {r.lots:,} | {r.pairs:,} | "
            f"{r.status} | {r.time_s:.1f} | {_gap(r)} | {r.objective:,.0f} | {r.score:.1f} | "
            f"{r.violations} |"
        )
    lines.append("")
    return "\n".join(lines)


def describe_environment() -> str:
    import highspy
    import pulp

    return (
        f"Python {platform.python_version()}, {platform.system()}, PuLP {pulp.__version__}, "
        f"highspy {getattr(highspy, '__version__', 'unknown')}"
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark the solver on seeded worlds.")
    parser.add_argument("--scenario", type=Path, default=Path("../../data/scenarios/default.yaml"))
    parser.add_argument("--out", type=Path, default=Path("../../docs/benchmark.md"))
    parser.add_argument("--sizes", type=int, nargs="+", default=list(DEFAULT_SIZES))
    parser.add_argument("--channels", type=int, nargs="+", default=list(DEFAULT_CHANNELS))
    parser.add_argument("--backends", nargs="+", choices=["highs", "cbc"], default=["highs", "cbc"])
    parser.add_argument("--time-limit", type=float, default=DEFAULT_TIME_LIMIT_S)
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=Path("../../tmp/benchmark_rows.jsonl"),
        help="finished rows are appended here and reused on the next run",
    )
    parser.add_argument("--fresh", action="store_true", help="delete the checkpoint first")
    args = parser.parse_args(argv)

    from reshelf_datagen import load_scenario

    if args.fresh:
        args.checkpoint.unlink(missing_ok=True)
    args.checkpoint.parent.mkdir(parents=True, exist_ok=True)
    rows = run_benchmark(
        load_scenario(args.scenario),
        sizes=args.sizes,
        channels=args.channels,
        backends=args.backends,
        time_limit_s=args.time_limit,
        log=True,
        checkpoint=args.checkpoint,
    )
    args.out.write_text(render(rows, describe_environment()), encoding="utf-8", newline="\n")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
