# Group pre-analysis: 2026-10-19-editor-comfort

> Run-scoped artifact. Committed on the integration branch, removed with a fix-forward
> `git rm` before the bundle merges.

## Scope of this analysis

**Research question:** Can #2476-#2479 ship as one strand on the existing editor without a backend change?

**The group's single logical change, in one sentence:** Add the template picker with standard sizes, object snap with align/distribute, mini-map with auto-save, and multi-duplicate to the garden planner editor (REQ-053 wave 7, WP 7.10-7.13).

**Out of scope:** E2E (WP 7.25), any backend semantics, slots in multi-duplicate (no `create_slot`, operator decision #2466 item 8), applying `recurring_task_templates` (item 9).

**Tier:** 2 - one repository, no published contract change (frontend client functions for existing routes only).

## Members

| Issue | Class | Admitting predicate | Evidence |
|---|---|---|---|
| #2476 | feature-request | dependency chain (after WP 7.9 #2475, merged: `place-template` route in `src/backend/app/api/v1/garden_plan/tenant_router.py:298`) | `GET\|POST /bed-templates` in `api/v1/bed_templates/tenant_router.py` |
| #2477 | feature-request | dependency chain + shared touch surface `EditorToolbar.tsx` | `candidates` seam exists, unused: `editor/tools/snap.ts:35` |
| #2478 | feature-request | dependency chain + shared `GardenPlanEditor.tsx`, `SaveBar.tsx` | none yet: no `MiniMap.tsx`, no auto-save |
| #2479 | feature-request | dependency chain + shared `GardenPlanEditor.tsx` | `editor/tools/duplicate.ts:4`: no `create_slot` |

**Dependency ordering:** #2476 -> #2477 -> #2478 -> #2479.

**Shared touch surface:** `editor/EditorToolbar.tsx`, `editor/GardenPlanEditor.tsx`, `state/gardenPlanSlice.ts`, `i18n/locales/{de,en}/pages.json`.

## Mode decision

**Mode:** A - single strand.

**Reason:** No member has uncertain acceptance or an external dependency; all four touch the same two files.

## Structural finding

**Cluster shape:** class cluster (one defect class: editor comfort features absent from the MVP).

**Root cause or defect class:** MVP deliberately shipped without the SHOULD comfort features.

**Process finding:** none.

**Preventive change:** not applicable.

**Recurrence fed to the portfolio loop:** none.

## Plan approval

**Authorised by:** `2026-10-19-editor-comfort/plan-approval` - granted by the operator in the dispatch brief (group record from issue-backlog-partition G-D).

**Group requirement artifact:** not applicable - REQ-053 v1.6 is the requirement; acceptance is in the issue bodies.

## Completeness matrix

| Member | frontend code | i18n DE/EN | UI-NFR-022 test ids | vitest + axe | docs DE/EN | bundle budget |
|---|---|---|---|---|---|---|
| #2476 | templates/, toolbar, add dialog; check: `npx vitest run src/features/gardenPlanner` | pages.json; check: key-parity script | new table in UI-NFR-022 | EditorComfort.test.tsx | locations-substrates.md | lazy() chunks; `npm run bundle:check` |
| #2477 | snap.ts, planIndex.ts, align.ts, SnapMarker; same | same | same | planIndex.snap.test.ts, align.test.ts | same | `npm run bundle:check` |
| #2478 | MiniMap.tsx, useAutoSave.ts, SaveBar; same | same | same | miniMap.test.ts, EditorComfort | same | `npm run bundle:check` |
| #2479 | duplicate.ts, MultiDuplicateDialog (lazy); same | same | same | duplicate.test.ts | same | lazy() chunk |

Backend, migrations, Pydantic models: not applicable (no change) - so the backend guards and `check_schema_examples.py` do not apply.

## Risks

- `place-template` is a server-side batch; unsaved edits are saved first and the placement is not an undo step (history emptied by a refresh).
- The chunk budget `routeChunks.gardenPlanner` (120 KB) must not be raised.

## Open questions for the operator

- None blocking.
