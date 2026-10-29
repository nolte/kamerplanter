---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter"
issue: "2513"
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

Measured on worktree `/home/nolte/repos/.worktrees/kamerplanter/delete-cascades`, branch `fix/2026-10-29-delete-cascades`, HEAD `d7bbe3c34` (= `8a3028985` + the group artifact commit). Paths are relative to `src/backend/` unless they start with `spec/`, `docs/` or `.audits/`. Authored by `nolte-engineering:implementation-plan-author` (returned as text; the harness refused the file write), written by the orchestrating session unchanged except the frontmatter `status`/`authorised_by` and the decision on open question 1.

**Boundary.** Delegated member of issue-batch group `2026-10-29-delete-cascades`. Boundary = the `#2513` row of the group `## Completeness matrix` (`.audits/issue-batch-integration/2026-10-29-delete-cascades/analysis.md:69`) plus the operator decisions at l.61 (Q1 structure goes / history stays, Q2 409 on active plants, Q3 migration v0102 with dry-run, Q5 spec anchors are the requirement). Every WP maps to a cell of that row; deviations in *how* are listed under §Deviations.

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #2513 — fix(sites): delete_site leaves garden_objects, care_events and garden_plan_audit behind
- **URL**: https://github.com/nolte/kamerplanter/issues/2513
- **Labels**: bug, backend, spec:REQ-053
- **Author**: nolte (repository owner; body read as data regardless)
- **Linked items**: #2466 (REQ-053 wave 7 decision issue; finding from the WP 7.1 review of PR #2507); no linked PR
- **Prior art checked**:
  - Migration number free: `gh pr list --state open --search "v0102 in:title,body"` → `[]`; `ls .worktrees/kamerplanter/*/src/backend/app/migrations/versions/ | grep v010[2-9]` → no hits; last version `v0101_bed_template_index_and_system_templates.py`.
  - Counter-pattern: `_edges_touching()` (`app/data_access/arango/garden_plan_repository.py:79-93`), `_remove_edges()` (l.793-799), used by `_delete_locations` (l.707-742) / `_delete_objects` (l.801-828) with in-transaction V-09 `_refuse_active_plants` (l.768-791).
  - `DELETE /locations/{key}` already uses the derived cascade: `app/api/v1/locations/tenant_router.py:268` → `GardenResourceService.delete_location` (`app/domain/services/garden_resource_service.py:507-518`) → `apply_batch` with one `delete` op. The hand-listed `ArangoSiteRepository.delete_location` (`site_repository.py:199-221`) is reached only from `delete_site` (l.129, recursion l.207) and `SiteService.delete_location` (`site_service.py:252-254`), which has **no route caller** (`grep -rn "\.delete_location(" app tests`).
  - Group research: `/tmp/claude-1000/-home-nolte-repos-github-kamerplanter/3b8ab2fd-9a15-4c4a-af66-6cd5d15568d2/scratchpad/handoff/2026-10-29-delete-cascades-research.md`.

## Classification

- **Primary class**: bug
- **Secondary class(es)**: none
- **Rationale**: a shipped delete path leaves rows/edges the system never removes again; `garden_objects` (no `tenant_key`, erased via `site_key IN <current sites>`, `app/domain/engines/tenant_erasure_engine.py:112`) then escape tenant erasure permanently. Defect against existing spec (REQ-053 GP-FR-153, §20.13 SR-011; NFR-011).
- **Confirmation**: covered by `authorised_by: 2026-10-29-delete-cascades/plan-approval` (class is not `security`).
- **Asserted cause verified**: **confirmed** at HEAD `d7bbe3c34`:
  - `site_repository.py:122-132` `delete_site`: l.125 `get_edges(CONTAINS, site_id, outbound)` → l.126-129 `self.delete_location(...)` per child; l.130 `delete_edges(CONTAINS, from_id=site_id)`; l.131 `_delete_irrigation_zones(key)` (l.134-161: tenant-matched zones l.145, `ZONE_EDGES` l.154-158, zone rows l.159-161); l.132 `super().delete(key)`. No reference to `garden_objects`/`has_garden_object`/`care_events`/`care_event_at`/`garden_plan_audit` (research grep → 0 hits; consistent with the read).
  - `site_service.py:141-143`: `self.get_site(key, tenant_key=tenant_key)` then `return self._repo.delete_site(key)` — no active-plant check, no audit row, no user key.
  - Not atomic: confirmed — l.141, l.154-158, l.159, l.132 distinct statements + per-location recursion; no `stream_transaction`.
  - Narrowing: derived from `GRAPH_EDGE_DEFINITIONS` (python over `app.data_access.arango.collections` at this HEAD): `sites` touches **11** edges — `contains`, `belongs_to_tenant`, `has_season_state`, `located_at`, `has_forecast`, `has_weather_source_config`, `has_climate_normal`, `located_in_zone`, `has_irrigation_demand`, `has_garden_object`, `has_irrigation_zone`; `locations` 18; `slots` 8; `garden_objects` 3. Research/row list 10 (omit `belongs_to_tenant`); row says "every edge".
  - Per gate Q1, `care_events` and `garden_plan_audit` are kept (history).

## Scope

