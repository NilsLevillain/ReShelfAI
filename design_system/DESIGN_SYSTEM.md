# Reshelf design system

Evidence level: the base palette is **sampled from the author's early mockups**. The type pairing, the hero flow components, dark mode and the video themes are **derived** for this project from the strategy and war plan (marked *derived*). Nothing here is validated with users yet.

Source of truth is `tokens/tokens.json`, plus `assets/icons.json` for icons and `components/components.css` for components (hand written, tokens only). Run `node design_system/scripts/build.mjs` to regenerate everything in `dist/` and the recap page. Open `dist/preview.html` to see tokens, logo, icons and components, with a theme switch.

Rule: nothing visual is invented inside a page. A new color, size, icon, component or layout rule goes into the design system first, then the page uses it. The recap page `product_management/recap.html` is built from this system and is the reference for the feature page pattern (section 6.5).

## 1. Provenance and what changed

The early mockups were the starting point, not the target. This system keeps their calm teal and blue character and the table first layout, and changes the rest:

| Kept | Changed or added |
|---|---|
| Teal for action, blue for data, indigo for links | New type pairing, new token names, accessible text colors |
| White cards on light grey canvas, tinted KPI tiles | Tile tints become fixed semantic tokens with dark variants |
| Dense zebra tables, filter bar, hint banner, modal, toasts | Hero flow components that the mockups lack (section 6) |
| Wide hero banners | Compact banners on inner pages, generated or free to use imagery |
| Light theme | Dark theme and a switch, for the app and for video |

## 2. Design character

Calm, trustworthy, quietly ecological. A deep teal brand, blue reserved for data, white cards on a light canvas, dense tables, big soft numbers. The memorable moment is the **euro cost of a rule change**, so that number gets the largest style in the system (`kpi-hero`).

Principles, each tied to the strategy:

| Principle | Strategy source | Design consequence |
|---|---|---|
| Tighten a rule. See what it costs. See why. | Value proposition, hero flow | The rule control, euro delta and Why panel sit on one screen, never on three |
| Trust over speed | Triage: four of five top asks are about trust | Every number can open its explanation. Solver status is always visible |
| Tables first, globe as a filter | Strategy trade offs, R1 | Tables are the main surface. The globe sets filters and never carries data alone |
| The solver decides, AI drafts | Strategy trade offs, R18 to R21 | AI content is visually different from solver content (dashed, lilac) so nobody mistakes one for the other |
| Baseline next to optimizer, always | ADR 005, metrics | Two fixed colors for the pair, used on every chart and chip |
| Simulated, never real | Synthetic data rule | A "Simulated data" badge on every screen and video frame |
| Brand risk is a trade off, not a footnote | Stakeholder conflicts | Brand tier has its own color set and shows in compare |

Colour rules: teal means act, blue means data, indigo means navigate or AI, amber means a cost or a warning, magenta means leave or destroy. Color never carries meaning alone.

## 3. Color

### 3.1 Brand and action

| Token | Hex | Origin | Use |
|---|---|---|---|
| `teal.500` | `#187573` | sampled | Primary button, outline button, active nav, optimizer. 5.48:1 on white |
| `teal.600` | `#1f6359` | sampled | Banners, hover. 7.03:1 with white text |
| `teal.400` | `#49828c` | sampled | Pagination active, icon strokes. **Not for text**, 4.33:1 on white |
| `teal.300` | `#64bdba` | sampled | Secondary bars, mass tier |
| `teal.200` | `#8bd8d3` | sampled | Gradient end, dark video accent |
| `teal.50` | `#f4f7f6` | sampled | Icon chip, light video ground |
| `indigo.600` | `#3b45cf` | sampled | Links, "Launch", AI marker. 7.15:1 |
| `magenta.600` | `#b6115a` | sampled | Leave and destroy actions. 6.53:1 with white text |

### 3.2 Data

| Token | Hex | Use |
|---|---|---|
| `blue.700` | `#084b9d` | Primary bar color, data numbers on tint |
| `blue.500` | `#006ef9` | Series 1, focus ring |
| `blue.400` | `#0c8ce9` | Gradient bars, info status |
| `blue.50` | `#e6f1ff` | Info bars, optimizer chip ground |
| `slate.700` | `#2c506d` | KPI text, series 2 |
| `amber.400` | `#f7c733` | Series 3, stock at risk area |
| `green.500` | `#59e0a0` | Allocated, positive flow |
| `red.500` | `#dc2026` | Remaining risk, inflow |

