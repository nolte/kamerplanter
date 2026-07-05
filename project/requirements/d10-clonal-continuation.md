# Requirements — D10 Clonal Continuation (monocarpic mother → pup instance)

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/.
Do not record a requirement before declaring the bounded context below.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back.
-->

Status: confirmed (teach-back accepted 2026-07-05)

## Bounded context

- **What:** Issue [#381](https://github.com/nolte/kamerplanter/issues/381) — when a
  **monocarpic mother plant** (Agave / Bromeliad / Guzmania pattern) auto-transitions
  into its **terminal reproductive phase**, the system creates **one new
  `plant_instance` (the pup)** and links it to the mother via a **`descended_from`
  edge (REQ-017)** plus a **`PropagationEvent(method=clone)`** — explicitly **not** a
  cycle restart. Follow-up to #305/#385 (D10 was deliberately deferred there).
- **For whom:** Growers of monocarpic/rosette perennials; the lineage surfaces in the
  Plant-Detail view so a user sees the pup as "descended from …" / "Kindel von …".
- **Out of scope:** Full `LineageEngine` traversal (`trace_ancestors` /
  `is_graft_compatible`), the full propagation API/router registration, and any
  non-D10 REQ-017 build-out. Only the D10-necessary minimal cut is in scope.

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question budget = `12` (used: 9)
  <!-- spec defaults; unchanged. All six load-bearing open questions resolved by user decision + a whole-scope teach-back. -->
- `U_gate = min_d c_d` over required dimensions = **0.85**
- Termination: `saturation` — every required dimension ≥ `τ_high` with teach-back on the functional/scope/acceptance dimensions; no positive-EVPI question remained.

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.90 | specification | Q1 (trigger = terminal-phase auto-transition) + phase-fallback answer + whole-scope teach-back |
| `non_functional` | yes | 0.90 | interpretation | Plan invariants (idempotency, 5-layer, tenant-isolation) confirmed in teach-back |
| `constraints` | yes | 0.90 | specification | Q6 (idempotent startup creation, no versioned migration) + additive-only invariant |
| `domain_objects` | yes | 0.88 | specification | Q2 (PropagationEvent) + Q3 (denormalized lineage field) + Q4 (inherited attributes) |
| `actors` | yes | 0.90 | interpretation | Celery `check_auto_transitions` → `phase_service`; mother/pup instances; tenant — confirmed |
| `acceptance_criteria` | yes | 0.85 | specification | Plan step 5 test list + teach-back on "not a cycle restart" + idempotency |
| `edge_cases` | yes | 0.85 | specification | Q4a (mother still holds slot → pup gets no slot), phase-fallback (Q4b), double-spawn guard, non-monocarpic contrast |
| `scope_boundaries` | yes | 0.85 | specification | Q5 (Backend **+ Frontend** + Tests), Q2 (PropagationEvent in), minimal-REQ-017 boundary confirmed |

Self-consistency note: `domain_objects` and `edge_cases` were each sketched with
`k = 2` independent readings before asking — the "slot inheritance" divergence
(mother alive vs. slot free) and the "phase fallback" divergence drove Q4a/Q4b.

## Requirements

<!-- EARS/CNL form, tagged confirmed/assumed, traceable to the deciding utterance. -->

- **R1** — WHEN a monocarpic mother plant auto-transitions into its terminal
  reproductive phase (`flowering` / `fruit_development` / `ripening`), the system
  SHALL spawn exactly **one** new `plant_instance` (the pup) instead of restarting
  the mother's cycle.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Q1 "Bei Eintritt in terminale Phase" + teach-back
- **R2** — WHEN the pup is spawned, the system SHALL set its `current_phase_key` to
  `pup_establishment` if that phase exists in the species sequence, otherwise SHALL
  fall back to the first phase of the sequence (via `_resolve_initial_phase_key`).
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Q4b "Fallback auf erste Sequence-Phase"
- **R3** — WHEN the pup is spawned, the system SHALL create a `descended_from` edge
  from the pup (child) to the mother AND persist a `PropagationEvent(method=clone)`
  linking mother → pup.
  - _dimension_: `functional` / `domain_objects` · _status_: `confirmed` · _source_: Q2 "Zusätzlich PropagationEvent(method=clone)"
- **R4** — WHEN the pup is spawned, the system SHALL inherit `tenant_key`,
  `species_key`, `cultivar`, and the mother's **location** — but SHALL NOT bind a
  slot (the mother still occupies its slot while senescing) — and SHALL set
  `planted_on` to the terminal transition date.
  - _dimension_: `domain_objects` / `edge_cases` · _status_: `confirmed` · _source_: Q4a "Location erben, kein Slot"
- **R5** — The system SHALL expose the lineage both as the `descended_from` edge AND
  as a denormalized field (`mother_key` / `propagated_from`) on the `PlantInstance`
  model and its API response.
  - _dimension_: `domain_objects` · _status_: `confirmed` · _source_: Q3 "Edge + denormalisiertes Feld"
- **R6** — WHEN the Plant-Detail view is shown for a pup, the frontend SHALL display
  an ancestry link ("Kindel von …" / "descended from …") to the mother instance.
  - _dimension_: `functional` / `scope_boundaries` · _status_: `confirmed` · _source_: Q5 "Inkl. Frontend-Abstammungs-Link"
- **R7** — WHEN the monocarpic terminal transition is re-evaluated, the system SHALL
  NOT spawn a duplicate pup nor a duplicate edge (idempotent; guarded by existence of
  the `descended_from` edge / a spawn marker).
  - _dimension_: `edge_cases` / `non_functional` · _status_: `confirmed` · _source_: teach-back "idempotent (Doppel-Spawn-Guard)"
- **R8** — The monocarpic terminal continuation SHALL NOT set `is_cycle_restart` nor
  increment `cycle_number`; continuity is expressed solely through the new instance.
  - _dimension_: `scope_boundaries` / `acceptance_criteria` · _status_: `confirmed` · _source_: Goal + teach-back "explizit kein Cycle-Restart"
- **R9** — The `descended_from` edge collection SHALL be created idempotently at
  startup (additive), WITHOUT a versioned migration-framework entry.
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: Q6 "Idempotente Startup-Erzeugung"
- **R10** — The pup SHALL inherit the mother's `tenant_key`, and every new path
  (spawn, edge, event) SHALL enforce tenant isolation (no cross-tenant spawn/edge).
  - _dimension_: `non_functional` / `edge_cases` · _status_: `confirmed` · _source_: Invariant SEC-001 (#385) confirmed in teach-back
- **R11** — The monocarpic terminal decision SHALL remain a pure engine (no I/O); the
  spawn + edge + event side-effects SHALL live in the service layer (5-layer, NFR-001).
  - _dimension_: `non_functional` / `constraints` · _status_: `confirmed` · _source_: Plan design decision §2 + invariants
- **R12** — Full `LineageEngine` traversal and the full propagation API/router
  registration SHALL remain out of scope (D10-minimal cut only).
  - _dimension_: `scope_boundaries` · _status_: `confirmed` · _source_: teach-back "nur der D10-nötige Minimalschnitt"

## Surviving assumptions / open risks

- **A1 (assumed)** — The pup's `PropagationEvent(method=clone)` reuses the existing
  `models/propagation.py` / `services/propagation_service.py` stubs *just enough* to
  persist the event; wiring the full propagation router stays out of scope (R12). If
  reusing the stub forces broader router/API activation, that boundary must be
  re-confirmed. _dimension_: `domain_objects` / `scope_boundaries`.
- **A2 (assumed)** — "Terminal reproductive phase" = the core-phase set
  `{flowering, fruit_development, ripening}` from `cyclic_lifecycle_engine.py:25`
  (`_REPRODUCTIVE_TERMINAL`). If a species' sequence names the terminal phase
  differently, the trigger predicate must map it. _dimension_: `functional` / `edge_cases`.
- **A3 (assumed)** — The denormalized `mother_key`/`propagated_from` field is additive
  on the Pydantic model and needs no data migration for existing instances (defaults
  to null). Consistent with R9's additive stance. _dimension_: `domain_objects`.
- **Residual (below `τ_high` is none)** — all required dimensions cleared `τ_high`;
  the three assumptions above are the named open risks to re-check during implementation.
