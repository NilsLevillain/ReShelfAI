"""Distribution, integrity and reproducibility tests for the seeded generator (RS-012, RS-013).

Ranges are design tolerances written from the scenario intent, not read off one output.
"""

from __future__ import annotations

import copy
import itertools
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from reshelf_datagen import generate, load_scenario, write_tables
from reshelf_datagen.build import Tables, _materials

SCENARIOS = Path(__file__).resolve().parents[2] / "scenarios"


@pytest.fixture(scope="module")
def cfg() -> dict[str, Any]:
    return load_scenario(SCENARIOS / "default.yaml")


@pytest.fixture(scope="module")
def tables(cfg: dict[str, Any]) -> Tables:
    return generate(cfg)


def small(cfg: dict[str, Any], n: int = 200, seed: int | None = None) -> dict[str, Any]:
    out = copy.deepcopy(cfg)
    out["generator"]["n_skus"] = n
    if seed is not None:
        out["seed"] = seed
    return out


def rsl(row: dict[str, Any], as_of: date) -> float:
    return float((row["VFDAT"] - as_of).days / (row["VFDAT"] - row["HSDAT"]).days)


# Reproducibility (TS-001)


def test_same_seed_gives_identical_hashes(cfg: dict[str, Any], tmp_path: Path) -> None:
    small_cfg = small(cfg)
    first = write_tables(generate(small_cfg), small_cfg, tmp_path / "a")
    second = write_tables(generate(small_cfg), small_cfg, tmp_path / "b")
    assert first == second
    assert (tmp_path / "a" / "manifest.json").read_bytes() == (
        tmp_path / "b" / "manifest.json"
    ).read_bytes()


def test_different_seed_changes_output(cfg: dict[str, Any], tmp_path: Path) -> None:
    a = write_tables(generate(small(cfg, seed=1)), small(cfg, seed=1), tmp_path / "a")
    b = write_tables(generate(small(cfg, seed=2)), small(cfg, seed=2), tmp_path / "b")
    assert a["sha256"]["MCHB"] != b["sha256"]["MCHB"]


def test_n_skus_parameter_sets_material_count(cfg: dict[str, Any]) -> None:
    assert len(generate(small(cfg, 120))["MARA"]) == 120


def test_manifest_has_no_timestamp_or_machine_suffix(cfg: dict[str, Any], tmp_path: Path) -> None:
    small_cfg = small(cfg)
    write_tables(generate(small_cfg), small_cfg, tmp_path)
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert set(manifest) == {"as_of", "rows", "scenario", "seed", "sha256"}


# Distributions (FR-01)


def test_tier_mix_follows_brand_shares(tables: Tables) -> None:
    counts = Counter(r["ZZTIER"] for r in tables["MARA"])
    assert counts == {"luxury": 240, "premium": 880, "mass": 880}


def test_five_brands_in_four_categories(tables: Tables) -> None:
    assert len({r["ZZBRAND"] for r in tables["MARA"]}) == 5
    assert {r["WGBEZ"] for r in tables["T023"]} == {"Fragrance", "Skincare", "Makeup", "Haircare"}


def test_abc_pareto_skew(cfg: dict[str, Any]) -> None:
    mats = _materials(cfg)
    known = [m for m in mats if m["abc"] != "NEW"]
    a = [m for m in known if m["abc"] == "A"]
    total = sum(m["volume"] for m in known)
    assert 0.08 <= len(a) / len(known) <= 0.25
    assert 0.78 <= sum(m["volume"] for m in a) / total <= 0.86
    assert {m["abc"] for m in known} == {"A", "B", "C"}


def test_new_materials_have_no_abc_row_and_no_history(tables: Tables) -> None:
    n = len(tables["MARA"])
    with_abc = {r["MATNR"] for r in tables["ZABC"]}
    new = {r["MATNR"] for r in tables["MARA"]} - with_abc
    assert len(new) == round(n * 0.06)
    assert not new & {r["MATNR"] for r in tables["ZSELLOUT"]}
    assert new & {r["MATNR"] for r in tables["MARC"]}, "NEW materials still carry stock"


def test_abc_rank_is_unique_and_follows_volume(cfg: dict[str, Any]) -> None:
    known = [m for m in _materials(cfg) if m["abc"] != "NEW"]
    ranks = sorted(m["rank"] for m in known)
    assert ranks == list(range(1, len(known) + 1))
    by_rank = sorted(known, key=lambda m: m["rank"])
    assert all(x["volume"] >= y["volume"] for x, y in itertools.pairwise(by_rank))