Categorical order: `blue.500`, `slate.700`, `amber.400`, `magenta.600`, `cyan.400`. **Not yet checked for color vision deficiency.** Run it through the dataviz validator before shipping charts and always add direct labels or values on bars.

Channel colors reuse this order for the five channels (outlet, friends and family, clearance website, donation, liquidation). Fix the mapping once in code so a channel keeps its color on every chart.

### 3.3 Hero flow colors *derived*

| Token | Light | Use |
|---|---|---|
| `compare.baseline` | `neutral.500` grey | Greedy baseline everywhere: chip, bar, line |
| `compare.optimizer` | `teal.500` | Optimizer everywhere |
| `compare.delta-gain` | `green.700` | Value gained against baseline |
| `compare.delta-cost` | `amber.700` | Euro cost of a rule. Amber, not red, because a cost is a trade off, not an error |
| `compare.violation` | `amber.500` | Baseline rule violations (the audit from ADR 005) |
| `tier.luxury` / `premium` / `mass` | violet `#5b3f8c`, blue `#2761aa`, teal `#64bdba` | Brand tier chips and compare columns |
| `ai.*` | lilac ground, indigo dashed border and text | Anything drafted by AI |
| `solver.optimal` / `limit` / `infeasible` | green, amber, rose grounds with matching text | Solver status chip next to every result |
| `globe.*` | ocean `blue.50`, land `neutral.100`, plant point `teal.500`, arc `cyan.400` | Globe, with dark variants |

### 3.4 Status

| Status | Bar and icon | Text on light |
|---|---|---|
| Success | `green.400` `#42be65` | `green.700` `#1a7f3c` |
| Warning | `amber.500` `#f1c21b` | `amber.700` `#8a6500` |
| Error | `red.400` `#fa4d56` | `red.700` `#c4262e` |

Toasts are dark (`neutral.800`) with a 4px left bar, icon, bold status word, then message. The save flow uses "Draft saved", "Allocation submitted", "Submission failed". Yellow is Warning and red is Error.

### 3.5 Neutrals and tiles

`neutral.0` card, `50` canvas, `100` zebra and subtle fills, `200` borders, `500` secondary text (4.61:1), `700` primary text, `800` toast ground.

KPI tiles use `tile.yellow`, `tile.aqua`, `tile.lilac`, `tile.rose`, in that order for value at risk, units, SKUs and near expiry. Fixed assignment, no other use. Each has a dark variant. Lilac tile and the AI lilac are close: the AI marker is told apart by its dashed border and its label.

### 3.6 Themes

**Light is the default** for the app, the demo and the video. Dark is a first class switch, not a roadmap item, because tokens make it nearly free (see the note on R14 in section 11).

* App: set `data-theme="dark"` or `"light"` on the root element. With no attribute, `prefers-color-scheme` decides. The user's choice is stored in `localStorage` under `reshelf-theme`, and the preview page shows the switch.
* Dark values are *derived*: canvas `#0f1f21`, surface `#16292c`, text `#e6eef0`. Primary text on canvas is 14.4:1, secondary 7.7:1.
* Video: see section 8.

### 3.7 Gradients

`hero-overlay` (teal over a photo or generated banner, keeps white text readable), `impact-card` (slate blue to aqua, once per page), `card-glow` (faint cyan corner on a hovered card).

## 4. Typography

| Role | Family | Why |
|---|---|---|
| UI and data | **IBM Plex Sans** | Open license (OFL), tabular figures, clear at 12px in tables |
| Navigation, page headlines | **Source Serif 4** | Gives a calm editorial signature against dense data |
| Wordmark and feature hero headline | **Sitka Banner** (`type.family.wordmark`), Source Serif 4 as fallback | Sitka ships with Windows only, so any asset that must look identical gets the wordmark converted to outlines. Weight 600 |
| IDs, codes, constraint names | **IBM Plex Mono** | EAN, SKU and rule names align in columns |

Free for web, Remotion and print. Web: `@fontsource/ibm-plex-sans`, `@fontsource/source-serif-4`, `@fontsource/ibm-plex-mono`. Video: `@remotion/google-fonts`. The pairing is my call.

| Token | Size / line | Role |
|---|---|---|
| `xs` | 12 / 16 | Table cells and head, axes, captions |
| `sm` | 13 / 20 | Labels, delta, buttons |
| `base` | 14 / 22 | Body, nav |
| `md` | 16 / 24 | Card title, lede |
| `lg` | 18 / 28 | Section title |
| `xl` | 20 / 28 | Modal title |
| `2xl` | 24 / 32 | Page title |
| `3xl` | 30 / 38 | KPI value |
| `4xl` | 38 / 46 | Docs headings |
| `5xl` | 48 / 56 | Hero euro cost, display |

