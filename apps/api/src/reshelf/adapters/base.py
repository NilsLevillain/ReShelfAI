from __future__ import annotations

from typing import Protocol

from reshelf.schema import CanonicalDataset


class DatasetError(ValueError):
    """The source data cannot be turned into a valid canonical dataset."""


class SourceAdapter(Protocol):
    def load(self) -> CanonicalDataset:
        """Read the source and return a validated canonical dataset, or raise `DatasetError`."""
        ...
