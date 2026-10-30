# Pre-analysis: #2544 GP-ACC-054 / GP-ACC-055 (transient, removed before merge)

Class: bug / missing behaviour behind two MUST acceptance criteria (found by the generated acceptance matrix, WP 6.1). Source: issue #2544. Authorised under operator autonomy 2026-10-09 / 2026-10-30 (partition 2026-10-29 single). Requirements: spec rows GP-FR-070, GP-FR-137, GP-ACC-054, GP-ACC-055 in spec/req/REQ-053_Grafische-Garten-Beetplanung.md (U_gate: spec anchors).

## Established (develop 8c5f69e2c)
- 054: `POST /planting-runs/mixed-culture` (`planting_run_service.create_mixed_culture`, ~l.247; reservation in `planting_reservation_service.py`) creates one run per species with its own `row_assignment`; `domain/models/planting_run.py` ~l.49-58 `check_row_assignment` validates one list only. Nothing checks that the sets of one mixed culture are disjoint. Spec: overlapping sets (`[1,2]` and `[2,3]`) answer 422. Also required by the issue: a test that every slot of a row carries the entry the row is assigned to.
- 055: `not_applicable_reason` (`domain/engines/crop_rotation_validator.py` ~l.143) turns the rotation check off for `planter`/`tent`/`shelf` unconditionally (`ROTATION_OFF_LOCATION_TYPES`) and for `Location.rotation_exempt` (bool, default False, `domain/models/site.py` ~l.441, API schemas `api/v1/locations/schemas.py` ~l.122, PATCH column list `site_service.py` ~l.29, privacy manifest `data_export_engine.py` ~l.601, `validate-planting` docs in `api/v1/locations/tenant_router.py` ~l.455). No per-bed switch-ON exists. Spec GP-FR-137: off by default for tent/shelf/planter, "je Beet einschaltbar"; GP-ACC-055: after switching one of the three on, only that location returns the rotation hint.

## Design (specialist may refute with evidence; record the decision)
- D-1 (054): in `create_mixed_culture` (before any write) the `row_assignment` sets of the entries must be pairwise disjoint; overlap -> `PlanError`-style 422 with a typed code (follow the nearby error-code naming, e.g. `layout.row_overlap`/`row_assignment.overlap`), naming the offending entries and rows; entries without row_assignment are not part of the check; test via API (`tests/api`) and service unit; plus the test that every slot of an assigned row carries the entry's run (layout calculator/reservation). Docs: api-reference error table DE/EN, spec status table row (§11.1-11.3) update.
- D-2 (055): additive tri-state switch: new optional `Location.rotation_enabled: bool | None = None` (None = type default; True = rotation check ON even for planter/tent/shelf; False = off). Precedence: `rotation_exempt` True -> off (existing, wins); else `rotation_enabled is True` -> on; else type default. PATCH/PUT with both `rotation_exempt=true` and `rotation_enabled=true` -> 422. Wire through model, API schema (create/patch/response), site_service PATCH columns, privacy manifest (`test_every_field_of_a_collection_is_disclosed`-style guard), export/import of locations if the plan export lists location fields (check `ExportLocation` and the DSGVO manifest guard), OpenAPI example/contract tests, and the frontend where `rotation_exempt` is already editable (mirror it; if there is no UI for rotation_exempt, add none and report). If a cleaner design emerges (e.g. replacing the pair by one tri-state with a migration), say why and choose the smaller blast radius.
- D-3 Acceptance: tests tagged `GP-ACC-054` / `GP-ACC-055` (see how `scripts/gp_acc_matrix.py` finds tags), then remove both entries from `spec/e2e-testcases/GP-ACC-gaps.json` and regenerate `spec/e2e-testcases/GP-ACC-matrix.md` (`python3 scripts/gp_acc_matrix.py --write`); the guard `test_req053_acceptance_matrix.py` must pass.

## Work packages
| id | what | specialist |
|---|---|---|
| P1 | D-1 mixed-culture disjointness + tests + docs | fullstack-developer |
| P2 | D-2 per-bed switch-on end to end + tests | fullstack-developer |
| P3 | D-3 matrix, gaps.json, spec status rows, docs | fullstack-developer |
Review after: python-code-reviewer (+ frontend part if touched).

## Risks
- A new Location field touches the privacy manifest, export, OpenAPI, frontend types: follow every guard that enumerates Location fields.
- No migration needed for an additive optional field (None default); say so explicitly.
