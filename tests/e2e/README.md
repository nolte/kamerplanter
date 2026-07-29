# E2E test suite — selection & identifiability

Selenium (Remote WebDriver / Grid) + pytest, Page-Object pattern. The suite runs
locally against the containerised stack (`scripts/run-e2e.sh` / `task test:e2e`)
**and in CI** (see below).

> **Where the `spec/project/e2e-test-automation` and `spec/project/e2e-test-stability`
> specs live:** not in this repository. Test files and page objects cite them by
> those paths, but they are owned by the shared `nolte-engineering` plugin and
> only exist in its checkout — by default
> `~/repos/github/claude-shared/spec/project/<name>/de.md` (override the checkout
> location with `NOLTE_CLAUDE_SHARED`; see the plugin-adoption section of the
> repository `CLAUDE.md`). Read them from there rather than improvising a
> baseline. Repository-local specs referenced below (`spec/e2e-testcases/`,
> `.audits/`) are exactly that: local.

## CI

Two GitHub Actions workflows wrap the same compose stack as local runs
(`docker-compose.e2e.yml` stays the single source of truth for the test
environment; `scripts/run-e2e.sh` is the shared entrypoint):

- **`e2e-smoke.yml`** — the fast smoke profile (`-m smoke`) on every pull
  request, pushes to `develop`, and manual dispatch. **Advisory** check: it was
  required on `develop` from ADR-011 / #793 until 2026-07-29, when the context
  was dropped over merge latency (see the 2026-07-29 addendum in ADR-011). It
  still reports on every pull request — read it before merging — but it no
  longer blocks. Its `pull_request` trigger still carries no `paths:` filter and
  the run/skip decision still lives in the workflow's `changes` job, so re-arming
  the gate stays a one-line change in `.github/settings.yml`.
- **`e2e-nightly.yml`** — the full suite, nightly (01:30 UTC) as a matrix over
  the compose profiles `light`, `full`, `mobile`, `tablet`, `full-mobile`
  (manual dispatch can select a single profile). A failing night files **no**
  GitHub issue: the run status, the per-profile rendered check runs and the
  uploaded artifacts carry everything the auto-filed issues used to restate.

Both jobs always upload `test-reports/e2e/**` (JUnit XML, protocol,
screenshots, container logs) as workflow artifacts (`e2e-smoke-reports` /
`e2e-nightly-reports-<profile>`) and write a job summary. That summary is
deliberately only a pointer at the artifact whenever the rendered report below
exists — totals and failed test names come from the report, and printing them
again from `protokoll.md` produced every result twice. `e2e-smoke` still falls
back to the full protocol excerpt when the rendering did not happen (fork PRs,
see below). Image builds are layer-cached via the `docker-compose.e2e.ci.yml`
overlay (BuildKit `gha` cache backend), which CI enables through
`E2E_COMPOSE_OVERLAYS` — local runs never load it.

### JUnit XML + rendered test reports

Every runner service in `docker-compose.e2e.yml` passes pytest
`--junitxml=junit-<profile>.xml` (`junit-default.xml`, `junit-smoke.xml`,
`junit-core-crud.xml`, `junit-full.xml`, `junit-mobile.xml`,
`junit-tablet.xml`, `junit-full-mobile.xml`, `junit-full-tablet.xml`). The
protocol plugin relocates the finished file — controller-only under the
xdist-parallel runners (`-n 4 --dist=loadfile`), via an `atexit` hook — into
the run's timestamped report dir, so it ends up at
`test-reports/e2e/<timestamp>/junit-<profile>.xml` alongside `protokoll.md`.
Locally, `scripts/run-e2e.sh` prints the resulting filename in its final
"Reports:" summary. Each `<testcase>` carries the `tc_id` `user_property`
described below.

Both CI workflows render that XML with `dorny/test-reporter` into a GitHub
check run plus a job-summary table with concrete per-test failure messages
(assertion text + a short traceback) — `e2e-smoke` publishes a single
"E2E smoke report" check, `e2e-nightly` publishes one
"E2E nightly — `<profile>`" check per matrix profile. Both workflows request
only `checks: write` — no `issues: write`, no `pull-requests: write`, no
`pull_request_target`.

