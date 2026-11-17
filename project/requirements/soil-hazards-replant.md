# Requirements — Soil hazards and the replant hint (#2888)

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/.
Interview conducted 2026-11-17 with the operator (German); artifact in English.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back.
Domain basis: spec/analysis/agrobiology-soil-hazards-research-2888.md (2026-11-15).
-->

## Bounded context

- **What:** the data foundation for soil-borne failure causes, built **independently of the REQ-054 planner** (not implemented yet, which consumes it later): a `failure_cause_class` on a `died` loss, `soil_hazards[]` on beds with an API, promotion of a confirmed soil-borne loss into `soil_hazards[]`, a knowledge table per hazard with evidence status, the replant hint and `crop_rotation_validator` reading `soil_hazards[]`, a definition of "same season", and fresh-substrate handling for pots and hydroponics.
- **For whom:** gardeners with outdoor beds (grower and above); bed soil hazards are created from grower upward and deleted by leads (REQ-054 AP-API-012).
- **Out of scope:** the REQ-054 planner itself (H-10/H-11 as planner rules); notifiable quarantine pests; new research inside this implementation step (it runs as its own parallel work step, R10).
- _source_: Q1 "passt".

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question budget = `8` (4 used)
- `U_gate = min_d c_d` over required dimensions = **0.8**
- Termination: `saturation` (final teach-back Q4 confirmed)

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.85 | specification (resolved) | Q3 package, Q4 teach-back |
| `non_functional` | yes | 0.8 | specification | E-10 handling Q2 "b" |
| `constraints` | yes | 0.85 | specification (resolved) | Q2 (E-10), never a hard block (issue + Q4) |
| `domain_objects` | yes | 0.85 | interpretation | research §5/§6 adopted (Q3 "ok") |
| `actors` | yes | 0.85 | specification | Q1, AP-API-012 |
| `acceptance_criteria` | yes | 0.8 | specification | issue AC (spec before code), Q4 |
| `edge_cases` | yes | 0.8 | specification | legacy data, hydroponics, perennials, unconfirmed cause (Q3) |
| `scope_boundaries` | yes | 0.9 | specification (resolved) | Q1 |

Self-consistency (k=2) diverged on scope (now vs. with the planner → Q1) and on the evidence rule (research first / evidenced values only / provisional values → Q2).

## Requirements

- **R1** — WHEN a plant ends with `termination_type = died`, the system SHALL record a `failure_cause_class ∈ {abiotic, pest_foliar, pest_soil, disease_soil, disease_foliar, mechanical, unknown}`, pre-filled from `termination_cause` per research §5; for `pest` and `disease` the user SHALL choose the class; a wilt follow-up question SHALL be offered for `heat`, `drought`, `waterlogging`, and for `unknown` on wilt-prone families. Plants without a class SHALL behave as today (REQ-053 v1.37).
  - _dimension_: `functional`, `edge_cases` · _status_: `confirmed` · _source_: Q3 point 5 "ok", Q4 "passt"
- **R2** — `termination_cause` SHALL gain `bolting`, classified `abiotic`.
  - _dimension_: `domain_objects` · _status_: `confirmed` · _source_: Q3 point 6
- **R3** — A bed SHALL carry `soil_hazards[] {hazard, affected hosts, confirmed_at, source}`, maintained via API (create from grower, delete lead only).
  - _dimension_: `domain_objects`, `actors` · _status_: `confirmed` · _source_: Q1, Q4 point 2
- **R4** — WHEN a loss is `disease_soil` with a named pathogen from the hazard list and confirmed, the system SHALL **offer** to add it to the bed's `soil_hazards[]`; an unconfirmed soil-borne loss SHALL never create an entry.
  - _dimension_: `functional`, `edge_cases` · _status_: `confirmed` · _source_: Q3 point 5, Q4 point 2
- **R5** — A knowledge table SHALL hold per hazard `soil_persistence_years`, `max_survival_years` and hosts at the finest available level (`families[]`, `genera[]`, `species_keys[]`), **each value with its evidence status**; only values at 3/3 SHALL drive the warning duration; supplementary research SHALL be added as data without code change.
  - _dimension_: `domain_objects`, `constraints` · _status_: `confirmed` · _source_: Q2 "b", Q3 points 1+3
