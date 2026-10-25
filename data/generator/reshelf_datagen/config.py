"""Scenario loading. A scenario yaml may extend another one in the same folder."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Merge dicts recursively. Lists and scalars in `override` replace those in `base`."""
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_scenario(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        raw: dict[str, Any] = yaml.safe_load(handle)
    parent = raw.pop("extends", None)
    if parent is None:
        return raw
    return deep_merge(load_scenario(path.parent / f"{parent}.yaml"), raw)
