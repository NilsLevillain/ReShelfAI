# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## State of the repo

Pre code. Only planning documents exist: `docs/war_plan.md` (execution plan, source of truth for architecture and the 8 week schedule), `product_management/` (discovery, strategy, metrics), `design_system/` (tokens, spec, imagery guide), and empty scaffold folders (`apps/api`, `apps/web`, `data/*`, `infra`, `video`). Check the week table in `docs/war_plan.md` section 7 to see what is in scope now and what is explicitly "not built" yet.

Commands below are **planned** in the war plan and do not exist until week 0 and 1 land: `make dev`, `make test`, `make demo-data`, `make precompute`. Python with `uv` and `pytest` (one test: `uv run pytest apps/api/tests/<file>::<test>`), web with `pnpm` and Vitest, one Playwright e2e test. Verify the Makefile exists before relying on them.

## What Reshelf is

A portfolio grade SaaS demo that allocates stock that cannot sell through primary retail (near expiry, discontinued, overproduction) to second life channels, under business rules, and explains each decision. Hero flow: tighten a rule, see what it costs in euros, see why. Two goals run in parallel: a public repo that proves product and engineering skill, and a possible commercial product later. Keep the design portable.

## Clean room rules (hard constraints)

The product is a from scratch rebuild of an employer prototype. Nothing from that prototype may appear anywhere, including docs.

* No employer or company names, logos, product names, internal system names, file or column names, Figma assets, slide content or code.
* No real numbers, targets, thresholds, scoring values or rules. Every value is invented and documented as an illustrative default.
* All data is synthetic, produced by a seeded generator. The demo company is the invented "Kestrel Beauty Group".
* Only generic public ERP concepts and standard SAP table and field names.
* KPIs are simulated and always shown against a greedy baseline. Never claim real business impact.
* `_private/` holds the original briefs and is gitignored. Read it for context, never copy from it and never commit it or quote it.

If a task risks breaking one of these rules, stop and ask.

## Architecture (big picture)

Data flows through three layers, and the solver only sees the last one:

```
Source tables (SAP style CSV/Parquet/warehouse) -> SourceAdapter -> Canonical dataset (Pydantic + pandera) -> Solver input
```

* `SourceAdapter` is a Python `Protocol`. v1 has CSV and Parquet adapters; BigQuery is a documented stub only. Source tables use standard SAP names (`MARA`, `MCHB` with `VFDAT` and `HSDAT`, `MBEW`, ...) plus custom `Z` tables (`ZCHANNEL`, `ZCHANNEL_RULE`, `ZSELLIN`, `ZSELLOUT`, `ZABC`, `ZPARAM`). Never let the solver read raw ERP tables.
* **Decision index is the lot** (material x plant x expiry bucket, bucketed by month), not material x plant. This keeps remaining shelf life rules exact without per batch variables (ADR 003).
* **Elimination before modeling**: pairs that fail remaining shelf life or brand tier rules are dropped from the admissible set, and each drop keeps a reason code. The Why panel reads these codes.
* **Solver** sits behind a `Solver` protocol (PuLP with HiGHS default, CBC fallback). `SolveResult` always carries status, objective, MIP gap, time and time limit, and the API returns them unchanged.
* **Two phase lexicographic objective**: phase 1 maximizes the SKU score, phase 2 maximizes net value with phase 1 fixed within epsilon (1% default). Unallocated units count as destroyed.
* Coverage and push constraints use the tight form (binary times the smallest valid bound), never a generic Big M (ADR 004). Score weights and all rule values live in `ZPARAM` and scenario yaml, never in code.
* **Explainability** is rule trace plus on demand counterfactual re solve (warm start, 10 s limit), not MILP duals. Rule trace reads the slack of every named constraint, so keep constraint names stable and meaningful.
* The **baseline** is a planner proxy, not a strawman and not an expert solver: it applies a short list of rules by hand (shelf life, brand tier, channel capacity) and ignores the rest (assortment, coverage, push). The full constraint checker audits it and lists violations per named constraint. KPIs show its raw value, its violations and its compliant value. A property test asserts the ADR 005 statement on 50 neutral seeds: optimizer score is at least the compliant baseline score, and when the baseline score is within epsilon of the optimizer's, optimizer net value is at least the baseline's. See `docs/adr/0005-planner-proxy-baseline.md`.
* **Demo mode**: `make precompute` runs the real solver on each seeded scenario and writes `data/precomputed/*.json` (results, KPIs, traces, top counterfactuals). The frontend reads that JSON by default and switches to the live API if `VITE_API_URL` answers a health check. A banner shows "Cached results" or "Live solver".
* TypeScript API types are generated from the FastAPI OpenAPI schema (`openapi-typescript`) and CI fails on drift. There is no shared schema package.
* Seeds and parameters are fixed in `data/scenarios/*.yaml`. Every run, test, screenshot and video frame must be reproducible, and hero elements carry stable `data-testid` values for the Remotion and Playwright work.

## Design system

