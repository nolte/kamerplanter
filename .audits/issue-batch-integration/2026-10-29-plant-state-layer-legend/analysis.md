# Group pre-analysis: 2026-10-29-plant-state-layer-legend

> Run-scoped artifact. Committed on the integration branch, removed with a fix-forward
> `git rm` before the bundle merges. It must never reach the default branch, and it must
> never be hidden behind a `.gitignore` entry.
>
> Origin: `issue-backlog-partition` 2026-10-29 (`.audits/issue-backlog-partition/2026-10-29.md`,
> approved 2026-10-29T15:20:49Z; hand-off payload
> `scratchpad/handoff/2026-10-29-plant-state-layer-legend.yml`). Research anchored by one
> read-only exploration agent against the `site-conditions-layers` bundle head `3042f8bc4`
> (PR #2570, the next `develop` tip) on 2026-10-30.

## Scope of this analysis

**Research question:** How do the plant-state channels that exist today only inside an
entered bed (`PlantMarkerBody`, `usePlantStates`) become a toggleable layer on the overview
plan with an "attention needed" filter (#2488), and how does the PDF/SVG legend render the
same channels and the phase colours (#2489) — without a new route, within the SVG allowlist,
the 5 s PDF budget and the 50 ms state budget?

**The group's single logical change, in one sentence:** Show plant states as a plan layer
with an "attention needed" filter and render the same state channels and phase colours in
the PDF/SVG legend.

**Out of scope:**
- A site-level plant-states route. #2455 item 11 (per visible bed above the marker LOD,
  paged ≤ 200) was confirmed as implemented on 2026-10-19; the route pin stays 890.
- Wiring `PlantStateService._frost_risk` (`plant_state_service.py:89-93`, still `False`
  "until WP 3.9") to `Microclimate.frost_risk` — no member asks for it; recorded as an open
  point for the operator (would change badge priority results for migrated beds, #2512 scope).
- The hover bubble on the overview (GP-UX-059 hover stays in the bed view, #2455 item 12).
- LOD/label refinements (#2490, single after this group), E2E part B (#2492).

**Tier:** 2 — one repository; additive layer + legend; the SVG writer stays inside the
GP-NFR-052 allowlist (no contract change).

## Members

| Issue | Class | Admitting predicate | Evidence |
|---|---|---|---|
| #2488 | feature-request | thematic coupling (anchor) | plan WP 7.22; measured: `renderer/SvgPlanRenderer.tsx:604-608` draws `PlantMarkerBody` only when `plant && interactive && state`, and the editor passes neither `enteredLocationKey` nor `plantStates` (`editor/GardenPlanEditor.tsx:1045-1069`) → the overview never shows channels today; `editor/layers.ts:4` names "the plant state" as the next layer |
| #2489 | feature-request | dependency chain | plan WP 7.23 depends on 7.22; `plan_svg_engine.py:820-848` draws every plant as one circle in `_PLANT_COLOR` and `_legend()` (:463-500) has one "Plant" entry (#2434 item 3 deferred phase colours to this package); `PlantShortInfo` (`garden_plan.py:561-567`) carries `phase_key` only |

**Dependency ordering:** #2488 → #2489 (the server-side state/phase enrichment of #2489
reuses the channel semantics #2488 fixes on the client; both read
`plant_state_calculator.py`).

**Shared touch surface:** `src/backend/app/domain/calculators/plant_state_calculator.py`
(read by both), `spec/e2e-testcases/fixtures/garden-plan-vectors.json` (`plant_state`
vectors + new `phase_color` vectors), i18n `pages.json` DE/EN, docs
`docs/{de,en}/user-guide/locations-substrates.md` (§Pflanzenzustand / §Plant state, PDF
paragraph). With the rest of the backlog: `editor/layers.ts`, `renderer/{scene.ts,SvgPlanRenderer.tsx}`,
`editor/GardenPlanEditor.tsx`, `zones/ZoneLegend.tsx` (#2490 after this group).

**Gates:** serial after group `site-conditions-layers` (PR #2570) on the same frontend
files; the integration branch is created only after #2570 merges.

## Mode decision

**Mode:** A — single strand.

**Reason:** both members `feature-request`, causes verified, no `security` member, no
external dependency, acceptance fixed by the decisions of 2026-10-19 (#2455, #2434, #2461).
Shared files profit from one strand.

## Structural finding

**Cluster shape:** symptom cluster.

**Root cause:** the plant-state channels (`plant_state_calculator.py` → `model/plantState.ts`)
are computed and drawn only in the bed view; neither the overview renderer nor the SVG writer
has a state or phase source. WP 3.7 (#2397) consciously built the bed view first; the plan
rows 7.22/7.23 are the deferred rest.

**Process finding:** none. **Preventive change:** not applicable. **Recurrence:** none.

## Plan approval

**Authorised by:** `2026-10-29-plant-state-layer-legend/plan-approval`, covering the members,
mode, and order above.

**Approval basis:** operator instruction 2026-10-30 ("mach weiter mit der gruppe und arbeite
sie möglichst autonom und vollständig ab") under the standing authorisation of 2026-10-09;
design decisions D-1…D-6 below are reported in the bundle.

**Group requirement artifact:** not applicable — symptom cluster; requirements = REQ-053
GP-UX-059 (l.683), GP-UX-060 (l.684), GP-UX-061 (l.685), GP-UX-005 (l.948), GP-NFR-038
(l.1651), GP-NFR-052 (l.1664), GP-NFR-073 (l.687), GP-FR-031 (l.394).

## Design decisions (binding for the dispatched runs)

- **D-1 Data source.** No new route. The overview fetches plant states per bed through the
  existing `usePlantStates`/`listPlantStates` (`planting/plantStateApi.ts:55-68`, 200 per
  page, ≤ 10 pages), only for beds that are at marker LOD (`renderer/lod.ts:27
  markersVisible`) **and** while the `plantState` layer is on; results are cached per bed key
  and refreshed with the existing day-change / `visibilitychange` logic. A new hook
  `usePlanPlantStates(siteKey, visibleBedKeys, enabled)` composes that; it exposes
  `Record<plantKey, PlantMarkerState>`.
- **D-2 Rendering.** `RenderOptions` gains `plantStateLayer?: { states: Record<plantKey,
  PlantMarkerState>; attentionOnly: boolean }`. In `renderer/scene.ts:105-157`: when the
  layer is on and a bed is at marker LOD, its plants become individual `SceneMarker`s with
  `state` (not `markerBatches`), drawn by `PlantMarkerBody` as in the bed view; `attentionOnly`
  drops markers without a badge. Below marker LOD the existing `SceneCluster.attentionOf()`
  gets the states (count + top badge, GP-UX-060); with `attentionOnly` clusters count only
  badged plants and hide when zero. Phase colours via the existing `markerFill(phaseKey,
  palette, phaseColors)` with `usePhaseColors` for the phases present in `model.plants`.
  GP-NFR-073: states are computed once per fetch (the calculator port), not per frame; the
  renderer benchmark (`renderer.benchmark.test.ts`) gains a case with 5 000 stated plants.
- **D-3 Layer + filter.** `editor/layers.ts` gains `plantState` (`defaultVisible: false`,
  `bar: 'toggle'`), icon in `LAYER_ICONS`, i18n `pages.gardenPlan.editor.zones.layers.{plantState,plantStateHint}`.
  The filter "only plants needing attention" is a dependent `ToggleButton` next to the layer
  toggles in `editor/ViewBar.tsx:127-146` (disabled while the layer is off), persisted in
  localStorage `kp_garden_plan_attention_filter` by a tiny hook beside `useLayerPrefs`.
  Testids: `garden-plan-layer-plantState`, `garden-plan-attention-filter`,
  `garden-plan-legend-plantState` (register in UI-NFR-022).
- **D-4 Legend (frontend).** `zones/ZoneLegend.tsx` gains `showPlantState`: a section that
  reuses `PlantStateLegend`'s ring/badge items (`PlantMarkerBody`/`PlantBadge`) and adds a
  phase-colour list for the phases present on the plan (`enums.phaseName.*`, swatch =
  `phaseColor(name)`). Lazy-load the section to protect the 120 KB chunk budget.
- **D-5 PDF/SVG (backend).** `garden_plan_export_service.py` enriches the view before
  rendering: (a) phase names for the distinct `phase_key`s (growth-phase repository), (b) per
  plant a `PlantVisualState` from `plant_state_calculator` using the same inputs
  `PlantStateService` builds (lift the input assembly into a shared helper so the API and
  the export compute identical states). `plan_svg_engine.py` draws, per plant below the
  2 000 counter threshold, the phase colour as fill (new `app/domain/engines/phase_colors.py`
  = Python reference of `planting/phaseColors.ts`, both pinned by new `phase_color` vectors
  in `garden-plan-vectors.json`), the lifecycle ring style (stroke-dasharray/width only) and
  at most one badge glyph (path, `#rrggbb`) — all within `ALLOWED_ELEMENTS/ATTRIBUTES`
  (:97-152), no `data-*`, no `style`. `_legend()` lists the phases present (swatch =
  circle), the lifecycle rings and the badge glyphs with DE/EN labels (dict at :238-271).
  Above the threshold nothing changes (counters, GP-NFR-038). Layout: legend entry count
  already feeds `choose_layout`.
- **D-6 Budget evidence.** PDF ≤ 5 s test (`test_garden_plan_export_service.py:134-150`)
  stays green with states enabled on the large fixture; allowlist test (:231-321) stays
  green; a new legend content test replaces `["Bed", "Bed (planned)", "Tree"]` (:418-436)
  with the phase/state entries; the frontend `plantState.benchmark.test.ts` (5 000 ≤ 50 ms)
  stays green.

## Completeness matrix

Columns as in the precedent artifact (`site-conditions-layers`): backend source, migration,
spec, tests, docs, frontend, config/workflows, generated indexes/pins.

| Member | Backend source | Migration | Spec | Tests | Docs | Frontend | Config / workflows | Generated indexes / pins |
|---|---|---|---|---|---|---|---|---|
| #2488 | not applicable — no route, no model change (D-1) | not applicable | not applicable — GP-UX-061 specifies layer + filter; status table is #2448's | `renderer/scene.test.ts` (stated markers at LOD, clusters count badges, attentionOnly), `renderer/SvgPlanRenderer.plantState.test.tsx` (channels on the overview), `editor/useLayerPrefs.test.tsx` (+`plantState`), new `editor/useAttentionFilter.test.ts`, `zones/ZoneLegend.test.tsx` (+ plant-state section, phase list), `src/test/pages/GardenPlanConditionLayers.test.tsx` twin for the toggle + filter + axe, `renderer.benchmark.test.ts` 5 000 stated plants ≤ 16 ms median, `model/plantState.benchmark.test.ts` green; GP-ACC-051/052 (`bed/BedPlanTab.plantState.test.tsx`, `plantMarkerStyle.test.ts`) unchanged green. Check: `npx vitest run src/features/gardenPlanner src/test/pages -q`, `GP_BENCHMARK=1 npx vitest run …benchmark…` outputs recorded | DE `docs/de/user-guide/locations-substrates.md:336` / EN `:328` replace "Ebene und Filter folgen später" with the shipped behaviour; layer paragraph DE :400 / EN :392 add the plant-state layer; changelog DE/EN. Check: `task docs:build` strict | D-1 `planting/usePlanPlantStates.ts` (new), D-2 `renderer/{types.ts,scene.ts,SvgPlanRenderer.tsx}`, D-3 `editor/{layers.ts,ViewBar.tsx,GardenPlanEditor.tsx,useAttentionFilter.ts}`, D-4 `zones/ZoneLegend.tsx`, i18n keys DE+EN. Check: `tsc --noEmit`, `eslint`, bundle check ≤ 120 KB | not applicable | route pin 890 unchanged (`pytest tests/unit/test_route_consumers_check.py`); UI-NFR-022 testid rows |
| #2489 | D-5 `domain/engines/phase_colors.py` (new, reference), shared state-input helper (lift from `plant_state_service.py:63-104`), `garden_plan_export_service.py:231-333` enrichment, `plan_svg_engine.py` `_plant_layer` (:820-848) + `_legend()` (:463-500) + labels (:238-271). Check: `ruff`, mypy ratchet, `pytest tests/unit/domain/engines tests/unit/domain/services/test_garden_plan_export_service.py tests/api/test_garden_plan_export_api.py -q` output recorded | not applicable | not applicable — GP-UX-005/061 specify the PDF legend | `test_plan_svg_engine.py`: legend content (phases + rings + badges, DE/EN), allowlist class green (every emitted tag/attribute on the allowlist), counters ≥ 2 000 unchanged; `test_garden_plan_export_service.py` PDF ≤ 5 s with states on the large fixture; new `test_phase_colors.py` + `model/plantState.vectors`-style vector test for `phase_color` both sides; `tests/api/test_garden_plan_export_api.py` SVG smoke. Check: commands with output recorded | PDF export paragraph DE :486 / EN ≈:478 (legend shows phases and states); changelog. Check: `task docs:build` strict | `planting/phaseColors.ts` pinned against the new vectors (TS port test); legend swatch parity | not applicable | schema-example ratchet unchanged (no new API model); route pin unchanged; vectors fixture extended (`spec/e2e-testcases/fixtures/garden-plan-vectors.json`) |

## Risks

- **Fetch fan-out** on large sites: N marker-LOD beds × ≤ 10 pages. Mitigation: fetch only
  while the layer is on, cache per bed, abort on layer-off; record the request count in the
  test for a 20-bed plan.
- **Renderer frame budget** with 5 000 individual stated markers instead of batched paths:
  the benchmark case decides; fallback is to keep batching per (phase colour × lifecycle)
  and draw badges as a separate overlay.
- **PDF budget** with per-plant state computation: computed once in the service, not in the
  writer; above 2 000 plants the counters apply as today.
- **Allowlist drift:** every new SVG element/attribute must already be in
  `ALLOWED_ELEMENTS/ATTRIBUTES`; the allowlist test is the gate, the allowlist is not widened.
- **Collision** with #2490 (same renderer files) — serial after this group by partition order.

## Open questions for the operator

None blocking. Reported with the bundle: `_frost_risk` placeholder in `PlantStateService`
(frost badge never fires today; wiring it to `microclimate.frost_risk` is a product decision
that interacts with #2512).

## Member results

| Member | Specialist | Check | Actual output |
|---|---|---|---|
| #2488 | `nolte-engineering:fullstack-developer` (30604a0cf, 293e66887, 60e2be838, 1dca4de8f, fc5f49663) | `npx vitest run src/features/gardenPlanner src/test/pages` | "Test Files 318 passed, 1 skipped; Tests 3579 passed, 7 skipped" |
| #2488 | same | `GP_BENCHMARK=1 npx vitest run applyOperation.benchmark layout.benchmark renderer.benchmark planIndex.slotFollow plantState.benchmark` | "5 files, 21 passed"; 5 000 stated single markers `buildScene` median **1.03 ms** (budget 16 ms); scene 0.16 ms, hit test 0.08 ms; `plantState.benchmark` 5 000 plants 21.37 ms (budget 50 ms) |
| #2488 | same | `usePlanPlantStates.test.ts` request count | 20 beds, 3 at marker LOD → exactly 3 GET `/locations/bed{0,1,2}/plant-states?offset=0&limit=200`, `requestCount()==3`; layer off → 0 |
| #2488 | same | `npx tsc --noEmit -p .` / `npx eslint src/features/gardenPlanner …` | no output / no output |
| #2488 | same | `npm run build && npm run bundle:check` | plan chunk **56.2 KB / 120 KB** (was 54.2); initial JS 379.7 / 400 KB; "All bundle budgets within limits." |
| #2488 | same | `pytest tests/unit/test_route_consumers_check.py -q` | "16 passed" — route pin 890 unchanged |
| #2488 | same | snapshots / pattern registry | `renderer/__snapshots__` unchanged; no new `<pattern>`, plan-wide pattern test (19) green; GP-ACC-051/052 green |
| #2489 | `nolte-engineering:fullstack-developer` (df577e72e, 986886a41, abb64f0e9, 8302b56b3) | `ruff check . && ruff format --check .` / mypy ratchet | "All checks passed!" / "2844 files already formatted" / "3419 findings now, 3434 recorded … GREEN" |
| #2489 | same | `pytest tests/api tests/unit/guards/test_keyed_service_writes_take_the_tenant.py tests/unit/test_route_consumers_check.py tests/unit/test_schema_example_ratchet.py tests/integration/test_garden_plan_tenant_isolation.py tests/integration/test_plant_state_repository.py` (live ArangoDB) | "3655 passed in 318.27s" — route pin 890 unchanged |
| #2489 | same | `pytest tests/unit/guards tests/unit/domain/engines tests/unit/domain/calculators …` | 5991 passed after fixing `test_geometry_vectors` for the new `phase_color` operation; vector/engine/export/plant-state tests "855 passed" |
| #2489 | same | PDF budget (GP-NFR-038) with 1 999 stated plants in 3 beds | **1.113 s** (limit 5 s) |
| #2489 | same | GP-NFR-052 / GP-ACC-045 allowlist class | unchanged, green; extra allowlist test with every lifecycle + badge green; allowlist not widened |
| #2489 | same | legend golden `tests/unit/domain/engines/golden/plan_svg_legend_de.svg` (raw writer output of `<g id="legend">`) | green; counters ≥ 2 000 unchanged + new test "states ignored above the threshold" |
| #2489 | same | frontend `npx vitest run …phaseColors.vectors.test.ts` + model tests / `tsc` / `eslint` | "13 passed / 319 passed, 3 skipped" / clean / clean; 22 `phase_color` vectors (10 named phases, case/whitespace/separators, negative hash, umlaut, emoji, overflow, empty) |
| #2489 | same | `task docs:build` strict | "Documentation built in 52.33 seconds", only pre-existing INFO anchor notes |
| #2488 fix | `nolte-engineering:fullstack-developer` (1b8a43b46, a7d0ac25e, 2713e1bd5, 9dd1e7d3f, 4e83e09fa) | `npx vitest run src/features/gardenPlanner src/test/pages` | first run "1 failed, 3610 passed, 7 skipped" (`ZoneLegend.test.tsx` pinned the old unsorted phase order) → adjusted, `zones` "47 passed"; changed suites renderer/planting/editor/pages green individually (full re-run at the bundle gate) |
| #2488 fix | same | concurrency / 404 cache / refresh tests | 10 beds: peak exactly 4 concurrent requests, all 10 served; queue dropped on view change and on layer off; zoomed-out plan: 0 plant-state + 0 growth-phase requests; `ph_seq` 404 → exactly 1 request per session; falsification with the old hook (restored via `cp`): 4 hook tests red, page tests red with old `phaseColors.ts`/editor |
| #2488 fix | same | `GP_BENCHMARK=1 npx vitest run renderer.benchmark plantState.benchmark` / `tsc --noEmit` / `eslint src/features/gardenPlanner` / `npm run build && bundle:check` | "2 files, 5 passed" / exit 0 / 0 problems / plan chunk **56.5 KB / 120 KB**, "All bundle budgets within limits"; snapshots unchanged |
| #2489 fix | `nolte-engineering:fullstack-developer` (f6b98db59, 16a9d688a, 96e4b2c58, eba5b4aad, 81803581a, f352a5e7a) | unit + API (svg engine, phase_colors, export service, plant-state service, export API) | "240 passed"; SCR-001 red→green: old code 3 red, new green (entry-key colour in the SVG) |
| #2489 fix | same | `tests/integration/test_plant_state_repository.py` (live ArangoDB) | "15 passed" (3 new: site-wide read == per-bed reads over 3 beds) |
| #2489 fix | same | repository calls for 50 beds | before: 50 × `list_bed_plants` = 250 AQL statements (worst case ≈ 10 000); after: ⌈plants/200⌉ calls (1–3 for 50–500 plants) via `list_plants_in_beds`; test asserts ≤ ⌈plants/200⌉+1 for 1/4/10 plants per bed |
| #2489 fix | same | 12-phase legend at 1:50 A4 (`test_the_bigger_legend_still_fits_the_acceptance_page`) | renders (`fits=True`), 6 phase entries + "+6 more phases"; old code `fits=False` (the 422); 30-char name truncated to 25 chars (`_LEGEND_LABEL_CHARS`), 6.8 mm + text ≤ 46 mm; golden unchanged |
| #2489 fix | same | `tests/unit/guards -q` | "1 failed, 3020 passed, 3 skipped" → `test_service_constructors_read_their_parameters` (`frost_risk_of(location)` unread param, pre-existing at 4e83e09fa) fixed in f352a5e7a, file green ("60 passed" with service tests); full guard suite re-run at the bundle gate |
| #2489 sec-fix | `nolte-engineering:fullstack-developer` (95fe8bc2c, 4d4eac462, f0cc700d8, 576dc4838) | unit + API + guards (export service, plant-state service/repository, svg engine, keyed guard, constructors guard, new repository unit tests, underlay print/API) | "283 passed"; phase-name lookups 400 → **1** (`IPhaseRepository.get_phase_names(keys)`, `DOCUMENT(@phases, k)`), counter double has no `get_phase_by_key` |
| #2489 sec-fix | same | integration `test_plant_state_repository.py` (+ `TestSlotOnlyPlants`, `TestManyBeds`) + new `test_lifecycle_phase_names.py` (live ArangoDB) | "24 passed" |
| #2489 sec-fix | same | repository/layer/route guards (`test_tenant_scoped_reads_are_derived`, `test_arango_call_surface_scoping`, `test_no_dead_unscoped_repository_reads`, merge-mode, `test_layer_imports_check`, `test_route_consumers_check`, `test_route_role_guards_check`) + `tests/unit/data_access` | "2242 passed" |
| #2489 sec-fix | same | `ruff check .` / `ruff format` / mypy ratchet | "All checks passed!" / unchanged / GREEN (3419 now, 3434 recorded) |
| bundle | session | backend gate (tree moving from f352a5e7a to 576dc4838 during the run): `ruff check .` / `ruff format --check .` / mypy ratchet / `pytest tests/unit tests/api tests/contracts -q` | "All checks passed!" / "2845 files already formatted" / GREEN / "2 failed, 23345 passed, 4 skipped, 6 deselected in 2668s": (1) `test_error_tracking_redacts_paths::test_the_request_url_is_the_route_pattern_with_method_kept` → passes alone ("10 passed", load flake); (2) `test_write_route_gates::…::test_the_unresolved_receiver_count_does_not_grow` → **real**: 2804 unresolved receivers = ceiling 2804 (`< 2804` required) — new code carries untyped receivers; fixed by annotation (ceiling never raised), see row below |
| bundle | session | `pytest tests/integration/test_garden_plan_repository.py tests/integration/test_garden_plan_tenant_isolation.py tests/integration/test_plant_state_repository.py tests/integration/test_tenant_export_roundtrip.py -q` (live ArangoDB) | "1 failed, 347 passed": the red is `TestGetPlanBenchmark::…p95_of_300_ms` XPASS(strict) — local machine faster than the CI xfail premise (#2526), unrelated |
| bundle | `nolte-engineering:fullstack-developer` (b25662e76) | `test_write_route_gates.py` unresolved-receiver guard | `genuine_unresolved_call_count()` 2804 → **2787** (develop baseline at merge-base baf7000a3: 2792; ceiling 2804 untouched); 12 branch calls removed by typed constructs (`Final[re.Pattern[str]]`, bitwise UTF-16 unit, typed rank functions, generator `_legend`/`_plant_legend`/`_bedded_plants`, `rows += window`) + 5 pre-existing `entries.append`/`seen.append`; "151 passed"; targeted suites "4227 passed"; ruff / format / mypy GREEN |
| bundle | `nolte-engineering:frontend-usability-optimizer` | DoD usability pass (ViewBar toggles + filter, legend section, cluster label, hint texts) | no change needed |
| bundle | session | frontend on tip f352a5e7a: `tsc --noEmit` / `eslint .` / `vitest run` / benchmarks / `npm run build && bundle:check` | exit 0 / "0 errors" (pre-existing warnings only) / "Test Files 613 passed, 1 skipped; Tests 6595 passed, 7 skipped" / "5 files, 21 passed" / plan chunk 56.5 KB / 120 KB PASS, initial JS 379.7 / 400 KB PASS |
| bundle | session | `task docs:build` (strict) on tip f352a5e7a | "Documentation built in 91.06 seconds", exit 0, no regenerated tracked file |
| #2489 fix | same | `tests/unit/test_route_consumers_check.py` / PDF budget / `ruff` / `ruff format` / mypy ratchet | "16 passed" (pin 890) / 1 999 stated plants **1.14 s**, GP-ACC-030 0.12 s / "All checks passed!" / "2845 files already formatted" / GREEN (headroom 15) |

## Deviations

| Member | Kind | What changed |
|---|---|---|
| #2488 | local adaptation | hook `usePlanPlantStates(siteKey, visibleBedKeys, enabled)` also returns `phaseNames`; request counter is a function (`requestCount()`, ref-based); marker-LOD beds come from new `renderer/scene.ts` `markerLodBedKeys(model, viewport)`; shared pieces extracted: `planting/plantStateClock.ts`, `viewsOf` in `usePlantStates.ts`, `usePhaseNames`/`colorsOf` in `phaseColors.ts`, `planting/PlantStateLegendItems.tsx` (used by `PlantStateLegend`) |
| #2488 | local adaptation | `attentionOnly`: beds whose states are not loaded keep their count/normal markers; hidden only when states are known and none has a badge; a selected marker stays visible; cluster count under the filter = badged plants, aria label "n Pflanzen · n mit Handlungsbedarf"; phase colours are passed to the renderer only while the layer is on (default view unchanged, no growth-phase requests without the layer) |
| #2488 | local adaptation (D-1 vs D-2 tension) | clusters **below** marker LOD show badge count/top badge only for beds already in the cache (zoomed in before); never-loaded beds show the plain count even under the filter — consequence of D-1 (no fetch below LOD, #2455 item 11 confirmed). Reported to the operator with the bundle; GP-UX-060 cluster semantics hold for loaded beds |
| #2489 | local adaptation | shared helper is `app/domain/services/plant_state_inputs.py` (`phase_facts`, `frost_risk_of`, `visual_state_of`); `PlantStateService._frost_risk`/`_state_of` removed in favour of it; `schemas.py` imports `phase_facts` from the new module; export reads states bed by bed (pages of 200, `tenant_key` on every read, only beds of the verified site), phase names once per distinct key; both repositories optional constructor args wired in `get_garden_plan_export_service` |
| #2489 | local adaptation | third frontend file touched: `model/geometry.vectors.test.ts` (`LAYOUT_OPERATIONS` += `phase_color`) with its Python twin `test_geometry_vectors.py`; `phaseColors.ts` unchanged (TS hash reproducible in Python: int32 `|0`, UTF-16 code units; checked with node incl. umlaut/emoji/overflow); fallback hashes the un-normalised name (pinned by the vectors) |
| #2489 | local adaptation | on paper the harvesting double ring is a thick ring and the failed cross an empty ring (rings via stroke width/dasharray + already-allowed `fill-opacity`); phase keys that are no growth phase (sequence entries) get no name and keep the default colour, ring and badge still drawn; `harvest_ready` is not drawn separately (part of the "harvest" badge) |
| #2488 fix | local adaptation | `SceneCluster.count` = total plants, new `shownCount` = drawn number under the filter (badged + unknown-state plants); per-plant filter rule; `refresh` on new `plan.revision` and after `ZonePanel.onChanged` (no refresh on reload without revision change — documented); failed beds retried on the next signature change and reported via `captureHandledError`; `PLANT_STATE_CONCURRENCY = 4` FIFO; `usePhaseNames` only for phases of plants with loaded states + session 404 cache; legend lists phases of loaded plants only (docs adjusted); plural key `clusterAttention_{one,other}`; `Intl.Collator` sort; `enums.phaseName.{drying,curing,cloning}` DE+EN; disabled filter → `aria-disabled` + `aria-describedby` |
| #2489 fix | local adaptation | `phase_facts`/`visual_state_of` moved to `app/domain/calculators/plant_state_inputs.py`, `frost_risk_of` stays in the service module; growth-phase name preferred, row `phase_name` fallback; new repository method `list_plants_in_beds` (`FILTER p.location_key IN @beds`, care events keyed per bed), `list_bed_plants` = single-bed case; legend cap 6 phases + "+n weitere Phase(n)" / "+n more phase(s)"; `_LEGEND_LABEL_CHARS = 25` from column width; known residual: 12 phases + 5 object types + all rings + all badges = 24 entries still exceed the 20-entry A4-landscape legend (needs a total budget or more columns) — recorded, not in the test; "Number = plants in the bed" (26 chars) untouched |
| #2489 sec-fix | local adaptation | `list_plants_in_beds`: `LET bed = p.location_key ?? slot.location_key`, `FILTER bed IN @beds` (slot rule kept, row reports the resolved bed); `limit` outside 1..200 or `offset < 0` → `ValueError` (no silent clamp: a shorter window would look like the end to the pager); > 500 beds read in chunks and merged by plant key; export catches `Exception` around the enrichment (domain layer may not import `arango`) → `logger.warning("garden_plan.plant_states_unavailable", site_key, error=<class>)` and plain circles; page-cap warning `garden_plan.plant_state_page_cap_reached`; keyed-service guard minimum for `GardenPlanExportService` 5 → 9 (counts private methods) |
| #2489 | note | commit trailers carry "Claude Opus 5.5" (agent model); corrected to the session attribution before the PR |
| #2488 | local adaptation | legend frame + title synchronous (testid `garden-plan-legend-plantState`), content `zones/PlantStateLegendSection.tsx` lazy; phases labelled via `enums.phaseName.<normalised>` with fallback to the stored name; page test `src/test/pages/GardenPlanPlantStateLayer.test.tsx`; `SaveUndo.test.tsx` prefs extended by `plantState: false`; docs frost note kept (still true: `_frost_risk` placeholder) |

## Requirement coverage

Not applicable — symptom cluster, no group requirement artifact.

## Findings

| Finding | Source | Outcome | Reproduction | Issue |
|---|---|---|---|---|
| FE #2488 SCR-001 `renderer/scene.ts:191` + `SvgPlanRenderer.tsx:754-757`: under `attentionOnly` the cluster `count` equals `attention`, so `clusterSummary` speaks "2 plants · 2 need attention" for 4 plants; docs DE :404 / EN :396 promise the total | member verification pass (frontend-code-reviewer, warning) | fix directly — `SceneCluster` keeps the total, visible number derived separately | bed with 4 plants, 2 badged, filter on → label says 2 instead of 4 | — |
| FE #2488 SCR-002 `SvgPlanRenderer.plantState.test.tsx:178-190`: cluster label under the filter untested | same (warning, test) | fix directly — add the `attentionOnly: true, attention > 0` label case | swap count/attention: tests stay green | — |
| FE #2488 SCR-003 `planting/usePlanPlantStates.ts:62-64,70`: cleanup writes the old `siteKey` closure into the cache; a `siteKey` change without remount never loads again (unreachable today: `GardenPlanRoute.tsx:135-141` remounts) | same (suggestion) | fix directly + rerender test | `renderHook` then `rerender({s:'site_2'})` → no second request | — |
| FE #2488 SCR-004 `usePlanPlantStates.ts:21-22`: exported `refresh` never called by the editor; failures swallowed silently (:87-92), bed stays plain until foreground | same (suggestion) | fix directly — wire refresh after plan reload/care actions; failed beds retried on the next LOD/signature change | reload plan without remount: badges stale | — |
| FE #2488 SCR-005 `GardenPlanEditor.tsx:315-319` + hook :72-93: no concurrency limit/debounce — zoom across the LOD threshold starts one GET per bed at once (250 in the benchmark plan) | same (suggestion, suspected) | fix directly — small in-flight cap (4) with queue, cancel on signature change | benchmark plan with 250 beds in view → 250 parallel GETs | — |
| FE #2488 SCR-006 `GardenPlanEditor.tsx:320-324` → `phaseColors.ts:57-79`: `usePhaseNames` fetches `/growth-phases/{key}` for every `phase_key` of the plan regardless of LOD; sequence entries answer 404 | same (suggestion, suspected) | fix directly — resolve only phase keys of plants with loaded states / drawn markers; cache 404s | layer on, zoomed out: N growth-phase GETs, 0 plant-state GETs | — |
| FE #2488 SCR-007 `scene.ts:158-170` (pinned `scene.test.ts:292,300-303`): "unknown" is judged per bed; in a partially known bed the filter hides stateless plants and drops a cluster | same (suggestion) | fix directly — per-plant unknown keeps the plant/cluster | 4 plants, 2 known calm, filter on → cluster gone | — |
| FE #2488 SCR-008: EN `pages.json:5327-5328` plural follows `count` only ("4 plants · 1 need attention"); `GardenPlanEditor.tsx:343` sorts raw phase names without locale; `enums.phaseName` lacks `drying`/`curing`/`cloning` known to `phaseColors.ts:15-19` | same (suggestion) | fix directly — separate plural key for the attention part, locale-aware sort of translated labels, add the three enum keys DE+EN | DE legend shows "drying" raw | — |
| FE #2488 SCR-009 `editor/ViewBar.tsx:166-181`: disabled filter toggle not focusable; `attentionFilterDisabledHint` only via hover tooltip | same (suggestion, a11y) | fix directly — `aria-disabled` + `aria-describedby` | Tab through the ViewBar with the layer off: hint never announced | — |
| BE #2489 SCR-001 `garden_plan_export_service.py:400-409`: `_phase_names` resolves only `growth_phases`; plants on phase-sequence entry keys get `None` → printed in `_PLANT_COLOR` while the bed view colours them via `view.phase.name` (`plant_state_repository.py:149-151` already returns `phase_name`); test `:542` pins the wrong behaviour "as on screen" | member verification pass (python-code-reviewer, warning) | fix directly — fall back to the row's `phase_name`, growth-phase name preferred (as the frontend) | plant with entry `current_phase_key` → PDF disc `#1b5e20`, bed tab `phaseColor(name)` | — |
| BE #2489 SCR-002 `garden_plan_export_service.py:387-398`: `_standing_plants` calls `list_bed_plants` per bed → 5 AQL statements per non-empty page per bed; 50 beds ≈ 250 statements, worst case 1 999 single-plant beds ≈ 10 000; no bed cap | same (warning) | fix directly — one site-wide read (`bed_keys IN @beds`, paged) for the export | site with 1 999 pot locations × 1 plant → PDF | — |
| BE #2489 SCR-003 `plan_svg_engine.py:662-667,757-759`: one legend entry per phase without cap (+ up to 6 rings, 5 badges); 12 phases + 5 object types ≈ 32 entries ≈ 104 mm strip → a fixed-scale PDF that fit before answers 422 `plan.does_not_fit`; `test_the_bigger_legend_still_fits_the_acceptance_page` (:761-772) uses one phase | same (warning, computed) | fix directly — cap phase entries (most frequent first, "+n weitere/more") and test with 12 phases at 1:50 A4 | 4 × 6 m plan, 12 phases, scale 1:50, A4 → 422 | — |
| BE #2489 SCR-004 `plan_svg_engine.py:759`: "Phase: " + 22 chars + "…" ≈ 46 mm text + 6.8 mm swatch > `_LEGEND_COLUMN_MM` 46 → runs into the next column | same (suggestion, computed) | fix directly — shorter truncation / width-aware label | long phase name in a 2-column legend | — |
| BE #2489 SCR-005 `garden_plan_export_service.py:372,389`: `assert … # noqa: S101` in production code (dropped under `python -O`) | same (suggestion) | fix directly — explicit `if … is None` guards | — | — |
| BE #2489 SCR-006 `domain/services/plant_state_inputs.py` `phase_facts` is pure (no I/O) but lives in services and is imported by `api/…/schemas.py:40` | same (suggestion, layering) | fix directly — move the pure parts to `domain/calculators/` | — | — |
| BE #2489 info: parity of `phase_facts`/`frost_risk_of`/`visual_state_of` with the removed service methods confirmed; ownership + paging + threshold gates confirmed (tests :585-609); allowlist attributes `transform`/`fill-opacity`/`stroke-dasharray` pre-existing; golden compares raw writer bytes; 22 vectors cover int32/UTF-16/astral/empty; retention/erasure untouched | same (info) | recorded | — | — |
| SEC #2489 W-1 `garden_plan_export_service.py:417-418`: one `get_phase_by_key` per distinct phase key, unbounded by the page cap (1 999 plants on ~400 species → hundreds of reads) | security read (python-code-reviewer, warning) | fix directly — batched key read | site with ~400 distinct phase keys → SVG | — |
| SEC #2489 W-2 `garden_plan_export_service.py:376-380` + `plant_state_repository.py:138`: the multi-bed read filters `p.location_key IN @beds` only; slot-only plants (`location_key = null`) are resolved via the slot by the service but never read → plain circle (correctness, not a leak) | same (warning, suspected) | fix directly — include slot-resolved plants in the AQL + tests | plant with `slot_key`, `location_key=null` → PDF without ring | — |
| SEC #2489 S-1 `garden_plan_export_service.py:376/402`: no error handling — a repository error turns the export into a 500 (fail-closed; no PII in logs) | same (suggestion) | fix directly — degrade to plain circles with `logger.warning` like the underlay path | repo double raising in `list_plants_in_beds` → 500 | — |
| SEC #2489 S-2 `plant_state_repository.py:93-100`: `list_plants_in_beds` caps neither `len(bed_keys)` nor `limit` (callers bound them) | same (suggestion) | fix directly — clamp/validate + chunking | direct call with `limit=10**6` → no error | — |
| SEC #2489 S-3 `garden_plan_export_service.py:401-407`: silent stop after 11 full pages (unreachable below the 2 000 threshold) | same (suggestion) | fix directly — warning log | double returning full pages | — |
| SEC #2489 I-7 `tests/unit/guards/test_keyed_service_writes_take_the_tenant.py:424/455`: `GardenPlanExportService` minimum of 5 `tenant_key` methods while it now has ≥ 8 → guard would not trip on a regression of the new methods | same (info) | fix directly — raise the pinned minimum | — | — |
| SEC #2489 info: AQL fully bind-parameterised, tenant filter on plants/tasks/care events/findings/harvest batches, stable `SORT p._key` before `LIMIT`; `DOCUMENT()` reads of cultivar/phase without tenant check are keyed only by own-tenant plants (residual only if a write path accepted foreign `cultivar_key`); care events indexed per bed; ownership before every read; SVG escaping + allowlist + `#RRGGBB` from fixed tables; no personal fields read, no cache | same (info) | recorded | — | — |
| FE #2488 info: lazy legend section (`ZoneLegend.tsx:213`) has Suspense but no error boundary (same pattern as `ZonePanel`); `plantStateHint` promises counts for far beds that only holds for previously loaded beds (wording for the usability pass) | same (info) | recorded; hint wording handed to the usability pass | — | — |
