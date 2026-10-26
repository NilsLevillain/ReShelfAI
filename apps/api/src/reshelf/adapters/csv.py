from __future__ import annotations

from pathlib import Path

import pandas as pd

from reshelf.adapters.base import DatasetError
from reshelf.adapters.sap import build_dataset
from reshelf.adapters.source_schemas import SOURCE_SCHEMAS
from reshelf.schema import CanonicalDataset


class CsvAdapter:
    """Reads one CSV file per source table from a folder, as written by the data generator."""

    def __init__(self, folder: Path | str) -> None:
        self.folder = Path(folder)

    def load(self) -> CanonicalDataset:
        if not self.folder.is_dir():
            raise DatasetError(f"source folder {self.folder} does not exist")
        frames: dict[str, pd.DataFrame] = {}
        for table in SOURCE_SCHEMAS:
            path = self.folder / f"{table}.csv"
            if not path.is_file():
                raise DatasetError(f"source table {table} is missing: {path}")
            # Strings only, so identifiers such as material numbers keep their leading zeros.
            frames[table] = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")
        return build_dataset(frames)
