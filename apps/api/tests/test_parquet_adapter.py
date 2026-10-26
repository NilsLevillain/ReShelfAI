"""Parquet adapter. TS-018: same canonical dataset as the CSV path."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from reshelf.adapters import CsvAdapter, DatasetError, ParquetAdapter
from reshelf.adapters.source_schemas import SOURCE_SCHEMAS


def to_parquet(source: Path, target: Path, typed: bool) -> None:
    target.mkdir()
    for table in SOURCE_SCHEMAS:
        frame = pd.read_csv(source / f"{table}.csv", dtype=str, keep_default_na=False)
        if typed:  # integer columns that survive the round trip as real integers
            for column in frame.columns:
                values = frame[column]
                if values.str.fullmatch(r"-?[1-9]\d*|0").all():
                    frame[column] = values.astype("int64")
        frame.to_parquet(target / f"{table}.parquet", index=False)


@pytest.mark.parametrize("typed", [False, True])
def test_parquet_gives_the_same_dataset_as_csv(
    source_dir: Path, tmp_path: Path, typed: bool
) -> None:
    target = tmp_path / "parquet"
    to_parquet(source_dir, target, typed)
    assert ParquetAdapter(target).load() == CsvAdapter(source_dir).load()


def test_missing_folder_and_missing_table_are_reported(source_dir: Path, tmp_path: Path) -> None:
    with pytest.raises(DatasetError, match="does not exist"):
        ParquetAdapter(tmp_path / "nowhere").load()
    target = tmp_path / "parquet"
    to_parquet(source_dir, target, typed=False)
    (target / "MARA.parquet").unlink()
    with pytest.raises(DatasetError, match="MARA"):
        ParquetAdapter(target).load()
