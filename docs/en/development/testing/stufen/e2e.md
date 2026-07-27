# E2E Tests

End-to-end tests (E2E) verify **complete user workflows in a real browser** — from the click through frontend and backend down to the database. They sit at the top of the [test pyramid](index.md): the least numerous, the slowest, but the most realistic. E2E tests use Selenium WebDriver with the page-object pattern and produce Markdown test protocols with screenshots (internal reference: NFR-008). <!-- NFR-008 -->

## What this level verifies

- **End-to-end flows:** e.g. login → create record → save → find again, across all layers.
- **Real interplay:** real browser, real frontend (nginx), real backend, real database.

## Tested areas at a glance

E2E suites are organized by requirement (REQ). Grouped thematically:

| Area | Example workflows | Extent |
|------|-------------------|--------|
| Master data & lifecycle | species/cultivars, phase control, planting run | extensive |
| Watering & feeding | nutrient solution, feeding, tank management | moderate |
| Tasks & care | task queue, care dashboard, reminders | moderate |
| Harvest & post-harvest | harvest readiness, harvest list, post-harvest | moderate |
| Plant protection | pests/diseases, photo recognition, diagnosis | moderate |
| Platform | login, tenants, privacy, light mode | extensive |
| Others | dashboard, calendar, onboarding, companion planting, notifications, AI assistant, print views | moderate |

!!! note "Curated test-case specifications"
    Detailed, numbered test cases live as Markdown documents under `spec/e2e-testcases/` (`TC-REQ-*`, `TC-NFR-*`) alongside `COVERAGE-REPORT.md`. Per requirement they describe preconditions, steps, and expected results.

## Tooling & location

| | Value |
|---|---|
| Tooling | Selenium WebDriver, pytest, page-object pattern |
| Location | `tests/e2e/` |
| Locator | `data-testid` attributes (never CSS structure) |

!!! info "CI: smoke gate per PR + nightly full run"
    The suite also runs in GitHub Actions — using the same Docker Compose stack as local runs: the `e2e-smoke` workflow runs the fast smoke profile on every pull request and on pushes to `develop`. Since ADR-011 it is a **required** check on `develop`, alongside `static / Static CI Tests`. Whether the suite actually runs is decided by a job inside the workflow rather than by a path filter on the trigger: a required workflow skipped by path filtering never reports a result and blocks the pull request indefinitely. The `e2e-nightly` workflow runs the complete suite nightly as a matrix over the compose profiles `light`, `full`, `mobile`, `tablet`, and `full-mobile`; a failing run no longer opens a GitHub issue — the run status, the per-profile rendered check run, and the artifacts carry everything the automatic issue merely restated. Test protocol, screenshots, and container logs are attached to every run as workflow artifacts.

## CI test reports

Every run writes a JUnit XML report (`junit-<profile>.xml`) alongside the protocol and screenshots, carrying each test's TC-ID as a `tc_id` property. In GitHub Actions, the `e2e-smoke` workflow (per pull request) and each profile in the `e2e-nightly` workflow additionally render this report via `dorny/test-reporter` as a GitHub check run and a job-summary table — with the concrete failure message (assertion text plus a short traceback) per failed test, instead of just a green/red overall status.

!!! note "Fork pull requests: no rendered check"
    On pull requests from forks, the render step cannot create a check run with the restricted `GITHUB_TOKEN` and is skipped (`continue-on-error`). `e2e-smoke` detects this and then writes the result overview plus the failed tests from the test protocol into the job summary; otherwise the job summary is only a pointer at the artifact, so the same numbers do not appear twice. The `junit-*.xml` artifact is available either way.

The rendered check run is a CI convenience — it does not replace the Markdown test protocol (`protokoll.md`) with its embedded screenshots, which remains the human-readable audit trail (NFR-008 §4.4).

## Running

```bash
# Local against a running app (Chrome headless, localhost:5173)
pytest tests/e2e/ -v

# Dedicated, isolated Docker stack (app + Selenium Grid)
./scripts/run-e2e.sh                    # full light suite
./scripts/run-e2e.sh --smoke            # smoke suite (~7 min)
./scripts/run-e2e.sh --profile mobile   # a single compose profile
```

Reports and screenshots land under `test-reports/e2e/<timestamp>/`, including the JUnit XML report — see [CI test reports](#ci-test-reports). The full stack, fixtures, and protocol format are in the [testing concept → E2E Tests](../index.md#e2e-tests-selenium).

## Conventions

- Every page object inherits from `BasePage` and encapsulates exactly one screen.
- Address elements exclusively via `data-testid` locators — never via brittle CSS paths.
- Take screenshots explicitly at meaningful checkpoints; on failure they are captured automatically.
