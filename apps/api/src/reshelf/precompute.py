"""Precompute command: run the real solver on each seeded scenario and write the demo JSON.

`python -m reshelf.precompute` writes `data/precomputed/<scenario>.json`, one `ScenarioResult`
per file (ADR 008). The web app reads these files in demo mode and shows "Cached results".

Demo world: the scenario with 30 SKUs and 5 channels, built by `benchmark.build_world`. Seed and
parameters come from the scenario file, so the plan, KPIs, trace and counterfactual costs are
reproducible. Solve times are not: `time_s` of the solve and of each counterfactual depends on the
machine and is the only field allowed to differ between two runs.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from reshelf.api_models import ScenarioResult
from reshelf.benchmark import build_world
from reshelf.pipeline import DEFAULT_TIME_LIMIT_S, run_scenario

DEMO_SKUS = 30
DEMO_CHANNELS = 5
DEFAULT_SCENARIOS = ("default", "luxury_protection")


def precompute_one(
    base: dict[str, Any],
    name: str,
    n_skus: int = DEMO_SKUS,
    n_channels: int = DEMO_CHANNELS,
    time_limit_s: float = DEFAULT_TIME_LIMIT_S,
    n_counterfactuals: int = 5,
) -> ScenarioResult:
    data = build_world(base, n_skus, n_channels)
    return run_scenario(
        data,
        name,
        time_limit_s=time_limit_s,
        n_counterfactuals=n_counterfactuals,
        seed=base.get("seed"),
        n_skus=n_skus,
        n_channels=n_channels,
    )


def write_result(result: ScenarioResult, out: Path) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{result.scenario}.json"
    path.write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the precomputed demo results.")
    parser.add_argument("--scenarios-dir", type=Path, default=Path("../../data/scenarios"))
    parser.add_argument("--out", type=Path, default=Path("../../data/precomputed"))
    parser.add_argument("--scenarios", nargs="+", default=list(DEFAULT_SCENARIOS))
    parser.add_argument("--n-skus", type=int, default=DEMO_SKUS)
    parser.add_argument("--n-channels", type=int, default=DEMO_CHANNELS)
    parser.add_argument("--time-limit", type=float, default=DEFAULT_TIME_LIMIT_S)
    args = parser.parse_args(argv)

    from reshelf_datagen import load_scenario

    for name in args.scenarios:
        base = load_scenario(args.scenarios_dir / f"{name}.yaml")
        result = precompute_one(base, name, args.n_skus, args.n_channels, args.time_limit)
        path = write_result(result, args.out)
        print(
            f"{name}: {result.solve.status} in {result.solve.time_s:.1f} s, "
            f"{len(result.lines)} lines, {len(result.counterfactuals)} counterfactuals -> {path}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
