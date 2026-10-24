# ADR 001: Tech Stack

**Date:** 2026-10-25  
**Status:** Accepted

## Decision

Reshelf uses a modern Python + React stack:

* **Backend:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic
* **Solver:** PuLP (MILP framework), HiGHS (primary), CBC (fallback)
* **Frontend:** React 18+, TypeScript, Vite, Tailwind CSS, shadcn/ui
* **Package managers:** `uv` for Python, `pnpm` for JavaScript
* **Database:** SQLite for v1 (Postgres ready with Alembic)
* **Testing:** pytest (Python), Vitest + Testing Library (web), Playwright (e2e)
* **CI/CD:** GitHub Actions, Docker, Cloud Run (or Render as fallback)

## Rationale

| Layer | Choice | Why | Rejected alternative |
|-------|--------|-----|----------------------|
| **Python** | 3.11+ | Modern async/type hints, broad data science support | Python 3.9 (too old), 3.13 (not stable yet) |
| **API** | FastAPI | Type-driven via Pydantic, built-in OpenAPI schema, excellent async | Django (too heavy), Flask (too minimal) |
| **ORM** | SQLAlchemy 2 | Modern syntax, async support, portable to Postgres | raw SQL (error-prone), Tortoise-ORM (smaller ecosystem) |
| **Solver** | PuLP + HiGHS | Python native, well-documented, reliable on medium-scale MILP | Pyomo (heavier), cvxpy (convex only), direct C bindings (less portable) |
| **Frontend** | React + TypeScript | Battle-tested, excellent tooling, large ecosystem for tables and charts | Vue (smaller community), Svelte (lighter but less adoption), Alpine (too minimal) |
| **Build tool** | Vite | Instant HMR, fast builds, ES modules native, smaller output than Webpack | Webpack (slower), Next.js (ties us to React + limits API choices) |
| **UI library** | shadcn/ui | Headless, full control, Tailwind integrated, no component distribution cost | Material-UI (heavier), Chakra (more opinioned), Bootstrap (dated) |
| **Package manager** | `uv` (Python), `pnpm` (JS) | Fast, lockfile generation, modern workflows | pip + venv (slow), npm (inefficient installs), poetry (slower than uv) |
| **Database** | SQLite v1 | Zero ops, perfect for POC, no schema boilerplate | Postgres immediately (unnecessary complexity), in-memory (not persistent) |
| **Testing** | pytest + Vitest | Simple syntax, parallel execution, great pytest plugins (hypothesis for properties) | unittest (verbose), Jest (slower) |

## Consequences

**Upside:**
* Type safety end-to-end (FastAPI → TypeScript via OpenAPI code generation).
* Modern async throughout (no threading complexity).
* Excellent local development experience (Vite HMR, auto-reload, no Docker required for week 1–6).
* Large ecosystem for optimization (PuLP is the standard in Python).
* Small bundle size and fast page load (Vite + lazy loading).

**Downside:**
* PuLP integer programs are slower than commercial solvers (acceptable for POC, noted in limitations).
* Vite ESM setup can be fragile with certain legacy dependencies (unlikely here).
* FastAPI boilerplate is minimal, but schema-first design requires discipline.

## Migration path

Postgres: swap SQLite connection string, run Alembic migrations, no code change.  
Solver: PuLP interface is generic; swapping HiGHS → Gurobi is a config line if budget allows later.  
Frontend: Vite and React are stable; no lock-in to Vercel or framework bundles.

## Notes

* TS types generated from FastAPI OpenAPI schema (`openapi-typescript`), not a shared package. CI fails if they drift.
* `devcontainer.json` ensures reproducibility; no "works on my machine" issues.
* Stack aligns with "single source of truth, minimal glue" principle from the war plan.
