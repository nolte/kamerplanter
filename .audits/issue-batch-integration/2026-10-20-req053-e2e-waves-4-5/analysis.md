# Group pre-analysis: 2026-10-20-req053-e2e-waves-4-5

> Run-scoped artifact. Committed on the integration branch, removed with a fix-forward
> `git rm` before the bundle merges. It must never reach the default branch.

## Scope of this analysis

**Research question:** can the wave 4 (tasks, history, supersede/redact) and wave 5 (field mode, performance
targets) acceptance of REQ-053 be pinned by tests today, with prerequisites WP 4.5 (#2423) and WP 5.1 (#2430)
on `develop`, and what does the measured product say about each body claim?

**The group's single logical change, in one sentence:** add the field-mode, history and benchmark tests for
waves 4 and 5 of REQ-053 (E2E under `tests/e2e/`, benchmark assertions, the Lighthouse plan route).

**Out of scope:** wave 7 E2E (#2491 and successors, `test_req053_wave7_*.py`); changing product code to meet a
target the measurement says is missed (reported instead); raising any bundle budget; a prod deploy (E-07).

**Tier:** 2 - tests and CI wiring inside one repository, no published contract.

## Members

| Issue | Class | Admitting predicate | Evidence |
|---|---|---|---|
| #2424 | feature-request (test) | shared touch surface + dependency chain 4.6 -> 5.4 | WP 4.5 = #2423 CLOSED; `gh issue view 2424` |
| #2433 | feature-request (test) | shared touch surface + dependency chain 4.6 -> 5.4 | WP 5.1 = #2430 CLOSED; `gh issue view 2433` |

**Dependency ordering:** #2424 then #2433 (the E2E chain 3.8 -> 4.6 -> 5.4 of plan section 3).

**Shared touch surface:** the REQ-053 E2E suite (`tests/e2e/_garden_plan_helpers.py`, `tests/e2e/pages/`).

## Mode decision

**Mode:** A - single strand. **Reason:** both members are tests that stand on develop's existing behaviour; no
member is likely to need removal.

## Structural finding

**Cluster shape:** neither - a dependency chain of two test work packages, no common defect.

**Process finding:** the issue bodies name paths that do not exist (`src/e2e/tests/req053/`, `tests/benchmarks/`);
the suite lives in `tests/e2e/` and the backend tiers allow no test outside a tier directory
(`.taskfiles/backend.yaml`). The group follows the repository, not the paths of the body.

**Preventive change:** none required for the group; reported to the operator.

## Plan approval

**Authorised by:** `2026-10-20-req053-e2e-waves-4-5/plan-approval`, given by the caller's brief (the issue-backlog
partition record G-J, `/tmp/kamerplanter/.audits/issue-backlog-partition/2026-10-19.md`).

## Completeness matrix

| Member | E2E tests | Page objects / helpers | Benchmarks | CI wiring |
|---|---|---|---|---|
| #2424 | `test_req053_bed_care.py` TC-053-020/022/023/028; check: `pytest test_req053_bed_care.py` in the E2E stack | `pages/bed_care_page.py`, care helpers; check: `ruff check`, `ruff format --check` | not applicable - no performance target in #2424 | not applicable - the E2E lanes already run `tests/e2e` |
| #2433 | `test_req053_field_mode.py` TC-053-025/026/019m; check: same stack | `pages/field_mode_page.py`; check: `ruff` | vitest `layout.benchmark.test.ts` + lane; pytest containment (unit tier) and `GET /plan` (integration tier); check: `task test:frontend:bench`, `pytest -k Benchmark` | `lighthouserc.json` plan route, `test:frontend:bench` task and advisory job |

## Risks

- Wall-clock assertions on a shared runner: medians over 100 runs for the frontend, p95 over 20 runs with
  spec budgets for the backend, a regression ceiling where the spec value is not met.
- `GET /plan` p95 measured 0.82 s against the 300 ms of GP-NFR-030 - the body's claim does not hold (reported).

## Open questions for the operator

- The `GET /plan` read model needs work to reach p95 <= 300 ms (see Member results); a follow-up issue is the
  operator's to open.

## Member results

| Member | Specialist | Check | Actual output |
|---|---|---|---|
| #2424 | no matching specialist - done inline | `e2e.sh test_req053_bed_care.py` | 5 passed |
| #2433 | no matching specialist - done inline | `e2e.sh test_req053_field_mode.py` | 4 passed |

## Deviations

| Member | Kind | What changed |
|---|---|---|
| #2424, #2433 | local adaptation | paths: `tests/e2e/`, `pages/`, `src/backend/tests/{unit,integration}`, `src/frontend/` instead of the paths named in the bodies |
| #2433 | local adaptation | `GET /plan` spec p95 asserted as a strict xfail beside a regression-ceiling test |