Weights: 400 body, 500 labels and numbers, 600 titles and table head, 700 page titles. Numbers use tabular figures. Lines under 80 characters. Sentence case, no all caps.

Text style roles (generated as `.rs-text-<role>`): `display`, `page-title`, `page-lede`, `card-title`, `nav`, `body`, `label`, `table-head`, `table-cell`, `kpi-value`, `kpi-label`, `kpi-hero`, `delta`, `code`, plus the feature page set: `wordmark`, `display-hero`, `section-title`, `stat-value`. The last three are fluid (`clamp`), so headlines and big numbers grow with the screen.

### Number format *derived*

| Kind | Format | Example |
|---|---|---|
| Money | Symbol first, short scale | `€13.0M`, `€412K` |
| Delta | Sign always shown, symbol after sign | `+€1.7M`, `−€1.2M` |
| Units | Thousands separator or K, M | `43.1K`, `3,627,294` |
| Share | One decimal under 10%, none above | `5.7%`, `78%` |
| Time and gap | Mono | `1.8 s`, `gap 0.0%` |

## 5. Space, shape, elevation, motion

* **Space**: 4px base. Steps 4, 8, 12, 16, 24, 32, 48, 64. Card padding 16 or 24, card gap 24.
* **Radius**: 4 buttons and inputs, 8 cards and tiles, 12 modals, pill for chips.
* **Shadow**: `card` faint two layer. `overlay` for modals and toasts only.
* **Layout**: see section 14. Pages are fluid, nav is 56, hero 136 on the app home page, 80 compact on inner pages, 24 gutter between app panels. Tables scroll sideways with a sticky first column, they never wrap.
* **Motion**: 120, 200, 320 ms. Motion answers an action: rule dial moves and numbers tick, panel opens, toast appears. No entrance animation on page load. Respects reduced motion. Allowed flourishes: the euro delta counting to its value after a rule change, and on a feature page the hero flow illustration (section 6.5), which plays once and then keeps its dashed lines flowing at `motion.duration.flow` (1600 ms per loop, linear). Hover on a card turns its border teal and fades in `gradient.card-glow`, and a chevron turns when a card opens. Decorative motion is never the only signal and stops under reduced motion.

## 6. Components

### 6.1 From the early mockups, adapted

| Component | Spec |
|---|---|
| Top nav | White, 56 tall, wordmark left, links in serif, active link teal.500, theme switch and account right |
| Banner | Image or generated pattern plus `hero-overlay`, white title and lede. 136 home, 80 elsewhere |
| Filter bar | Card with labelled selects, "All" default. The globe writes into it |
| Hint banner | `bg.hint`, bulb icon, one paragraph that says what to do on this page |
| Context bar | `bg.info`, bold key and value pairs for the selected lot |
| KPI tile | Tinted, label, value, delta line with arrow, icon chip |
| Home card | White, icon in round `teal.50` chip, title, one line, "Launch" link |
| Data table | Zebra, 12px, link in first column, sticky head, page size 8, teal active page. Excel export button in the header |
| Buttons | Outline teal secondary, one filled teal primary per view, magenta for leave actions |
| Toast | Dark, status bar, bold status word then message, close |
| Modal | White 12px radius, two column cards, "Go back" bottom right |

### 6.2 New, for the hero flow and the strategy

