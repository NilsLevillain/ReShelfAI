# Field mapping: source tables to canonical dataset

Evidence level: design, code in progress (week 2). Source names are standard SAP names or custom `Z` and `ZZ` names, all synthetic. Every default below is an invented illustrative default, stored in `ZPARAM` or the scenario yaml, never in code.

Format: source table.field, canonical field, transformation.

## Material

| Source | Canonical | Transformation |
|---|---|---|
| `MARA.MATNR` | `Material.material` | Strip leading zeros, upper case |
| `MAKT.MAKTX` (`SPRAS = E`) | `Material.description` | Trim. Keep accents (test TS-176) |
| `MARA.MATKL` joined to `T023.WGBEZ` | `Material.category` | Use the group description |
| `MARA.ZZBRAND` | `Material.brand` | As is |
| `MARA.ZZTIER` | `Material.tier` | Enum `luxury`, `premium`, `mass`. Pandera rejects anything else |
| `MARA.MHDHB` | `Material.shelf_life_months` | Integer above 0 |
| `MARA.MHDRZ` | not used by the solver | Kept in the source only. The minimum remaining shelf life comes from the channel (`ZCHANNEL.MINRSL`) |

## Plant

| Source | Canonical | Transformation |
|---|---|---|
| `T001W.WERKS` | `Plant.plant` | As is |
| `T001W.NAME1` | `Plant.name` | Trim |
| `T001W.LAND1` | `Plant.country` | ISO 3166 alpha 2 |
| `T001W.ZZREGION` | `Plant.region` | Enum `europe`, `north_america`, `asia_pacific` |
| `T001W.ZZPTYPE` | `Plant.kind` | Enum `factory`, `dc` |

## Lot (the decision index)

| Source | Canonical | Transformation |
|---|---|---|
| `MCHB.MATNR`, `MCHB.WERKS` | `Lot.material`, `Lot.plant` | Group key |
| `MCHB.VFDAT` | `Lot.expiry_bucket`, `Lot.expiry_date` | Bucket is `yyyy-mm` of `VFDAT`. `expiry_date` is the earliest `VFDAT` in the bucket, so remaining shelf life is never overstated (ADR 003) |
| `MCHB.CLABS` | `Lot.qty` | Sum over batches (`CHARG`) and storage locations (`LGORT`) in the group. Lots with a sum of zero or less are dropped |
| `MBEW.STPRS` joined on `BWKEY = WERKS` | `Lot.unit_cost` | Standard price. Weighted average if several valuation rows exist. Missing price rejects the dataset |
| `MCHB.ZZREASON` | `Lot.stock_reason` | Enum `near_expiry`, `excess`, `obsolete`, `discontinued`, `overproduction`. Most frequent reason by quantity when a lot mixes reasons. Attribute for the overview and filters, not a solver input |
| `MARC.MMSTA` | not mapped | Discontinued status already shows in `ZZREASON` |
| `MARD.LABST` | reconciliation only | Check: `LABST` equals the sum of `CLABS` per material, plant and storage location. A mismatch is a validation error |

## Channel, rules and group limits

| Source | Canonical | Transformation |
|---|---|---|
| `ZCHANNEL.CHANNEL`, `CTYPE`, `LAND1`, `LAT`, `LON` | `Channel.*` | As is. `CTYPE` enum: `outlet`, `friends_family`, `clearance_web`, `ngo_donation`, `liquidation` |
| `ZCHANNEL.CAPUNITS` | `Channel.capacity_units` | Integer, not negative |
| `ZCHANNEL.MAXSKU` | `Channel.max_skus` | Integer, not negative |
| `ZCHANNEL.TRANSITD` | `Channel.transit_days` | Integer, not negative. Delivery date is `as_of` plus this value |
| `ZCHANNEL.MINRSL` | `ChannelRule.min_rsl_pct` | Percent from 0 to 100 |
| `ZCHANNEL.RECFACT` | `ChannelRule.recovery_factor` | Share of unit cost recovered, from 0 to 1 |
| `ZCHANNEL_RULE.TIER` where `ALLOWED = X` | `ChannelRule.allowed_tiers` | Set of tiers per channel |
| `ZCHANNEL_RULE.BRANDPEN` | `ChannelRule.brand_penalty[tier]` | Euro per unit. Missing tier defaults to 0 for allowed tiers |
| `ZCHANNEL_ASRT.MAXSKU`, `MAXUNITS` | `GroupLimit.max_skus`, `max_units` | Per channel, brand and category. A missing row means no group limit |

## Demand and score

| Source | Canonical | Transformation |
|---|---|---|
| `ZSELLOUT.QTY` over the last 12 closed periods | `Demand.daily_demand` | Sum divided by 365, per material and channel |
| `ZSELLOUT.QTY` by calendar month | `Demand.seasonality` | Month total divided by the monthly mean. Twelve indexes with a mean of 1 |
| `ZCHSTOCK.QTYONHAND` | `Demand.channel_stock` | Stock held by the second life channel, read as is. Not derived from sell in and sell out |
| `ZCHSTOCK.QTYTRANSIT` | `Demand.in_transit` | Shipped, not yet delivered. Coverage need counts on hand plus in transit. A pair without a row has no stock |
| `ZABC.ABCCLASS`, `ZABC.RANK` | `Abc.abc_class`, `Abc.rank` | The class is derived per material and channel. A pair with sellout history in the channel keeps the `ZABC` class (`C` if the material has no row). A pair with no sellout history in the channel is `NEW`, because past sales cannot forecast it. A missing rank counts as the lowest, rank N, where N is the number of ranked materials |
| `ZPARAM.PUSH_QUANTITY_UNITS_<CATEGORY>` | push quantity per category | Units placed when a `NEW` SKU is pushed into a channel, one row per product category |
| `ZPARAM` | scenario parameters | Typed and validated by Pydantic (negative capacity, percent above 100, unknown class are rejected before any solve) |

## Defaults for missing data (each has a test)

| Case | Default |
|---|---|
| No demand row for a material and channel | No coverage need |
| `NEW` material whose category has no push quantity | Not allocated to that channel, reason shown in the trace |
| No `ZCHANNEL_ASRT` row | No group limit |
| No rank | Lowest rank in the class |

## Where the generator writes

`make demo-data` writes the source tables above as CSV files into `data/generated/<scenario>/` (gitignored), one file per table. The `CsvAdapter` reads that folder. A Parquet copy is a later step.
