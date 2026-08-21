---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter"
issue: "1210"
classification: "bug"
secondary-classes: ["infra", "docs"]
route: "direct"
status: approved
created: "2026-08-21"
---

# Issue Orchestration — Pre-analysis

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #1210 — The #1163 MCP fix has not reached the running instance
- **URL**: https://github.com/nolte/kamerplanter/issues/1210
- **Labels**: bug, release, backend, deployment
- **Linked items**: #1145, #1163, #1164, #1217 (merged 2026-08-18, `Refs` not `Closes`), #1229 (release-lag alert, closed 2026-08-20), nolte/k8s-home-lab#837 (open)
- **Prior art checked**: a prior orchestration run of this same issue exists — PR #1217 delivered AC 3, 5 and 6 and deliberately left the issue open. No requirement artefact under `project/requirements/` covers #1210 (29 files scanned). No open PR currently targets this issue.
- **Trust boundary**: issue body and its single comment are both authored by `nolte`, repository owner — inside the trusted-author set per `spec/claude/trusted-author-injection-guard/`.

## Classification

- **Primary class**: bug
- **Secondary class(es)**: infra, docs
- **Rationale**: unchanged from the prior orchestration run, deliberately — re-classifying the same issue mid-life would break the audit trail. The residual scope is documentation- and infra-shaped, which the work packages reflect.

## State of the acceptance criteria — measured 2026-08-21

