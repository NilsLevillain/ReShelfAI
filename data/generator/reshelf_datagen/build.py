"""Build the source tables (SAP style) for one scenario. Pure function of the scenario config.

Each section draws from its own random stream, so a change in one section never shifts another.
Every value comes from the scenario yaml and is an illustrative default (clean room rule).
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import unicodedata
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np

Row = dict[str, Any]
Tables = dict[str, list[Row]]

TABLE_COLUMNS: dict[str, list[str]] = {
    "MARA": ["MATNR", "MTART", "MATKL", "MHDHB", "MHDRZ", "ZZBRAND", "ZZTIER"],
    "MAKT": ["MATNR", "SPRAS", "MAKTX"],
    "T023": ["MATKL", "WGBEZ"],
    "T001W": ["WERKS", "NAME1", "LAND1", "ZZREGION", "ZZPTYPE"],
    "MARC": ["MATNR", "WERKS", "MMSTA"],
    "MARD": ["MATNR", "WERKS", "LGORT", "LABST"],
    "MCHB": ["MATNR", "WERKS", "LGORT", "CHARG", "CLABS", "HSDAT", "VFDAT", "ZZREASON"],
    "MBEW": ["MATNR", "BWKEY", "STPRS"],
    "ZABC": ["MATNR", "ABCCLASS", "RANK"],
    "ZCHANNEL": [
        "CHANNEL",
        "CTYPE",
        "LAND1",
        "LAT",
        "LON",
        "CAPUNITS",
        "MAXSKU",
        "MINRSL",
        "RECFACT",
    ],
    "ZCHANNEL_RULE": ["CHANNEL", "TIER", "ALLOWED", "BRANDPEN"],
    "ZCHANNEL_ASRT": ["CHANNEL", "ZZBRAND", "MATKL", "MAXSKU", "MAXUNITS"],
    "ZSELLIN": ["MATNR", "CHANNEL", "SHIPDATE", "QTY", "QTYTRANSIT"],
    "ZSELLOUT": ["MATNR", "CHANNEL", "PERIOD", "QTY"],
    "ZPARAM": ["PARAM", "VALUE", "UNIT", "NOTE"],
}

TIERS = ["luxury", "premium", "mass"]
DAYS_PER_MONTH = 30.4375

# Name parts per category. Accents are folded when `generator.accents` is false.
PRODUCT_NAMES: dict[str, list[str]] = {
    "Fragrance": ["Eau de Parfum", "Eau de Toilette", "Extrait", "Body Mist", "Cologne"],
    "Skincare": ["Crème Visage", "Sérum", "Lotion Tonique", "Baume Nuit", "Gel Nettoyant"],
    "Makeup": ["Rouge à Lèvres", "Fond de Teint", "Mascara", "Fard à Joues", "Vernis"],
    "Haircare": ["Shampoo", "Conditioner", "Hair Mask", "Scalp Serum", "Styling Cream"],
}
VARIANTS = [
    "Nuit Dorée",
    "Éclat",
    "Ambre",
    "Fleur d'Oranger",
    "Bois Noir",
    "Brume Légère",
    "Velours",
    "Lumière",
    "Cèdre",
    "Rose Poudrée",
    "Pivoine",
    "Océan",
    "Soie",
    "Citron Vert",
    "Santal",
    "Aurore",
]
SIZES = ["15 ml", "30 ml", "50 ml", "100 ml", "250 ml", "400 ml"]


def _fold(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def _apportion(shares: list[float], total: int) -> list[int]:
    """Largest remainder apportionment so counts sum exactly to `total`."""
    raw = [s * total for s in shares]
    counts = [math.floor(r) for r in raw]
    order = sorted(range(len(shares)), key=lambda i: (counts[i] - raw[i], i))
    for i in order[: total - sum(counts)]:
        counts[i] += 1
    return counts


def _last_months(as_of: date, n: int) -> list[tuple[int, int]]:
    year, month = as_of.year, as_of.month
    out: list[tuple[int, int]] = []
    for _ in range(n):
        month -= 1
        if month == 0:
            year, month = year - 1, 12
        out.append((year, month))
    return out[::-1]


def _rng(seed: int, stream: int) -> np.random.Generator:
    return np.random.default_rng([seed, stream])


def _category_code(category: str) -> str:
    return category[:4].upper()


def _materials(cfg: dict[str, Any]) -> list[Row]:
    g = cfg["generator"]
    rng = _rng(cfg["seed"], 0)
    n: int = g["n_skus"]
    brands: list[dict[str, Any]] = g["brands"]
    counts = _apportion([b["sku_share"] for b in brands], n)
    brand_idx = rng.permutation(np.repeat(np.arange(len(brands)), counts))
    volume = np.maximum(
        500, np.rint(g["volume_median"] * np.exp(g["volume_sigma"] * rng.standard_normal(n)))
    ).astype(int)
    is_new = np.zeros(n, dtype=bool)
    is_new[rng.choice(n, round(n * g["new_share"]), replace=False)] = True

    abc = np.array(["NEW"] * n, dtype=object)
    rank = np.zeros(n, dtype=int)
    known = [i for i in np.argsort(-volume, kind="stable") if not is_new[i]]
    total = float(sum(volume[i] for i in known))
    cum = 0.0
    for position, i in enumerate(known, start=1):
        share_before = cum / total
        abc[i] = (
            "A" if share_before < g["abc_cut_a"] else "B" if share_before < g["abc_cut_b"] else "C"
        )
        rank[i] = position
        cum += float(volume[i])

    cost_noise = rng.standard_normal(n)
    name_draw = rng.integers(0, 1_000_000, size=(n, 3))
    rows: list[Row] = []
    for i in range(n):
        brand = brands[int(brand_idx[i])]
        names = PRODUCT_NAMES[brand["category"]]
        description = (
            f"{brand['name']} {VARIANTS[name_draw[i, 0] % len(VARIANTS)]} "
            f"{names[name_draw[i, 1] % len(names)]} {SIZES[name_draw[i, 2] % len(SIZES)]}"
        )
        rows.append(
            {
                "matnr": str(100001 + i).zfill(18),
                "description": description if g["accents"] else _fold(description),
                "brand": brand["name"],
                "category": brand["category"],
                "tier": brand["tier"],
                "shelf_life_months": brand["shelf_life_months"],
                "volume": int(volume[i]),
                "abc": str(abc[i]),
                "rank": int(rank[i]),
                "unit_cost": round(
                    max(
                        0.5,
                        brand["unit_cost_median"] * math.exp(g["unit_cost_sigma"] * cost_noise[i]),
                    ),
                    2,
                ),
            }
        )
    return rows


def _lots(cfg: dict[str, Any], materials: list[Row]) -> tuple[list[Row], list[Row]]:
    """Return batch rows (MCHB shaped, plus plant and material keys) and plant rows."""
    g = cfg["generator"]
    rng = _rng(cfg["seed"], 2)
    as_of: date = cfg["as_of"]
    plants: list[dict[str, Any]] = g["plants"]
    plant_p = np.array([p["weight"] for p in plants], dtype=float)
    plant_p /= plant_p.sum()
    reasons: dict[str, dict[str, Any]] = g["reasons"]
    reason_names = list(reasons)
    step: int = g["lot_qty_step"]
    min_cases = math.ceil(g["min_lot_qty"] / step)
    batches: list[Row] = []
    seq = 0
    for mat in materials:
        if mat["abc"] == "NEW":
            weights = np.array([g["new_reasons"].get(r, 0.0) for r in reason_names])
        else:
            weights = np.array(
                [
                    reasons[r]["share"]
                    * (1.0 if mat["abc"] in reasons[r]["prefer_abc"] else g["off_class_weight"])
                    for r in reason_names
                ]
            )
        weights = weights / weights.sum()
        shelf_days = round(mat["shelf_life_months"] * DAYS_PER_MONTH)
        for _ in range(int(rng.integers(g["lots_per_sku"][0], g["lots_per_sku"][1] + 1))):
            reason = reason_names[int(rng.choice(len(reason_names), p=weights))]
            spec = reasons[reason]
            plant = plants[int(rng.choice(len(plants), p=plant_p))]
            lo, hi = spec["rsl_range"]
            rsl = lo + (hi - lo) * float(rng.beta(*spec["rsl_beta"]))
            cases = max(
                min_cases,
                round(
                    mat["volume"]
                    * spec["qty_factor"]
                    * math.exp(0.4 * float(rng.standard_normal()))
                    / step
                ),
            )
            lot_expiry = as_of + timedelta(days=round(rsl * shelf_days))
            n_batches = min(
                int(rng.integers(g["batches_per_lot"][0], g["batches_per_lot"][1] + 1)), cases
            )
            split = rng.multinomial(cases, rng.dirichlet(np.ones(n_batches)))
            jitter_cap = max(0, int((0.995 - rsl) * shelf_days))
            for batch_cases in split:
                if batch_cases == 0:
                    continue
                expiry = lot_expiry + timedelta(days=int(rng.integers(0, min(20, jitter_cap) + 1)))
                seq += 1
                batches.append(
                    {
                        "matnr": mat["matnr"],
                        "werks": plant["code"],
                        "lgort": "FG01" if plant["kind"] == "factory" else "DC01",
                        "charg": f"B{expiry:%y%m}{seq:05d}",
                        "clabs": int(batch_cases) * step,
                        "hsdat": expiry - timedelta(days=shelf_days),
                        "vfdat": expiry,
                        "reason": reason,
                    }
                )
    return batches, plants


def _sell_history(
    cfg: dict[str, Any], materials: list[Row], channels: list[dict[str, Any]]
) -> tuple[list[Row], list[Row]]:
    g = cfg["generator"]
    rng = _rng(cfg["seed"], 1)
    as_of: date = cfg["as_of"]
    months = _last_months(as_of, 12)
    profiles = {c: np.array(v, dtype=float) / np.mean(v) for c, v in g["seasonality"].items()}
    types = g["channel_types"]
    carry = np.array([types[c["type"]]["carry_prob"] for c in channels])
    weight = np.array([types[c["type"]]["demand_weight"] * c["market_weight"] for c in channels])
    nc = len(channels)
    sellout: list[Row] = []
    sellin: list[Row] = []
    for mat in materials:
        if mat["abc"] == "NEW":
            continue
        p = np.minimum(0.95, carry * g["abc_carry_multiplier"][mat["abc"]])
        carries = rng.random(nc) < p
        base = mat["volume"] * g["second_life_share"] * weight / 12.0
        season = np.array([profiles[mat["category"]][m - 1] for _, m in months])
        noise = np.exp(g["seasonality_noise_sigma"] * rng.standard_normal((nc, 12)))
        qty = np.rint(base[:, None] * season[None, :] * noise).astype(int)
        for c in np.flatnonzero(carries):
            q = qty[c]
            if q.sum() == 0:
                continue
            code = channels[c]["code"]
            for (year, month), value in zip(months, q, strict=True):
                if value > 0:
                    sellout.append(
                        {
                            "matnr": mat["matnr"],
                            "channel": code,
                            "period": f"{year}{month:02d}",
                            "qty": int(value),
                        }
                    )
            for quarter in range(4):
                year, month = months[3 * quarter]
                shipped = round(
                    float(q[3 * quarter : 3 * quarter + 3].sum())
                    * float(rng.uniform(*g["sellin_noise"]))
                )
                if shipped > 0:
                    sellin.append(
                        {
                            "matnr": mat["matnr"],
                            "channel": code,
                            "shipdate": date(year, month, 15),
                            "qty": shipped,
                            "qtytransit": 0,
                        }
                    )
            if rng.random() < 0.3:
                days_ago = int(rng.integers(3, 46))
                shipped = max(1, round(float(q.mean()) * float(rng.uniform(0.5, 1.5))))
                sellin.append(
                    {
                        "matnr": mat["matnr"],
                        "channel": code,
                        "shipdate": as_of - timedelta(days=days_ago),
                        "qty": shipped,
                        "qtytransit": shipped if days_ago < g["transit_days"] else 0,
                    }
                )
    return sellout, sellin


def _flatten(prefix: str, value: Any) -> list[tuple[str, str]]:
    if isinstance(value, dict):
        out: list[tuple[str, str]] = []
        for key, sub in value.items():
            out.extend(_flatten(f"{prefix}_{key}".upper(), sub))
        return out
    if isinstance(value, list):
        return [(prefix, ",".join(str(v) for v in value))]
    return [(prefix, str(value))]


def _unit(param: str) -> str:
    if param.endswith("_DAYS"):
        return "days"
    if param.endswith("_UNITS"):
        return "units"
    if param.endswith("_S"):
        return "s"
    return ""


def generate(cfg: dict[str, Any]) -> Tables:
    """Return the source tables as lists of rows keyed by SAP style column names."""
    g = cfg["generator"]
    mats = _materials(cfg)
    batches, plants = _lots(cfg, mats)
    by_matnr = {m["matnr"]: m for m in mats}

    total_units = sum(b["clabs"] for b in batches)
    types = g["channel_types"]
    weight_sum: dict[str, float] = {}
    for ch in g["channels"]:
        weight_sum[ch["type"]] = weight_sum.get(ch["type"], 0.0) + ch["market_weight"]
    channel_rows: list[Row] = []
    capacity: dict[str, int] = {}
    for ch in g["channels"]:
        spec = types[ch["type"]]
        cap = round(
            g["total_capacity_ratio"]
            * total_units
            * spec["capacity_share"]
            * ch["market_weight"]
            / weight_sum[ch["type"]]
        )
        capacity[ch["code"]] = cap
        channel_rows.append(
            {
                "CHANNEL": ch["code"],
                "CTYPE": ch["type"],
                "LAND1": ch["country"],
                "LAT": ch["lat"],
                "LON": ch["lon"],
                "CAPUNITS": cap,
                "MAXSKU": spec["max_skus"],
                "MINRSL": spec["min_rsl_pct"],
                "RECFACT": spec["recovery_factor"],
            }
        )

    sellout, sellin = _sell_history(cfg, mats, g["channels"])

    rules = cfg["rules"]
    rule_rows = [
        {
            "CHANNEL": ch["code"],
            "TIER": tier,
            "ALLOWED": "X" if tier in rules["allowed_tiers"][ch["type"]] else "",
            "BRANDPEN": rules["brand_penalty"][ch["type"]][tier],
        }
        for ch in g["channels"]
        for tier in TIERS
    ]
    asrt_rows = [
        {
            "CHANNEL": ch["code"],
            "ZZBRAND": brand["name"],
            "MATKL": _category_code(brand["category"]),
            "MAXSKU": max(1, math.ceil(g["group_sku_share"] * types[ch["type"]]["max_skus"])),
            "MAXUNITS": round(g["group_units_share"] * capacity[ch["code"]]),
        }
        for ch in g["channels"]
        for brand in g["brands"]
    ]

    stock: dict[tuple[str, str], int] = {}
    discontinued: set[tuple[str, str]] = set()
    lgort: dict[tuple[str, str], str] = {}
    for b in batches:
        key = (b["matnr"], b["werks"])
        stock[key] = stock.get(key, 0) + b["clabs"]
        lgort[key] = b["lgort"]
        if b["reason"] == "discontinued":
            discontinued.add(key)

    cost_rng = _rng(cfg["seed"], 3)
    plant_factor = {k: round(float(cost_rng.uniform(0.97, 1.03)), 4) for k in sorted(stock)}

    param_rows = [
        {"PARAM": name, "VALUE": value, "UNIT": _unit(name), "NOTE": "illustrative default"}
        for name, value in _flatten("", cfg["params"])
    ]
    for row in param_rows:
        row["PARAM"] = row["PARAM"].lstrip("_")

    return {
        "MARA": [
            {
                "MATNR": m["matnr"],
                "MTART": "FERT",
                "MATKL": _category_code(m["category"]),
                "MHDHB": m["shelf_life_months"],
                "MHDRZ": 25,
                "ZZBRAND": m["brand"],
                "ZZTIER": m["tier"],
            }
            for m in mats
        ],
        "MAKT": [{"MATNR": m["matnr"], "SPRAS": "E", "MAKTX": m["description"]} for m in mats],
        "T023": [
            {"MATKL": code, "WGBEZ": name}
            for code, name in sorted(
                {(_category_code(b["category"]), b["category"]) for b in g["brands"]}
            )
        ],
        "T001W": [
            {
                "WERKS": p["code"],
                "NAME1": p["name"],
                "LAND1": p["country"],
                "ZZREGION": p["region"],
                "ZZPTYPE": p["kind"],
            }
            for p in plants
        ],
        "MARC": [
            {"MATNR": k[0], "WERKS": k[1], "MMSTA": "Z1" if k in discontinued else ""}
            for k in sorted(stock)
        ],
        "MARD": [
            {"MATNR": k[0], "WERKS": k[1], "LGORT": lgort[k], "LABST": stock[k]}
            for k in sorted(stock)
        ],
        "MCHB": [
            {
                "MATNR": b["matnr"],
                "WERKS": b["werks"],
                "LGORT": b["lgort"],
                "CHARG": b["charg"],
                "CLABS": b["clabs"],
                "HSDAT": b["hsdat"],
                "VFDAT": b["vfdat"],
                "ZZREASON": b["reason"],
            }
            for b in batches
        ],
        "MBEW": [
            {
                "MATNR": k[0],
                "BWKEY": k[1],
                "STPRS": round(by_matnr[k[0]]["unit_cost"] * plant_factor[k], 2),
            }
            for k in sorted(stock)
        ],
        "ZABC": [
            {"MATNR": m["matnr"], "ABCCLASS": m["abc"], "RANK": m["rank"]}
            for m in mats
            if m["abc"] != "NEW"
        ],
        "ZCHANNEL": channel_rows,
        "ZCHANNEL_RULE": rule_rows,
        "ZCHANNEL_ASRT": asrt_rows,
        "ZSELLIN": [
            {
                "MATNR": s["matnr"],
                "CHANNEL": s["channel"],
                "SHIPDATE": s["shipdate"],
                "QTY": s["qty"],
                "QTYTRANSIT": s["qtytransit"],
            }
            for s in sellin
        ],
        "ZSELLOUT": [
            {"MATNR": s["matnr"], "CHANNEL": s["channel"], "PERIOD": s["period"], "QTY": s["qty"]}
            for s in sellout
        ],
        "ZPARAM": param_rows,
    }


def _format(value: Any) -> str:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float):
        return f"{value:.6f}".rstrip("0").rstrip(".")
    return str(value)


def write_tables(tables: Tables, cfg: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    """Write one CSV per table plus a manifest with row counts and SHA 256 hashes."""
    out_dir.mkdir(parents=True, exist_ok=True)
    hashes: dict[str, str] = {}
    counts: dict[str, int] = {}
    for table, columns in TABLE_COLUMNS.items():
        path = out_dir / f"{table}.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(columns)
            for row in tables[table]:
                writer.writerow([_format(row[c]) for c in columns])
        hashes[table] = hashlib.sha256(path.read_bytes()).hexdigest()
        counts[table] = len(tables[table])
    manifest = {
        "scenario": cfg["name"],
        "seed": cfg["seed"],
        "as_of": cfg["as_of"].isoformat(),
        "rows": counts,
        "sha256": hashes,
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest
