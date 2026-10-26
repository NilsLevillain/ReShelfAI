"""Source adapters: read source tables and return a validated canonical dataset."""

from reshelf.adapters.base import DatasetError, SourceAdapter
from reshelf.adapters.csv import CsvAdapter
from reshelf.adapters.parquet import ParquetAdapter

__all__ = ["CsvAdapter", "DatasetError", "ParquetAdapter", "SourceAdapter"]
