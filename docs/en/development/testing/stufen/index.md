# Test Levels

Kamerplanter organizes its automated tests into four **test levels**. Each level has its own focus, its own tooling, and its own runtime characteristic. Together they form a **test pyramid**: the lower the level, the more tests run and the faster they are; the higher, the fewer tests and the more realistic the scenario.

| Level | Focus | Tooling | Location | Runs in CI |
|-------|-------|---------|----------|------------|
| [Unit](unit.md) | Individual functions/classes in isolation | pytest / vitest | `src/backend/tests/unit/`, `src/frontend/src/test/{store,hooks}/` | Yes |
| [Integration](integration.md) | Interplay with a real database/API | pytest | `src/backend/tests/integration/`, `…/api/` | Yes (skipped when no DB) |
| [Component](component.md) | React components in the rendered DOM | vitest + Testing Library | `src/frontend/src/test/components/` | Yes |
| [E2E](e2e.md) | Complete user workflows in a real browser | Selenium | `tests/e2e/` | No (local / on demand) |

!!! tip "Practical instructions"
    How to install and run each suite is documented in detail in the [testing concept](../index.md) — organized there by **tooling**. These pages describe *what* each level covers and *why*.

## The pyramid

- **Base — Unit:** Many, very fast tests with no external dependencies. They verify business logic (VPD, GDD, EC calculations, reducers, hooks) in isolation and give feedback in seconds.
- **Middle — Integration & Component:** Fewer tests that verify real interplay — on the backend against a running ArangoDB, on the frontend against the rendered DOM with a mocked API (MSW).
- **Top — E2E:** Few, slow tests that drive a complete user workflow through a real browser, frontend, backend, and database.

## Which level when?

- **New business logic** (calculation, engine, service) → at least one **unit test**.
- **New repository/DB access or API endpoint** → an **integration test**.
- **New or changed React component** → a **component test**.
- **New end-to-end workflow** (e.g. login → create → save) → an **E2E test**.

Rule of thumb: write the test at the **lowest** level that still reliably catches the failure. That keeps the suite fast and the error messages precise.