| AC | State | Evidence |
|---|---|---|
| 3 — delivery path written down | delivered | `docs/{de,en}/deployment/ci-cd.md`, six hops, both manual hops named (#1217) |
| 5 — instance reports the actual build | delivered as code, **inert in production** | `build_revision` ships behind `HEALTH_EXPOSE_BUILD_REVISION`, default off; the live instance omits the key |
| 6 — un-delivered fix becomes visible | delivered **and verified in production** | `release-lag.yml` opened #1229 on 2026-08-19; v0.2.1 was published the same day; the job auto-closed #1229 on 2026-08-20 |
| 1, 2 — fix live on the instance | **probably already satisfied** — see the refutation | `v0.2.1` contains `796c0047` (#1163), verified by `git merge-base --is-ancestor` |
| 4 — draft deliberate? intended cadence? | **open** | `grep -rn -i "cadence\|Kadenz"` over the delivery docs returns no hit |

## The refutation — established, with provenance

The working hypothesis carried by this issue and by the prior run's issue comment is *"the instance runs `0.0.23` images, roughly a month old"*. Measurement on 2026-08-21 contradicts it:

- `supported_majors` was introduced by `46878ea26` on 2026-08-15 (#1180); `git tag --contains 46878ea26` names **`v0.2.1` only**.
- GHCR `ghcr.io/nolte/kamerplanter-backend:0.0.23` carries OCI annotation `org.opencontainers.image.revision: b40b3ccd8393a612876bdf8c48ad0144f81e32c3`, created `2026-07-23T06:51:20.122Z`.
- `git merge-base --is-ancestor 46878ea26 b40b3ccd` is **false**. The `0.0.23` image cannot serve the field.
- `GET https://kamerplanter.just-a-lab.duckdns.org/api/health` returns `{"status":"healthy","version":"1.0.0","mode":"light","supported_majors":[1]}` — it **does** serve the field.

**Therefore the running backend is not the image the GitOps overlay on `origin/master` names.** `origin/master` in `nolte/k8s-home-lab` still carries `targetRevision: v0.1.0` and `image.tag: "0.0.23"` today, and PR #837 is still open. The instance is nonetheless at or beyond `v0.2.1`.

Two consequences, and the second is the load-bearing one:

1. AC 1 and AC 2 are most likely already satisfied, because `v0.2.1` contains the #1163 fix. **Unestablished**: whether `assign_nutrient_plan` with `dry_run: false` now returns 200. The observation that would settle it is the `dry_run` discriminator from #1145, or `kubectl` against the running pod; both prod contexts (`intel-nuc` 192.168.178.23, `smart-home-02` 192.168.178.104) answered `no route to host` from this session, so neither was made.
2. **The delivery-verification procedure this issue produced would have given the wrong answer today.** The section "Has my merged fix been delivered yet?" asks three questions in order; step 2 reads `targetRevision` from the GitOps repository and would have reported an instance a month behind. Step 3 (`build_revision`) is unanswerable there because the flag is off. The procedure does not name the failure mode where the manifest and the running cluster disagree — which is exactly the state measured.

## Scope

- **In scope**: AC 4 (establish the draft question and write down the intended cadence) plus the live-verification path — correcting the verification procedure where it is now demonstrably wrong, making the build question answerable without the flag and without cluster access, and naming the production-overlay requirement that would make `build_revision` non-inert. Recording the GitOps-drift finding.
- **Out of scope**: landing `nolte/k8s-home-lab#837` and any edit to that repository (hop 5, a different repository); the live re-verification of AC 1/2 itself, which needs cluster or MCP credentials this session does not have; the `publish-helm-charts` attestation failure (already fixed by `17aae5f58`).

## Route

- **Decision**: direct
- **Rationale**: one coherent outcome — make the answer to "is my fix delivered?" trustworthy — carried by a single PR strand against `develop`, touching the delivery documentation only. No new or retargeted roadmap item. Bounded in the planning sense, per the skill's boundedness rule.

## Operator decisions recorded at the approval gate (2026-08-21)

- **Q1 — cadence**: keep `RELEASE_LAG_THRESHOLD_DAYS` at **3**. The documentation states 3 as the policy rather than as an unexplained grace window, and names the known limit: on 2026-08-16, when the bug was re-encountered, the oldest un-released commit was 2.6 days old, so the alert would not yet have fired.
- **Q2 — P3 shape**: **documentation only**. No helper script, therefore no new code, therefore no `security-review` gate on this run.
- **Q3 — requirements gate**: **operator override recorded.** No `requirements-elicit` run. Justification: the issue enumerates six acceptance criteria, three are delivered and were re-measured today with provenance, and the operator bounded the residual scope explicitly at the acquisition gate. Understanding is evidenced, not weak.

## Work packages

### P1 — Establish the draft question and write down the intended cadence (AC 4)

- **Problem statement**: no document states how quickly a merged fix is expected to reach a running instance, nor whether `v0.2.1` was held back deliberately. `RELEASE_LAG_THRESHOLD_DAYS` defaults to 3 and is documented as a "grace window" with no policy behind it, so the number is unfalsifiable — nobody can say whether 3 is right.
- **Acceptance criteria**: `docs/{de,en}/deployment/ci-cd.md` states the intended cadence for shipping a merged fix as **3 days**, and names `RELEASE_LAG_THRESHOLD_DAYS` as the mechanism that enforces exactly that cadence, so the two numbers visibly agree. The known limit is stated rather than flattered: at 3 days the alert would not have fired at the moment the defect was re-encountered on 2026-08-16. The v0.2.1 draft question is answered on the record — omission rather than a deliberate hold, established by #1229 firing on 2026-08-19 and the release being published the same day. A reader can name the cadence and the consequence of exceeding it without reading the workflow.
- **Touched files / artifacts**: `docs/de/deployment/ci-cd.md`, `docs/en/deployment/ci-cd.md`. `.github/workflows/release-lag.yml` is **not** touched — the operator kept the default.
- **Specialist**: `mkdocs-documentation`
- **Depends on**: none

### P2 — Correct the verification procedure, which today returns the wrong answer

- **Problem statement**: the documented three-step check treats the GitOps `targetRevision` as authoritative for what the cluster runs. Measured today, the manifest and the cluster disagree, and following the procedure yields "a month behind" for an instance that is current. The failure mode is not named anywhere.
- **Acceptance criteria**: the "Has my merged fix been delivered yet?" section names the manifest-versus-cluster disagreement as a real failure mode, states which observation wins when the steps disagree (the pod's `imageID`, or the instance's own answer — never the manifest alone), and a reader following the corrected procedure against this instance on 2026-08-21 arrives at "delivered". Any statement elsewhere in the delivery docs asserting the instance runs `0.0.23` is corrected or dated.
- **Touched files / artifacts**: `docs/de/deployment/ci-cd.md`, `docs/en/deployment/ci-cd.md`
- **Specialist**: `mkdocs-documentation`
- **Depends on**: P1 (same documentation file)

### P3 — Make the build question answerable without the flag and without the cluster

- **Problem statement**: AC 5's field is default-off, and on the instance that motivated the issue the key is absent — a state deliberately indistinguishable from "not configured". So the question the issue exists to answer is still unanswerable from outside. Yet it *was* answered today by a chain needing neither the flag nor cluster access: registry tag, then the OCI annotation `org.opencontainers.image.revision`, then `git merge-base --is-ancestor <fix> <revision>`.
- **Acceptance criteria**: the delivery documentation carries that chain as a runnable procedure with the exact commands, so an operator can answer "does artefact X contain commit Y?" from the public registry alone; and it states the limit plainly — the chain identifies an *artefact*, not what the cluster is running, and therefore does not replace step 3.
- **Touched files / artifacts**: `docs/de/deployment/ci-cd.md`, `docs/en/deployment/ci-cd.md`
- **Specialist**: `mkdocs-documentation`
- **Depends on**: P2 (same documentation section)

### P4 — Name the production-overlay requirement that makes `build_revision` non-inert

- **Problem statement**: the flag is off in production, so the field added for exactly this question answers nothing on exactly the instance that motivated it. This repository cannot set it — hop 5 lives in `nolte/k8s-home-lab` — but it can state it as a deployment requirement so the next overlay change carries it.
- **Acceptance criteria**: the deployment documentation names `HEALTH_EXPOSE_BUILD_REVISION=true` as the recommended setting for a production instance whose delivery state must be auditable, restates the security trade-off that made it opt-in rather than silently reversing it, and points at the GitOps overlay as the place it is set. The external action is recorded on #1210 so it is not rediscovered.
- **Touched files / artifacts**: `docs/de/deployment/ci-cd.md`, `docs/en/deployment/ci-cd.md`, `docs/de/deployment/konfigurationsmatrix.md`, `docs/en/deployment/konfigurationsmatrix.md`
- **Specialist**: `mkdocs-documentation`
- **Depends on**: P3 (same documentation section)

### P5 — File the GitOps drift as its own finding

- **Problem statement**: the overlay on `origin/master` names an image the cluster demonstrably does not run. Either the manifest drifted from the cluster, or an out-of-band update bypassed the documented chain. Both defeat the delivery chain's integrity, and neither is fixable in this repository.
- **Acceptance criteria**: an issue exists carrying the measured contradiction with its provenance (the four observations above and their exact output), stating both candidate explanations and naming the observation that would separate them.
- **Touched files / artifacts**: none — a GitHub issue
- **Specialist**: no matching specialised agent — generalist remediation
- **Depends on**: none

### P6 — Re-verify AC 1/2 on the running instance

- **Problem statement**: the evidence says the fix is live; nothing has confirmed it end-to-end. Both prod cluster contexts are unreachable from this session.
- **Acceptance criteria**: `assign_nutrient_plan` with `dry_run: false` returns 200 against the instance and the assignment reads back; `get_mcp_activity` returns 200. The outcome is recorded on #1210, and the issue is closed only once it holds.
- **Touched files / artifacts**: none — an operator action
- **Specialist**: none — operator action, credentials not held by this session
- **Depends on**: none

## Dependency ordering

`P1 → P2 → P3 → P4` — one sequential chain against the same documentation files, dispatched to a single specialist so the shared tree is never written concurrently. `P5` and `P6` are independent of the chain and of each other.

## Risks

- **All four docs packages edit the same files.** Mitigation: a single sequential dispatch, never parallel — the shared-tree collision failure mode.
- **AC 1/2 stay unproven when P6 cannot be run.** Mitigation: the PR uses `Refs`, not `Closes`, exactly as #1217 did; the issue stays open until P6 holds.
- **DE/EN parity.** The docs contract is DE-canonical with an EN mirror; a package editing only one side leaves the pair inconsistent. Mitigation: every acceptance criterion names both files.
- **No security-sensitive source path is touched.** The `build_revision` disclosure decision was reviewed under #1217 and is not reopened: P4 documents the existing trade-off and recommends an opt-in, it does not change the default. With Q2 answered documentation-only, no new code enters this PR, so `security-review` is not triggered.

## Open questions

None. Q1, Q2 and Q3 were answered at the approval gate on 2026-08-21 and are recorded above.

## Dispatch log

<!-- appended during operation 5 -->

- **P5** — dispatched to the generalist (no matching specialised agent — generalist remediation). Filed as **nolte/k8s-home-lab#839**, carrying the four measured observations, both candidate explanations, and the two `kubectl` commands that separate them. Operator chose `nolte/k8s-home-lab` as the target at the dispatch gate, since the manifest and its correction live there.
