# Pre-analysis: #2514 wave 3 follow-ups (transient, removed before merge)

Class: bug (primary; items are decided spec/test-case deviations). Source: issue #2514 = operator decision 2026-10-19 on #2498 items 1-3.
Authorised under operator autonomy 2026-10-09 / 2026-10-30 (partition 2026-10-29 single). Requirements: the issue body is the decision record (U_gate override).

## Established (read at develop 7e1904d6b)
- Item 1: `spec/e2e-testcases/TC-REQ-053.md` l.524: precondition "Beet mit Geometrie (z. B. 3,0 × 1,2 m)" of TC-053-015 (l.517). Decision: 3,0 × 1,6 m, the default edge margin stays. Corpus-grep needed for the same bed size in the E2E test (`tests/e2e/test_req053_*`), `GP-ACC-019`, docs.
- Item 2: `src/frontend/src/features/gardenPlanner/planting/PositionCorrectionDialog.tsx` l.33-35: `STEP_CM = 1`, `BIG_STEP_CM = 5`; `stepCm` prop (l.47) is passed 10 by field mode (`FieldBedSheet`), big-step buttons (l.54, 231-244) hidden there. Spec REQ-053 l.982 (§18.1 step 9): "Stepper als Standard (±10 cm, ...)" . Decision: spec wins, 10 cm is the step; 1 and 5 cm stay as fine steps.
- Item 3: backend `planting_reservation_service.py` l.109/621 stores the English summary `"Position corrected ({slot_id})"` (comment: "the UI renders the localised text from category"); `history/historyFormat.ts::itemHeadline` returns `item.care_event?.summary` raw for every care event, so the history line shows English text with the slot id. i18n has `pages.bed.history.category.position_corrected` (en l.6919, de l.6920). `CareEventLine.plant_keys` exists; `HistoryItem.plant_name` is null for care events (`careLineToItem` sets null).

## Design
- D-1 Test case: bed 3,0 × 1,6 m in TC-053-015 (and every copy of that example found by grep).
- D-2 Stepper: `STEP_CM = 10` default; fine steps 1 cm and 5 cm remain reachable (the specialist designs the placement: e.g. a fine-step row next to the 10 cm arrows; field mode unchanged: 10 cm, no fine row). Update component tests, i18n labels, docs/user guide if they state the step, E2E page object / TC steps that assume 1 cm.
- D-3 History line: for `category === "position_corrected"` render a localised line with the plant name instead of the server summary and the slot id (`pages.bed.history.event.positionCorrected` DE/EN, e.g. "Position korrigiert: {{name}}"). Plant name source: resolve it from data the list already has; if the history response lacks names for care events, extend the response additively (backend `BedHistoryItemResponse` / care-event line) rather than N extra requests — specialist to measure and decide, record it. Fallback without a name: the localised line without it. The server summary text stays (audit/export), only the client rendering changes.

## Work packages
| id | what | specialist |
|---|---|---|
| P1 | test-case example (D-1) | fullstack-developer |
| P2 | stepper 10 cm + fine steps (D-2) | fullstack-developer |
| P3 | localised history line with plant name (D-3) | fullstack-developer |
Reviews after: frontend-code-reviewer (+ usability pass for the stepper layout, mobile-first, 44 px targets).

## Risks / operator points
- Fine-step UI is a design choice inside the decision ("keep 1 / 5 cm as fine steps"); report the chosen layout.
- If D-3 needs a response field, it is additive on a read DTO.
