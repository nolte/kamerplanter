---
artifact-type: issue-orchestration-analysis
repo: nolte/kamerplanter
issue: 1210
classification: bug
secondary-classes: [infra]
route: direct
status: draft
created: 2026-08-17
---

# Issue Orchestration — Pre-analysis

<!-- Run-scoped artifact: committed on the run's feature branch, then removed with a
     fix-forward `git rm` before the PR merges, per spec/project/issue-orchestration/
     §Pre-analysis artifact lifecycle. -->

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #1210 — "The #1163 MCP fix has not reached the running instance: assign_nutrient_plan and get_mcp_activity still 500 two days after merge, with no release cut"
- **URL**: https://github.com/nolte/kamerplanter/issues/1210
- **Labels**: bug, release, backend, deployment
- **Linked items**: #1145 (the two MCP defects, analysed), #1163 (the merged fix), #1164 (opaque MCP 500s), #1026 (chart-image-digest freshness job), #1024/#1025/#987 (digest pinning), #1173 (overlay tag-override note), #1180 (`supported_majors`)
- **Prior art checked**: `docs/de/deployment/ci-cd.md` §"Deployment und Rollback" (already documents the digest mechanism — and states one fact that is **refuted** below); `.github/workflows/chart-image-digest-freshness.yml` + `scripts/ci/check_digest_freshness.py` (already close the pin-vs-registry half of AC-6); `helm/kamerplanter/values.yaml:81-121` (the image-pinning rationale); no open pull request references #1210 (`gh pr list --state open --limit 15`, 2026-08-17 — only Renovate PRs #1213–#1215). No `project/features/` entry and no roadmap item covers delivery visibility.

## Requirements gate — explicit operator override

No artifact exists under `project/requirements/` for this issue. The operator recorded an
explicit override, reproduced verbatim:

> the issue's six acceptance criteria are testable and the root cause has been measured
> rather than assumed.

Planning proceeds on that override. The measured grounding is recorded under
§Established facts below; each load-bearing claim names the observation behind it, per
`spec/claude/claim-provenance/`.

## Classification

- **Primary class**: bug
- **Secondary class(es)**: infra
- **Rationale**: a merged fix is not being served by the running instance (a defect in the
  delivery path, not in application code), and the remedy is build/CI/deployment plumbing.

## Established facts

Everything in this section was measured on 2026-08-17. The issue's own causal claim is
refuted; the plan is built against what was found instead.

### CONFIRMED — the issue's stated cause was right, and an earlier entry here was wrong

**This section previously claimed the opposite. That claim was a measurement error and is
retracted in full.**

The retracted claim: that the ArgoCD `Application` tracks `targetRevision: develop`, and
that a published release is therefore not on the instance's delivery path. It was derived
from the **local working copy** of
`argo-charts/src/applications/kamerplanter/deploy/argocd/application.yaml`, which held an
**unpushed** change — now `nolte/k8s-home-lab` PR #837. ArgoCD reads GitHub, not a local
checkout.

- **ESTABLISHED** (`git show origin/master:src/applications/kamerplanter/deploy/argocd/application.yaml`
  in `~/repos/github/argo-charts`, remote `git@github.com:nolte/k8s-home-lab.git`): the
  ref ArgoCD actually reads pins `path: helm/kamerplanter`,
  `repoURL: https://github.com/nolte/kamerplanter.git`, **`targetRevision: v0.1.0`** —
  a release tag — plus six per-controller `tag: "0.0.23"` overrides.
- **ESTABLISHED** (operator, 2026-08-17): production rolls out **release versions only**.
  This is intended, and PR #837's `targetRevision: develop` half is rejected on that basis.
- **Therefore the issue's own diagnosis holds**: `v0.2.0` was published 2026-08-13T18:09Z,
  `#1163` merged 2026-08-14T20:50Z — after it — and `v0.2.1` was never published. With
  production anchored to a release tag, an unpublished release *is* the blocker.
- The instance runs image `0.0.23` under a `v0.1.0` chart, because the overlay's tag
  overrides win over the chart's pins. That is why `/api/health` lacks `supported_majors`
  (added 2026-08-15) — the running image predates it by roughly a month.

