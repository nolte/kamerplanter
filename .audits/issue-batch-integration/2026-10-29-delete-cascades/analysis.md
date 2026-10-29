# Group pre-analysis: 2026-10-29-delete-cascades

> Run-scoped artifact. Committed on the integration branch, removed with a fix-forward
> `git rm` before the bundle merges. It must never reach the default branch, and it must
> never be hidden behind a `.gitignore` entry.
>
> Origin: `issue-backlog-partition` 2026-10-29 (`.audits/issue-backlog-partition/2026-10-29.md`,
> approved 2026-10-29T15:20:49Z). Research findings (anchored, 263 lines):
> `/tmp/claude-1000/-home-nolte-repos-github-kamerplanter/3b8ab2fd-9a15-4c4a-af66-6cd5d15568d2/scratchpad/handoff/2026-10-29-delete-cascades-research.md`.
> Measured against `develop` = `8a3028985`.

## Scope of this analysis

**Research question:** Is there one root mechanism behind "deleting a site leaves garden objects, care events and audit rows" (#2513) and "deleting a bed template leaves `Location.template_key` and blocks the archive re-import" (#2528), or one recurring defect class — and what exactly must a fix touch so that both deletes leave no orphan that escapes erasure or blocks a re-import?

**The group's single logical change, in one sentence:** Make deleting a site or a bed template cascade to its dependents — derived from the graph's edge definitions and the export engine's declared references instead of a hand-written list — so no orphan survives tenant erasure or blocks a tenant-archive re-import.

**Out of scope:**
- `sites.plan.underlay.attachment_key` on site delete — #2545 item 1, single after this group (shares `site_service.delete_site`).
- Nulling `*_key` **fields** on location-level referrers owned by other requirements (sensors, tasks, planting runs, calendar feeds, tanks, actuators, location assignments, succession plans): their *edges* are cut by the derived cascade, their rows stay; a field sweep is the class sweep's finding, filed, not widened into this bundle.
- GP-FR-153 (delete dialog names the affected children) — frontend, separate item.
- Substrate delete leaving `soil_profile.substrate_key` (`substrate_repository.py:128-129` bare `super().delete`) — same class, found by the sweep; see open question 4.

**Tier:** 2 — one repository, no published contract changes (the import becomes *more* lenient, additively; no route added, route-count pin untouched).

## Members

| Issue | Class | Admitting predicate | Evidence |
|---|---|---|---|
| #2513 | bug | thematic coupling (anchor) | `site_repository.delete_site` l.122-132 removes locations/slots (`CONTAINS`, `HAS_SLOT`), zones + `ZONE_EDGES` (l.131) and the site row; `grep -n "GARDEN_OBJECTS\|HAS_GARDEN_OBJECT\|CARE_EVENT\|AUDIT" site_repository.py` → 0 hits. `garden_objects` are selected by tenant erasure via `site_key IN <current sites>` (`tenant_erasure_engine.py:112`), so an object of a deleted site **escapes erasure permanently** |
| #2528 | bug | thematic coupling | `bed_template_repository.delete_template` l.147-164 only REMOVEs the template; `template_key` is `_internal("bed_templates")` (`tenant_export_engine.py:558`), `bed_templates` ∈ HYBRID_CATALOGUES (l.439-452); `TenantImportEngine._require_catalogue` (`tenant_import_engine.py:231-236`) → `_catalogue_rows` (`tenant_export_service.py:900-914`) → refusal l.861-866 / l.1154-1157 **before** the nulling path l.386-394 runs — the re-import block **holds** (code path; no test yet) |

**Dependency ordering:** independent members; recorded order #2513 → #2528 (the lifted edge helper of #2513 is reused by #2528's test fixture, nothing more).

**Shared touch surface:** none at file level between the two members' primary files. Shared with the rest of the backlog: `src/backend/app/domain/engines/tenant_export_engine.py` / `tenant_export_service.py` (#2528 ↔ #2138 pipeline, #2545 item 4), `site_service.delete_site` (#2513 ↔ #2545 item 1). Hotspots shared with the parallel group `plan-input-hardening`: next migration number (**v0102**), `enums.py`, `collections.py`, route-count pin — this group takes v0102 only if open question 3 is answered "yes"; the other group plans no migration (its research is pending — re-check before claiming the number).

## Mode decision

**Mode:** A — single strand.

**Reason:** removability criterion not met. Both members are `bug` with a cause verified against the code (records `asserted_cause.status: verified`), no `security` classification, no dependency outside the group's control, no outstanding review that could reject either. Acceptance is fixed at this gate by open questions 1–4; once answered, neither member is likely to be dropped. Overlapping edge-helper code profits from one strand.

## Structural finding

**Cluster shape:** class cluster.

**Root cause or defect class:** *delete without derived dependents.* Each delete path hand-lists what it removes (`delete_site` l.125-132; `delete_location` l.199-221 cuts `has_slot`/`contains`/`zone_covers` only; `delete_template` l.147-164; `delete_substrate` bare). The repository already owns the counter-pattern — `_edges_touching()` derived from `GRAPH_EDGE_DEFINITIONS` (`garden_plan_repository.py:79-93`, its docstring names `delete_location`'s hand list as what it replaces) and `_remove_edges()` (l.793-799), used by the plan batch's `_delete_locations/_delete_objects` (l.707-828, with the V-09 active-plant refusal l.768-791) — but no legacy delete uses it, and no field-level equivalent exists although `TenantExportEngine.FIELD_REFERENCES`/`COLLECTION_REFERENCES` already declare every `*_key` reference (SSOT).

**Process finding:** no delete-side guard exists. The guards cover tenant-erasure inventory (`tests/unit/guards/test_garden_plan_collections_are_in_the_erasure_cascade.py` pins "field ∈ anonymisation rules", never "parent delete reaches child"), account-erasure fields, write-side reference verification and object-storage deletes — so both members were silent. **To be filed as its own issue after this gate**, referencing `2026-10-29-delete-cascades`.

**Preventive change:** a guard test with two machine-readable populations: (1) for every vertex collection with a `delete_*` method, every edge in `_edges_touching(V)` is cut by that delete or allowlisted with a reason; (2) for every `_internal(target)` reference pair in `TenantExportEngine.FIELD_REFERENCES`, the target's delete nulls/removes the referrer **or** the import treats the reference as nullable — one pinned decision per pair.

**Recurrence fed to the portfolio loop:** finding class "hand-listed cascade / no derived dependents" — recurrence 2 within this group (#2513, #2528) + 2 siblings the research surfaced (`delete_location` partial, `delete_substrate` bare), to be reported to `continuous-improvement` with count 4 when the process issue is filed.

## Plan approval

**Authorised by:** `2026-10-29-delete-cascades/plan-approval`, covering the members, mode, and order above. Revoked for undispatched members by any structural regression until re-approved.

**Group requirement artifact (class cluster only):** proposed as in the precedent group `2026-10-09-consent-gates`: spec anchors serve as the requirement, no `requirements-elicit` run — REQ-053 GP-FR-024 (409 on active plants, l.385), GP-FR-101 ("physisch löscht nur die DSGVO-Kaskade", l.797), GP-FR-153 (l.479), §20.12 template model (l.1378), §20.13 SR-011 (every DELETE writes `garden_plan_audit` atomically, l.1388); REQ-056 §8.3 steps 1+3 (l.377, 379); NFR-011 R-25/R-26 (l.135-136); REQ-002 §"Kaskadierendes Löschen" (l.953-967). Each member's run traces its acceptance to these; an uncovered condition falls back to the member's own elicitation. **Operator confirms or asks for a `requirements-elicit` run at this gate.**

**Plan approved by operator:** 2026-10-29T16:05:17Z (AskUserQuestion). Decisions at the gate: Q1 → structure rows go, history rows (`care_events`, `garden_plan_audit`) stay; Q2 → 409 on active plants: yes; Q3 → migration v0102 with dry-run: yes; Q4 → #2528 variants (a)+(b), `delete_substrate` filed from the sweep; Q5 → spec anchors as the requirement; Q6 → process-finding issue filed after this gate.

## Completeness matrix

Columns derived from the repository: backend source (`src/backend/pyproject.toml`), migration (`src/backend/app/migrations/versions/`, last `v0101`), spec (`spec/`), tests (`task test:backend:unit|integration`, `.taskfiles/backend.yaml:142,160`), docs (`mkdocs.yml`, `docs/de|en`), frontend (`src/frontend/package.json`), config/workflows (`.github/workflows/`, `Taskfile.yaml`), generated indexes/pins (route-count pin `tests/unit/test_route_consumers_check.py`, `scripts/check_privacy_inventory.py`, `TenantErasureEngine.INVENTORY`; no checked-in OpenAPI).

| Member | Backend source | Migration | Spec | Tests | Docs | Frontend | Config / workflows | Generated indexes / pins |
|---|---|---|---|---|---|---|---|---|
| #2513 | lift `_edges_touching`/`_remove_edges` (`garden_plan_repository.py:79-99,793-799`) into a shared module; `site_repository.delete_site` l.122-132 cuts **every** edge of `_edges_touching(SITES)` (contains, has_season_state, located_at, has_forecast, has_weather_source_config, has_climate_normal, located_in_zone, has_irrigation_demand, has_garden_object, has_irrigation_zone) and removes the site's structure rows: `garden_objects`, `season_states`, `weather_forecasts`/`climate_normals`/`weather_source_configs` (via existing `delete_by_site` l.59), `irrigation_demands`; `delete_location` l.199-221 switches to the derived edge set (cuts `care_event_at`, `has_task`, `run_at_location`, `assigned_to_location`, `placed_in` edges too); `site_service.delete_site` l.141-143 refuses with 409 when a `plant_instances` row with `removed_on = null` references the site (V-09 one level up); history rows (`care_events`, `garden_plan_audit`) stay per open question 1 and SR-011 audit row is written; all inside one stream transaction. Check: `task test:backend:unit` + `task test:backend:integration` green, `ruff check` 0 | `v0102_purge_site_orphans.py`: remove `garden_objects`/`season_states`/`weather_*`/`irrigation_demands` whose `site_key` no longer resolves and dangling edges; `--dry-run` reports counts per collection. Check: `python -m app.migrations upgrade --to 0102 --dry-run` output recorded; unit test of the migration (open question 3; `not applicable` if answered "no") | REQ-053: new sentence under §20.13 / GP-FR-153 defining the site-delete cascade (structure rows go, history rows stay, 409 on active plants), DE canonical + EN mirror. Check: `task docs` strict build green; spec-drift check `task check` (section refs) | extend `tests/integration/test_irrigation_zone_repository.py:497-511` (`test_deleting_a_site_removes_its_zones_and_their_edges`) with garden_objects/care_event edges/season_states + tenant-B positive control; new `tests/unit/domain/services/test_site_service_refuses_active_plants.py`; migration unit test. Check: `pytest <files> -q` output recorded | `docs/de|en/changelog/unreleased.md` entry; `docs/de/user-guide/privacy.md:401,479` sentence on what a site delete removes. Check: `task docs` strict | not applicable — backend cascade only; GP-FR-153 dialog text is out of scope | not applicable — no workflow, Taskfile or settings change | not applicable — no route added (pin 890 stays), no new collection (erasure INVENTORY unchanged), no `*_by` field (privacy inventory unchanged); check: `pytest tests/unit/test_route_consumers_check.py` still 16 passed |
| #2528 | variant (a): `bed_template_repository.delete_template` l.147-164 nulls `template_key` on every `locations` row of the tenant (system template: all tenants) in the same AQL/transaction (`OPTIONS {keepNull:false}`); variant (b): `TenantImportEngine._require_catalogue` l.231-236 treats an internal hybrid reference whose target is in neither archive nor catalogue as nullable provenance → `_CLEARED` + `nulled_references[]` (precedents `garden_plan_import_service.py:670-673`, `tenant_import_engine.py:386-394`) instead of refusing. Check: unit + integration green, `ruff` 0 | nulling of already-dangling `template_key` rides in `v0102` (one `UPDATE locations FILTER template_key NOT IN bed_templates`); `not applicable` if open question 3 is "no" and variant (b) is chosen (import heals old archives) | REQ-053 §20.12: sentence "deleting a template nulls `template_key` on placed beds"; REQ-056 §8.3 step 1: internal hybrid references without a catalogue row are nulled and reported, not refused (only if variant (b)). DE + EN. Check: `task docs` strict | `tests/integration/test_garden_plan_tenant_isolation.py:1175-1205` (template delete → bed `template_key` null, tenant B untouched); `tests/integration/test_bed_template_repository.py:160-171`; `tests/unit/domain/services/test_bed_template_service.py:245-278`; `tests/integration/test_tenant_export_roundtrip.py:570-592` add place → delete template → export → import **succeeds** with `nulled_references` (+ substrate twin as the sweep probe). Check: `pytest <files> -q` output recorded | `docs/de|en/deployment/tenant-export-import.md:92,124` catalogue-refusal row reworded (only if variant (b)); changelog entry. Check: `task docs` strict | not applicable — no UI change (template picker already tolerates a missing template) | not applicable | not applicable — no route, no collection, no field shape change |

**Class sweep (fix bundle, one section):** predicate = `for V in vertex collections with a delete_*: _edges_touching(V) − edges cut by delete_*` plus `for (field, target) in FIELD_REFERENCES internal pairs: does target.delete_* null/remove field OR import treat it nullable`. Run once at group level; residual gaps (`delete_location` field referrers, `delete_substrate`, `delete_garden_object` path) are **filed** as one follow-up issue, not fixed here, unless open question 4 says otherwise.

## Class sweep (measured 2026-10-29T18:15Z on the integration branch, `ab33b0925`)

**Predicate (1):** for every vertex collection `V` with a repository `delete_*`: `edges_touching(V)` minus the edges that delete cuts (name-based scan of the method body; derived-set calls count as the full set). **Predicate (2):** every `_internal(target)` reference pair of `TenantExportEngine` — see the #2528 plan §Class sweep (39 targets, 80 paths; 10 hybrid targets, only `workflow_phases → task_templates` nulls its referrer today).

| V | delete | `edges_touching(V)` | residual (not cut) | verdict |
|---|---|---|---|---|
| `sites` | `delete_site` | 11 | — (derived set) | fixed by #2513 |
| `locations` | `delete_location` | 17 | — (derived set) | fixed by #2513 |
| `irrigation_zones` | `delete_zone` | 5 | — (derived `ZONE_EDGES`) | already derived (WP 7.1) |
| `garden_objects` | `delete_garden_object` | 3 | none | ok |
| `slots` | `delete_slot` → `_delete_slot_internal` | 7 | `log_slot`, `placed_in`, `run_planned_at`, `system_has_growbed` (cuts `adjacent_to`, `filled_with`, `has_slot`) | **residual → follow-up issue** |
| `bed_templates` | `delete_template` | 1 (`belongs_to_tenant`) | edge defined for templates but never written (`grep -rn BELONGS_TO_TENANT app/ | grep -i template` → none) | not a gap |
| `substrates` | `delete_substrate` (bare `super().delete`) | 1 (`uses_type`) | `uses_type` + the `substrate_key` referrers of predicate (2) | **residual → follow-up issue** (gate Q4) |
| `plant_instances` | base `delete` | 27 | 23 named edges not referenced by any dedicated delete (plants are mostly removed via erasure/run services — lower bound, unmeasured there) | **residual → follow-up issue** (listed, not scoped here) |

Predicate (2) residuals (hybrid targets whose delete does not null referrers): `substrates`, `species`, `cultivars`, `fertilizers`, `activities`, `task_templates`, partial `nutrient_plans`, `workflow_templates` — one decision per pair belongs to the guard issue #2556.

Helper duplicates found by the sweep (same derivation, different files): `planting_reservation_repository.py:60` (`_edges_touching` copy), `irrigation_zone_repository.py:50,596` (`_edges_touching_zones`, own `_remove_edges`) → same follow-up issue.

Sweep script and raw output: `scratchpad/class_sweep.txt` of the orchestrating session (name-based approximation; `delete_slot` and `bed_templates` re-checked by reading the method bodies).

## Risks

- **Blast radius of #2513.** The issue names 3 collections; the measured dependent set is ~20. A derived cascade is the right fix for the class but changes behaviour for REQ-046/047/037 rows (weather, season states, irrigation demands) on a site delete. Cost if wrong: data a user expected to survive a site delete disappears — mitigated by the 409 on active plants and the spec sentence.
- **History vs. structure decision (open question 1).** Deleting `care_events`/`garden_plan_audit` with the site contradicts GP-FR-101 and SR-011 and may collide with PflSchG/CanG retention (NFR-011) for treatment events; keeping them leaves `site_key`-scoped rows whose site is gone (reachable by tenant erasure, so no GDPR gap).
- **Migration number collision** with the parallel group `plan-input-hardening` (v0102). Mitigation: that group's research is pending; this group claims v0102 only after confirming, and the partition records the two groups must not both add a migration.
- **Prod data:** the purge migration deletes rows; dry-run on the prod snapshot first (operator's P-point rule), counts recorded in the member result.
- **Import leniency (variant b)** changes a refusal into a report; a reviewer may see it as weakening the catalogue contract. Mitigation: scope it to `_internal` hybrid references only, keep refusal for global catalogue entries (species etc.).

## Open questions for the operator

1. **Which site dependents go, which stay?** Recommendation: structure rows go (`garden_objects`, `season_states`, `weather_*`, `irrigation_demands`, zones, locations, slots) and every derived edge is cut; **history rows stay** (`care_events`, `garden_plan_audit` — tenant-scoped erasure and R-25/R-26 reach them, SR-011 stays consistent). This partially narrows #2513's ask (its title lists care_events and audit rows) — the artifact records the spec reason. Alternative: delete all three as the issue asks.
2. **409 on active plants when deleting a site** (GP-FR-024 one level up)? Recommendation: yes.
3. **Backfill migration v0102** purging already-orphaned rows and nulling dangling `template_key`? Recommendation: yes, with dry-run; it is the only way the GDPR gap (orphans escaping erasure) closes for existing data.
4. **#2528 variant:** (a) null on delete, (b) import treats internal hybrid references as nullable, or both? Recommendation: **both** — (a) stops new orphans, (b) heals archives exported before the fix and covers `substrate_key` without touching `delete_substrate` here. Include the two-line `delete_substrate` nulling as well (same class, measured gap), or file it from the sweep? Recommendation: file it from the sweep (keep the bundle on the two members).
5. **Requirement artifact:** spec anchors as listed (precedent), or a `requirements-elicit` run? Recommendation: spec anchors.
6. **Process finding** → file the guard issue now (after this approval), referencing the group id? Recommendation: yes.

## Member results

Filled during implementation. Each entry records the dispatched specialist and the
**actual output** of every declared check, never an assertion that it passed.

| Member | Specialist | Check | Actual output |
|---|---|---|---|
| #2513 WP-1 | nolte-engineering:fullstack-developer | `pytest tests/unit/data_access/arango/test_graph_edges.py tests/unit/data_access/arango/test_garden_plan_collections.py -q`; `ruff check .`; `ruff format --check .`; `pytest tests/unit/test_route_consumers_check.py -q` | `16 passed in 2.50s`; `All checks passed!`; `2825 files already formatted`; `16 passed` |
| #2513 WP-2 | nolte-engineering:fullstack-developer | `pytest tests/integration/{test_site_delete_cascade,test_irrigation_zone_repository,test_garden_plan_repository,test_garden_resource_repository,test_garden_plan_tenant_isolation}.py` (ArangoDB 3.12.12 local); `ruff check .`; `ruff format --check .`; `tests/unit -k site` | `1 failed, 358 passed` (failure = pre-existing strict XPASS benchmark, #2526, unrelated); `All checks passed!`; `2826 files already formatted`; `619 passed` |
| #2513 WP-3 | nolte-engineering:fullstack-developer | `pytest tests/integration/test_site_delete_cascade.py tests/integration/test_irrigation_zone_repository.py` (ArangoDB); unit+API tests; final combined run; `ruff check .`; `ruff format --check .` | `41 passed in 12.14s`; `4 passed`; `91 passed in 33.54s`; `All checks passed!`; `2828 files already formatted` |
| #2513 WP-4 | nolte-engineering:fullstack-developer | `pytest tests/integration/test_location_delete_cascade.py …` (in the 128-test set) | `128 passed in 37.38s` |
| #2513 WP-5 | nolte-engineering:fullstack-developer | `pytest tests/unit/migrations -q`; integration set incl. `test_v0102_purge_site_orphans.py`; `ruff check .`; `migration.up(db, dry_run=True)` on local dev DB | `1425 passed, 1 skipped in 142.76s`; `128 passed in 37.38s`; `All checks passed!`; `scanned=0 changed=0 dry_run=True` (stale dev DB; prod-snapshot dry-run still open) |
| #2513 review round 1 (F1–F9) | nolte-engineering:fullstack-developer | 6 integration files; unit/API `-k site` + non-service files; `ruff check .`; `ruff format --check .` | `353 passed`; `285 passed, 4502 deselected` + `97 passed`; `All checks passed!`; `2832 files already formatted`; mypy `site_repository.py` 17 (was 22), v0102 0 |
| #2528 WP-A | nolte-engineering:fullstack-developer | `pytest tests/integration/test_bed_template_repository.py tests/integration/test_garden_plan_tenant_isolation.py …` (in the 5-file set) | `336 passed` (set); falsification `4 failed / 278 passed` → `282 passed` |
| #2528 WP-B | nolte-engineering:fullstack-developer | unit engine/service/guard tests + `test_tenant_export_roundtrip.py` | `185 passed` (unit set); integration red `TenantImportRefusedError` → green |
| #2528 WP-C | nolte-engineering:fullstack-developer | `tests/unit/migrations/versions/test_v0102_purge_site_orphans.py`, `tests/integration/test_v0102_purge_site_orphans.py`; `up(db, dry_run=True)` | `13 failed / 16 passed` → green; dry-run `scanned 0 changed 0`, step `{matched 0, nulled 0}` |
| #2528 WP-D1 | generalist | `grep -c "#2528" spec/req/REQ-053_…md spec/req/REQ-056_…md` | `2`, `6` |
| #2528 WP-D2 | mkdocs-documentation | `.venv-docs/bin/mkdocs build --strict -f <worktree>/mkdocs.yml`; `git diff --stat -- docs` | `Aborted with 3 warnings` (the 3 pre-existing EN anchors, none new); 4 files +8/−6 |
| #2528 review round 2 (G1–G8) | nolte-engineering:fullstack-developer | integration (4 files); unit set incl. `tests/unit/guards`; `ruff check .`; `ruff format --check .` | `320 passed` (+1 spy expectation corrected → `1 passed`); `1 failed, 3192 passed, 19 skipped` (the failure = legacy-reader guard, fixed in `c3c2738d8`); `All checks passed!`; `2832 files already formatted` |
| group quality gate | quality-gate skill (Taskfile targets, uv shim) | `task lint:backend`; `task typecheck:backend`; `task test:backend -- -q -x --deselect <known XPASS benchmark>` (ArangoDB + TimescaleDB local) | `All checks passed!`; mypy ratchet `3419 findings now, 3434 recorded … GREEN`; `1 failed, 6914 passed, 7 deselected in 2939.86s (0:48:59)` — the failure `test_the_unresolved_receiver_count_does_not_grow` (`2805 < 2804`) fixed in the next row |
| group quality gate follow-up | nolte-engineering:fullstack-developer | `unres2.py \| grep -c ^GEN`; `pytest tests/unit/api/test_write_route_gates.py`; unit (data_access, v0102, tenant_export_service); integration (3 files) | GEN `1974 → 1961` (develop 1968; ceiling untouched); `151 passed`; `1769 passed`; `55 passed`; `ruff` clean; mypy 17 = 17 |
| #2513 WP-6 | generalist (no spec-authoring agent) | `grep -c "site.has_active_plants\|GP-ACC-061\|Standort löschen" spec/req/REQ-053_…md` | `4` |
| #2513 WP-7 | mkdocs-documentation | `.venv-docs/bin/mkdocs build --strict -f <worktree>/mkdocs.yml`; `git diff --stat -- docs` | `Aborted with 3 warnings in strict mode!` (3 pre-existing EN anchor warnings, identical on develop); 4 files, +4/−2 |
| | | | |

## Deviations

| Member | Kind | What changed |
|---|---|---|
| | | |

## Requirement coverage

| Member | Covered or fallback | Coverage check or the requirement it added |
|---|---|---|
| | | |

## Findings

| Finding | Source | Outcome | Reproduction | Issue |
|---|---|---|---|---|
| write-route-gate guard: genuine unresolved receiver count 2805 ≥ ceiling 2804 (new `doc_id.split`/`dict.fromkeys`/untyped locals in the delete + migration code) | check (quality gate, `task test:backend`) | fixed directly: str-typed helpers + annotations, count 1961 (< develop 1968), ceiling never raised | `test_write_route_gates.py` → `151 passed`; `unres2.py` GEN 1974 → 1961 | — |
| guard `test_legacy_reference_field_readers_are_decided` red: `_refuse_active_plants` (#2513 WP-3) names the bind variable `slot_keys` → undecided reader of `watering_logs.slot_keys` | check (unit suite, round 2 of #2528) | fixed directly: register entry `_ECHO` (compares `plant_instances.slot_key` with the site's own removed slots; no watering log is read) | `pytest tests/unit/guards/test_legacy_reference_field_readers_are_decided.py -q` → `8 passed` (commit `c3c2738d8`) | — |
| #2528 WP-A: tenant-template delete skips beds with empty `site_key` anchored only via `contains` under a tenant bed — Low | code-security-reviewer (+ python reviewer, suspected) | fixed directly | `test_a_nested_bed_without_a_site_key_is_released_through_the_containment_graph` red `'template_key' not in {...}` → green (22 passed); site resolved via `DOCUMENT(@@sites, l.site_key) || FIRST(FOR v IN 1..20 INBOUND l @@contains FILTER IS_SAME_COLLECTION(@@sites, v) …)` | — |
| #2528 WP-C: v0102 nulling UPDATE does not re-check at write time (bed re-templated between plan and apply would be nulled) — Low | both reviewers | fixed directly | unit red `(1, 1) == (1, 0)`, integration `test_a_bed_retemplated_between_plan_and_apply_is_not_nulled` red `2 == (2 - 1)` → green (31 passed); `_UNSET_TEMPLATE_KEY` re-checks at write time | — |
| #2528 WP-C: `template_key` in id form (`sites/<key>`) might resolve `DOCUMENT(@templates, …)` to another collection — Info | code-security-reviewer | measured, no change | ArangoDB 3.12.12: `DOCUMENT("bed_templates", "sites/x")` → `[None]` for an existing site x; comment added above `_DANGLING_TEMPLATE_KEYS` | — |
| `api/v1/bed_templates/tenant_router.py:102-103` docstring still says beds keep `template_key` as provenance (reaches OpenAPI) — Info | code-security-reviewer | fixed directly: docstring now says the beds' `template_key` is unset since it would name nothing; no `tests/api` assertion on the text | read | — |
| `TenantExportEngine.validate()` does not enforce the provenance contract (internal + hybrid target) and no guard pins the provenance path set — Suggestion D11 | python-code-reviewer | fixed directly | `TestTheProvenanceContract` red `DID NOT RAISE ValueError` → green (18 passed); `_require_provenance_contract` in `validate()` | — |
| `catalogue_requirements()`/`optional_catalogue_requirements()` + two `_catalogue_rows` calls = four archive passes per import — Suggestion D7 | python-code-reviewer | fixed directly | spy red `{'needs': 2, 'rows': 1} == {'needs': 1, 'rows': 1}` → green; `TenantImportEngine.catalogue_needs()` one pass, `_catalogue_rows(needs, *, resolve_optional)`; roundtrip spy `{'needs': 3, 'rows': 3}` (was 6 passes) | — |
| `test_a_missing_provenance_key_does_not_refuse_at_request_time` asserts only `created.key` — test health | python-code-reviewer | fixed directly | request-time test now asserts `[[]]` and no `bed_templates`/`substrates` query; roundtrip already asserted both (l.646f.) | — |
| count returned by `_unset_template_key` unused, released beds not logged — Info | both reviewers | fixed directly | repository logs `bed_template.beds_released` (`template_key`, `released_beds`); `capture_logs` test expects `[1]` | — |
| `soil_profile.substrate_key` as provenance is a domain decision (missing substrate row cleared silently) — Info | python-code-reviewer | accepted: gate Q4 named `substrate_key` explicitly; documented in REQ-056 v1.7 and docs | — | — |
| import stores `template_key: null`, repo and v0102 remove the attribute — cosmetic inconsistency | python-code-reviewer | accepted (both read as `None`; v0102 ignores null) | — | — |
| v0102 `DOCUMENT(e._to)` with a missing vertex collection (suspected error) | python-code-reviewer | measured, no change | `RETURN DOCUMENT("nonexistent_collection_x/x")` on ArangoDB 3.12.12 → `[None]`, no error; comment added at `_dangling_end` | — |
| `site_repository.py` contains-closure removes a bed re-homed to another site (`update_location` moves `site_key`, stale `contains` edge stays) — Medium | member verification pass (code-security-reviewer) | fixed directly | `test_a_bed_rehomed_to_another_site_stays_with_its_subtree_and_slots` red: `AssertionError: locations/moved / None is not None` → green; `_contains_closure(…, site_key=)` keeps hits with `site_key` null/""/equal only (`site_repository.py:348-372`) | — |
| `has_slot` branch takes a slot whose `location_key` points to another (tenant-B) location — Low, legacy data | code-security-reviewer | fixed directly | `…slot_reached_only_by_edge…` red: `document('slots/…') is None` → green; edge-only slot counts only with `location_key` null/"" (repo l.402, v0102 l.205) | — |
| `delete_site` repo call carries no `tenant_key`; service pre-check then unscoped write (MT-010 defence-in-depth) | both reviewers | fixed directly | `test_another_tenants_key_deletes_nothing` red: `DID NOT RAISE NotFoundError` → green; `_SITE_FOR_DELETE` filters `s.tenant_key == @tenant_key` (l.64), empty key → `ValueError` | — |
| v0102: `garden_objects` row with empty `site_key` linked only by a dangling `has_garden_object` edge loses the edge, keeps the row → unreachable (GDPR) — Low | code-security-reviewer | fixed directly | `test_an_unsited_garden_object_linked_only_from_a_gone_site_goes` red (`obj_gone_only` stayed) → green; new step `unsited_garden_objects_of_missing_sites` (v0102 l.165) | — |
| v0102 `REMOVE … OPTIONS {ignoreErrors:true}` + `removed=len(ids)` overstates the report — D1 | python-code-reviewer | fixed directly | unit `test_a_key_gone_before_the_apply_is_matched_but_not_counted_as_removed` red `(2, 2) == (2, 1)` + integration `test_remove_counts_only_what_was_actually_removed` red `None == 1` → green; `_remove` returns `int` via `RETURN OLD._key` (l.344/362) | — |
| zone tenant rule (strict equality) ≠ dependents rule (null/""/equal): zone with empty `tenant_key` keeps its row, loses its edge | python-code-reviewer | fixed directly | `test_an_unstamped_zone_goes_and_a_foreign_zone_stays` red (`zone_unstamped` stayed) → green; zones use the null/""/equal rule (l.74) | — |
| v0102 never captures a nested location with empty `site_key` whose parent is already gone | python-code-reviewer | fixed directly | `test_an_unsited_location_whose_parent_is_gone_goes_with_its_chain` red (`stranded` stayed) → green; `_LOCATIONS_OF_MISSING_SITES` (l.177) also takes `site_key`-less locations without an existing `contains` parent | — |
| 409 tests never seed a plant without the `removed_on` key (semantics unpinned) | python-code-reviewer | fixed directly (test gap only) | `test_a_plant_without_a_removed_on_field_refuses_the_delete` green on first run — semantics now pinned | — |
| `_edges_touching` copies in `planting_reservation_repository.py:60` and `irrigation_zone_repository.py:50,596` (`ZONE_EDGES` could be `edges_touching(IRRIGATION_ZONES)`) | both reviewers | filed with the class sweep (outside the member's files) | grep shown in WP-1 report | pending (bundle stage) |
| three definitions of "locations of a site": `get_location_tree` (`1..10 OUTBOUND contains`, no `site_key`-only beds) vs `_location_ids_of_site` (unbounded ∪ `site_key`) vs v0102 — delete removes beds the tree never shows | python-code-reviewer | filed (read path `get_location_tree` is outside the row) | bed at depth 11 or `site_key`-only → tree vs delete | pending (bundle stage) |
| no index on `plant_instances.site_key/location_key/slot_key`, `locations.site_key`, `garden_objects.site_key` (full scans inside the 10 s budget) — suspected | python-code-reviewer | measured: missing → filed at bundle stage | `grep -rn add_persistent_index app/ | grep -E "plant_instances|locations|garden_objects|slots"` → only `slots(location_key, slot_id)` unique index (`collections.py:2358`); none on `plant_instances.site_key/location_key/slot_key`, `locations.site_key`, `garden_objects.site_key` | pending |
| 409 predicate has no tenant filter: a tenant-B plant with `site_key` of site A would block A's delete — only via legacy data/direct DB (write-side verified #719/#1372) | code-security-reviewer | accepted by design (refuses only, never deletes; count is a bare number) | — | — |
| audit row of a legacy site with `tenant_key ""` would escape tenant erasure — not API-reachable | code-security-reviewer | recorded, no change (legacy sites are not deletable via API) | — | — |
| strict MkDocs build aborts on 3 EN anchor links (`konfigurationsmatrix.md` ×2, `compliance-anbauvereinigung.md`) | check (WP-7 docs build) | pre-existing on develop, not fixed in the bundle (unrelated files) | same build on develop → same anchors warn, `Aborted with 130 warnings` | — (docs-freshness scope; no issue filed by this group) |
| `.claude/plugin-adoption.yml` drifted (2 new nolte-shared skills); `check:plugin-shadowing` pre-commit hook rejects every commit | check (pre-commit on the artifact commit) | fixed outside the bundle | `task check:plugin-shadowing -- --refresh` → 2 inventory lines added; hook passes on PR #2557 | PR #2557 (chore, awaiting operator merge) |
| | | | | |
