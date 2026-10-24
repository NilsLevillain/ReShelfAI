# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## State of the repo

Pre code. Only planning documents exist: `docs/war_plan.md` (execution plan, source of truth for architecture and the 8 week schedule), `product_management/` (discovery, strategy, metrics), and empty scaffold folders (`apps/api`, `apps/web`, `data/*`, `infra`, `video`). Check the week table in `docs/war_plan.md` section 7 to see what is in scope now and what is explicitly "not built" yet.

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
* A **greedy baseline** uses the same constraint checker as the optimizer so the comparison is fair. A property test asserts optimizer value is at least greedy value on any seeded dataset.
* **Demo mode**: `make precompute` runs the real solver on each seeded scenario and writes `data/precomputed/*.json` (results, KPIs, traces, top counterfactuals). The frontend reads that JSON by default and switches to the live API if `VITE_API_URL` answers a health check. A banner shows "Cached results" or "Live solver".
* TypeScript API types are generated from the FastAPI OpenAPI schema (`openapi-typescript`) and CI fails on drift. There is no shared schema package.
* Seeds and parameters are fixed in `data/scenarios/*.yaml`. Every run, test, screenshot and video frame must be reproducible, and hero elements carry stable `data-testid` values for the Remotion and Playwright work.

## Working agreements

* Start in plan mode for new phases. State what will be built, what will not, and how success is checked. Build in small vertical slices that end with tests green.
* Proposals follow: option, upside, downside, recommendation. Distinguish facts, assumptions and open questions. Do not invent requirements.
* Prose written for Nils avoids hyphens and dashes as punctuation. Rephrase instead. Tables and short bullets are preferred.
* Every constraint gets a pytest (feasible and violating case). Cut order if late: deep dive page, Excel export polish, live API, 10k benchmark row. Never cut: compare, Why panel, tests, README.
* Conventional commits, small PRs, one ADR per major choice in `docs/adr/`.

## Product management docs

`product_management/` is part of the portfolio and is numbered for reading order (`1_discovery/`, `2_strategy/`, then `product_statement/`, `differentiators/`, `GTM_strategy/`). Conventions:

* Every claim about a competitor or regulation is tagged **[V]** verified on a public source, **[K]** background knowledge, or **[H]** hypothesis. Do not upgrade a tag without a source.
* Figures are illustrative or hypotheses. Mark evidence level at the top of each document.
* Decisions already made: repo license is **all rights reserved**; first revenue model is a **free pilot for a reference customer, then paid pilots**.