**The `image.tag` override remains a genuine defect even under release tags.** At release
time `scripts/ci/pin_chart_image_digests.sh` writes `<version>@sha256:<digest>` into the
chart values; a per-controller `image.tag` override replaces that digest with a mutable
tag, and `pullPolicy: IfNotPresent` then degrades to "keep whatever is cached on the node"
— the failure measured in #1024. Operator decision on #837: keep the release tag, remove
the six overrides.

**Method note, recorded so the error is not repeated:** when a load-bearing fact lives in
another repository, measure the ref the consumer actually reads (`origin/<branch>`), never
the local working tree.

### ESTABLISHED — the actual root cause, and that it is still live

- The chart pins image **bytes** by digest (`tag: latest@sha256:…`), documented at
  `helm/kamerplanter/values.yaml:81-121`; `pullPolicy: IfNotPresent` is deliberate and
  safe *because* the reference is content-addressed.
- The ArgoCD overlay carried per-controller `image.tag` overrides, which replace the
  digest with a mutable tag; combined with `IfNotPresent` this degrades to "keep whatever
  is cached on the node". Fixed in argo-charts commit `3e53606c`
  ("fix(kamerplanter): restore the chart's image-pinning invariant in prod"), whose own
  comment cites `nolte/kamerplanter#1210`.
- **The fix was never pushed.** `git status -sb` in `~/repos/github/argo-charts` reports
  `master...origin/master [ahead 3]`; `git log --oneline origin/master..HEAD` lists
  `3e53606c` among the three unpushed commits. ArgoCD reads from GitHub, so it has never
  seen it.
- **The instance is still stale today.** `curl https://kamerplanter.just-a-lab.duckdns.org/api/health`
  at 2026-08-17T17:30Z returned `{"status":"healthy","version":"1.0.0","mode":"light"}` —
  three fields, **no `supported_majors`**. That field was added by `46878ea26` (#1180,
  2026-08-15). The running build therefore predates 2026-08-15.
