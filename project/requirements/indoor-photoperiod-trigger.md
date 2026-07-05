# Requirements — E1 indoor light-schedule photoperiod trigger (REQ-018)

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back.
Issue: #382. Split off from #305 (outdoor path merged in #385).
-->

## Bounded context

- **What:** Make the existing `photoperiod_based` phase-transition trigger fire for **indoor** plants by deriving the effective photoperiod (hours of light per day) from the configured grow-light schedule persisted on the `Location` model (REQ-018 domain data: `light_type`, `lights_on`, `lights_off`, `use_dynamic_sunrise`), mirroring how the outdoor path already derives it from astronomical day length. Both short-day and long-day induction must work from the light schedule.
- **For whom:** Indoor growers (cannabis, controlled-environment horticulture) whose plants transition phase by artificial photoperiod rather than by season. Directly serves the automated `check_auto_transitions` Celery task; no new human-facing UI.
- **Out of scope:**
  - Autoflower cultivars — they carry no `photoperiod_based` rule (they are `time_based`); no code change, only a regression test that they never fire via photoperiod (confirmed by REQ-003 §1a).
  - The REQ-018 actuator control layer (`actuator.py`/`actuator_service.py` raise `NotImplementedError`) — the schedule is read from `Location`, not from the actuator scaffold.
  - The outdoor GPS/sun path — unchanged; the evaluator (`TransitionTriggerEvaluator`) is source-agnostic and untouched.
  - Actuator-side photoperiod *protection* (REQ-018: "Kurztagspflanzen — Photoperiode NICHT verlängern", dark-phase interruption) — that governs light *control*, not the read-only transition trigger.

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question budget = `6` (spec defaults; unchanged — no project override needed for a tightly-scoped follow-up whose design was pre-researched in `.resume/lifecycle-indoor-photoperiod/plan.md`).
- `U_gate = min_d c_d` over required dimensions = **0.85**
- Termination: `saturation` — every required dimension ≥ `τ_high` with teach-back on the two load-bearing decisions; no remaining candidate question has positive net EVPI (the spec confirmed the read model; the two genuine specification-uncertainty decisions are now user-confirmed).

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.90 | interpretation | Code inspection (`transition_trigger_evaluator.py`, `phase_transitions.py`, `site.py`) + REQ-003 v2.10 E1 confirms `photoperiod_based`/`critical_day_length_hours` model + issue #382 scope |
| `non_functional` | yes | 0.85 | interpretation | CLAUDE.md invariants: NFR-001 5-layer (derivation in a domain calculator, not the task), NFR-003 English source, multi-tenant isolation on the location lookup |
| `constraints` | yes | 0.85 | interpretation | Plan-verified: no dependency on REQ-018 actuator scaffold (`NotImplementedError`); no new repository dep (`get_location_by_key` exists); no new Celery wiring |
| `domain_objects` | yes | 0.90 | interpretation | Verified models: `Location.light_type/lights_on/lights_off/use_dynamic_sunrise` (site.py:57-89), `PlantInstance.location_key` (plant_instance.py:15), `TransitionTriggerEvaluator` |
| `actors` | n/a — the only actor is the system `check_auto_transitions` Celery task iterating all tenants; no human interaction | — | — | Plan §"No new Celery beat wiring"; issue #382 |
| `acceptance_criteria` | yes | 0.85 | interpretation | Issue #382 test scope + plan step 4: indoor short-/long-day fire from schedule, dynamic-sunrise falls back to outdoor, autoflower does not fire |
| `edge_cases` | yes | 0.85 | specification | **Teach-back confirmed** (this session): equal `lights_on==lights_off` → `None` (skip); midnight wrap `(off−on) mod 24`; `use_dynamic_sunrise=True` → fall through to outdoor; `light_type==natural` windowsill → no artificial schedule → fall through |
| `scope_boundaries` | yes | 0.90 | specification | **Teach-back confirmed** (this session): indoor wins over GPS when a usable artificial schedule exists; outdoor path and autoflower unchanged |

## Requirements

