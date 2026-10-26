"""Rule trace: binding rules per allocation line and the channels elimination blocked."""

from __future__ import annotations

import factory as f
import pytest

from reshelf.constraints import Solution
from reshelf.ids import Pair
from reshelf.schema import GroupLimit
from reshelf.solver import PulpSolver
from reshelf.solver_input import SolverInput
from reshelf.trace import TRACED_RULES, BlockedChannel, build_trace


def pair(data: SolverInput, material: str, channel: str) -> Pair:
    (key,) = [k for k in data.lots if k[0] == material]
    return (key, channel)


def binding_names(data: SolverInput, x: dict[Pair, int]) -> set[str]:
    trace = build_trace(data, Solution(x=x))
    return {rule.constraint for line in trace.lines for rule in line.binding}


def test_supply_binds_when_the_lot_ships_fully() -> None:
    data = f.solver_input()
    assert "supply" in binding_names(data, {pair(data, "M1", "C1"): 100})
    assert "supply" not in binding_names(data, {pair(data, "M1", "C1"): 60})


def test_cap_binds_at_channel_capacity() -> None:
    data = f.solver_input(channels=[f.channel("C1", capacity=50)])
    assert "cap" in binding_names(data, {pair(data, "M1", "C1"): 50})
    assert "cap" not in binding_names(data, {pair(data, "M1", "C1"): 49})


def test_sku_binds_at_the_sku_limit() -> None:
    data = f.solver_input(channels=[f.channel("C1", max_skus=1)])
    assert "sku" in binding_names(data, {pair(data, "M1", "C1"): 60})


def test_cov_hi_binds_at_the_coverage_need() -> None:
    # 1 unit a day over 90 days is a need of 90
    data = f.solver_input(demands=[f.demand("M1", "C1", daily=1.0)])
    assert "cov_hi" in binding_names(data, {pair(data, "M1", "C1"): 90})
    assert "cov_hi" not in binding_names(data, {pair(data, "M1", "C1"): 80})


def test_cov_lo_binds_at_the_lower_bound() -> None:
    # need 180, supply 100, alpha 0.5 gives a lower bound of 50
    data = f.solver_input()
    assert "cov_lo" in binding_names(data, {pair(data, "M1", "C1"): 50})
    assert "cov_lo" not in binding_names(data, {pair(data, "M1", "C1"): 51})


def test_push_binds_for_a_new_material() -> None:
    data = f.solver_input(demands=[f.demand("M1", "C1", history=False)])
    names = binding_names(data, {pair(data, "M1", "C1"): 50})  # Haircare push quantity is 50
    assert {"push", "cov_hi"} <= names
    assert "cov_lo" not in names


def _group_data() -> SolverInput:
    return f.solver_input(
        materials=[f.material("M1"), f.material("M2")],
        lots=[f.lot("M1"), f.lot("M2")],
        group_limits=[
            GroupLimit(
                channel="C1", brand="Brightleaf", category="Haircare", max_skus=1, max_units=100
            )
        ],
    )


def test_asrt_and_asrt_units_bind_at_the_group_limits() -> None:
    data = _group_data()
    names = binding_names(data, {pair(data, "M1", "C1"): 100})
    assert {"asrt", "asrt_units"} <= names
    # One SKU still fills the SKU limit, but 60 units leave room under the unit limit.
    partial = binding_names(data, {pair(data, "M1", "C1"): 60})
    assert "asrt" in partial
    assert "asrt_units" not in partial


def test_link_constraints_are_never_traced() -> None:
    data = f.solver_input()
    trace = build_trace(data, Solution(x={pair(data, "M1", "C1"): 100}))
    assert not {r.constraint for r in trace.binding} & {
        "link_xy",
        "link_yx",
        "link_yz",
        "link_zy",
    }


def test_binding_tolerance_is_a_parameter() -> None:
    data = f.solver_input(channels=[f.channel("C1", capacity=53)])
    x = {pair(data, "M1", "C1"): 50}
    assert "cap" not in {r.constraint for r in build_trace(data, Solution(x=x)).binding}
    loose = build_trace(data, Solution(x=x), tolerance=3)
    assert "cap" in {r.constraint for r in loose.binding}


def test_line_lists_its_instances_with_slack() -> None:
    data = f.solver_input(channels=[f.channel("C1", capacity=50)])
    trace = build_trace(data, Solution(x={pair(data, "M1", "C1"): 50}))
    (line,) = trace.lines
    assert line.quantity == 50
    cap = next(r for r in line.binding if r.constraint == "cap")
    assert (cap.instance, cap.slack) == ("cap[C1]", 0.0)
    assert trace.lines_per_rule["cap"] == 1
    assert trace.line(line.line) is line


def test_unknown_line_is_an_error() -> None:
    data = f.solver_input()
    with pytest.raises(KeyError, match="no allocation line"):
        build_trace(data, Solution(x={})).line("nope")


def test_lines_with_zero_units_are_not_traced() -> None:
    data = f.solver_input(channels=[f.channel("C1"), f.channel("C2")])
    trace = build_trace(data, Solution(x={pair(data, "M1", "C1"): 60, pair(data, "M1", "C2"): 0}))
    assert [line.channel for line in trace.lines] == ["C1"]


def test_empty_plan_has_an_empty_trace() -> None:
    trace = build_trace(f.solver_input(), Solution(x={}))
    assert (trace.lines, trace.binding, trace.lines_per_rule) == ((), (), {})


def test_blocked_channels_carry_their_elimination_reason() -> None:
    data = f.solver_input(
        materials=[f.material("M1", brand="Atelier Sable", tier="luxury")],
        channels=[f.channel("C1"), f.channel("C2", allowed=frozenset({"mass"}))],
        demands=[f.demand("M1", "C1")],
    )
    trace = build_trace(data, Solution(x={pair(data, "M1", "C1"): 60}))
    (line,) = trace.lines
    assert line.blocked == (BlockedChannel("C2", ("TIER",)),)


def test_trace_is_deterministic() -> None:
    data = _group_data()
    x = {pair(data, "M1", "C1"): 100}
    assert build_trace(data, Solution(x=x)) == build_trace(data, Solution(x=x))


def test_trace_of_a_solved_plan_matches_the_plan() -> None:
    data = f.solver_input(
        materials=[f.material("M1"), f.material("M2")],
        lots=[f.lot("M1"), f.lot("M2", qty=300)],
        channels=[f.channel("C1", capacity=120), f.channel("C2", capacity=80)],
        demands=[f.demand(m, c) for m in ("M1", "M2") for c in ("C1", "C2")],
    )
    result = PulpSolver().solve(data)
    assert result.status == "optimal"
    trace = build_trace(data, Solution(result.x, result.y, result.z))
    assert {(line.line, line.quantity) for line in trace.lines} == {
        (f"{'/'.join(p[0])},{p[1]}", qty) for p, qty in result.x.items() if qty > 0
    }
    assert trace.lines_per_rule  # some rule limits this plan
    assert set(trace.lines_per_rule) <= set(TRACED_RULES)
    assert all(rule.slack <= 1e-6 for line in trace.lines for rule in line.binding)
