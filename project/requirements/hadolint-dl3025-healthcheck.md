# Requirements — hadolint DL3025/DL3066 Dockerfile conformance

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/ (authoritative source at
claude-shared/spec/project/requirements-elicitation/en.md).
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back
or an authoritative operator answer.
-->

- **Working copy / branch:** `fix/hadolint-dl3025-healthcheck` (off `origin/develop` @ `e83060165`)
- **Plan:** `.resume/hadolint-dl3025/plan.md`
- **Trigger:** CI job "Lint backend Dockerfile", run
  [30703377601](https://github.com/nolte/kamerplanter/actions/runs/30703377601)
- **Governing constraints:** NFR-003 (source & GitHub-facing content in English),
  NFR-018 §1 (a check that looks pinned but isn't; do not weaken a gate to make
  it pass)

## Bounded context

- **What:** Make the `hadolint` job in `.github/workflows/docker-lint-build.yml`
  green again by bringing every Dockerfile into conformance with hadolint
  **v2.15.0** at `--failure-threshold info`, **without weakening the gate**. The
  fix is notational, not behavioural: shell-form `HEALTHCHECK … CMD` becomes JSON
  (exec) notation, and the non-numeric `USER root` becomes the numerically
  identical `USER 0`. The branch additionally closes the coverage gap that hid a
  seventh finding: `src/inference-service/Dockerfile` has **no** lint step in the
  workflow at all.
- **Why it matters now:** the `hadolint` job is a `needs:` predecessor of all
  seven `build-*` jobs. While it is red, **no image builds** — every open Renovate
  PR is blocked. The failure is repo-wide, not PR-specific: the Dockerfiles have
  not changed since #641; the linter did.
- **Root cause (measured):** `.github/workflows/docker-lint-build.yml` pins
  `hadolint/hadolint-action` by SHA (= v3.4.0), which pins the *wrapper*; that
  action's own `Dockerfile` reads `FROM ghcr.io/hadolint/hadolint:v2.15.0-debian`,
  so the *linter* is unpinned. hadolint 2.12.0 and 2.14.0 report nothing on these
  files; v2.15.0 reports the findings below, because DL3025 began flagging
  `HEALTHCHECK … CMD <shell form>` in 2.15.0.
- **For whom:** the repository's CI (the blocked merge train and its Renovate
  PRs), and anyone operating the containers — the health checks must keep
  reporting `unhealthy` exactly as before.
- **Explicitly out of scope:** pinning the hadolint *version* (Q2 — follow-up
  issue referencing NFR-018 §1, operator decision); lowering
  `failure-threshold`; any change to runtime `USER`/UID semantics; any
  application-code, dependency, or image-content change.

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question
  budget = `3` (spec defaults; the requirement arrived code-grounded — the
  finding inventory was measured against the exact CI image before the interview
  opened — so only the three recorded open questions carried real specification
  uncertainty, and two of them were tightly coupled into one turn).
- `U_gate = min_d c_d` over required dimensions = **0.88**
- Termination: `saturation` (every required dimension ≥ `τ_high`; two decision
  turns resolved all three open questions; no remaining candidate question has
  positive net EVPI). Question budget was not reached — 2 of 3 turns used.

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.95 | interpretation | Full sweep with `ghcr.io/hadolint/hadolint:v2.15.0-debian --failure-threshold info` over all eight Dockerfiles reproduced the exact finding set (6 in-workflow + 1 unlinted); every finding maps to one mechanical notation change |
| `non_functional` | yes | 0.90 | interpretation | Behaviour preservation is the bar, not a green linter: each `HEALTHCHECK` must still exit non-zero on an unhealthy service (plan invariant, verified by step 5) |
| `constraints` | yes | 0.95 | specification→resolved | Do not lower `failure-threshold` (NFR-018 §1); do not change runtime `USER`/UID semantics (UID 1000 ↔ `fsGroup:1000`, the `backend-attachments` PVC-503 incident); verify only against `v2.15.0-debian`, never `hadolint:latest` (2.14.0 reports nothing and would falsely signal success) |
| `domain_objects` | yes | 0.95 | interpretation | Enumerated from source: 7 linted Dockerfiles + 1 unlinted; 6 shell-form `HEALTHCHECK … CMD` blocks (2× `curl`, 4× `python -c`); 1 `USER root`; the `hadolint` job's per-file lint steps |
| `actors` | yes | 0.90 | interpretation | CI (`hadolint` job gating seven `build-*` jobs), the blocked Renovate PRs, and container operators reading health state |
| `acceptance_criteria` | yes | 0.90 | specification→resolved | Zero findings across **all eight** files under the exact CI image; backend prod container reaches `healthy`; `src/inference-service` has a lint step; no threshold or `USER`-semantics change in the diff |
| `edge_cases` | yes | 0.88 | interpretation | `DL3066` is *info*-level but the job runs at `failure-threshold: info`, so fixing only DL3025 leaves the job red; the `python -c` payloads use single-quoted `'127.0.0.1'` internally and therefore embed in a JSON string without escaping; the CI log understates the damage because the job aborts on its first failing step |
| `scope_boundaries` | yes | 0.90 | specification→resolved | Q3 answered authoritatively: fix `src/inference-service` *and* add its lint step in this branch. Q2 answered authoritatively: linter pinning is a follow-up issue, not this diff |

_Self-consistency (`k≥2`) evidence event:_ two independent sketches for DL3066 /
`USER root` diverged — sketch A treated it as a **notation** defect (`USER 0`,
semantically identical since root *is* UID 0, fixing it on the same line as the
DL3025 changes) versus sketch B as a **suppression** case
(`# hadolint ignore=DL3066` retaining the existing rationale comment). The
divergence put `c_d` below `τ_low`, making the clarification mandatory rather
than discretionary; the operator selected sketch A against the rendered code
preview (teach-back on the artifact itself).