- **R1** — WHEN the `check_auto_transitions` task evaluates a `photoperiod_based` transition rule for a plant whose `location_key` resolves to a `Location` with a **usable artificial schedule** (`light_type != natural` AND both `lights_on` and `lights_off` set AND `use_dynamic_sunrise == False`), the system SHALL compute the effective photoperiod as the light-on hours of that schedule and evaluate the rule against it (short-day fires when hours `<` critical, long-day when `>`).
  - _dimension_: `functional` · _status_: `confirmed` · _source_: issue #382 "resolve effective indoor photoperiod from the light schedule (REQ-018) for short-/long-day induction" + teach-back on resolution rule
- **R2** — WHEN a plant has BOTH a usable artificial indoor schedule AND a GPS `Site`, the system SHALL resolve the effective photoperiod from the **indoor schedule** (indoor wins), because an artificially lit plant does not experience the astronomical day length.
  - _dimension_: `scope_boundaries` · _status_: `confirmed` · _source_: teach-back "Indoor wins; dynamic→outdoor" (this session)
- **R3** — WHEN a plant's `Location` has `use_dynamic_sunrise == True`, the system SHALL treat the schedule as sun-tracking (not a fixed artificial photoperiod) and fall through to the existing outdoor GPS/sun day-length path.
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: teach-back "dynamic→outdoor" (this session)
- **R4** — WHEN a plant has no usable artificial schedule (no `location_key`, `light_type == natural`, missing `lights_on`/`lights_off`, or `use_dynamic_sunrise == True`), the system SHALL fall back to the current outdoor GPS day-length logic, and SHALL return `None` (trigger skipped, unchanged behaviour) when the outdoor path also yields nothing.
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: plan Q3 + code inspection of current `_day_length_for_plant` returning `None`
- **R5** — WHEN computing light-on hours from an artificial schedule, the system SHALL handle the midnight wrap as `(lights_off_minutes − lights_on_minutes) mod (24×60)` (e.g. `18:00`→`06:00` = 12h), and SHALL treat `lights_on == lights_off` as ambiguous → return `None` (skip the trigger) rather than 0h or 24h.
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: teach-back "Treat as None (skip trigger)" (this session)
- **R6** — WHEN evaluating a `time_based` autoflower plant, the system SHALL NOT fire any photoperiod transition (autoflower carries no `photoperiod_based` rule), and a regression test SHALL assert this. No production code change is required for autoflower.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: REQ-003 §1a (lines 606–741: "Blüte wird NICHT durch Lichtwechsel ausgelöst") + issue #382 "Keep autoflower on time_based"
- **R7** — The system SHALL place the pure schedule→hours derivation in a domain calculator (unit-testable in isolation, near `photoperiod_calculator.py`), keeping the Celery task as orchestration only (NFR-001 5-layer), and SHALL read the location via the plant's own tenant scope so the lookup cannot leak a location across tenants.
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: CLAUDE.md NFR-001 + plan "Invariants & guardrails" (multi-tenancy note)

## Surviving assumptions / open risks

- **A1 (assumed, low risk)** — `get_location_by_key` tenant-scoping must be verified during implementation. If it is not tenant-scoped, the code MUST guard that the resolved location belongs to the plant's tenant before using its schedule. Named residual risk carried into work-step 3 (tenant-isolation guardrail in the plan). Not a blocker; a code-inspection checkpoint.
- **A2 (assumed, low risk)** — Source-of-truth choice: REQ-018 also models a phase-level `target_photoperiod_hours` (float) on the environment profile, but that lives in the actuator/profile scaffold this issue deliberately does not depend on. Deriving from `Location.lights_on/lights_off` (persisted, non-scaffold) is the correct source for the trigger; noted in case a future change wants to reconcile the two.
- **A3 (below-`τ_high`? no — all cells ≥ 0.85)** — No dimension sits below `τ_high`; there is no budget-capped residual. `non_functional`/`constraints`/`acceptance_criteria` at 0.85 are interpretation-confident (verified against code + spec) and will be validated by the green quality gate (plan step 5) rather than by further questions.
