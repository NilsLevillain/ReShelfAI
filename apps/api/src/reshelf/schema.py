"""Canonical dataset: the only input the solver sees.

Source tables (SAP style) are mapped to these entities by a `SourceAdapter`. Every default and
rule value is an invented illustrative default and lives in `Params` or the scenario yaml.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Tier = Literal["luxury", "premium", "mass"]
ChannelType = Literal["outlet", "friends_family", "clearance_web", "ngo_donation", "liquidation"]
PlantKind = Literal["factory", "dc"]
Region = Literal["europe", "north_america", "asia_pacific"]
StockReason = Literal["near_expiry", "excess", "obsolete", "discontinued", "overproduction"]
AbcClass = Literal["A", "B", "C", "NEW"]
PlannerRule = Literal["rsl", "tier", "capacity"]

TIERS: tuple[Tier, ...] = ("luxury", "premium", "mass")
ABC_CLASSES: tuple[AbcClass, ...] = ("A", "B", "C", "NEW")

NonNegInt = Annotated[int, Field(ge=0)]
NonNegFloat = Annotated[float, Field(ge=0)]
Share = Annotated[float, Field(ge=0, le=1)]
Percent = Annotated[float, Field(ge=0, le=100)]


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Material(_Frozen):
    material: str
    description: str
    category: str
    brand: str
    tier: Tier
    shelf_life_months: Annotated[int, Field(gt=0)]


class Plant(_Frozen):
    plant: str
    name: str
    country: str
    region: Region
    kind: PlantKind


class Lot(_Frozen):
    """The decision index: one material in one plant with one expiry month."""

    material: str
    plant: str
    expiry_bucket: Annotated[str, Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")]
    expiry_date: date
    qty: Annotated[int, Field(gt=0)]
    unit_cost: NonNegFloat
    stock_reason: StockReason

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.material, self.plant, self.expiry_bucket)


class Channel(_Frozen):
    channel: str
    type: ChannelType
    country: str
    lat: float
    lon: float
    capacity_units: NonNegInt
    max_skus: NonNegInt
    transit_days: NonNegInt


class ChannelRule(_Frozen):
    channel: str
    min_rsl_pct: Percent
    allowed_tiers: frozenset[Tier]
    recovery_factor: Share
    brand_penalty: dict[Tier, NonNegFloat]


class GroupLimit(_Frozen):
    """Limits for one brand in one category inside one channel (rules asrt and asrt_units)."""

    channel: str
    brand: str
    category: str
    max_skus: NonNegInt
    max_units: NonNegInt


class Demand(_Frozen):
    """Sales view of one material in one channel.

    `has_history` is false when the channel never sold the material. Past sales cannot forecast
    such a pair, so it is classed NEW.
    """

    material: str
    channel: str
    daily_demand: NonNegFloat
    seasonality: Annotated[list[NonNegFloat], Field(min_length=12, max_length=12)]
    channel_stock: NonNegInt
    in_transit: NonNegInt
    has_history: bool


class Abc(_Frozen):
    material: str
    abc_class: Literal["A", "B", "C"]
    rank: Annotated[int, Field(gt=0)]


class Params(_Frozen):
    """Scenario parameters (ZPARAM). Validated before any solve."""

    score_base: dict[AbcClass, NonNegFloat]
    score_rank_weight: NonNegFloat
    epsilon: Share
    coverage_days: NonNegFloat
    coverage_alpha: Share
    push_quantity_units: dict[str, NonNegInt]
    solver_time_limit_s: Annotated[float, Field(gt=0)]
    counterfactual_time_limit_s: Annotated[float, Field(gt=0)]
    planner_rules: list[PlannerRule]

    @field_validator("score_base")
    @classmethod
    def _all_classes(cls, value: dict[AbcClass, float]) -> dict[AbcClass, float]:
        missing = set(ABC_CLASSES) - set(value)
        if missing:
            raise ValueError(f"score_base is missing classes {sorted(missing)}")
        return value


class CanonicalDataset(_Frozen):
    as_of: date
    params: Params
    materials: list[Material]
    plants: list[Plant]
    lots: list[Lot]
    channels: list[Channel]
    rules: list[ChannelRule]
    group_limits: list[GroupLimit]
    demand: list[Demand]
    abc: list[Abc]

    @model_validator(mode="after")
    def _references_exist(self) -> CanonicalDataset:
        materials = {m.material for m in self.materials}
        plants = {p.plant for p in self.plants}
        channels = {c.channel for c in self.channels}
        problems: list[str] = []
        problems += [
            f"lot references unknown material {lot.material}"
            for lot in self.lots
            if lot.material not in materials
        ]
        problems += [
            f"lot references unknown plant {lot.plant}"
            for lot in self.lots
            if lot.plant not in plants
        ]
        problems += [
            f"rule references unknown channel {r.channel}"
            for r in self.rules
            if r.channel not in channels
        ]
        problems += [
            f"group limit references unknown channel {g.channel}"
            for g in self.group_limits
            if g.channel not in channels
        ]
        problems += [
            f"demand references unknown pair {d.material} / {d.channel}"
            for d in self.demand
            if d.material not in materials or d.channel not in channels
        ]
        problems += [
            f"abc references unknown material {a.material}"
            for a in self.abc
            if a.material not in materials
        ]
        problems += [
            f"channel {c} has no rule" for c in sorted(channels - {r.channel for r in self.rules})
        ]
        if problems:
            raise ValueError("; ".join(problems[:10]))
        return self
