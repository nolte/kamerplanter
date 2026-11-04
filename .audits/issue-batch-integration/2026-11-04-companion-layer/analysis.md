# Group pre-analysis: 2026-11-04-companion-layer

> Run-scoped artifact. Committed on the integration branch, removed with a fix-forward `git rm` before the bundle merges.

## Scope of this analysis

**Research question:** Can #2658 (companion edges endpoint) and #2659 (plan overlay) ship as one bundle, and what must "same expression as the planting dialog" mean in code?

**The group's single logical change, in one sentence:** The garden plan shows a companion-planting layer whose lines come from a new per-bed companion-edges endpoint that judges each adjacent pair with the same rule as the planting dialog.

**Out of scope:** E2E (WP 8.31, #2674); new companion data or scores; any change to how `adjacent_to` edges are derived (WP 3.3).

**Tier:** 2 — one repository, additive read endpoint.

## Members

| Issue | Class | Admitting predicate | Evidence |
|---|---|---|---|
| #2658 | feature-request | thematic coupling | companion edges per bed for the overlay (REQ-053 §16.2 GP-FR-134) |
| #2659 | feature-request | dependency chain | issue body "Depends on: WP 8.15 (#2658)" |

Re-check of the partition record: both OPEN, author `nolte` (trusted), bounded, no asserted cause. Kind "symptom" overturned to **neither** (feature chain).

**Dependency ordering:** #2658 → #2659.

**Shared touch surface:** none by file; #2659 consumes #2658's response shape. Against other work: `api/v1/locations/` (serial after reach-thresholds #2707, before bed-photos).

## Mode decision

**Mode:** A — single strand. Deterministic acceptance, no external dependency.

## Structural finding

**Cluster shape:** neither — feature chain. **Process finding:** none.

**Measured observations (origin/develop 705047be1):**
- `CompanionPlantingEngine.check_compatibility(species_key, slot_key, *, tenant_key)` (`domain/engines/companion_planting_engine.py:20`) judges one species against all neighbours of a slot, with one repository read per neighbour slot and per species (N+1). Called per edge for 500 edges this does not scale.
- "Same expression" therefore means: extract the per-pair decision (incompatible set wins, else compatible with score, else unknown) into one pure function that `check_compatibility` and the new overlay service both call, and prove it with one test that asserts equality on the same pair. Not a second rule.
- `adjacent_to` (`data_access/arango/collections.py:456`) links slots; `get_adjacent_slots` (`graph_repository.py:232`) is per slot.

## Plan approval

**Authorised by:** `2026-11-04-companion-layer/plan-approval` — approved by the coordinator under the operator's standing authorisation for wave 8 (2026-11-04, decision 3: plan gates without an open decision).

**Group requirement artifact:** not applicable — not a class cluster.

## Completeness matrix

| Member | Backend | Frontend | Tests & guards | Docs & i18n |
|---|---|---|---|---|
| #2658 | `domain/services/companion_overlay_service.py` (new, `*, tenant_key: str`, ownership via `location_ownership`), shared pair rule extracted from the engine, route `GET /locations/{key}/companion-edges` in `api/v1/locations/`, cap 500 + `truncated`; check: unit + API tests | not applicable — API only | equality test engine vs overlay on the same pair; 404 foreign bed; viewer read; cap; tenant-isolation route walk, route-consumer pin, bounded-list guard, write-gate ceiling unchanged; check: `tests/api` + all guards | API reference DE/EN |
| #2659 | not applicable — consumes #2658 | `renderer/CompanionOverlay.tsx` (new, lazy if it adds weight), layer "Mischkultur" in `editor/useLayerPrefs.ts`, `SvgPlanRenderer.tsx`; line style + colour per status; hover/tap reason and score; legend; culling <= 500 per viewport, LOD threshold | vitest culling limit, greyscale distinguishability, axe; GP-ACC-033 benchmark stays green; bundle budget not raised | i18n DE/EN; user guide DE/EN (garden plan layers) |

## Risks

- N+1 reads if the overlay calls the engine per edge — mitigated by the extracted pure rule plus batched reads.
- Renderer performance (GP-ACC-033) with 500 lines; culling must happen before render.
- Species names in reasons are tenant-scoped reads (#927): the overlay must use the tenant-scoped repository reads.

## Open questions for the operator

- none

## Member results

| Member | Specialist | Check | Actual output |
|---|---|---|---|
| #2658 | pending | pending | pending |
| #2659 | pending | pending | pending |

## Deviations

| Member | Kind | What changed |
|---|---|---|
| — | — | none yet |
