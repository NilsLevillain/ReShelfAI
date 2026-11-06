"""Globe data: points per plant and channel, arcs that add up to the plan."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from reshelf.api import create_app
from reshelf.geo import COUNTRY_CENTRE

SPEC = {"name": "geo", "base": "default", "n_skus": 20, "n_channels": 5, "time_limit_s": 30}


@pytest.fixture(scope="module")
def result() -> Iterator[dict]:  # type: ignore[type-arg]
    with TestClient(create_app("sqlite://")) as c:
        sid = c.post("/scenarios", json=SPEC).json()["id"]
        assert c.post(f"/scenarios/{sid}/solve").status_code == 200
        yield c.get(f"/scenarios/{sid}/results").json()["result"]


def test_every_point_has_a_valid_position(result: dict) -> None:  # type: ignore[type-arg]
    geo = result["geo"]
    assert geo["plants"] and geo["channels"]
    for p in geo["plants"] + geo["channels"]:
        assert -90 <= p["lat"] <= 90
        assert -180 <= p["lon"] <= 180


def test_plant_risk_and_arcs_reconcile_with_stock_and_plan(result: dict) -> None:  # type: ignore[type-arg]
    geo = result["geo"]
    assert sum(p["value_at_risk"] for p in geo["plants"]) == pytest.approx(
        result["stock"]["summary"]["value_at_risk"], abs=0.5
    )
    sent = sum(a["units"] for a in geo["arcs"])
    assert sent == sum(c["allocated_units"] for c in geo["channels"])
    assert sent == sum(p["allocated_units"] for p in geo["plants"])
    assert sent == result["stock"]["summary"]["allocated_units"]


def test_arcs_join_known_points(result: dict) -> None:  # type: ignore[type-arg]
    geo = result["geo"]
    plants = {p["plant"] for p in geo["plants"]}
    channels = {c["channel"] for c in geo["channels"]}
    assert all(a["plant"] in plants and a["channel"] in channels for a in geo["arcs"])


def test_demo_plant_countries_are_in_the_table() -> None:
    assert {"PL", "MX", "CN", "NL", "US", "SG"} <= set(COUNTRY_CENTRE)
