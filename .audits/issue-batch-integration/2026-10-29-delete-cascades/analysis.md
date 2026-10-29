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
| `.claude/plugin-adoption.yml` drifted (2 new nolte-shared skills); `check:plugin-shadowing` pre-commit hook rejects every commit | check (pre-commit on the artifact commit) | fixed outside the bundle | `task check:plugin-shadowing -- --refresh` → 2 inventory lines added; hook passes on PR #2557 | PR #2557 (chore, awaiting operator merge) |
| | | | | |
