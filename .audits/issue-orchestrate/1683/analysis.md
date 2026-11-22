---
artifact-type: issue-orchestration-analysis
repo: nolte/kamerplanter
issue: "1683"
classification: infra
secondary-classes: []
route: direct
status: approved
created: 2026-11-22
---

# Issue Orchestration — Pre-analysis #1683

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #1683 — Run the lane-input recorder in CI so .github/lane-inputs/ is measured, never hand-edited — then promote the coverage guard to required
- **Labels**: cicd, github-actions, test
- **Linked items**: #1596, #1682, #1747, #1794 (recording leaves PRs), weekly bot PRs #2459/#2554/#2633/#2837/#2988/#3031
- **Prior art checked**: `.github/workflows/lane-inputs.yml`, `scripts/ci/lane_inputs.py`, `src/backend/tests/unit/guards/test_lane_filters_cover_measured_inputs.py`, `.github/workflows/backend-guards.yml`, `src/backend/pyproject.toml`; no open PR references #1683.
- **Working copy**: /home/nolte/repos/.worktrees/kamerplanter/promote-lane-input-guard; created via `task worktree:add`; `git check-ignore -q` on this path: not ignored.

## Classification

- **Primary class**: infra
- **Rationale**: CI gate wiring (which guard tests the required lane runs); no product code. Not a red run, so not a `workflow-health-triage` case.
- **Asserted cause verified**: none asserted. The open review finding from #1747 (first matching `accepted_gaps` only) is **refuted as still open**: `scripts/ci/lane_inputs.py` `read_drift` and `delegated_reads` iterate every matching gap (comment "Every matching gap, not the first (#1683 review of #1747)").

## Checklist status (measured 2026-11-22)

| Box | Status | Evidence |
|---|---|---|
| 1 Recorder in CI writes the manifests | done | `lane-inputs.yml` record/compare/guard/propose jobs; weekly bot PRs merged 10-19, 10-26, 11-02, 11-09, 11-16, 11-18 |
| 2 guards/coverage measured in CI, no partial manifests | done | 45 manifests, `status:` 29 measured / 16 derived / 0 partial |
| 3 non-zero exit needs `allow_failure_reason` | done | both `exit_code: 1` manifests carry one (`frontend--npm-audit-dev.yaml:23`, `docker-publish--publish-helm-charts.yaml:48`); rule in guard + recorder |
| 4 no `'**'` gap, no boilerplate | done in substance | no `pattern: '**'`; 35 identical reasons are the 34 `covered_by: backend-guards.yml/guards` delegations of `backend--lint-test.yaml`, each machine-checked against the guards lane's recording (not an unchecked exemption) |
| 5 promote to required on measured history | **open — operator decision** | see below |

## Measured history for box 5 (NFR-018 §4)

- The file has two parts. (a) Drift rules (`lane_inputs_drift` marker) hold the committed manifests against the live workflows; they need a recording and, by #1794, run only in `lane-inputs.yml`. Measured: drift **every week** in the last 6 weeks (6 bot PRs, 4 needed a human commit). As a PR-required check this would block PRs — **not proposed**.
- (b) Everything else in `test_lane_filters_cover_measured_inputs.py` plus `test_record_legs_provide_the_measured_jobs_environment.py` (the only two `pytest.mark.advisory` files) runs today in the advisory unit tier (`pytest tests/unit/`, backend.yml). Measured over the last 200 develop `backend.yml` runs (since 2026-11-02): 183 success, 6 failure, 11 cancelled; **0 failures from either file** (grep of every failed log).

## Scope

- **In scope**: promote part (b): remove `pytestmark = pytest.mark.advisory` from both files, so the required `Write-route and tree guards` lane runs them; drift rules stay deselected via `tests/conftest.py`. Update the comments that say "promotion is #1683's decision" (backend-guards.yml ~l.271, pyproject.toml marker text, guard docstrings). Record the promotion per NFR-018 §4 (`.github/settings.yml` comment form or the NFR text, whichever the repo uses for promotions).
- **Out of scope**: making the drift rules PR-required (contradicts #1794 and the weekly drift history); changing the weekly cadence.

## Route

- **Decision**: direct — one coherent outcome, one PR, no roadmap item.

## Work packages

### P1 — Promote the recording-free lane-input guards into the required guards lane

- **Problem**: two guard files are deselected from the required lane only by the advisory marker awaiting #1683.
- **Acceptance**: (1) `grep -rn "mark.advisory" src/backend/tests/` empty (or the marker definition removed if nothing uses it, keeping `-m 'not advisory'` harmless or removing it consistently); (2) the required lane's exact command (`backend-guards.yml` ~l.324, `--max-skipped 0`) run locally collects and passes both files with 0 skipped, drift rules still deselected; (3) `test_lane_inputs_drift_runs_only_in_its_lane.py` and any guard about the advisory marker still green; (4) comments no longer say the promotion is pending; promotion recorded with the measured numbers above.
- **Files**: the two test files, `src/backend/pyproject.toml`, `.github/workflows/backend-guards.yml` (comments; check whether a changed job spec stales `.github/lane-inputs/backend-guards--guards.yaml` `job_spec_sha256` and, if so, note it — the weekly bot PR re-records it), possibly `.github/settings.yml` comments / `spec/nfr/NFR-018`.
- **Specialist**: fullstack-developer (project agent; matches CI/test wiring with code edits).
- **Depends on**: none.

## Risks

- Guards-lane wall clock grows by the runtime of both files (to be measured in the lane, reported in the PR).
- If either file needs an environment the guards lane lacks, `--max-skipped 0` turns it red — measured in P1 acceptance (2).

## Open questions (operator)

1. Approved by the operator 2026-11-22: promote part (b); drift rules stay weekly-only. #1683 closes after the merge.
