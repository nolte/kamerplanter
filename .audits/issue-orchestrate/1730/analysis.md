---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter"
issue: "1730"
classification: "infra"
secondary-classes: ["bug"]
route: "direct"
status: approved
created: "2026-09-24"
---

# Issue Orchestration — Pre-analysis

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #1730 — lane-inputs: backend jobs read docker-compose.reach.yml and scripts/reach/* that their filters do not select
- **Labels**: cicd
- **Linked items**: #1596, #1683, #1715, #1723, #1726 (evidence), run 35979465184
- **Prior art checked**: no open PR references #1730 (`gh pr list --search 1730`).

## Classification

- **Primary class**: infra (relevance filter of a CI workflow)
- **Secondary class(es)**: bug (a job's filter does not select what it reads)
- **Rationale**: The defect is a path filter in `.github/workflows/backend.yml` plus a delegation in the lane-input manifests.
  It is not handed to `workflow-health-triage`: nothing is red on develop yet. The operator pre-approved direct orchestration.
- **Asserted cause verified**: confirmed and refined.
  - `scripts/reach/{_reach_common,observe_*}.py`: established. `strace` of `tests/unit/test_reach_observation_helpers.py`
    opens all five (`load_repo_script("reach/observe_*")`, lines 25-27, 280). The guards lane only lists the directory
    `scripts/reach/` (evidence manifest `backend-guards--guards.yaml:300`), so `accepted_gaps[scripts/**]` is false for these files.
  - `docker-compose.reach.yml`: established. The reader is `tests/unit/migrations/test_e2e_admin_env_containment.py`
    (glob `docker-compose*.yml`, line 38), not a reach test. The guards lane ALSO reads it: `strace -f` of the guards lane
    shows the reading process is a child `pytest tests/unit/migrations/test_e2e_admin_env_containment.py` started by
    `tests/unit/guards/test_execution_guards.py::_run_tier` (asserts `returncode == 0`), so the containment test really
    runs inside the required guards lane. The issue text implies only a filter gap. A missing accepted_gaps entry
    delegating to guards is the accurate fix, as for the five other compose files (gaps 7-11).
  - Local reproduction: the guard run on the evidence manifests gives exactly the four findings from the issue.

## Scope

- **In scope**: filter entry `scripts/reach/**` in both `backend.yml` path lists; an accepted_gaps entry
  `docker-compose.reach.yml` covered_by `backend-guards.yml/guards` in both backend manifests; manifests refreshed from a
  `lane-inputs` recording of the final branch.
- **Out of scope**: the generic reason text on gaps 7-11 (compose files are read by the child pytest, not by "tree
  guards"). Recorded in the PR's class sweep and not changed here.

## Route

- **Decision**: direct. One outcome, one PR, no roadmap item.
- **Requirements gate**: operator override (bounded CI issue, parent session 2026-09-24).

## Work packages

### P1 — backend.yml filter + manifest delegation + recorder refresh

- **Problem statement**: backend lint-test/coverage read `scripts/reach/*` (their own unit test) and
  `docker-compose.reach.yml` (containment test). The first is selected by no filter and by no reading delegation lane.
  The second has no gap entry.
- **Acceptance criteria**: `test_lane_filters_cover_measured_inputs.py` green on the manifests recorded from the final
  head; the lane-inputs `compare` job is green on the final head; red without the filter entry (falsification).
- **Touched files**: `.github/workflows/backend.yml`, `.github/lane-inputs/*.yaml` (recorded), accepted_gaps of
  `backend--lint-test.yaml` / `backend--coverage.yaml` (hand-written field).
- **Specialist**: `nolte-shared:cicd-pipeline-design` matches in principle. Implemented directly as operator-directed strand
  (two filter lines + one gap entry). The recorder is the instrument for the manifests.
- **Depends on**: none

## Risks

- The recording carries unrelated develop drift. Expected; any non-reach finding of a different class stops the run.
- Widening the filter makes the advisory backend lanes run on reach-script-only changes. That is intended.

## Open questions

none

## Dispatch log

- P1: direct (operator brief).
