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
| | | | |

## Deviations

| Member | Kind | What changed |
|---|---|---|
| | | |

## Requirement coverage

Not applicable — symptom cluster, no group requirement artifact.

## Findings

| Finding | Source | Outcome | Reproduction | Issue |
|---|---|---|---|---|
| | | | | |
