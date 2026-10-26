from __future__ import annotations

from pathlib import Path

import pandas as pd

from reshelf.adapters.folder import load_folder
from reshelf.schema import CanonicalDataset


def _read(path: Path) -> pd.DataFrame:
    # Strings only, so identifiers such as material numbers keep their leading zeros.
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")


class CsvAdapter:
    """Reads one CSV file per source table from a folder, as written by the data generator."""

    def __init__(self, folder: Path | str) -> None:
        self.folder = Path(folder)

    def load(self) -> CanonicalDataset:
        return load_folder(self.folder, ".csv", _read)
