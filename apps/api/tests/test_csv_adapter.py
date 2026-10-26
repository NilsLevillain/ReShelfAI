"""CsvAdapter and canonical schema (TS-008 to TS-013, TS-201 to TS-203, TS-207 data side)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from conftest import Row, read_table
from pydantic import ValidationError

from reshelf.adapters import CsvAdapter, DatasetError, SourceAdapter
from reshelf.schema import TIERS, CanonicalDataset, Params

Edit = Callable[..., Path]


@pytest.fixture(scope="module")
def dataset(source_dir: Path) -> CanonicalDataset:
    adapter: SourceAdapter = CsvAdapter(source_dir)
    return adapter.load()


# TS-008 happy path


def test_load_returns_canonical_dataset(dataset: CanonicalDataset, source_dir: Path) -> None:
    assert isinstance(dataset, CanonicalDataset)
    assert len(dataset.materials) == 200
    assert len(dataset.channels) == 20
    assert len(dataset.plants) == 6
    assert len(dataset.rules) == 20
    assert dataset.as_of.isoformat() == "2026-10-01"


def test_material_ids_have_no_leading_zeros(dataset: CanonicalDataset) -> None:
    assert all(not m.material.startswith("0") for m in dataset.materials)
    assert {a.material for a in dataset.abc} <= {m.material for m in dataset.materials}


def test_category_uses_the_group_description(dataset: CanonicalDataset) -> None:
    assert {m.category for m in dataset.materials} == {
        "Fragrance",
        "Skincare",
        "Makeup",
        "Haircare",
    }


def test_lots_sum_batches_and_keep_earliest_expiry(
    dataset: CanonicalDataset, source_dir: Path
) -> None:
    _, batches = read_table(source_dir, "MCHB")
    total = sum(int(b["CLABS"]) for b in batches if int(b["CLABS"]) > 0)
    assert sum(lot.qty for lot in dataset.lots) == total
    assert len({lot.key for lot in dataset.lots}) == len(dataset.lots)
    earliest: dict[tuple[str, str, str], str] = {}
    for b in batches:
        key = (b["MATNR"].lstrip("0"), b["WERKS"], b["VFDAT"][:7])
        earliest[key] = min(earliest.get(key, b["VFDAT"]), b["VFDAT"])
    assert all(lot.expiry_date.isoformat() == earliest[lot.key] for lot in dataset.lots)


def test_unit_cost_comes_from_the_standard_price(
    dataset: CanonicalDataset, source_dir: Path
) -> None:
    _, prices = read_table(source_dir, "MBEW")
    price = {(p["MATNR"].lstrip("0"), p["BWKEY"]): float(p["STPRS"]) for p in prices}
    assert all(lot.unit_cost == price[(lot.material, lot.plant)] for lot in dataset.lots)


def test_channels_carry_transit_time(dataset: CanonicalDataset) -> None:
    transit = {c.type: c.transit_days for c in dataset.channels}
    assert transit["clearance_web"] < transit["liquidation"]


def test_rules_hold_allowed_tiers_and_penalties(dataset: CanonicalDataset) -> None:
    rules = {r.channel: r for r in dataset.rules}
    assert "luxury" in rules["CLR_DE"].allowed_tiers
    assert "luxury" not in rules["NGO_ES"].allowed_tiers
    assert rules["CLR_DE"].brand_penalty["luxury"] == 6.0
    assert set(rules["OUT_PL"].brand_penalty) == set(TIERS)


def test_push_quantity_depends_on_category(dataset: CanonicalDataset) -> None:
    push = dataset.params.push_quantity_units
    assert push["Fragrance"] == 5
    assert push["Haircare"] == 50
    assert push["Makeup"] == 30


def test_demand_has_history_flag_and_seasonality_mean_one(dataset: CanonicalDataset) -> None:
    with_history = [d for d in dataset.demand if d.has_history]
    assert with_history
    for d in with_history[:200]:
        assert d.daily_demand > 0
        assert sum(d.seasonality) / 12 == pytest.approx(1.0)
    assert all(d.seasonality == [1.0] * 12 for d in dataset.demand if d.daily_demand == 0)


def test_daily_demand_is_a_year_of_sellout_over_365(
    dataset: CanonicalDataset, source_dir: Path
) -> None:
    _, sellout = read_table(source_dir, "ZSELLOUT")
    first = sellout[0]
    key = (first["MATNR"].lstrip("0"), first["CHANNEL"])
    year = sum(int(r["QTY"]) for r in sellout if (r["MATNR"].lstrip("0"), r["CHANNEL"]) == key)
    demand = next(d for d in dataset.demand if (d.material, d.channel) == key)
    assert demand.daily_demand == pytest.approx(year / 365)


def test_in_transit_is_not_counted_as_channel_stock(
    dataset: CanonicalDataset, source_dir: Path
) -> None:
    _, sellin = read_table(source_dir, "ZSELLIN")
    transit = sum(int(r["QTYTRANSIT"]) for r in sellin)
    assert transit > 0
    assert sum(d.in_transit for d in dataset.demand) == transit


# TS-009 to TS-012 rejections


def test_negative_quantity_is_rejected(edit_source: Edit) -> None:
    def change(rows: list[Row]) -> list[Row]:
        rows[0]["CLABS"] = "-5"
        return rows

    with pytest.raises(DatasetError, match="MCHB"):
        CsvAdapter(edit_source("MCHB", change)).load()


def test_unknown_tier_is_rejected(edit_source: Edit) -> None:
    def change(rows: list[Row]) -> list[Row]:
        rows[0]["ZZTIER"] = "ultra"
        return rows

    with pytest.raises(DatasetError, match="MARA"):
        CsvAdapter(edit_source("MARA", change)).load()


def test_percent_above_100_is_rejected(edit_source: Edit) -> None:
    def change(rows: list[Row]) -> list[Row]:
        rows[0]["MINRSL"] = "150"
        return rows

    with pytest.raises(DatasetError, match="ZCHANNEL"):
        CsvAdapter(edit_source("ZCHANNEL", change)).load()


def test_missing_table_is_rejected(edit_source: Edit) -> None:
    folder = edit_source()
    (folder / "ZCHANNEL.csv").unlink()
    with pytest.raises(DatasetError, match="ZCHANNEL"):
        CsvAdapter(folder).load()


def test_missing_folder_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(DatasetError, match="does not exist"):
        CsvAdapter(tmp_path / "nope").load()


def test_missing_standard_price_rejects_the_dataset(edit_source: Edit) -> None:
    with pytest.raises(DatasetError, match="standard price"):
        CsvAdapter(edit_source("MBEW", lambda rows: rows[1:])).load()


def test_stock_ledger_mismatch_is_rejected(edit_source: Edit) -> None:
    def change(rows: list[Row]) -> list[Row]:
        rows[0]["LABST"] = str(int(rows[0]["LABST"]) + 1)
        return rows

    with pytest.raises(DatasetError, match="LABST"):
        CsvAdapter(edit_source("MARD", change)).load()


def test_lot_for_unknown_plant_is_rejected(edit_source: Edit) -> None:
    with pytest.raises(DatasetError, match="unknown plant"):
        CsvAdapter(edit_source("T001W", lambda rows: rows[1:])).load()


def test_missing_as_of_is_rejected(edit_source: Edit) -> None:
    with pytest.raises(DatasetError, match="AS_OF"):
        CsvAdapter(
            edit_source("ZPARAM", lambda rows: [r for r in rows if r["PARAM"] != "AS_OF"])
        ).load()


def test_unknown_push_category_is_rejected(edit_source: Edit) -> None:
    def change(rows: list[Row]) -> list[Row]:
        rows.append({"PARAM": "PUSH_QUANTITY_UNITS_TOYS", "VALUE": "5", "UNIT": "", "NOTE": "x"})
        return rows

    with pytest.raises(DatasetError, match="TOYS"):
        CsvAdapter(edit_source("ZPARAM", change)).load()


def test_header_only_tables_give_an_empty_dataset(edit_source: Edit) -> None:
    folder = edit_source()
    for table in ("MCHB", "MARD", "MBEW", "ZSELLIN", "ZSELLOUT"):
        header, _ = read_table(folder, table)
        (folder / f"{table}.csv").write_text(",".join(header) + "\n", encoding="utf-8")
    loaded = CsvAdapter(folder).load()
    assert loaded.lots == []
    assert loaded.demand == []
    assert loaded.materials


# TS-207 parameter validation


def _params(**changes: object) -> Params:
    base: dict[str, object] = {
        "score_base": {"A": 1.0, "B": 0.7, "C": 0.4, "NEW": 0.55},
        "score_rank_weight": 0.25,
        "epsilon": 0.01,
        "coverage_days": 90,
        "coverage_alpha": 0.5,
        "push_quantity_units": {"Fragrance": 5},
        "solver_time_limit_s": 60,
        "counterfactual_time_limit_s": 10,
        "planner_rules": ["rsl", "tier", "capacity"],
    }
    return Params.model_validate(base | changes)


def test_valid_params_pass() -> None:
    assert _params().epsilon == 0.01


@pytest.mark.parametrize(
    "changes",
    [
        {"coverage_days": -1},
        {"coverage_alpha": 1.5},
        {"epsilon": -0.1},
        {"push_quantity_units": {"Fragrance": -5}},
        {"score_base": {"A": 1.0, "B": 0.7, "C": 0.4}},
        {"score_base": {"A": 1.0, "B": 0.7, "C": 0.4, "NEW": 0.5, "X": 0.1}},
        {"planner_rules": ["rsl", "coverage_magic"]},
        {"solver_time_limit_s": 0},
    ],
)
def test_invalid_params_are_rejected(changes: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        _params(**changes)