- **The chart, meanwhile, pins a build that contains both fixes.** The backend pin is
  `sha256:e2b0aec41662…` (`helm/kamerplanter/values.yaml:147`). An anonymous GHCR read of
  that digest returns an OCI image index whose annotations include
  `org.opencontainers.image.revision: 37cbc06fcf0c7d69c07f7abbd3d485cb241070da` and
  `org.opencontainers.image.created: 2026-08-16T14:28:39.211Z`.
  `git merge-base --is-ancestor 796c00474 37cbc06f` → true (contains the #1163 MCP fix);
  `git merge-base --is-ancestor 46878ea26 37cbc06f` → true (contains `supported_majors`).

  **This is the decisive measurement.** The chart pins a build containing the fix; the
  instance does not serve it. The gap is between the pin and the running pod — precisely
  the overlay-override failure — and it is confirmed by measurement, not inferred from
  the argo-charts commit alone.
- **The existing freshness job cannot see this.** `chart-image-digest-freshness.yml` run
  32002642308 (2026-08-17T06:41Z) concluded `success`; it compares the chart pin against
  GHCR `:latest` and is green because the *pin* is current. Its blind spot is the last
  hop: whether the pod runs the pinned bytes.
- Renovate bumped the backend digest in PR #1140, merged 2026-08-16T15:16Z — about three
  hours **after** the issue's 12:00Z measurement, so at measurement time the chart still
  pinned a pre-#1163 backend digest. This is a second, independent contributor and is now
  resolved; it is not the reason the instance is stale today.

### ESTABLISHED — the version constant (the issue's secondary finding is correct)

- `app_version: str = "1.0.0"` is a hardcoded constant at
  `src/backend/app/config/settings.py:24`.
- It is consumed at `src/backend/app/main.py:41` (Sentry `resolve_release`), `:86`
  (startup log), `:168` (mDNS service info), `:198` (`FastAPI(version=…)` → OpenAPI
  `info.version`), `:372` (`/api/health`), and `src/backend/app/tasks/__init__.py:49`
  (worker Sentry release).
- **Consequence for the design**: `app_version` must **not** be repurposed into a build
  identifier. Doing so would rewrite the OpenAPI contract version (and with it the
  `openapi.json` release asset and the API docs) and the mDNS advertisement. The build
  identity has to be a **new, separate** field.
- Nothing bakes a build identity into the image today: `src/backend/Dockerfile` declares
  no `ARG`/`ENV` for a revision, and `.github/workflows/docker-publish.yml` passes
  `labels:`/`annotations:` but no `build-args:` (grep for `build-arg` in that file returns
  nothing).
- `resolve_release` (`src/backend/app/observability/error_tracking.py:192-201`) prefers the
  `SENTRY_RELEASE` env var and falls back to `component@version`. `helm/kamerplanter/values.yaml`
  sets `SENTRY_RELEASE: ""` (lines 201, 514, 601, 774), so today every Sentry event is
  attributed to the fictitious release `kamerplanter-backend@1.0.0`.
- `src/backend/app/observability/error_tracking.py` is a **synced copy**, not a source of
  truth: the SSOT is `src/libs/kp_errortracking/kp_errortracking/error_tracking.py`,
  copied byte-identically into three services and regenerated with
  `python src/libs/kp_errortracking/sync.py` (module docstring, lines 13-21). Any change
  there fans out to `src/inference-service/` and `src/knowledge-service/` as well. This is
  why the Sentry improvement is recorded as a follow-up below rather than folded into a
  package.

### ESTABLISHED — gates and test homes

- `develop` requires exactly two checks:
  `gh api repos/nolte/kamerplanter/branches/develop/protection --jq '.required_status_checks.contexts'`
  → `["static / Static CI Tests","lint-test-build (22)"]`. `static` is the pre-commit lane
  (`.github/workflows/build-static-tests.yaml`); the backend pytest suite
  (`task test:backend:unit`, `.github/workflows/backend.yml:117`) runs but is **not**
  required.
- Repo scripts are already unit-tested from the backend suite via the
  `src/backend/tests/support/repo_scripts.py` loader — see
  `src/backend/tests/unit/test_workflow_gate_integrity_check.py`,
  `test_schema_example_ratchet.py`, `test_utc_calendar_day_check.py`. A new CI script has
  an established, working test home.
- `scripts/check_workflow_gate_integrity.py` runs in the required `static` lane and will
  inspect any new workflow (NFR-018 §2: a check that cannot fail must not exist).
- No workflow currently knows the instance URL (grep for `duckdns`/`INSTANCE_URL`/`STAGING_URL`
  across `.github/workflows/*.yml` returns nothing). `/api/health` is reachable
  anonymously — the curl above used no credentials.

### UNESTABLISHED

- **Whether the frontend, knowledge-service and inference-service images should also
  report a build identity.** Not observed; the ACs speak only about the API answering
  "which build is this". The observation that would settle it: whether a stale
  *frontend* has ever produced a comparable misdiagnosis. Not made; recorded as a
  follow-up, not planned.
- **Whether `publish-helm-charts` failing since 2026-08-16 affects this instance.** The
  operator's finding 9 (run 31955579431: "Attest chart provenance" fails with
  `Error: No credentials found for registry ghcr.io`, while "Push chart to GHCR"
  succeeded) is confirmed as a failure by `gh run list --workflow=docker-publish.yml`
  (two `failure` conclusions on 2026-08-16 at 15:16Z and 15:24Z, `success` before). It is
  **not** on this instance's delivery path, because ArgoCD reads the chart from the git
  branch, not from the OCI chart package. Recorded as a follow-up issue, not a package.

## Scope