| Component | Spec | Strategy source |
|---|---|---|
| Rule dial | Slider or stepper on a precomputed grid, teal track, current value in mono, label names the rule in plain words | Hero flow, demo mode |
| Euro delta | `kpi-hero` number in `delta-cost` or `delta-gain`, with "cost of this rule" and baseline reference beneath | Hero |
| Compare panel | Two or three scenario columns, baseline column grey, optimizer teal, deltas between, brand risk row with tier chips | R8, R9 |
| Why panel | Right side drawer. Sections: rule trace (binding rules as amber chips with slack bar), blocked channels (reason code in mono plus plain sentence), counterfactual button "Relax this rule" that returns the euro cost | R4 to R6, ADR 005 |
| Baseline audit | List of baseline violations per named constraint, amber, with raw value and compliant value | ADR 005 |
| Solver status chip | `solver.*` colors: status, MIP gap, time and limit. Always shown beside results | War plan, SolveResult |
| Data source banner | Slim bar: "Cached results" (info) or "Live solver" (success) | Demo mode |
| Simulated badge | Small neutral pill "Simulated data" in the nav, in the README banner and on video frames | Synthetic data rule |
| Globe | `globe.*` tokens, points sized by value at risk, arcs after a solve. Click sets a filter chip above the table. Table fallback when WebGL is missing | R1, war plan 6.4 |
| Scenario switcher | Select with save and load, shows overridden scenarios with a pencil icon | R7, R10 |
| Process stepper | Four steps (Parameters, Run, Review, Export): number or check in a disc, label, a line between. Done is teal, current is filled teal.500 with `aria-current="step"`, upcoming is neutral. State always has a word or icon, never color alone. Classes `rs-stepper`, `rs-stepper__item` (`data-state="done"`), `rs-stepper__disc`, `rs-stepper__label` | War plan 6.3b |
| Column group toggle | `rs-seg rs-seg--cols` above a table: identity, stock, allocation, value. Hides or shows a group of columns, the sticky first column stays | War plan 6.3b |
| Group by select | `rs-groupby`, rows `rs-row--group` and `rs-row--total`. Select in the table header (brand, category, channel, plant). Group rows are collapsible and carry subtotals, the totals row stays last | War plan 6.3b |
| Share cell | `rs-share`, `rs-share__bar`, `rs-share__fill` with `--rs-share` set inline to the percent. Number plus a thin in cell bar for allocation share or remaining units. Optimizer teal for allocated, `compare.baseline` grey for remaining. The number is always printed | War plan 6.3b |
| Reason and hierarchy chart | Stock split by reason (bar) and brand to category drill (stacked bars with a breadcrumb). Series use the categorical order. A click writes a filter chip. Breadcrumb is `rs-crumbs` | War plan 6.3b |
| Inline error | `rs-error`, `rs-error__endpoint`. `status.error` text and icon, the endpoint name in mono, a Retry button. Replaces the content area for that panel only. Never an empty state, never a silent fallback | War plan 6.3b |
| AI draft card | Dashed indigo border, lilac ground, label "Drafted by AI, needs your approval", Approve and Discard buttons, the validated rule diff in a table | R18, R19 |
| Decision log row | Owner, reason, approver, time, scenario link. Read only | R22 (pending E9) |
| Empty and loading states | Plain sentence plus one action ("Run the optimizer to see results"). Skeleton rows for tables, never spinners alone | Voice |

### 6.5 Feature page pattern (recap, landing, README site)

Built in `components/components.css`, class prefix `rs-`. Reference page: `product_management/recap.html` (source `recap.src.html`).

| Component | Class | Spec |
|---|---|---|
| Nav with tabs | `rs-nav`, `rs-tab` | 56 tall. Serif tab labels with an icon, active tab teal.500 with a 3px underline. Under 640 the tabs become a fixed bottom bar (thumb reach) |
| Feature hero | `rs-hero` | `bg.brand` ground with `gradient.hero-glow`. `display-hero` headline in the wordmark family, one lede line, three outcome pills (icon in a teal.200 disc), a small "synthetic data" note, and the flow illustration on the right from 1024. The headline states the outcome in plain words, never the mechanism |
| How it works strip | `rs-how` | Three steps overlapping the hero edge: icon chip, bold title, one line with a concrete example. Cost words use `compare.delta-cost` |
| Page head | `rs-page-head`, `rs-evidence` | `section-title` question or claim, then one pill that states the evidence level (honest status) |
| Stat card | `rs-card rs-stat` | `stat-value` number and a short label. The dashed variant (`rs-card--dashed`) is for an honest zero |
| Card | `rs-card` | White, 8 radius, card shadow. **Hover: the border turns `border.brand` and `gradient.card-glow` fades in over 320 ms.** Optional icon chip on top, title, grey text, optional footer pushed to the bottom with `rs-card__foot` |
| Cards grid | `rs-cards` | Auto fit columns from `layout.card-min`. **Cards in a row always share one height** (stretch). `--top` only for expandable cards. 3 up and 4 up variants, see section 14 |
| Expandable card | `rs-bet` | A `details` card. The summary shows icon, title and "How we test it" with a chevron that turns 180 degrees. The body has a rule above it, with pass (green text) and fail (amber text) lines |
| Segmented control | `rs-seg` | Pill buttons for filters and tab like switches. Selected is filled teal.500. Counts shown in a muted number |
| Choice row | `rs-choice` | The left border color says the decision: green build now, blue later, magenta not doing. Always paired with text |
| North star block | `rs-north` | Aqua tint, one metric in serif, three guardrails with an alert icon in amber |
| Vision band | `rs-vision` | `gradient.impact-card`, once per page, dark text |
| Level table | `rs-table`, `rs-level` | Three dots plus the word, so color never carries meaning. Own product column tinted aqua |
| Steps | `rs-step` | Top border says free (teal) or paid (blue). A pill says the state |
| Week selector | `rs-weeks`, `rs-week`, `rs-week-detail` | Ten buttons with a build and a discovery bar and the hours as text, a diamond marks a gate. The selected week fills the detail panel |
| Callout | `rs-callout` | Left bar plus tint. Amber for a warning or a rule, blue for information |
| Go deeper | `rs-deeper` | A collapsed bar at the bottom of every pane with the detail that did not fit in the two minute read: lists in cards and links to the source documents |
| Hero flow illustration | `assets/illustrations/flow-hero.svg` | Stock units travel from one shelf to three second life channels (plays once), then the dashed lines flow lightly. Colors read tokens. Reduced motion jumps to the end state |

