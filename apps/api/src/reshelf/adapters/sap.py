"""Map validated SAP style source tables to the canonical dataset (see docs/mapping.md).

This is the only module that knows SAP table and field names.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from typing import Any

import pandas as pd
import pandera.errors
from pydantic import ValidationError

from reshelf.adapters.base import DatasetError
from reshelf.adapters.source_schemas import SOURCE_SCHEMAS
from reshelf.schema import (
    CanonicalDataset,
    ChannelRule,
    Demand,
    Lot,
    Params,
)

DAYS_PER_YEAR = 365
SCORE_CLASSES = ("A", "B", "C", "NEW")


def _material_id(raw: str) -> str:
    return raw.lstrip("0").upper()


def _rows(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return [{str(k): v for k, v in row.items()} for row in frame.to_dict("records")]


def validate_frames(frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Check every source table against its schema. Missing tables or columns are errors."""
    out: dict[str, pd.DataFrame] = {}
    for name, schema in SOURCE_SCHEMAS.items():
        if name not in frames:
            raise DatasetError(f"source table {name} is missing")
        try:
            out[name] = schema.validate(frames[name], lazy=True)
        except pandera.errors.SchemaErrors as err:
            cases = err.failure_cases.head(5).to_dict("records")
            raise DatasetError(f"table {name} is invalid: {cases}") from err
    return out


def _params(zparam: pd.DataFrame, categories: dict[str, str]) -> tuple[date, Params]:
    raw = dict(zip(zparam["PARAM"], zparam["VALUE"], strict=True))
    if "AS_OF" not in raw:
        raise DatasetError("parameter AS_OF is missing in ZPARAM")
    try:
        as_of = date.fromisoformat(raw["AS_OF"])
    except ValueError as err:
        raise DatasetError(f"parameter AS_OF is not a date: {raw['AS_OF']}") from err

    by_upper = {name.upper(): name for name in categories.values()}
    push: dict[str, int] = {}
    prefix = "PUSH_QUANTITY_UNITS_"
    for key, value in raw.items():
        if key.startswith(prefix):
            category = by_upper.get(key.removeprefix(prefix))
            if category is None:
                raise DatasetError(f"parameter {key} names an unknown category")
            push[category] = int(value)
    try:
        params = Params.model_validate(
            {
                "score_base": {
                    c: raw[f"SCORE_BASE_{c}"] for c in SCORE_CLASSES if f"SCORE_BASE_{c}" in raw
                },
                "score_rank_weight": raw["SCORE_RANK_WEIGHT"],
                "epsilon": raw["EPSILON"],
                "coverage_days": raw["COVERAGE_DAYS"],
                "coverage_alpha": raw["COVERAGE_ALPHA"],
                "push_quantity_units": push,
                "solver_time_limit_s": raw["SOLVER_TIME_LIMIT_S"],
                "counterfactual_time_limit_s": raw["COUNTERFACTUAL_TIME_LIMIT_S"],
                "planner_rules": [r for r in raw.get("PLANNER_RULES", "").split(",") if r],
            }
        )
    except KeyError as err:
        raise DatasetError(f"parameter {err.args[0]} is missing in ZPARAM") from err
    except ValidationError as err:
        raise DatasetError(f"ZPARAM is invalid: {err}") from err
    return as_of, params


def _last_closed_periods(as_of: date, n: int = 12) -> list[str]:
    year, month = as_of.year, as_of.month
    out: list[str] = []
    for _ in range(n):
        month -= 1
        if month == 0:
            year, month = year - 1, 12
        out.append(f"{year}{month:02d}")
    return out