- **In scope**: acceptance criteria **3, 5 and 6** of the issue.
  - **AC-3** — the delivery path is written down, correctly: what triggers it, what the
    instance tracks, who cuts a release; including the digest-pin mechanism, the ArgoCD
    `targetRevision: develop` fact, the Renovate write-back, and the image-pinning
    invariant. This includes correcting the refuted statement at
    `docs/de/deployment/ci-cd.md:462` and its EN mirror.
  - **AC-5** — the API reports the actual build, without breaking `supported_majors`
    (#1180), the OpenAPI `info.version`, the mDNS advertisement, or the Sentry
    `resolve_release` consumers.
  - **AC-6** — a merged fix that has not reached the running instance becomes visible to
    someone, closing the last hop the existing freshness job cannot see.
- **Out of scope**:
  - **AC-1 and AC-2** (fix live on the instance; `get_mcp_activity` answering 200) —
    satisfied by pushing argo-charts `3e53606c` to `origin/master`. That is a mutation in
    a **different repository** and the operator has taken it as their own action. No work
    package here.
  - **AC-4** (was v0.2.1 left draft deliberately; what is the intended cadence) —
    recorded by the operator as unresolved; carried in §Open questions. No work package.
  - **The broken chart provenance attestation** (finding 9) — recommend a follow-up
    issue; not a package here, and not on this instance's delivery path (see
    §UNESTABLISHED).
  - **Build identity for the frontend and side services**, and **feeding the new build
    identity into `resolve_release`** — both are follow-ups (see §Follow-ups), because
    neither is required by AC-3/5/6 and the second fans out across three services via the
    `kp_errortracking` sync.

## Route

- **Decision**: direct
- **Rationale**: one coherent outcome — *make the deployed build legible and delivery
  drift visible* — deliverable as a single PR strand, with no new roadmap item. Recorded
  by the orchestrator.

## Declared contract (so P1 and P3 can proceed concurrently)

To keep the packages independently dispatchable, the response contract is fixed **here**
rather than discovered during implementation:

```jsonc
GET /api/health  →  200
{
  "status": "healthy",
  "version": "1.0.0",              // unchanged: the app/API version (OpenAPI info.version)
  "mode": "light",
  "supported_majors": [1],         // unchanged: #1180 negotiation input
  "build_revision": "37cbc06fcf0c7d69c07f7abbd3d485cb241070da"   // NEW — or "unknown"
}
```

- `build_revision` is the **full 40-character git SHA** the image was built from, baked
  into the image at build time.
- When nothing set it (local checkout, `--target dev`, a compose run of an unbaked image)
  the value is the literal string `"unknown"`. It is never fabricated and never derived
  from `app_version`.
- Settings field `build_revision`, environment variable `BUILD_REVISION`
  (`model_config = {"env_prefix": ""}`, `src/backend/app/config/settings.py:623`, so the
  field name maps directly — same convention as `app_version` ← `APP_VERSION`).

## Work packages

### P1 — Bake the build revision into the backend image and report it from `/api/health`

- **Problem statement**: the running instance cannot say which build it is, so a
  "did my fix arrive?" question can only be answered by re-triggering the defect. The
  version it does report (`1.0.0`) is a constant that matches no release ever published.
- **Acceptance criteria** (all testable):
  1. `GET /api/health` against an image built by `docker-publish.yml` returns
     `build_revision` equal to the commit SHA that produced it.
  2. With `BUILD_REVISION` unset or empty, `GET /api/health` returns
     `build_revision: "unknown"` — asserted by a unit/API test that sets no env var.
  3. The response still carries `status`, `version`, `mode` and `supported_majors` with
     unchanged values; `src/backend/tests/api/test_api_major_discovery.py` passes
     untouched in substance (`supported_majors == [1]`).
  4. `FastAPI(version=…)` / OpenAPI `info.version` and the mDNS service info still report
     `settings.app_version`, not the revision — asserted by a test reading
     `app.openapi()["info"]["version"]`.
  5. `resolve_release` behaviour is unchanged: `SENTRY_RELEASE` still wins, the fallback
     is still `component@app_version`. Existing tests in
     `src/backend/tests/unit/observability/test_error_tracking.py` pass unmodified.
  6. The `ARG`/`ENV` pair sits **after** the dependency-install and `COPY . .` layers in
     the `prod` stage, so a changed revision does not invalidate the pip layer cache —
     verified by inspecting the stage order in the Dockerfile diff.
  7. A falsification check: reverting only the `build-args:` line in `docker-publish.yml`
     makes criterion 1 fail (the value must come from the build, not from a default).
