---
artifact-type: issue-orchestration-analysis
repo: nolte/kamerplanter
issue: 737
classification: refactor
secondary-classes: [feature-request, docs]
route: direct
status: in_progress
created: 2026-07-23
approved: 2026-07-23
approval-notes: operator approved direct route + requirements-gate override + single-PR delivery of P1/P2/P3
---

# Issue Orchestration — Pre-analysis

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #737 — Follow-ups from plant-property data-model completion (#729/#731/#735)
- **URL**: https://github.com/nolte/kamerplanter/issues/737
- **Labels**: enhancement, backend
- **Linked items**: follow-up to merged #729, #731, #735; source plan `.audits/datenmodell-pflanzeneigenschaften-plan.md`
- **Prior art checked**: the three source PRs are merged on develop; no open PR addresses these tasks; no `project/features/` or `project/roadmap.md` item covers them. Issue authored by `nolte` (repo owner + operator) → trusted content.

## Classification

- **Primary class**: refactor
- **Secondary class(es)**: feature-request (P2 adds an enum value), docs (P1 reconciles knowledge-base docs)
- **Rationale**: the issue completes and hardens the just-shipped plant-property data model (data/spec consistency, enum completeness, latent-risk engine hardening); no bug, no user-facing capability as its core.

## Requirements gate

- No `project/requirements/` artefact exists for this issue and none meets `τ_high`.
- **Operator override recorded**: the issue itself is requirements-ready — each of the three tasks carries a problem statement, concrete file anchors, a proposed approach, and testable acceptance criteria. Dispatching `requirements-elicit` would be redundant. Override to be confirmed by the operator at artifact approval.

## Scope

- **In scope**: the three tasks A/B/C of #737, delivered as one coherent PR that closes the issue — (A) reconcile the drifting tender-perennial Steckbriefe, (B) extend `DtmReference` with a flowering-onset value and backfill the Cannabis rows, (C) make `phase_transition_engine` cultivation-aware.
- **Out of scope**: revisiting the deliberately-excluded species (Solanum tuberosum, Tropaeolum majus, Foeniculum vulgare); any broader lifecycle-engine redesign; the optional hook-hardening in Task A is included only as a small additive step if low-risk.

## Route

- **Decision**: direct
- **Rationale**: one coherent outcome (finish the plant-property data-model follow-ups), a single PR strand, no new or retargeted roadmap item. The three tasks are small and topically bound; orchestrated as three work packages inside one PR (Operation 5 dispatches packages, Operation 6 opens one PR). The issue's note that they "can ship as separate PRs" is a convenience option, not a multi-outcome signal.
- **Pipeline hand-off**: n/a

## Work packages

### P1 — Reconcile tender-perennial Steckbrief lifecycle drift

- **Problem statement**: after #735 the 11 tender perennials are seeded as botanically `cycle_type: perennial`, but `spec/knowledge/plants/ocimum_basilicum.md` and `spec/knowledge/plants/impatiens_walleriana.md` still state `Lebenszyklus: annual`; Begonia semperflorens Steckbrief existence to confirm. The Steckbrief-consistency hook (#680) does not track `cycle_type`, so the drift passes CI silently.
- **Acceptance criteria**: the two drifting Steckbriefe document a botanical `perennial` lifecycle with the cultivation-annual note (pattern from `capsicum_annuum.md` / `verbena_x_hybrida.md`); Begonia semperflorens confirmed present-and-reconciled or documented absent; for all 11 species the Steckbrief `Lebenszyklus (botanisch)` matches the seeded `cycle_type: perennial`; `python app/migrations/seed_steckbrief_consistency.py --verbose` stays green.
- **Touched files / artifacts**: `spec/knowledge/plants/ocimum_basilicum.md`, `spec/knowledge/plants/impatiens_walleriana.md`, possibly a Begonia semperflorens Steckbrief.
- **Specialist**: growing-phase-auditor
- **Depends on**: none

### P2 — Extend `DtmReference` with a flowering-onset value (Cannabis)