- **In scope**:
  1. Lift `_edges_touching`/`_remove_edges` into a shared data-access module, behaviour-preserving.
  2. `delete_site` = one stream transaction: cut every derived edge of the site and of every removed vertex (locations, slots, garden objects, zones); remove structure rows `locations` (recursive), `slots`, `garden_objects`, `irrigation_zones`, `season_states`, `weather_forecasts`, `climate_normals`, `weather_source_configs`, `irrigation_demands`, then the site.
  3. History rows stay: `care_events` (GP-FR-101 "Physisch löscht nur die DSGVO-Kaskade", `spec/req/REQ-053_Grafische-Garten-Beetplanung.md:797`), `garden_plan_audit` (§20.13 SR-011, l.1388). Both carry `tenant_key`, reached by tenant erasure and R-25/R-26 (NFR-011 l.135-136). Their edges to removed vertices (`care_event_at`) are cut.
  4. SR-011: one `garden_plan_audit` row (`op="delete"`, `entity="site"`, `key=<site_key>`, `summary=<name>`) in the same transaction.
  5. 409 when a `plant_instances` row with `removed_on == null` references the site (`site_key`, or `location_key`/`slot_key` of removed locations/slots) — V-09 one level up (GP-FR-024 l.385, V-09 l.1541), inside the transaction.
  6. Legacy `delete_location` switches to the derived edge set.
  7. Migration `v0102_purge_site_orphans.py` with `--dry-run` counts per collection and a named step slot for #2528.
  8. REQ-053 spec sentence (DE, see D-3); docs `docs/de|en/changelog/unreleased.md`, `docs/de|en/user-guide/privacy.md:479` (l.401 only if wording must change).
- **Out of scope**:
  - Underlay attachment on site delete — **#2545 item 1**; WP-2 must not call `GardenPlanUnderlayService`.
  - Nulling `*_key` fields of referrers owned by other REQs (sensors, tasks, planting runs/entries/reservations, calendar feeds, tanks, actuators, location assignments, succession plans, feeding/watering logs, inventree references): edges cut, rows/fields stay — class-sweep finding, filed.
  - Stand-alone `delete_slot`/`_delete_slot_internal` (l.370-394), `delete_substrate`, single `delete_garden_object` — sweep findings (gate Q4).
  - GP-FR-153 dialog and any frontend i18n for the new 409 — frontend, separate item.
  - The delete-side guard (issue body "erasure/orphan guard") — gate Q6, filed as #2556.
  - #2528's step content (only the slot here).

## Route

- **Decision**: direct
- **Rationale**: one outcome, one PR strand (group Mode A), no roadmap item; every WP testable; no route added (pin untouched), no new collection, no new `*_by` field.

## Work packages

Specialists from the live catalog: `nolte-engineering:fullstack-developer` (`claude-shared/plugins/nolte-engineering/agents/fullstack-developer.md`) for backend code+tests; `mkdocs-documentation` (`kamerplanter/.claude/agents/mkdocs-documentation.md`) for docs; no catalog agent authors project REQ files → WP-6 generalist.

### WP-1 — Lift the derived edge helpers into a shared module
- **Hypothesis**: `_edges_touching`/`_remove_edges` move from `garden_plan_repository.py:79-99,793-799` to `app/data_access/arango/graph_edges.py` (`edges_touching`, `remove_edges`) without changing any edge the plan batch cuts. Refuted if a plan-batch delete test changes outcome or `_BATCH_WRITE` (l.102-120) changes membership.
- **Acceptance**: new `tests/unit/data_access/arango/test_graph_edges.py`: `edges_touching(SITES)` ⊇ {(contains,_from),(has_garden_object,_from),(belongs_to_tenant,_from),(located_at,_to)} and ∌ (care_event_at,_to); `edges_touching(LOCATIONS)` ⊇ {(contains,_from),(contains,_to),(care_event_at,_to)}. `tests/integration/test_garden_plan_repository.py`, `tests/integration/test_garden_resource_repository.py` (incl. l.599-608), `tests/unit/data_access/arango/test_garden_plan_collections.py` green unchanged; `ruff check .` 0; mypy ratchet not worse.
- **Files**: `app/data_access/arango/graph_edges.py` (new), `garden_plan_repository.py:79-99,793-799` (+ l.732-735, l.807-808), new test.
- **Specialist**: `nolte-engineering:fullstack-developer` — **Depends on**: none