- **Touched files / artifacts**:
  - `src/backend/Dockerfile` (`ARG BUILD_REVISION=""` + `ENV BUILD_REVISION=${BUILD_REVISION}` in the `prod` stage, placed last)
  - `.github/workflows/docker-publish.yml` (backend build step: `build-args: BUILD_REVISION=${{ github.sha }}`)
  - `src/backend/app/config/settings.py` (new field `build_revision: str = ""`)
  - `src/backend/app/main.py` (health payload; **not** the `FastAPI(version=…)` argument)
  - `src/backend/tests/api/test_api_major_discovery.py` or a sibling test module
- **Specialist**: `fullstack-developer` (project-local `.claude/agents/fullstack-developer.md`).
  Description match: "Features implementiert, APIs erstellt … Helm-Charts erstellt …
  bestehender Code refactored", tags `[implementation, backend, frontend, fullstack]`.
- **Depends on**: none

### P2 — Alert when the running instance does not serve the digest the chart pins

- **Problem statement**: `chart-image-digest-freshness.yml` closes the GHCR→chart-pin hop
  and is green today, while the instance runs a build from before 2026-08-15. Nothing in
  the repository can see the chart-pin→running-pod hop, which is exactly where this
  incident lives.
- **Acceptance criteria** (all testable):
  1. A scheduled workflow resolves, in one run: (a) the backend digest pinned in
     `helm/kamerplanter/values.yaml`, (b) that digest's
     `org.opencontainers.image.revision` annotation from GHCR, and (c) `build_revision`
     from `GET <instance>/api/health`.
  2. When (b) and (c) are equal, the run exits 0, opens no issue, and closes an existing
     open drift issue if one is present.
  3. When they differ and the pinned image has been current for longer than the grace
     window (`DRIFT_THRESHOLD_HOURS`, default 24), the run opens **one** deduped issue
     carrying the label `deployed-build-drift`, naming both revisions and the run URL;
     a second run updates that issue instead of opening a new one.
  4. **Fail-loud (NFR-018 §2)**: an unset instance-URL variable, an unreachable instance,
     a missing/`"unknown"` `build_revision`, a missing annotation, or an unparseable
     manifest makes the run **red** and opens **no** issue. An undetermined check must
     never read as clean. Asserted by unit tests over each of those inputs.
  5. Unit tests live in `src/backend/tests/unit/test_deployed_build_check.py`, loading the
     script through `src/backend/tests/support/repo_scripts.py` (the pattern already used
     by `test_workflow_gate_integrity_check.py`), with the registry and HTTP responses
     injected — no network access in the test.
  6. `python3 scripts/check_workflow_gate_integrity.py` passes on the new workflow.
  7. Replaying today's measured inputs (pinned revision `37cbc06f…`, instance reporting a
     pre-#1180 build) through the script yields the drift verdict — i.e. the check would
     have caught this incident.
- **Touched files / artifacts**:
  - `.github/workflows/deployed-build-freshness.yml` (new; schedule offset from the 06:00 UTC freshness job and the 00:00 UTC Nuclei nightly — 07:00 UTC, after the pin check; `permissions: contents: read, packages: read, issues: write`; fixed `concurrency` group, `cancel-in-progress: false`)
  - `scripts/ci/check_deployed_build.py` (new; mirrors the structure and fail-loud contract of `scripts/ci/check_digest_freshness.py`)
  - `src/backend/tests/unit/test_deployed_build_check.py` (new)
  - repository **variable** `DEPLOYED_INSTANCE_URL` (configuration, not a code change — the URL is public and `/api/health` is unauthenticated)
- **Specialist**: `fullstack-developer` — **partial match, recorded deliberately**. No
  agent or skill in the live catalog claims GitHub Actions workflow authoring:
  `deployment-change-analyzer` and `deployment-bestpractices-reviewer` are reviewers,
  `deployment-chart-manage` and `bjw-common-deployment-generator` are Helm-chart scoped.
  `fullstack-developer` is the closest by description (implementation across the stack)
  and owns the Python script; the workflow YAML is generalist work inside that dispatch.
- **Depends on**: P1 (criterion 1c requires `build_revision` to exist; the contract is
  already fixed in §Declared contract, so authoring may start once P1's contract is
  merged, and criterion 4 makes the job honest — it goes red, not green — during the
  window before a baked image is actually deployed).

### P3 — Correct and complete the delivery-path documentation

