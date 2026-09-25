# Issue #1794 — pre-analysis

- Issue: #1794 (author nolte, repository owner — trusted), label `cicd`
- Classification: `infra` (CI lifecycle change, not a red run → not routed to workflow-health-triage); secondary `spec-change` (NFR-018 §4.3)
- Requirements gate: operator override — the operator's brief of 2026-09-25 states the decision and the design; no `project/requirements/` artefact.
- Route: implement directly (one outcome, one PR strand, no roadmap item).

## Measured before the first change (claim provenance)

- Established: the manifest guard is already `advisory` and deselected by the required guards lane (`-m 'not advisory'`, backend-guards.yml:278); it still runs in `task test:backend:unit` (backend.yml lint-test, advisory) — that is the feature-PR run to remove it from.
- Established: `lane-inputs.yml` triggers on `pull_request` with paths `.github/workflows/**` etc. (lane-inputs.yml `on:`).
- Established: `lane-inputs--{plan,record,compare}.yaml` exist only because lane-inputs.yml is `on:`-path-filtered; without the `pull_request` trigger the workflow has no filter.
- Established: `vars.PORTFOLIO_APP_ID` and `secrets.PORTFOLIO_APP_PRIVATE_KEY` exist (`gh variable list`, `gh secret list`); `automerge.yaml` merges `automerge`-labelled non-Renovate PRs with an App token.
- Established: `compare` byte-differs every run (`replay_seconds`, inside-filter reads), so "manifests differ" MUST be compare's verdict, not a byte diff.

## Work packages

| id | problem | acceptance | files | specialist |
|----|---------|-----------|-------|------------|
| P1 | real-tree manifest checks run on feature PRs | marker `lane_inputs_drift`, deselected unless `--lane-inputs-drift`; synthetic tests stay | guard test, tests/conftest.py, pyproject.toml | generalist (operator brief) |
| P2 | lane runs on PRs; no bot PR | schedule+dispatch only; guard job; propose job with App token on develop only | lane-inputs.yml, lane_inputs.py | generalist |
| P3 | manifests of the lane's own jobs | delete lane-inputs--*.yaml; adjust recorder test | .github/lane-inputs, recorder test | generalist |
| P4 | docs/spec | NFR-018 §4.3, docs ci-cd DE/EN, NFR-009/renovate comment, backend-guards comment | | generalist |

No matching specialised agent was dispatched — generalist remediation under the operator's brief.
