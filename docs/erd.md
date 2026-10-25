# Entity relationship diagrams

Evidence level: design, no code yet. All table content is synthetic (Kestrel Beauty Group). Only standard SAP table and field names are used, plus custom `Z` tables and `ZZ` append fields, which is the usual SAP convention. Every value the generator writes is an illustrative default.

The solver never reads the source layer. The path is source tables, then a `SourceAdapter`, then the canonical dataset, then the solver input. Field level rules are in `mapping.md`.

## 1. Source layer (SAP style)

```mermaid
erDiagram
    MARA ||--|{ MAKT : "described by"
    MARA ||--|{ MARC : "extended to plant"
    MARA }o--|| T023 : "material group"
    MARC ||--|{ MARD : "storage location"
    MARC ||--o| MBEW : "valuation"
    MARD ||--|{ MCHB : "batch stock"
    T001W ||--|{ MARC : "plant"
    MARA ||--o| ZABC : "ABC class"
    MARA ||--o{ ZSELLIN : "shipped to channel"
    MARA ||--o{ ZSELLOUT : "sold by channel"
    ZCHANNEL ||--|{ ZSELLIN : "receives"
    ZCHANNEL ||--|{ ZSELLOUT : "sells"
    ZCHANNEL ||--|{ ZCHANNEL_RULE : "tier rule"
    ZCHANNEL ||--|{ ZCHANNEL_ASRT : "group limit"

    MARA {
        string MATNR PK
        string MTART
        string MATKL FK
        int MHDHB "total shelf life, months"
        int MHDRZ "min remaining shelf life, percent"
        string ZZBRAND "append field"
        string ZZTIER "append field, luxury premium mass"
    }
    MAKT {
        string MATNR PK
        string SPRAS PK
        string MAKTX
    }
    T023 {
        string MATKL PK
        string WGBEZ
    }
    T001W {
        string WERKS PK
        string NAME1
        string LAND1
        string ZZREGION "append field"
        string ZZPTYPE "append field, factory or dc"
    }
    MARC {
        string MATNR PK
        string WERKS PK
        string MMSTA "plant material status"
    }
    MARD {
        string MATNR PK
        string WERKS PK
        string LGORT PK
        float LABST "unrestricted stock"
    }
    MCHB {
        string MATNR PK
        string WERKS PK
        string LGORT PK
        string CHARG PK "batch"
        float CLABS "unrestricted batch stock"
        date HSDAT "production date"
        date VFDAT "expiry date"
        string ZZREASON "append field, stock reason"
    }
    MBEW {
        string MATNR PK
        string BWKEY PK "valuation area, equals plant"
        float STPRS "standard price per unit"
    }
    ZABC {
        string MATNR PK
        string ABCCLASS "A B C"
        int RANK
    }
    ZCHANNEL {
        string CHANNEL PK
        string CTYPE
        string LAND1
        float LAT
        float LON
        float CAPUNITS
        int MAXSKU
        float MINRSL "percent"
        float RECFACT
    }
    ZCHANNEL_RULE {
        string CHANNEL PK
        string TIER PK
        bool ALLOWED
        float BRANDPEN "euro per unit"
    }
    ZCHANNEL_ASRT {
        string CHANNEL PK
        string ZZBRAND PK
        string MATKL PK
        int MAXSKU
        float MAXUNITS
    }
    ZSELLIN {
        string MATNR PK
        string CHANNEL PK
        date SHIPDATE PK
        float QTY
        float QTYTRANSIT "still in transit"
    }
    ZSELLOUT {
        string MATNR PK
        string CHANNEL PK
        string PERIOD PK "yyyymm"
        float QTY
    }
    ZPARAM {
        string PARAM PK
        string VALUE
        string UNIT
        string NOTE "illustrative default tag"
    }
```

Notes on the custom pieces:

* `ZCHANNEL_ASRT` is new compared with `docs/war_plan.md` section 4.2. It holds the group limits `A_{g,c}` (SKUs) and `U_{g,c}` (units, the Q8 decision, 2026-10-25) per channel and group, where a group is brand by category.
* A plant is either a factory or a distribution center. Distribution centers are plants of their own (`ZZPTYPE = dc`), which is how SAP models them, so the decision index stays material by plant by expiry month.
* `ZPARAM` holds scalar parameters and score weights. It has no foreign key.

## 2. Canonical layer

```mermaid
erDiagram
    Material ||--|{ Lot : "has"
    Plant ||--|{ Lot : "holds"
    Channel ||--|{ ChannelRule : "has"
    Channel ||--|{ GroupLimit : "has"
    Material ||--o{ Demand : "needed in"
    Channel ||--o{ Demand : "needs"
    Material ||--o| Abc : "classified"

    Material {
        string material PK
        string description
        string category
        string brand
        string tier
        int shelf_life_months
    }
    Plant {
        string plant PK
        string name
        string country
        string region
        string kind
    }
    Lot {
        string material FK
        string plant FK
        string expiry_bucket PK "yyyy-mm"
        date expiry_date "earliest batch expiry in the bucket"
        int qty
        float unit_cost
        string stock_reason
    }
    Channel {
        string channel PK
        string type
        string country
        float lat
        float lon
        int capacity_units
        int max_skus
    }
    ChannelRule {
        string channel FK
        float min_rsl_pct
        list allowed_tiers
        float recovery_factor
        map brand_penalty "per tier"
    }
    GroupLimit {
        string channel FK
        string brand
        string category
        int max_skus
        int max_units
    }
    Demand {
        string material FK
        string channel FK
        float daily_demand
        list seasonality "12 monthly indexes"
        int channel_stock
        int in_transit
    }
    Abc {
        string material FK
        string abc_class "A B C NEW"
        int rank
    }
```

`Plant` and `GroupLimit` are additions to the entity list in `docs/war_plan.md` section 4.4. The solver input holds lots, channels, rules, group limits, demand and scores, plus the admissible set with reason codes.
