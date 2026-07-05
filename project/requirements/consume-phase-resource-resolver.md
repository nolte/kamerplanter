# Requirements — Consume the phase resource resolver (E7/E8) — Issue #383

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back or
an authoritative user answer.
-->

## Bounded context

- **What:** Wire the already-implemented but **inert** `phase_resource_resolver`
  (`resolve_irrigation`, `resolve_nutrient`, `ph_micronutrient_availability`;
  REQ-003 §E7/E8) into the production watering and nutrient service paths so its
  phase-regime logic (flush = water-only/0:0:0, rest = no feed + reduced water,
  `dry_storage`/dormancy = volume 0, `waterlogging_tolerance` cap, E8 `target_ph`
  + pH-gated micronutrient availability) actually influences recommendations and
  becomes visible in the API and the plant-detail view. The resolver is made the
  **authoritative phase-modulation layer**, consolidating the two existing
  overlapping per-phase tables (`WateringVolumeEngine._PHASE_FACTOR`,
  `ResourceProfileGenerator._DEFAULT_PROFILES`) instead of adding a third truth.
- **For whom:** Kamerplanter growers/users who receive watering-volume and
  nutrient-dosing recommendations and read per-phase guidance on the plant-detail
  view; the watering (REQ-004) and nutrient/dosing (REQ-004) subsystems as the
  consuming layers.
- **Override precedence (confirmed):** live soil-moisture **sensor** override
  (REQ-005) > static phase/species defaults > `waterlogging_tolerance` cap. An
  **ET override hook** (REQ-037) is prepared as a documented seam only
  (override param defaults to `None`/fallback); no ET value is computed here.
