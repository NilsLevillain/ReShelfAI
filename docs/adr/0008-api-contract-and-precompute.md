# ADR 008: One JSON contract for the API and the precomputed demo

**Status**: Accepted (2026-11-05)
**Deciders**: Nils
**Related**: `docs/war_plan.md` sections 6.2 and 6.5, `reshelf/api_models.py`, `reshelf/pipeline.py`, `reshelf/precompute.py`, `reshelf/api.py`, `reshelf/db.py`

> Evidence level: design decision. The demo world (30 SKUs, 5 channels) solved to optimal in under a second per scenario on the author's machine, and the counterfactual re solves with it. Larger worlds are unmeasured, the benchmark run was deferred.

## Context

Week 4 builds a web app that reads either `data/precomputed/*.json` (demo mode) or a live API. Two producers must give the same shape, or the UI would mix sources.

## Decisions

| Topic | Choice | Reason |
|---|---|---|
| Contract | One Pydantic model, `ScenarioResult`, written to disk by the precompute and returned by the API | One source of truth per screen. OpenAPI types come from it |
| Line ids | String `lot label,channel`, the id of the rule trace | Tuple keys cannot be JSON keys. The trace and the lines share the id |
| Solver fields | Status, objective, MIP gap, time and time limit pass through unchanged | War plan 5.5 |
| Demo world | 30 SKUs and 5 channels of each seeded scenario | Optimal in about a second, so every counterfactual is real. The UI labels it a demo world. Larger worlds are a later decision, after the benchmark |
| Reproducibility | Same seed gives the same plan, KPIs, trace and counterfactual costs. Only `time_s` differs between runs and tests exclude it. No timestamps in the files | Files in git do not change on every run |
| Persistence | SQLite through SQLAlchemy 2. A scenario row keeps its spec, a result row keeps the `ScenarioResult` as JSON text. Tables come from `create_all` | A payload change needs no table migration. Postgres needs only a new URL |
| Counterfactual endpoint | Rebuilds the seeded world and repeats the base solve, then re solves with the relaxed rule | The stored result keeps no solver state. The world is deterministic, and the call is cheap at demo size |
| Scenario edits | A scenario spec may override keys of the scenario `params` block. Unknown keys are rejected | The parameter editor of week 5 needs it, and a typo must not pass silently |
| Errors | Plain sentence in `detail`, matching status code | War plan 5.9 |

## Consequences

* The counterfactual endpoint solves twice. At 2,000 SKUs that would be too slow, so it needs stored solver state or a job queue then.
* Alembic is a dependency but has no migration yet. Add one before the first deployed database.
* Stock endpoints (week 4) and Excel export (week 5) are not built.
