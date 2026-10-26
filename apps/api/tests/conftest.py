from __future__ import annotations

import copy
import csv
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from reshelf_datagen import generate, load_scenario, write_tables

SCENARIOS = Path(__file__).resolve().parents[3] / "data" / "scenarios"

Row = dict[str, str]


def small_config(n_skus: int = 200, seed: int | None = None) -> dict[str, Any]:
    cfg = copy.deepcopy(load_scenario(SCENARIOS / "default.yaml"))
    cfg["generator"]["n_skus"] = n_skus
    if seed is not None:
        cfg["seed"] = seed
    return cfg


@pytest.fixture(scope="session")
def source_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Source CSV tables of a small seeded world. Read only: copy it before editing."""
    cfg = small_config()
    out = tmp_path_factory.mktemp("source")
    write_tables(generate(cfg), cfg, out)
    return out


def read_table(folder: Path, table: str) -> tuple[list[str], list[Row]]:
    with (folder / f"{table}.csv").open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


@pytest.fixture
def edit_source(source_dir: Path, tmp_path: Path) -> Callable[..., Path]:
    """Copy the source tables and let a test change rows of one table."""

    def edit(
        table: str | None = None, change: Callable[[list[Row]], list[Row]] | None = None
    ) -> Path:
        target = tmp_path / "edited"
        shutil.copytree(source_dir, target)
        if table is not None and change is not None:
            header, rows = read_table(target, table)
            with (target / f"{table}.csv").open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=header, lineterminator="\n")
                writer.writeheader()
                writer.writerows(change(rows))
        return target

    return edit
