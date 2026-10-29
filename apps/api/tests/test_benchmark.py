"""Benchmark helpers and the scale smoke test (war plan 5.9)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from conftest import SCENARIOS
from reshelf_datagen import load_scenario

from reshelf.benchmark import (
    BenchRow,
    benchmark_config,
    build_world,
    load_rows,
    pick_channels,
    render,
    run_benchmark,
    run_row,
)


@pytest.fixture(scope="module")
def base() -> dict[str, Any]:
    return load_scenario(SCENARIOS / "default.yaml")


def test_five_channels_hold_every_type_once(base: dict[str, Any]) -> None:
    picked = pick_channels(base["generator"]["channels"], 5)
    assert len(picked) == 5
    assert {c["type"] for c in picked} == set(base["generator"]["channel_types"])


def test_pick_channels_is_capped_and_deterministic(base: dict[str, Any]) -> None:
    channels = base["generator"]["channels"]
    assert pick_channels(channels, 100) != []
    assert len(pick_channels(channels, 100)) == len(channels)
    assert pick_channels(channels, 7) == pick_channels(channels, 7)


def test_config_scales_sku_limits_and_keeps_the_input(base: dict[str, Any]) -> None:
    before = base["generator"]["channel_types"]["outlet"]["max_skus"]
    cfg = benchmark_config(base, 300, 5)
    assert cfg["generator"]["n_skus"] == 300
    assert cfg["generator"]["channel_types"]["outlet"]["max_skus"] == -(-before * 300 // 2000)
    assert base["generator"]["channel_types"]["outlet"]["max_skus"] == before
    assert len(base["generator"]["channels"]) == 20


def test_render_lists_every_row_with_its_limit() -> None:
    row = BenchRow(300, 5, "highs", 600, 2500, "feasible", 59.96, 60.0, None, 1234.4, 55.55, 0)
    text = render([row], "test env")
    assert "| 300 | 5 | highs | 600 | 2,500 | feasible | 60.0 | n/a | 1,234 | 55.5 | 0 |" in text
    assert "Time limit per solve: 60 s" in text
    assert "test env" in text


@pytest.mark.parametrize("backend", ["highs", "cbc"])
def test_scale_smoke_status_time_and_invariants(base: dict[str, Any], backend: str) -> None:
    """A mid size world solves inside the limit with a plan the full checker accepts."""
    data = build_world(base, 30, 5)
    row = run_row(data, 30, 5, backend, 60.0)  # type: ignore[arg-type]
    assert row.status in ("optimal", "feasible")
    assert row.time_s <= row.time_limit_s + 5.0
    assert row.violations == 0
    assert row.objective >= 0


def test_checkpoint_resumes_without_solving_again(base: dict[str, Any], tmp_path: Path) -> None:
    checkpoint = tmp_path / "rows.jsonl"
    first = run_benchmark(base, [20], [5], ["highs"], 30.0, checkpoint=checkpoint)
    assert len(load_rows(checkpoint)) == 1

    # Same row again: reused as saved, so the (changing) solve time is identical.
    again = run_benchmark(base, [20], [5], ["highs"], 30.0, checkpoint=checkpoint)
    assert again == first
    assert len(load_rows(checkpoint)) == 1

    # A new backend is solved and appended, the saved row stays.
    both = run_benchmark(base, [20], [5], ["highs", "cbc"], 30.0, checkpoint=checkpoint)
    assert both[0] == first[0]
    assert [r.backend for r in both] == ["highs", "cbc"]
    assert len(load_rows(checkpoint)) == 2
