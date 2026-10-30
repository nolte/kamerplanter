---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter"
issue: "2542"
classification: "security"
secondary-classes: ["bug"]
route: "direct"
status: approved
created: "2026-10-30"
---

# Issue Orchestration — Pre-analysis

> Run-scoped artifact on the Mode B sub-branch `fix/2026-10-29-plan-input-hardening-2542`
> of group `2026-10-29-plan-input-hardening` (base: integration tip `9c4faa5b9`, which
> already carries member #2547). Removed fix-forward before the bundle merges.
> Group delegation: `authorised_by: 2026-10-29-plan-input-hardening/plan-approval`
> (`.audits/issue-batch-integration/2026-10-29-plan-input-hardening/analysis.md`, commit
> `4817216e9`, lists #2542, Mode B, design D-3…D-8). The `security` classification was
> fixed by the partition record (approved 2026-10-29T15:20:49Z) and the operator's
> 2026-10-30 autonomy; recorded here instead of asked.

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #2542 — sec(garden-plan): import/restore hardening from the #2541 security review (pre-parse quotas, snapshot growth, deep JSON, multipart ceiling, PDF area_m2 None)
- **URL**: https://github.com/nolte/kamerplanter/issues/2542
- **Labels**: security, backend, spec:REQ-053
- **Linked items**: #2541 (WP 6.2 review source, `spec/analysis/security-review-req-053.md` SR-004/005/012), #2539, #2529 (non-finite coordinates — out of scope, see PR #2579), #2446
- **Prior art checked**: partition record 2026-10-29; group research 2026-10-30 against `808c17aad`; anchors re-read at `9c4faa5b9` (below). No open PR touches these items.

## Classification

- **Primary class**: security (secondary: bug for the `Info` item, which is refuted)
- **Rationale**: warnings/suggestions of a security review over one input path (import/restore/batch).
- **Asserted causes verified** (per item, at `9c4faa5b9`):
  - **W-1 confirmed**: `app/domain/models/garden_plan_export.py:172-174` — `locations`, `slots`, `garden_objects` have no `max_length`; only `zones` (l.176) is capped. `garden_plan_import_service.py`: `_read_document` l.386 → `_prepare` l.429 (per-key lookups) → `_check_quotas` l.852 after the loops; `dry_run` returns after `_prepare` (l.274).
  - **W-2 confirmed**: `garden_plan_repository.py:1092-1107` `_write_audit` inserts an `import_snapshot` row for every non-merge import and every restore, no per-site cap anywhere (`grep -rn "max_snapshots|SNAPSHOT_CAP|snapshots_per_site" app/` → nothing); only `purge_audit_before` (l.1123) after 365 days (`settings.py` `retention_garden_plan_audit_retention_days`).
  - **S-1 confirmed and reproduced**: `garden_plan_service.py:248` `_count_points` recurses; probe with `props` nested 600 deep → `RecursionError` (300 ok, 3000 RE) while `json.loads` still parses 3000 → the request ends in 500; called twice (after `_parse`).
  - **S-2 confirmed**: `tenant_router.py:573` `PlanImportRequest.model_validate_json(raw)` on the event loop; `run_in_threadpool` imported l.15 and used l.586 for the service only.
  - **S-3 literally true, no defect**: `app/common/body_limit.py` `ceiling_for` applies route-pattern ceilings for any content type by design (docstring), so multipart on the import route gets ~5.06 MiB instead of 26 MiB — stricter; the route never parses multipart. **No change** (D-8).
  - **S-4 confirmed, spec-mandated**: `tenant_router.py:458` CSP `default-src 'none'; style-src 'unsafe-inline'`; engine emits no style (`plan_svg_engine.py:12`); pinned by `tests/api/test_garden_plan_export_api.py:173`, `main.py:473` comment, `spec/req/REQ-053…md:1664` GP-NFR-052(e), `spec/req/REQ-032…md:309`, `docs/{en,de}/reference/api-reference.md:187`.
  - **Info refuted**: `Location.area_m2: float = Field(ge=0)` (`site.py:401`) is required; `Location(area_m2=None)` → `ValidationError`; `_bed_rows` skips `geometry is None`; no `model_construct` in `app/`. **No change** (D-8).

## Scope

- **In scope**: W-1, W-2, S-1, S-2, S-4 as designed in D-3…D-7; tests proving each; spec + docs updates for S-4 and W-2.
- **Out of scope**: S-3 and Info (measured non-defects, recorded in the bundle notes); non-finite coordinates (#2529 / PR #2579); snapshot compression; the other `Geometry`-embedding schemas.

## Route

- **Decision**: direct — one strand inside the member's matrix row (Backend source, Spec, Tests, Docs; Migration/Frontend/Config not applicable; pins: fake repository, keyed-writes guard, ceiling).

## Work packages

### P1 — W-1 pre-parse list caps
- **Problem statement** (refutable): adding `max_length` to the three lists in `GardenPlanExport` (`locations`, `garden_objects` ≤ `MAX_PLAN_OBJECTS_PER_SITE` = 500; `slots` ≤ `MAX_SLOTS_PER_SITE` = 8 000, constants in `garden_plan.py:48,54`) refuses an oversized file in `_read_document` before `_prepare` runs any lookup, also for `dry_run`; the existing `_finding_of`/`_code_of` mapping turns the pydantic `too_long` error into a `validation.invalid` finding (422). The same model is the export `response_model`, so the caps must be ≥ the quotas (they are equal).
- **Acceptance**: a document with 501 locations is refused with 422 and the fake repository records **zero** zone/substrate lookups (count calls on the fake); 500 locations still reach `_check_quotas` as today; export of a full site still serialises; `tests/api/test_garden_plan_import_api.py` + `tests/unit/domain/services/test_garden_plan_import_service.py` green.
- **Touched**: `garden_plan_export.py`, tests. **Specialist**: `nolte-engineering:fullstack-developer`. **Depends on**: none.

### P2 — W-2 snapshot cap per site
- **Problem statement** (refutable): a constant `MAX_SNAPSHOTS_PER_SITE = 20` (module of the import models; a product-visible number reported to the operator) enforced in `_write_audit` inside the same stream transaction: after inserting the new `import_snapshot` row, remove the oldest `import_snapshot` rows of that `site_key`+`tenant_key` beyond the cap (order `revision DESC, DATE_TIMESTAMP(at) DESC` as `list_import_snapshots` uses). Only snapshot rows are pruned; other audit rows stay. The interface `domain/interfaces/garden_plan_repository.py` and the fake `tests/support/garden_plan_fakes.py` mirror it. Restore and non-dry `replace` both pass through `_write_audit`, so both are capped.
- **Acceptance**: unit test on the fake: 21 replace imports → 20 snapshots listed, the oldest gone, newest present; integration test (`tests/integration/test_garden_plan_import.py`, ArangoDB) with the same expectation; `list_import_snapshots` paging unchanged; keyed-writes guard green (`tests/unit/guards/test_keyed_service_writes_take_the_tenant.py`); spec GP-NFR-055 (`REQ-053…md:1667`) gains one clause naming the cap; docs `api-reference.md:258` DE/EN sentence "kept as long as the log" gains the cap.
- **Touched**: `garden_plan_repository.py`, interface, fake, import model module, spec, docs, tests. **Specialist**: `nolte-engineering:fullstack-developer`. **Depends on**: none.

### P3 — S-1 iterative `_count_points`
- **Problem statement**: rewrite `_count_points` (`garden_plan_service.py:248`) with an explicit stack (no recursion), compute it once instead of twice after `_parse`.
- **Acceptance**: a batch body whose op `props` nests 5 000 levels answers 422 (`plan.too_complex` or the size/points code the service already uses) and never 500 — pinned by an api test with `raise_server_exceptions=False`; existing `test_more_than_20000_points_are_too_complex` / `test_a_body_over_two_megabytes_is_too_complex` green; a direct unit test of `_count_points` on nested depth 5 000 returns without `RecursionError`.
- **Touched**: `garden_plan_service.py` (only that function and its call sites), tests. **Specialist**: `nolte-engineering:fullstack-developer`. **Depends on**: none.

### P4 — S-2 parse off the event loop
- **Problem statement**: `envelope = await run_in_threadpool(PlanImportRequest.model_validate_json, raw)` in `tenant_router.py:573`, keeping the surrounding `PydanticValidationError` mapping.
- **Acceptance**: `tests/api/test_garden_plan_import_api.py` green (bad JSON still 422, 5 MB still 413); route signature/OpenAPI unchanged (`python -m scripts.export_openapi` byte-identical).
- **Touched**: `tenant_router.py`. **Specialist**: `nolte-engineering:fullstack-developer`. **Depends on**: none.

### P5 — S-4 SVG CSP without `style-src 'unsafe-inline'`
- **Problem statement**: `SVG_DOWNLOAD_HEADERS` CSP → `default-src 'none'`; update the pin in `tests/api/test_garden_plan_export_api.py:173`, the comment `main.py:473`, spec `REQ-053…md:1664` GP-NFR-052(e) and `REQ-032…md:309`, docs `api-reference.md:187` DE/EN. The engine emits no `style`; the allowlist contract (`plan_svg_engine.py:12`) stays.
- **Acceptance**: `grep -rn "unsafe-inline" src/backend spec/req docs/` → no hit on the garden-plan SVG path; export api tests green; a test that the SVG body contains no `<style` and no `style=` (if not already pinned, add one).
- **Touched**: router, test, main.py comment, two spec files, two docs files. **Specialist**: `nolte-engineering:fullstack-developer`. **Depends on**: none.

## Dependency ordering

P1 ∥ P2 ∥ P3 ∥ P4 ∥ P5 (independent; one specialist run implements all five in separate commits, in that order).

## Risks

- P2 prunes history retroactively for sites above the cap (operator point D-4); audit log rows other than snapshots are never touched — test must prove that.
- Keyed-writes guard: any new repository write method takes `*, tenant_key: str` (no default).
- Write-gate ceiling 2804 must not rise.
- Security-sensitive path: yes (input hardening) → `code-security-reviewer` scoping on this worktree + security-oriented review before the bundle (group operation 5 verification).

## Open questions

none blocking (D-4 value 20 reported to the operator).

## Dispatch log
2026-10-30 P1–P5 dispatched to nolte-engineering:fullstack-developer (one run) — done, five commits: a1763e435 (W-1), be2221266 (W-2), 56a76ab7a (S-1), 1cbbedd4e (S-2), b5108a4a8 (S-4). **Refutation (P1):** the premise "caps may live on `GardenPlanExport` because they equal the quotas" is wrong — `SiteService.create_location` (`site_service.py:182`) does not check the plan quota and `_check_quota` allows an already larger plan to shrink, so a site above 500 locations exists and its export would 500 with a cap on the export model (measured: `test_the_export_of_a_site_above_the_quota_is_still_written` fails in that variant). Done instead: subclass `GardenPlanImportDocument(GardenPlanExport)` with `max_length` on the three lists, used by `_read_document`; `_finding_of` maps `too_long` on the top-level lists to `plan.quota_exceeded` (GP-NFR-017, already translated in the UI). Behaviour change: a 501-location file is a full 422 also on `dry_run` (was: report with `plan.quota_exceeded`). W-2: `MAX_SNAPSHOTS_PER_SITE = 20` in `garden_plan_import.py`; `_write_audit` → `_prune_snapshots(txn, write)` (AQL `LET keep … LIMIT @cap`, deletes only `op == "import_snapshot"` of the same site+tenant outside `keep`), no new public repository method; fake mirrors it; spec GP-NFR-055 clause + REQ-053 changelog 1.6; docs api-reference.md:258 DE/EN, user-guide locations-substrates.md (DE l.504, EN l.496), i18n restore-dialog help text `pages.json` ~l.6407 DE/EN. S-1: iterative `_count_points`, called once; HEAD measured 500 (`RecursionError`, 496 frames) at depth 5000 → now 422 `VALIDATION_ERROR` `details == [("props.path.inner","validation.invalid",0)]`; api test with `raise_server_exceptions=False` (fixture switch added) + unit depth-5000 test (5003 points). S-2: `await run_in_threadpool(PlanImportRequest.model_validate_json, raw)`; OpenAPI byte-identical (`cmp`). S-4: CSP `default-src 'none'`; test l.173, `main.py` comment, GP-NFR-052(e), REQ-032 l.309 (+ changelog lines), docs l.187 DE/EN; new engine test `test_the_document_has_no_style_element_or_attribute`; `grep -rn "unsafe-inline" src/backend spec/req docs/` → only the two changelog lines. Checks (verbatim tails): ruff `All checks passed!` / `2849 files already formatted` EXIT=0; mypy ratchet `3419 findings now, 3434 recorded … GREEN` EXIT=0; pytest selection (api + import/service units + models + keyed-writes + write_route_gates + req053 matrix) `4408 passed, 182 warnings in 320.35s` EXIT=0; `tests/integration/test_garden_plan_import.py` (ArangoDB reachable) `40 passed in 18.49s` EXIT=0; `tests/unit/guards` `3005 passed, 19 skipped, 5 deselected, 83 warnings in 781.75s` EXIT=0; mkdocs strict: only the 3 catalog nav warnings; `pre-commit run --files` on both spec files: all Passed/Skipped EXIT=0. Falsifications: old export model → 4 tests fail; without `_prune_snapshots` → `assert 21 == 20`; HEAD `_count_points` → both new tests `RecursionError`. Operator points: cap 20 prunes retroactively in one transaction (no batch limit); `dry_run` with oversized lists is now a 422. Open for the group verification: security-oriented review of `_prune_snapshots` (AQL bind vars, tenant+site filter), `_read_document`/`_finding_of`, `_count_points`, router (import parse, CSP); UI review of the one i18n string; this artifact's REQ-053 line anchors shifted by one (new changelog line).