- **Problem statement**: the one document that describes how a merge reaches the cluster
  states the wrong delivery anchor (a release tag and per-controller `image.tag`
  overrides), and its FAQ answers "which image version is running?" by inspecting the
  registry from outside — the exact detour this issue was filed about.
- **Acceptance criteria** (all testable by reading the rendered page against the
  measured facts in §Established facts):
  1. `docs/de/deployment/ci-cd.md` §"Produktion: der Pin liegt zusätzlich im
     GitOps-Repository" no longer claims `targetRevision: vX.Y.Z`; it states that the
     production `Application` tracks `targetRevision: develop` at `path: helm/kamerplanter`
     from `github.com/nolte/kamerplanter.git`, and states explicitly that **a published
     release is not on this instance's delivery path**.
  2. The page names the four hops end to end — merge on `develop` → `docker-publish`
     pushes and moves `:latest` → Renovate's grouped `kamerplanter images` PR writes the
     new digest → ArgoCD syncs the commit and pods roll — and says who cuts a release and
     what a release *is* for (chart package, compose assets, docs), given that it does not
     drive this instance.
  3. The image-pinning invariant is stated as an invariant with its consequence: an
     overlay must not carry per-controller `image.tag` overrides, because the override
     replaces the digest and `pullPolicy: IfNotPresent` then means "keep whatever is
     cached on the node". #1210 is cited as the measured incident, alongside #1024.
  4. The FAQ entry *"Wie sehe ich, welche Image-Version gerade läuft?"* answers with
     `curl <instance>/api/health` → `build_revision` first, keeping `docker inspect` /
     GHCR only as the fallback for an image that is not running.
  5. The two-hop verification chain is documented: `chart-image-digest-freshness`
     (GHCR → chart pin) and the P2 job (chart pin → running instance), with the statement
     that the first being green does **not** imply the second.
  6. `docs/en/deployment/ci-cd.md` mirrors every change (DE-canonical + EN-mirror per
     `spec/style-guides/DOCS.md`), and `docs/de|en/deployment/argocd.md` is checked for
     the same stale `targetRevision` claim and corrected if present.
  7. A strict MkDocs build passes.
- **Touched files / artifacts**: `docs/de/deployment/ci-cd.md`,
  `docs/en/deployment/ci-cd.md`, `docs/de/deployment/argocd.md`,
  `docs/en/deployment/argocd.md`; `mkdocs.yml` only if a new page is added (adding one is
  **not** required — the existing §"Deployment und Rollback" is the right home, and
  `helm/kamerplanter/values.yaml:81-121` plus `ec0b4dc7e` already carry the invariant in
  code comments; do not duplicate them, link them).
- **Specialist**: `mkdocs-documentation` (project-local
  `.claude/agents/mkdocs-documentation.md`). Description match: "Erstellt und pflegt
  endnutzerfreundliche, mehrsprachige Dokumentation im MkDocs-Material-Format gemaess
  NFR-005 … wenn Dokumentationsseiten erstellt, aktualisiert oder uebersetzt werden
  sollen".
- **Depends on**: none — the field name it documents (`build_revision`) is fixed by
  §Declared contract, so P3 runs concurrently with P1. If P1 changes the contract, P3's
  criterion 4 must be re-checked before the PR.

## Dependency ordering

```
P1 ──► P2
P3        (independent — dispatchable concurrently with P1)
```

- P1 and P3 may be dispatched in parallel: their file sets are disjoint
  (`src/backend/**` + `.github/workflows/docker-publish.yml` vs `docs/**`).
- P2 waits on P1 only for the response contract, which §Declared contract fixes.
- Per the recorded feedback that write-capable agents on a shared tree collide
  (`git stash` conflicts), run the two concurrent dispatches in separate worktrees or
  sequence them.

## Risks