> **Fork PRs:** the render step (`continue-on-error: true`) cannot create a
> check run with a fork PR's read-only `GITHUB_TOKEN`, so no rendered check
> appears there. `e2e-smoke` detects this via `steps.report.outcome` and writes
> the full protocol excerpt (result overview + failed tests) into the job
> summary instead, so the results stay visible; the raw `junit-*.xml` is in the
> run's artifact either way.

The rendered check run and job summary are a CI convenience layer on top of
the existing reporting — they do **not** replace the Markdown protocol
(`protokoll.md`) and screenshots, which stay the human-facing audit trail
(NFR-008 §4.4).

## Waiting: how a test knows the page is there

`BasePage.wait_for_loading_complete()` waits for the **absence** of
`[data-testid='loading-skeleton']`. That is a weak signal and, on its own, not a
valid assertion: an absence poll cannot tell "the skeleton has not mounted yet"
from "the skeleton is gone because loading finished", so right after a
`navigate()` it returns *immediately* while the route's lazily-imported chunk is
still resolving (`e2e-test-stability` §D). It is kept only because ~340 call
sites pair it with a durable wait that does the real work.

Use the branch-aware helpers instead. They key on the **presence** of the content
the caller is about to read, and they report **which** settled state the route
reached, so a test asserts an outcome instead of accepting any of them:

