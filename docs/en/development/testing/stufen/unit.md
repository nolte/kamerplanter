# Unit Tests

Unit tests verify a **single function or class in isolation** — without a database, network, or browser. They are the base of the [test pyramid](index.md): the most numerous, the fastest, the most precise in their error messages.

## What this level verifies

- **Backend business logic:** pure calculations and engine rules (VPD via Tetens, GDD accumulation, EC budget), adapter logic (GBIF/Perenual enrichment).
- **Frontend logic without a DOM:** Redux slices (reducers, actions) and custom hooks that are testable as pure functions.

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
