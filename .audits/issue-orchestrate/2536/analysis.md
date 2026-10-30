# Pre-analysis: #2536 editor comfort follow-ups (transient, removed before merge)

Class: bug (review findings of PR #2532, frontend garden-plan editor, REQ-053 WP 7.10-7.13; some are feature gaps of SHOULD requirements). Source: issue #2536 (8 numbered items). Authorised under operator autonomy 2026-10-09 / 2026-10-30 (partition 2026-10-29 single). Requirements: the issue is the decision record; spec rows GP-FR-154 (snap order: object corner -> object edge -> grid, visible guide + marker, tolerance 10 px mouse / 24 px touch) and GP-FR-155 (undo granularity, undo of an unsaved op removes it).

## Items as the issue states them (line numbers to be re-measured by the specialist)
1. Snap marker shows the pointer point, not the snapped anchor (`editor/GardenPlanEditor.tsx` ~492-503 vs `editor/tools/selectMachine.ts` ~305-311; test 'shows the edge as a guide' in `EditorComfort.test.tsx` ~90-104 codifies it).
2. Anchor-only snap: snap applies to the dragged object's anchor, not to all four bbox corners, so "right edge to left edge" is impossible. Next step: all four bbox corners as sources, smallest distance wins, marker at the snapped source (also fixes 1). `editor/tools/snap.ts`.
3. `distributeSelection` (`editor/align.ts` or wherever it lives, ~138-147): sorts by centre but starts at the smallest `lo`, so a wide object protruding left is moved though the docstring says outermost stay; overlapping boxes give a negative gap and overlap afterwards; a locked object in between is ignored and can be covered.
4. Edits during a save are refused with a notice (`plan.saving`) instead of being queued: needs undo history rebased across the in-flight boundary (a first attempt made deleting a saved entity un-undoable, GP-FR-155). "Revisit if users hit the notice." => NOT in scope: no change, document as operator point.
5. `applyDerived` (`model/planModel.ts` ~161-187) overwrites local geometry derivations (bbox/area) for keys that still have an op in `pending`.
6. Mini-map re-renders on every pointermove (not memoised, up to 500 rects), 1 px offset from the border in `getBoundingClientRect`; no keyboard path (documented => leave).
7. Small: the spacing field always shows 'm' (ignores `useLengthUnit`); `failedCopy` is not displayed; 'place at centre' puts the template anchor, not its centre, in the middle; the ghost does not show whether the placement would be invalid (UX); shared test vectors with the backend for `placeGeometry` (Python is the reference).
8. The PR body of #2532 still describes the state before the review fixes (merged PR: optional `gh pr edit`, low value).

## Design (specialist may refute with evidence)
- D-1 Items 1+2 together: snap sources = all four bbox corners (plus the anchor) of the dragged object against object corners/edges/grid in the GP-FR-154 order, smallest distance wins, the marker/guide is drawn at the snapped source; keep tolerances and the Alt/disable behaviour; pure function in `tools/snap.ts` with unit tests (property: result within tolerance, order corner->edge->grid); update the test that codified the old marker.
- D-2 Item 3: distribute keeps the outermost objects fixed (min lo / max hi by bbox extent, not centre-sorted lo), equal gaps, negative gap => refuse with a notice or distribute by centres (decide, record, test), locked objects keep their position and are treated as obstacles/fixed (never moved, not covered: when impossible say so).
- D-3 Item 5: `applyDerived` skips geometry derivations for keys with a pending op (test).
- D-4 Item 6: memoise the mini-map rect list (`useMemo` on the plan model, not on pointer state), fix the 1 px border offset; keyboard path stays documented-as-missing.
- D-5 Item 7: spacing field uses `useLengthUnit` (convert on display/input, store metres), show `failedCopy` where the copy failure is reported, 'place at centre' centres the template's bbox, ghost invalid-state feedback (red outline, no new copy beyond an aria label) only if small; shared `placeGeometry` vectors: look for the existing shared vector mechanism (`garden-plan-vectors.json` is used for site_fit/phase_color) and add placeGeometry cases evaluated by both the TS function and a Python test if a Python reference exists; else report.
- D-6 Item 4 untouched; item 8 optional.

## Work packages
| id | what | specialist |
|---|---|---|
| P1 | D-1 snap sources + marker + tests | fullstack-developer |
| P2 | D-2 distribute + D-3 applyDerived + tests | fullstack-developer |
| P3 | D-4 mini-map, D-5 small items | fullstack-developer |
Review after: frontend-code-reviewer; frontend-usability-optimizer glance for ghost feedback and the unit field if changed.

## Risks
- Snap is a hot path (drag at 60 fps): no allocation storms, keep O(n) in objects near the pointer; benchmark with the existing garden planner benchmark if one exists (CI job "Garden planner benchmarks").
- Undo granularity must not change (GP-FR-155).