def _lots(mchb: pd.DataFrame, mbew: pd.DataFrame, mard: pd.DataFrame) -> list[Lot]:
    batches = mchb.assign(MATNR=mchb["MATNR"].map(_material_id))
    stock = mard.assign(MATNR=mard["MATNR"].map(_material_id))

    on_batches = batches.groupby(["MATNR", "WERKS", "LGORT"])["CLABS"].sum()
    on_ledger = stock.groupby(["MATNR", "WERKS", "LGORT"])["LABST"].sum()
    gap = on_batches.sub(on_ledger, fill_value=0)
    if (gap != 0).any():
        first = gap[gap != 0].index[0]
        raise DatasetError(f"MARD.LABST differs from the sum of MCHB.CLABS for {first}")

    price_rows: dict[tuple[str, str], list[float]] = defaultdict(list)
    for r in _rows(mbew):
        price_rows[(_material_id(r["MATNR"]), r["BWKEY"])].append(r["STPRS"])
    prices = {key: sum(v) / len(v) for key, v in price_rows.items()}

    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in _rows(batches):
        if r["CLABS"] > 0:
            groups[(r["MATNR"], r["WERKS"], r["VFDAT"][:7])].append(r)

    lots: list[Lot] = []
    for (material, plant, bucket), rows in sorted(groups.items()):
        if (material, plant) not in prices:
            raise DatasetError(f"no standard price (MBEW) for material {material} in plant {plant}")
        by_reason: Counter[str] = Counter()
        for r in rows:
            by_reason[r["ZZREASON"]] += int(r["CLABS"])
        top_reason = sorted(by_reason.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        lots.append(
            Lot.model_validate(
                {
                    "material": material,
                    "plant": plant,
                    "expiry_bucket": bucket,
                    "expiry_date": date.fromisoformat(min(r["VFDAT"] for r in rows)),
                    "qty": sum(int(r["CLABS"]) for r in rows),
                    "unit_cost": prices[(material, plant)],
                    "stock_reason": top_reason,
                }
            )
        )
    return lots


def _demand(stock: pd.DataFrame, sellout: pd.DataFrame, as_of: date) -> list[Demand]:
    periods = set(_last_closed_periods(as_of))

    history: set[tuple[str, str]] = set()
    sold_total: dict[tuple[str, str], int] = defaultdict(int)
    recent: dict[tuple[str, str], list[float]] = defaultdict(lambda: [0.0] * 12)
    for m, c, period, qty in zip(
        sellout["MATNR"], sellout["CHANNEL"], sellout["PERIOD"], sellout["QTY"], strict=True
    ):
        key = (_material_id(m), c)
        sold_total[key] += int(qty)
        if qty > 0:
            history.add(key)
        if period in periods:
            recent[key][int(period[4:]) - 1] += float(qty)

    on_hand: dict[tuple[str, str], int] = defaultdict(int)
    transit: dict[tuple[str, str], int] = defaultdict(int)
    for r in _rows(stock):
        key = (_material_id(r["MATNR"]), r["CHANNEL"])
        on_hand[key] += int(r["QTYONHAND"])
        transit[key] += int(r["QTYTRANSIT"])

    out: list[Demand] = []
    for key in sorted(set(sold_total) | set(on_hand) | set(transit)):
        months = recent[key] if key in recent else [0.0] * 12
        total = sum(months)
        seasonality = [m / (total / 12) for m in months] if total > 0 else [1.0] * 12
        out.append(
            Demand(
                material=key[0],
                channel=key[1],
                daily_demand=total / DAYS_PER_YEAR,
                seasonality=seasonality,
                channel_stock=on_hand[key],
                in_transit=transit[key],
                has_history=key in history,
            )
        )
    return out


def _rules(zchannel: pd.DataFrame, zrule: pd.DataFrame) -> list[ChannelRule]:
    rules: list[ChannelRule] = []
    for r in _rows(zchannel):
        rows = zrule[zrule["CHANNEL"] == r["CHANNEL"]]
        rules.append(
            ChannelRule.model_validate(
                {
                    "channel": r["CHANNEL"],
                    "min_rsl_pct": r["MINRSL"],
                    "allowed_tiers": set(rows.loc[rows["ALLOWED"] == "X", "TIER"]),
                    "recovery_factor": r["RECFACT"],
                    "brand_penalty": dict(zip(rows["TIER"], rows["BRANDPEN"], strict=True)),
                }
            )
        )
    return rules


def build_dataset(raw_frames: dict[str, pd.DataFrame]) -> CanonicalDataset:
    f = validate_frames(raw_frames)
    categories = dict(zip(f["T023"]["MATKL"], f["T023"]["WGBEZ"], strict=True))
    as_of, params = _params(f["ZPARAM"], categories)

    names = {_material_id(r["MATNR"]): r["MAKTX"] for r in _rows(f["MAKT"]) if r["SPRAS"] == "E"}
    try:
        data: dict[str, Any] = {
            "as_of": as_of,
            "params": params,
            "materials": [
                {
                    "material": _material_id(r["MATNR"]),
                    "description": names.get(_material_id(r["MATNR"]), "").strip(),
                    "category": categories[r["MATKL"]],
                    "brand": r["ZZBRAND"],
                    "tier": r["ZZTIER"],
                    "shelf_life_months": r["MHDHB"],
                }
                for r in _rows(f["MARA"])
            ],
            "plants": [
                {
                    "plant": r["WERKS"],
                    "name": r["NAME1"].strip(),
                    "country": r["LAND1"],
                    "region": r["ZZREGION"],
                    "kind": r["ZZPTYPE"],
                }
                for r in _rows(f["T001W"])
            ],
            "lots": _lots(f["MCHB"], f["MBEW"], f["MARD"]),
            "channels": [
                {
                    "channel": r["CHANNEL"],
                    "type": r["CTYPE"],
                    "country": r["LAND1"],
                    "lat": r["LAT"],
                    "lon": r["LON"],
                    "capacity_units": r["CAPUNITS"],
                    "max_skus": r["MAXSKU"],
                    "transit_days": r["TRANSITD"],
                }
                for r in _rows(f["ZCHANNEL"])
            ],
            "rules": _rules(f["ZCHANNEL"], f["ZCHANNEL_RULE"]),
            "group_limits": [
                {
                    "channel": r["CHANNEL"],
                    "brand": r["ZZBRAND"],
                    "category": categories[r["MATKL"]],
                    "max_skus": r["MAXSKU"],
                    "max_units": r["MAXUNITS"],
                }
                for r in _rows(f["ZCHANNEL_ASRT"])
            ],
            "demand": _demand(f["ZCHSTOCK"], f["ZSELLOUT"], as_of),
            "abc": [
                {
                    "material": _material_id(r["MATNR"]),
                    "abc_class": r["ABCCLASS"],
                    "rank": r["RANK"],
                }
                for r in _rows(f["ZABC"])
            ],
        }
        return CanonicalDataset.model_validate(data)
    except KeyError as err:
        raise DatasetError(f"material group {err.args[0]} is missing in T023") from err
    except ValidationError as err:
        raise DatasetError(f"canonical dataset is invalid: {err}") from err
