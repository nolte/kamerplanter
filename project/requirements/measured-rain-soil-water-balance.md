# Requirements — Measured site rainfall and a multi-day soil water balance (#3002)

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/.
Interview conducted 2026-11-17 with the operator (German); artifact in English.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back.
-->

## Bounded context

- **What:** a rain gauge (Netatmo, read through Home Assistant) bound to an outdoor/greenhouse site feeds measured daily rainfall into the irrigation demand; the demand becomes a multi-day soil water balance (FAO-56 style); a watering reminder is deferred while the balance shows no demand.
- **Why:** avoid unnecessary watering when the forecast reported no rain but the gauge measured it (Q1).
- **For whom:** growers with outdoor/greenhouse sites (they see the balance and the deferred reminder); members with the `technical` admin scope bind the sensor (CLAUDE.md §7, REQ-005 §4c, #2112).
- **Today:** `src/backend/app/tasks/irrigation_tasks.py:145` computes a single-day balance from `forecast.precipitation_mm` with a FAO rule of thumb and no carry-over (`water_holding_capacity_mm=None`); no sensor metric for precipitation exists; `care_event(rainfall)` records a skipped round without a quantity (`domain/models/irrigation_zone.py:270`).
- **Out of scope:** indoor sites; a direct Netatmo cloud integration; more than one rain gauge per site or per-bed gauges; actuator irrigation (REQ-018); researching the soil-texture water-holding values themselves (R-008, rule E-10).
- _source_: Q1, Q2, Q7 teach-back "ja".

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question budget = `8` (7 used)
- `U_gate = min_d c_d` over required dimensions = **0.8**
- Termination: `saturation` (final teach-back Q7 confirmed)

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.85 | specification (resolved) | Q3 "c" multi-day balance, Q5 "B" defer reminder, Q7 |
| `non_functional` | yes | 0.8 | specification | Q6 freshness 6 h, provenance per day |
| `constraints` | yes | 0.85 | specification (resolved) | HA single-instance + entity grants (CLAUDE.md §7); R-008/E-10 gate on soil values |
| `domain_objects` | yes | 0.8 | interpretation | Q4 "C" storage source chain; site-level rain sensor (Q6b) |
| `actors` | yes | 0.85 | interpretation | Q6b `technical` scope binds; grower sees deferral |
| `acceptance_criteria` | yes | 0.8 | specification | issue AC + Q7 teach-back |
| `edge_cases` | yes | 0.8 | specification | Q6 stale/missing data, implausible zero |
| `scope_boundaries` | yes | 0.9 | specification (resolved) | Q7 out-of-scope list confirmed |

Self-consistency (k=2) diverged on the time window (last 24 h vs. since last watering vs. soil bucket → Q3), on where storage capacity comes from (→ Q4) and on what "no demand" does to a reminder (show / defer / complete → Q5); each resolved by a decision answer. "möglich" in Q1 was read as "nötig" and confirmed in Q2.

## Requirements

- **R1** — An outdoor or greenhouse site SHALL accept one optional rain sensor: a Home Assistant entity the tenant has been granted (`tenant_ha_entity_grants`), bound through the existing REQ-046 mode-B precipitation mapping; it applies to every bed of the site. _Amended 2026-11-17 (D1): binding keeps today's LEAD gate (REQ-049 §2.10); the `technical` scope gates the entity listings only._
  - _dimension_: `functional`, `actors`, `constraints` · _status_: `confirmed` · _source_: Q2 "über HA", Q6b "ja das passt"
- **R2** — The system SHALL store the gauge's daily rainfall sum per site and day as an `observed` record **beside** the public forecast (REQ-046 extended; today one source per run displaces the forecast). _Amended 2026-11-17 (D1)._
  - _dimension_: `functional`, `non_functional` · _status_: `confirmed` · _source_: Q6b
- **R3** — The irrigation demand SHALL be a multi-day soil water balance (FAO-56 style): rainfall fills the root-zone store up to its capacity, the excess is lost, ETc depletes it; this replaces the current FAO rule-of-thumb reduction of precipitation.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Q3 "c", Q7 "ja"
- **R4** — The store capacity SHALL come, in this order, from substrate × volume for planters/raised beds/tents (REQ-037 §3.3, REQ-053 GP-FR-113), from the bed's `soil_texture` where a value is sourced (R-008, E-10), else from a lead-set default per site; WHEN none exists, the demand SHALL fall back to the single-day balance with the FAO rule of thumb and the measured rainfall of the last 24 hours. _Amended 2026-11-17 (D6)._
  - _dimension_: `domain_objects`, `constraints` · _status_: `confirmed` · _source_: Q4 "C"
- **R5** — For the current day the balance SHALL use a measured value at most 6 hours old, for completed days the day's last measured value, else the forecast; the provenance (measured / forecast) SHALL be shown per day. _Amended 2026-11-17 (D2): a per-day 6-h rule would drop yesterday's total the next morning._
  - _dimension_: `edge_cases`, `non_functional` · _status_: `confirmed` · _source_: Q6 "passt"
- **R6** — WHEN the balance shows no demand for a due watering reminder and a fresh measured value covers the period, the system SHALL defer the reminder to the first day with demand, annotated with amount and source (e.g. "deferred: 12 mm rain, Netatmo"); the user SHALL be able to restore it.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Q5 "B"
- **R7** — WHEN no fresh measured value exists, the system SHALL NOT defer a reminder because of measured rain; the forecast-based deferral of REQ-005 G-010 stays unchanged. _Amended 2026-11-17 (D3)._
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: Q6
- **R8** — WHEN measured and forecast rainfall diverge strongly (e.g. 0 mm measured vs. 20 mm forecast), the system SHALL show a hint and SHALL NOT correct either value automatically.
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: Q6
- **R9** — Before implementation, the soil water balance model and its parameters SHALL be reviewed by `agrobiology-requirements-reviewer`; REQ-037 (§3.1/§3.3 water balance, §3.4 deferral, §7 acceptance criteria) and REQ-005 (precipitation as sensor metric) SHALL be updated.
  - _dimension_: `acceptance_criteria`, `constraints` · _status_: `confirmed` · _source_: Q7 "ja", issue AC

## Consistency review (2026-11-17)

`feature-consistency-reviewer` found the site-level HA precipitation binding (REQ-046 mode B), an inert watering suppression (`care_reminder_engine.py:656`), the missing water-balance widget, and a conflict with REQ-005 G-010. Operator decisions D1–D6 (2026-11-17) amended R1, R2, R4, R5, R7 and added F-31; details in the feature files F-28..F-31.

## Assumptions and open risks

- **A1** (`assumed`) — The Netatmo integration in Home Assistant exposes a daily cumulative rain sensor (e.g. "Regen heute"); a gauge that only exposes hourly or instantaneous values needs a summation rule. Check before F-design.
- **A2** (`assumed`) — The deferral reuses the existing care-reminder scheduling (REQ-022) rather than a new reminder kind; ADR-008 / #1061 (one recurrence engine) is on hold and is not a precondition.
- **A3** (`assumed`) — The 6-hour freshness limit is a fixed value, not configurable.
- **Risk** — Until R-008 sources soil-texture values, the bucket only works with an operator default; without one, the feature degrades to R4's single-day fallback (still useful for the Q1 case).
- **Risk** — The demand is computed per run while the gauge is per site; a site with mixed beds shares one rainfall series (accepted in Q6b).
