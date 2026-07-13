# Requirements — Phase-definition detail page: plant-instances & species lists

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back.
-->

## Bounded context

- **What:** Extend the existing phase-definition detail page
  (`PhaseDefinitionDetailPage`, route `/phasen/definitionen/:key`) with two new
  sections and give the whole page a holistic UX rework.
  - **List 1** — plant instances of the current tenant that are *currently* in
    this phase (active instances only).
  - **List 2** — all species (global catalog) that traverse this phase
    definition.
  - Both lists' rows link to the corresponding detail page.
- **For whom:** Growers working inside their own tenant. The page serves a
  **dual purpose**: operational ("which of my plants are in this phase right
  now, so I can care for them") *and* reference ("which species go through this
  phase").
- **Out of scope (v1):** pagination of the lists; creating/editing plant
  instances or species from within the lists; any cross-tenant view.

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`,
  question budget = ~6 (spec defaults; not overridden).
- `U_gate = min_d c_d` over required dimensions = **0.80**
- Termination: `saturation` (`min_d c_d ≥ τ_high` and no positive-EVPI question
  remains after Q5). Full teach-back confirmed ("passt so!"); list-1 active
  filter confirmed (Q5 → a).

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.92 | interpretation | Full teach-back confirmed ("passt so!") |
| `non_functional` | yes | 0.80 | interpretation | UX-rework scope (Q3→a) + project conventions (mobile-first, i18n DE/EN, read-only) |
| `constraints` | yes | 0.85 | interpretation | CLAUDE.md/plan invariants (5-layer, SEC-001 tenant filter, EN source) + tenant-scoping confirmed (Q2→c) |
| `domain_objects` | yes | 0.85 | interpretation | Code grounding (Explore) + teach-back on the `current_phase_key`→`PhaseSequenceEntry`→`phase_definition_key` indirection |
| `actors` | yes | 0.88 | specification | Q2→c (grower, own tenant, dual purpose) + teach-back |
| `acceptance_criteria` | yes | 0.88 | interpretation | Q4 (row fields) + teach-back on both lists' fields & empty states |
| `edge_cases` | yes | 0.82 | specification | Empty states (teach-back), no pagination (Q4→simple list), active-only (Q5→a) |
| `scope_boundaries` | yes | 0.88 | specification | Q3→a (full-page UX) + teach-back out-of-scope list |

## Requirements

<!-- EARS/CNL form; tagged confirmed/assumed with traceability. -->

- **R1** — WHEN a user opens the phase-definition detail page for a phase
  definition `key`, the system SHALL display a "plant instances currently in
  this phase" section listing the **active** plant instances of the user's
  current tenant whose resolved current phase maps to that phase definition.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: "es sollen dort Pflanzen instanzen angezeigt werden welche aktuell in dieser phase sind" + Q5→a (active only)

- **R2** — Each List-1 row SHALL show the plant-instance label, its species, its
  location/slot, the phase start date (`current_phase_started_at`), and the
  elapsed days-in-phase; and each row SHALL link to
  `/pflanzen/plant-instances/{key}`.
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: Q4 defaults + "die dauer ist sicher noch hilfreich" (teach-back: days-in-phase on List 1)

- **R3** — List 1 SHALL be a simple (non-paginated) list and SHALL show a total
  count of the plant instances it contains.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: "am anfang reicht sicher eine einfache liste" (Q4)

- **R4** — WHEN the tenant has no active plant instances in that phase, the
  system SHALL render a friendly empty-state message instead of an empty list.
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: teach-back ("Leerer Zustand: … aktuell keine Pflanzen in dieser Phase")

- **R5** — WHEN a user opens the phase-definition detail page, the system SHALL
  display a second section listing all species (global catalog) that traverse
  this phase definition (resolved via
  `PhaseDefinition` → sequences → `PhaseSequenceEntry` → species).
  - _dimension_: `functional` · _status_: `confirmed` · _source_: "eine zweite anzeige soll dem nutzer alle arten listen welche diese phase allgemein durchlaufen"

- **R6** — Each List-2 row SHALL show the scientific name, the common name, and
  the phase's typical duration (optionally an illustration/icon); and each row
  SHALL link to `/stammdaten/species/{key}`.
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: Q4 defaults + "die dauer ist sicher noch hilfreich" (teach-back: typical duration on List 2)

- **R7** — WHEN no species are associated with the phase definition, the system
  SHALL render an empty-state message.
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: teach-back ("Leerer Zustand: keine Arten hinterlegt")

- **R8** — The system SHALL expose the List-1 data via a new **tenant-scoped**,
  read-only backend endpoint that filters by `tenant_key` and rejects an empty
  `tenant_key` (SEC-001), reusing the 5-layer path (API → Service → Repository).
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: SEC-001 invariant + Q2→c (tenant scoping) + code grounding (no such endpoint exists today)

- **R9** — The system SHALL expose the List-2 data via a new global read-only
  endpoint `/phase-definitions/{key}/species`, composed from existing repository
  building blocks (`get_sequences_for_definition` + `get_species_for_sequence`).
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: code grounding + teach-back ("dünner globaler Endpoint")

- **R10** — The entire phase-definition detail page (existing content plus both
  new sections) SHALL be reworked holistically for UX, remaining mobile-first
  and i18n-complete (DE + EN synchronous).
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: "die ganze anzeige soll von einem UX Experte überarbeitet werden" + Q3→a (whole page)

## Surviving assumptions / open risks

<!-- Every `assumed` entry and every below-`τ_high` cell, named as a risk. -->

- **A1 (legacy phase path)** — `PlantInstance.current_phase_key` may point at a
  legacy `GrowthPhase` (LifecycleConfig model) instead of a `PhaseSequenceEntry`.
  *Assumed:* the List-1 query resolves **both** paths where data exists; the
  exact reach is settled at implementation by inspecting real data. Residual
  `edge_cases` risk (`c_d = 0.82`). Implementation-level, low user-EVPI.
- **A2 ("active" definition)** — "active plant instance" is *assumed* to mean
  not archived / not completed / not harvested; the exact `PlantInstance` status
  values to include/exclude are confirmed against the status enum at
  implementation.
- **A3 (illustration in List 2)** — the illustration/icon per species row is
  *assumed* nice-to-have, not blocking; the UX pass decides final presentation.
- **A4 (performance)** — a simple, unpaginated List 1 is *assumed* acceptable
  for typical tenant plant counts; revisit if a tenant has very many instances
  in one phase (deferred with pagination, out of scope v1).
- **A5 (non_functional at τ_high)** — mobile-first + DE/EN i18n are firm project
  conventions and will be applied; residual uncertainty is only the final UX
  layout, owned by the usability pass.
```
