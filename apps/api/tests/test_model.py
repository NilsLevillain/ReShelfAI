"""The model is built from the registry and keeps its row labels."""

from __future__ import annotations

import factory as f

from reshelf.constraints import CONSTRAINT_LABELS, CONSTRAINTS, Solution, evaluate
from reshelf.model import BUILDERS, build_model
from reshelf.schema import GroupLimit


def test_every_registry_constraint_has_a_builder() -> None:  # TS-040
    assert set(BUILDERS) == {c.name for c in CONSTRAINTS}
    assert len(CONSTRAINT_LABELS) == len(BUILDERS)


def test_model_rows_use_the_labels_the_checker_reports() -> None:
    data = f.solver_input(
        materials=[f.material("M1"), f.material("M2", category="Fragrance")],
        lots=[f.lot("M1"), f.lot("M2")],
        demands=[f.demand("M1", "C1"), f.demand("M2", "C1", history=False)],  # M2 is NEW: push
        group_limits=[
            GroupLimit(
                channel="C1", brand="Brightleaf", category="Haircare", max_skus=3, max_units=500
            )
        ],
    )
    model = build_model(data)
    checker = {r.instance for r in evaluate(data, Solution(x={}))}
    assert set(model.rows) == checker
    assert {label.split("[")[0] for label in model.rows} == {c.name for c in CONSTRAINTS}


def test_only_admissible_pairs_become_variables() -> None:
    data = f.solver_input(
        channels=[f.channel("C1"), f.channel("C2", allowed=frozenset({"luxury"}))]
    )
    model = build_model(data)
    assert set(model.x) == set(model.y) == set(data.admissible)
    assert {c for (_, c) in model.x} == {"C1"}
    assert set(model.z) == set(data.lots_of)
