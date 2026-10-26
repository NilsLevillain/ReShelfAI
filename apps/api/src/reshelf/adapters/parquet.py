from __future__ import annotations

from pathlib import Path

import pandas as pd

from reshelf.adapters.folder import load_folder
from reshelf.schema import CanonicalDataset


def _read(path: Path) -> pd.DataFrame:
    # Parquet carries types. Cast to text and let the pandera schemas coerce, so the CSV and
    # Parquet paths feed the same frames to the SAP mapping.
    return pd.read_parquet(path).fillna("").astype(str)


class ParquetAdapter:
    """Reads one Parquet file per source table from a folder."""

    def __init__(self, folder: Path | str) -> None:
        self.folder = Path(folder)

    def load(self) -> CanonicalDataset:
        return load_folder(self.folder, ".parquet", _read)
