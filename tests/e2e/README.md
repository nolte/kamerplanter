# E2E test suite — selection & identifiability

Selenium (Remote WebDriver / Grid) + pytest, Page-Object pattern. The suite runs
locally against the containerised stack (`scripts/run-e2e.sh` / `task test:e2e`)
**and in CI** (see below).

## CI

Two GitHub Actions workflows wrap the same compose stack as local runs
(`docker-compose.e2e.yml` stays the single source of truth for the test
environment; `scripts/run-e2e.sh` is the shared entrypoint):

- **`e2e-smoke.yml`** — the fast smoke profile (`-m smoke`) on path-filtered
  pull requests, pushes to `develop`, and manual dispatch. **Non-required**
  check by design: `static` stays the only required check until the flake
  behaviour of the E2E jobs is known.
- **`e2e-nightly.yml`** — the full suite, nightly (01:30 UTC) as a matrix over
  the compose profiles `light`, `full`, `mobile`, `tablet`, `full-mobile`
  (manual dispatch can select a single profile). A failing night opens a
  GitHub issue labelled `e2e-nightly`; while one is open, further failures
  only append a comment.

Both jobs always upload `test-reports/e2e/**` (protocol, screenshots,
container logs) as workflow artifacts and write a job summary from the
generated protocol. Image builds are layer-cached via the
`docker-compose.e2e.ci.yml` overlay (BuildKit `gha` cache backend), which CI
enables through `E2E_COMPOSE_OVERLAYS` — local runs never load it.

## Selecting which tests to run after a change

Tests are **machine-selectable** along two independent axes plus the legacy
suites, so a code/feature change maps to the affected tests without hand-marking
700+ functions. Markers are derived automatically at collection time
(`conftest.py::pytest_collection_modifyitems`) and enforced with
`--strict-markers` (`pytest.ini`).

### 1. REQ axis — `req<NNN>` (auto-derived, no annotation)

Derived from the `test_req<NNN>_*.py` file name. Nothing to annotate.

```bash
pytest -m req004          # everything under test_req004_*.py
pytest -m "req007 or req008"
```

### 2. Feature axis — semantic, cross-cutting to REQ IDs

A module opts in via a module-level `FEATURES` tuple. This axis is what makes
selection robust when a feature spans several REQ files (fertilizer lives across
several `test_req004_*.py` files; harvest spans REQ-007 **and** REQ-008; a
core-lifecycle journey touches several REQs).

```python
# in a test module, after the imports:
FEATURES = ("nutrient",)                        # single feature
FEATURES = ("watering", "nutrient")             # cross-cutting journey file
```

```bash
pytest -m watering        # watering-log + the watering steps of the journey
pytest -m harvest         # spans test_req007_*.py and test_req008_*.py
pytest -m "nutrient and smoke"
```

Registered feature markers (`conftest.py::KNOWN_FEATURE_MARKERS`):

| Marker | Scope |
|---|---|
| `plant` | plant instance capture & lifecycle (Pflanzenerfassung) |
| `watering` | watering log / irrigation events (Gießen/Bewässerung) |
| `nutrient` | fertilizer, nutrient plans, feeding events, EC (Düngen/Dünger) |
| `harvest` | harvest & post-harvest management (Ernte) |
| `calendar` | calendar, sowing calendar, season overview (Aussaat/Kalender) |
| `journey` | core-lifecycle happy-path journey (auto-applied to `*_core_lifecycle_journey.py`) |

Declaring a `FEATURES` value outside this set is a **hard collection error**
(typo guard). To add a new feature marker, register it in `KNOWN_FEATURE_MARKERS`
first, then add the `FEATURES` tuple to the relevant modules.

`pytest --markers` lists every registered marker (feature axis, one `req<NNN>`
per file, plus the legacy `smoke` / `core_crud` / `requires_auth` /
`requires_desktop`).

### 3. Legacy suites (unchanged)

```bash
task test:e2e:smoke       # -m smoke  (fast, ~2 min)
docker compose -f docker-compose.e2e.yml --profile core-crud run --rm e2e-core-crud
```

## TC-ID traceability

Each test's docstring TC-ID (e.g. `TC-REQ-004-W001`) is lifted into the standard
junit `user_properties` channel as a `tc_id` property
(`conftest.py::_record_tc_id`), so downstream tooling — and the generated
markdown protocol — can consume it. This is in addition to the bespoke protocol
extraction in `protocol_plugin.py`.

> Note: the *test-declared* TC-IDs (`…-W001`, `…-PI-005`) currently drift from
> the spec IDs (`TC-004-NNN`) in `spec/e2e-testcases/`. See the coverage audit
> below; a full traceability reconciliation is tracked as a follow-up.

## Core-function coverage

`.audits/e2e-core-function-coverage/2026-07-14-core-function-coverage.md` maps
the implemented Selenium tests against the spec test cases for the five core
functions and names the real gaps (Spec-vs-implementation — complementary to
`spec/e2e-testcases/COVERAGE-REPORT.md`, which is Spec-vs-Spec).
