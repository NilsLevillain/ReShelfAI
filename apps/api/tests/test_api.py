"""Scenario API: create, solve, results, compare, explain, counterfactual and the error sentences."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from reshelf.api import create_app

SPEC = {"name": "unit", "base": "default", "n_skus": 20, "n_channels": 5, "time_limit_s": 30}


@pytest.fixture(scope="module")
def client() -> Iterator[TestClient]:
    with TestClient(create_app("sqlite://")) as c:
        yield c


@pytest.fixture(scope="module")
def solved(client: TestClient) -> dict[str, object]:
    scenario = client.post("/scenarios", json=SPEC)
    assert scenario.status_code == 201
    response = client.post(f"/scenarios/{scenario.json()['id']}/solve")
    assert response.status_code == 200
    return {"scenario_id": scenario.json()["id"], **response.json()}


def test_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_solve_returns_solver_fields_and_lines(solved: dict[str, object]) -> None:
    result = solved["result"]
    assert isinstance(result, dict)
    assert result["solve"]["status"] == "optimal"
    assert result["solve"]["time_limit_s"] == 30
    assert result["label"] == "Simulated data"
    assert result["lines"]


def test_results_returns_what_solve_stored(client: TestClient, solved: dict[str, object]) -> None:
    again = client.get(f"/scenarios/{solved['scenario_id']}/results").json()
    assert again["result_id"] == solved["result_id"]
    assert again["result"] == solved["result"]


def test_explain_returns_the_rule_trace_of_a_line(
    client: TestClient, solved: dict[str, object]
) -> None:
    line = solved["result"]["lines"][0]["line"]  # type: ignore[index]
    response = client.get(f"/results/{solved['result_id']}/lines/{line}/explain")
    assert response.status_code == 200
    assert response.json()["line"] == line


def test_counterfactual_relaxes_a_binding_rule(
    client: TestClient, solved: dict[str, object]
) -> None:
    traces = solved["result"]["trace"]["lines"]  # type: ignore[index]
    item = next(t for t in traces if any(b["constraint"] != "supply" for b in t["binding"]))
    rule = next(b for b in item["binding"] if b["constraint"] != "supply")
    response = client.post(
        f"/results/{solved['result_id']}/lines/{item['line']}/counterfactual",
        json={"instance": rule["instance"], "mode": "off"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["instance"] == rule["instance"]
    assert body["cost_eur"] >= 0


def test_counterfactual_rejects_a_rule_that_does_not_bind_the_line(
    client: TestClient, solved: dict[str, object]
) -> None:
    line = solved["result"]["lines"][0]["line"]  # type: ignore[index]
    response = client.post(
        f"/results/{solved['result_id']}/lines/{line}/counterfactual",
        json={"instance": "cap[NOPE]"},
    )
    assert response.status_code == 422
    assert "does not bind" in response.json()["detail"]


def test_compare_two_scenarios(client: TestClient, solved: dict[str, object]) -> None:
    other = client.post(
        "/scenarios", json={**SPEC, "name": "tight", "params": {"coverage_days": 30}}
    )
    assert other.status_code == 201
    assert client.post(f"/scenarios/{other.json()['id']}/solve").status_code == 200
    response = client.get(f"/scenarios/compare?ids={solved['scenario_id']},{other.json()['id']}")
    assert response.status_code == 200
    rows = response.json()["rows"]
    assert [r["name"] for r in rows] == ["unit", "tight"]
    assert rows[0]["value_delta_vs_first"] == 0
    assert "greedy baseline" in response.json()["comparison"]


@pytest.mark.parametrize(
    ("method", "path", "payload", "status", "text"),
    [
        ("get", "/scenarios/999/results", None, 404, "No scenario with id 999"),
        ("post", "/scenarios/999/solve", None, 404, "No scenario with id 999"),
        ("get", "/results/999/lines/x/explain", None, 404, "No result with id 999"),
        ("post", "/scenarios", {**SPEC, "base": "nope"}, 404, "Unknown base scenario"),
        ("post", "/scenarios", {**SPEC, "params": {"bogus": 1}}, 422, "Unknown parameter"),
        ("post", "/scenarios", {**SPEC, "n_skus": 0}, 422, None),
        ("get", "/scenarios/compare?ids=1", None, 422, "at least two"),
        ("get", "/scenarios/compare?ids=a,b", None, 422, "whole numbers"),
    ],
)
def test_errors_are_plain_sentences(
    client: TestClient, method: str, path: str, payload: object, status: int, text: str | None
) -> None:
    response = getattr(client, method)(path, **({"json": payload} if payload else {}))
    assert response.status_code == status
    if text:
        assert text in response.json()["detail"]


def test_scenario_without_result_says_to_solve_first(client: TestClient) -> None:
    created = client.post("/scenarios", json=SPEC).json()
    response = client.get(f"/scenarios/{created['id']}/results")
    assert response.status_code == 404
    assert "Solve it first" in response.json()["detail"]
