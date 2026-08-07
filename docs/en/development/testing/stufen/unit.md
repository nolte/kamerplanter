# Unit Tests

Unit tests verify a **single function or class in isolation** — without a database, network, or browser. They are the base of the [test pyramid](index.md): the most numerous, the fastest, the most precise in their error messages.

## What this level verifies

- **Backend business logic:** pure calculations and engine rules (VPD via Tetens, GDD accumulation, EC budget), adapter logic (GBIF/Perenual enrichment).
- **Frontend logic without a DOM:** Redux slices (reducers, actions) and custom hooks that are testable as pure functions.

## Tested areas at a glance

| Area | Tested elements | Extent |
|------|-----------------|--------|
| Domain logic (backend) | VPD/GDD/EC calculations, phase engine, karenz gate, companion/crop rotation | extensive |
| Repositories (backend) | ArangoDB access, graph queries | extensive |
| Migrations | schema migration framework | extensive |
| Celery tasks | background jobs, retention/anonymization | moderate |
| Adapters | weather (DWD/Open-Meteo/OWM/NASA), GBIF, Perenual, PlantNet, Home Assistant, notifications | moderate |
| Frontend | Redux slices, custom hooks | moderate |

## Tooling & location

| | Backend | Frontend |
|---|---|---|
| Tooling | pytest (`asyncio_mode = "auto"`) | vitest |
| Location | `src/backend/tests/unit/` | `src/frontend/src/test/store/`, `…/hooks/` |
| Dependencies | none external | none (no provider wrapper needed) |

## Running

```bash
# Backend
cd src/backend && pytest tests/unit/ -v

# Frontend
cd src/frontend && npm test
```

Full prerequisites and patterns are in the [testing concept → Backend Tests](../index.md#backend-tests-pytest) and [→ Frontend Tests](../index.md#frontend-tests-vitest).

## Conventions

- Engine tests instantiate the class directly and mock **no** repositories.
- Service tests mock the repository (`AsyncMock(spec=…)`).
- Redux slice tests run entirely without React — call the reducer as a pure function.
- Every new feature needs at least one unit test for its business logic.
- **No datastore access.** A backend unit test that reaches ArangoDB, TimescaleDB or
  Valkey through a provider in `app/common/dependencies.py` aborts immediately —
  with a message naming the provider chain (guard: `tests/support/db_guard.py`).
  The same applies to `tests/api/`.

!!! warning "Why this is a guard rather than just a convention"
    With the dev stack running, `localhost:8529` answers. The test then goes green
    locally while reading and writing the dev database, and only fails in CI where
    nothing is listening — where the diagnosis costs about 18 seconds of connection
    timeout per affected call. A test that genuinely needs a database belongs in
    `tests/integration/`. The emergency exit is the marker
    `@pytest.mark.allow_db_connection("<reason>")` — with a mandatory reason, so the
    exceptions stay countable.
