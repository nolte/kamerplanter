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
| #2538 | same | `task docs` strict build | **not run by the member** (would provision `.venv-docs`); runs at the bundle gate |

## Deviations

| Member | Kind | What changed |
|---|---|---|
| #2538 | local adaptation | `recreateLocation` cannot send `site_conditions` in `create_location` (server `CreateLocationData` is `extra="forbid"`); it now returns `[create_location, update_fields {site_conditions:{sun_profile}}]`. Frost risk/drainage of a recreated bed are not restored (new bed server-side) |
| #2538 | local adaptation | shared helper lives at `app/domain/engines/site_conditions_merge.py` (`merge_site_conditions`, `NESTED_SITE_PARTS`, `sent_fields`), used by both services; PATCH behaviour unchanged (PATCH does not stamp `source`; only the batch stamps `manual`) |
| #2538 | local adaptation | batch model is a dedicated strict `PlanSunProfilePatch` (3 fields) instead of `_StrictSunProfile` (carries `source`); merge result validated against `SiteConditions`; explicit `site_conditions: null` → 422 `fields.site_conditions` (would erase frost risk) |
| #2538 | local adaptation | frontend keeps a normalised D-3 shape locally (`unknown`/`null`/`false` and empty parts dropped); the inverse sends the actual previous values, so undo restores the starting plan exactly; `SoilDrainage` moved to `model/types.ts` (re-exported from `bed/types.ts`); new testid `garden-plan-panel-sun-profile` registered in UI-NFR-022 v1.6 |

## Requirement coverage

Not applicable — symptom cluster, no group requirement artifact.

## Findings

| Finding | Source | Outcome | Reproduction | Issue |
|---|---|---|---|---|
| | | | | |
