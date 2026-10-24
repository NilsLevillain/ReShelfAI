# Imagery guide

Evidence level: licence statements are **[K] background knowledge**. Check the licence page of each source on the day you download, and record it in `assets/CREDITS.md`. No specific photo has been selected or verified yet.

## Rules

* No visible brands, logos, packaging text or recognizable people. Unbranded bottles and jars only.
* Prefer licences that need no attribution. Keep a credit line anyway for every file.
* Keep a record: file, source URL, author, licence, date downloaded.
* Export at 2400 px wide for heroes (shown at about 1100 by 136, so crop to a wide strip), 1600 px for cards, WebP for web, PNG or JPG for Remotion.
* Use compact 80 px banners on inner pages and 136 px on home. Always lay the `hero-overlay` gradient over photos. Text sits on the left, so choose photos whose interest is on the right.

## Sources, safest first

| Source | Licence [K] | Notes |
|---|---|---|
| Wikimedia Commons, filtered to CC0 or Public Domain | CC0, PD | Check the licence of each file, mixed content |
| NASA image library | Mostly public domain | Good for Earth and satellite views. Avoid images with logos |
| Copernicus Sentinel imagery (ESA) | Free, attribution requested | Satellite crops of farmland, coastlines, forests. Fits the ecology story well |
| Pexels | Pexels licence, free to use, no attribution needed | Not CC0. Do not redistribute the raw files as a collection |
| Unsplash | Unsplash licence, free to use | Not CC0. Same limit on redistribution. Watch for branded items |
| Pixabay | Pixabay Content License | Not CC0. Read the current terms, they have changed before |

Third party images keep their own terms. Commit only images whose licence allows it, and list each one in `CREDITS.md`.

## A zero risk option

Generate the banners yourself. A teal gradient mesh with soft shapes, or a seeded procedural pattern (contour lines, field patches, bottle silhouettes) made in SVG. Upsides: no licence, perfectly on palette, deterministic for Remotion, tiny files. Downside: less emotional than a photo. **Recommendation**: use generated banners everywhere by default and add two or three real photos only for the home page and the README, where the emotional pull matters.

## Page by page ideas

| Page | Mood | Search terms |
|---|---|---|
| Home | Land, renewal, scale | aerial farmland patchwork, terraced fields from above, rice paddies aerial |
| Overview | Water, forest, impact | aerial turquoise river forest, canopy from above, lake and trees aerial |
| Stock at risk | Supply chain, inventory | warehouse shelves wide angle, pallet racks, empty warehouse aisle, shipping containers aerial |
| Remonetization allocation | Choice, flow, routes | highway interchange aerial, rail yard aerial, cargo port from above |
| Allocation results | Clean energy, completion | solar panels aerial, solar farm rows, wind turbines on green hills |
| Deep dive modal | Product, detail | unbranded glass bottle macro, amber dropper bottle, plain white jar on stone, water droplets on leaf |
| Empty states | Calm, open | single plant seedling, empty shelf soft light |
| Environmental impact card | Trees, carbon | young forest, leaf macro, seedlings in soil |
| Video opening | Contrast between waste and second life | pallets of boxes, then green fields, conveyor belt with plain boxes |
| Docs and README | Neutral | abstract teal gradient (generated) |

## Product pictures

Beauty products are the hardest case because real packaging is a brand asset. Options:

| Option | Upside | Downside |
|---|---|---|
| Unbranded stock photos of bottles, tubes, jars | Real, warm | Hard to match across a set, some still show embossed marks |
| Simple 3D or SVG product silhouettes in the palette | Consistent, no licence to track, animatable in Remotion | Less realistic |
| Photos of your own plain objects | Fully yours | Time |

**Recommendation**: SVG silhouettes with soft teal tints for tables, tiles and video, and one unbranded photo per page for the hero only. The synthetic "Kestrel Beauty Group" catalog needs invented product names, never real ones.

## Treatments

* Corner radius 8, same as cards.
* Hero: photo plus `hero-overlay`, cropped wide, no blur.
* Cards and tiles use icons, not photos.
* Alt text on every image describing the scene, in plain language.
* Icons: a single outline set at 1.5px stroke, rounded caps, in `teal.400` or `teal.500`. Lucide (ISC licence [K]) fits and is available for React and Remotion.
