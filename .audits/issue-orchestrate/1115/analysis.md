---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter"
issue: "1115"
classification: "bug"
secondary-classes: []
route: "direct"
status: approved
created: "2026-08-10"
approved: "2026-08-10"
---

# Issue Orchestration — Pre-analysis

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #1115 — boundary-validation ceiling is stale: MAX_ENUM_WIDENED_FIELDS 54 vs 46 in the tree
- **URL**: https://github.com/nolte/kamerplanter/issues/1115
- **Labels**: backend
- **Linked items**: filed from the #1090/#1109 run (failure observed and proven pre-existing across C-1..C-8); #973 (drop-passes-unrecorded design)
- **Prior art checked**: no open/linked PRs; open PRs are Renovate-only (no widened-field additions in flight). Not self-resolved (constant still 54 on origin/develop b46f70282).

## Requirements gate

- **Operator override recorded (2026-08-10)**: issue is operator-authored with a machine-checkable AC; grounded in measured evidence (checker run: tree carries 46; staleness margin 5 exceeded by 8). `requirements-elicit` waived.

## Classification

- **Primary class**: bug
- **Secondary class(es)**: none
- **Rationale**: deterministic in-tree test failure (`test_the_ceiling_is_not_stale_by_more_than_a_working_margin`) caused by a stale recorded constant — not infra (runners/workflows healthy; the test correctly reports real staleness). Operator-confirmed 2026-08-10.

## Scope

- **In scope**: lower `MAX_ENUM_WIDENED_FIELDS` from 54 to 46 in `scripts/check_boundary_validation.py`; prove the gate and the staleness test green; verify the checker's self-reported count agrees.
- **Out of scope**: any change to the widened-field set itself; changes to the margin (5) or the no-growth ratchet design (#973).

## Route

- **Decision**: direct
- **Rationale**: one file, one constant, machine-checkable AC, single PR strand, no roadmap item.

## Decomposition note

Inline decomposition (skill fallback) — a single one-line package; dispatching `implementation-plan-author` would be disproportionate. Recorded per operation 3.

## Work packages

### B-1 — Lower the recorded ceiling to the measured tree count

- **Problem statement**: `MAX_ENUM_WIDENED_FIELDS = 54` (`scripts/check_boundary_validation.py:182`) lags the tree's actual 46 widened fields by 8 > margin 5, so the staleness guard fails repo-wide in the non-required `lint-test (3.14)` lane, masking real regressions optically.
- **Acceptance criteria**:
  1. Constant lowered to 46 (the value the checker itself reports as the lowerable target).
  2. `scripts/check_boundary_validation.py` gate passes; `pytest src/backend/tests/unit/test_boundary_validation_check.py -q` fully green (staleness test AND the rest of the suite).
  3. Red-first evidence: staleness test shown failing pre-change (already measured repeatedly; re-confirm once in this worktree).
  4. `ruff check`/`format` clean on the touched file; no other file modified.
- **Touched files / artifacts**: `scripts/check_boundary_validation.py`
- **Specialist**: nolte-engineering:fullstack-developer
- **Depends on**: none

## Dependency ordering

B-1 only.

## Risks

- Shared-constant collision: a concurrently merged PR adding widened fields would make 46 too low → gate goes red loudly (fail-safe direction). Open PRs are Renovate-only; risk accepted.
- Zero headroom by design: the next widened field immediately trips the gate — that is the ratchet working as intended (#973 allows lowering without recording; raising requires justification).

## Open questions

None.

## Dispatch log
