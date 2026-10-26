"""ADR 005 on the 50 neutral seeds. TS-065, TS-066.

For each seed the optimizer is compared with the compliant baseline, never with the raw one:

1. optimizer score >= compliant baseline score, and
2. when the baseline score is within epsilon of the optimizer score, optimizer net value >=
   baseline net value.

Worlds are small (`N_SKUS`) so 50 solves stay affordable. Channel SKU limits are scaled with the
world, otherwise the assortment rules never bind at this size.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from conftest import SCENARIOS, small_config
from reshelf_datagen import generate, write_tables

from reshelf.adapters import CsvAdapter
from reshelf.baseline import baseline_planner
from reshelf.constraints import Solution, violations
from reshelf.solver import PulpSolver
from reshelf.solver_input import SolverInput, build_solver_input

N_SKUS = 20
FULL_SIZE = 2000
SEEDS: list[int] = yaml.safe_load((SCENARIOS / "neutral_seeds.yaml").read_text())["seeds"]
TOLERANCE = 1e-6


def world(seed: int, tmp_path: Path) -> SolverInput:
    cfg = small_config(n_skus=N_SKUS, seed=seed)
    for spec in cfg["generator"]["channel_types"].values():
        spec["max_skus"] = max(1, -(-spec["max_skus"] * N_SKUS // FULL_SIZE))
    write_tables(generate(cfg), cfg, tmp_path)
    return build_solver_input(CsvAdapter(tmp_path).load())


def test_there_are_50_distinct_seeds() -> None:
    assert len(SEEDS) == 50
    assert len(set(SEEDS)) == 50


@pytest.mark.slow
@pytest.mark.parametrize("seed", SEEDS)
def test_optimizer_is_at_least_the_compliant_baseline(seed: int, tmp_path: Path) -> None:
    data = world(seed, tmp_path)
    result = PulpSolver().solve(data)
    baseline = baseline_planner(data)

    assert result.status == "optimal"
    assert violations(data, Solution(x=baseline.compliant_x)) == []
    assert violations(data, Solution(x=result.x, y=result.y, z=result.z)) == []

    score_opt, score_base = result.score, baseline.compliant.score
    assert score_opt >= score_base - TOLERANCE * max(1.0, abs(score_opt))

    epsilon = data.params.epsilon
    if score_base >= (1 - epsilon) * score_opt:
        slack = (result.mip_gap or 0.0) * abs(result.objective) + TOLERANCE
        assert result.objective >= baseline.compliant.value_recovered - slack
