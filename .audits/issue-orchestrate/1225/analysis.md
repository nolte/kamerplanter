---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter"
issue: "1225"
classification: "bug"
secondary-classes: [infra]
route: "direct"
status: approved
created: "2026-08-19"
---

# Issue Orchestration — Pre-analysis

<!-- Run-scoped artifact: committed on the run's feature branch, removed with a
     fix-forward `git rm` before the PR merges (spec/project/issue-orchestration/
     §Pre-analysis artifact lifecycle). Durable facts go to the PR's Risk / rollout
     notes and the issue comment; the requirement artefact under
     project/requirements/delivery-run-alert.md stays. -->

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #1225 — A red run on the delivery lane alerts nobody: no workflow_run observer exists
- **URL**: https://github.com/nolte/kamerplanter/issues/1225
- **Labels**: bug, deployment
- **Linked items**: #1218 (open — the incident; P3 of its plan is this issue), PR #1224 (merged — cause fix + outcome check, P3 deferred by operator decision), #1223 (open — `needs.changes.result` silent path, out of scope), #1210 (release-lag sibling)
- **Prior art checked**: `closedByPullRequestsReferences` empty; `gh pr list --search 1225` → only an unrelated Renovate PR (#905). `git ls-tree origin/develop` shows no `delivery-run-alert.yml`; `grep -rl workflow_run .github/workflows/` empty (established, 2026-08-19). `release-assets-complete.yml:5` and `check_release_assets.py` docstring already *name* `delivery-run-alert.yml` as the process watcher — a reference to a file that does not exist yet (established, `file:line`). Not self-resolved.
- **Trust**: author `nolte` = repository owner → trusted-author set; no comments. The issue's "Shape" section is an operator instruction, not foreign text.

## Classification

- **Primary class**: bug
- **Secondary class(es)**: infra
- **Rationale**: labelled `bug`; a missing safeguard that let a real defect go unobserved for five days. It is *not* a red-CI triage (the red runs are diagnosed and fixed in #1224), so the `infra → workflow-health-triage` short-circuit does not apply.

## Requirements gate

- `project/requirements/delivery-run-alert.md` written in this run. **Operator override recorded**: no interview (autonomous run); every requirement cites the owner-authored issue sentence or sibling artefact it is read from. R1–R8 all `confirmed`, lowest `c_d` 0.8 (R6, the no-flap closing rule — derived, specialist may refute).

## Scope

- **In scope**: `.github/workflows/delivery-run-alert.yml` (`workflow_run` on `Build & Publish Container Images`, `types: [completed]`, plus `workflow_dispatch` with `run_id`); `scripts/ci/check_delivery_run.py` (injected fetch + clock, report file, fail-loud); unit tests in `src/backend/tests/unit/test_delivery_run_check.py` replaying the measured runs; the sibling-style alert issue step (one deduped issue, label `delivery-run-failed`).
- **Out of scope**: the chart-job cause and the release-asset outcome check (#1224, merged); `needs.changes.result` (#1223); label colour/description (manual, as on #1224); observing other workflows.

## Route

- **Decision**: direct
- **Rationale**: one coherent outcome (a red delivery run becomes a visible issue), a single PR strand, no roadmap item — it is a deferred package of an already-approved plan. Bounded.

## Work packages

### P1 — Fail-loud delivery-run check script + unit tests

- **Problem statement (hypothesis)**: a standalone `scripts/ci/check_delivery_run.py` that, given a run id, fetches `GET /repos/{r}/actions/runs/{id}` and `/jobs` through an injected `fetch`, and writes `delivery-run-report.json` with a determined verdict: `alert` (conclusion ∈ {failure, timed_out, startup_failure}; lists failed jobs by name), `resolved` (conclusion == success; lists jobs that *ran* and succeeded vs. skipped), or neither (cancelled/neutral/skipped — reported, no action). Not-completed run, unknown id, unreachable API, unparseable payload → raise → red run, no report (NFR-018 §2). Unit tests replay the measured fixtures: 31729355999 (v0.2.0 tag, `publish-helm-charts (kamerplanter)` failure, `update-release-assets` skipped, 8 builds success), 31955164085 and 31955579431 (develop, chart job failure, everything else skipped), 32259216513 (v0.2.1, success, chart job ran). Fixtures are recorded payload shapes, not invented (see memory rule: a fixture inventing impossible data certifies nothing).
- **Acceptance criteria**: (a) `python3 scripts/ci/check_delivery_run.py --run-id 31729355999 report.json` with a fake fetch returning the recorded payload → report `alert: true`, `failed_jobs == ["publish-helm-charts (kamerplanter)"]`, exit 0; (b) the v0.2.1 fixture → `resolved: true`, `succeeded_jobs` contains the chart job, `skipped_jobs` does not; (c) a develop-push success fixture where the chart job is skipped → `resolved: true` but `succeeded_jobs` lacks the chart job (the workflow step, P2, uses this to refuse closing); (d) `status != completed`, HTTP error, missing `jobs` array → exception, no report written, exit 1 with `::error::`; (e) `pytest src/backend/tests/unit/test_delivery_run_check.py` green; `task precommit`/ruff green.
- **Touched files / artifacts**: `scripts/ci/check_delivery_run.py`, `src/backend/tests/unit/test_delivery_run_check.py`
- **Specialist**: `nolte-engineering:fullstack-developer` (description: "fix a bug with real code … plus matching tests"; runtime Glob confirmed `plugins/nolte-engineering/agents/fullstack-developer.md`)
- **Depends on**: none

### P2 — `delivery-run-alert.yml` observer workflow

- **Problem statement (hypothesis)**: a workflow mirroring `release-assets-complete.yml`'s shape: `on.workflow_run` (`workflows: ["Build & Publish Container Images"]`, `types: [completed]`) + `workflow_dispatch` (`run_id`); `permissions: contents: read, actions: read, issues: write`; fixed concurrency group `delivery-run-alert`, `cancel-in-progress: false`; step 1 runs the P1 script with `DELIVERY_RUN_ID: ${{ inputs.run_id || github.event.workflow_run.id }}`; step 2 (`if: always() && hashFiles('delivery-run-report.json') != ''`, digest-pinned `actions/github-script`) opens/updates the single issue labelled `delivery-run-failed` on `alert`, embedding the failed-job set in an HTML-comment marker; on `resolved` closes it **only if** every job named in the marker is in `succeeded_jobs`, otherwise comments that the green run skipped them and leaves it open (R6, no flap). Header comment explains the incident, the skipped-job blindness, and the fail-loud contract like its siblings.
- **Acceptance criteria**: (a) `actionlint`/the repo's workflow lint passes (check what `task precommit` runs); (b) the two actions are pinned to the same SHAs as the siblings; (c) `grep -rl workflow_run .github/workflows/` now returns the file; (d) a static read confirms `if:` gating on the report file and the marker-based closing rule; (e) the existing references in `release-assets-complete.yml:5` and `check_release_assets.py` resolve to the real file name.
- **Touched files / artifacts**: `.github/workflows/delivery-run-alert.yml`
- **Specialist**: `nolte-engineering:fullstack-developer` (same agent, continued — it owns the report schema). Description-match note: `nolte-shared:cicd-pipeline-design` names "writes and patches workflow files" but is a multi-step operator dialogue for *pipeline design* (stage selection, required/advisory split); a single alerting job copied from two in-repo siblings does not need that dialogue. Its read-only twin is dispatched in P3 instead.
- **Depends on**: P1

### P3 — Conformance review of the produced change (read-only)

- **Problem statement**: independent checks that P1/P2 are spec-conformant: `nolte-shared:cicd-pipeline-reviewer` on the workflow (pinning, permissions, untrusted-input handling — `github.event.workflow_run.*` is untrusted and must reach scripts via `env`, never inline), `nolte-engineering:unit-test-reviewer` on the tests (fixture honesty, falsification in both directions, no network).
- **Acceptance criteria**: no critical/high finding left unaddressed; findings applied by the P1/P2 agent or recorded with reason.
- **Touched files / artifacts**: none (read-only); fixes flow back into P1/P2 files
- **Specialist**: `nolte-shared:cicd-pipeline-reviewer`, `nolte-engineering:unit-test-reviewer`
- **Depends on**: P1, P2

## Dependency ordering

P1 → P2 → P3 (reviews in parallel) → verify (quality-gate) → PR.

## Risks

- **`workflow_run` only fires from the default branch's workflow file** — the observer cannot be exercised by this PR's own CI; verification before merge is by unit tests + `workflow_dispatch` after merge (`gh workflow run delivery-run-alert.yml -f run_id=31729355999` opens the alert for a historical run; close it afterwards). Mitigation: state this in the PR and the header comment.
- **Untrusted input**: `github.event.workflow_run.head_branch`/`display_title` are attacker-influenced on a fork PR — but `docker-publish.yml` has no `pull_request` trigger, so only `push`/`tag`/dispatch runs feed this. Still route every event field through `env`, never script interpolation (sibling pattern).
- **Permissions**: `actions: read` on the `GITHUB_TOKEN` for `/runs/{id}/jobs`; public repo reads work anonymously too, the token lifts the rate limit. No security-sensitive path per `security-review`'s path list (`.github/workflows/**` is reviewed by `cicd-pipeline-reviewer` instead); `security-review` skill is still run over the diff before the PR per operation 6.
- **Alert flapping on skipped jobs** — addressed by R6; the reviewer must confirm the closing rule is in the workflow, not only in the plan.
- **Label `delivery-run-failed` does not exist** — `issues.create` creates it without colour; manual follow-up, as for the sibling labels (PR #1224 note).

## Open questions

- none blocking. (Recorded assumption: `cancelled` is neither alert nor resolve.)

## Dispatch log