def test_all_five_stock_reasons_present(tables: Tables) -> None:
    reasons = Counter(r["ZZREASON"] for r in tables["MCHB"])
    assert set(reasons) == {"near_expiry", "excess", "obsolete", "discontinued", "overproduction"}
    total = sum(reasons.values())
    assert all(count / total >= 0.05 for count in reasons.values())
    assert 0.25 <= reasons["near_expiry"] / total <= 0.45


def test_aging_histogram_shape(tables: Tables, cfg: dict[str, Any]) -> None:
    as_of = cfg["as_of"]
    values = [rsl(r, as_of) for r in tables["MCHB"]]
    assert all(0.0 < v < 1.0 for v in values)
    under_quarter = sum(v < 0.25 for v in values) / len(values)
    over_85 = sum(v > 0.85 for v in values) / len(values)
    assert 0.25 <= under_quarter <= 0.50, "a visible tail of stock near expiry"
    assert 0.05 <= over_85 <= 0.30, "a visible block of fresh overproduction"
    middle = sum(0.25 <= v <= 0.85 for v in values) / len(values)
    assert middle >= 0.30


def test_remaining_shelf_life_ordering_by_reason(tables: Tables, cfg: dict[str, Any]) -> None:
    by_reason: dict[str, list[float]] = defaultdict(list)
    for r in tables["MCHB"]:
        by_reason[r["ZZREASON"]].append(rsl(r, cfg["as_of"]))
    mean = {k: sum(v) / len(v) for k, v in by_reason.items()}
    assert mean["near_expiry"] < mean["obsolete"] < mean["excess"]
    assert mean["overproduction"] == max(mean.values())


def test_seasonality_peaks_for_fragrance_in_winter(tables: Tables) -> None:
    category = {r["MATNR"]: r["MATKL"] for r in tables["MARA"]}
    month_total: dict[str, int] = defaultdict(int)
    for r in tables["ZSELLOUT"]:
        if category[r["MATNR"]] == "FRAG":
            month_total[r["PERIOD"][4:]] += r["QTY"]
    winter = (month_total["11"] + month_total["12"]) / 2
    summer = (month_total["06"] + month_total["07"]) / 2
    assert winter >= 1.5 * summer


def test_haircare_is_flat(tables: Tables) -> None:
    category = {r["MATNR"]: r["MATKL"] for r in tables["MARA"]}
    month_total: dict[str, int] = defaultdict(int)
    for r in tables["ZSELLOUT"]:
        if category[r["MATNR"]] == "HAIR":
            month_total[r["PERIOD"][4:]] += r["QTY"]
    assert max(month_total.values()) <= 1.25 * min(month_total.values())


def test_sell_out_across_many_countries(tables: Tables) -> None:
    country = {r["CHANNEL"]: r["LAND1"] for r in tables["ZCHANNEL"]}
    assert len(tables["ZCHANNEL"]) == 20
    assert len(set(country.values())) >= 12
    sold_in = {country[r["CHANNEL"]] for r in tables["ZSELLOUT"]}
    assert sold_in == set(country.values())
    assert {r["CTYPE"] for r in tables["ZCHANNEL"]} == {
        "outlet",
        "friends_family",
        "clearance_web",
        "ngo_donation",
        "liquidation",
    }


def test_sell_out_covers_twelve_closed_periods(tables: Tables) -> None:
    periods = sorted({r["PERIOD"] for r in tables["ZSELLOUT"]})
    assert periods[0] == "202510"
    assert periods[-1] == "202609"
    assert len(periods) == 12


def test_some_sell_in_is_in_transit(tables: Tables) -> None:
    in_transit = [r for r in tables["ZSELLIN"] if r["QTYTRANSIT"] > 0]
    assert 0 < len(in_transit) < 0.2 * len(tables["ZSELLIN"])
    assert all(r["QTYTRANSIT"] == r["QTY"] for r in in_transit)


# Plants and stock integrity


def test_stock_sits_in_factories_and_distribution_centers(tables: Tables) -> None:
    kinds = Counter(r["ZZPTYPE"] for r in tables["T001W"])
    assert kinds == {"factory": 3, "dc": 3}
    stocked = {r["WERKS"] for r in tables["MARD"]}
    assert stocked == {r["WERKS"] for r in tables["T001W"]}


def test_storage_stock_reconciles_with_batch_stock(tables: Tables) -> None:
    batch_sum: dict[tuple[str, str], int] = defaultdict(int)
    for r in tables["MCHB"]:
        batch_sum[(r["MATNR"], r["WERKS"])] += r["CLABS"]
    assert {(r["MATNR"], r["WERKS"]): r["LABST"] for r in tables["MARD"]} == dict(batch_sum)


