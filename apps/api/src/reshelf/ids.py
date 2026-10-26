"""Identifiers shared by elimination, solver input and constraints."""

from __future__ import annotations

LotKey = tuple[str, str, str]  # material, plant, expiry bucket
Pair = tuple[LotKey, str]  # lot, channel
MatChan = tuple[str, str]  # material, channel
Group = tuple[str, str]  # brand, category


def lot_label(key: LotKey) -> str:
    return "/".join(key)


def pair_label(pair: Pair) -> str:
    return f"{lot_label(pair[0])},{pair[1]}"


def mc_label(mc: MatChan) -> str:
    return f"{mc[0]},{mc[1]}"
