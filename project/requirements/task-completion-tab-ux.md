# Requirements — Task "Abschließen" (complete) tab: holistic UX rework

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back.
-->

## Bounded context

- **What:** Holistically rework the "ABSCHLIESSEN" (complete) tab of the task
  detail page (`src/frontend/src/pages/aufgaben/TaskDetailPage.tsx`, route
  `/aufgaben/tasks/:key#complete`) for UX. The **ratings** (Schwierigkeit +
  Qualität) are the focal point: today they are bare number inputs
  (`FormNumberField`, 1–5) and should become a proper rating control.
- **For whom:** Users completing a task (entering completion notes, actual
  duration, difficulty/quality ratings, photos).
- **Out of scope:** any backend / data-contract change; the completion
  save/validation behaviour; other tabs of the task detail page; the task list.

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`,
  question budget = ~3 (spec defaults; not overridden — small, clear FE UX task).
- `U_gate = min_d c_d` over required dimensions = **0.80**
- Termination: `saturation` (teach-back confirmed "passt").

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.85 | interpretation | Rating control must still yield 1–5 or null (teach-back) |
| `non_functional` | yes | 0.90 | interpretation | UX rework of whole tab (Q1→b) + a11y/mobile conventions |
| `constraints` | yes | 0.88 | interpretation | FE-only, no backend/contract change (teach-back) |
| `domain_objects` | yes | 0.85 | interpretation | Code grounding: completion fields (`actual_duration_minutes`, `difficulty_rating`, `quality_rating`, notes, photo refs) |
| `actors` | yes | 0.85 | specification | User completing a task |
| `acceptance_criteria` | yes | 0.85 | interpretation | Teach-back on control + preserved contract |
| `edge_cases` | yes | 0.80 | specification | "not rated"/null state, mobile, keyboard a11y |
| `scope_boundaries` | yes | 0.90 | specification | Q1→b (whole tab), FE-only, no functional change |

## Requirements

- **R1** — The "Abschließen" tab SHALL be reworked holistically for UX
  (completion notes, actual duration, ratings, photos) as a coherent, mobile-first
  whole.
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: "bewertungen muss durch einen ux experten überarbeitet werden" + Q1→b (whole tab)

- **R2** — The difficulty and quality ratings SHALL be captured via a proper 1–5
  rating control (e.g. star rating or segmented 1–5 selector) instead of number
  input fields, with a clear "not rated" (null) state.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: screenshot (bare number fields) + teach-back (rating control, "nicht bewertet"-Zustand)

- **R3** — The rework SHALL NOT change the backend/data contract: completion
  still submits `actual_duration_minutes`, `difficulty_rating` (1–5 or null),
  `quality_rating` (1–5 or null), completion notes, and photo refs, with the same
  save/validation behaviour.
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: teach-back ("kein Backend-Change, gleiche Werte")

- **R4** — The rating control SHALL be keyboard-operable and accessible
  (aria-labels), with touch targets ≥48px.
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: project a11y / mobile-first conventions + teach-back

- **R5** — All new/changed user-facing strings SHALL be maintained in i18n with
  DE and EN synchronous.
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: project i18n convention

## Surviving assumptions / open risks

- **A1 (control choice)** — the concrete control (MUI `Rating` stars vs a
  segmented 1–5 selector) is *assumed* to be the UX specialist's call; it must
  keep the null / "not rated" state expressible (the field is nullable).
- **A2 (no functional bug)** — the user reported no functional defect; this is
  *assumed* a pure UX rework. If save/validation issues surface during the work,
  re-scope.

## Sequencing note

FIX-05 edits `TaskDetailPage.tsx` and the shared i18n files — the i18n files are
also touched by FIX-02. Per the shared-tree rule, FIX-05 implementation starts
only **after** FIX-02 has been committed.
