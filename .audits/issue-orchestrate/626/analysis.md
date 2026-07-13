---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter"
issue: "626"
classification: "bug"
secondary-classes: []
route: "direct"
status: done
created: "2026-07-13"
---

# Issue Orchestration — Pre-analysis

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #626 — Create Plant always 422s for species with a PhaseSequence — dialog defaults current_phase_key from the wrong source (LifecycleConfig vs PhaseSequence)
- **URL**: https://github.com/nolte/kamerplanter/issues/626
- **Labels**: bug, fix
- **Prior art checked**: no open PR addresses it; authored from live prod repro + code + running-backend confirmation.

## Classification

- **Primary class**: bug
- **Rationale**: The Create Plant dialog auto-fills a `current_phase_key` the backend always rejects (422) for PhaseSequence-backed species — a shipped-behaviour defect.
- **Requirements gate**: operator override — the issue carries code-grounded, testable ACs verified against source and the running prod backend.

## Scope

- **In scope**: Make `PlantInstanceCreateDialog` resolve the *Current Phase* options and default the **same way the backend does** — PhaseSequence-first (`getSpeciesPhaseSequence`), LifecycleConfig-growth-phases fallback — so the auto-selected default is always a member of the backend's `_valid_phase_keys`.
- **Out of scope**: Backend validation (it is correct — validates against the authoritative sequence). No change to `_valid_phase_keys` / `create_plant`.

## Route

- **Decision**: direct — one coherent frontend outcome, single PR strand, no roadmap item. Bounded despite affecting 5 shared entry points (one dialog).

## Work packages

### P1 — Resolve dialog phase source PhaseSequence-first

- **Problem statement**: `PlantInstanceCreateDialog.tsx:252-262` loads/auto-selects the current phase from `getLifecycleConfig → listGrowthPhases` only (LifecycleConfig), while the backend validates against the species' PhaseSequence when one exists → the pre-filled phase 422s.
- **Acceptance criteria**: mirror the issue's ACs — PhaseSequence-first resolution via `getSpeciesPhaseSequence(speciesKey)` (`phaseSequences.ts:17`); build *Current Phase* options + auto-select-first from the PhaseSequence entries when a sequence exists; fall back to LifecycleConfig growth phases only when no sequence; default `current_phase_key` is always in the backend's valid set (no 422); LifecycleConfig-only species still create; human-readable phase labels; all 5 shared entry points create successfully; regression test asserting the default key validity; eslint/tsc/vitest green.
- **Touched files**: `src/frontend/src/pages/pflanzen/PlantInstanceCreateDialog.tsx`; possibly `src/frontend/src/api/endpoints/phaseSequences.ts` / `phases.ts` (only if a helper is missing); tests under `src/frontend/src/test/`.
- **Specialist**: `fullstack-developer`
- **Depends on**: none

## Dependency ordering

P1 (single package).

## Risks

- **PhaseSequence entry shape vs GrowthPhase shape**: options rendering must handle both types' label/key fields. Mitigation: normalize to a `{key,label}` option list before rendering; specialist verifies both branches.
- **Duplicate-from / actual-state-capture path**: the dialog also supports `duplicateFrom` (preserves an existing `current_phase_key`). Mitigation: keep that branch intact; only change the *auto-resolve when no explicit phase* path.
- **No security-sensitive paths** touched → `security-review` not required.

## Open questions

none — operator authorized a clear fix.

## Dispatch log

- 2026-07-13 P1 dispatched to `fullstack-developer` — DONE. Dialog resolves *Current Phase* PhaseSequence-first via `getSpeciesPhaseSequence` (option value = `entry.key`, exactly what BE `_valid_phase_keys` checks), LifecycleConfig fallback for sequence-less species; sources normalized to `{key,label}` with i18n `enums.phaseName` fallback; `duplicateFrom` + species-switch reset intact; `growthPhases` state removed. 2 new regression tests (PhaseSequence-first + fallback). lint 0 errors, tsc clean, vitest 3333/3333 green (incl. PlantIdentificationPage 11/11).
- 2026-07-13 verify: UI-review by `frontend-usability-optimizer` — CLEAN, no changes. `enums.phaseName.*` DE/EN full parity (21 keys); `entry.key` used only as option value never label (raw keys never shown); default visible; empty/loading `disabled` guard intact; mobile-first ok.
- 2026-07-13 independent gate in worktree: lint 0 errors, tsc clean; dev's full vitest run 3333/3333 green (unchanged since UI-review made no edits). Ready for PR.