`design_system/` is the single visual source for the web app, the Remotion video and generated docs. Read `design_system/DESIGN_SYSTEM.md` before any UI, video or doc styling work.

* `design_system/tokens/tokens.json` is the source of truth. Never hand edit `design_system/dist/`. After a token change run `node design_system/scripts/build.mjs` and commit `dist/` with it.
* Never hard code a color, font size, radius or duration. Use `--rs-*` CSS variables, `.rs-text-*` classes, or `tokens` from `design_system/dist/tokens.ts`.
* **Light is the default theme** for the app, the demo and the video. Dark is a switch (`data-theme` on the root, stored as `reshelf-theme`). Remotion compositions take a `theme` prop that defaults to `light` and read `tokens.video.theme[mode]` and `tokens.semantic[mode]`.
* Fixed color pairs: greedy baseline is grey (`compare.baseline`), optimizer is teal (`compare.optimizer`), euro cost of a rule is amber (`compare.delta-cost`), AI drafted content is dashed indigo on lilac (`ai.*`). Solver content and AI content must never look alike.
* Every screen with numbers shows a "Simulated data" badge. Every compared KPI says "against the greedy baseline".
* Use the reserved `data-testid` names listed in section 6.4 of the spec for hero elements.
* Images: generated banners by default, otherwise only free to use sources listed in `design_system/IMAGERY.md`, each recorded in `design_system/assets/CREDITS.md`. Never reuse a mockup image.
* The `_private/Figma` mockups were a starting point. Adapt their patterns, do not copy screens pixel for pixel, and do not carry over any name, logo, label or text from them.
* **Workflow**: edit `design_system/tokens/tokens.json` → run `node design_system/scripts/build.mjs` → commit both `tokens.json` and `dist/` together. Never hand edit `dist/` files. The same build also reads `components/components.css` (components and layout), `assets/icons.json` (icons) and rebuilds `product_management/recap.html` from `recap.src.html`.
* **Nothing visual lives only in a page.** New colors, sizes, icons, components, logo variants and layout rules go into the design system first (see sections 6.5 and 12 to 14 of the spec). Use `rs-*` component classes and the icon sprite. Pages are fluid, not a centered column.
* **Color conventions**: brand tiers (luxury/premium/mass) use violet, blue and teal, never mixed. Chart series and channel colors use the categorical order defined in `tokens.json`. WCAG contrast checked: avoid teal.400 for small text (4.33:1 is below the 4.5:1 minimum).
* **Remotion**: import `{ tokens } from 'design_system/dist/tokens'`. Use `tokens.video.theme[props.theme ?? 'light']` for scene colors and `tokens.semantic[props.theme ?? 'light']` for UI inside components. Default mode is `light`.

## Git commits

Do not add `Co-Authored-By:` attribution lines to commit messages. Sign commits with the user's own git user config only.

## Working agreements

* Start in plan mode for new phases. State what will be built, what will not, and how success is checked. Build in small vertical slices that end with tests green.
* Proposals follow: option, upside, downside, recommendation. Distinguish facts, assumptions and open questions. Do not invent requirements.
* Prose written for Nils avoids hyphens and dashes as punctuation. Rephrase instead. Tables and short bullets are preferred.
* Every constraint gets a pytest (feasible and violating case). Cut order if late: deep dive page, Excel export polish, live API, 10k benchmark row. Never cut: compare, Why panel, tests, README.
* Conventional commits, small PRs, one ADR per major choice in `docs/adr/`.
* **Errors are shown, never swallowed.** No empty catch, no client side workaround for a failed request. The Vite dev server proxies `/api`. A failed panel shows an inline error with a retry.
* **One source of truth per screen.** The UI never recomputes a number and never mixes sources. Results come from the API or the precomputed JSON.
* **Docs from code where possible.** `docs/model.md` is generated from the named constraint registry (`make model-doc`) and CI fails on drift. Never commit LP files, logs or machine suffixed copies. Use `make export-lp` into `tmp/`.
* **Tests beyond constraints.** Score hierarchy, result invariants (no negative quantity, no line above supply, totals reconcile), parameter validation and explicit defaults for missing data each have a test (`2_test_scenarios.md` section 14).
* **Earlier prototype review.** A prior prototype outside this repo was reviewed once on 2026-10-25 for generic ideas only. Treat it like `_private/`: read for context, never copy names, data, values or code, and do not mention it in any doc.

## Product management docs

`product_management/` is part of the portfolio and is numbered for reading order (`1_discovery/`, `2_strategy/`, then `product_statement/`, `differentiators/`, `GTM_strategy/`). Conventions:

* Every claim about a competitor or regulation is tagged **[V]** verified on a public source, **[K]** background knowledge, or **[H]** hypothesis. Do not upgrade a tag without a source.
* Figures are illustrative or hypotheses. Mark evidence level at the top of each document.
* Decisions already made: repo license is **all rights reserved**; first revenue model is a **free pilot for a reference customer, then paid pilots**.