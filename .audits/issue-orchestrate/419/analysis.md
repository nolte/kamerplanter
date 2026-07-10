---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter"
issue: 419
classification: "refactor"
secondary-classes: []
route: "direct"
status: verified-green
created: "2026-07-09"
---

# Issue Orchestration — Pre-analysis

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #419 — test(frontend): cover 20 large detail/list pages (delete flows + main paths)
- **URL**: https://github.com/nolte/kamerplanter/issues/419
- **Labels**: chore
- **Linked items**: split out of #395 (ConfirmDialog loading state, merged as #418); draft delete-flow tests recoverable from dropped commit `fa271c4c1`
- **Prior art checked**: no `project/features/` entry, no `project/roadmap.md` item, no open PR targets #419. The July coverage-remediation wave (#414, #362, +322 tests) raised the global gate via *other* files and never touched these 20 pages — verified: 0/20 are in the current coverage scope.

## Classification

- **Primary class**: refactor
- **Secondary class(es)**: none
- **Rationale**: Pure test-coverage maintenance chore (GitHub label `chore`); no behaviour change, no security or spec dimension. `refactor` is the closest primary class in the closed set for a quality/maintenance change.
- **Requirements gate**: no `project/requirements/` artifact exists for #419. Operator recorded an **explicit override** (2026-07-09): the requirements are crisp and self-contained — each page's tests must bring the page *and its newly-scoped transitive imports* to ≥ the vitest gate (statements/functions/lines 80 %, branches 75 %); draft delete-flow tests recoverable from dropped commit `fa271c4c1`. A formal `requirements-elicit` interview would add no clarity.

## Scope

- **In scope**: Add vitest component tests for all 20 listed detail/list pages (render + primary CRUD/delete flows incl. the `ConfirmDialog` `loading` state + error paths + key view modes), each page covered to ≥ gate, landed as **one PR that closes #419** while keeping global coverage green.
- **Out of scope**: Any production-code change to the pages themselves (test-only PR). Raising the branch-coverage threshold (`vitest.config.ts` pin stays 75). Pre-existing untested modules not among the 20 pages.

## Route

- **Decision**: direct
- **Rationale**: One coherent outcome (cover the 20 pages), a single PR strand, no new or retargeted roadmap item, and no goal-outcome span. A test-coverage chore has no roadmap outcome, so the formal pipeline is inappropriate. Operator confirmed **all 20 pages in one PR** (2026-07-09).
- **Pipeline hand-off**: n/a

## The binding constraint (v8 coverage-scope trap)

Current baseline (all four gates green, but two razor-thin):

| Metric | Current | Gate | Headroom |
|--------|---------|------|----------|
| statements | 84.33 % | 80 | comfortable |
| lines | 86.48 % | 80 | comfortable |
| functions | 80.22 % | 80 | ~9 functions |
| branches | 75.04 % | 75 | ~3 branches |

vitest `provider: 'v8'` instruments only *imported* files. Adding a test file for a currently-untested page pulls its **entire body plus transitive imports** (sub-components, hooks) into the denominator for the first time. With near-zero headroom on functions and branches, every landed page must be covered **well above** gate, or global coverage goes red. This is why the work is real per page (page + its newly-scoped imports), and why packages are grouped by domain to share transitive imports. The coverage check is **non-required** (only `static` blocks merge), but not regressing it is the whole point of #419.

## Work packages

Packages P1–P5 are independent authoring clusters (one dispatch each); pages are grouped by domain so each cluster's shared sub-components enter coverage scope once. P6 is the central verification + PR package that depends on all authoring packages.

### P1 — Watering & Nutrient pages

- **Problem statement**: No tests for the fertilizer/nutrient/watering detail pages.
- **Pages**: `FertilizerDetailPage`, `NutrientPlanDetailPage`, `FeedingEventDetailPage`, `TankDetailPage`, `WateringLogDetailPage`
- **Acceptance criteria**: For each page, a new test file covers render + primary CRUD/delete flow (incl. `ConfirmDialog` `loading` state) + error path + key view modes, such that `npx vitest run <test> --coverage --coverage.include='**/<Page>.tsx' --coverage.reporter=text` reports ≥80 % func/lines/stmts and ≥75 % branch for that page. All tests green.
- **Touched files / artifacts**: new `src/frontend/src/test/*.test.tsx` (or co-located) files only — no production code.
- **Specialist**: nolte-engineering:component-test-generator
- **Depends on**: none

### P2 — Phase & Workflow pages

- **Problem statement**: No tests for the phase-definition/phase-sequence/workflow pages.
- **Pages**: `PhaseSequenceDetailPage`, `PhaseSequenceListPage`, `PhaseDefinitionDetailPage`, `PhaseDefinitionListPage`, `WorkflowDetailPage`, `WorkflowTemplateListPage`
- **Acceptance criteria**: as P1, per page, verified via `--coverage.include`.
- **Touched files / artifacts**: new test files only.
- **Specialist**: nolte-engineering:component-test-generator
- **Depends on**: none

