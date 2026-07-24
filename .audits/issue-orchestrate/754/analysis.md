---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter"
issue: 754
classification: "infra"
secondary-classes: ["test"]
route: "direct"
status: approved
created: "2026-07-24"
---

# Issue Orchestration — Pre-analysis

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #754 — E2E suite: generate JUnit XML reports and render them in GitHub Actions
- **URL**: https://github.com/nolte/kamerplanter/issues/754
- **Labels**: enhancement, cicd, test
- **Linked items**: none (no `closedByPullRequestsReferences`, no open PR, no branch)
- **Prior art checked**: no matching `project/features/` entry, no `project/roadmap.md` item, no open PR referencing 754 or "junit"/"e2e report", no `*754*`/`*junit*` branch → not self-resolved.

## Classification

- **Primary class**: infra
- **Secondary class(es)**: test
- **Rationale**: Adds JUnit XML reporting + a rendering Action to the E2E CI pipeline (build/CI tooling). NOT a red-workflow/CI-failure triage → stays here for direct decomposition rather than handing to `workflow-health-triage`.

## Scope

- **In scope**:
  1. JUnit XML generation for all 7 pytest runner services in `docker-compose.e2e.yml` + collection into the run's timestamped `test-reports/e2e/<ts>/` via `scripts/run-e2e.sh`.
  2. xdist compatibility (`-n 4 --dist=loadfile`) — single merged XML, no per-worker partials, protocol plugin (`tests/e2e/conftest.py` `optionalhook`, line ~1065) unaffected.
  3. Rendering via a GitHub Action (concrete failure messages) in `e2e-smoke.yml` (per-PR job summary) and `e2e-nightly.yml` (per-profile matrix leg + link from the auto-created failure issue); raw `junit-*.xml` uploaded as artifacts.
  4. TC-ID `user_property` (`conftest.py::_record_tc_id`, line ~237) present in the XML and visible in the rendered report.
- **Out of scope** (Non-goals from the issue): replacing the Markdown protocol / screenshots (stay the human-facing audit trail per `spec/project/e2e-test-automation/`); making `e2e-smoke` a required check.

## Route

- **Decision**: direct
- **Rationale**: one coherent outcome (JUnit reports rendered in E2E CI), a single PR strand, no new/retargeted roadmap item → direct. Operator-confirmed 2026-07-24.
- **Pipeline hand-off**: n/a

## Requirements gate

- No requirement artefact exists under `project/requirements/` for this issue.
- **Operator override recorded (2026-07-24)**: the issue body is itself a complete specification (Motivation, 4-part Scope, explicit Acceptance-criteria checklist, Non-goals). U_gate is met in substance; `requirements-elicit` skipped by explicit operator decision.

## Work packages

### P1 — JUnit XML generation + run-e2e.sh collection

- **Problem statement**: pytest produces no JUnit XML today. Add `--junitxml` to every E2E runner and ensure the file lands in the run's timestamped report dir without breaking the xdist protocol plugin.
- **Acceptance criteria**:
  - All 7 runner services (`e2e-tests`, `e2e-smoke`, `e2e-tests-full`, `e2e-tests-mobile`, `e2e-tests-tablet`, `e2e-tests-full-mobile`, `e2e-tests-full-tablet`) pass `--junitxml=<container-report-dir>/junit-<profile>.xml` so `run-e2e.sh`'s existing `cp -r "$CONTAINER_REPORT"/*` move carries it into `$REPORT_DIR`.
  - Under `-n 4 --dist=loadfile` exactly one merged XML per run is produced (no per-worker partials); the protocol plugin (`optionalhook`) still writes `protokoll.md`/`checkpoint.jsonl`.
  - The `tc_id` `user_property` (`_record_tc_id`) appears in the XML.
- **Touched files / artifacts**: `docker-compose.e2e.yml`, `scripts/run-e2e.sh` (and possibly a small note in `tests/e2e/conftest.py` only if a hook adjustment is needed — no test-logic change).
- **Specialist**: `fullstack-developer` (project-tuned specialist; owns compose/shell/CI infra per its description)
- **Depends on**: none

### P2 — Workflow rendering + artifact upload

- **Problem statement**: CI has no rendered, machine-readable test report; failures require digging through raw logs.
- **Acceptance criteria**:
  - `e2e-smoke.yml`: a render step (e.g. `dorny/test-reporter` or `EnricoMi/publish-unit-test-result-action`, pinned by SHA per repo convention) shows failing tests with concrete assertion messages in the job summary; raw `junit-*.xml` uploaded as an artifact; job stays non-required; fork-PR permission model handled safely.
  - `e2e-nightly.yml`: per-profile-leg rendering (report name per matrix profile); the existing `github-script` failure-issue body links to the rendered summary / per-profile artifact; raw XML uploaded.
  - No secrets/elevated `permissions` granted to untrusted fork-PR code beyond what rendering requires.
- **Touched files / artifacts**: `.github/workflows/e2e-smoke.yml`, `.github/workflows/e2e-nightly.yml`
- **Specialist**: `fullstack-developer`
- **Depends on**: P1 (XML must exist at a known path)

### P3 — Traceability & developer docs

