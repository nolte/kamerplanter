# E2E Tests

End-to-end tests (E2E) verify **complete user workflows in a real browser** — from the click through frontend and backend down to the database. They sit at the top of the [test pyramid](index.md): the least numerous, the slowest, but the most realistic. E2E tests use Selenium WebDriver with the page-object pattern and produce Markdown test protocols with screenshots (internal reference: NFR-008). <!-- NFR-008 -->

## What this level verifies

- **End-to-end flows:** e.g. login → create record → save → find again, across all layers.
- **Real interplay:** real browser, real frontend (nginx), real backend, real database.

## Tooling & location

| | Value |
|---|---|
| Tooling | Selenium WebDriver, pytest, page-object pattern |
| Location | `tests/e2e/` |
| Locator | `data-testid` attributes (never CSS structure) |

!!! info "No CI job — deliberately local / on demand"
    The E2E suite does **not** run automatically in the CI pipeline; it runs locally or on demand via a dedicated Docker Compose stack. This is a deliberate decision (runtime, browser infrastructure), not a gap.

## Running

```bash
# Local against a running app (Chrome headless, localhost:5173)
pytest tests/e2e/ -v

# Dedicated, isolated Docker stack (app + Selenium Grid)
./scripts/run-e2e.sh
```

Reports and screenshots land under `test-reports/<timestamp>/`. The full stack, fixtures, and protocol format are in the [testing concept → E2E Tests](../index.md#e2e-tests-selenium).

## Conventions

- Every page object inherits from `BasePage` and encapsulates exactly one screen.
- Address elements exclusively via `data-testid` locators — never via brittle CSS paths.
- Take screenshots explicitly at meaningful checkpoints; on failure they are captured automatically.