### P3 — Location, Site, Substrate, Slot pages

- **Problem statement**: No tests for the location/site/substrate/slot detail pages.
- **Pages**: `LocationDetailPage`, `SiteDetailPage`, `SubstrateDetailPage`, `SlotDetailPage`
- **Acceptance criteria**: as P1, per page, verified via `--coverage.include`.
- **Touched files / artifacts**: new test files only.
- **Specialist**: nolte-engineering:component-test-generator
- **Depends on**: none

### P4 — Tasks, Activity, Calendar pages

- **Problem statement**: No tests for the task/activity/calendar pages (CalendarPage is the largest, ~32 % func at issue time).
- **Pages**: `CalendarPage`, `TaskDetailPage`, `ActivityDetailPage`
- **Acceptance criteria**: as P1, per page, verified via `--coverage.include`.
- **Touched files / artifacts**: new test files only.
- **Specialist**: nolte-engineering:component-test-generator
- **Depends on**: none

### P5 — Batch & Botanical pages

- **Problem statement**: No tests for the batch/botanical-family detail pages.
- **Pages**: `BatchDetailPage`, `BotanicalFamilyDetailPage`
- **Acceptance criteria**: as P1, per page, verified via `--coverage.include`.
- **Touched files / artifacts**: new test files only.
- **Specialist**: nolte-engineering:component-test-generator
- **Depends on**: none

### P6 — Global verification + PR

- **Problem statement**: Individually-green pages can still drag global coverage below gate via shared transitive imports; the aggregate must be verified before the PR.
- **Acceptance criteria**: Full `npx vitest run --coverage` reports all four gates green (stmts/func/lines ≥80, branch ≥75) with the 20 pages in scope; `quality-gate` passes (`static`); PR opened via `pull-request-create` with `Closes #419` and Risk/rollout notes carrying the classification + per-package specialist. Any page still below gate routes back to its authoring package for a top-up pass.
- **Touched files / artifacts**: none beyond top-up test edits; the PR.
- **Specialist**: orchestrator-run `quality-gate` + `unit-test-runner` (project) for any green-up top-up; `pull-request-create` for the PR.
- **Depends on**: P1, P2, P3, P4, P5

## Dependency ordering

P1, P2, P3, P4, P5 (independent, dispatched concurrently) → P6 (verify + PR).

## Risks

- **v8 transitive-import drag** — a fully-covered page still pulls poorly-covered sub-components/hooks into scope, lowering global func/branch. *Mitigation*: domain clustering (shared imports covered once); per-page `--coverage.include` gate; P6 global re-measure with a top-up loop before the PR.
- **Branch gate razor-thin (~3 branches)** — the aggregate could land just under 75 % branch. *Mitigation*: P6 measures precisely and P1–P5 target ≥80 % branch per page (above the 75 gate) to build headroom; the check is non-required so a marginal miss does not block merge but is fixed before opening.
- **Parallel agents on a shared worktree** — concurrent git operations can trigger a git-stash recovery conflict. *Mitigation*: agents are instructed to **only create new test files and run vitest read-only — no git commands**; this is the proven functional-isolation pattern used for the July +322-test remediation in this repo.
- **jsdom / test-infra footguns** — no native `localStorage`/`matchMedia`; EN default locale; `react-grid-layout` crashes under jsdom; `ModuleVisibilityState = 'enabled'|'disabled'`. *Mitigation*: agents briefed with the reusable Kamerplanter FE test-infra patterns (renderWithProviders, msw `server.use`, i18n de-switch, mocks).

## Open questions

None — scope, route, and requirements override confirmed by operator on 2026-07-09.

## Dispatch log

