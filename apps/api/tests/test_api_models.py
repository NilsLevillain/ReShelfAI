"""Response models and the scenario pipeline: one JSON contract for the API and the precompute."""

from __future__ import annotations

import pytest
from factory import solver_input

from reshelf.api_models import ScenarioResult
from reshelf.pipeline import run_scenario


@pytest.fixture(scope="module")
def result() -> ScenarioResult:
    return run_scenario(solver_input(), "unit", time_limit_s=20.0, seed=1, n_skus=1, n_channels=1)


def test_solver_fields_are_passed_on_unchanged(result: ScenarioResult) -> None:
    assert result.solve.status == "optimal"
    assert result.solve.time_limit_s == 20.0
    assert result.solve.time_s >= 0
    assert result.label == "Simulated data"


def test_json_round_trip(result: ScenarioResult) -> None:
    again = ScenarioResult.model_validate_json(result.model_dump_json())
    assert again == result


def test_lines_obey_the_result_invariants(result: ScenarioResult) -> None:
    assert result.lines, "the default world sells something"
    for line in result.lines:
        assert line.quantity > 0
        assert line.quantity <= line.lot_supply
        assert line.line == f"{line.lot},{line.channel}"


def test_totals_reconcile_with_the_kpis(result: ScenarioResult) -> None:
    assert sum(line.quantity for line in result.lines) == result.optimizer.units_allocated
    assert sum(line.net_value_eur for line in result.lines) == pytest.approx(
        result.optimizer.value_recovered
    )
    assert result.optimizer.value_recovered == pytest.approx(result.solve.objective, rel=1e-4)
    assert result.baseline.compliant.units_allocated == sum(
        line.quantity for line in result.baseline.compliant_lines
    )


def test_trace_lines_match_allocation_lines(result: ScenarioResult) -> None:
    assert [t.line for t in result.trace.lines] == [line.line for line in result.lines]
