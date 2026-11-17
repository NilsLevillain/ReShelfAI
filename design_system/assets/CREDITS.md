# Credits

Every third party image or dataset used in the product is listed here with its source and licence.

| Asset | Used for | Source | Licence |
|---|---|---|---|
| Country outlines (`countries-110m.json`) | Borders on the stock globe (`apps/web/src/stock/countries.ts`) | Natural Earth, version 4.1.0, redistributed as TopoJSON by the `world-atlas` npm package, read with `topojson-client` | Natural Earth data is public domain. The `world-atlas` package is ISC |

Nothing is copied into the repo. The outlines come from the npm package at build time and ship in the globe chunk.
