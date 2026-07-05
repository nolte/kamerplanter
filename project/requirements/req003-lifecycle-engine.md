# Requirements — REQ-003 Lifecycle Engine (Issue #305)

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back or
an authoritative user answer.
-->

## Bounded context

- **What:** Complete the backend engine implementation + cross-spec wiring +
  model/schema fields + frontend UI for the REQ-003 lifecycle audits (D8–D13 flow
  templates, E1–E8 triggers/paths/resources) that PR #304 deferred as spec/schema
  only. The `origin/develop` base already ships the foundation (models, D8 role
  map, trigger evaluators, resource resolver, `is_cycle_restart`); this work is
  **fix-forward + gap-closing, not re-implementation**.
- **For whom:** Kamerplanter growers/users managing plant lifecycles (removing a
  lost plant, reviewing survival, per-phase care regimes); the plant-phase state
  machine (REQ-003) as the consuming subsystem.
- **Out of scope (explicit):** `harvest` → `ripening` data backfill and the
  subsequent enum removal (Issue #306, data-mutating, forbidden in an additive
  PR); the `$ref` phase-enum consolidation (Issue #307). Both are separate strands.
- **Source of truth:** `spec/req/REQ-003_Phasensteuerung.md` §D8–D13 / §E1–E8;
  `spec/analysis/lifecycle-flow-completeness-audit.md`; Issue
  [#305](https://github.com/nolte/kamerplanter/issues/305).

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question
  budget = 5 (the plan's 5 pre-formulated open questions). Spec defaults, unchanged.
- `U_gate = min_d c_d` over required dimensions = **0.8** (meets `τ_high`).
- Termination: **saturation** — the three specification-uncertainty decisions
  (Q1 PR-cut, Q2 frontend-viz depth, Q3 D9–D12 seed strategy) were resolved by
  authoritative user answers; the two remaining open questions (Q4 death-freeze
  mechanism, Q5 migration need) were resolved to `assumed` by code reconnaissance
  (interpretation uncertainty answerable without the user). No positive-EVPI
  question remained.

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.9 | interpretation | REQ-003 §D8–E8 + completeness audit fully specify behaviour; code recon confirmed evaluators/role-map present, E3–E6 wiring partial |
| `non_functional` | yes | 0.85 | interpretation | CLAUDE.md + plan invariants (NFR-001 5-layer, NFR-003 English source, NFR-016 migration framework, Mobile-First, `useMemo`) |
| `constraints` | yes | 0.9 | specification | User answer Q1 (single PR); plan invariants (additive-only, no removal, Pydantic v2, fix-forward) |
| `domain_objects` | yes | 0.9 | interpretation | Code recon: `PhaseType` (53), `TransitionTriggerType`, `PlantInstance.termination_type/termination_cause/reversion_count`, `lifecycle.growth_determinacy` exist as fields |
| `actors` | yes | 0.8 | interpretation | Grower removing/losing a plant; engine; seed layer — derived from spec + code, not user-stated |
| `acceptance_criteria` | yes | 0.85 | specification | Issue #305 A–G + AC checklist; per-trigger/flag/template test obligation from plan |
| `edge_cases` | yes | 0.8 | interpretation | `k=2` self-consistency on the E5 death-freeze wiring (see A1): two independent sketches converged after code recon on reusing the removal path → low divergence; plus E3 reversion guard, E6 premature bolting, E4 indeterminate abstraction, no-backward-transition-except-`is_reversion`/`is_cycle_restart` |
| `scope_boundaries` | yes | 0.9 | specification | Audit "Offen" section (#306/#307 out of scope); user answers Q1/Q3 |

## Requirements

### Backend — triggers, non-linear paths, loss (A–F, E-series)

- **R1** — WHEN a phase transition trigger is `photoperiod_based` and the effective
  day length ≤ `critical_day_length_hours`, the `PhaseTransitionEngine` SHALL fire
  the transition. (E1)
  - _dimension_: `functional` · _status_: `confirmed` · _source_: REQ-003 §E1; audit E1
- **R2** — WHEN a phase transition trigger is `vernalization_based` and accumulated
  chill hours meet the gate, the engine SHALL fire the transition. (E2)
  - _dimension_: `functional` · _status_: `confirmed` · _source_: REQ-003 §E2; `VernalizationTracker`
- **R3** — WHEN a transition is flagged `is_reversion=true`, the engine SHALL permit
  the otherwise-forbidden backward transition AND SHALL increment `reversion_count`. (E3)
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: REQ-003 §E3; plan invariant "no backward transition except `is_reversion`/`is_cycle_restart`"
- **R4** — WHEN a lifecycle's `growth_determinacy` is `indeterminate`, the engine
  SHALL treat the productive phase as a stable phase (no automatic advance). (E4)
  - _dimension_: `functional` · _status_: `confirmed` · _source_: REQ-003 §E4
- **R5** — WHEN a plant instance is removed with `termination_type='died'`, the
  system SHALL record `termination_cause`, freeze the current phase, and close its
  open tasks/reminders via the existing plant-removal path. (E5)
  - _dimension_: `edge_cases` · _status_: `confirmed` (behaviour) / `assumed` (mechanism, see A1) · _source_: REQ-003 §E5
- **R6** — WHEN a `vegetative → bolting` transition occurs under stress conditions,
  the engine SHALL mark it `is_premature=true`. (E6)
  - _dimension_: `functional` · _status_: `confirmed` · _source_: REQ-003 §E6
- **R7** — The engine SHALL map all 53 `PhaseType` values to engine roles via
  `phase_role_map` (D8), with no unmapped phase. (D8)
  - _dimension_: `domain_objects` · _status_: `confirmed` · _source_: audit Befund 2 (D8)
- **R8** — The seed layer SHALL provide **real reference species** for the D9–D12
  flow templates: CAM/succulent double-rest (D9), pup-monocarpy Agave/Bromelie (D10),
  photoperiodic ornamental Poinsettia/Kalanchoe (D11), palm/fern/fine-grained
  geophyte (D12).
  - _dimension_: `scope_boundaries` · _status_: `confirmed` · _source_: **User answer Q3 — "Reale Referenz-Arten"**
- **R9** — The system SHALL resolve a per-phase irrigation regime with ET/sensor
  override (`phase_resource_resolver`). (E7)
  - _dimension_: `functional` · _status_: `confirmed` · _source_: REQ-003 §E7
- **R10** — The system SHALL resolve a per-phase NPK/EC/pH nutrient regime with
  feeder scaling + pH gating. (E8)
  - _dimension_: `functional` · _status_: `confirmed` · _source_: REQ-003 §E8

### Frontend (G)

- **R11** — WHEN a user removes a plant instance, the UI SHALL capture
  `termination_type` and, when `='died'`, `termination_cause`.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Issue #305 G; code recon (absent in `src/frontend/src`)
- **R12** — The UI SHALL present a survival-rate + failure-cause view as **both a
  table and a chart** (loss by phase/cause, via the dataviz skill), Mobile-First
  with descriptive help text.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: **User answer Q2 — "Tabelle + Chart"**
- **R13** — The plant detail / phase view SHALL show the per-phase irrigation and
  nutrient regime (R9/R10 surfaced).
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Issue #305 G; plan step 3

### Non-functional & delivery

- **R14** — All new engine logic SHALL be pure/testable (no I/O), the caller
  collecting context, per the 5-layer architecture (NFR-001) and the existing
  `TransitionTriggerEvaluator` pattern.
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: CLAUDE.md NFR-001; plan invariants
- **R15** — All changes SHALL be additive (no enum/field removal); the new nullable/
  defaulted fields (`termination_type`, `termination_cause`, `reversion_count`,
  `growth_determinacy`) SHALL require no data migration for existing instances.
  - _dimension_: `constraints` · _status_: `assumed` (see A2) · _source_: code recon (fields nullable/defaulted); plan Q5
- **R16** — Acceptance-criteria tests SHALL cover each trigger (E1/E2), flag
  (E3/E6), template (D9–D12), the D8 mapping, and E4/E5/E7/E8, with no regression
  of the D1–D7 archetypes.
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: Issue #305 AC; plan step 4
- **R17** — Issue #305 SHALL be delivered as a **single PR** to `develop`.
  - _dimension_: `scope_boundaries` · _status_: `confirmed` · _source_: **User answer Q1 — "Ein großer PR"**

## Surviving assumptions / open risks

- **A1** _(assumed, R5)_ — E5 death-freeze **reuses** the existing plant-removal
  path in `plant_instance_service.py` plus the `task_service`/`care_reminder_service`
  close mechanics, rather than a new path (matches fix-forward invariant; resolves
  plan Q4). `k=2` self-consistency: two independent wiring sketches converged after
  code recon → low divergence, but verify the exact close-hook during implementation.
- **A2** _(assumed, R15)_ — No data migration is required because the new fields are
  nullable/defaulted. Verify `reversion_count`'s default and that no non-null DB
  constraint is added before closing this assumption.
- **A3** _(open, R12)_ — Exact chart type for the survival/failure view is deferred
  to implementation (dataviz skill picks it); low risk.
- **A4** _(scope, R17)_ — `harvest`→`ripening` backfill (#306) and `$ref`
  consolidation (#307) remain explicitly out of scope for this PR.
- **A5** _(scope, revisit after gap-audit)_ — Two #305 boxes are deferred by
  **user decision** to keep this PR focused, and will be documented as follow-up
  issues rather than dropped silently:
  - **A3 / D10 clonal continuation** — the monocarpic *terminal* decision stays
    (done); creating a new pup `plant_instance` + `descended_from` edge is REQ-017
    work (`lineage_engine` is a `NotImplementedError` scaffold). → **follow-up #381**.
  - **B1 / E1 indoor photoperiod** — outdoor astronomical photoperiod trigger
    stays (done); the indoor light-schedule source (REQ-018) stays deferred;
    autoflower→`time_based` is safeguarded. → **follow-up #382**.
  - **E7/E8 resolver live consumption** — the `PhaseResourceResolver` (incl. E8
    pH gating) is implemented + tested but has no service/API consumer; wiring it
    into the watering/nutrient paths pulls in REQ-037/005/004/019. → **follow-up #383**.
- **A6** _(revisit after docs pass)_ — E4/E6 were code-complete but data-inert;
  activated by seed data (tomato/pepper/cucumber `growth_determinacy: indeterminate`;
  spinach photoperiod `vegetative→bolting` `is_premature`). Docs flipped from
  "partially available" to active for those species. Broader species coverage +
  UI/API editability of the classification remain future work.
  - **A1** (transition engine not consulting `phase_role_map`) is acceptable as-is:
    the role map is consumed by the resource resolver and cyclic engine; the
    transition engine's `sequence_order`+flags decision is correct.