| Helper | Use it for |
|---|---|
| `wait_for_content(page, what)` | the everyday case: "navigate, then read the page". Fails loudly, quoting the app's own error text, when an error surface won instead |
| `wait_for_page_settled(page, what)` | the test legitimately accepts several outcomes and wants to branch on `state.branch` |
| `wait_for_settled({name: locator, …}, what)` | any other disjunction (a tab panel's table **or** its `EmptyState`) |
| `navigate_direct(path, settled)` | a deliberately invalid key, where no `open()` accepts the path. The settle locator is a **mandatory** parameter |
| `require_branch(state, expected, what)` | make the accepted outcome explicit at the point of the read |
| `wait_for_skeleton_gone(what)` | the *legal* skeleton-absence poll — only after a settled branch is present, which is what makes the absence falsifiable |

`wait_for_settled` returns a `SettledState` carrying `branch` (the winner),
`locator`, and `present` (every branch found). Resolution is by **declared
order**, and that ordering is the contract: `{content: PAGE, error:
ERROR_DISPLAY}` says "if the page root is there, that is the outcome I am
reading". Branch probing is one `execute_script` round-trip rather than N
`find_elements` calls, because the session's 3 s implicit wait applies to every
*empty* `find_elements` and would otherwise cost N×3 s per poll cycle.

**Structural rule:** a `navigate()` call outside an `open()`-shaped method is a
review finding — it returns once the document is loaded, which for this SPA is
before the route exists. `tests/e2e_selftest/test_navigation_contract.py` holds a
shrink-only allowlist of the sites that still violate it.

Browser-free unit tests for all of the above live in `tests/e2e_selftest/`
(`task test:e2e:selftest`) — deliberately outside this directory so they need no
stack and do not change this suite's collected count.

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

### 3. Gherkin tags → markers (pytest-bdd scenarios)

BDD scenarios under `features/` participate in the same selection axes as the
classic tests. pytest-bdd turns **every** scenario/feature/rule tag into a
pytest marker at import time and never registers it, which under
`--strict-markers` is a *collection error* that aborts the whole run — so
`conftest.py::pytest_configure` scans `features/**/*.feature` and registers the
tags it finds before collection starts.

Only four tag shapes are accepted; anything else is a hard `UsageError` naming
the tag and its file (typo guard, same idea as the `FEATURES` guard):

| Tag shape | Example | Meaning |
|---|---|---|
| `TC-NNN-NNN` / `TC-REQ-NNN-NNN` | `@TC-004-092` | the test case ID (see TC-ID traceability below) |
| `reqNNN` | `@req004` | REQ axis |
| a `KNOWN_FEATURE_MARKERS` key | `@watering` | feature axis |
| `smoke`, `core_crud`, `requires_auth`, `requires_desktop` | `@smoke` | legacy suites |

**In practice a `.feature` should carry only its `@TC-…` tag.** The REQ axis is
derived from the step module's `test_req<NNN>_*.py` file name and the feature
axis from that module's `FEATURES` tuple, so restating either one in Gherkin is
redundant — it would just create a second place to keep in sync. Python markers
(`@pytest.mark.smoke`) on the scenario function work as usual.

```bash
pytest -m TC-004-092      # the scenario itself (unquoted — 'TC-004-092' in quotes matches nothing)
pytest -m req004          # includes the BDD scenario, from the step module's file name
pytest -m watering        # includes it, from the step module's FEATURES tuple
```

#### Checking the `@TC-…` tag actually resolves

`pytest_configure` only guards the tag's *shape* — `@TC-004-092` and
`@TC-999-999` are equally acceptable to it. Whether the referenced test case
**exists** is checked by a separate script:

```bash
task test:e2e:traceability                        # exit 0 / 1, no stack needed
task test:e2e:traceability -- --list-unimplemented # + the cases with no scenario yet
python3 scripts/check_bdd_traceability.py --help   # roots are configurable
```

It parses `features/**/*.feature` and the `## TC-…: <title>` headings in
`spec/e2e-testcases/*.md`, and exits non-zero on two defects
(`spec/project/behavior-driven-development/`, where traceability is a hard gate):

| Defect | Meaning |
|---|---|
| orphan tag | a `@TC-<id>` no test-case document declares |
| untagged scenario | a scenario with no TC-ID at all |

The reverse direction is **not** a defect: a declared test case without a
scenario is simply not automated yet (1 of 2173 today), so it is reported as an
informational count. The script reuses `protocol_plugin.py::TC_ID_PATTERN`
for the ID shape and `_gherkin.py` for Gherkin line classification (tag lines,
docstring state) rather than restating either, and needs no third-party package.
It is deliberately **not** wired into a CI gate — run it locally, or in review,
when touching `.feature` files.

### 4. Legacy suites (unchanged)

```bash
task test:e2e:smoke       # -m smoke  (190 tests, ~7 min with -n 4)
docker compose -f docker-compose.e2e.yml --profile core-crud run --rm e2e-core-crud
```

## TC-ID traceability

Each test's docstring TC-ID (e.g. `TC-REQ-004-W001`) is lifted into the standard
junit `user_properties` channel as a `tc_id` property
(`conftest.py::_record_tc_id`), so downstream tooling — and the generated
markdown protocol — can consume it. This is in addition to the bespoke protocol
extraction in `protocol_plugin.py`.

**Derivation order — docstring first, Gherkin tag as fallback.** The docstring
channel is structurally dead for pytest-bdd scenarios: `pytest_bdd.scenario`
overwrites the scenario function's `__doc__` unconditionally with
`"<feature>: <scenario>"`. For those tests the ID is read off the `@TC-…`
**marker** instead (`conftest.py::_tc_id_from_markers`) — markers rather than
`__scenario__.tags` because markers are stable public pytest API and also carry
tags declared on an `Examples:` table. Classic tests are untouched by this: they
carry no TC marker, so their ID keeps coming from the docstring.

The *strict* ID shape is owned by `protocol_plugin.py::TC_ID_PATTERN` and
imported by `conftest.py`, so the two cannot drift apart. It matches both
spellings in use — `TC-004-092` and the older `TC-REQ-001-006`. (Until that
pattern was widened, the protocol's "Testfall-ID" silently never rendered for
any `TC-NNN-NNN` ID, BDD or classic.) `conftest.py::_TC_ID_SCAN` stays
deliberately wider for the junit property so it also captures test-local shapes
such as `TC-REQ-004-W001`.

> Note: the *test-declared* TC-IDs (`…-W001`, `…-PI-005`) currently drift from
> the spec IDs (`TC-004-NNN`) in `spec/e2e-testcases/`. See the coverage audit
> below; a full traceability reconciliation is tracked as a follow-up.

## Core-function coverage

`.audits/e2e-core-function-coverage/2026-07-14-core-function-coverage.md` maps
the implemented Selenium tests against the spec test cases for the five core
functions and names the real gaps (Spec-vs-implementation — complementary to
`spec/e2e-testcases/COVERAGE-REPORT.md`, which is Spec-vs-Spec).
