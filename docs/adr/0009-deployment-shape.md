# ADR 009: Deployment shape

Status: accepted (2026-11-06). Not yet deployed anywhere.

## Context
Reshelf has a FastAPI solver API and a static React app. The demo must start cold and work even when the API is down. A real deploy needs credentials that do not exist yet.

## Decision
* Two images built from the repo root: `infra/api.Dockerfile` (uv, uvicorn, SQLite on a volume at `/data`) and `infra/web.Dockerfile` (pnpm build, nginx).
* nginx serves the static app and proxies `/api/` to the `api` service. The web image is built with `VITE_API_URL=/api`, so the app probes `/api/health` and switches from cached results to the live solver when it answers.
* The precomputed JSON is bundled into the web build, so the web image alone is a working demo.
* `infra/docker-compose.yml` runs both. Web on port 8080, API on port 8000.
* CI builds both images and does not push. A Cloud Run deploy of the API and a static host for the web app are documented in the README and not wired.

## Consequences
* Upside: one command to run, a static fallback, no secrets in the repo.
* Downside: SQLite on a volume fits one instance only. Tables come from `create_all`, so a deployed database needs an Alembic migration first.
* The images were not built on the author's machine (no Docker installed). CI is the first build.

## Note on numbering
There is no ADR 002 in the repo. The sequence skips it and no record explains why.