def test_referential_integrity(tables: Tables, cfg: dict[str, Any]) -> None:
    matnrs = {r["MATNR"] for r in tables["MARA"]}
    assert {r["MATNR"] for r in tables["MCHB"]} <= matnrs
    assert {(r["MATNR"], r["WERKS"]) for r in tables["MARC"]} == {
        (r["MATNR"], r["BWKEY"]) for r in tables["MBEW"]
    }
    assert {r["CHANNEL"] for r in tables["ZSELLIN"]} <= {r["CHANNEL"] for r in tables["ZCHANNEL"]}
    assert all(r["STPRS"] > 0 for r in tables["MBEW"])


def test_batches_are_live_and_quantities_positive(tables: Tables, cfg: dict[str, Any]) -> None:
    for r in tables["MCHB"]:
        assert r["HSDAT"] < cfg["as_of"] < r["VFDAT"]
        assert r["CLABS"] > 0
    assert len({r["CHARG"] for r in tables["MCHB"]}) == len(tables["MCHB"])


def test_discontinued_status_matches_batch_reason(tables: Tables) -> None:
    flagged = {(r["MATNR"], r["WERKS"]) for r in tables["MARC"] if r["MMSTA"] == "Z1"}
    from_batches = {
        (r["MATNR"], r["WERKS"]) for r in tables["MCHB"] if r["ZZREASON"] == "discontinued"
    }
    assert flagged == from_batches


def test_descriptions_keep_accents_when_enabled_and_fold_when_not(cfg: dict[str, Any]) -> None:
    with_accents = generate(small(cfg, 300))
    assert any(not r["MAKTX"].isascii() for r in with_accents["MAKT"])
    plain = small(cfg, 300)
    plain["generator"]["accents"] = False
    assert all(r["MAKTX"].isascii() for r in generate(plain)["MAKT"])


# Channels, rules and limits


def test_capacity_follows_total_ratio(tables: Tables, cfg: dict[str, Any]) -> None:
    total_units = sum(r["CLABS"] for r in tables["MCHB"])
    capacity = sum(r["CAPUNITS"] for r in tables["ZCHANNEL"])
    assert capacity == pytest.approx(
        cfg["generator"]["total_capacity_ratio"] * total_units, rel=0.001
    )


def test_group_limits_cover_every_channel_and_brand(tables: Tables) -> None:
    assert len(tables["ZCHANNEL_ASRT"]) == 20 * 5
    capacity = {r["CHANNEL"]: r["CAPUNITS"] for r in tables["ZCHANNEL"]}
    max_sku = {r["CHANNEL"]: r["MAXSKU"] for r in tables["ZCHANNEL"]}
    for r in tables["ZCHANNEL_ASRT"]:
        assert 1 <= r["MAXSKU"] <= max_sku[r["CHANNEL"]]
        assert 0 < r["MAXUNITS"] <= capacity[r["CHANNEL"]]


def test_default_rules_allow_luxury_in_clearance_but_not_donation(tables: Tables) -> None:
    allowed = {(r["CHANNEL"][:3], r["TIER"]): r["ALLOWED"] for r in tables["ZCHANNEL_RULE"]}
    assert allowed[("CLR", "luxury")] == "X"
    assert allowed[("NGO", "luxury")] == ""
    assert allowed[("LIQ", "luxury")] == ""
    assert allowed[("OUT", "mass")] == "X"


def test_every_parameter_is_tagged_illustrative(tables: Tables) -> None:
    assert tables["ZPARAM"]
    assert all(r["NOTE"] == "illustrative default" for r in tables["ZPARAM"])
    names = {r["PARAM"] for r in tables["ZPARAM"]}
    assert {"SCORE_BASE_A", "SCORE_BASE_NEW", "EPSILON", "COVERAGE_DAYS", "PLANNER_RULES"} <= names


# Scenarios


def test_luxury_protection_changes_only_the_rule(cfg: dict[str, Any]) -> None:
    base = generate(cfg)
    protected = generate(load_scenario(SCENARIOS / "luxury_protection.yaml"))
    for table in (
        "MARA",
        "MCHB",
        "MBEW",
        "ZSELLOUT",
        "ZSELLIN",
        "ZCHANNEL",
        "ZCHANNEL_ASRT",
        "ZPARAM",
    ):
        assert base[table] == protected[table], table
    changed = [
        (b["CHANNEL"], b["TIER"])
        for b, p in zip(base["ZCHANNEL_RULE"], protected["ZCHANNEL_RULE"], strict=True)
        if b != p
    ]
    assert changed
    assert all(channel.startswith("CLR") and tier == "luxury" for channel, tier in changed)