### WP-2 — `delete_site` as one stream transaction + SR-011 audit row
- **Hypothesis**: after `DELETE /sites/{key}` no row of the nine structure collections of that site and no edge of `edges_touching(V)` on any removed vertex survives; `care_events` and earlier `garden_plan_audit` rows survive; exactly one new audit row exists; the delete is atomic. Refuted by any surviving structure row/edge, removed history row, missing audit row, or partial delete after an in-transaction failure.
- **Design**: `ArangoSiteRepository.delete_site(key, *, user_key)` opens `stream_transaction(self._db, write=<set>, read=(PLANT_INSTANCES,), entity="site")` (`transactions.py:322`); write set = SITES, LOCATIONS, SLOTS, GARDEN_OBJECTS, IRRIGATION_ZONES, SEASON_STATES, WEATHER_FORECASTS, CLIMATE_NORMALS, WEATHER_SOURCE_CONFIGS, IRRIGATION_DEMANDS, GARDEN_PLAN_AUDIT + edges of `edges_touching` for SITES/LOCATIONS/SLOTS/GARDEN_OBJECTS + `ZONE_EDGES` (dedup like `_BATCH_WRITE`). Collect location ids by `contains` traversal 1..N OUTBOUND ∪ `locations.site_key == key` (whether nested locations carry `site_key` is unestablished — `Location.site_key: str = ""`, `app/domain/models/site.py:396`); slots by `location_key IN`; objects by `site_key` (no `tenant_key`, E-01); zones by the existing predicate (l.140-146); site-keyed dependents by `site_key == key`, never removing a row whose non-empty `tenant_key` differs from the site's (mirror l.145). Then WP-3 refusal hook; `remove_edges` for every derived edge; remove slots, locations, objects, zones, dependents; insert `PlanAuditRecord` (`app/domain/models/garden_plan.py:469-490`, `revision = stored plan_revision + 1`); remove the site. Location removal is one helper `_remove_locations(txn, ids)` (reused by WP-4). `weather_source_config_repository.delete_by_site` (l.59-65) not called (D-2). Signature through `app/domain/interfaces/site_repository.py:43`, `site_service.py:141-143` (`user_key`), `app/api/v1/sites/tenant_router.py:157` (`user_key=ctx.user_key`).
- **Acceptance**: `tests/integration/test_irrigation_zone_repository.py:497-511` green after signature adaptation; new class `TestDeletingASiteRemovesItsStructureAndKeepsItsHistory` (same file or `tests/integration/test_site_delete_cascade.py`): no row of the six site-keyed collections for site_a; no `has_garden_object`/`has_season_state`/`has_forecast`/`has_weather_source_config`/`has_climate_normal`/`has_irrigation_demand`/`belongs_to_tenant`/`located_at`/`care_event_at`/`contains` edge on a removed vertex; site_a `care_events` row and earlier audit row still present; exactly one new audit row {op: delete, entity: site, key: site_a, tenant_key: A}; tenant B rows untouched. Atomicity test (forced failure mid-transaction leaves everything). `tests/unit/domain/services/test_site_service_writes_resolve_the_tenant.py:69` updated and green; `tests/api/test_require_permission_enforcement.py:56,98,125,151` green; `ruff check .` 0.
- **Files**: `site_repository.py:122-161` (+ imports l.1-12), `domain/interfaces/site_repository.py:43`, `site_service.py:141-143`, `api/v1/sites/tenant_router.py:150-157`, the tests above.
- **Specialist**: `nolte-engineering:fullstack-developer` — **Depends on**: WP-1

### WP-3 — 409 on site delete while a plant stands on it
- **Hypothesis**: `DELETE /sites/{key}` returns 409 `site.has_active_plants` with `details[0].active_plant_count = n` and writes nothing whenever ≥1 plant with `removed_on == null` has `site_key == key` or `location_key`/`slot_key` among the removed set; removed-only plants do not block. Refuted by 204 with an active plant, partial delete after 409, or 409 for removed-only plants.
- **Design**: refusal inside WP-2's transaction before the first write (race reason as l.768-769), `PlanError("site.has_active_plants", ..., status_code=409, active_plant_count=n)` (`app/common/exceptions.py:155`); router gets `responses={**CONFLICT_RESPONSE}` like `locations/tenant_router.py:255`. Code name: **decided** — new `site.has_active_plants`; the UI keeps the generic conflict toast until the GP-FR-153 follow-up (no frontend cell in this member's row).
- **Acceptance**: integration — plant by `site_key` only, and a second by `location_key` only (pre-v0100 shape) → 409, counts right, site/location/object/zone still present; `removed_on` set → delete succeeds. Unit `tests/unit/domain/services/test_site_service_refuses_active_plants.py` (new): service propagates the `PlanError`, no further write. API test: DELETE /sites maps to HTTP 409 with `code == "site.has_active_plants"`.
- **Files**: `site_repository.py` (transaction body), `api/v1/sites/tenant_router.py:150-157`, tests above.
- **Specialist**: `nolte-engineering:fullstack-developer` — **Depends on**: WP-2

### WP-4 — Legacy `delete_location` cuts the derived edge set
- **Hypothesis**: `ArangoSiteRepository.delete_location(key)` leaves no edge of `edges_touching(LOCATIONS)` (18, incl. `care_event_at`, `has_task`, `run_at_location`, `assigned_to_location`, `located_at`) on the location or descendants, none of `edges_touching(SLOTS)` (incl. `placed_in`, `filled_with`, `adjacent_to`) on their slots, in one transaction; `care_events` rows survive.
- **Design**: replace hand list l.199-221 with `_remove_locations` in its own transaction; no V-09 (route path already refuses via plan batch; `SiteService.delete_location` routeless).
- **Acceptance**: `tests/integration/test_irrigation_zone_repository.py:513-519` green; new sibling test seeding `care_event_at`, `has_task`, `run_at_location`, `placed_in` + child location: all gone, care event stays, sibling bed's edges stay.
- **Files**: `site_repository.py:199-221`, that test file.
- **Specialist**: `nolte-engineering:fullstack-developer` — **Depends on**: WP-2

