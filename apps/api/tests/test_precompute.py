"""Precompute command: valid JSON, one file per scenario, reproducible apart from solve times."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from conftest import SCENARIOS
from reshelf_datagen import load_scenario

from reshelf.api_models import ScenarioResult
from reshelf.precompute import main, precompute_one, write_result


@pytest.fixture(scope="module")
def base() -> dict[str, Any]:
    return load_scenario(SCENARIOS / "default.yaml")


def _without_times(result: ScenarioResult) -> dict[str, Any]:
    data = result.model_dump()
    data["solve"].pop("time_s")
    for item in data["counterfactuals"]:
        item.pop("time_s")
    return data


@pytest.fixture(scope="module")
def first(base: dict[str, Any]) -> ScenarioResult:
    return precompute_one(
        base, "default", n_skus=20, n_channels=5, time_limit_s=30.0, n_counterfactuals=2
    )


def test_written_file_loads_back(first: ScenarioResult, tmp_path: Path) -> None:
    path = write_result(first, tmp_path)
    assert path.name == "default.json"
    assert ScenarioResult.model_validate_json(path.read_text(encoding="utf-8")) == first
    assert first.seed == 20261025
    assert first.n_skus == 20
    assert first.solve.status == "optimal"
    assert first.counterfactuals, "the demo world has binding rules to relax"


def test_rerun_is_identical_apart_from_times(base: dict[str, Any], first: ScenarioResult) -> None:
    again = precompute_one(
        base, "default", n_skus=20, n_channels=5, time_limit_s=30.0, n_counterfactuals=2
    )
    assert _without_times(again) == _without_times(first)


def test_optimizer_is_compared_with_the_baseline(first: ScenarioResult) -> None:
    assert first.baseline.compliant.score <= first.optimizer.score + 1e-6
    assert first.baseline.raw.units_allocated >= first.baseline.compliant.units_allocated


def test_cli_writes_one_file_per_scenario(tmp_path: Path) -> None:
    code = main(
        [
            "--scenarios-dir", str(SCENARIOS),
            "--out", str(tmp_path),
            "--scenarios", "default",
            "--n-skus", "20",
            "--time-limit", "30",
        ]
    )  # fmt: skip
    assert code == 0
    assert [p.name for p in tmp_path.iterdir()] == ["default.json"]
