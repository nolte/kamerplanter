# Pre-Analysis — Issue #626

| Field | Value |
|-------|-------|
| Issue | [#626](https://github.com/nolte/kamerplanter/issues/626) |
| Title | Bug: Create Plant always 422s for species with a PhaseSequence — dialog defaults `current_phase_key` from the wrong source (LifecycleConfig vs PhaseSequence) |
| Classification (primary) | `bug` |
| Classification (secondary) | — |
| Route | direct implementation (bounded, single PR strand, no roadmap item) |
| Requirements gate | operator override — acceptance criteria in the issue are already precise and testable (τ_high satisfied); no `project/requirements/626-*.md` authored |
| Worktree | `/home/nolte/repos/.worktrees/kamerplanter/626-plant-create-phase-source` (branch `fix/626-plant-create-phase-source`, off `origin/develop`) |
| State | OPEN, labels `bug`, `fix`; no linked/closing PRs; not self-resolved |

## Classification rationale

Reported reproducible failure (HTTP 422 on plant creation) with a known root
cause and a corrected behaviour to restore → `bug`. The backend is correct; the
defect is a frontend phase-source divergence. No spec change, no security
surface, no new capability → single primary class `bug`.

## Root cause (verified in code)

- **Backend** `src/backend/app/domain/services/plant_instance_service.py`
  - `_valid_phase_keys(species_key)` resolves **PhaseSequence-first**:
    returns `{entry.key for entry in entries}` when the species has a sequence
    with entries; only falls back to LifecycleConfig growth-phase keys otherwise.
  - `create_plant` (`:122-138`) rejects a supplied `current_phase_key` not in
    that set → `ValidationError` (`PHASE_NOT_IN_SEQUENCE`, HTTP 422).
- **Frontend** `src/frontend/src/pages/pflanzen/PlantInstanceCreateDialog.tsx`
  (`:252-266`) loads/auto-selects the phase from the **LifecycleConfig fallback
  only** (`getLifecycleConfig → listGrowthPhases → setValue('current_phase_key',
  sorted[0].key)`) and never consults the PhaseSequence. For a PhaseSequence-backed
  species the auto-selected key is never a member of the backend's valid set → the
  default always 422s, with no user interaction.

The endpoint the fix needs already exists:
`getSpeciesPhaseSequence(speciesKey)` →
`GET /api/v1/species/{key}/phase-sequence`
(`src/frontend/src/api/endpoints/phaseSequences.ts:17-24`), returning
`PhaseSequence | null` with `entries: PhaseSequenceEntry[]`
(`entry.key`, `entry.sequence_order`, `entry.phase_definition`, `types.ts:3289-3344`).

## In scope

- Make `PlantInstanceCreateDialog`'s phase-loading effect resolve the *Current
  Phase* options and default **PhaseSequence-first, LifecycleConfig fallback** —
  mirroring the backend's `_valid_phase_keys` resolution order.
- Keep phase labels human-readable and keep existing behaviour for
  LifecycleConfig-only species (and the duplicate/`duplicateFrom` path).
- Regression test proving the auto-selected default is a member of the backend's
  valid set for a PhaseSequence-backed species.

## Out of scope

- Any backend change — backend behaviour is authoritative and correct.
- Changes to the 5 shared entry points themselves (they only pass props to the
  shared dialog); they benefit automatically from the dialog fix.
- Broader PhaseSequence/lifecycle refactors (REQ-003 #539/#565).

## Work packages

| ID | Problem statement | Acceptance criteria | Touches | Specialist | Deps |
|----|-------------------|---------------------|---------|------------|------|
| WP-1 | Dialog phase-source diverges from backend: default `current_phase_key` comes from LifecycleConfig even when a PhaseSequence is authoritative, so creation 422s. | (1) PhaseSequence-backed species creates with the auto-selected default, no 422 (e.g. *Chlorophytum comosum* / species `6085`). (2) *Current Phase* dropdown lists PhaseSequence entries (not LifecycleConfig growth phases) when a sequence exists; first entry pre-selected. (3) Species without a PhaseSequence still fall back to LifecycleConfig and create. (4) `duplicateFrom` path unchanged. (5) Regression test asserts the default `current_phase_key` ∈ backend valid set for a PhaseSequence-backed species. (6) eslint/tsc/vitest pass. | `src/frontend/src/pages/pflanzen/PlantInstanceCreateDialog.tsx`; `src/frontend/src/test/pages/PlantInstanceCreateDialog.test.tsx` (+ MSW handlers under `src/frontend/src/test/mocks/`) | `fullstack-developer` | — |

Single atomic package; no inter-package DAG.

## Implementation guidance (for the specialist)

- In the phase-loading effect (`PlantInstanceCreateDialog.tsx:234-267`), first
  `await getSpeciesPhaseSequence(speciesKey)`. If the returned sequence has
  `entries.length > 0`, build the phase options from those **entries** (value =
  `entry.key`, order = `entry.sequence_order`, label = the entry's phase display
  name via `entry.phase_definition`) and auto-select the first entry by
  `sequence_order`. Only when the call returns `null`/no entries, fall back to
  the existing `getLifecycleConfig → listGrowthPhases` path.
- The dropdown at `:523-535` currently renders from `growthPhases: GrowthPhase[]`.
  Prefer a normalised option list (e.g. `{ key, sequence_order, label }[]`) that
  **both** paths populate, and render the `FormSelectField` from that — so the
  dropdown, the `disabled` guard, and the auto-select all read one source and the
  two shapes (`PhaseSequenceEntry` vs `GrowthPhase`) don't get conflated.
- Preserve the `isInitialDuplicate` guard: don't override `current_phase_key`
  when restoring a duplicate.
- Label resolution should stay human-readable; reuse the existing
  `enums.phaseName.*` i18n fallback pattern where a raw phase `name` is all
  that's available.

## Risks

- **Async ordering:** the effect already races species/cultivar loads; adding a
  `getSpeciesPhaseSequence` call must keep the `isInitialDuplicate` and
  `initialLoadDone` guards intact so a stale response can't clobber a
  user/duplicate selection. Low, but call it out in review.
- **Label gaps:** a PhaseSequence entry may lack a populated `phase_definition`;
  the label fallback must not render blank. Covered by AC + review.
- **Shared blast radius:** the dialog is used by 5 entry points; the regression
  test plus the UI-review pass mitigate a behavioural regression on the
  LifecycleConfig-only path.

## Open questions

None — the issue fully specifies the fix and the endpoint already exists.

## Route decision (operator-confirmed)

Direct implementation. Bounded: one coherent outcome, one PR strand, no
new/retargeted roadmap item. Confirmed with operator on 2026-07-13.

## Dispatch log

- WP-1 → `fullstack-developer` — **done, verified green**.
  - Files: `PlantInstanceCreateDialog.tsx`, `PlantInstanceCreateDialog.test.tsx`,
    `src/frontend/src/test/mocks/handlers.ts` (default `GET /species/:key/phase-sequence` → `null`).
  - Change: normalised `phaseOptions: {key, sequence_order, label}[]` state replaces
    `growthPhases`; effect resolves PhaseSequence-first (entries → options + auto-select
    first by `sequence_order`) with LifecycleConfig fallback; `cancelled` flag guards
    against stale-response clobber; `isInitialDuplicate`/`initialLoadDone` guards intact.
  - Regression tests: new `current-phase source (#626)` group (3 tests) — default is a
    PhaseSequence entry key (goes red on LifecycleConfig regression), dropdown lists entry
    labels, `null`-sequence falls back to LifecycleConfig.
  - Verification: `tsc --noEmit` PASS; eslint PASS (0 err, 4 pre-existing warnings);
    vitest PASS 27/27 (dialog) + 64/64 (related suites).
  - Not committed (files only).

## Post-implementation chain (project feedback)

- UI-review → `frontend-usability-optimizer` — **done, no change needed** (label/helper
  text, sortby `sequence_order`, `disabled` guard, i18n all preserved; baseline green).
- Docs → `mkdocs-documentation` — **done, no change needed** (the create-dialog fields
  aren't documented step-by-step; visible UX unchanged; mirrors #614 precedent).
- Verification gate → `quality-gate` — **green** (worktree, FE-only diff): eslint 0 errors
  (4 pre-existing warnings), `tsc --noEmit` exit 0, vitest 38/38 (dialog + identification).