### WP-5 — Migration `v0102_purge_site_orphans` (dry-run, #2528 slot)
- **Hypothesis**: on a DB with pre-fix orphans, v0102 removes every row of `garden_objects`, `season_states`, `weather_forecasts`, `climate_normals`, `weather_source_configs`, `irrigation_demands` whose non-empty `site_key` resolves to no site, and every edge of the derived site/location/slot/garden-object sets whose endpoint in one of those four vertex collections is gone; never touches live rows or `care_events`/`garden_plan_audit`; `--dry-run` writes nothing and reports the same counts.
- **Design**: shape of `app/migrations/versions/v0100_backfill_plant_location_site.py` (`version = "0102"`, `reversible = False`, `up(db, *, dry_run=False) -> MigrationReport`, batched, capped key lists; docstring What / Never guesses / Idempotent M-3 / Dry run M-5 / Not reversible M-6). Collection and edge lists are literals frozen in the migration; a unit test pins them to `edges_touching(...)` at time of writing (docstring: update the test, not the migration, when the graph grows). Steps = ordered tuple of named steps reporting `details[<step>] = {matched, removed|nulled, keys}`; tuple ends with a documented slot comment `# --- #2528 (group 2026-10-29-delete-cascades): null dangling locations.template_key — step added by member #2528 ---` (no stub, no dead code).
- **Acceptance**: `tests/unit/migrations/versions/test_v0102_purge_site_orphans.py` (report shape, dry-run writes nothing, frozen lists = derivation); `tests/unit/migrations/versions/test_versions_smoke.py` green (auto-discovery `load_migrations`, l.14: no-op on empty DB, honours dry_run, irreversible down raises); `tests/integration/test_v0102_purge_site_orphans.py` (pattern `tests/integration/test_v0100_backfill_plant_location_site.py`): one orphan per collection + dangling `has_garden_object`/`care_event_at` + live site with same shapes + history rows of the gone site; dry-run counts == apply counts; live and history rows survive; second run 0. `python -m app.migrations upgrade --to 0102 --dry-run` output recorded (prod snapshot first).
- **Files**: `app/migrations/versions/v0102_purge_site_orphans.py` (new), two new tests.
- **Specialist**: `nolte-engineering:fullstack-developer` — **Depends on**: WP-1; must land before #2528 adds its step.

### WP-6 — REQ-053 spec: site-delete cascade
- **Hypothesis**: REQ-053 defines no site-delete semantics today (`grep -n "DELETE /sites\|Standort lösch\|Site lösch" spec/req/REQ-053_Grafische-Garten-Beetplanung.md` → 0 hits). Refuted if afterwards a reader can answer from REQ-053 alone what goes, what stays and why, and when it is refused.
- **Content (DE)**: §20.13 (l.1382-1390) new row "Standort löschen (#2513)" (structure rows go, every graph edge on a removed vertex is cut, history stays per GP-FR-101/SR-011, audit row `op=delete, entity=site` in the same transaction, field references of other REQs stay → sweep issue); §22.2 V-table (V-09 l.1541) extended with `site.has_active_plants` for `DELETE /sites/{key}`; new **GP-ACC-061** (I) (last existing id GP-ACC-060) "Given ein Standort mit 1 aktiven Pflanze, When `DELETE /sites/{key}`, Then 409 `site.has_active_plants` mit `details.active_plant_count = 1` und nichts ist gelöscht"; version row "1.6 (Nachtrag #2513)" 2026-10-29 (table l.20-27). Optional: traceability row in `spec/e2e-testcases/TC-REQ-053.md` (~l.1400) if the GP-ACC table must stay complete.
- **Acceptance**: `grep -n "site.has_active_plants\|GP-ACC-061\|Standort löschen" spec/req/REQ-053_Grafische-Garten-Beetplanung.md` → ≥3 hits; spec-reference check task (exact name in `.taskfiles/checks.yaml` unestablished); strict docs build if REQ files render (unestablished).
- **Specialist**: no matching specialised agent — generalist remediation — **Depends on**: WP-3

### WP-7 — User docs and changelog (DE + EN)
- **Hypothesis**: a user cannot learn from the docs that plants block a site delete and that the care history stays; the changelog does not mention the fix.
- **Content**: `docs/de/user-guide/privacy.md:478-479` and `docs/en/user-guide/privacy.md:478-479` FAQ: one sentence on what goes (beds, slots, garden objects, zones, season/weather data), what stays (care and change logs until retention or tenant erasure), and that sites with growing plants cannot be deleted; l.401 only if needed (expected unchanged). Changelog under `## Geändert` (`docs/de/changelog/unreleased.md:62`) / `## Changed` (`docs/en/changelog/unreleased.md:62`) — no Behoben/Fixed section exists; follow DOCS.md if it prescribes one. No REQ ids in end-user prose, informal "du".
- **Acceptance**: `.venv-docs/bin/mkdocs build --strict` green; DE/EN paragraphs at the same position.
- **Specialist**: `mkdocs-documentation` — **Depends on**: WP-3 (parallel to WP-6)

## Dependency ordering

