"""Generated source tables through the adapter into the solver input."""

from __future__ import annotations

from pathlib import Path

import pytest

from reshelf.adapters import CsvAdapter
from reshelf.constraints import Solution, violations
from reshelf.solver_input import SolverInput, build_solver_input


@pytest.fixture(scope="module")
def data(source_dir: Path) -> SolverInput:
    return build_solver_input(CsvAdapter(source_dir).load())


def test_solver_input_has_admissible_pairs_and_reason_codes(data: SolverInput) -> None:
    assert data.admissible
    assert data.dropped
    assert {r for reasons in data.dropped.values() for r in reasons} <= {"RSL", "TIER", "NO_PUSH"}
    assert not set(data.admissible) & set(data.dropped)
    assert len(data.admissible) + len(data.dropped) == len(data.lots) * len(data.channels)


def test_every_selectable_pair_has_bounds_and_a_score(data: SolverInput) -> None:
    assert data.classes
    for mc in data.classes:
        assert 0 <= data.lower[mc] <= data.upper[mc] or data.classes[mc] == "NEW"
        assert data.score[mc] > 0
        assert data.supply[mc] > 0


def test_pairs_without_sales_are_new_and_pushed_by_category(data: SolverInput) -> None:
    new = [mc for mc, c in data.classes.items() if c == "NEW"]
    assert new
    for mc in new:
        category = data.materials[mc[0]].category
        assert data.upper[mc] == data.params.push_quantity_units[category]


def test_luxury_never_reaches_a_channel_that_refuses_it(data: SolverInput) -> None:
    for (lot_key, channel), reasons in data.dropped.items():
        tier = data.materials[lot_key[0]].tier
        if tier not in data.rules[channel].allowed_tiers:
            assert "TIER" in reasons


def test_the_empty_plan_is_feasible_on_generated_data(data: SolverInput) -> None:
    assert violations(data, Solution(x={})) == []