Writing rules for a feature page: plain words a stranger understands, no solver or project jargon in the visible copy, one idea per card, detail goes under Go deeper. Every number is honest: zero is shown as zero.

### 6.3 Page map

| Page (war plan) | Mockup pattern to reuse | New pieces |
|---|---|---|
| Home | Home cards, banner | Simulated badge, data source banner |
| Stock overview | Overview tiles, donut, bars, filter bar | Globe as filter |
| Parameters | Filter bar, hint banner | Rule dials, scenario switcher, AI draft card |
| Results | Results tiles, line, waterfall, table | Solver chip, baseline audit, Why panel |
| Compare | none | Compare panel, euro delta |
| Material deep dive | Deep dive modal | Rule trace for the lot |

### 6.4 Test hooks

Hero elements carry stable `data-testid` values, for Playwright and Remotion. Reserved names: `rule-dial`, `euro-delta`, `compare-panel`, `baseline-column`, `optimizer-column`, `why-panel`, `rule-trace`, `counterfactual-button`, `solver-status`, `data-source-banner`, `simulated-badge`, `globe`, `kpi-value-at-risk`, `kpi-units-destroyed`, `ai-draft-card`.

## 7. Voice

Active voice, sentence case, plain verbs. Buttons say what happens: "Save draft", "Submit allocation". A toast repeats the action it confirms. Errors say what went wrong and what to do. Name things as the planner does: "rule", "channel", "lot", "expiry", never solver words in the main UI (the Why panel may show constraint names in mono as detail).

Fixed lines: tagline "Tighten a rule. See what it costs. See why." Counterfactual button "Relax this rule". Every KPI that compares carries "against the greedy baseline". Every screen with numbers carries "Simulated data".

## 8. Video (Remotion)

1920 by 1080 at 30 fps, text about twice the web scale (body 36, title 72, kpi 160), safe margin 96. **Light is the default theme and dark is a prop.**

```ts
import { tokens } from '../design_system/dist/tokens';
const theme = tokens.video.theme[props.theme ?? 'light'];       // video ground, text, accent
const ui = tokens.semantic[props.theme ?? 'light'];             // product colors inside UI shots
```

| Mode | Ground | Text | Accent |
|---|---|---|---|
| Light (default) | `teal.50` | `neutral.700` | `teal.500` |
| Dark | `teal.800` | white | `teal.200` |

Real UI components are rendered with the same theme as the scene, so a theme prop switches the whole video. Cross fade 9 frames, hold each beat at least 45 frames. The storyboard in the war plan section 10 maps to tokens as follows: problem counter in `delta-cost` amber, globe uses `globe.*`, baseline versus optimizer uses `compare.*`, Why panel uses `kpi-hero` for the euro cost, call to action in `teal.500` filled button. Render one cut per theme only if time allows. Never retype a value in a composition.

## 9. Documentation and README

Use `dist/tokens.css` for any generated HTML. README banner: `teal.600` ground, white text, `5xl`, the "Simulated data" badge. Mermaid theme variables: primary `teal.500`, text `neutral.700`, lines `neutral.200`. Docs diagrams use the same compare colors (grey baseline, teal optimizer).

## 10. Accessibility floor

