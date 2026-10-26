"""Shared by the file adapters: one file per source table in a folder."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pandas as pd

from reshelf.adapters.base import DatasetError
from reshelf.adapters.sap import build_dataset
from reshelf.adapters.source_schemas import SOURCE_SCHEMAS
from reshelf.schema import CanonicalDataset


def load_folder(
    folder: Path, suffix: str, read: Callable[[Path], pd.DataFrame]
) -> CanonicalDataset:
    """Read `{table}{suffix}` for every source table. `read` must return text columns only."""
    if not folder.is_dir():
        raise DatasetError(f"source folder {folder} does not exist")
    frames: dict[str, pd.DataFrame] = {}
    for table in SOURCE_SCHEMAS:
        path = folder / f"{table}{suffix}"
        if not path.is_file():
            raise DatasetError(f"source table {table} is missing: {path}")
        frames[table] = read(path)
    return build_dataset(frames)
