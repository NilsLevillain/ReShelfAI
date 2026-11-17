"""Map data for the globe: plant points, channel points and plant to channel arcs.

Plants carry a country, not coordinates, so a plant sits at an approximate country centre. The
table is generic public geography. A plant in a country that is not listed is left off the globe
and still shows in the stock table.
"""

from __future__ import annotations

from collections import defaultdict

from pydantic import BaseModel

from reshelf.ids import Pair
from reshelf.kpis import unit_value
from reshelf.solver_input import SolverInput

# Approximate country centres (latitude, longitude).
COUNTRY_CENTRE: dict[str, tuple[float, float]] = {
    "PL": (52.0, 19.1), "MX": (23.6, -102.5), "CN": (35.9, 104.2), "NL": (52.1, 5.3),
    "US": (39.8, -98.6), "SG": (1.35, 103.8), "DE": (51.2, 10.4), "FR": (46.6, 2.2),
    "GB": (54.0, -2.0), "ES": (40.4, -3.7), "IT": (42.8, 12.6), "BR": (-14.2, -51.9),
    "IN": (21.0, 78.0), "JP": (36.2, 138.3), "AE": (24.0, 54.0), "ZA": (-29.0, 24.0),
    "KE": (0.2, 37.9), "TR": (39.0, 35.2), "AU": (-25.3, 133.8), "CA": (56.1, -106.3),
}  # fmt: skip


class GeoPlant(BaseModel):
    plant: str
    name: str
    country: str
    lat: float
    lon: float
    value_at_risk: float
    units: int
    allocated_units: int
    destroyed_units: int
    value_destroyed: float  # cost of the units the plan does not place


class GeoChannel(BaseModel):
    channel: str
    type: str
    country: str
    lat: float
    lon: float
    allocated_units: int
    value_recovered: float  # net value of what the plan sends to this channel


class GeoArc(BaseModel):
    plant: str
    channel: str
    units: int


class GeoCountry(BaseModel):
    """Everything the plan does in one country: stock held there and stock sent there."""

    country: str
    plants: list[str]
    channels: list[str]
    units: int
    value_at_risk: float
    allocated_units: int
    destroyed_units: int
    value_destroyed: float
    received_units: int
    value_recovered: float


class GeoOut(BaseModel):
    plants: list[GeoPlant]
    channels: list[GeoChannel]
    arcs: list[GeoArc]
    countries: list[GeoCountry]


def geo_out(data: SolverInput, x: dict[Pair, int]) -> GeoOut:
    risk: dict[str, float] = defaultdict(float)
    units: dict[str, int] = defaultdict(int)
    for lot in data.lots.values():
        risk[lot.plant] += lot.qty * lot.unit_cost
        units[lot.plant] += lot.qty
    arcs: dict[tuple[str, str], int] = defaultdict(int)
    sent: dict[str, int] = defaultdict(int)
    out: dict[str, int] = defaultdict(int)
    placed_cost: dict[str, float] = defaultdict(float)
    recovered: dict[str, float] = defaultdict(float)
    for pair, qty in x.items():
        if qty <= 0:
            continue
        lot_key, channel = pair
        plant = data.lots[lot_key].plant
        arcs[(plant, channel)] += qty
        sent[channel] += qty
        out[plant] += qty
        placed_cost[plant] += qty * data.lots[lot_key].unit_cost
        recovered[channel] += qty * unit_value(data, pair)

    plant_list = sorted(data.plants.values(), key=lambda p: p.plant)
    channel_list = sorted(data.channels.values(), key=lambda c: c.channel)
    plants = [
        GeoPlant(
            plant=p.plant,
            name=p.name,
            country=p.country,
            lat=COUNTRY_CENTRE[p.country][0],
            lon=COUNTRY_CENTRE[p.country][1],
            value_at_risk=round(risk[p.plant], 2),
            units=units[p.plant],
            allocated_units=out[p.plant],
            destroyed_units=units[p.plant] - out[p.plant],
            value_destroyed=round(risk[p.plant] - placed_cost[p.plant], 2),
        )
        for p in plant_list
        if p.country in COUNTRY_CENTRE
    ]
    channels = [
        GeoChannel(
            channel=c.channel,
            type=c.type,
            country=c.country,
            lat=c.lat,
            lon=c.lon,
            allocated_units=sent[c.channel],
            value_recovered=round(recovered[c.channel], 2),
        )
        for c in channel_list
    ]
    shown = {p.plant for p in plants}

    countries = [
        GeoCountry(
            country=code,
            plants=[p.plant for p in plant_list if p.country == code],
            channels=[c.channel for c in channel_list if c.country == code],
            units=sum(units[p.plant] for p in plant_list if p.country == code),
            value_at_risk=round(sum(risk[p.plant] for p in plant_list if p.country == code), 2),
            allocated_units=sum(out[p.plant] for p in plant_list if p.country == code),
            destroyed_units=sum(
                units[p.plant] - out[p.plant] for p in plant_list if p.country == code
            ),
            value_destroyed=round(
                sum(risk[p.plant] - placed_cost[p.plant] for p in plant_list if p.country == code),
                2,
            ),
            received_units=sum(sent[c.channel] for c in channel_list if c.country == code),
            value_recovered=round(
                sum(recovered[c.channel] for c in channel_list if c.country == code), 2
            ),
        )
        for code in sorted({p.country for p in plant_list} | {c.country for c in channel_list})
    ]
    return GeoOut(
        plants=plants,
        channels=channels,
        arcs=[
            GeoArc(plant=p, channel=c, units=u) for (p, c), u in sorted(arcs.items()) if p in shown
        ],
        countries=countries,
    )