* Text contrast at least 4.5:1, large text and UI parts at least 3:1. Checked pairs are noted above. Dark values were checked for primary and secondary text only.
* Visible focus ring in `border.focus`.
* Never color alone: chips carry text, bars carry values, series carry direct labels.
* Minimum 12px, minimum target 32px.
* Reduced motion respected, including the euro delta count.
* The globe has a table equivalent.

## 11. Open questions and notes

* **Wordmark and logo**: a proposal exists (section 12). Needs the author's review before the video and README banner. Convert the wordmark to outlines for the banner and the video.
* **R14 in the triage**: light and dark was declined as cosmetic. It is now a decision to support both. Cost is low with tokens, but update `3_feature_triage.md` and the backlog so the docs agree.
* **Compact banner**: recommended 80px on inner pages to give tables more room. Confirm when the first page is built.
* **Serif nav**: keep or drop to one family. Decide on the first built page.
* **Chart palette**: color vision check pending.
* **Dark tile and AI colors**: derived, check on screen.

## 12. Logo and wordmark *derived, proposal*

* **Mark** (`assets/logo/mark.svg`, mono version `mark-mono.svg`): three shelves. The middle shelf hands a short unit (teal.300) to a second shelf. It reads as "give stock a second shelf" and works at 16 px.
* **Wordmark**: "Reshelf" in `type.family.wordmark` (Sitka Banner, fallback Source Serif 4), weight 600, tracking tight, sentence case. Primary text color on light, white on teal.
* **Lockup**: mark left, 8 px gap (`space.2`), wordmark right, vertically centered. Nav size is `size.mark` (28).
* **Color use**: mark teal.500 plus teal.300 on light grounds. White or `mark-mono` on teal.600 and photos. Clear space equals one shelf height on all sides. Do not recolor, rotate or add effects.
* **For assets that leave the web** (README banner, video, social preview): export the wordmark to outlines so Sitka does not need to be installed.

## 13. Icons

* Source `assets/icons.json`. 24 by 24 grid, 2 px stroke, round caps and joins, `currentColor`. Built into `dist/icons.svg` (sprite) and `dist/icons.ts`.
* Use: `<svg class="rs-icon"><use href="#rs-i-euro"/></svg>` after inlining the sprite once per page. Sizes: `rs-icon--sm` 16, default 20, `rs-icon--lg` 24 (`size.icon-*`).
* **Icon chip**: `rs-icon-chip`, a 40 px round chip in teal.100 with a teal.600 glyph (dark theme: `bg.subtle` and `text.brand`). The chip is a grid, so a glyph is always centered. Never style the chip's parent with a descendant `span` rule, it breaks the centering.
* Every glyph must be optically centered on 12,12. Check new icons in `dist/preview.html` inside a chip.
* Meaning is fixed: euro is cost or money, scale is fairness, shield is a guarantee, alert is a guardrail, why is explanation, sliders is a rule. Do not reuse an icon for a second meaning.
* Current set: search, chart, flag, bin, leaf, euro, sliders, why, hand, wallet, reach, team, chev, alert, shield, tag, box, lock, law, scale, play, clock, sun, moon, book.

## 14. Responsive layout rules

Tokens: `layout.root-size`, `layout.pad`, `layout.card-min`, `layout.card-min-wide`, `layout.card-min-stat`, `layout.content-max`, breakpoints `sm` 640, `md` 1024, `lg` 1440, `xl` 1800.

* **Fluid, never a centered column.** The `html` font size is `clamp(16px, 0.3vw + 12.5px, 24px)`, so every rem grows on large screens and a zoomed out view fills the screen. Side padding is `clamp(1rem, 4vw, 6rem)`. Only an ultra wide cap (`content-max` 2400) stops growth. This replaces the old 1400 cap on feature pages. Dense app tables can still set their own max.
* **Grids auto fit** from the card minimums: `repeat(auto-fit, minmax(min(100%, card-min), 1fr))`. From `xl` the card grids lock to 4 up (3 up for the wide variant).
* **Below 640 (phone)**: one column, tabs move to a fixed bottom bar, the hero illustration shrinks to 24rem, how it works steps stack, week buttons wrap to 5 per row, the Go deeper hint text hides.
* **From 640**: how it works is 3 columns, weeks are 10 in a row, north star is 2 columns.
* **From 1024 (md)**: hero is 2 columns (text and illustration), split sections are 2 columns.
* Tables scroll sideways inside their card. Touch targets 32 px minimum, and the bottom tab bar is 60 px.
* Test at 390, 768, 1440 and 1920 wide, and zoomed out to 50%.
