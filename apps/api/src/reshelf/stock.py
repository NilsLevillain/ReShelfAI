"""Stock view: lots at risk, split by reason and by brand and category, with what the plan sends out.

Built from the same `SolverInput` and plan as the rest of the result, so the stock screens never
read a different source than the results screens (ADR 008). Value at risk is units times unit cost.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date

from pydantic import BaseModel

from reshelf.ids import LotKey, Pair, lot_label
from reshelf.solver_input import SolverInput


class StockLot(BaseModel):
    lot: str
    material: str
    description: str
    brand: str
    category: str
    tier: str
    plant: str
    reason: str
    expiry_date: date
    days_to_expiry: int
    units: int
    unit_cost: float
    value_at_risk: float
    allocated_units: int
    channels_open: int
    channels_blocked: int


class StockBucket(BaseModel):
    key: str
    lots: int
    units: int
    value_at_risk: float
    allocated_units: int


class StockBrandCategory(StockBucket):
    brand: str
    category: str


class StockSummary(BaseModel):
    total_lots: int
    total_units: int
    value_at_risk: float
    allocated_units: int
    by_reason: list[StockBucket]
    by_brand: list[StockBucket]
    by_brand_category: list[StockBrandCategory]


class StockOut(BaseModel):
    summary: StockSummary
    lots: list[StockLot]


def stock_lots(data: SolverInput, x: dict[Pair, int]) -> list[StockLot]:
    allocated: dict[LotKey, int] = defaultdict(int)
    for (lot_key, _), units in x.items():
        allocated[lot_key] += units
    open_n: dict[LotKey, int] = defaultdict(int)
    for lot_key, _ in data.admissible:
        open_n[lot_key] += 1
    blocked_n: dict[LotKey, int] = defaultdict(int)
    for lot_key, _ in data.dropped:
        blocked_n[lot_key] += 1

    rows = []
    for key, lot in sorted(data.lots.items()):
        material = data.materials[lot.material]
        rows.append(
            StockLot(
                lot=lot_label(key),
                material=lot.material,
                description=material.description,
                brand=material.brand,
                category=material.category,
                tier=material.tier,
                plant=lot.plant,
                reason=lot.stock_reason,
                expiry_date=lot.expiry_date,
                days_to_expiry=(lot.expiry_date - data.as_of).days,
                units=lot.qty,
                unit_cost=lot.unit_cost,
                value_at_risk=round(lot.qty * lot.unit_cost, 2),
                allocated_units=allocated[key],
                channels_open=open_n[key],
                channels_blocked=blocked_n[key],
            )
        )
    return rows


def _bucket(key: str, rows: list[StockLot]) -> StockBucket:
    return StockBucket(
        key=key,
        lots=len(rows),
        units=sum(r.units for r in rows),
        value_at_risk=round(sum(r.value_at_risk for r in rows), 2),
        allocated_units=sum(r.allocated_units for r in rows),
    )


def stock_summary(lots: list[StockLot]) -> StockSummary:
    by_reason: dict[str, list[StockLot]] = defaultdict(list)
    by_brand: dict[str, list[StockLot]] = defaultdict(list)
    by_pair: dict[tuple[str, str], list[StockLot]] = defaultdict(list)
    for r in lots:
        by_reason[r.reason].append(r)
        by_brand[r.brand].append(r)
        by_pair[(r.brand, r.category)].append(r)
    total = _bucket("all", lots)
    return StockSummary(
        total_lots=total.lots,
        total_units=total.units,
        value_at_risk=total.value_at_risk,
        allocated_units=total.allocated_units,
        by_reason=sorted(
            (_bucket(k, v) for k, v in by_reason.items()), key=lambda b: -b.value_at_risk
        ),
        by_brand=sorted(
            (_bucket(k, v) for k, v in by_brand.items()), key=lambda b: -b.value_at_risk
        ),
        by_brand_category=[
            StockBrandCategory(**_bucket(f"{b}/{c}", v).model_dump(), brand=b, category=c)
            for (b, c), v in sorted(by_pair.items())
        ],
    )


def stock_out(data: SolverInput, x: dict[Pair, int]) -> StockOut:
    lots = stock_lots(data, x)
    return StockOut(summary=stock_summary(lots), lots=lots)


def filter_lots(
    lots: list[StockLot],
    brand: str | None = None,
    category: str | None = None,
    reason: str | None = None,
) -> list[StockLot]:
    return [
        r
        for r in lots
        if (brand is None or r.brand == brand)
        and (category is None or r.category == category)
        and (reason is None or r.reason == reason)
    ]
