# Requirements — Species list origin provenance filter (Issue #397)

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/ (methodology spec shipped in claude-shared).
Do not record a requirement before declaring the bounded context below.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back.
-->

## Bounded context

- **What:** Add a provenance (`origin`) filter control to the species list at
  `src/frontend/src/pages/stammdaten/SpeciesListPage.tsx`. The list already
  *displays* an `OriginChip` per row (`system` / `enrichment` / `import` /
  `tenant`) but offers no way to filter by origin. This closes that gap per
  UI-NFR-018 R-016/R-017/R-018.
- **For whom:** Users of the species list across all experience levels who need
  to narrow a mixed system/tenant/enriched/imported catalog to a chosen subset
  (e.g. "only my data", "only enriched").
- **Out of scope:** Backend/API changes (the `origin` field is already present on
  the read model and resolved client-side via `resolveOrigin`); any list other
  than the species list (cultivars, diseases, treatments, nutrient plans,
  workflow templates); new i18n keys (the `common.origin.*` labels already exist);
  changing `OriginChip` rendering semantics.

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question budget = `3`
  <!-- spec defaults; unchanged. One high-EVPI decision question was spent (select
       semantics); the remaining dimensions were authoritatively fixed by
       UI-NFR-018 R-016/017/018 + UI-NFR-010 + the existing frontend infrastructure. -->
- `U_gate = min_d c_d` over required dimensions = **0.85**
- Termination: `saturation` (`min_d c_d ≥ τ_high` and no positive-EVPI question remained)

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.9 | specification | Operator answer "Multi-Select Chips (OR)" + teach-back confirmed; UI-NFR-018 R-016/017/018 |
| `non_functional` | yes | 0.85 | interpretation | UI-NFR-010 R-016/017 (URL query params), R-041 (chip filter), R-031 (empty-result hint); OriginChip colour/label reuse |
| `constraints` | yes | 0.9 | interpretation | Code read: existing `ToggleFilter` set + `filterChips` + `resolveOrigin`; MUI 7; existing `common.origin.*` i18n keys |
| `domain_objects` | yes | 0.95 | interpretation | `DataOrigin` union (`system`/`enrichment`/`import`/`tenant`) in `@/api/types`; `OriginChip.tsx` |
| `actors` | yes | 0.9 | interpretation | Issue scope: species-list users; no role-specific behaviour |
| `acceptance_criteria` | yes | 0.85 | specification | Derived from R-016/017/018 + UI-NFR-010 R-010/R-031; teach-back confirmed |
| `edge_cases` | yes | 0.8 | interpretation | `tenant` renders no chip but IS a filter option ("Eigene"/"Custom"); empty result; AND-composition with other filters |
| `scope_boundaries` | yes | 0.9 | specification | Issue explicitly scopes `SpeciesListPage.tsx`; frontend-only |

## Requirements

<!-- EARS/CNL form, tagged confirmed/assumed, traced to the utterance/source. -->

- **R1** — WHEN the species list is displayed, the frontend SHALL offer an
  "Herkunft" (origin) filter control presenting the four origin options
  System / Angereichert / Importiert / Eigene (`system` / `enrichment` /
  `import` / `tenant`).
  - _dimension_: `functional` · _status_: `confirmed` · _source_: UI-NFR-018 R-016/R-017 + operator confirmation
- **R2** — The origin filter SHALL be a **multi-select chip filter**: multiple
  origins can be active simultaneously and are combined with **OR** (a row
  matches when its resolved origin is one of the selected origins), consistent
  with the existing `ToggleFilter` chip pattern.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: operator answer "Multi-Select Chips (OR)" + teach-back
- **R3** — WHEN no origin chip is selected, the list SHALL show all rows
  (default "Alle", no origin filter active).
  - _dimension_: `functional` · _status_: `confirmed` · _source_: UI-NFR-018 R-018 + teach-back
- **R4** — The origin filter SHALL be **AND-composed** with the other active
  list filters (family, growth habit, toggle filters) — a row must satisfy the
  origin filter *and* every other active filter.
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: teach-back; consistency with existing `filteredItems` composition
- **R5** — The filter option labels and colours SHALL reuse the existing
  `common.origin.*` i18n keys and `OriginChip` colour mapping
  (`system`→info, `enrichment`→secondary, `import`→default; `tenant`→"Custom"/"Eigene").
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: Issue "Keep it consistent with the OriginChip labels/colours"
- **R6** — The active origin-filter state SHALL be reflected in the URL query
  parameters and restored on load, consistent with the family filter's existing
  `searchParams` handling.
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: UI-NFR-010 R-016/R-017/R-018
- **R7** — The origin filter SHALL count toward the active-filter count, be
  cleared by "Alle Filter zurücksetzen", and — WHEN it yields zero rows —
  surface the specific empty-filter hint rather than the generic empty state.
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: UI-NFR-010 R-009/R-010/R-031
- **R8** — The `tenant` ("Eigene"/"Custom") origin SHALL be a selectable filter
  option even though `OriginChip` renders nothing for `tenant` rows; the filter
  must still be able to isolate user-owned data.
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: UI-NFR-018 R-017 (options include "Eigene")

## Surviving assumptions / open risks

- **A1 (assumed):** The species read model exposes `origin` (or `is_system`) on
  every row so `resolveOrigin` classifies all four values; imported/enriched rows
  are assumed already stamped by the enrichment/import paths. Low risk — the
  origin column already renders live.
- **A2 (assumed):** Placement follows the existing collapsible filter panel
  (`filtersOpen`) rather than a new surface; no separate mobile layout beyond the
  panel's existing responsive behaviour. Confirm during implementation review.
- **R-016 note:** UI-NFR-018 R-016 mandates the filter only for tables with
  *mixed* system/tenant data; the species list qualifies. No conditional-hide
  requirement was requested — the filter is always shown.
