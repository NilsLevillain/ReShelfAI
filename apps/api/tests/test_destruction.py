"""Destruction causes: every unit that is not placed gets one cause, and the causes add up."""

from __future__ import annotations

from pathlib import Path

import factory as f
import pytest
from conftest import small_config
from reshelf_datagen import generate, write_tables

from reshelf.adapters import CsvAdapter
from reshelf.destruction import CAUSES, LEVER, DestructionOut, apportion, explain_destruction
from reshelf.solver import PulpSolver
from reshelf.solver_input import SolverInput, build_solver_input


def explain(data: SolverInput) -> DestructionOut:
    result = PulpSolver().solve(data)
    assert result.status == "optimal"
    return explain_destruction(data, result.x)


def units_by_cause(out: DestructionOut) -> dict[str, int]:
    return {c.cause: c.units for c in out.causes}


def test_apportion_adds_up_and_is_deterministic() -> None:
    parts = apportion(10, {"a": 1.0, "b": 1.0, "c": 1.0})
    assert sum(parts.values()) == 10
    assert parts == apportion(10, {"a": 1.0, "b": 1.0, "c": 1.0})
    assert apportion(5, {"a": 0.0, "b": 0.0}) == {"a": 0, "b": 0}
    assert apportion(0, {"a": 2.0}) == {"a": 0}


def test_channels_that_hold_enough_days_of_sales_cap_the_plan() -> None:
    # Sells 0.5 a day, 90 days of coverage is a need of 45 units. 100 units in the lot.
    data = f.solver_input(demands=[f.demand("M1", "C1", daily=0.5)])
    out = explain(data)
    assert units_by_cause(out) == {"coverage_ceiling": 55}
    assert out.units_placed == 45
    assert out.causes[0].lever == "coverage_days"


def test_new_products_stop_at_their_push_quantity() -> None:
    data = f.solver_input(demands=[f.demand("M1", "C1", history=False)])
    out = explain(data)
    assert units_by_cause(out) == {"push_ceiling": 50}
    assert out.causes[0].lever == "push_quantity_units"


def test_a_channel_that_already_has_stock_needs_nothing() -> None:
    data = f.solver_input(demands=[f.demand("M1", "C1", daily=2.0, stock=1000)])
    out = explain(data)
    assert units_by_cause(out) == {"no_demand": 100}


def test_a_lot_no_channel_accepts_is_blocked() -> None:
    data = f.solver_input(channels=[f.channel("C1", allowed=frozenset({"luxury"}))])
    out = explain(data)
    assert units_by_cause(out) == {"blocked": 100}
    assert out.units_placed == 0


def test_full_channel_capacity_is_named() -> None:
    data = f.solver_input(channels=[f.channel("C1", capacity=50)])
    out = explain(data)
    assert units_by_cause(out) == {"capacity": 50}


def test_a_channel_sku_limit_leaves_the_second_sku_unplaced() -> None:
    data = f.solver_input(
        materials=[f.material("M1"), f.material("M2")],
        lots=[f.lot("M1"), f.lot("M2")],
        channels=[f.channel("C1", max_skus=1)],
    )
    out = explain(data)
    assert units_by_cause(out) == {"sku_limit": 100}
    assert out.causes[0].lever == "channel_sku_limit_scale"
    assert out.causes[0].top_materials[0].units == 100


def test_room_with_no_tight_limit_is_not_worth_sending() -> None:
    # Net value is negative, the SKU is selected for its score and gets only its lower bound.
    data = f.solver_input(
        channels=[f.channel("C1", penalty={"luxury": 0.0, "premium": 0.0, "mass": 6.0})]
    )
    out = explain(data)
    assert units_by_cause(out) == {"not_worth": 50}


def test_causes_are_known_and_have_a_lever_entry() -> None:
    assert set(LEVER) == set(CAUSES)


@pytest.fixture(scope="module")
def generated(tmp_path_factory: pytest.TempPathFactory) -> SolverInput:
    cfg = small_config(n_skus=12, seed=3)
    out: Path = tmp_path_factory.mktemp("destruction")
    write_tables(generate(cfg), cfg, out)
    return build_solver_input(CsvAdapter(out).load())


def test_causes_add_up_to_the_units_destroyed_on_a_generated_world(generated: SolverInput) -> None:
    result = PulpSolver().solve(generated, 30)
    assert result.has_plan
    out = explain_destruction(generated, result.x)
    assert out.units_destroyed == result.units_destroyed
    assert sum(c.units for c in out.causes) == out.units_destroyed
    assert out.units_at_risk == out.units_placed + out.units_destroyed
    assert sum(c.share for c in out.causes) == pytest.approx(1.0 if out.units_destroyed else 0.0)
    assert all(c.units > 0 and c.value_at_risk >= 0 for c in out.causes)
    assert out == explain_destruction(generated, result.x)


def test_an_empty_plan_destroys_everything(generated: SolverInput) -> None:
    out = explain_destruction(generated, {})
    assert out.units_placed == 0
    assert sum(c.units for c in out.causes) == out.units_at_risk
