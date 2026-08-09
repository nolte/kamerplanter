# Pre-Analysis — Issue #1058

- **Issue:** #1058 — Side services run zero tests in CI (knowledge-service, inference-service, kp_vectordb)
- **Labels:** cicd, backend, test
- **State:** open · **Author/trust:** nolte (trusted); no embedded commands to execute.
- **Run:** issue-orchestrate, 2026-08-09

## Classification

- **Primary:** `infra` — a CI-coverage-authoring gap (existing test suites executed by no workflow). This is NOT a red-workflow / CI-failure issue, so the `workflow-health-triage` short-circuit does **not** apply (that skill triages failing runs; this authors new coverage).
- **Secondary:** `test`.

## Scope

**In scope (grounded):** three test suites present on develop but run in no workflow —
`src/knowledge-service/tests/` (5), `src/inference-service/tests/` (10), `src/libs/kp_vectordb/tests/` (3); each has its own `pyproject.toml`. Only image-build workflows touch these paths. Deliverables: a PR-triggered workflow that executes each suite; `task check` wiring; fail-on-empty-collection; update the stale gap-describing comments; extend `check_utc_calendar_day.py` scope after the suites run; record the advisory→required decision.

**Out of scope:** `kp_errortracking` (copy-sync only, no suite); the frontend; changing the suites' contents; promoting the lanes to required now (advisory first).

## Route

**Direct** — bounded: one coherent outcome (wire side-service tests into CI), one PR strand, no roadmap item. The issue carries a concrete proposal + acceptance criteria.

## Requirements gate

No `project/requirements/` artefact. **Operator override:** the issue is fully specified with measured current state and acceptance criteria (trusted author); `requirements-elicit` not warranted.

## Operator decisions (2026-08-09)

- **Structure:** a new dedicated workflow **`side-services.yml`** with one job per service + per-service `paths` filters (not a matrix in backend.yml).
- **Gate status:** **advisory** start (not required); promote later on measured stability per NFR-018 §4.

## Work packages

| id | problem | acceptance | files | specialist | deps |
|----|---------|-----------|-------|------------|------|
| WP-1 | Side-service suites run in no workflow; author `side-services.yml` (job per service, paths filters, fail-on-empty-collection), wire `task check`, update the stale gap comments, extend the UTC gate scope after the suites run, record advisory→required decision. | Each suite is executed by a PR-triggered job with correct paths filters; a zero-collection suite fails its job (negative control shown once); `task check` runs the suites (missing tool ⇒ FAIL); `errortracking-sync`/`check_utc_calendar_day.py` gap comments updated; advisory decision recorded (NFR-018 §4). Workflow follows github-actions-best-practices (digest-pinned actions, least-privilege `permissions`, concurrency). | `.github/workflows/side-services.yml` (new), `Taskfile.yml`/`task check`, `scripts/…/check_utc_calendar_day.py`, `.pre-commit-config.yaml` comment | `cicd-pipeline-design` (skill) | — |

## Risks

- **inference-service tests may be heavy** (model downloads). Split a unit tier (no model) that actually runs from an optional/heavy tier; the unit tier must not be silently skipped.
- **fail-on-empty-collection** must be real (pytest `--co -q` count guard or `-p no:cacheprovider` + exit-code check), per NFR-018 §2 — a suite that collects nothing must go red, not green.
- Advisory lanes must not be wired into branch-protection required checks now.

## Open questions

None — structure and gate-status are operator-decided above.