- **Problem statement**: the E2E README documents the protocol/TC-ID channel but not the new JUnit-report + CI-render pipeline.
- **Acceptance criteria**: `tests/e2e/README.md` (and any CI-docs page it points to) documents where the JUnit XML is written, how it is rendered per PR / per nightly profile, and that the TC-ID lands as a `user_property`. DE/EN parity respected where the docs are mirrored.
- **Touched files / artifacts**: `tests/e2e/README.md` (+ mkdocs page if one mirrors it)
- **Specialist**: `mkdocs-documentation`
- **Depends on**: P1, P2

## Dependency ordering

P1 → P2 → P3

## Risks

- **Fork-PR token permissions (security-sensitive path)**: render/annotation actions and `upload-artifact` on `pull_request` from forks have a restricted token; a naive `pull_request_target` or broad `permissions:` grant would be a privilege-escalation vector. → P2 must keep least-privilege `permissions:` and avoid `pull_request_target` with untrusted checkout. **`security-review` skill + `code-security-reviewer` on the diff are REQUIRED before the PR opens** because the change touches `.github/workflows/`.
- **xdist + protocol-plugin interaction**: built-in `--junitxml` is xdist-aware, but the bespoke `optionalhook` protocol plugin must not shadow `record_property`. → P1 verifies a single merged XML with the `tc_id` property present and `protokoll.md` intact by running `scripts/run-e2e.sh --smoke` locally if the environment allows, else documents the manual verification path.
- **Report-dir move race**: `run-e2e.sh` finds the container report dir by `-newer`; the XML must be written *inside* that dir (not a sibling) so the existing `cp -r` picks it up. → P1 writes the XML under the container report dir.
- **Action pinning**: third-party render actions must be pinned by commit SHA (repo convention, e.g. `actions/*` already SHA-pinned). → P2 pins by SHA.

## Open questions

- none (render-action choice left to the specialist per the issue's decision criteria; both `dorny/test-reporter` and `EnricoMi/publish-unit-test-result-action` satisfy the criteria — specialist picks and justifies).

## Verify log

- 2026-07-24 `nolte-engineering:code-security-reviewer` on the diff — CLEAN. No Critical/High/Medium across all 6 CI-supply-chain/privilege categories: least-privilege tokens (`checks: write`, no `pull-requests: write`, no `write-all`), no `pull_request_target`, full-SHA action pinning, injection-free `github-script` (only trusted `context`/`env`/API values in the issue body), `run-e2e.sh` glob safe, `atexit` relocation uses `source.name` only (no path traversal). Info notes only: SHA↔tag offline-unverifiable (dorny `@a43b3a5f…` already confirmed via `gh api` in P2); pre-existing test-secrets in compose (declared non-prod); cosmetic fork-controlled markdown in job summary (read-only token, no exec).
- 2026-07-24 Local gate — CI ruff runs `working-directory: src/backend` so `ruff check/format .` never covers `tests/e2e/`; E402/format noise seen was default-config artifact on a non-ruff-managed file, not from P1 (P1 additions clean). YAML valid on all 3 changed YAML files; `actionlint 1.7.7` PASS on both workflows (P2); `mkdocs build --strict` exit 0 (P3). conftest change's real gate is the `e2e-smoke` run triggered on the PR.

## Dispatch log

- 2026-07-24 P1 dispatched to `fullstack-developer` — DONE. `--junitxml=junit-<profile>.xml` on all runners (8, incl. `e2e-core-crud` added for consistency) in `docker-compose.e2e.yml`; protocol plugin relocates the static XML into the timestamped report dir via `atexit` (controller-only xdist guard); `run-e2e.sh` echo updated (drift-free glob). Verified empirically with real `conftest.py`/pytest (tc_id property present, idempotent, worker-guarded); full `run-e2e.sh --smoke` NOT run (expensive full stack) — manual verification steps documented in artifact. Uncommitted. Per-profile files for P2: `junit-{default,smoke,full,mobile,tablet,full-mobile,full-tablet,core-crud}.xml` in `test-reports/e2e/<ts>/`.
- 2026-07-24 P2 dispatched to `fullstack-developer` — DONE. `dorny/test-reporter@a43b3a5f7366b97d083190328d2c652e1a8b6aa2 # v3.0.0` in `e2e-smoke.yml` + `e2e-nightly.yml`; `checks: write` least-privilege (no `pull-requests: write`, no `pull_request_target`); render step `if: always()` + `continue-on-error: true` + `fail-on-error/empty: false` for fork-PR safety; nightly `github-script` now lists per-profile check runs (`checks.listForRef`) and links them into the failure issue body + dedup comment; raw XML already in existing `test-reports/e2e/` artifacts. Verified: yaml OK, `actionlint 1.7.7` PASS on both, SHA pin resolved via `gh api`. Uncommitted. **Security-review flagged by specialist** (workflow `permissions`, third-party action, fork behaviour) → will run `code-security-reviewer` + `security-review` in verify phase.
- 2026-07-24 P3 dispatched to `mkdocs-documentation` — DONE. `tests/e2e/README.md` (EN) + `docs/{de,en}/development/testing/index.md` + `docs/{de,en}/development/testing/stufen/e2e.md` (DE canonical + EN mirror, matching headings) document the JUnit-XML location/naming, dorny render (check-run + job-summary), least-privilege, fork-PR caveat, tc_id property; also fixed a pre-existing `test-reports/<ts>/` → `test-reports/e2e/<ts>/` path drift. Verified with isolated `mkdocs build --strict` (exit 0, no new warnings). No nav changes. Uncommitted.