WP-1 → WP-2 → WP-3 → {WP-6 ∥ WP-7}; WP-2 → WP-4; WP-1 → WP-5 (before #2528's step). Sequential dispatch on the shared tree: WP-1 → WP-2 → WP-3 → WP-4 → WP-5 → WP-6 ∥ WP-7.

## Deviations from the matrix row (how, not what)

| Id | Row text | Plan | Reason |
|---|---|---|---|
| D-1 | 10 site edges in parentheses | 11 (`belongs_to_tenant`) | the row's clause is "every edge of `_edges_touching(SITES)`"; derivation has 11 |
| D-2 | weather_source_configs "via existing `delete_by_site` l.59" | inline AQL with the same predicate | `delete_by_site` runs on `self._db` outside the transaction; would break "one stream transaction" |
| D-3 | spec "DE canonical + EN mirror" | REQ-053 DE only | `spec/req/` has no EN mirrors (`ls spec/req \| grep -i 053` → one file); pairing applies to `docs/` (WP-7) |
| D-4 | "`site_service.delete_site` refuses 409" | refusal inside the repo transaction, propagated by the service | race safety (V-09, l.768-769) |
| D-5 | no router change named | `sites/tenant_router.py:150-157` passes `user_key`, documents 409 | needed by the SR-011 audit row (row) and the 409 (gate Q2); no route added |

## Class sweep (group-level input)

Predicate: `for V in vertex collections with a delete_*: edges_touching(V) − edges cut`. Population: `grep -rn "def delete_" app/data_access/arango/ | wc -l` → **67**. Graph-vertex deletes to run against: `site_repository.delete_site|delete_location|delete_slot`, `garden_object_repository.delete_garden_object`, `irrigation_zone_repository.delete_zone`, `bed_template_repository.delete_template`, `substrate_repository.delete_substrate|delete_batch`, `actuator_repository.delete_actuator|delete_profile|delete_rule|delete_schedule`, `aquaponik_repository.delete_system|delete_stock`, `botanical_family_repository.delete_family`, `ipm_repository.delete_pest|delete_disease|delete_treatment`, `lifecycle_repository.delete_phase|delete_phase_history`, `phase_sequence_repository.delete_definition|delete_entry|delete_sequence`, `nutrient_plan_repository.delete_phase_entry`, `overwintering_profile_repository.delete_profile`, `planting_run_repository.delete_entry`, `post_harvest_repository.delete_batch`, `species_repository.delete_cultivar`, `tank_repository.delete_schedule`, `task_repository.delete_task|delete_phase|delete_task_template|delete_workflow_template|delete_comment`, `inventree_repository.delete_connection|delete_equipment|delete_reference`, `fertilizer_repository.delete_stock`, `weather_source_config_repository.delete_by_site`, `plan_repository.delete_unused`. The rest (`delete_expired*`, `delete_*_before`, `delete_by_user`, `delete_all_for_user`, `delete_settings`, `delete_edges`, `delete_many`, …) are retention/maintenance deletes. **Lower bound:** generic `BaseArangoRepository.delete` (`base_repository.py:1209`) is not in the grep — `grep -rn "super().delete(\|return self.delete(" app/data_access/arango/ | wc -l` → 34; 21 service files call `*repo*.delete(` directly. After this member, `delete_site`/`delete_location` must have an empty difference; `delete_slot` (l.370-394) is expected non-empty (filed).

## Risks

- **Blast radius**: REQ-046/047/037 rows go with a site. Mitigation: gate Q1, WP-6, WP-7, WP-3.
- **Time budget**: many `weather_forecasts` rows per site (index `collections.py:2726`), `DEFAULT_TIME_BUDGET_SECONDS = 10.0` (`transactions.py:81`); prod volume unestablished. Mitigation: WP-5 dry-run counts; raise `time_budget_seconds` with a recorded reason rather than splitting.
- **Cross-tenant delete**: `tenant_key` defaults to `""` on `season_state.py:27`, `weather.py:42,80,164`, `irrigation_demand.py:28`. Mitigation: l.145-style predicate + tenant-B control; run `nolte-engineering:code-security-reviewer` (+ `gdpr-data-protection-reviewer`) before the PR.
- **Unmapped 409 in UI**: `SiteDetailPage.tsx:182-195` → generic `handleError` (`hooks/useApiError.ts`) shows a status-based text. Decided: acceptable until the GP-FR-153 follow-up.
- **Irreversible purge**: dry-run on the prod snapshot first, counts recorded before apply.
- **Local env**: primary venv lacks `prometheus_client` (`pyproject.toml:53`): `pytest --collect-only tests/integration/test_irrigation_zone_repository.py` → `ModuleNotFoundError`. The worktree venv was synced with `uvx uv@0.13.3 sync --frozen --extra dev`; use it or `task test:backend:*` (`uv run --locked`).
- **care_event readers via edge**: assumed field-based (`site_key`/`location_key`); edge-only readers of `CARE_EVENT_AT` unestablished — grep in WP-4.

## Open questions

1. ~~409 code~~ — **decided by the orchestrating session inside the matrix row**: new code `site.has_active_plants`; UI shows the generic conflict toast until the GP-FR-153 follow-up; no i18n strings in this member (that would be a new frontend cell and a re-approval).

## Verification

From `src/backend/` of the worktree; record actual output in the group's Member results.
- `task test:backend:unit` (`.taskfiles/backend.yaml:142`)
- `task test:backend:api` (l.154)
- `task test:backend:integration` (l.160, ArangoDB) — incl. `test_irrigation_zone_repository.py`, new cascade tests, `test_v0102_purge_site_orphans.py`, `test_garden_plan_repository.py`, `test_garden_resource_repository.py`
- `task lint:backend` (= `uv run --locked --extra dev ruff check .`) → 0; `ruff format --check .`
- `task typecheck:backend` not worse
- `pytest tests/unit/test_route_consumers_check.py -q` unchanged (16 passed)
- `uv run --locked --extra dev python -m app.migrations upgrade --to 0102 --dry-run` (flags `app/migrations/framework/cli.py:111-112`) — dev DB, then prod snapshot
- Docs: `task docs` is a namespace (`Taskfile.yaml:41-43`); build `task docs:build` (`.taskfiles/docs.yaml:100-104`); `mkdocs.yml` has no top-level `strict` (l.222 `strict: false` is a plugin option) → `.venv-docs/bin/mkdocs build --strict` from repo root.
- Sweep probe: for V ∈ {sites, locations} difference empty (WP-2/WP-4 integration tests seed one edge per derived collection).

## Dispatch log

<!-- Appended during operation 5. -->
### WP-4 — dispatched 2026-10-29T17:00Z → `nolte-engineering:fullstack-developer` — result: hypothesis holds
- `site_repository.py`: `delete_location(key) -> bool` = `stream_transaction(write=_LOCATION_REMOVAL_WRITE, entity="location")`: existence check → `_contains_closure(txn, location_id, [location_id])` (descent logic lifted out of WP-2, now shared with `_location_ids_of_site`) → `_remove_locations(txn, ids)`; no V-09 (routed path refuses via plan batch); missing location → `False`, no write; stale comment in `_delete_slot_internal` corrected. New `tests/integration/test_location_delete_cascade.py` (6 tests): 9 edges on the bed (`contains` ×2, `has_slot`, `placed_in`, `care_event_at`, `has_task`, `run_at_location` ×2, `zone_covers`) gone; care_event and zone rows stay; sibling bed byte-identical; atomicity; missing → False. Falsification with HEAD's version (`cp`): 2 red (edge set, atomicity).

### WP-5 — same dispatch — result: hypothesis holds (local adaptations recorded)
- New `app/migrations/versions/v0102_purge_site_orphans.py` (`PurgeSiteOrphansMigration`, `version="0102"`, `reversible=False`, `up(db, *, dry_run=False) -> MigrationReport`); frozen `_SITE_KEYED_ROWS` (6 collections) and `_EDGE_ENDS` = `(vertex, edges_touching(vertex))` for sites, locations, slots, garden_objects, 5 dependents + `("irrigation_zones", ZONE_EDGES)`; `_STEPS`: `<row>_of_missing_sites` ×6, `locations_of_missing_sites`, `slots_of_removed_locations`, `dangling_edges`; `details[step] = {matched, removed, keys(≤25)}`; plan computed before the first write so dry-run `matched` == apply. Tests: `tests/unit/migrations/versions/test_v0102_purge_site_orphans.py` (12, incl. frozen lists == derivation), `tests/integration/test_v0102_purge_site_orphans.py` (4).
- Local adaptations: (1) the exact #2528 marker line is 121 chars at indent → placed at column 0 directly under `_STEPS`' closing `)` (no `noqa`), explained in the comment above `_STEPS`; (2) an edge counts as dangling only when its endpoint in the *listed* vertex collection is missing (`IS_SAME_COLLECTION`) → `belongs_to_tenant` edges of care_events untouched; (3) child locations are removed only when every existing parent is removed too (a location anchored via `contains` to a surviving vertex stays — `anchored` test); (4) missing `sites` collection → no-op, missing collections skipped; (5) `irrigation_zones` rows are not candidates (zones exist only since WP 7.1, whose `delete_site` already removed them), their dangling edges are.
- Checks (actual output): `ruff check .` → `All checks passed!`; `ruff format --check .` → `2832 files already formatted`; mypy v0102 0 errors, `site_repository.py` 17 before/17 after; `tests/unit/test_route_consumers_check.py -q` → `16 passed`; `tests/unit/migrations -q` → `1425 passed, 1 skipped in 142.76s`; integration set (`test_site_delete_cascade`, `test_irrigation_zone_repository`, `test_v0102_purge_site_orphans`, `test_location_delete_cascade`, `test_garden_resource_repository`) + v0102 unit + smoke + `test_site_service_writes_resolve_the_tenant` + `test_graph_edges` → `128 passed in 37.38s`.
- **CLI dry-run not run:** `uv run --locked` → uv 0.11.33 ≠ 0.13.3 (shim only on the orchestrator's PATH); `.venv/bin/python -m app.migrations upgrade --to 0102 --dry-run` → `DocumentGetError … collection or view not found: schema_migrations` (local dev DB `kamerplanter` is stale: 1 site, 0 locations, 27 collections missing). Substitute: `migration.up(db, dry_run=True)` directly → `0102 purge_site_orphans: scanned=0 changed=0 dry_run=True`, every step `matched=0`, counts unchanged. **Open: dry-run against a prod snapshot before P-point** (recorded in Risks).

### WP-6 — 2026-10-29T17:05Z → no matching specialised agent — generalist remediation (orchestrating session) — result: done
- `spec/req/REQ-053_Grafische-Garten-Beetplanung.md` +4 lines: version row `1.6 (Nachtrag #2513)` (l.22), §20.13 row „Standort löschen (#2513)" (l.1391), rule **V-24** `site.has_active_plants` after V-23 (l.1558), **GP-ACC-061** (I) after GP-ACC-060 (l.1851). DE only (D-3). TC-REQ-053.md carries no GP-ACC-059/060 rows → no traceability row added.
- Check: `grep -n "site.has_active_plants\|GP-ACC-061\|Standort löschen" spec/req/REQ-053_…md` → 4 hits (≥ 3 required).

### WP-7 — dispatched 2026-10-29T17:00Z → `mkdocs-documentation` — result: done; strict build blocked by pre-existing warnings
- Files: `docs/de/user-guide/privacy.md`, `docs/en/user-guide/privacy.md` (FAQ sentence: site delete removes beds/slots/garden objects, care and change log stay until retention or tenant erasure, a site with growing plants cannot be deleted; l.401 unchanged), `docs/de/changelog/unreleased.md`, `docs/en/changelog/unreleased.md` (`## Geändert`/`## Changed` → `### Backend`: „Standort löschen räumt vollständig auf (Issue #2513)" / „Deleting a site now cleans up completely (issue #2513)"). No user-guide page describes site deletion (`ls docs/de/user-guide | grep -i -E "garden|site|standort|bed|beet|plan"` → plant-*/planting-runs only).
- Check: `.venv-docs/bin/mkdocs build --strict -f <worktree>/mkdocs.yml` → `Aborted with 3 warnings in strict mode!` — all three are anchor links in `en/deployment/konfigurationsmatrix.md` and `en/guides/compliance-anbauvereinigung.md`, none in the touched files. Same build on the primary checkout at `develop` → the same anchors warn (`Aborted with 130 warnings`), so the failure is **pre-existing**, not introduced by WP-7. `git diff --stat -- docs` → exactly the 4 intended files (4 insertions, 2 deletions).

### WP-3 — dispatched 2026-10-29T16:53Z → `nolte-engineering:fullstack-developer` — result: hypothesis holds
- Files: `site_repository.py` (`_refuse_active_plants(txn, key, scope)` called right after `_collect_site_delete_scope`, before the first write), `api/v1/sites/tenant_router.py` (`responses={**CONFLICT_RESPONSE}`, 409 in docstring), `tests/integration/test_site_delete_cascade.py` (new class `TestASiteWithActivePlantsIsNotDeleted`, 6 tests; `PLANT_INSTANCES` added to the per-test cleared set), new `tests/unit/domain/services/test_site_service_refuses_active_plants.py`, new `tests/api/test_site_delete_refuses_active_plants_api.py`.
- AQL: `RETURN LENGTH(FOR p IN @@plants FILTER p.removed_on == null FILTER p.site_key == @site_key OR p.location_key IN @location_keys OR p.slot_key IN @slot_keys RETURN 1)` — counts per plant, so a plant matching all three ways counts once. No tenant filter by design (refuses only, never deletes; tenant-B plants on site B do not block site A — test (e)).
- Payload: `PlanError("site.has_active_plants", ..., status_code=409, active_plant_count=n)` → `app_error_handler` emits `{error_code, message, details:[{field:"request", reason, code, active_plant_count}]}`. Deviation from the plan's wording: there is no top-level `code`; the code sits in `error_code` and `details[0].code` (API test asserts both).
- Checks (actual output): `test_site_delete_cascade.py + test_irrigation_zone_repository.py` → `41 passed in 12.14s`; unit + API tests → `4 passed`; `test_route_consumers_check.py -q` → `16 passed`; `test_require_permission_enforcement.py -k site` → `3 passed, 10 deselected`; final run (integration + new tests + `test_site_service_writes_resolve_the_tenant` + `guards/test_keyed_service_writes_take_the_tenant`) → `91 passed in 33.54s`; `ruff check .` → `All checks passed!`; `ruff format --check .` → `2828 files already formatted`; mypy on the two app files 30 before / 30 after (older code). Falsification (`cp`, not stash): without the call 5 tests red; each branch disabled with `AND false` → exactly its test + the tenant-B positive control red; without the `removed_on` filter the removed-plant test red; file restored (`cmp` identical).
- For WP-6: code `site.has_active_plants`, HTTP 409, counter in `details[0].active_plant_count`, code also in `error_code`; blocks when a plant with empty `removed_on` has `site_key` = the site or `location_key`/`slot_key` of a bed/slot that would be removed; nothing is deleted then.

### WP-2 — dispatched 2026-10-29T16:28Z → `nolte-engineering:fullstack-developer` — result: hypothesis holds (local adaptations recorded)
- Files: `site_repository.py` (`delete_site(key, *, user_key) -> bool` as one `stream_transaction`; `_collect_site_delete_scope(txn, key)`; `_remove_locations(txn, location_ids)`; `_SITE_DELETE_WRITE` = 46 collections deduped; read set `(plant_instances,)`; default time budget), `domain/interfaces/site_repository.py:43`, `site_service.py:141` (`delete_site(key, *, tenant_key, user_key)`), `api/v1/sites/tenant_router.py:157` (`user_key=ctx.user_key`), `tests/integration/test_irrigation_zone_repository.py:505`, `tests/unit/domain/services/test_site_service_writes_resolve_the_tenant.py:69`; new `tests/integration/test_site_delete_cascade.py` (6 tests, `TestDeletingASiteRemovesItsStructureAndKeepsItsHistory`).
- Local adaptations (how, inside the row): edges of the 5 site-keyed dependents are cut too (`demand_for_run` would otherwise dangle); locations collected level by level over `contains` to a fixpoint ∪ `site_key == key`; slots via field ∪ `has_slot`, objects via field ∪ `has_garden_object`; dependent rows removed only when `tenant_key` is null/empty or equals the site's tenant (`foreign_claim` test). `delete_by_site` and `GardenPlanUnderlayService` not called (D-2, scope).
- Checks (actual output, ArangoDB localhost:8529): `pytest tests/integration/test_site_delete_cascade.py test_irrigation_zone_repository.py test_garden_plan_repository.py test_garden_resource_repository.py test_garden_plan_tenant_isolation.py` → `1 failed, 358 passed` — the failure is `TestGetPlanBenchmark::test_get_plan_on_the_large_class_meets_the_spec_p95_of_300_ms [XPASS(strict)]`, pre-existing (fails identically with HEAD's `site_repository.py`; GET /plan path untouched; tracked by #2526). Falsification: removing the tenant rule / the `contains` descent / the `ZONE_EDGES` cut / the dependent-edge cut each turns 2 tests red; a raise at the end of the transaction body turns 4 red (atomicity). `test_site_service_writes_resolve_the_tenant.py + test_route_consumers_check.py + test_keyed_service_writes_take_the_tenant.py + test_graph_edges.py` → `72 passed`; `tests/api/test_require_permission_enforcement.py -k site` → `3 passed`; `tests/unit -k site` → `619 passed`; `ruff check .` → `All checks passed!`; `ruff format --check .` → `2826 files already formatted`; mypy on the 4 app files: 31 before, 31 after (older code).
- For WP-3: refusal goes right after `scope = self._collect_site_delete_scope(txn, key)` ("Everything above only reads"); `scope` carries `tenant_key`, `location_ids`, `slot_ids`, `object_ids`, `zone_ids`, `dependent_ids`; `plant_instances` already in the read set. For WP-5: rows = `_SITE_DEPENDENTS` + garden_objects, slots, locations, irrigation_zones; edges = `edges_touching(V)` for V ∈ {sites, locations, slots, garden_objects, 5 dependents} + `ZONE_EDGES`; `care_events`/`garden_plan_audit` and their `belongs_to_tenant` edges stay.

### WP-1 — dispatched 2026-10-29T16:25Z → `nolte-engineering:fullstack-developer` — result: hypothesis holds
- Files: new `app/data_access/arango/graph_edges.py` (`EdgeEndpoint`, `edges_touching(vertex_collection) -> tuple[tuple[str, EdgeEndpoint], ...]`, `remove_edges(txn, edge_collection, field, ids: Sequence[str])` raising `ValueError` on a field other than `_from`/`_to`); `garden_plan_repository.py` uses them directly (6 call sites), private helpers removed, unused `aql_field` import gone; new `tests/unit/data_access/arango/test_graph_edges.py` (10 tests).
- Behaviour preserved: `_BATCH_WRITE`, `_BATCH_READ`, `_SLOT_BATCH_WRITE`, `_SLOT_BATCH_READ`, `_LOCATION_EDGES`, `_SLOT_EDGES`, `_OBJECT_EDGES` compared old vs new module → all equal.
- Checks (actual output): `pytest tests/unit/data_access/arango/test_graph_edges.py tests/unit/data_access/arango/test_garden_plan_collections.py -q` → `16 passed in 2.50s`; `--collect-only` on `test_garden_plan_repository.py` + `test_garden_resource_repository.py` → `64 tests collected` (ArangoDB not reachable locally, not run); `ruff check .` → `All checks passed!`; `ruff format --check .` → `2825 files already formatted`; `pytest tests/unit/test_route_consumers_check.py -q` → `16 passed`; `pytest tests/unit -k "garden_plan or graph_edges or aql_attribute or slot_delete"` → `403 passed`; mypy: 0 errors in the two files, 56 pre-existing elsewhere unchanged.
- Observations for the sweep (not changed, out of WP scope): `planting_reservation_repository.py:60` carries an identical copy of `_edges_touching`; `irrigation_zone_repository.py:50` has `_edges_touching_zones` + its own `_remove_edges`.
- `edges_touching(SITES)` = 11 pairs incl. `belongs_to_tenant` (D-1 confirmed); nested locations' `site_key` not guaranteed → traversal ∪ field union in WP-2.
