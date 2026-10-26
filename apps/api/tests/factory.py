"""Small hand built datasets for unit tests. Every value is invented."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from reshelf.schema import (
    Abc,
    CanonicalDataset,
    Channel,
    ChannelRule,
    Demand,
    GroupLimit,
    Lot,
    Material,
    Params,
    Plant,
)
from reshelf.solver_input import SolverInput, build_solver_input

AS_OF = date(2026, 10, 1)
ALL_TIERS = frozenset({"luxury", "premium", "mass"})
FLAT = [1.0] * 12


def params(**changes: Any) -> Params:
    base: dict[str, Any] = {
        "score_base": {"A": 1.0, "B": 0.7, "C": 0.4, "NEW": 0.55},
        "score_rank_weight": 0.25,
        "epsilon": 0.01,
        "coverage_days": 90,
        "coverage_alpha": 0.5,
        "push_quantity_units": {"Fragrance": 5, "Haircare": 50},
        "solver_time_limit_s": 60,
        "counterfactual_time_limit_s": 10,
        "planner_rules": ["rsl", "tier", "capacity"],
    }
    return Params.model_validate(base | changes)


def material(
    code: str,
    category: str = "Haircare",
    brand: str = "Brightleaf",
    tier: str = "mass",
    shelf_life_months: int = 32,
) -> Material:
    return Material.model_validate(
        {
            "material": code,
            "description": code,
            "category": category,
            "brand": brand,
            "tier": tier,
            "shelf_life_months": shelf_life_months,
        }
    )


def lot(
    code: str,
    qty: int = 100,
    plant: str = "P1",
    expiry_in_days: int = 600,
    unit_cost: float = 10.0,
    bucket: str | None = None,
) -> Lot:
    expiry = AS_OF + timedelta(days=expiry_in_days)
    return Lot.model_validate(
        {
            "material": code,
            "plant": plant,
            "expiry_bucket": bucket or f"{expiry.year}-{expiry.month:02d}",
            "expiry_date": expiry,
            "qty": qty,
            "unit_cost": unit_cost,
            "stock_reason": "excess",
        }
    )


def channel(
    code: str,
    capacity: int = 10_000,
    max_skus: int = 100,
    transit_days: int = 10,
    type_: str = "outlet",
    min_rsl_pct: float = 0.0,
    allowed: frozenset[str] = ALL_TIERS,
    recovery: float = 0.5,
    penalty: dict[str, float] | None = None,
) -> tuple[Channel, ChannelRule]:
    return (
        Channel.model_validate(
            {
                "channel": code,
                "type": type_,
                "country": "FR",
                "lat": 0.0,
                "lon": 0.0,
                "capacity_units": capacity,
                "max_skus": max_skus,
                "transit_days": transit_days,
            }
        ),
        ChannelRule.model_validate(
            {
                "channel": code,
                "min_rsl_pct": min_rsl_pct,
                "allowed_tiers": allowed,
                "recovery_factor": recovery,
                "brand_penalty": penalty or {"luxury": 0.0, "premium": 0.0, "mass": 0.0},
            }
        ),
    )


def demand(
    code: str,
    channel_code: str,
    daily: float = 2.0,
    stock: int = 0,
    in_transit: int = 0,
    seasonality: list[float] | None = None,
    history: bool = True,
) -> Demand:
    return Demand.model_validate(
        {
            "material": code,
            "channel": channel_code,
            "daily_demand": daily,
            "seasonality": seasonality or FLAT,
            "channel_stock": stock,
            "in_transit": in_transit,
            "has_history": history,
        }
    )


def dataset(
    materials: list[Material] | None = None,
    lots: list[Lot] | None = None,
    channels: list[tuple[Channel, ChannelRule]] | None = None,
    demands: list[Demand] | None = None,
    abc: list[Abc] | None = None,
    group_limits: list[GroupLimit] | None = None,
    parameters: Params | None = None,
) -> CanonicalDataset:
    """Default world: one haircare SKU of class B with 100 units, one outlet that sells 2 a day."""
    materials = materials if materials is not None else [material("M1")]
    channels = channels if channels is not None else [channel("C1")]
    lots = lots if lots is not None else [lot("M1")]
    codes = {m.material for m in materials}
    if demands is None:
        demands = [demand(code, channels[0][0].channel) for code in sorted(codes)]
    if abc is None:
        abc = [
            Abc(material=code, abc_class="B", rank=i + 1) for i, code in enumerate(sorted(codes))
        ]
    return CanonicalDataset(
        as_of=AS_OF,
        params=parameters or params(),
        materials=materials,
        plants=[Plant(plant="P1", name="Plant", country="FR", region="europe", kind="dc")],
        lots=lots,
        channels=[c for c, _ in channels],
        rules=[r for _, r in channels],
        group_limits=group_limits or [],
        demand=demands,
        abc=abc,
    )


def solver_input(**kwargs: Any) -> SolverInput:
    return build_solver_input(dataset(**kwargs))