- **R6** — WHEN a planting in a bed matches a host of a hazard in `soil_hazards[]`, the replant hint and `crop_rotation_validator` SHALL show an overridable WARNING ("plant anyway" with a reason) until `confirmed_at + soil_persistence_years`, then an INFO until `confirmed_at + max_survival_years`; a hazard without an evidenced duration SHALL show a WARNING without a time statement ("soil-borne pathogen confirmed, rotation break unknown"). The check SHALL never be a hard block.
  - _dimension_: `functional`, `constraints` · _status_: `confirmed` · _source_: Q2, Q3 point 1, Q4 point 4
- **R7** — `root_knot_nematode` and `sclerotinia` SHALL only ever produce an INFO.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Q3 point 2
- **R8** — "Same season" for the replant exception SHALL mean a replant date within the cultivation window of the replaced plant (`planted_on` … expected end), not the calendar year; for perennials only the failure year counts.
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: Q3 point 4
- **R9** — A pot with fresh substrate SHALL not raise soil warnings; in hydroponics a soil-borne loss SHALL create no `soil_hazards[]` entry but the hint "clean and disinfect the system before replanting".
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: Q3 point 7
- **R10** — The values listed in research §6.3 SHALL be researched further (three independent sources per value, preferably German state sources: LWK, LTZ, JKI) as a parallel work step; results are entered as data.
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: Q2 "b", Q4 point 7
- **R11** — REQ-053 §11.3 (cause class, `bolting`, season) and REQ-054 §5.2/§6 H-10 (two time fields, soft hazards, host levels) SHALL be updated **before code**.
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: issue acceptance, Q4 point 8

- **R12** — The hazard knowledge table SHALL be keyed by the eight REQ-054 hazards (no *Fusarium* formae speciales for now) and live as seed YAML next to `ipm.yaml`; a bed's `soil_hazards[]` entry SHALL reference the hazard key and resolve its hosts from the table at check time.
  - _dimension_: `domain_objects` · _status_: `confirmed` · _source_: revisit 2026-11-17 decisions 1+2 "ja"
- **R13** — The termination dialog SHALL capture pathogen, `confirmed` and `source` for a soil-borne loss (F-19); bulk "clear bed" stays unclassified; a plant in a premature bolting phase (REQ-003 E6) SHALL pre-fill `bolting`, and `bolting` SHALL join `ABIOTIC_TERMINATION_CAUSES`.
  - _dimension_: `functional`, `edge_cases` · _status_: `confirmed` · _source_: revisit decisions 3–5
- **R14** — The hazard check SHALL also run on beds with `rotation_exempt` or disabled rotation; planter/tent/shelf carry no soil hazard.
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: revisit decision 6
- **R15** — The cultivation window's expected end SHALL be `planted_on + days_to_maturity` of the species, falling back to the calendar-year rule when missing.
  - _dimension_: `domain_objects` · _status_: `confirmed` · _source_: revisit decision 7
- **R16** — The bed soil profile SHALL gain `substrate_replaced_on`; a planting after it raises no soil warning; hydroponics is recognised by `Location.irrigation_system ∈ {HYDRO, NFT, EBB_FLOW}`.
  - _dimension_: `domain_objects`, `edge_cases` · _status_: `confirmed` · _source_: revisit decision 8
- **R17** — WHEN only `max_survival_years` is evidenced, the system SHALL warn without a time statement until it ends, then nothing.
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: revisit decision 9
- **R18** — The replant hint SHALL follow the cause class (research §5): `pest_foliar` none, `disease_foliar` INFO "remove residues, do not compost", unconfirmed `disease_soil` WARNING.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: revisit decision 10
- **R19** — `soil_hazards` SHALL be part of the garden-plan export/import and the tenant export.
  - _dimension_: `scope_boundaries` · _status_: `confirmed` · _source_: revisit decision 11
- **R20** — The spec update (R11) SHALL also cover REQ-003 E5 (`termination_cause` enum), REQ-054 AP-ACC-022 and TC-REQ-054.
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: revisit decision 12

## Surviving assumptions / open risks

- **Revisit 2026-11-17:** the consistency check of F-18..F-21 found twelve open points (storage and keying, host reference, ownership of the pathogen capture, bulk clear, bolting prefill, gate bypass, window end, fresh substrate, partial evidence, class-based hint, export, spec scope); the operator accepted all recommendations (R12–R20).

- **Evidence gaps:** with today's research most hazards have no 3/3 block duration (research §6.1), so most warnings start without a time statement until R10 delivers.
- **Planner consumption:** the REQ-054 planner (H-10/H-11) will read the same `soil_hazards[]` and knowledge table; its hard-block semantics there differ from the replant hint's warning-only semantics — to be reconciled when the planner is built. `assumed`.
- **Phaseolus in the pea complex** and other open host questions (research R-002 open points) stay unresolved data gaps.
