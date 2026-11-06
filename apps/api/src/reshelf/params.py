"""Validation of parameter edits from the editor (war plan 6.2).

The base scenario file holds the defaults. An edit replaces one key of its `params` block. Every
value is checked here, so a bad number is a plain sentence at save time, not a solver failure.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

CLASSES = ("A", "B", "C", "NEW")
PLANNER_RULES = ("rsl", "tier", "capacity")

# key: (low, high, whole number). Scalar parameters only.
SCALARS: dict[str, tuple[float, float, bool]] = {
    "score_rank_weight": (0.0, 1.0, False),
    "epsilon": (0.0, 0.1, False),
    "coverage_days": (1, 365, True),
    "coverage_alpha": (0.0, 1.0, False),
    "solver_time_limit_s": (1, 600, True),
    "counterfactual_time_limit_s": (1, 120, True),
}


def _number(key: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{key} must be a number.")
    return float(value)


def _scalar(key: str, value: Any) -> None:
    low, high, whole = SCALARS[key]
    number = _number(key, value)
    if whole and number != int(number):
        raise ValueError(f"{key} must be a whole number.")
    if not low <= number <= high:
        raise ValueError(f"{key} must be between {low:g} and {high:g}.")


def validate_params(edits: Mapping[str, Any], defaults: Mapping[str, Any]) -> None:
    """Raise `ValueError` with a plain sentence for the first bad edit."""
    unknown = sorted(set(edits) - set(defaults))
    if unknown:
        raise ValueError(f"Unknown parameter(s): {', '.join(unknown)}.")
    for key, value in edits.items():
        if key in SCALARS:
            _scalar(key, value)
        elif key == "score_base":
            if not isinstance(value, dict) or set(value) != set(CLASSES):
                raise ValueError("score_base needs one value for each of A, B, C and NEW.")
            for cls, weight in value.items():
                if not 0 <= _number(f"score_base {cls}", weight) <= 2:
                    raise ValueError(f"score_base {cls} must be between 0 and 2.")
        elif key == "push_quantity_units":
            if not isinstance(value, dict):
                raise ValueError("push_quantity_units must map a category to units.")
            for category, units in value.items():
                number = _number(f"push_quantity_units {category}", units)
                if number != int(number) or not 0 <= number <= 10_000:
                    raise ValueError(
                        f"push_quantity_units {category} must be a whole number from 0 to 10000."
                    )
        elif key == "planner_rules":
            if not isinstance(value, list) or not set(value) <= set(PLANNER_RULES):
                raise ValueError(
                    f"planner_rules must be a list taken from {', '.join(PLANNER_RULES)}."
                )
