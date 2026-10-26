"""Pandera schemas for the source tables. Names are standard SAP names plus custom Z tables."""

from __future__ import annotations

from pandera.pandas import Check, Column, DataFrameSchema

_REASONS = ["near_expiry", "excess", "obsolete", "discontinued", "overproduction"]
_TIERS = ["luxury", "premium", "mass"]
_DATE = r"^\d{4}-\d{2}-\d{2}$"


def _int(minimum: int = 0, *, strict: bool = False) -> Column:
    check = Check.gt(minimum) if strict else Check.ge(minimum)
    return Column(int, check, coerce=True)


def _str() -> Column:
    return Column(str, coerce=True)


SOURCE_SCHEMAS: dict[str, DataFrameSchema] = {
    "MARA": DataFrameSchema(
        {
            "MATNR": _str(),
            "MATKL": _str(),
            "MHDHB": _int(0, strict=True),
            "ZZBRAND": _str(),
            "ZZTIER": Column(str, Check.isin(_TIERS)),
        }
    ),
    "MAKT": DataFrameSchema({"MATNR": _str(), "SPRAS": _str(), "MAKTX": _str()}),
    "T023": DataFrameSchema({"MATKL": _str(), "WGBEZ": _str()}),
    "T001W": DataFrameSchema(
        {
            "WERKS": _str(),
            "NAME1": _str(),
            "LAND1": _str(),
            "ZZREGION": Column(str, Check.isin(["europe", "north_america", "asia_pacific"])),
            "ZZPTYPE": Column(str, Check.isin(["factory", "dc"])),
        }
    ),
    "MARD": DataFrameSchema({"MATNR": _str(), "WERKS": _str(), "LGORT": _str(), "LABST": _int()}),
    "MCHB": DataFrameSchema(
        {
            "MATNR": _str(),
            "WERKS": _str(),
            "LGORT": _str(),
            "CHARG": _str(),
            "CLABS": _int(),
            "VFDAT": Column(str, Check.str_matches(_DATE)),
            "ZZREASON": Column(str, Check.isin(_REASONS)),
        }
    ),
    "MBEW": DataFrameSchema(
        {"MATNR": _str(), "BWKEY": _str(), "STPRS": Column(float, Check.ge(0), coerce=True)}
    ),
    "ZABC": DataFrameSchema(
        {
            "MATNR": _str(),
            "ABCCLASS": Column(str, Check.isin(["A", "B", "C"])),
            "RANK": _int(0, strict=True),
        }
    ),
    "ZCHANNEL": DataFrameSchema(
        {
            "CHANNEL": _str(),
            "CTYPE": Column(
                str,
                Check.isin(
                    ["outlet", "friends_family", "clearance_web", "ngo_donation", "liquidation"]
                ),
            ),
            "LAND1": _str(),
            "LAT": Column(float, coerce=True),
            "LON": Column(float, coerce=True),
            "CAPUNITS": _int(),
            "MAXSKU": _int(),
            "MINRSL": Column(float, Check.in_range(0, 100), coerce=True),
            "RECFACT": Column(float, Check.in_range(0, 1), coerce=True),
            "TRANSITD": _int(),
        }
    ),
    "ZCHANNEL_RULE": DataFrameSchema(
        {
            "CHANNEL": _str(),
            "TIER": Column(str, Check.isin(_TIERS)),
            "ALLOWED": Column(str, Check.isin(["X", ""])),
            "BRANDPEN": Column(float, Check.ge(0), coerce=True),
        }
    ),
    "ZCHANNEL_ASRT": DataFrameSchema(
        {
            "CHANNEL": _str(),
            "ZZBRAND": _str(),
            "MATKL": _str(),
            "MAXSKU": _int(),
            "MAXUNITS": _int(),
        }
    ),
    "ZSELLIN": DataFrameSchema(
        {
            "MATNR": _str(),
            "CHANNEL": _str(),
            "SHIPDATE": Column(str, Check.str_matches(_DATE)),
            "QTY": _int(),
            "QTYTRANSIT": _int(),
        }
    ),
    "ZSELLOUT": DataFrameSchema(
        {
            "MATNR": _str(),
            "CHANNEL": _str(),
            "PERIOD": Column(str, Check.str_matches(r"^\d{4}(0[1-9]|1[0-2])$")),
            "QTY": _int(),
        }
    ),
    "ZPARAM": DataFrameSchema({"PARAM": _str(), "VALUE": _str()}),
}

__all__ = ["SOURCE_SCHEMAS"]