| Risk | Mitigation |
|---|---|
| **Public disclosure of the exact running commit.** `build_revision` on an unauthenticated endpoint tells anyone precisely which code is deployed, enabling exact CVE/patch targeting. | The endpoint already discloses `version` and `mode`, and the repository is public, so the incremental exposure is small — but this is a deliberate trade, not an oversight. **Route the P1 diff through `code-security-reviewer` before the PR.** If the verdict is negative, the fallback is a short SHA or an authenticated `/api/v1/version`; the AC-6 job can authenticate. |
| Cache invalidation: an `ARG`/`ENV` placed too early in the Dockerfile rebuilds every layer on every commit, lengthening all eight image builds. | P1 criterion 6 pins the placement (last in the `prod` stage) and makes it reviewable in the diff. |
| Repurposing `app_version` would silently change the OpenAPI `info.version`, the `openapi.json` release asset and the mDNS advertisement. | P1 criteria 3–4 assert the old value is preserved; the plan mandates a **new** field. |
| The P2 job watches exactly one instance (the operator's lab) and needs `DEPLOYED_INSTANCE_URL` configured. | Criterion 4 makes an unset variable a **red run**, so the job can never report clean on nothing (NFR-018 §2) — the same contract the existing freshness job uses. |
| P2's unit tests run in `backend.yml`, which is **not** a required check on `develop` (measured). A future regression in the script would not block a merge. | Accepted for now and recorded here. If blocking enforcement is wanted, the `e2e-selftest` pre-commit hook (`.pre-commit-config.yaml:123`) is the existing pattern for putting a pytest suite into the required `static` lane. |
| P2 could be built as a second job inside `chart-image-digest-freshness.yml` instead of a new workflow. | A separate workflow was chosen so the two checks keep distinct dedup anchors, labels and permissions; a shared workflow would entangle two alerts in one issue. Reconsider only if the operator prefers one file. |
| The instance stays stale regardless of everything planned here until argo-charts `3e53606c` is pushed. | Out of scope by operator decision (AC-1/AC-2). P2 is designed to make exactly this state loud rather than silent — and would already be alerting today. |
| Doc drift recurs: the corrected page can go stale the next time the overlay changes. | P3 criterion 5 ties the prose to the two automated checks, so the checks — not the prose — are the enforcement. |

## Open questions

1. **AC-4 — was v0.2.1 left in draft deliberately, and what is the intended cadence?**
   Recorded by the operator as unresolved and carried here rather than guessed. The
   observation that would settle it: the operator's own intent, plus whether any consumer
   depends on published releases now that the production instance demonstrably does not
   (`targetRevision: develop`). **This observation was not made.** Until it is, the
   honest statement for AC-3 is "releases exist for the chart package, the compose assets
   and the docs deploy — not for this instance."
2. **Is `DEPLOYED_INSTANCE_URL` acceptable as a public repository variable**, and is
   `https://kamerplanter.just-a-lab.duckdns.org` the instance to watch? The URL already
   appears in the public issue body and in the ArgoCD manifest, and `/api/health` answered
   an unauthenticated request — so no secret is required, but the choice is the
   operator's.
3. **Should `build_revision` be full or short SHA?** The plan specifies full (matching the
   `org.opencontainers.image.revision` annotation exactly, so P2's comparison needs no
   truncation). Confirm if a shorter public value is preferred (see the security risk).

## Follow-ups (recommended issues, not packages here)

- **Chart provenance attestation broken since 2026-08-16.** `publish-helm-charts
  (kamerplanter)` fails at "Attest chart provenance" with `Error: No credentials found for
  registry ghcr.io` (run 31955579431); the preceding "Push chart to GHCR" step succeeded,
  so the chart still publishes and only the attestation is missing. Not on this instance's
  delivery path (ArgoCD reads the chart from git), which is why it is a separate issue.
- **Feed the baked revision into `resolve_release`.** Today `SENTRY_RELEASE: ""` in the
  chart means every Sentry event is attributed to `kamerplanter-backend@1.0.0`. The fix
  belongs in the SSOT `src/libs/kp_errortracking/kp_errortracking/error_tracking.py`
  followed by `python src/libs/kp_errortracking/sync.py`, fanning out to three services —
  a distinct strand, and not required by AC-3/5/6.
- **Build identity for the frontend and side services**, if a stale frontend or
  knowledge-service ever produces a comparable misdiagnosis.

## Dispatch log

<!-- Appended during operation 5; one line per package once its specialist reports.
     <YYYY-MM-DD> P<k> dispatched to <subagent_type> — <result one-liner> -->
