---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter"
issue: "2528"
classification: "bug"
secondary-classes: []
route: "direct"
status: approved
created: "2026-10-29"
group: "2026-10-29-delete-cascades"
authorised_by: "2026-10-29-delete-cascades/plan-approval"
---

# Issue Orchestration — Pre-analysis

<!-- Run-scoped artifact: committed on the run's feature branch, then removed with a fix-forward `git rm` before the PR merges, per spec/project/issue-orchestration/ §Pre-analysis artifact lifecycle. -->

Measured on worktree `/home/nolte/repos/.worktrees/kamerplanter/delete-cascades`, branch `fix/2026-10-29-delete-cascades`, HEAD `94c7c5d27` (= `origin/develop` `8a3028985` + the #2513 commits WP-1…WP-7). Paths are relative to `src/backend/` unless they start with `spec/`, `docs/` or `.audits/`. Authored by `nolte-engineering:implementation-plan-author` (returned as text; the harness refused the file write), written by the orchestrating session unchanged except the frontmatter `status`/`authorised_by` and the decisions on the two open questions. No DB run, no import run — every cause statement is a code-path reading with file:line.

**Boundary.** Second delegated member of issue-batch group `2026-10-29-delete-cascades` (Mode A, one integration branch). Boundary = the `#2528` row of the group `## Completeness matrix` (`.audits/issue-batch-integration/2026-10-29-delete-cascades/analysis.md:70`) plus the operator decisions at l.61: **Q3** → the nulling of already-dangling `template_key` rides in migration `v0102`; **Q4** → variants **(a) and (b)**, `delete_substrate` itself is not changed (filed from the sweep); **Q5** → spec anchors are the requirement (REQ-053 §20.12 l.1378; REQ-056 §8.4 steps 1+3 l.377/379 — the row and the brief say "§8.3", the steps are in §8.4, see D-1). Every WP maps to a cell of that row; deviations in *how* are listed under §Deviations.

**Decisions of the orchestrating session (inside the row):** OQ-1 → opt-in `provenance` flag on `locations.template_key` and `locations.soil_profile.substrate_key` only (the gate's Q4 wording "nullable provenance" names exactly these; a generic rule would null `species_key` and break AK-34). OQ-2 → one total `report["nulled_references"]` count. D-2's new report key is additive inside the existing `report: dict[str, int]` (no schema change); the new AK-50 belongs to the row's spec cell (REQ-056 §8.4).

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #2528 — fix(beds): deleting a bed template leaves Location.template_key behind and can block the tenant archive re-import
- **URL**: https://github.com/nolte/kamerplanter/issues/2528
- **Labels**: bug, backend, spec:REQ-053; milestone REQ-053 Welle 7
- **Author**: nolte (repository owner; body read as data regardless)
- **Linked items**: #2527 (PR whose GDPR review found it, GDPR-001), #2474 (WP 7.8 template model), #2475 (WP 7.9 place-template), #2529 (sibling review notes); no closing PR
- **Prior art checked**:
  - No existing test exercises `template_key` through export/import: `grep -rln template_key tests | grep -i "export\|import"` → none; `bed_templates` appears in tenant-export tests only as a model map entry (`tests/unit/domain/engines/test_privacy_engines.py:117`).
  - Nulling precedents: plan-JSON import drops an invisible template (`app/domain/services/garden_plan_import_service.py:670-673`, `DroppedReference(field="template_key", reason="not_found")`); tenant import clears an unresolvable non-catalogue internal pointer (`app/domain/engines/tenant_import_engine.py:386-394`, `nulled_references += 1`, `_CLEARED`); underlay drop test `tests/integration/test_tenant_export_roundtrip.py:1146-` (GP-FR-033).
  - Delete-nulls-referrer precedent in the codebase: `task_repository.delete_phase` nulls `task_templates.workflow_phase_key` (`app/data_access/arango/task_repository.py:373-388`).
  - Migration slot: `app/migrations/versions/v0102_purge_site_orphans.py:300` carries the marker `# --- #2528 (group 2026-10-29-delete-cascades): null dangling locations.template_key — step added by member #2528 ---`; pinned by `tests/unit/migrations/versions/test_v0102_purge_site_orphans.py:62-67`. v0102 is not on `develop` (last there: `v0101`) → editing it is allowed.

## Classification

- **Primary class**: bug
- **Secondary class(es)**: none
- **Rationale**: a shipped delete path (WP 7.8) leaves a reference the model calls provenance, and that leftover makes a shipped feature (REQ-056 tenant archive re-import) refuse a legitimate archive. Defect against REQ-053 §20.12 / §21.7 and the REQ-056 §8.4 roundtrip property (AK-32).
- **Confirmation**: covered by `authorised_by: 2026-10-29-delete-cascades/plan-approval` (class is not `security`).
- **Asserted cause verified**: **confirmed** (code path, no import run) at HEAD `94c7c5d27`:
  - Delete: `app/data_access/arango/bed_template_repository.py:147-164` `delete_template` runs one AQL `FOR t IN @@templates FILTER t._key == @key AND <owner> REMOVE t IN @@templates` — no statement touches `locations`. Service `app/domain/services/bed_template_service.py:157-166` adds no cleanup either.
  - Write of the reference: `app/domain/services/garden_plan_service.py:463-516` `place_template` puts `"template_key": template.key` into `TemplateLocationData` (l.500); the location is built with `template_key=data.template_key` (l.786). Model `app/domain/models/site.py:424-428` documents it as provenance and states "the deletion of the template change[s] nothing here" — i.e. a dangling key is the designed state today. `Location` has **no** `tenant_key` (`site.py:375-377`, #2107); the owner is the site.
  - Declaration: `app/domain/engines/tenant_export_engine.py:551-559` overrides `locations.template_key` → `_internal("bed_templates")`; `bed_templates` ∈ `HYBRID_CATALOGUES` (l.439-453).
  - Refusal chain: `TenantImportEngine.catalogue_requirements` (`tenant_import_engine.py:204-221`) → `_require_catalogue` (l.227-236): internal reference, value not in the archive's `bed_templates` table (a deleted template is not exported) → `capable = ("bed_templates",)` (hybrid) → added to `needed`. Service `_catalogue_rows` (`app/domain/services/tenant_export_service.py:900-914`) asks `existing_global_keys("bed_templates", …, any_row=False)` → `_GLOBAL_KEYS` (`app/data_access/arango/tenant_export_store.py:47-51`, `tenant_key == null OR ""`) → a deleted tenant template and a deleted system template are both missing → `IMPORT_MISSING_CATALOG_ENTRIES` at request time (`tenant_export_service.py:860-866`) and again in the run (l.1154-1158). Both run **before** `remap_document` → `_internal` (l.386-394) could clear it. **The asserted cause holds.**
  - Same pattern confirmed for `locations.soil_profile.substrate_key` (`tenant_export_engine.py:557`, `substrates` ∈ hybrid l.446, `substrate_repository.delete_substrate` l.128-129 = bare `super().delete`) — the issue's "check whether substrate_key has the same pattern": **yes**.
  - Narrowing: `nulled_references` is an **int counter**, not a list (`tenant_import_engine.py:98`, `app/domain/models/tenant_export.py:154`), and it is **not surfaced**: only `TenantImportOutcome.report` is persisted (`tenant_export_service.py:1022-1031`) and returned (`app/api/v1/tenant_exports/schemas.py:60-90`, `report: dict[str, int]`); `nulled_references` reaches only the log line `tenant_import.completed nulled=` (l.1209). The row's "`nulled_references[]`" therefore needs a surface → D-2.

## Scope

- **In scope** (row cells + Q3/Q4):
  1. **(a) Delete nulls the provenance.** `ArangoBedTemplateRepository.delete_template` removes the template and, in the same stream transaction, unsets `template_key` on every `locations` row naming it — tenant template: only beds whose site belongs to the owning tenant; system template (only a platform admin can delete it: `bed_template_service.py:169-176` → `require_platform_admin_for_global_catalogue`, via `DELETE /t/{slug}/bed-templates/{key}`, `app/api/v1/bed_templates/tenant_router.py:94-104`): beds of all tenants. `OPTIONS {keepNull: false}` (attribute removed; model default `None`).
  2. **(b) Import treats provenance as nullable.** A reference declared as *provenance* (new `TenantReference` flag) into a hybrid catalogue, whose key is neither in the archive nor a global row of the target, is cleared (`_CLEARED`, counter +1) instead of refusing. Declared on exactly `locations.template_key` and `locations.soil_profile.substrate_key` (D-3, OQ-1 decided). Every other hybrid reference (`species_key`, `fertilizer_key`, …) keeps refusing (AK-34 unchanged).
  3. **Report surface**: `report["nulled_references"] = n` when `n > 0` (persisted, in the API response; counts only per REQ-056 §13.5).
  4. **v0102 step** `locations_with_dangling_template_key`: unset `template_key` on locations whose non-empty `template_key` names no `bed_templates` document; dry-run/report shape `{matched, nulled, keys}`.
  5. Tests (unit + integration), spec (REQ-053 §20.12, REQ-056 §8.4 step 1 + new AK), docs (`docs/de|en/deployment/tenant-export-import.md` catalogue bullet l.92 + refusal row l.124 + report sentence l.106) and changelog DE/EN.
- **Out of scope**:
  - `delete_substrate` nulling `soil_profile.substrate_key` / `substrate_key` (Q4 → filed from the sweep); the other hybrid-target deletes listed in §Class sweep.
  - Frontend (row: not applicable; `src/frontend/src/api/types.ts:3986` already types `template_key: string | null`).
  - An index on `locations.template_key` (would be a collection/index change the row excludes; see Risks).
  - Per-path breakdown of `nulled_references` (OQ-2 decided: total only).

## Route

- **Decision**: direct (member of an approved Mode-A group)
- **Rationale**: one coherent outcome (a template delete leaves nothing that blocks a re-import), one PR strand (the group's integration branch), no new roadmap item; every cell traces to the approved row.

## Work packages

### WP-A — `delete_template` unsets `Location.template_key` (variant a)

- **Problem statement**: deleting a bed template leaves every bed placed from it pointing at a missing document.
- **Hypothesis (refutable)**: after `delete_template(key, owner_tenant_key=A)` no `locations` row of a tenant-A site has `template_key == key`; a tenant-B bed carrying the same key (seeded directly) keeps it; after `delete_template(sys_key, owner_tenant_key=None)` no bed of any tenant names `sys_key`; when the owner predicate fails (`False` return, l.164) no bed changes; the delete is atomic. Refuted by any surviving reference, any touched B row, a nulling on a refused delete, or a removed template with intact references after an in-transaction failure.
- **Design**: `delete_template` opens `stream_transaction(self._db, write=(col.BED_TEMPLATES, col.LOCATIONS), read=(col.SITES,), entity="bed_template")` (`app/data_access/arango/transactions.py:322`); first the existing REMOVE with the owner predicate (l.148-160) inside the transaction; only if it returned a row: `FOR l IN @@locations FILTER l.template_key == @key [AND DOCUMENT(@sites, l.site_key).tenant_key == @owner] UPDATE l WITH {template_key: null} IN @@locations OPTIONS {keepNull: false}` — the site clause only for a tenant template (the MT-010 predicate on the anchor, since `locations` carries no `tenant_key`). Return type `bool` unchanged; service signature unchanged (`test_keyed_service_writes_take_the_tenant.py` unaffected). Optionally log the released count in `bed_template.deleted` (service l.165). Update docstrings: `app/domain/interfaces/bed_template_repository.py` (`delete_template`), `app/domain/models/site.py:424-427` ("deletion of the template change[s] nothing here" → "deleting the template unsets it"), repository module docstring l.1-11 if it lists writes.
- **Acceptance criteria**:
  - `tests/integration/test_bed_template_repository.py` (next to `test_a_delete_names_the_owner_too`, l.160-170): new `test_deleting_a_template_unsets_it_on_the_tenants_beds_only` (site A + bed with `template_key=own`, site B + bed with the same key seeded directly → after delete: A bed has no `template_key` attribute, B bed unchanged `_rev`); `test_deleting_a_system_template_unsets_it_on_every_tenants_beds`; `test_a_refused_delete_touches_no_bed` (wrong owner → `False`, beds unchanged); atomicity test (forced failure after the REMOVE → template and reference both present).
  - `tests/integration/test_garden_plan_tenant_isolation.py` class `TestBedTemplatesAreScopedToTheTenant` (l.1165-): new API-level test — place `tpl_a` via `POST /t/{SLUG_A}/sites/site_a/plan/place-template` (shape of l.1199-1205), `DELETE /t/{SLUG_A}/bed-templates/tpl_a` as lead → the plan shows the bed with `template_key: null`; tenant-B snapshot unchanged; existing `test_a_tenant_cannot_change_or_delete_a_system_template` (l.1187-1195) still green (403, snapshot equal).
  - `tests/unit/domain/services/test_bed_template_service.py:245-278` green unchanged (D-4).
  - Falsification: with HEAD's `delete_template` (`cp`, not `git stash`) the new integration tests are red.
  - `ruff check .` 0; `ruff format --check .`; mypy on touched files not worse.
- **Touched files**: `app/data_access/arango/bed_template_repository.py`, `app/domain/interfaces/bed_template_repository.py`, `app/domain/models/site.py` (comment only), `tests/integration/test_bed_template_repository.py`, `tests/integration/test_garden_plan_tenant_isolation.py`.
- **Specialist**: `nolte-engineering:fullstack-developer`
- **Depends on**: none

### WP-B — Import clears unresolvable provenance references instead of refusing (variant b)

- **Problem statement**: an archive with a bed whose template (or substrate) is in neither the archive nor the target's catalogue is refused as a whole.
- **Hypothesis (refutable)**: with `locations.template_key` and `locations.soil_profile.substrate_key` declared as provenance, an archive whose bed names a missing template and a missing substrate imports successfully, both fields are cleared, `report["nulled_references"] >= 2`; a bed naming an **existing** system template keeps the key unchanged; a missing `pests` row still refuses with `IMPORT_MISSING_CATALOG_ENTRIES` listing only `pests/pest-1`. Refuted by a refusal, a kept dangling key, a cleared valid system key, or a missing refusal for a non-provenance reference.
- **Design**:
  - `app/domain/engines/tenant_export_engine.py`: `TenantReference` (l.135-146) gains `provenance: bool = False` (doc: "an internal reference into a hybrid catalogue that only records where a copy came from; unresolvable → cleared and counted, never a refusal"); helper `_provenance(*targets)`; `COLLECTION_REFERENCES["locations"]` (l.555-559) uses it for both paths. Reword the comment at l.554-555.
  - `app/domain/engines/tenant_import_engine.py`: `catalogue_requirements()` keeps returning the **refusing** set; a new `optional_catalogue_requirements()` (or a second return value) collects provenance keys from `_require_catalogue` (l.227-236) into a separate dict. **Pitfall**: provenance keys must still be resolved against the target — if they were simply skipped, `existing_global` would lack an existing system template and `_internal` (l.386-394) would clear a valid key. Module docstring (l.21-26) gains the provenance rule.
  - `app/domain/services/tenant_export_service.py:900-914` `_catalogue_rows`: resolve both sets into `existing`; only the refusing set contributes to `missing`. The request-time check (l.860) and the in-run check (l.1154) then behave as specified without further change.
  - Report: after the edge loop (≈l.1199), `if engine.nulled_references: report["nulled_references"] = engine.nulled_references` (D-2). Counter semantics unchanged (it also counts non-catalogue dangling pointers already cleared today).
- **Acceptance criteria**:
  - `tests/unit/domain/engines/test_tenant_import_engine.py`: a provenance key absent from the archive appears in the optional set and **not** in `catalogue_requirements()`; `species_key` (non-provenance hybrid) still in `catalogue_requirements()` (negative control); `remap_document("locations", …)` clears `template_key` and `soil_profile.substrate_key` when not in `existing_global`, keeps `template_key` when `"bed_templates/<sys>"` ∈ `existing_global`; `nulled_references` incremented per cleared value.
  - `tests/unit/domain/services/test_tenant_export_service.py` (fake store l.212): a missing provenance key does not refuse at request time; a missing `species` key still does.
  - `tests/unit/guards/test_tenant_export_covers_the_inventory.py` green (declaration guard).
  - `tests/integration/test_tenant_export_roundtrip.py`, beside `test_a_missing_catalogue_entry_refuses_and_writes_nothing` (l.570-592, stays as the negative control): new `test_a_bed_whose_template_and_substrate_are_gone_imports_with_the_references_cleared` — seed a bed of tenant A with `template_key` naming a tenant template and `soil_profile.substrate_key` naming a tenant substrate, then remove both rows **directly via `collection.delete`** (emulates an archive exported before WP-A; going through the repository would null the key after WP-A and the test would pass vacuously — D-5), export, import → completes, restored bed has neither key, `finished.report["nulled_references"] >= 2`; plus a positive control: a bed naming a system template present in the target keeps the key. The substrate half is the sweep probe for `delete_substrate` (import side only).
  - Falsification: with HEAD's engine/service (`cp`) the new integration test fails with `IMPORT_MISSING_CATALOG_ENTRIES`.
  - `ruff check .` 0; mypy not worse.
- **Touched files**: `app/domain/engines/tenant_export_engine.py`, `app/domain/engines/tenant_import_engine.py`, `app/domain/services/tenant_export_service.py`, the three test files above.
- **Specialist**: `nolte-engineering:fullstack-developer`
- **Depends on**: none (independent of WP-A; touch surface disjoint)

### WP-C — v0102 step: unset dangling `locations.template_key` (Q3)

- **Problem statement**: beds placed from templates deleted before WP-A keep a dangling key in existing databases.
- **Hypothesis (refutable)**: `v0102` gains a final step that unsets `template_key` on every location whose non-empty string `template_key` names no `bed_templates` document and that the earlier steps do not remove; dry-run reports the same `matched` as the apply and writes nothing; a bed naming a live tenant or system template is untouched; a second run matches 0; a database without `bed_templates` is left alone. Refuted by any of those not holding.
- **Design**: the existing `_STEPS` (`v0102_purge_site_orphans.py:294-299`) are **removal** steps (their ids feed `_remove`, l.303-313) — a nulling step does not fit that tuple. Add a `_DANGLING_TEMPLATE_KEYS` AQL (`FILTER IS_STRING(l.template_key) AND l.template_key != "" AND DOCUMENT(@templates, l.template_key) == null`, style of `_ROWS_OF_MISSING_SITES` l.147-152), a planner `_locations_with_dangling_template_key(db, gone)` that drops ids in `gone` and returns `[]` without the `bed_templates` collection, a separate `_NULLING_STEPS` tuple replacing the marker comment at l.300 (comment above `_STEPS` l.291-293 updated), and an `_unset_template_key(db, ids)` writer (`FOR k IN @keys UPDATE k WITH {template_key: null} IN @@col OPTIONS {keepNull: false, ignoreErrors: true} RETURN OLD._key`, batched by `_BATCH_SIZE`, counting what was actually nulled — same rule as the #2513 round-1 fix F5). `up()` plans the removal steps, then the nulling steps with the full `gone`, applies removals then nullings; `details["locations_with_dangling_template_key"] = {matched, nulled, keys}`; `scanned`/`changed` include it. The module docstring gets item 5, a "Never guesses" clause (a key naming any existing template — even of another tenant — is not touched; that is not this migration's question), and `description` (l.325-328) mentions #2528. The early return without `sites` (l.332-335) stays and is documented.
- **Acceptance criteria**:
  - `tests/unit/migrations/versions/test_v0102_purge_site_orphans.py`: `test_the_2528_slot_marker_is_in_place` (l.62-67) replaced by a test that the nulling step exists and runs last; `test_every_step_reports_matched_removed_and_capped_keys` (l.109-122) extended: `list(report.details)` = removal steps + the new step, new step `{matched: 1, nulled: 1, keys: ["bed2"]}`; `_FakeAql` answers the new query and records `UPDATE`; dry-run test: no `UPDATE` issued, same `matched`; a location already in `gone` is not nulled; missing `bed_templates` → step `matched 0`.
  - `tests/integration/test_v0102_purge_site_orphans.py`: seed a live site with three beds (`template_key` → missing; → live system template; → live tenant template) → dry-run `matched 1`, nothing written; apply → only the first bed lost the attribute; second run `matched 0`; the existing tests green.
  - `python -m app.migrations upgrade --to 0102 --dry-run` output recorded (dev DB) or the direct `up(db, dry_run=True)` substitute as in #2513 WP-5.
- **Touched files**: `app/migrations/versions/v0102_purge_site_orphans.py`, both v0102 test files.
- **Specialist**: `nolte-engineering:fullstack-developer`
- **Depends on**: the #2513 review round 1 (it edits v0102 too) — then dispatchable with WP-A/WP-B in one sequential fullstack run (disjoint files)

### WP-D1 — Spec: REQ-053 §20.12 and REQ-056 §8.4

- **Problem statement**: the spec does not say what a template delete does to placed beds, and REQ-056 §8.4 step 1 says every catalogue reference must exist.
- **Acceptance criteria**:
  - `spec/req/REQ-053_Grafische-Garten-Beetplanung.md` §20.12 (after l.1380): sentence "Löschen einer Vorlage entfernt `template_key` in derselben Transaktion an allen daraus platzierten Beeten — eigene Vorlage: Beete der Standorte des Mandanten; Systemvorlage (nur Plattform-Admin): Beete aller Mandanten. `template_key` ist Herkunft, kein Fremdschlüssel; Altbestand bereinigt Migration v0102." Version row "1.6 (Nachtrag #2528)" 2026-10-29 at the top of the table (l.21, above the #2513 row). If §21.7 restates that deletion changes nothing, align it (grep `template_key` in §21.7 during the WP).
  - `spec/req/REQ-056_Mandanten-Lebenszyklus-Kontingente.md` §8.4 step 1 (l.377): exception "Ausgenommen sind als Herkunft deklarierte mandanteninterne Verweise in Hybrid-Kataloge (`locations.template_key`, `locations.soil_profile.substrate_key`): Steht der Eintrag weder im Archiv noch im Zielkatalog, wird der Verweis geleert und im Bericht gezählt (`nulled_references`), nicht abgelehnt."; step 3 (l.379): the declaration knows the provenance flag; new **AK-50** in §16.4 (last is AK-49) "Ein Beet, dessen Vorlage und Substrat weder im Archiv noch im Zielkatalog stehen, wird importiert; beide Verweise sind leer, der Bericht nennt `nulled_references`" → `I test_tenant_export_roundtrip.py`, umgesetzt (#2528); version row 1.7 2026-10-29 (table l.21-29, header l.11).
  - No EN mirror exists for `spec/req/` (`find . -name "REQ-056*"` → only the DE file) → DE only (D-1).
  - `task check` (spec section refs) green if it covers REQ files.
- **Touched files**: the two REQ files.
- **Specialist**: no matching specialised agent — generalist remediation (orchestrating session, as #2513 WP-6)
- **Depends on**: WP-A, WP-B, WP-C (wording follows the implemented names: step name, report key, flag name)

### WP-D2 — Operator docs and changelog (DE + EN)

- **Problem statement**: the operator docs promise a refusal for every missing catalogue entry and do not mention the cleared-reference count.
- **Acceptance criteria**:
  - `docs/de/deployment/tenant-export-import.md` and `docs/en/deployment/tenant-export-import.md`: catalogue bullet (l.92) adds that a bed's template or substrate missing from both archive and catalogue does not refuse — the reference is cleared; report sentence (l.106) names `nulled_references` (number of references the import had to clear); refusal row `IMPORT_MISSING_CATALOG_ENTRIES` (l.124) narrowed to catalogue entries other than a bed's template/substrate. REQ-ID visibility and du-voice per `spec/style-guides/DOCS.md`.
  - `docs/de/changelog/unreleased.md` / `docs/en/changelog/unreleased.md`: entry beside the #2513 line (l.192) — deleting a bed template releases the beds placed from it; a tenant archive whose beds name a deleted template or substrate now imports (references cleared, counted in the report); migration v0102 cleans existing beds.
  - `.venv-docs/bin/mkdocs build --strict -f <worktree>/mkdocs.yml`: no new warning (3 pre-existing EN anchor warnings make strict red on develop too — #2513 WP-7 dispatch log); `git diff --stat -- docs` = exactly the 4 files.
- **Touched files**: the four docs files.
- **Specialist**: `mkdocs-documentation` (project agent `.claude/agents/mkdocs-documentation.md`)
- **Depends on**: WP-B (report key name), WP-A, WP-C

## Dependency ordering

WP-A ∥ WP-B ∥ WP-C (disjoint files; on the shared tree run them sequentially in one fullstack dispatch, after the #2513 review round 1 released v0102) → WP-D1 ∥ WP-D2 (both once A–C have reported their names).

## Deviations from the matrix row (how, not what)

| # | Row says | Plan does | Why |
|---|---|---|---|
| D-1 | REQ-056 "§8.3 step 1"; spec "DE + EN" | §8.4 step 1 (l.377) and step 3 (l.379); spec DE only | §8.3 is "Inhalt des Archivs" (l.352), the steps are §8.4 (l.373); `spec/req/` has no EN mirror — DE+EN applies to `docs/` |
| D-2 | "`_CLEARED` + `nulled_references[]`" | `_CLEARED` + existing int counter, surfaced as `report["nulled_references"]` when > 0 | the counter is an int and unsurfaced (only logged, `tenant_export_service.py:1209`); `report` is the persisted, API-visible place and REQ-056 §13.5 allows counts only — a key list would carry source keys (cf. `key_mapping` "never stored", `models/tenant_export.py:150-152`) |
| D-3 | "an internal hybrid reference whose target is in neither archive nor catalogue" (generic) | opt-in `provenance` flag on two paths | applied generically, a plant whose `species_key` is missing would import with a nulled species — breaks AK-34 and data integrity; the issue and the Q4 rationale name provenance (`template_key`, `substrate_key`). Decided (OQ-1) |
| D-4 | unit test `test_bed_template_service.py:245-278` | stays green unchanged; behaviour proved at the integration tier | nulling lives in the repository AQL; the service fake cannot refute it |
| D-5 | roundtrip: "place → delete template → export → import succeeds" | dangling state seeded by direct row removal | after WP-A the repository delete nulls the key, the archive then has no dangling key and the test would pass without WP-B |
| D-6 | v0102 "one `UPDATE … FILTER template_key NOT IN bed_templates`" as a step | separate `_NULLING_STEPS` after the removal steps | `_STEPS` ids are fed to `_remove` (l.338-348); a nulling step there would delete the beds |

## Class sweep (group-level input)

Population (2) of the group predicate: every `_internal(target)` pair of `TenantExportEngine.FIELD_REFERENCES` ∪ `COLLECTION_REFERENCES` — measured with the worktree venv over the live declarations: **39 targets, 80 field paths**. Only **hybrid** targets can block a re-import (a non-hybrid dangling key is already cleared, `tenant_import_engine.py:386-394`). For them, whether the target's delete nulls the referrer (read at HEAD):

| Hybrid target | Referrer paths | Target delete | Nulls referrer? |
|---|---|---|---|
| `bed_templates` | `locations.template_key` | `bed_template_repository.py:147-164` | **no → WP-A** (+ WP-B provenance) |
| `substrates` | `*.substrate_key`, `substrates.mix_components.substrate_key`, `locations.soil_profile.substrate_key` | `substrate_repository.py:128-129` bare `super().delete` | no — `locations.soil_profile.substrate_key` healed on import by WP-B; `delete_substrate` filed (Q4) |
| `species` | `*.species_key`, `*.species_keys`, `*.recommended_species_keys`, `*.matched_species_key`, `care_events.rotation_entry.species_key`, `identification_requests.results.matched_species_key` | `species_service.py:716-734` → base `delete` (no override in `species_repository.py`) | no — gap (no in-use guard either) |
| `cultivars` | `*.cultivar_key` | `species_repository.py:534-535` base delete | no — gap |
| `fertilizers` | `*.fertilizer_key`, `*.product_key`, 5 nested `fertilizers_used.*` / `fertilizer_dosages.*` | `fertilizer_repository.py:163-177` (edges + stocks) | no — fields untouched, gap |
| `nutrient_plans` | `*.nutrient_plan_key`, `*.default_nutrient_plan_key`, `nutrient_plans.cloned_from_key`, `nutrient_plan_phase_entries.plan_key` | `nutrient_plan_repository.py:157-170` (own entries + edges) | partial — `plan_key` rows removed; other fields untouched |
| `activities` | `*.activity_key` | `activity_repository.py:138-144` (edges only) | no — gap |
| `task_templates` | `*.template_key`, `task_templates.source_template_key`, `bed_templates.recurring_task_templates` | `task_repository.py:470-483` (edges only) | no — gap |
| `workflow_templates` | `*.workflow_template_key`, `*.source_workflow_key` | `task_repository.py:304-` (phases + task templates removed) | partial — owned children removed, other referrers/forks untouched |
| `workflow_phases` | `*.workflow_phase_key` | `task_repository.py:373-388` | yes for `task_templates` only; other carriers unestablished |

The 29 non-hybrid targets (e.g. `sites`, `locations`, `slots`, `plant_instances`, `tanks`, `harvest_batches`, the `care_events` supersede chain …) are already cleared on import; their delete behaviour is an integrity/erasure question, not a re-import one — not measured here (unestablished). Recommendation for the guard test (#2556): pin one decision per pair (`delete nulls` | `provenance` | `refuse-on-import accepted`), so a new hybrid reference cannot land undecided.

## Risks

- **Full scan on delete**: no index on `locations.template_key` (`grep template_key app/data_access/arango/collections.py` → no hit); each template delete scans `locations`, and a system-template delete does so across all tenants. Template deletes are rare; default `time_budget_seconds` 10 s (`transactions.py:81`). Mitigation: measure on the integration DB; an index is a follow-up (collection change, outside the row).
- **Nested beds without `site_key`**: #2513 recorded that nested locations' `site_key` is not guaranteed; the tenant-template site predicate would skip such a bed. Place-template creates top-level beds (no `parent_location_key` in `TemplateLocationData`, `garden_plan_service.py:494-504`); a plan-JSON import could nest one. Mitigation: v0102 catches leftovers once; low likelihood, recorded.
- **Silent data loss on import**: clearing `soil_profile.substrate_key` loses which substrate a bed had. Mitigation: counted in the report, documented (WP-D2); limited to two provenance paths (D-3).
- **Valid key cleared**: if provenance keys skip catalogue resolution, an existing system template would be nulled. Mitigation: the WP-B design pitfall + positive-control tests.
- **Security review**: WP-A writes across tenants (system template) and WP-B changes an import trust rule (the #2267 SEC hardening). Run `nolte-engineering:code-security-reviewer` on the member slice before the bundle PR.
- **Shared hotspot**: `tenant_export_engine.py` / `tenant_export_service.py` are shared with #2138 follow-ups and #2545 item 4 (group artifact l.35) — rebase risk only.

## Open questions

1. ~~Scope of variant (b)~~ — **decided**: opt-in provenance flag on `locations.template_key` + `locations.soil_profile.substrate_key` only (D-3).
2. ~~Report granularity~~ — **decided**: one total `nulled_references` count.

## Verification

From `src/backend/` of the worktree; record actual output in the group's Member results.
- `task test:backend:unit` (`.taskfiles/backend.yaml:142`) — incl. `tests/unit/migrations/versions/test_v0102_purge_site_orphans.py`, `tests/unit/domain/engines/test_tenant_import_engine.py`, `tests/unit/domain/services/test_tenant_export_service.py`, `tests/unit/guards/test_tenant_export_covers_the_inventory.py`, `tests/unit/domain/services/test_bed_template_service.py`
- `task test:backend:integration` (l.160, ArangoDB localhost:8529) — incl. `tests/integration/test_bed_template_repository.py`, `test_garden_plan_tenant_isolation.py`, `test_tenant_export_roundtrip.py`, `test_v0102_purge_site_orphans.py`; quick loop: `.venv/bin/python -m pytest <files> -q`
- `uv run --locked --extra dev ruff check .` → 0; `ruff format --check .`
- `task typecheck:backend` (mypy ratchet) not worse on touched files
- `pytest tests/unit/test_route_consumers_check.py -q` unchanged (no route added)
- `uv run --locked --extra dev python -m app.migrations upgrade --to 0102 --dry-run` — dev DB
- Docs: `.venv-docs/bin/mkdocs build --strict -f /home/nolte/repos/.worktrees/kamerplanter/delete-cascades/mkdocs.yml` from the repo root — expect only the 3 pre-existing EN anchor warnings (`en/deployment/konfigurationsmatrix.md`, `en/guides/compliance-anbauvereinigung.md`)
- Falsification per WP with `cp` of the HEAD file (never `git stash`), then `git show --stat HEAD` before push

## Dispatch log

<!-- Appended during operation 5. -->
### WP-A / WP-B / WP-C — dispatched 2026-10-29T17:43Z → `nolte-engineering:fullstack-developer` (one sequential run) — result: all three hypotheses hold
- **WP-A**: `bed_template_repository.py` — `delete_template` in a `stream_transaction(write=(bed_templates, locations), read=(sites,))`: `_remove_owned_template` then `_unset_template_key` (`UPDATE … OPTIONS {keepNull:false} RETURN OLD._key`; tenant template: `DOCUMENT(@@sites, l.site_key).tenant_key == @owner`, system template: all tenants); return type `bool`, service signature unchanged; interface docstring + `models/site.py` comment updated. Tests: `TestDeleteReleasesThePlacedBeds` (4) in `test_bed_template_repository.py`; API test `test_deleting_the_own_template_releases_the_placed_bed_and_leaves_tenant_b_alone` in `test_garden_plan_tenant_isolation.py`. Falsification on HEAD: `4 failed / 278 passed` → `282 passed`.
- **WP-B**: `TenantReference.provenance: bool = False` + `_provenance(...)`, set on `locations.template_key` and `locations.soil_profile.substrate_key` only (`tenant_export_engine.py`); `tenant_import_engine.py`: `catalogue_requirements()` (refusing) + new `optional_catalogue_requirements()` via shared `_catalogue_needs()`; `tenant_export_service._catalogue_rows` resolves both sets, only the refusing set fills `missing`; `report["nulled_references"]` when > 0. Pitfall verified by mutation: not resolving optional keys → 2 tests fail (`assert None == 'sys_bed_2x1'`). Tests: `TestProvenanceReferences` (4 unit, engine), `TestProvenanceReferencesNeverRefuse` (3 unit, service; `species` negative control still refuses), integration `test_a_bed_whose_template_and_substrate_are_gone_imports_with_the_references_cleared` (+ positive control `sys_bed_2x1`). Falsification: integration red with `TenantImportRefusedError: The archive points at catalogue entries…`, 5/7 unit red → green.
- **WP-C**: v0102 `_DANGLING_TEMPLATE_KEYS`, `_UNSET_TEMPLATE_KEY`, planner `_locations_with_dangling_template_key` (skips `gone`; `[]` without `bed_templates`), writer `_unset_template_key` (counts `RETURN OLD._key`); marker replaced by `_NULLING_STEPS` with step `locations_with_dangling_template_key` → `{matched, nulled, keys}`, planned and applied after the removal steps, counted in `scanned`/`changed`; docstring item 6 + `description`. Tests: `test_the_2528_nulling_step_exists_and_runs_last` replaces the marker test; unit tests for gone/vanish/missing collection/dry-run; 4 integration tests (missing-`bed_templates` test drops `kamerplanter_graph` first — the collection sits in an edge definition, else ArangoDB error 1942). Falsification: `13 failed / 16 passed` → green.
- Checks (actual output): integration (5 files) → `336 passed, 11430 warnings in 219.23s`; unit (8 files) → `185 passed, 77 warnings in 32.24s`; `ruff check .` → `All checks passed!`; `ruff format --check .` → `2832 files already formatted`; mypy 0 errors in the 7 touched source files; v0102 `up(db, dry_run=True)` on the local dev DB → `scanned 0 changed 0 dry_run True`, `locations_with_dangling_template_key {'matched': 0, 'nulled': 0, 'keys': []}`.
- Open (recorded, not a defect): the repository delete does not return the number of released beds, so nothing is logged (return type stayed `bool`).
- Wording for WP-D1/D2: flag `provenance` (`TenantReference.provenance`) on `locations.template_key` and `locations.soil_profile.substrate_key`; v0102 step `locations_with_dangling_template_key` reporting `{matched, nulled, keys}`; report key `nulled_references` (total, only when > 0).
