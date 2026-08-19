# Requirements — Delivery-lane run observer (`workflow_run` alert on docker-publish.yml)

<!--
Produced as the requirements gate of the `issue-orchestrate` skill for issue
#1225, following spec/project/requirements-elicitation/ (authoritative source at
claude-shared/spec/project/requirements-elicitation/en.md).

OPERATOR OVERRIDE, RECORDED: no funnel interview was conducted. The run was
autonomous and the issue body — authored by the repository owner, who is the
operator — already states the problem, the measured evidence, the scope boundary,
the shape, the sibling contract to follow and the test fixtures. Per the spec, an
authoritative operator answer confirms a requirement; every requirement below
cites the sentence of #1225 (or the sibling artefact) it is read from. `c_d` is
an uncertainty proxy, not a calibrated probability.
-->

- **Working copy / branch:** `fix/ci-delivery-lane-observer` (off `origin/develop` @ `3e76232f2`)
- **Trigger:** issue [#1225](https://github.com/nolte/kamerplanter/issues/1225) — work package **P3** of #1218's approved plan, deferred out of PR #1224 by operator decision
- **Governing constraints:** NFR-003 (source & GitHub-facing content in English), NFR-018 §2 (fail loud: an undetermined check is not a clean check), `spec/project/github-actions-best-practices/` (digest-pinned actions, least-privilege permissions, fixed concurrency group for alerting jobs)

## Bounded context

- **What:** an observer of `.github/workflows/docker-publish.yml` (workflow name `Build & Publish Container Images`) that turns a **red** completed run of that workflow into something a human sees: one deduplicated, labelled GitHub issue that is opened/updated on a red run and closed when the lane is demonstrably healthy again.
- **Why it matters now (measured, #1225 §Measured):** `publish-helm-charts` failed on 2026-08-13 (run 31729355999, tag `v0.2.0`), 2026-08-16 (31955164085, `develop`) and 2026-08-16 (31955579431, `develop`). Each run is red in the Actions tab; each went unnoticed for five days. `grep -rl "workflow_run" .github/workflows/` returns nothing on `origin/develop` (re-measured 2026-08-19).
- **For whom:** the repository maintainer(s) — the only people who can act on a red delivery run.

## Requirements

| ID | Requirement | Source | c_d | Status |
|----|-------------|--------|-----|--------|
| R1 | The observer is a `workflow_run` workflow (`types: [completed]`) on `Build & Publish Container Images`, so it runs after every delivery run regardless of how that run was triggered (push to `develop`, `v*` tag, `workflow_dispatch`). | #1225 §Shape "A `workflow_run` observer on the delivery lane"; `docker-publish.yml` `on:` block | 0.95 | confirmed (operator text) |
| R2 | A red delivery run (`conclusion == failure`, plus the equivalent hard conclusions `timed_out`, `startup_failure`) opens — or updates, never duplicates — **one** issue carrying a dedicated label; the issue body names the run, its trigger (branch/tag), and every job that failed. | #1225 §Shape "alerts through one deduplicated issue"; sibling `release-assets-complete.yml` dedup anchor | 0.9 | confirmed |
| R3 | Fail-loud contract: an unreachable API, an unparseable run/jobs payload, an unknown `run_id`, or a run that is not yet `completed` makes **the observer run red and opens no issue** (NFR-018 §2). A determined verdict writes a report file that gates the issue step. | #1225 §Shape "write a report file that gates the issue step, and go red rather than silent when a result is undetermined (NFR-018 §2)" | 0.95 | confirmed |
| R4 | The check logic lives in a standalone Python script under `scripts/ci/` with an **injected HTTP layer and clock**, mirroring `check_release_lag.py` / `check_release_assets.py`, and is unit-tested from `src/backend/tests/unit/` via `tests.support.repo_scripts` against constructed payloads — no network in tests. | #1225 §Shape "Both inject their HTTP layer and clock"; sibling test docstrings | 0.9 | confirmed |
| R5 | A `workflow_dispatch` input `run_id` lets the observer be pointed at a historical run; the three measured red runs (31729355999, 31955164085, 31955579431) and a measured green run that *executed* the chart job (32259216513, tag `v0.2.1`, 2026-08-19) are the fixtures the unit tests replay. | #1225 §Shape "The plan recommended a `run_id` dispatch input … the three listed above are available as fixtures" | 0.9 | confirmed |
| R6 | **Closing must not flap on a skipped job.** `publish-helm-charts` runs only on `helm/**` changes, a `v*` tag or dispatch; on every other `develop` push it is *skipped*, and a skipped job reports success (#1225 "the lane reads green most of the time and the red runs look intermittent"). A green run therefore resolves the alert only if every job recorded as failed in the open alert actually **ran and succeeded** in that run (not skipped). A green run that skipped them leaves the alert open and says so. | #1225 §Measured, second bullet; sibling "closing keyed on `resolved`, never on `!alert`" | 0.8 | confirmed (derived — the specialist may refute with a simpler mechanism that still cannot flap) |
| R7 | Permissions are least-privilege (`actions: read`, `issues: write`, `contents: read`), actions are digest-pinned to the same SHAs the siblings use, and the job uses a fixed, non-cancelling concurrency group. | `spec/project/github-actions-best-practices/`; sibling workflows | 0.95 | confirmed |
| R8 | `release-assets-complete.yml` and `check_release_assets.py` already refer to the observer as **`delivery-run-alert.yml`** ("did the delivery run go red?"); the new workflow takes that file name so the existing cross-references become true. | `release-assets-complete.yml` header line 5; `check_release_assets.py` docstring | 0.95 | confirmed |

## Out of scope

- The *cause* of the chart-job failure and the outcome check on release artefacts — already delivered by #1224.
- `needs.changes.result` not being consulted by the build jobs — #1223, a different silent path.
- Observing any workflow other than `docker-publish.yml` (the observer is written so a second workflow name could be added to `workflows:` later, but none is).
- Label creation (`issues.create` creates a missing label implicitly; colour/description are a manual follow-up, as noted on PR #1224).

## Gap matrix (surviving assumptions)

| Dimension | Assumption | Falsified by |
|-----------|------------|--------------|
| Conclusion set | `cancelled` is neither alert nor resolve (an operator act, not a lane failure); `skipped`/`neutral` likewise. | A cancelled run hiding a real failure — revisit if observed. |
| Dedup key | One label (`delivery-run-failed`), at most one open issue. | Two concurrent red runs — serialised by the concurrency group. |
| Resolution memory | The failed-job set is carried in the alert issue body inside an HTML-comment marker the closing step parses. | Manual edits to the body removing the marker → closing step falls back to "leave open, ask human". |
