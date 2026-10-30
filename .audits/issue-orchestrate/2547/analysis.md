---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter"
issue: "2547"
classification: "bug"
secondary-classes: []
route: "direct"
status: approved
created: "2026-10-30"
---

# Issue Orchestration — Pre-analysis

> Run-scoped artifact on the Mode B sub-branch `fix/2026-10-29-plan-input-hardening-2547`
> of group `2026-10-29-plan-input-hardening`; removed fix-forward before the bundle merges.
> Group delegation: `authorised_by: 2026-10-29-plan-input-hardening/plan-approval`
> (resolved against `.audits/issue-batch-integration/2026-10-29-plan-input-hardening/analysis.md`,
> commit `4817216e9`, which lists #2547 and carries the plan approval).

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #2547 — fix(garden-plan): GP-ACC-056 - out-of-range boundary point answers generic VALIDATION_ERROR instead of geometry.invalid with the point index
- **URL**: https://github.com/nolte/kamerplanter/issues/2547
- **Labels**: bug, backend, spec:REQ-053
- **Linked items**: PR #2546 (merged `0d8cad496`, added the 422-only test), #2445, #2529 (non-finite coordinates — out of scope here)
- **Prior art checked**: partition record 2026-10-29 (re-checked live: OPEN, 0 comments, author nolte = trusted); group research 2026-10-30 against `808c17aad`; anchors re-read at this branch's head `4817216e9` (below)

## Classification

- **Primary class**: bug
- **Secondary class(es)**: none
- **Rationale**: acceptance criterion GP-ACC-056 (`spec/req/REQ-053_Grafische-Garten-Beetplanung.md:1849`) is not met on the boundary route.
- **Asserted cause verified**: **confirmed** at `4817216e9` — `app/domain/models/geometry.py:99-104` `_validate_point` raises a plain `ValueError` (no code, no index) inside `_validate_points` (l.123-128, whole-tuple validator); `app/api/v1/garden_plan/schemas.py:58` `boundary: Geometry` is a typed request field, so FastAPI's `RequestValidationError` reaches `app/common/error_handlers.py:60-82` which always emits `error_code: VALIDATION_ERROR`; the `geometry.invalid` mapping `_finding_code` (`app/domain/services/garden_plan_service.py:229-232`) is only used by the batch path (`_findings_of` l.235). Probe (research, minimal FastAPI app with the repo handlers): raw `[1000.5, 0]` → 422 `VALIDATION_ERROR`, detail `code: value_error`. Test pin: `tests/api/test_garden_plan_api.py:168-179` (comment l.173-174 records the same measurement on 2026-10-20).

## Scope

- **In scope**: the boundary route (`PUT …/plan/boundary`) answers 422 with `details[].code == "geometry.invalid"` and the offending `point_index`; the batch path's geometry findings carry `point_index` too when the error is a point-range violation (issue: "and ideally the batch geometry validation"); the GP-ACC-056 test is tightened; docs error-code list mentions the index.
- **Out of scope**: non-finite coordinates (`Infinity` → 500, #2529); the other request schemas that embed `Geometry` (garden_objects, sites, locations, slots) and GP-ACC-058 (rotation) — same shape, separate issues; any new top-level error code (group decision D-1).

## Route

- **Decision**: direct
- **Rationale**: one outcome, one strand, inside the member's completeness-matrix row (Backend source, Tests, Docs; Spec/Migration/Frontend/Config not applicable).

## Work packages

### P1 — typed point-range error with index

- **Problem statement** (hypothesis, refutable): the geometry validator can raise `PydanticCustomError("geometry.invalid", <message>, {"point_index": i})` per point (precedent `app/api/v1/watering_logs/schemas.py:7,34`) so the index travels in the pydantic error `ctx`; `_finding_code`/`_findings_of` in `garden_plan_service.py` can read `ctx["point_index"]` into the finding (batch path), and the boundary route can map a `PydanticValidationError` over `PlanBoundaryRequest.boundary` to a `PlanValidationError` (`app/common/exceptions.py:198-220`) carrying `[{code: "geometry.invalid", point_index, message}]` — **while `PlanBoundaryRequest` stays typed for OpenAPI** (D-2). Preferred mechanism for the route: keep `boundary: Geometry` in the schema and add a model/field validator on `PlanBoundaryRequest` or on `Geometry` such that the error already carries the custom type, then extend `validation_error_handler` **minimally**: when a pydantic error's `type` is `geometry.invalid`, emit that code in `details[].code` and copy `ctx.point_index` — OR parse the raw body in the router as `PlanBatchRequest` does (`schemas.py:79-81`) and raise `PlanValidationError`. The specialist chooses the smallest change that keeps the OpenAPI schema and records why; a refutation (e.g. `ctx` is not serialised by the handler, or the custom type is swallowed by the tuple validator) is a first-class result.
- **Acceptance criteria**:
  1. `PUT …/plan/boundary` with a polygon point `[1000.5, 0]` at index 1 → 422, body `error_code == "VALIDATION_ERROR"`, `details[0].code == "geometry.invalid"`, `details[0].point_index == 1`; plan unchanged (existing test tightened).
  2. `[1000.0, 0]` → 200 (unchanged).
  3. Batch (`POST …/plan/batch`) op with an out-of-range point → the existing `geometry.invalid` finding additionally carries `point_index` (new test next to `tests/unit/domain/services/test_garden_plan_service.py` geometry cases or `tests/api/test_garden_plan_api.py`).
  4. Bed-frame geometries (−1000…1000) keep their range (`tests/unit/domain/models/test_geometry.py` green, plus one case asserting the custom error type).
  5. `task lint:backend`, `task typecheck:backend`, `task test:backend:unit`, `task test:backend:api` green; `task openapi:export && task openapi:lint` green (boundary body schema unchanged).
  6. `docs/{en,de}/reference/api-reference.md` error-code line for `geometry.invalid` mentions `point_index` (both languages, same sentence); `task docs:build` strict green.
- **Touched files / artifacts**: `src/backend/app/domain/models/geometry.py`, `src/backend/app/domain/services/garden_plan_service.py` (l.229-236 only; do not touch `_count_points` l.239-248 — #2542 edits it next), `src/backend/app/api/v1/garden_plan/tenant_router.py` (put_boundary l.279-312) and/or `app/common/error_handlers.py`, `src/backend/tests/api/test_garden_plan_api.py:168-179`, `src/backend/tests/unit/domain/models/test_geometry.py`, docs api-reference DE/EN.
- **Specialist**: `nolte-engineering:fullstack-developer` (runtime inventory: senior full-stack engineer for backend features/bug fixes with tests)
- **Depends on**: none

## Dependency ordering

P1 only.

## Risks

- `validation_error_handler` is global: a change there must be keyed on the custom error type only, never alter the shape for other routes (`tests/api` suite pins it). Mitigation: acceptance 5 runs the api suite.
- Write-route gate guard: no new unannotated write call (`tests/unit/api/test_write_route_gates.py` ceiling 2804).
- GP-ACC matrix guard (`tests/unit/guards/test_req053_acceptance_matrix.py`): only if a **new test file** names `gp_acc_056` → regenerate with `python3 scripts/gp_acc_matrix.py --write`.
- Security-sensitive path? No (input validation tightening, no auth/tenant change); the group's bundle still runs `security-review` over the full diff.

## Open questions

none (D-1/D-2 decided in the group artifact under operator autonomy).

## Dispatch log