_Withheld clarification (discretionary-zone restraint):_ the exact JSON shape of
the `curl` health check — whether to keep `--fail`/`-f` long-form, and whether to
preserve `|| exit 1` inside a `/bin/sh -c` wrapper — was **not** asked. `curl -f`
already exits non-zero on an HTTP error status, Docker treats every non-zero exit
as `unhealthy` identically, and the operator had already rejected the shell-wrapper
form when the plan's design decision was agreed. EVPI did not exceed the cost of
one more turn.

## Requirements

- **R1** — WHEN the `hadolint` job lints a Dockerfile containing a
  `HEALTHCHECK`, the Dockerfile SHALL express that health check's command in JSON
  (exec) notation, so that hadolint v2.15.0 reports no DL3025 finding.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: plan design
    decision, "Convert each HEALTHCHECK to JSON (exec) notation" (operator-agreed)
- **R2** — WHEN a `curl`-based health check is converted to JSON notation, the
  Dockerfile SHALL drop the trailing `|| exit 1`, because `curl -f` already exits
  non-zero on an HTTP error status and Docker treats every non-zero exit as
  `unhealthy` identically.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: plan design
    decision rationale (operator-agreed over the `/bin/sh -c` wrapper form)
- **R3** — WHEN a converted health check runs against an unhealthy service, the
  container SHALL still be reported `unhealthy` — behaviour preservation is the
  acceptance bar, not a green linter.
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: plan
    invariant, "Behaviour preservation is the bar, not a green linter. Step 5 is
    not optional."
- **R4** — WHEN `src/frontend/Dockerfile` switches to the root user for the asset
  `chown`, it SHALL name that user by its numeric UID (`USER 0`) rather than the
  non-numeric `USER root`, so that hadolint reports no DL3066 finding, and the
  final runtime user SHALL remain `USER 101` unchanged.
  - _dimension_: `functional`, `constraints` · _status_: `confirmed` · _source_:
    Q1 answer, "USER 0 statt USER root" selected against the rendered preview
- **R5** — WHEN the `hadolint` job runs, it SHALL lint
  `src/inference-service/Dockerfile` as well, and that Dockerfile SHALL satisfy
  R1 — closing the coverage gap that currently hides a measured DL3025 finding at
  line 62.
  - _dimension_: `functional`, `scope_boundaries` · _status_: `confirmed` ·
    _source_: Q3 answer, "Jetzt mitfixen"
- **R6** — The change SHALL NOT lower `failure-threshold`, add a repository-wide
  `.hadolint.yaml` ignore for DL3025/DL3066, or otherwise weaken the gate;
  findings are fixed, not suppressed.
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: plan
    invariant referencing NFR-018 §1
- **R7** — The change SHALL NOT alter `USER`/UID semantics in any Dockerfile
  beyond R4's notation change, because UID 1000 matches the deployment's
  `fsGroup:1000` (attachments-PVC writability).
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: plan
    invariant, `backend-attachments` PVC-503 incident
- **R8** — WHEN verifying the fix locally, the sweep SHALL run against
  `ghcr.io/hadolint/hadolint:v2.15.0-debian` at `--failure-threshold info`, never
  `hadolint:latest`, which is 2.14.0 and reports nothing on these files.
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: plan
    "The verification command" and its "the image tag is load-bearing" note
- **R9** — WHEN the fix is complete, the sweep SHALL report zero findings across
  **all eight** Dockerfiles (the seven previously linted plus
  `src/inference-service`).
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_:
    plan step 4 widened by the Q3 answer
- **R10** — The unpinned-linter root cause SHALL be recorded as a follow-up issue
  referencing NFR-018 §1 rather than fixed in this branch, so the pull request
  stays a reviewable notation-only diff.
  - _dimension_: `scope_boundaries` · _status_: `confirmed` · _source_: Q2
    answer, "Folge-Issue mit NFR-018-Bezug"

## Surviving assumptions / open risks

- **Risk (accepted, R10):** until the follow-up issue is acted on, the linter
  version remains unpinned behind a SHA-pinned action, so hadolint 2.16.0 can
  turn the job red again without any repository change. This is the NFR-018 §1
  failure class and is knowingly deferred, not resolved.
- **Assumption (unconfirmed, low impact):** `USER 0` and `USER root` resolve to
  the same effective user *and* primary group in `nginxinc/nginx-unprivileged`,
  making R4 semantically inert. Grounded in the images carrying a standard
  `/etc/passwd` where root is UID 0/GID 0, and in the fact that only `COPY` and
  `RUN chown -R 101:101` execute between the switch and `USER 101`. Not
  separately verified inside the image; the frontend image build in the quality
  gate is the check that would surface a divergence.
- **~~Assumption~~ (resolved):** the four `python -c` health checks need no
  escaping when embedded in a JSON string. Proven: the built image's
  `Config.Healthcheck.Test` parses to exactly
  `["CMD","python","-c","import socket,sys; … s.connect_ex(('127.0.0.1',8000)) …"]`
  — three argv elements, single quotes intact — and the check reaches `healthy`
  (exit 0) with a listener and `unhealthy` (exit 111, ECONNREFUSED) without one.
- **Residual coverage note:** R3 was verified on the `curl` form against the real
  backend prod image (exit 0 → `healthy`; exit 22 on HTTP 503 → `unhealthy`;
  exit 7 on connection refused → `unhealthy`) and on the `python -c` form by
  grafting the verbatim instruction onto that image. The remaining three
  `python -c` checks differ only in port number and are not each built and
  observed individually — a deliberate cost decision, not an oversight.
