# Group pre-analysis: 2026-10-29-site-conditions-layers

> Run-scoped artifact. Committed on the integration branch, removed with a fix-forward
> `git rm` before the bundle merges. It must never reach the default branch, and it must
> never be hidden behind a `.gitignore` entry.
>
> Origin: `issue-backlog-partition` 2026-10-29 (`.audits/issue-backlog-partition/2026-10-29.md`,
> approved 2026-10-29T15:20:49Z; hand-off payload
> `scratchpad/handoff/2026-10-29-site-conditions-layers.yml`). Research anchored by one
> read-only exploration agent against `develop` = `fdc63f51c` (2026-10-29T23:52Z).

## Scope of this analysis

**Research question:** Which single change to the garden-plan read model and the plan batch
write lets (a) the editor's properties panel edit the sun window and foliage shade without a
second write path (#2538, remainder of #2486) and (b) the sun / moisture / frost map layers
read their data from the plan (#2487) — and what must each member touch so that the plan
response stays under its 1 MB ceiling (E-13) and the undo model stays invertible?

**The group's single logical change, in one sentence:** Carry site conditions (sun window,
foliage shade, frost risk, drainage) through the plan read model and the plan batch write,
render them as the sun, moisture and frost map layers, and make them editable in the
properties panel.

**Out of scope:**
- Editing `microclimate.frost_risk` from the editor or the batch. The frost sync rule
  (`garden_resource_service.py:348-363` `_mirror_frost_risk`) is being reworked by the single
  #2512 (decision (a) of #2503); the batch accepts `site_conditions.sun_profile` only, so the
  frost mirror is never reached from the plan path. The frost **layer** only reads
  `microclimate.frost_risk` (#2454 item 2: winter readers stay on `frost_exposed`).
- Export/import file schema (`domain/models/garden_plan_export.py`, import service): #2512
  edits both files for `frost_exposed`. This group adds nothing there unless the round-trip
  test shows `sun_profile` does not survive today; if it does not, that is a local adaptation
  recorded below, kept to an additive key.
- Plant-state layer and legend (#2488/#2489, group `plant-state-layer-legend`, serial after
  this one on `editor/layers.ts` and `renderer/SvgPlanRenderer.tsx`).
- LOD/label refinements (#2490), E2E part B (#2492), the user guide WP 6.3 (#2447) beyond
  the two sentences this group removes/adds.
- Any computation from the sun profile (§29 stays out, GP-FR-159).
- No new route: the batch field rides on `update_fields` (REQ-053 v1.6 addendum WP 3.9 (d),
  spec l.22); route-count pin 890 untouched.

**Tier:** 2 — one repository, additive API fields on an existing response and an existing
operation body, no published contract broken (OpenAPI is generated, not checked in).

## Members

| Issue | Class | Admitting predicate | Evidence |
|---|---|---|---|
| #2538 | feature-request | shared touch surface (anchor) | body: "overlaps #2487 … coordinate or do it in that package"; measured: `garden_plan_service.py:122-125` `_LOCATION_COLUMNS = {geometry,bbox,area_m2,name,path,depth,description,notes,sun_exposure,height_m} ∪ {locked,z_order}` — no `site_conditions`; `models/garden_plan.py:113-120` `LocationFieldsPatch` (name, description, notes, sun_exposure, height_m; `extra="forbid"`); `api/v1/garden_plan/schemas.py:179-220` `PlanLocationResponse` carries `sun_exposure` only; frontend `model/types.ts:201-228` `PlanLocation` likewise |
| #2487 | feature-request | shared touch surface | plan WP 7.21 adds `sun_window`, `microclimate.frost_risk`, `soil_profile.drainage` to the same `PlanLocationResponse` (:179) that #2538 extends; `editor/layers.ts:2-6` comment: "later sun / moisture / frost … are added HERE" — registry holds `grid, zones, lastWatered, underlay` only |
| #2486 | feature-request | dependency chain | comment 2026-10-20 (nolte): "NOT delivered: the properties panel … tracked in #2538. This issue stays open until #2538 is done"; PR #2537 (`7bf4ece9`) delivered `bed/SunDialog.tsx`, `bed/SunWindowFields.tsx`, `field/FieldSunSection.tsx`; `editor/PropertiesPanel.tsx:239-251` sun section still offers `SunTileSelector` only |

**Dependency ordering:** #2538 → #2487 → #2486. #2538 carries the whole read-model extension
(all four fields, one edit of `PlanLocationResponse` and `PlanLocation`), the batch field and the
panel; #2487 builds the three layers on the fields #2538 projected and adds drainage to the bed
header; #2486 has no code of its own — it closes with #2538's panel.

**Shared touch surface:** `src/backend/app/api/v1/garden_plan/schemas.py` (`PlanLocationResponse`
:179-220 + example :181-196), `src/frontend/src/features/gardenPlanner/model/types.ts`
(`PlanLocation` :201-228), `src/frontend/src/features/gardenPlanner/editor/PropertiesPanel.tsx`
(#2538 ↔ #2486), i18n `src/frontend/src/i18n/locales/{de,en}/pages.json`. With the rest of the
backlog: `editor/layers.ts`, `renderer/SvgPlanRenderer.tsx` (#2488, #2490 — serial after this
group), `garden_plan_service.py` (#2542/#2547 group `plan-input-hardening`, serial after).

**Gates recorded by the partition, re-checked:** PR #2548 merged `eadfd49ce` (touched
`schemas.py` +72 / `tenant_router.py` +37, `PlanLocationResponse` untouched); PR #2546 merged
`0d8cad496` (tests only). Prerequisites 7.6 (#2472 via #2533) and #2464 are on `develop`.

## Mode decision

**Mode:** A — single strand.

**Reason:** removability criterion not met. All three members are `feature-request` with a
verified cause (records `asserted_cause.status: verified`), none is `security`, no dependency
outside the group's control, no outstanding review. The members edit the same files
(`PlanLocationResponse`, `PlanLocation`, `PropertiesPanel.tsx`, `pages.json`); separate
sub-branches would only manufacture conflicts between them.

## Structural finding

**Cluster shape:** symptom cluster.

**Root cause:** the garden-plan read model is a *lean projection* by design
(`garden_plan_service.py:119-121`: "Everything else … belongs to other paths (status, soil, …)
that run outside the plan revision (GP-NFR-007)"), and the site conditions added in WP 3.9
(`site.py:238-288` `SunProfile`, `Microclimate`, `SiteConditions`; `Location.site_conditions`
:431) were never admitted to that projection or to the batch write. Everything the three issues
ask for — panel chips (#2486/#2538) and three layers (#2487) — is a reader or writer of that
missing field.

**Process finding:** none in the development process; WP 3.9 (a) consciously added the model and
the PATCH merge first and deferred the plan path to wave 7 (spec v1.6 addendum, l.22). No guard
is missing.

**Preventive change:** not applicable — planned deferral, not a defect class.

**Recurrence fed to the portfolio loop:** none.

## Plan approval

**Authorised by:** `2026-10-29-site-conditions-layers/plan-approval`, covering the members,
mode, and order above. Revoked for undispatched members by any structural regression until
re-approved.

**Approval basis:** operator instruction 2026-10-29 ~23:00Z and 2026-10-30 ("mach weiter mit
der gruppe und arbeite sie möglichst autonom und vollständig ab") under the standing
authorisation of 2026-10-09 (plan gates of the approved partition are taken by the session;
product choices are collected and reported). Design decisions taken here, reported in the
bundle: D-1 lean nested projection; D-2 batch accepts `sun_profile` only; D-3 unknown-valued
enums are projected as absent (`None`) to protect the 1 MB ceiling; D-4 legend extends the
existing `ZoneLegend` (one legend, one testid).

**Group requirement artifact:** not applicable — symptom cluster, per-member requirement = the
spec rows REQ-053 GP-FR-158 (l.594), GP-FR-159 (l.595), GP-FR-169 (l.605), GP-FR-047 (l.555),
GP-UX-057 (l.606), GP-FR-031 (l.392), v1.6 addendum WP 3.9 (l.22).

## Design decisions (binding for the dispatched runs)

- **D-1 Read model shape.** `PlanLocationResponse` gains `site_conditions: PlanSiteConditionsResponse | None`
  with `sun_profile: {sun_window, direct_sun_hours_summer, foliage_shade_in_summer}` and
  `microclimate: {frost_risk}`, plus `soil_profile: PlanSoilProfileResponse | None` with
  `{drainage}`. Nothing else from `SiteConditions`/`SoilProfile` is projected (lean read model,
  GP-NFR-007). The frontend `PlanLocation` mirrors it. Projection happens in the router's
  `to_response` step (`tenant_router.py:124-133`) — the AQL read (`garden_plan_repository.py:177-196`)
  already returns the whole document.
- **D-2 Batch field.** `LocationFieldsPatch.site_conditions: PlanSiteConditionsPatch | None`
  (strict, `extra="forbid"`) allowing **only** `sun_profile` (`sun_window`, `direct_sun_hours_summer`,
  `foliage_shade_in_summer`); `microclimate` and the rest stay on `PATCH /locations`. The merge
  rule is the PATCH rule (`garden_resource_service.py:332-345` `_merged_site_conditions`) lifted
  into one shared helper used by both paths. `site_conditions` joins `_LOCATION_COLUMNS` so
  `_changed_fields` (:1134) writes it inside the plan revision. `sun_profile.source` is set to
  `manual` like PATCH.
- **D-3 Budget.** Enum values `unknown` and `foliage_shade_in_summer=false` with no window are
  projected as `None` so `response_model_exclude_none=True` (`tenant_router.py:213`) drops them;
  the ceiling test `test_a_large_garden_fits_the_response_budget_and_the_time_budget`
  (`tests/integration/test_garden_plan_repository.py`, ceiling `1_000_000` bytes at :63, large
  class ≈ 0.85 MB today) must stay green and its measured size is recorded below.
- **D-4 Layers.** `editor/layers.ts` gains `sun`, `moisture`, `frost` (`defaultVisible: false`,
  `bar: 'toggle'`), icons in `GardenPlanEditor.tsx:171-175`, overlays in a new
  `renderer/ConditionOverlays.tsx` following `renderer/ZoneOverlays.tsx` (pattern tile + icon,
  never colour alone; WCAG 1.4.1), fed from `scene.shapes` + plan locations; legend sections added
  to `zones/ZoneLegend.tsx` (keeps `data-testid="garden-plan-layer-legend"`). Headless/base
  renderers get the options with no-op defaults. New i18n: `pages.gardenPlan.editor.zones.layers.{sun,sunHint,moisture,moistureHint,frost,frostHint}`,
  legend keys, and `enums.sunWindow`, `enums.frostRisk` (DE+EN; `enums.soilDrainage` exists).
- **D-5 Undo.** `model/applyOperation.ts:234-272` `updateLocationFields` builds the `before`
  patch for `site_conditions.sun_profile` from the read model (invertible); `recreateLocation`
  (:315-329) copies `site_conditions` too.
- **D-6 Panel.** `editor/PropertiesPanel.tsx` sun section (:239-251) adds `SunWindowFields`
  (lazy, `bed/SunWindowFields.tsx`) and the foliage switch; every change commits one
  `update_fields {site_conditions:{sun_profile:{…}}}` through `onCommit(ops,'edit')` → `applyAction`.
  No PATCH from the editor. Bulk (`SunBulk` :474-500) stays `sun_exposure` only.

## Completeness matrix

Columns derived from the repository: backend source (`src/backend/pyproject.toml`), migration
(`src/backend/app/migrations/versions/`), spec (`spec/`), tests (`task test:backend:*`,
`task test:frontend`), docs (`mkdocs.yml`, `docs/de|en`), frontend (`src/frontend/package.json`),
config/workflows (`.github/workflows/`, Taskfiles), generated indexes/pins (route-count pin
`tests/unit/test_route_consumers_check.py:308` = 890, schema-example ratchet
`tests/unit/test_schema_example_ratchet.py`, OpenAPI generated by `task openapi:export`, not
checked in).

| Member | Backend source | Migration | Spec | Tests | Docs | Frontend | Config / workflows | Generated indexes / pins |
|---|---|---|---|---|---|---|---|---|
| #2538 | D-1 `schemas.py:179-220` + example :181-196; D-2 `models/garden_plan.py:113-120` `LocationFieldsPatch.site_conditions`, shared merge helper (lift `_merged_site_conditions` from `garden_resource_service.py:332-345`), `garden_plan_service.py:122-125` `_LOCATION_COLUMNS` + `_update_fields` :857-885 nested merge, `_check_fields_patch` :625-631 reports `fields.site_conditions.*` as `validation.invalid`; D-3 projection; check: `uv run --locked --extra dev python -m pytest tests/api tests/unit/domain/services/test_garden_plan_service.py tests/unit/test_schema_example_ratchet.py -q` output recorded; `ruff check .` 0 | not applicable — no stored shape changes (field exists since v0098), no new collection | not applicable — GP-FR-158/159 and addendum WP 3.9 (d) already specify the panel and the `update_fields` path; the implementation-status table is #2448's | `tests/api/test_garden_plan_api.py`: plan response carries `site_conditions`/`soil_profile` for a seeded bed and omits them when unknown; `update_fields` with `site_conditions.sun_profile` merges (other sun fields untouched), rejects `microclimate` (422 `fields.site_conditions.microclimate`), bumps `plan_revision`; `tests/unit/domain/services/test_garden_plan_service.py:157-180` twin; export→import round trip keeps `sun_profile` (`tests/integration/test_tenant_export_roundtrip.py` or plan export test); ceiling test size recorded; frontend `editor/PropertiesPanel.test.tsx:256ff` chips+switch commit the op, `model/applyOperation.test.ts:217ff` inverse restores `before`, `editor/SaveUndo.test.tsx` undo/redo; axe. Check: commands with output recorded | remove EN `docs/en/user-guide/locations-substrates.md:386` and DE `docs/de/user-guide/locations-substrates.md:394` "not yet" sentences, replace with one sentence that the panel edits them inside the plan save; changelog `docs/de|en/changelog/unreleased.md`. Check: `task docs` strict build | D-5 `model/applyOperation.ts:234-272,315-329`; `model/types.ts:201-228,359-365` (`PlanLocation.site_conditions`, `soil_profile`, `LocationFieldsPatch.site_conditions`); D-6 `editor/PropertiesPanel.tsx:239-251`; i18n reuse `pages.gardenPlan.sun.window.*`, `sun.foliage.*`. Check: `npx vitest run src/features/gardenPlanner -q`, `npx tsc --noEmit`, `npx eslint src/features/gardenPlanner`, bundle check `routeChunks.gardenPlanner` ≤ 120 KB (`task check:bundle` or the Vite budget script) | not applicable — no workflow/Taskfile change | route pin stays 890 (`pytest tests/unit/test_route_consumers_check.py` output recorded); schema-example ratchet updated for the new example fields; OpenAPI regenerates from code (`task openapi:lint` green) |
| #2487 | nothing beyond #2538's projection (frost_risk + drainage already projected by D-1); check: none of its own — the #2538 API tests cover the fields | not applicable — read only | not applicable — GP-FR-169/GP-FR-047 already specify the layers; status table is #2448's | `renderer/ConditionOverlays.test.tsx`: the three layers render pattern + icon per value, greyscale-distinguishable (as GP-ACC-052, `renderer/ZoneOverlays.test.tsx` pattern), hidden when toggled off; `editor/useLayerPrefs.test.tsx:14` registry defaults include the three ids; `zones/ZoneLegend` test: sections appear only for visible layers; `bed/BedHeader.test.tsx`: drainage line; `renderer/SvgPlanRenderer.test.tsx` snapshots updated; axe. Check: `npx vitest run src/features/gardenPlanner -q` output recorded | user guide: where the zones/last-watered layers are documented (`grep -rn "lastWatered\|Gießstand\|Ebenen" docs/de docs/en`), add the three layers in one short paragraph DE+EN; changelog. Check: `task docs` strict | D-4 `editor/layers.ts`, `editor/GardenPlanEditor.tsx:171-175,280-309,1420`, `renderer/{types.ts:93-103,SvgPlanRenderer.tsx:115-170,ConditionOverlays.tsx (new),HeadlessPlanRenderer.ts,BasePlanRenderer.ts}`, `zones/ZoneLegend.tsx`, `bed/BedHeader.tsx:68-140` (drainage via `soil_profile.drainage`, `pages.bed.soil.drainage`), i18n new keys DE+EN. Check: as #2538 + `i18n` parity (`npx vitest run src/i18n -q` or the i18n completeness test) | not applicable | not applicable — no route, no example change beyond #2538's |
| #2486 | not applicable — delivered by #2538 (panel) and PR #2537 (dialog, summary, field sheet) | not applicable | not applicable | acceptance "chips ≥ 64 px in field mode" already pinned by `bed/SunWindowFields.test.tsx` (PR #2537); the panel test of #2538 is this member's proof. Check: `npx vitest run src/features/gardenPlanner/bed src/features/gardenPlanner/editor/PropertiesPanel.test.tsx -q` output recorded | the #2538 docs sentence closes the "not yet" note | no file of its own | not applicable | not applicable |

## Risks

- **1 MB ceiling (E-13).** The large class sits at ≈ 0.85 MB; a nested object per location with
  defaults could eat the headroom. D-3 projects unknowns as absent; the ceiling test's measured
  byte count is recorded in Member results. If it still fails, the fallback is flat optional
  fields — a local adaptation of D-1, not a regression.
- **Collision with #2512** on `garden_plan_import_service.py:703-704` / export model if the
  round trip needs an additive key. Mitigation: #2512 is not started; if this group touches the
  export, say so in the bundle so #2512 rebases.
- **Collision with `plant-state-layer-legend`** on `layers.ts`, `SvgPlanRenderer.tsx`,
  `GardenPlanEditor.tsx`, `pages.json`: that group is serial after this one by partition order.
- **Bundle budget** `routeChunks.gardenPlanner` 120 KB: `SunWindowFields` is already a shipped
  chunk; the overlays are small SVG; measure with the existing bundle check before the PR.
- **Snapshot churn** in `SvgPlanRenderer.test.tsx` `__snapshots__`: layers off by default, so
  existing snapshots should not change; a changed snapshot is reviewed, not blindly updated.

## Open questions for the operator

None blocking. Reported with the bundle: D-2 (frost risk not editable from the editor — follows
#2512), D-3 (unknown projected as absent; the panel shows the "unknown" chip from absence).

## Member results

Filled during implementation. Each entry records the dispatched specialist and the
**actual output** of every declared check, never an assertion that it passed.

| Member | Specialist | Check | Actual output |
|---|---|---|---|
| #2538 | `nolte-engineering:fullstack-developer` (commits fdcca2622, 7968828ab, 3417372d1, c4d9d0dbb, 3d0df4456) | `uv run --locked --extra dev ruff check .` / `ruff format --check .` | "All checks passed!" / "2831 files already formatted" |
| #2538 | same | `pytest tests/unit/test_route_consumers_check.py tests/unit/test_schema_example_ratchet.py tests/unit/guards -q` | "3067 passed, 3 skipped, 5 deselected" — route pin 890 unchanged |
| #2538 | same | `scripts/check_schema_examples.py` | "704 model(s) without an example, exactly at the recorded ceiling" (all 4 new schemas have examples) |
| #2538 | same | `pytest tests/api tests/unit/domain tests/unit/test_schema_example_ratchet.py -q` | "11727 passed" |
| #2538 | same | `pytest tests/integration/test_garden_plan_repository.py -q` (live ArangoDB) | "1 failed, 33 passed" — the red is `TestGetPlanBenchmark::…p95_of_300_ms` XPASS(strict): local p95 < 300 ms (machine effect; CI xfails, #2526). Ceiling test green |
| #2538 | same | ceiling test measured size (large class, 150 beds) | 888 225 B without site conditions; **917 925 B** with every bed at the worst case (≈ 198 B/bed) < 1 000 000 B; seed now uses the worst case, docstring records both |
| #2538 | same | mypy ratchet hook (backend) | Passed |
| #2538 | same | `npx vitest run src/features/gardenPlanner` | "Test Files 100 passed, 1 skipped; Tests 1377 passed, 6 skipped" |
| #2538 | same | `npx tsc --noEmit -p .` / `npx eslint src/features/gardenPlanner` | no output / no output |
| #2538 | same | `npm run build && npm run bundle:check` | `routeChunks.gardenPlanner` 53.5 KB / 120 KB PASS; initial JS 379.6 / 400 KB PASS |
| #2538 | same | export→import round trip | `ExportLocation.site_conditions` already carries `sun_profile`; new test batch→export→import (new key) keeps `sun_profile`, `source=manual`; export/import files untouched (no #2512 collision) |
| #2538 fix | `nolte-engineering:fullstack-developer` (93f150911, 52680d5b6) | SCR-001 red→green `test_a_frost_risk_patched_after_the_read_survives_the_sun_profile_write` | before: `assert FrostRisk.UNKNOWN == 'high'` failed; after fix: passed. `site_conditions` removed from `_LOCATION_COLUMNS`; `PlanBatchWrite.location_sun_profiles` written via `_write_sun_profile` (`merge=True, keep_none=False`, 1202 → `WriteConflictError`) |
| #2538 fix | same | `pytest tests/unit/domain/services/test_garden_plan_service.py tests/api/test_garden_plan_api.py -q` | "138 passed" (SCR-002 cases red before: `assert ['a'] == []`) |
| #2538 fix | same | `pytest tests/integration/test_garden_plan_repository.py -k "large_garden_fits or sun_profile_write_keeps"` | "2 passed, 33 deselected"; ceiling measured **918 525 B** (longest literals `afternoon`/`normal`/`moderate`, 12.75 h) |
| #2538 fix | same | `pytest tests/unit/guards -q` / `ruff check .` / `ruff format --check .` | "3018 passed, 3 skipped, 5 deselected" / "All checks passed!" / "2831 files already formatted" |
| #2487 | `nolte-engineering:fullstack-developer` (6c5845eba, 72aff7909, f12bb7630, c20c0f5bb, 81d12e009) | `npx vitest run src/features/gardenPlanner src/i18n src/test/i18n src/test/pages/GardenPlanZones.test.tsx src/test/pages/GardenPlanConditionLayers.test.tsx` | "Test Files 112 passed, 1 skipped; Tests 1527 passed, 6 skipped" |
| #2487 | same | `npx tsc --noEmit -p .` / `npx eslint src/features/gardenPlanner …` | no output, exit 0 / no output, exit 0 |
| #2487 | same | `npm run build && npm run bundle:check` | plan route chunk 54.2 KB / 120 KB PASS (was 53.5 KB); initial JS 379.7 / 400 KB PASS |
| #2487 | same | `GP_BENCHMARK=1 npx vitest run applyOperation.benchmark layout.benchmark renderer.benchmark planIndex.slotFollow` | "Test Files 4 passed; Tests 18 passed" (renderer.benchmark covers buildScene + hit test only, not React overlay rendering) |
| #2487 | same | `git diff 1c4e49d1e -- renderer/__snapshots__` | empty — SvgPlanRenderer snapshots unchanged (layers off by default) |
| #2487 | same | i18n parity DE/EN (ad hoc key diff; no repo parity test exists) | `enums.json` 0 differences; `pages.json` 1 pre-existing difference `pages.phaseSequences.searchSequences` (not from this group) |
| #2486 | — (no code) | `npx vitest run src/features/gardenPlanner/bed src/features/gardenPlanner/editor/PropertiesPanel.test.tsx` | covered by the #2538 and #2487 runs above (1527 passed) |
| #2487 fix | `nolte-engineering:fullstack-developer` (3abfecd93, 50ae89b55, 175666881, 261914104) | new placement + plan-wide pattern tests against the old tip 81d12e009 | 5 of 16 red before (4 placement tests + plan-wide pattern test); all green after |
| #2487 fix | same | `npx vitest run src/features/gardenPlanner src/test/pages/GardenPlanConditionLayers.test.tsx src/test/pages/GardenPlanZones.test.tsx` | "Test Files 105 passed, 1 skipped; Tests 1435 passed, 6 skipped" |
| #2487 fix | same | `planContrast.test.ts` condition inks ≥ 3:1 (paper / active / planned / retired) | light: sun 5.82/3.57/4.19/4.93, moisture 11.27/6.92/8.11/9.54, frost 9.40/5.77/6.76/7.95; dark: sun 9.71/4.85/6.78/6.83, moisture 8.32/4.16/5.81/5.85, frost 11.97/5.98/8.36/8.42; high-contrast: sun 5.82/3.22/4.05/4.93, moisture 11.27/6.24/7.85/9.54, frost 14.53/8.05/10.12/12.30; old 45 % checker 2.03 light / 3.02 dark recorded as failing |
| #2487 fix | same | `tsc --noEmit` / `eslint src/features/gardenPlanner` / `npm run build && npm run bundle:check` | exit 0 / exit 0 / plan chunk 54.2 KB / 120 KB PASS; snapshots unchanged |
| bundle | session | `pytest tests/unit tests/api tests/contracts -q` (integration tip 261914104, 1 h run under load) | "2 failed, 23226 passed, 4 skipped, 6 deselected": (1) `test_req053_acceptance_matrix::test_the_committed_matrix_is_the_generated_one` → matrix regenerated via `scripts/gp_acc_matrix.py --write` (1 line), 5 passed; (2) `test_error_tracking_shape_redactor::test_the_redactor_is_linear[…]` timing-based, 34 passed alone in 1.55 s (load flake, unrelated) |
| bundle | session | `pytest tests/integration/test_garden_plan_repository.py tests/integration/test_garden_plan_tenant_isolation.py tests/integration/test_tenant_export_roundtrip.py -q` (live ArangoDB) | "323 passed, 1 xfailed in 182.96s" |
| bundle | session | frontend on tip 261914104: `tsc --noEmit` / `eslint .` / `vitest run` / `npm run build && bundle:check` | exit 0 / "0 errors, 136 warnings" (pre-existing, 0 in gardenPlanner) / "Test Files 608 passed, 1 skipped; Tests 6534 passed, 6 skipped" / plan chunk 54.2 KB / 120 KB PASS, initial JS 379.7 / 400 KB PASS |
| bundle | `nolte-engineering:frontend-usability-optimizer` | DoD usability pass on PropertiesPanel sun section, ZoneLegend/ViewBar toggles, BedHeader drainage, glyph row | no change needed; residual: glyph row may overlap the bed name on beds ≈ 46–68 px high (pattern still carries the value) — known limitation, in the PR risk notes |
| bundle | session | `task docs:build` (strict, provisions `.venv-docs`) | "Documentation built in 115.91 seconds", exit 0, `git status` clean (no regenerated file) |
| bundle | session | `ruff check .` / `ruff format --check .` / mypy ratchet (integration tip before the #2487 fixes) | "All checks passed!" / "2831 files already formatted" / "GREEN (headroom 15)" |
| #2538 | same | `task docs` strict build | superseded by the bundle row above |

## Deviations

| Member | Kind | What changed |
|---|---|---|
| #2538 | local adaptation | `recreateLocation` cannot send `site_conditions` in `create_location` (server `CreateLocationData` is `extra="forbid"`); it now returns `[create_location, update_fields {site_conditions:{sun_profile}}]`. Frost risk/drainage of a recreated bed are not restored (new bed server-side) |
| #2538 | local adaptation | shared helper lives at `app/domain/engines/site_conditions_merge.py` (`merge_site_conditions`, `NESTED_SITE_PARTS`, `sent_fields`), used by both services; PATCH behaviour unchanged (PATCH does not stamp `source`; only the batch stamps `manual`) |
| #2538 | local adaptation | batch model is a dedicated strict `PlanSunProfilePatch` (3 fields) instead of `_StrictSunProfile` (carries `source`); merge result validated against `SiteConditions`; explicit `site_conditions: null` → 422 `fields.site_conditions` (would erase frost risk) |
| #2487 | local adaptation | `RenderOptions.sunLayer/moistureLayer/frostLayer` are booleans (values already on `scene.shapes[].entry.source`), not a `byBed` map like `wateredLayer`; `HeadlessPlanRenderer`/`BasePlanRenderer` untouched (options optional); no read-only view consumes `wateredLayer`, so only the editor is wired |
| #2487 | local adaptation | layers registered after `underlay` to keep the existing toggle order; `SaveUndo.test.tsx` "remembers the grid switch" extended by the three default keys; extra tests `zones/ZoneLegend.test.tsx`, `src/test/pages/GardenPlanConditionLayers.test.tsx` |
| #2487 | local adaptation | docs: zones/last-watered layers are not yet in the user guide (WP 6.3 #2447), so the layer paragraph sits in "Sonne und Schatten am Beet" / "Sun and shade of a bed" plus one drainage sentence; stale sentences DE l.454 / EN l.446 ("last watered layer follows later") and DE l.336 / EN l.328 (plant-state tile) left for #2447 |
| #2538 | local adaptation | frontend keeps a normalised D-3 shape locally (`unknown`/`null`/`false` and empty parts dropped); the inverse sends the actual previous values, so undo restores the starting plan exactly; `SoilDrainage` moved to `model/types.ts` (re-exported from `bed/types.ts`); new testid `garden-plan-panel-sun-profile` registered in UI-NFR-022 v1.6 |

## Requirement coverage

Not applicable — symptom cluster, no group requirement artifact.

## Findings

| Finding | Source | Outcome | Reproduction | Issue |
|---|---|---|---|---|
| BE SCR-001 `garden_plan_service.py:125-128,882-884` + `garden_plan_repository.py:1048,1235`: batch writes the whole `site_conditions` column it read at `_load` (`merge=False`, no `_rev`); a `PATCH /locations` setting `frost_risk=high` between load and commit is reverted while `frost_exposed` stays True (drift #2512) | member verification pass (python-code-reviewer, warning) | fixed directly — batch writes only the `site_conditions.sun_profile` sub-path | unit test with fake repo: `_load`, mutate `frost_risk="high"`, `_commit` → expected `high`, was `unknown` (red → green recorded below) | — |
| BE SCR-002 `garden_plan_service.py:882-884`, `site_conditions_merge.py:37`: empty `{"site_conditions": {}}` / `{"sun_profile": {}}` creates a default `SiteConditions()`, stamps `manual`, lists the bed in `updated`, bumps the revision | same (suggestion) | fixed directly — empty `sun_profile` patch is a no-op | `batch(... fields={"site_conditions": {}}).updated == []` | — |
| BE SCR-003 `tests/integration/test_garden_plan_repository.py:139-149`: ceiling seed not the longest shape (`high` < `normal`, `5.5` < `12.75`), docstring says "largest shape" | same (suggestion, test) | fixed directly — longest literals, byte count re-measured (918 525 B) | ceiling test output recorded above | — |
| FE #2487 SCR-001 `renderer/ConditionOverlays.tsx:73,238,286`: sun glyph top-right overlaps the task badge (`SvgPlanRenderer.tsx:493-503`), drawn after `ShapeNode` → covers the task count | member verification pass (frontend-code-reviewer, warning) | fixed directly — disjoint corners for glyphs, zone number and badge; collision test | bed with `open_task_count>0` + `sun_window`, sun layer on, label zoom: count hidden | — |
| FE #2487 SCR-002 `ConditionOverlays.tsx:80,147,166` vs `ZoneOverlays.tsx:149-200`: moisture `drops` ≈ watered `dots` (same ink, centred dot), sun `rising` = watered `diagonal` path; below label zoom the pattern alone carries meaning (WCAG 1.4.1) | same (warning) | fixed directly — plan-wide disjoint pattern families + cross-layer uniqueness test | watered + drainage layers on, zoomed out: `drainage=good` indistinguishable from "watered 0–1 d" | — |
| FE #2487 SCR-003 `ConditionOverlays.tsx:155`: `checker` at `fillOpacity 0.45` ≈ 2.0:1 light / 3.0:1 dark (hand-computed) | same (warning, suspected) | fixed directly — full opacity/outlined; `planContrast.test.ts` extended to the condition inks | `sun_window=mixed`, light theme, below label zoom | — |
| FE #2487 SCR-004 `ConditionOverlays.tsx:234-244`: bbox corners place the glyph outside circular beds | same (suggestion) | fixed directly (circle handling as `TaskBadge`) | large circle bed at label zoom | — |
| FE #2487 SCR-005 `spec/ui-nfr/UI-NFR-022:172`: `bed-header-drainage` registered under `field-mode-*` | same (suggestion) | fixed directly — own `bed-header-*` row | grep `bed-header-` in §2.5.1 | — |
| FE #2487 SCR-006 docs DE:400 / EN:392 omit that the glyph appears at label zoom only; DE:398 „niedrig“ vs enum „Gering“ | same (suggestion) | fixed directly | read | — |
| FE #2487 SCR-007 `ConditionOverlays.tsx:254`: `ConditionLayer` not memoised | same (suggestion) | fixed directly (`memo`; `ZoneLayer` was never memoised — reviewer's premise wrong, left as is) | — | — |
| FE #2487 fix note: watered class `d4_7` pattern `diagonal` was identical to the first zone's 45° hatch → renamed to `zigzag` so the plan-wide uniqueness test holds (19 tiles, `data-pattern-family`) | fix pass of SCR-002 | fixed directly (local adaptation inside the shared touch surface) | plan-wide pattern test red on old tip | — |
| FE #2487 open: on low beds (< ~44 px) the glyph row is dropped; on medium-low beds it may still overlap the bed name label | fix pass | handed to the usability pass; if not cheaply fixable, recorded as known limitation | visual | — |
| FE #2487 info: undo of a saved delete does not restore `microclimate`/`soil_profile` (`applyOperation.ts:376-378`) → frost/drainage layers lose the bed's value | same (info) | recorded (same product decision as FE SCR-005 of #2538) | — | — |
| BE obs. `garden_resource_service.py:256` → `update_location_fields` (`garden_plan_repository.py` ~l.1252, `merge=False`, no `_rev`): `PATCH /locations` still writes the whole `site_conditions` column; a PATCH that read before a batch and writes after it resets `sun_profile` without a 409 (pre-existing class, PATCH side) | fix pass of SCR-001 | filed | code path; no test | #2569 |
| FE SCR-001 `editor/PropertiesPanel.test.tsx:328`: title says "not a PATCH" but no `bedApi` mock asserts it | member verification pass (frontend-code-reviewer, suggestion) | fixed directly (with #2487 dispatch) — `vi.mock('../bed/bedApi')` + `expect(patch).not.toHaveBeenCalled()` | add a `patchBed` call in `commitSunProfile`: test stays green today | — |
| FE SCR-002 `model/types.ts:208-231` / `bed/types.ts:81-89`: sun-profile shape declared four times | same (suggestion) | fixed directly — `bed/types.ts` derives from `model/types.ts` | add a field only in `bed/types.ts`: `tsc` silent | — |
| FE SCR-003 `model/applyOperation.test.ts:348`: no subtree delete (parent + child with sun profile) checks inverse ordering | same (suggestion, test) | fixed directly — subtree test added | reorder `deleteLocation` to `[...creates, ...updates]`: tests stay green | — |
| FE SCR-004 `editor/SaveUndo.test.tsx:210-211`: after redo of a saved undo only the plan object is asserted, not the pending queue (inverse + edit) | same (suggestion, test) | fixed directly — pending-queue assertion added | make redo enqueue nothing: test stays green | — |
| FE SCR-005 `applyOperation.ts:376-379`: delete → save → undo loses frost risk (and, as before, soil profile) | same (info) | recorded, product decision (matches server: a recreated bed is new) | — | — |
| FE SCR-006 `garden_plan_service.py:197-198`: every `sun_profile` batch write (incl. undo inverse) stamps `source=manual`; an earlier `computed` is not restored; `source` is not projected | same (info) | recorded, accepted (PATCH keeps client `source`; undo restores values) | — | — |
