"""Stock view: totals reconcile with the lots and with the plan, endpoints filter and report errors."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from reshelf.api import create_app
from reshelf.stock import StockLot, filter_lots, stock_summary

SPEC = {"name": "stock", "base": "default", "n_skus": 20, "n_channels": 5, "time_limit_s": 30}


@pytest.fixture(scope="module")
def client() -> Iterator[TestClient]:
    with TestClient(create_app("sqlite://")) as c:
        yield c


@pytest.fixture(scope="module")
def scenario_id(client: TestClient) -> int:
    sid = client.post("/scenarios", json=SPEC).json()["id"]
    assert client.post(f"/scenarios/{sid}/solve").status_code == 200
    return int(sid)


def lot(**kw: object) -> StockLot:
    base: dict[str, object] = dict(
        lot="M1/P1/2027-03", material="M1", description="d", brand="B1", category="Skincare",
        tier="premium", plant="P1", reason="near_expiry", expiry_date="2027-03-31",
        days_to_expiry=100, units=10, unit_cost=2.0, value_at_risk=20.0, allocated_units=4,
        channels_open=2, channels_blocked=1,
    )  # fmt: skip
    return StockLot.model_validate({**base, **kw})


def test_summary_buckets_add_up_to_the_totals() -> None:
    lots = [
        lot(),
        lot(lot="M2/P1/2027-04", material="M2", brand="B2", reason="excess", units=5, value_at_risk=10.0, allocated_units=0),
        lot(lot="M3/P1/2027-05", material="M3", category="Makeup", units=1, value_at_risk=2.0, allocated_units=1),
    ]  # fmt: skip
    s = stock_summary(lots)
    assert (s.total_lots, s.total_units, s.value_at_risk, s.allocated_units) == (3, 16, 32.0, 5)
    for buckets in (s.by_reason, s.by_brand, s.by_brand_category):
        assert sum(b.units for b in buckets) == s.total_units
        assert sum(b.value_at_risk for b in buckets) == pytest.approx(s.value_at_risk)
    assert s.by_reason[0].key == "near_expiry"  # largest value at risk first


def test_filter_lots_combines_filters() -> None:
    lots = [lot(), lot(brand="B2"), lot(category="Makeup")]
    assert len(filter_lots(lots, brand="B1")) == 2
    assert len(filter_lots(lots, brand="B1", category="Skincare")) == 1
    assert len(filter_lots(lots)) == 3


def test_result_stock_reconciles_with_the_plan(client: TestClient, scenario_id: int) -> None:
    result = client.get(f"/scenarios/{scenario_id}/results").json()["result"]
    planned = sum(line["quantity"] for line in result["lines"])
    assert (
        result["stock"]["summary"]["allocated_units"]
        == planned
        == result["optimizer"]["units_allocated"]
    )
    for row in result["stock"]["lots"]:
        assert 0 <= row["allocated_units"] <= row["units"]
        assert row["value_at_risk"] == pytest.approx(row["units"] * row["unit_cost"], abs=0.01)


def test_stock_endpoints(client: TestClient, scenario_id: int) -> None:
    summary = client.get("/stock/summary", params={"scenario_id": scenario_id}).json()
    lots = client.get("/stock/lots", params={"scenario_id": scenario_id}).json()
    assert summary["total_lots"] == len(lots) > 0
    brand = lots[0]["brand"]
    only = client.get("/stock/lots", params={"scenario_id": scenario_id, "brand": brand}).json()
    assert only and all(r["brand"] == brand for r in only)


def test_stock_errors_are_sentences(client: TestClient) -> None:
    missing = client.get("/stock/summary", params={"scenario_id": 999})
    assert missing.status_code == 404 and "999" in missing.json()["detail"]
    unsolved = client.post("/scenarios", json=SPEC).json()["id"]
    r = client.get("/stock/lots", params={"scenario_id": unsolved})
    assert r.status_code == 404 and "Solve it first" in r.json()["detail"]