- 2026-07-09 — Operator gates approved: requirements-elicit **override**, route **direct / all-20-one-PR**, artifact **approved**, dispatch mode **parallel**.
- 2026-07-09 — Shared `src/frontend/src/test/helpers.tsx` change (add `tasksReducer`, from dropped commit `fa271c4c1`) applied centrally by orchestrator to avoid multi-agent conflict on the shared file.
- 2026-07-09 — P1–P5 dispatched in parallel to nolte-engineering:component-test-generator (worktree `/home/nolte/repos/.worktrees/kamerplanter/419`).
- 2026-07-10 — P1–P5 all returned: 20 new test files, ~335 tests, all green; every page individually ≥ gate via `--coverage.include` (borderline branch: Slot 75.0, Calendar 76.9, Workflow 79.3, Tank 79.4).
- 2026-07-10 — **P6 aggregate check FAILED the premise.** Full-suite coverage with the 20 new files: statements 79.94 % / branches 70.00 % / functions 75.96 % (lines 82.27 % OK) → 3 gates red. Verified against a clean **develop full-suite baseline** (green: 84.36 / 75.10 / 80.26 / 86.50). The per-page `--coverage.include` check only measured each page file; rendering each page pulls its **transitive child graph** (dialogs, tabs, views, hooks) into scope for the first time — pages are `React.lazy` in `AppRoutes`, so they were out of develop's scope. Delta introduced by the 20 files: **+1375 functions, +3469 branches** into the denominator, ~mostly uncovered; to clear the gate needs **+211 functions and +570 branches** covered across ~370 truly-new transitive files. The two biggest drags are entire additional large pages (`PlantInstanceDetailPage` F-144/B-479, pulled via `useRunNutrientData.ts` → page import; `PlantingRunDetailPage` F-72/B-131) plus `DosageCalculatorTab` (0 %), the nutrient-plan-detail subtree, calendar views (`SowingCalendarView`, `PhaseTimelineView`), and workflow dialogs (`WorkflowInstantiateDialog`, `WorkflowPhaseDialog`).
- 2026-07-10 — **Escalated to operator**: closing #419 (all 20 pages) *and* keeping global coverage green requires covering the transitive closure too. The coverage check is non-required (`static` still passes; lines still ≥80).
- 2026-07-10 — **Correction (path-normalization bug in my own baseline diff):** coverage-summary keys are absolute paths; develop's summary sits under `/repos/github/…` and the worktree's under `/repos/.worktrees/…`, so an unnormalized diff flagged *all* files as new. After normalizing to repo-relative keys: only **59 genuinely-new files** (not 370), **+1375 functions / +3469 branches** into scope (498 func / 1451 branch uncovered). `PlantInstanceDetailPage`/`PlantingRunDetailPage` were NOT new (path artifact) — every real drag is a legitimate child of the 20 pages. Deterministic import-graph attribution + a removal simulation confirmed a green prune needs dropping ≥5 pages (branch margin razor-thin 75.15), whereas covering ~12 child modules clears the gate with headroom.
- 2026-07-10 — **Operator revised route → EXPAND** (data materially changed: expand went from ~370 files to ~12 child modules / one wave). Keep all 20 pages, cover the newly-exposed children, close #419 green.
- 2026-07-10 — **P7 dispatched** (parallel, nolte-engineering:component-test-generator) — cover the newly-exposed child modules: P7a nutrient-plan-detail tabs/hooks; P7b duengung dialogs/calc/gantt; P7c calendar views; P7d workflow dialogs + watering-log dialog; P7e standorte/sensor sections & dialogs.
- 2026-07-10 — **P7a–P7e all returned**: 20 new child-module test files, ~187 tests, all green; every module ≥80 % on all four metrics (branch 82.7–96.2 %). Biggest single drag `DosageCalculatorTab` 0 %→82.7 % branch. Total suite additions across P1–P7: ~40 new test files.
- 2026-07-10 — Final full-suite coverage verification: initial runs hit the repo's documented **wandering `findBy*` load-flake** (`WorkflowInstantiateDialog` empty-template test — passes isolated & in the pages subset, misses the 1000ms default async window under full-suite parallelism). Root-caused as timing, not pollution (default per-file isolation is on). **Systemic fix**: raised Testing-Library `asyncUtilTimeout` to 5000ms in `src/test/setup.ts` (same spirit as the file's existing AuthImage load-timeout stub) — stabilises the whole suite, not just this test.
- 2026-07-10 — **P6 GREEN**: full suite 2871/2871 pass; all four gates green with headroom — statements 85.59 % / branches 77.26 % / functions 82.08 % / lines 87.79 % (vs develop 84.36 / 75.10 / 80.26 / 86.50). Expand *raised* branch coverage (75.10 → 77.26), the opposite of the naive add-tests-lower-coverage trap. #419 fully satisfiable green.
- 2026-07-10 — **Static-check fix**: `tsc -b` initially failed on ~19 type errors in the new test files (vitest transpiles without typecheck, so runtime-green ≠ type-clean). Dispatched **unit-test-runner** (project agent) → fixed all type/lint errors (enum values, nullable fixtures, msw body casts, `.at(-1)`→index, typed `vi.fn()` mocks, removed unused imports & stale `mixing_order`). Verified: `tsc -b` clean, `eslint` 0 errors (117 pre-existing warnings), 152/152 tests green in the 9 touched files.
- 2026-07-10 — **Flake root-caused & fixed deterministically**: the async-timeout bump alone did not fix `WorkflowInstantiateDialog`; traced to the dialog's load effect depending on `useApiError().handleError`, whose `useCallback` deps are `[t, notification]` — react-i18next hands back a new `t` on `languageChanged`, and under load a mid-test language event re-runs the effect and strands the loading spinner. Fix: mock `react-i18next` in that one test file to a single bound `t` (stable identity, still delegates to the i18n singleton). Full suite now **deterministic green**: 2871/2871, gates 85.59 / 77.25 / 82.08 / 87.79.
- 2026-07-10 — **PR opened**: committed (`97fbcadaa`, rebased onto develop tip `a47b287a5`), `lint:frontend` 0 errors, pushed, opened **draft PR #435** (`Closes #419`) via `pull-request-create` with operator-approved title/body and the required Risk/rollout audit trail. Posted orchestration summary as a comment on #419. Orchestration stops here; merge belongs to `pull-request-merge` after CI is green.
status-final: verified-green, PR #435 (draft) open