- **Out of scope (explicit, confirmed via teach-back):**
  - **REQ-037 full evapotranspiration** — `aquacropeto` dependency,
    `EvapotranspirationCalculator`, `irrigation_demands` collection + migration,
    `GrowthPhase.crop_coefficient_kc` + Kc cascade, the `compute_irrigation_demand`
    Celery beat task, CareReminderEngine integration, and the ET frontend widget.
    Deferred to a dedicated REQ-037 follow-up issue.
  - **REQ-005 weather ingestion** — `weather_forecasts` collection, the
    `fetch_weather_forecasts` task, and any weather adapter (Open-Meteo/DWD/OWM).
    None of it exists in code; deferred to a REQ-005 follow-up issue. (The ET
    hook is REQ-037's precondition, so both defer together.)
- **Source of truth:** `spec/req/REQ-003_Phasensteuerung.md` §E7/E8;
  `spec/req/REQ-004_*`, `spec/req/REQ-005_Hybrid-Sensorik.md`,
  `spec/req/REQ-037_Evapotranspiration-Bewaesserung.md` (deferred);
  `spec/style-guides/BACKEND.md` (5-layer); Issue
  [#383](https://github.com/nolte/kamerplanter/issues/383).

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`,
  question budget = 6 (2 batched interview rounds used).
- `U_gate = min_d c_d` over required dimensions = **0.7**
- Termination: **saturation on all load-bearing dimensions** (scope, functional,
  constraints, acceptance criteria all confirmed via teach-back); the two
  below-`τ_high` dimensions (`actors`, `edge_cases`) are low-stakes and resolved
  by documented engineering-default assumptions, so no positive-EVPI question
  remains under the user's explicit "work autonomously to PR" directive.

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.88 | specification | Teach-back Q1–Q4 + scope teach-back: consume resolver in both paths, active sensor override, ET hook, consolidate tables, enrich responses, frontend guidance |
| `non_functional` | yes | 0.82 | interpretation | Confirmed constraints: 5-layer (NFR-001), backward-compat of existing volume/dosing tests, mobile-first + descriptive-text frontend, DE/EN i18n |
| `constraints` | yes | 0.9 | specification | Scope teach-back: "no third truth" (consolidate), ET as hook only, REQ-037/REQ-005 out of scope, source English |
| `domain_objects` | yes | 0.82 | interpretation | Explore map confirmed exact types: `IrrigationRegime`/`NutrientRegime`, `waterlogging_tolerance` (Literal), `nutrient_demand_level` (StrEnum), `VolumeSuggestion`, `DosageCalculationResult`, `SensorReading`/`ObservationService.get_latest_reading` |
| `actors` | yes | 0.72 | interpretation | Issue G2 ("plant detail view") + repo persona; single grower actor assumed, low stakes |
| `acceptance_criteria` | yes | 0.85 | specification | Confirmed regime behaviours (flush→0:0:0, rest→no feed/reduced, dormancy→0 vol, waterlogging-cap, pH>6.5→micro lockout, sensor>default, guidance visible, no silent regression) |
| `edge_cases` | yes | 0.7 | interpretation | Handled by documented defaults (no sensor reading→fallback, unknown phase→base, missing species field→None); listed as residual risks |
| `scope_boundaries` | yes | 0.92 | specification | Explicit scope teach-back after discovering ET + REQ-005 weather are fully greenfield |

## Requirements

<!-- EARS/CNL form, tagged confirmed/assumed, with traceability. -->

- **R1** — WHEN `WateringService.suggest_volume` computes a base volume for a
  plant in a given phase, the watering engine SHALL obtain the phase-modulated
  volume, `water_only` flag, and note from `resolve_irrigation` (fed the computed
  base volume + the species `waterlogging_tolerance`) instead of its own
  `_PHASE_FACTOR` table.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: "Resolver konsolidiert (empfohlen)"
- **R2** — WHEN a live soil-moisture sensor reading is available for the plant's
  location, the watering path SHALL let that sensor override beat the static
  phase/species default, and the `waterlogging_tolerance` cap SHALL be applied
  last (precedence: sensor > default > cap).
  - _dimension_: `functional` · _status_: `confirmed` · _source_: "Sensor aktiv + ET-Hook (empfohlen)"
- **R3** — WHERE no live sensor reading exists, the watering path SHALL fall back
  to the resolver-modulated static default, and SHALL expose a documented ET
  override seam (parameter defaulting to `None`) that is inert in this change.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: scope teach-back
- **R4** — WHEN the nutrient/dosing path computes a per-phase profile/dosage, it
  SHALL consume `resolve_nutrient` + `ph_micronutrient_availability` (fed the
  species `nutrient_demand_level`) so that flush → no feed (0:0:0), rest → no
  feed, and pH > ~6.5 → micronutrient lockout guidance are reflected, replacing
  the standalone `ResourceProfileGenerator._DEFAULT_PROFILES` phase logic.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: "Resolver konsolidiert"; Q3 nutrient hook point
- **R5** — WHEN the profiles/watering/nutrient API responses are produced, they
  SHALL be enriched (additively, backward-compatibly) with the resolver's
  computed guidance fields (`water_only`/feed regime, `note`, `micros_available`,
  `ph_note`) rather than exposing only the raw stored per-phase profiles.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: "Bestehende Responses anreichern (empfohlen)"
- **R6** — WHEN a grower opens the plant-detail view, the frontend SHALL display
  the computed guidance (flush/rest/water-only regime, recommended volume, and a
  pH-availability warning) with descriptive text, mobile-first, DE/EN i18n, and
  the mandatory UI-review → tests → docs agent chain.
  - _dimension_: `functional`/`non_functional` · _status_: `confirmed` · _source_: "Inkl. Frontend"
- **R7** — The resolver SHALL remain a pure domain engine (no I/O), all
  consumption SHALL live in the service layer, and existing watering/dosing
  tests SHALL NOT break silently — any deliberate behaviour change SHALL be
  covered by an updated/added test.
  - _dimension_: `constraints`/`non_functional` · _status_: `confirmed` · _source_: NFR-001 + "Rückwärtskompatibilität" invariant
- **R8** — Service-level tests SHALL prove the resolver output is consumed:
  flush → 0:0:0/water-only, rest → no feed + reduced water, dormancy/dry_storage
  → volume 0, `waterlogging_tolerance` sensitive → volume cap, pH > 6.5 → micro
  lockout, and sensor reading present → overrides static default.
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: Issue "Tests: service-level consumption" + scope teach-back

## Surviving assumptions / open risks

- **A1 (`actors`, c_d 0.72):** Single grower actor; the guidance is read on the
  existing plant-detail view, not a new role-gated surface. _Risk: low._
- **A2 (`edge_cases`, c_d 0.7):** No live sensor reading → fall back to
  resolver-modulated static default (no error). Unknown/unmapped phase name →
  resolver returns the base regime unchanged. Missing `waterlogging_tolerance` /
  `nutrient_demand_level` → treated as `None` (no cap / neutral demand). _These
  are documented engineering defaults, not user decisions._
- **A3 (soil-moisture metric is partly greenfield):** No `soil_moisture`
  `metric_type` and no "latest-reading-by-metric-for-location" query exist yet;
  R2 requires adding the metric string + a plant → location → sensor → latest
  reading resolution helper, reusing `ObservationService.get_latest_reading` and
  the Arango sensor registry. _Risk: medium (buildable, non-trivial); if it
  balloons, R2 may be split to a follow-up while R1/R3–R8 land._
- **A4 (consolidation regression risk):** Replacing `_PHASE_FACTOR` /
  `_DEFAULT_PROFILES` with resolver calls may shift existing volume/dosing test
  expectations; R7 mandates each such shift be deliberate and re-asserted.
- **A5 (ET hook is inert):** REQ-037 full ET and REQ-005 weather ingestion are
  out of scope; the ET seam computes nothing in this change (follow-up issues).
