# Group pre-analysis: 2026-10-29-plan-input-hardening

> Run-scoped artifact. Committed on the integration branch, removed with a fix-forward
> `git rm` before the bundle merges. It must never reach the default branch, and it must
> never be hidden behind a `.gitignore` entry.
>
> Origin: `issue-backlog-partition` 2026-10-29 (`.audits/issue-backlog-partition/2026-10-29.md`,
> approved 2026-10-29T15:20:49Z; hand-off payload
> `scratchpad/handoff/2026-10-29-plan-input-hardening.yml`). Research anchored by one
> read-only exploration agent against `develop` `808c17aad` on 2026-10-30 (the
> `plant-state-layer-legend` bundle PR #2576 was still in CI; its diff does not touch the
> files below except `garden_plan_service.py`, which is why the branch waits for it).

## Scope of this analysis

**Research question:** Which of the seven #2542 review items are still defects at HEAD and
where in the five-layer stack does each belong, and how does the boundary route answer
`geometry.invalid` with a point index (#2547) when the range check fires inside request
validation before the service's code mapping is reached?

**The group's single logical change, in one sentence:** Harden the garden-plan import,
restore and geometry write paths so oversized, deeply nested or out-of-range input answers
a typed 422 (`geometry.invalid` with point index, quota and cap errors) within fixed
pre-parse limits instead of a 500 or an untyped `VALIDATION_ERROR`.

**Out of scope:**
- `Infinity` / non-finite coordinates (#2529): measured during research — a raw boundary
  `[Infinity, 0]` answers **500** `INTERNAL_ERROR` (`decimal.InvalidOperation` from
  `round_length` → `Decimal.quantize`, `geometry.py` validator) while `[NaN, 0]` is a 422.
  #2529 owns the finite guard; this group records the measurement for it and does not fix it.
- Snapshot compression / count-only storage (W-2 alternative): the cap alone bounds the
  growth; compression is a different mechanism (#2545-style follow-up if ever needed).
- The other request schemas that carry `Geometry` the same way
  (`garden_objects/schemas.py:41,78`, `sites/schemas.py:58`, `locations/schemas.py:106`,
  `slots/schemas.py:28`, `garden_plan/schemas.py:187,267,433`) — GP-ACC-056 names the
  boundary route; the batch path is included because the issue asks for it and V-01 is
  defined there. GP-ACC-058 (rotation −1) has the same generic-422 shape and stays open.
- The 25 MiB multipart ceiling design (S-3): measured as **stricter** on the import route,
  not looser — see Members.

**Tier:** 2 — one repository; backend-only; error contract extended additively
(`point_index` in a 422 detail), SVG CSP tightened (removing a directive, no consumer
relies on inline styles: the engine emits none, `plan_svg_engine.py:12`).

## Members

| Issue | Class | Admitting predicate | Evidence |
|---|---|---|---|
| #2542 | security | shared touch surface (anchor) | body names `garden_plan_import_service.py`, `garden_plan_export.py`, `garden_plan_service.py`; measured at HEAD: `garden_plan_export.py:172-174` `locations`/`slots`/`garden_objects` have no `max_length` (only `zones` l.176 has `MAX_PLAN_ZONES`), `_prepare` (`garden_plan_import_service.py:429`) runs lookups before `_check_quotas` (l.477, def l.852-855) also for `dry_run` (l.260-275); `_write_audit` (`garden_plan_repository.py:1092-1107`) inserts a snapshot row with no per-site cap, `purge_audit_before` (l.1123-1147) only after `retention_garden_plan_audit_retention_days` = 365 (`settings.py:126`); `_count_points` (`garden_plan_service.py:239-248`) recursive, probe n=600 → `RecursionError`, called twice (l.465/471); `tenant_router.py:573` `PlanImportRequest.model_validate_json(raw)` on the event loop (≤ 5 MB + 64 KiB) |
| #2547 | bug | shared touch surface | body names `garden_plan_service.py` and `api/v1/garden_plan/tenant_router.py` (both in #2542's surface); measured: `geometry.py:99-105` `_validate_point` raises `ValueError` inside `_validate_points` (l.123-128, whole-tuple → `loc=('polygon','points')`, no index); `put_boundary` (`tenant_router.py:272-312`) takes `PlanBoundaryRequest.boundary: Geometry` (`schemas.py:46-58`) so FastAPI's `RequestValidationError` → `validation_error_handler` (`error_handlers.py:60-89`) emits `error_code: VALIDATION_ERROR`, `details[].code: value_error`; `_finding_code` (`garden_plan_service.py:229-236`) maps geometry fields → `geometry.invalid` only on the batch path; `point_index` exists nowhere but in the spec (GP-ACC-056 `REQ-053…md:1849`) |

**Per-item verdicts for #2542 (measured, see research anchors above):**

| Item | Verdict | Fix location |
|---|---|---|
| W-1 list caps | verified | model: `max_length` on the three lists in `GardenPlanExport` (`locations`, `garden_objects` ≤ `MAX_PLAN_OBJECTS_PER_SITE` = 500, `slots` ≤ `MAX_SLOTS_PER_SITE` = 8 000, `garden_plan.py:48,54`); the model is also the export `response_model`, so caps must be ≥ the quotas |
| W-2 snapshot cap | verified (no cap anywhere; no prune pattern in the codebase) | repository: prune the oldest `import_snapshot` rows of the site inside `_write_audit` in the same transaction; constant `MAX_SNAPSHOTS_PER_SITE` in the import model module; interface `domain/interfaces/garden_plan_repository.py` + fake `tests/support/garden_plan_fakes.py`; docs line "kept one year" (`docs/{en,de}/reference/api-reference.md:252`) |
| S-1 recursion | verified, reproduced (n=600 `RecursionError`; JSON parse still fine at 3 000 → 500 window) | service: iterative `_count_points` with an explicit stack, computed once |
| S-2 parse on loop | verified | router: `run_in_threadpool(PlanImportRequest.model_validate_json, raw)` (already imported l.15), keep the `PydanticValidationError` mapping |
| S-3 multipart ceiling | literally true, **no risk**: `ceiling_for` (`body_limit.py:228-237`) applies the 5 MiB pattern ceiling for any content type by design (docstring l.128-136), so multipart on the import route gets ~5.06 MiB instead of 26 MiB; the route never parses multipart | no change; recorded as a measured non-defect in the bundle |
| S-4 CSP `style-src 'unsafe-inline'` | verified; **mandated by spec** GP-NFR-052(e) (`REQ-053…md:1664`), REQ-032 (`…:309`), pinned by `test_garden_plan_export_api.py:137`, `main.py:472-474` comment, docs `api-reference.md:187` | router constant `SVG_DOWNLOAD_HEADERS` → `default-src 'none'`; spec lines, test, docs, comment |
| Info PDF `area_m2 = None` | **refuted**: `Location.area_m2: float = Field(ge=0)` is required (`site.py:401`), `Location(area_m2=None)` → `ValidationError`; `_bed_rows` (`garden_plan_export_service.py:335-353`) skips `geometry is None`; no `model_construct` in `app/` | no change |

**Dependency ordering:** #2547 → #2542. #2547 is the smaller slice and edits
`garden_plan_service.py:229-236` (`_finding_code`) and `tenant_router.py:272-312`; #2542
edits the adjacent `_count_points` (l.239-248) and `tenant_router.py:456-459,556-586`.
Sequential sub-branches off the integration tip avoid the adjacent-hunk conflict.

**Shared touch surface:** `src/backend/app/domain/services/garden_plan_service.py`,
`src/backend/app/api/v1/garden_plan/tenant_router.py`, `src/backend/tests/api/test_garden_plan_api.py`,
`docs/{en,de}/reference/api-reference.md`. With PR #2576: `garden_plan_service.py`
(hence the gate).

**Gates:** PR #2546 merged `0d8cad496` (the GP-ACC-056 test to tighten exists at
`test_garden_plan_api.py:168-179`); `site-conditions-layers` merged `baf7000a3`; the
integration branch is created only after PR #2576 merges.

## Mode decision

**Mode:** B — sub-branch per member.

**Reason:** #2542 is `security`-classified; its S-4 change needs a spec edit and its W-2
cap is a product-visible retention change — either may be rejected in the bundle review.
Mode B keeps #2542 droppable by removing one merge. #2547's sub-branch merges first.

## Structural finding

**Cluster shape:** class cluster — input-validation gaps of one write path family
(import / batch / boundary), different functions, no single root cause.

**Root cause or defect class:** limits and typed error mapping were added per route as the
WP landed, not at the layer that owns them: the quota is checked after the work it should
bound (W-1), the recursion is bounded by the JSON parser instead of the function that
recurses (S-1), the geometry range rule lives in the model where Pydantic's generic
handler owns the error shape (#2547), and the SVG CSP was copied from the spec text that
assumed inline styles the engine never emits (S-4).

**Process finding:** none filed. The WP 6.2 security review (`spec/analysis/security-review-req-053.md`
SR-004/SR-005/SR-012) found these; the review itself worked. The repeated shape "typed
error mapping sits in the service, but the rule fires in request validation" exists for
every schema carrying `Geometry` (see out of scope) — recorded for the operator, not
filed as a process issue (threshold not met: one review, one group).

**Preventive change:** none in this group. Candidate for the operator: a guard test that
every pydantic validator in `domain/models/geometry.py` raises a `PydanticCustomError`
with a stable code (so request-level failures are typed), once #2547's mechanism is in.

**Recurrence fed to the portfolio loop:** "limit added after the work it bounds" — 1 (this group).

## Plan approval

**Authorised by:** `2026-10-29-plan-input-hardening/plan-approval`, covering the members,
mode, and order above, under the operator's 2026-10-09 / 2026-10-30 autonomy for the
approved partition. Revoked for undispatched members by any structural regression until
re-approved.

**Group requirement artifact (class cluster only):** not elicited — every member's
acceptance is already pinned by REQ-053 (GP-ACC-056 l.1849, V-01 l.1538, GP-NFR-017
l.1092, GP-FR-141 l.1583, GP-NFR-051/052/055 l.1663-1667) plus the security review
findings SR-004/005/012; the spec is the requirement artifact (`U_gate`: those anchors).

### Design decisions (binding for the dispatched runs)

- **D-1 (#2547 error shape):** the boundary route answers the **same contract as the batch
  path**: `PlanValidationError` → HTTP 422, `error_code: VALIDATION_ERROR`,
  `details: [{code: "geometry.invalid", point_index: <int>, message}]`
  (`exceptions.py:198-220`; the batch already emits `details[].code = geometry.invalid` with
  `op_index`). This is what the spec's "422 `geometry.invalid` mit dem Punktindex in
  `details`" (l.1849) literally says, and what `ImportWizard.tsx:85-101` / `codeKey` already
  decode. No new top-level error code.
- **D-2 (#2547 mechanism):** the geometry validator raises `PydanticCustomError("geometry.invalid", …, {"point_index": i})`
  per point (precedent `watering_logs/schemas.py:7,34`), so the index travels in the
  pydantic error `ctx`. `PlanBoundaryRequest.boundary` stays typed; the router catches the
  `RequestValidationError`-equivalent by parsing the raw body like `PlanBatchRequest`
  (`schemas.py:79-81`) **or** the `_finding_code` mapping gains `point_index` from `ctx` on
  the batch path and a small shared helper maps a `PydanticValidationError` over a
  geometry to a `PlanValidationError` for the boundary route. The dispatched run picks the
  variant that keeps `schemas.py` typed for OpenAPI and records it.
- **D-3 (W-1):** `max_length` on the three lists, values = the existing quota constants
  (no new numbers); the import's `_finding_of`/`_code_of` (`garden_plan_import_service.py:1138-1150`)
  already maps `max_length` violations to `validation.invalid` — add a test that a 501st
  location is refused **before** any zone/substrate lookup (fake repository call count).
- **D-4 (W-2):** `MAX_SNAPSHOTS_PER_SITE` (proposed 20; a product-visible number — reported
  to the operator) enforced in `_write_audit` within the batch transaction by removing the
  oldest `import_snapshot` rows of the site beyond the cap; restore and non-dry replace
  both pass through it. Interface + fake updated; docs sentence "kept one year" gains the
  cap; spec GP-NFR-055 gains one clause.
- **D-5 (S-1):** iterative `_count_points`, computed once, with a test that a props
  nesting of depth 5 000 answers the complexity 422 (or passes) and never 500.
- **D-6 (S-2):** `await run_in_threadpool(PlanImportRequest.model_validate_json, raw)`.
- **D-7 (S-4):** `SVG_DOWNLOAD_HEADERS` CSP → `default-src 'none'`; spec GP-NFR-052(e)
  and REQ-032 l.309 updated in the same bundle (spec-change label), test string, docs,
  `main.py` comment.
- **D-8 (S-3, Info):** no change; the bundle's Risk notes carry both measurements.

## Completeness matrix

| Member | Backend source | Migration | Spec | Tests | Docs | Frontend | Config / workflows | Generated indexes / pins |
|---|---|---|---|---|---|---|---|---|
| #2547 | `domain/models/geometry.py` validator → `PydanticCustomError("geometry.invalid", ctx point_index)`; `domain/services/garden_plan_service.py:229-236` finding carries `point_index`; `api/v1/garden_plan/tenant_router.py:272-312` boundary → `PlanValidationError`; check: `task lint:backend && task typecheck:backend` | not applicable — no stored shape changes | not applicable — GP-ACC-056 l.1849 already states the contract; verify wording matches D-1 | tighten `tests/api/test_garden_plan_api.py:168-179` (`…gp_acc_056`) to assert `details[0].code == "geometry.invalid"` and `point_index`; `tests/unit/domain/models/test_geometry.py` error code; batch test for `point_index`; check: `task test:backend:unit` + `task test:backend:api` | `docs/{en,de}/reference/api-reference.md:245` error-code list mentions `point_index`; check: `task docs:build` (strict) | not applicable — `codeKey` already maps `geometry.invalid`; no UI reads `point_index` | not applicable | `spec/e2e-testcases/GP-ACC-matrix.md` unchanged unless a test file is added (`python3 scripts/gp_acc_matrix.py --write`, guard `test_req053_acceptance_matrix.py:41`); write-gate ceiling 2804 untouched (no new unannotated write call) |
| #2542 | `domain/models/garden_plan_export.py:172-174` `max_length`; `data_access/arango/garden_plan_repository.py:1092-1107` snapshot prune + `domain/interfaces/garden_plan_repository.py`; `domain/services/garden_plan_service.py:239-248` iterative; `api/v1/garden_plan/tenant_router.py:573` threadpool, `:456-459` CSP; check: `task lint:backend && task typecheck:backend` | not applicable — the prune runs forward on write; existing oversize histories shrink on the next snapshot (recorded risk) | `spec/req/REQ-053…md:1664` GP-NFR-052(e) CSP value, `:1667` GP-NFR-055 snapshot cap clause, `spec/req/REQ-032…md:309`; check: `pre-commit run --files <spec files>` + `grep -n "unsafe-inline" spec/req/REQ-053*.md` returns nothing | new: 501st location refused before lookups (fake call count), snapshot cap prune (unit on fake + integration `tests/integration/test_garden_plan_import.py`), `_count_points` depth 5 000, CSP string `tests/api/test_garden_plan_export_api.py:137`, import parse off-loop (behavioural: still 422 on bad JSON); check: `task test:backend:unit`, `task test:backend:api`, `task test:backend:integration` (ArangoDB) | `docs/{en,de}/reference/api-reference.md:187` CSP, `:252` snapshot cap; check: `task docs:build` | not applicable — no UI change; `KNOWN_FAILURES` already covers `VALIDATION_ERROR` | not applicable — body ceilings (`main.py:427-437`) unchanged; S-3 no change | `tests/support/garden_plan_fakes.py` fake gains the prune; keyed-writes guard `test_keyed_service_writes_take_the_tenant.py` (any new write takes `tenant_key` kw-only); write-gate ceiling 2804 untouched |

## Risks

- **W-2 prune deletes history retroactively**: a site with > cap snapshots loses the
  oldest on its next import/restore. Cost: an operator who relied on year-long snapshot
  history cannot restore beyond the cap. Mitigated by the number being a constant the
  operator can veto before merge (reported) and by the audit *log* rows staying (only the
  `snapshot` payload rows are pruned).
- **D-2 raw-body parsing** could drop the OpenAPI schema of the boundary body if the
  dispatched run chooses the raw variant; the plan prefers keeping `PlanBoundaryRequest`
  typed. Check: `task openapi:export && task openapi:lint` after #2547.
- **S-4 CSP** removal is safe only while the engine emits no `style`; the existing
  allowlist test (`plan_svg_engine.py:12` contract) pins that.
- **Adjacent hunks** in `garden_plan_service.py` (l.229-248) — handled by Mode B ordering.
- **Ceiling guard**: `_GENUINE_UNRESOLVED_CEILING = 2804` (`test_write_route_gates.py:2491`)
  must not be raised; new write calls are annotated, not counted.

## Open questions for the operator

- None blocking under the 2026-10-30 autonomy. Reported, not asked: the
  `MAX_SNAPSHOTS_PER_SITE` value (D-4, proposed 20) and the decision D-1 to keep
  `VALIDATION_ERROR` as the top-level code with `geometry.invalid` in `details`.

## Member results

| Member | Specialist | Check | Actual output |
|---|---|---|---|
| #2547 | nolte-engineering:fullstack-developer (P1), nolte-engineering:python-code-reviewer (verification), fullstack-developer (fix round) | `ruff check . && ruff format --check .` | `All checks passed!` / `2849 files already formatted` EXIT=0 |
| #2547 | — | mypy ratchet (`scripts/mypy_ratchet_hook.sh`) | `3419 findings now, 3434 recorded … GREEN` EXIT=0 |
| #2547 | — | `pytest tests/api -q -x` (+ targeted unit) | `3439 passed, 182 warnings in 336.07s` EXIT=0; after fix round `tests/unit/domain/models/test_geometry.py tests/unit/domain/services/test_garden_plan_service.py tests/unit/common tests/api/test_garden_plan_api.py` → `900 passed, 80 warnings in 30.20s` |
| #2547 | — | `pytest tests/unit/api`, `tests/unit/guards`, `tests/unit/domain`, `tests/unit/common` | `1111 passed`; `3005 passed, 19 skipped, 5 deselected`; `8486 passed`; `730 passed` (all EXIT=0); write-gate ceiling 2804 unchanged |
| #2547 | — | `python -m scripts.export_openapi` + spectral | `Wrote openapi.json (659 paths).`; `0 errors, 37 warnings` (pre-existing); exported schema byte-identical to HEAD (`cmp`) |
| #2547 | — | `python3 scripts/gp_acc_matrix.py --check` | EXIT=0 after `--write` (new tests name GP-ACC-056) |
| #2547 | — | `mkdocs build --strict` (direct, primary `.venv-docs`) | `Aborted with 3 warnings` — all three are nav refs to the generated catalog (`de/skills`, `de/agents`, `de/tags.md`) absent in the worktree; no warning from the changed pages; full `task docs:build` deferred to the bundle gate |
| #2547 | — | falsification (cp, not stash) | handler reverted → api test fails `point_index == 1`; `_finding_extra` → `{}` → batch test `KeyError: 'point_index'` |

## Deviations

| Member | Kind | What changed |
|---|---|---|
| #2547 | local adaptation | docs: `api-reference.md:245` is the **import** error table (`ImportFinding` has no `point_index`) → new section "Garden Plan save: geometry errors" DE/EN instead; matrix cell Docs updated accordingly. Side effect accepted under D-1: every route embedding `Geometry` now answers `geometry.invalid` (origin without index) for a range violation; dimension/rotation/count stay `value_error` (GP-ACC-058, pre-existing). |

## Requirement coverage

not applicable — no group requirement artifact (spec anchors serve as `U_gate`).

## Findings

| Finding | Source | Outcome | Reproduction | Issue |
|---|---|---|---|---|
| `docs/{en,de}/reference/api-reference.md:252` claims every boundary geometry defect is `geometry.invalid`; measured: `width_m:-1`, 2-point polygon, `rotation_deg:-1` → `value_error`, only range → `geometry.invalid` (SCR-001) + bed frame named but not on those endpoints (SCR-002) | member verification pass (python-code-reviewer) | fixed directly ec3461189 | `parse_geometry({...width_m:-1})` → `value_error {'error': ValueError('Dimensions must lie within 0.01..1000.0 m, got -1.0.')}` | — |
| `point_index` through the bed-frame WrapValidator unproven (SCR-003) | member verification pass | measured, test added 5a3351f40 | `SlotPatch.model_validate({'geometry':{'kind':'polygon','points':[[0,0],[-1000.5,0],[0,1]]}})` → `geometry.invalid {'point_index': 1} ('geometry','polygon','points')` | — |
| rule "point_index only for geometry.invalid" duplicated in `error_handlers.py` and `garden_plan_service.py`; literal next to constant (SCR-004/005) | member verification pass | fixed directly 5a3351f40 (`point_index_of` helper in `geometry.py`) | tests `900 passed` after refactor | — |
| boundary route: non-range shape rules (dimensions, vertex count, rotation) answer `value_error`, not V-01 `geometry.invalid` (GP-ACC-058 shape); after #2579 non-finite values would answer `finite_number` there | member verification pass + #2579 analysis | pre-existing, filed as operator point (follow-up issue candidate, not in this group) | see SCR-001 reproduction | — |
| `geometry.py` validator: raw boundary `[Infinity, 0]` → 500 `INTERNAL_ERROR` (`decimal.InvalidOperation`) | research probe (minimal FastAPI app with the repo handlers) | filed as a comment on the owning issue | `json.loads('[Infinity, 0]')` → `[inf, 0]`; `parse_geometry` → `decimal.InvalidOperation` | #2529 |
