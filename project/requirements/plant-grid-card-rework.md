# Requirements — Dashboard "Plant grid" card: speaking names, location & granular links

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back.
-->

## Bounded context

- **What:** Rework the plant-instance card (`PlantGridCard`) inside the dashboard
  "Plant grid" widget (`src/frontend/src/components/dashboard/widgets/PlantGridWidget.tsx`,
  DASH-2 / issue #488) so a user can tell *which plant* a card represents, see
  its location, and jump to the relevant detail pages.
- **For whom:** Growers scanning their dashboard. Today the card shows a bare
  number (e.g. "7432"), a phase chip and a due date — the species is invisible
  and the whole card is a single link to the plant detail.
- **Out of scope (v1):** the separate list page `/pflanzen/plant-instances`
  (`PlantInstanceListPage`, a candidate FIX-03); pagination; making the due date
  a link.

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`,
  question budget = ~5 (spec defaults; not overridden).
- `U_gate = min_d c_d` over required dimensions = **0.80**
- Termination: `saturation` (`min_d c_d ≥ τ_high`, no positive-EVPI question
  remains). Full teach-back confirmed ("passt").

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.90 | interpretation | Full teach-back confirmed ("passt") |
| `non_functional` | yes | 0.80 | interpretation | Project conventions (mobile-first, i18n DE/EN, useMemo) + no-nested-anchor constraint |
| `constraints` | yes | 0.85 | interpretation | 5-layer, tenant-scoped payload (existing), EN source, HTML/a11y (no nested `<a>`) |
| `domain_objects` | yes | 0.85 | interpretation | Code grounding: `PlantGridEntry`, `PlantInstance.list_active_for_tenant`, `Species.common_names`, `Location`, `PhaseSequenceEntry.phase_definition_key` |
| `actors` | yes | 0.85 | specification | Screenshot + "so weiß keiner um welche pflanze es sich handelt" (grower on dashboard) |
| `acceptance_criteria` | yes | 0.85 | interpretation | Q1 (name model=b), Q2 (link set + phase link), teach-back |
| `edge_cases` | yes | 0.82 | specification | No custom name→common name; no location→hide; phase not resolvable→chip w/o link; compact format |
| `scope_boundaries` | yes | 0.88 | specification | Q3→a (widget only, not list page); date no link; no pagination |

## Requirements

<!-- EARS/CNL form; tagged confirmed/assumed with traceability. -->

- **R1** — The card's primary title SHALL be the plant instance's own
  user-given name when it has one; otherwise it SHALL fall back to the species
  common name (with the cultivar name when present). The bare instance number
  (e.g. "7432") SHALL be shown only as a small secondary reference, never as the
  sole title.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: "hier müssen auch die sprechenden namen angezeigt werden" + Q1→b (user label first, species as subtitle)

- **R2** — The aggregated `plant_grid` payload SHALL be enriched server-side (in
  the same tenant-scoped `list_active_for_tenant` round-trip, no extra fetch /
  no N+1) with the species common name, so the card can render the speaking name.
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: code grounding (payload lacks `species_name` today) + teach-back ("Backend-Anreicherung um den Arten-Namen")

- **R3** — The card SHALL display the plant's location in **both** the detailed
  and the compact card format (today it appears only in the detailed format).
  - _dimension_: `functional` · _status_: `confirmed` · _source_: "auf der karte soll auch der standort vermerkt sein" + teach-back (both formats)

- **R4** — Each piece of information on the card SHALL be its **own** link: the
  title → `/pflanzen/plant-instances/{key}`; the species → `/stammdaten/species/{species_key}`;
  the location → `/standorte/locations/{location_key}`; the phase chip → the
  phase-definition detail page. The due date SHALL NOT be a link.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: "die einzelnen informationen sollen die möglichkeiten haben durch links auf die detail seiten zu wechseln" + Q2 (link set, date not linked)

- **R5** — The `plant_grid` payload SHALL additionally carry the
  `phase_definition_key` (resolved from `current_phase_key` →
  `PhaseSequenceEntry.phase_definition_key`) to target the phase link. WHEN it
  cannot be resolved for an instance, the phase chip SHALL render **without** a
  link and without error (graceful degradation).
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Q2 (phase link wanted) + teach-back (unresolvable → chip without link)

- **R6** — The card SHALL NOT be wrapped in a single card-wide link; the
  granular links SHALL be implemented without nesting anchors (valid HTML,
  accessible focus order).
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: teach-back (no card-wide link; nested anchors forbidden)

- **R7** — The card SHALL be reworked holistically for UX (clear title/subtitle
  hierarchy, chips, visibly distinguishable links, touch targets ≥48px,
  mobile-first, accessibility), consistent across the detailed and compact
  formats.
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: "die karte für eine instanze soll überarbeitet werden" + teach-back (UX by specialist)

- **R8** — All new/changed user-facing strings SHALL be maintained in i18n with
  DE and EN synchronous (DE default).
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: project i18n convention

## Surviving assumptions / open risks

<!-- Every `assumed` entry and every below-`τ_high` cell, named as a risk. -->

- **A1 ("own name" detection)** — the card currently shows "7432", i.e.
  `plant_name` appears to hold the instance number rather than a real label.
  *Assumed:* treat `plant_name` as the user label and fall back to the species
  common name when it is empty **or** equals the numeric id/`instance_id`; the
  exact detection is settled at implementation by inspecting how `plant_name` is
  populated. Residual `edge_cases` risk (`c_d = 0.82`).
- **A2 (common-name localization)** — the species common name is *assumed* to
  come from `Species.common_names` (locale-appropriate / first entry); when none
  exists, fall back to `humanizeSlug(species_key)`.
- **A3 (location link)** — *assumed* target `/standorte/locations/{location_key}`;
  when `location_key` is missing, the location link/row is hidden.
- **A4 (phase link resolution)** — needs the backend `phase_definition_key`
  enrichment (R5). The legacy `GrowthPhase` path may not resolve to a
  `PhaseDefinition`; those chips render without a link (R5), *assumed* acceptable.
- **A5 (compact density)** — showing speaking name + location + granular links in
  the compact format may pressure layout; final presentation is *assumed* owned
  by the UX pass (R7).

## Sequencing note

FIX-02 edits `PlantGridWidget.tsx`, the backend `list_active_for_tenant`
enrichment (in `plant_instance_repository.py`), and the shared i18n files —
files also touched by FIX-01. Per the shared-tree rule, FIX-02 implementation
starts only **after** the FIX-01 chain (impl → UX → tests → docs → commit) has
committed.