- **Problem statement**: `DtmReference` (`app/common/enums.py:193`) has only `direct_seed`/`transplant`; 3 Cannabis sativa cultivar rows carry `days_to_maturity` but no `dtm_reference` because photoperiod-cannabis DTM counts from the flip to flowering.
- **Acceptance criteria**: a new enum value (`from_flip`) present and identical across the 3 single-source locations (`enums.py`, `plant_info.schema.yaml` inline dtm_reference enum, `frontend/src/api/types.ts`); i18n labels added in `de/enums.json` + `en/enums.json` under `dtmReference.*`; the enum 3-way-sync and i18n-completeness contracts (`tests/contracts/test_plant_property_enum_sync.py`) stay green; the 3 Cannabis rows carry the new value; REQ-007/REQ-017 changelog line added if spec-relevant.
- **Touched files / artifacts**: `app/common/enums.py`, `app/migrations/seed_data/schemas/plant_info.schema.yaml`, `frontend/src/api/types.ts`, `frontend/src/i18n/locales/{de,en}/enums.json`, `app/migrations/seed_data/species.yaml`, possibly `spec/req/REQ-007*`/`REQ-017*`.
- **Specialist**: fullstack-developer
- **Depends on**: none

### P3 — Make `phase_transition_engine` cultivation-aware (latent-risk hardening)

- **Problem statement**: `PhaseTransitionEngine._cycle_is_perennial` (`app/domain/engines/phase_transition_engine.py:48`) decides perennial-ness from the raw botanical `cycle_type` + instance override, ignoring species `cultivation_cycle_type`. Harmless today, latent bug if a reclassified species gains a repeating sequence or `cycle_restart_phase_order`.
- **Acceptance criteria**: `_cycle_is_perennial` (or its callers) use the effective, cultivation-aware cycle via `resolve_effective_cycle` (`app/domain/engines/cycle_resolver.py:36`); a test proves a botanically-perennial + cultivation-annual species does not trigger a phase-sequence restart even with a repeating sequence / `cycle_restart_phase_order`; existing perennial-restart tests (`tests/unit/tasks/test_phase_transitions.py`) stay green.
- **Touched files / artifacts**: `app/domain/engines/phase_transition_engine.py`, `tests/unit/tasks/test_phase_transitions.py` (+ possibly a new engine test).
- **Specialist**: fullstack-developer
- **Depends on**: none

## Dependency ordering

P1, P2, P3 are mutually independent (disjoint file sets). Dispatched sequentially — P1 → P2 → P3 — because they share one worktree/git tree (avoids concurrent-writer stash conflicts), not because of data dependencies.

## Risks

- **P2 enum drift** → the now-active enum-sync + i18n contract gates (#731) will fail the build if the new value isn't mirrored across all 3 locations + both locales; specialist must run `pytest tests/contracts/` before reporting done.
- **P3 lifecycle-engine behaviour** → engine change carries regression risk; mitigated by the required negative test (no restart for cultivation-annual) plus keeping the existing perennial-restart suite green.
- **Security**: no security-sensitive path touched (knowledge docs, an enum + i18n, engine branch logic — no auth/tenant/query/injection surface). `code-security-reviewer` / `security-review` not required for this issue.

## Open questions

- Confirm the requirements-gate operator override (see Requirements gate).
- Confirm the direct route + single-PR orchestration of the three tasks.

## Dispatch log

- 2026-07-23 P1 dispatched to growing-phase-auditor — reconciled ocimum_basilicum.md, impatiens_walleriana.md and (found-to-exist) begonia_semperflorens.md to botanical `perennial` with 3-source evidence; other 8 already correct.
- 2026-07-23 P2 dispatched to fullstack-developer — added `DtmReference.FROM_FLIP` across enums.py/schema/types.ts + de/en i18n + CultivarDetailPage constant, set 3 Cannabis rows, REQ-007 v2.5→2.6; contracts green (18 enum-sync), tsc EXIT 0.
- 2026-07-23 P3 dispatched to fullstack-developer — routed `_is_perennial_cycle_restart` through `resolve_effective_cycle` (cultivation-aware) at all 3 call sites; 5 new engine tests; 4769 passed; no frozen migration touched.
