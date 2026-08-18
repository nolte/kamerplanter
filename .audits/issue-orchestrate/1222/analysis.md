---
artifact-type: issue-orchestration-analysis
repo: nolte/kamerplanter
issue: 1222
classification: bug
secondary-classes: [infra]
route: direct
status: draft
created: 2026-08-18
---

# Issue Orchestration — Pre-analysis

<!-- Run-scoped artifact: committed on the run's feature branch, then removed with a
     fix-forward `git rm` before the PR merges, per spec/project/issue-orchestration/
     §Pre-analysis artifact lifecycle. -->

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #1222 — Every `helm/**` merge to develop republishes the OCI chart under a published release's version
- **URL**: https://github.com/nolte/kamerplanter/issues/1222
- **Labels**: bug, release, deployment
- **Linked items**: #1218 (found while orchestrating it; #1218's fix merged as `17aae5f58`), #987 / #1024 / #1025 (the image-side digest pinning this issue is the chart-side analogue of), #1026 (`chart-image-digest-freshness.yml`)
- **Prior art checked**: `gh pr list --search 1222 --state open` → `[]`, no competing strand [ESTABLISHED: command output]. No `project/requirements/` artifact for #1222 [ESTABLISHED: operator brief, override recorded]. No roadmap item. Two prior guards of exactly the shape this plan reuses already exist: `scripts/check_workflow_gate_integrity.py` and `scripts/check_attest_registry_credentials.py`.

## Classification

- **Primary class**: bug
- **Secondary class(es)**: infra
- **Rationale**: A published artefact is silently mutated in the registry; that is a defect in the delivered product, not a CI-health question. (Decided by the operator; not re-opened.)

## Grounding — established facts

Every load-bearing claim below is marked ESTABLISHED (command output or `file:line`) or UNESTABLISHED (with the observation that would settle it, and a statement that it was not made), per `spec/claude/claim-provenance/`.

### The defect

- **E1 — The overwrite happened.** Anonymous GHCR read of `nolte/charts/kamerplanter:0.2.0` returns annotations `org.opencontainers.image.created: 2026-08-18T14:09:14Z`, `org.opencontainers.image.version: "0.2.0"`, layer digest `sha256:d328e879db866ca8745302da2d210011ac664bc59357cbea079bb06a0997925e`. Release `v0.2.0` was published `2026-08-13T18:09:49Z` (`gh release list`). The chart under that tag was therefore rebuilt from `develop` **five days after** the release. [ESTABLISHED: `curl` against `ghcr.io/v2/nolte/charts/kamerplanter/manifests/0.2.0` + `gh release list`]
- **E2 — The develop tree carries the released version.** `helm/kamerplanter/Chart.yaml:5` → `version: 0.2.0`; `:6` → `appVersion: "1.0.0"`. [ESTABLISHED: file]
- **E3 — The mechanism.** `.github/workflows/docker-publish.yml:747-758` (`Determine chart version`) emits `version=${REF_NAME#v}` only when `$REF` starts with `refs/tags/v`, and the **empty string** otherwise. `:760-767` (`Update chart version for release`) is gated on `steps.version.outputs.version != ''` and is therefore skipped on a `develop` push. `:818-819` (`Package chart`) runs `helm package`, which reads the version straight from `Chart.yaml`. `:821-838` (`Push chart to GHCR`) pushes that. [ESTABLISHED: file:line]
- **E4 — The committed value is exactly what develop publishes.** Because the rewrite at `:767` is the only thing that changes `.version` and it never runs on a branch ref (E3), the value committed in `Chart.yaml` **is** the OCI tag develop publishes under. [ESTABLISHED: derived from E3, no other write to `.version` exists in the workflow]
- **E5 — The push is not coupled to a successful run.** In the #1218 runs the job died at `Attest chart provenance` (`:839-845`), which is **after** `Push chart to GHCR` (`:821`). Step order is file order, so the push had already succeeded. "The job was red, so nothing shipped" is false here. [ESTABLISHED: file:line ordering + operator's measured #1218 history]
- **E6 — The registry tag set matches the release set.** `nolte/charts/kamerplanter` carries exactly `0.0.2`…`0.0.24`, `0.1.0`, `0.2.0` — i.e. one tag per published release and nothing else. This is the evidence that `helm push` derives the OCI tag verbatim from the chart version. [ESTABLISHED: tags/list + `gh release list`; the direct proof (a push) was not performed]
- **E7 — The spec being violated.** `spec/project/continuous-delivery/en.md:53` — "**MUST** give every published artifact a version reference that resolves to the same bytes forever; republishing different content under an existing version reference is prohibited". [ESTABLISHED: file:line]

### The chosen fix, and whether it works

- **E8 — The release path already handles a pre-release develop value.** `:767` is an unconditional assignment, `yq -i ".version = \"$VERSION\" | .appVersion = \"$VERSION\""` — it overwrites whatever is committed, including a pre-release. Nothing in the release path branches on the pre-existing value. [ESTABLISHED: file:line]
- **E9 — Helm accepts the pre-release and names the artefact from it.** Probe with the repo's own chart shape: `version: 0.3.0-dev` → `Successfully packaged chart and saved it to: …/kamerplanter-0.3.0-dev.tgz`; `version: 0.3.0.dev` → `Error: validation: chart.metadata.version "0.3.0.dev" is invalid`. So SemVer-2 pre-release is valid and the `.tgz` filename carries it. [ESTABLISHED: `helm package`, helm v4.2.3 local]
- **E10 — The glob-based consumers survive it.** `:830` pushes `"$CHART"-*.tgz` and `:861` (`Upload chart as release asset`) passes `"$CHART"-*.tgz`; both match `kamerplanter-0.3.0-dev.tgz`. [ESTABLISHED: file:line + E9]
- **E11 — `Chart.lock` does not carry the chart version.** It carries only the three dependency versions and their digest. `helm dependency build` is unaffected. [ESTABLISHED: `helm/kamerplanter/Chart.lock`]
- **E12 — The image-digest pin does not read the chart version.** `scripts/ci/pin_chart_image_digests.sh` takes the version as `$2` from the workflow (`:784`, sourced from the tag) and touches only `values.yaml`. It never reads `Chart.yaml`. [ESTABLISHED: script + `file:line`]
- **E13 — Skaffold does not read the chart version.** `skaffold.yaml:56,172,242` use `chartPath: helm/kamerplanter` only. [ESTABLISHED: grep]
- **E14 — No test asserts the chart version.** A repo-wide grep for `Chart.yaml` across `*.py *.sh *.yml *.yaml *.md *.ts` returns only: `.github/workflows/docker-publish.yml`, `.github/release-automation.yml`, `docs/**`, `spec/style-guides/HELM.md`, `.claude/skills/req-coverage-audit/SKILL.md`. Nothing under `src/backend/tests/` or `scripts/` reads it. [ESTABLISHED: grep]

### What the merge will publish (first live proof)

- **E15 — The chart job will run on merge.** `on.push.paths` (`:6-13`) includes `helm/**`; the `changes` job's `helm` filter (`:88-89`) is `helm/**`; `publish-helm-charts`'s condition (`:728`) is satisfied by `needs.changes.outputs.helm == 'true'`. `.github/workflows/**` is *not* in `on.push.paths`, so a workflow-only change would not trigger it — but this change touches `helm/**`, so it does. [ESTABLISHED: file:line]
- **E16 — What it publishes.** Version step → empty (branch ref, E3) → no rewrite → `helm package` → `kamerplanter-0.3.0-dev.tgz` → push creates a **new** tag `0.3.0-dev` under `ghcr.io/nolte/charts/kamerplanter`. `:0.2.0` is **not** touched. This is the first live proof and it cannot itself do harm: it creates a tag no consumer pins and overwrites nothing. [ESTABLISHED: derived from E3/E6/E9/E15]
- **E17 — The merge also rebuilds the backend image.** The unit tests for the new guard belong in `src/backend/tests/unit/` (the established placement — `src/backend/tests/support/repo_scripts.py` docstring states it, and all eleven sibling `test_*_check.py` files sit there), and `src/backend/**` is both in `on.push.paths` and in the `backend` path filter. So `build-backend` runs and rewrites `ghcr.io/nolte/kamerplanter-backend:latest`. Routine, but it starts the Renovate digest write-back cycle for `values.yaml`. [ESTABLISHED: file:line + directory listing]

### Consumers of the chart version — all of them, measured

Grep for the literal `0.2.0` across `*.md *.yaml *.yml *.sh *.py *.ts *.json` (excluding `node_modules`, `.git`, lockfiles):

| Consumer | Status after the change | Action |
|---|---|---|
| `helm/kamerplanter/Chart.yaml:5` | the thing being changed | **P2** |
| `docs/de/deployment/helm.md:22` and `docs/en/deployment/helm.md:22` | **INVALIDATED** — a `yaml` block mirroring `Chart.yaml`, explicitly marked `<!-- Quelle/Source: helm/kamerplanter/Chart.yaml -->` at `:33` | **P4** |
| `docs/de/deployment/argocd.md:65,131,216` and `docs/en/…:65,131,216` — `targetRevision: 0.2.0` | **stays correct** — `0.2.0` remains a published release, and `targetRevision` must name a release. But it was correct *by coincidence* (it matched `Chart.yaml`); after the change the rationale must be stated, and readers must be told never to point `targetRevision` at the `-dev` channel | **P4** (note, not a number change) |
| `docs/de/deployment/kubernetes.md:67,165` and `docs/en/…:67,165` — `helm pull … --version 0.2.0` | **stays correct on the version**; but the *registry path* in those lines is wrong (see O4) | no change here; O4 |
| `docs/{de,en}/deployment/ci-cd.md:309` — "On a release tag, `version` and `appVersion` … are automatically set to the release version" | **stays true**, and becomes the anchor for the new develop-channel statement | **P4** |
| `.github/release-automation.yml:25,47` | **STALE CLAIM** — it says chart `version` "moves independently of the application release, which is why it reads 0.2.0 against an app at 1.0.0". `docker-publish.yml:767` forces `.version == .appVersion == <release version>` on every release, so the chart version does **not** move independently. Contradicted at `file:line`. | **P5** |
| `spec/style-guides/HELM.md:66,553,560` — §2.2 and §13 "Chart-Versionierung & Publishing" show `version: 0.2.0` as the Kamerplanter `Chart.yaml` | **STALE** — the style guide will contradict the enforced gate, and §13 is exactly where the develop-channel convention belongs | **P5** |
| `scripts/ci/pin_chart_image_digests.sh`, `scripts/check_chart_image_digests.py`, `scripts/ci/check_release_assets.py`, `chart-image-digest-freshness.yml`, `skaffold.yaml`, `Chart.lock` | **unaffected** — E11, E12, E13; the release-asset checker derives `kamerplanter-<v>.tgz` from the *release tag*, never from `Chart.yaml` | none |
| `docs/*/development/debugging.md:29`, `.vscode/launch.json:2`, `NFR-004:1057` | false positives — `"version": "0.2.0"` is the VS Code launch-schema version | none |

### The corrupted `:0.2.0` tag

- **E18 — Repair in place is possible but spec-prohibited.** *Possible*: a `workflow_dispatch` of `docker-publish.yml` on ref `v0.2.0` satisfies `publish-helm-charts`'s condition via `startsWith(github.ref, 'refs/tags/v')` (`:728`), takes the release path, and would re-push `:0.2.0` from the v0.2.0 tree. *Prohibited*: `spec/project/continuous-delivery/en.md:55` — "**MUST** treat an accidental publication as a forward-only event: the remedy is to publish a new version and, where the ecosystem supports it, mark the bad version as withdrawn. **Overwriting the bad version in place destroys the immutability guarantee every consumer depends on**." Re-pushing `:0.2.0` would be a *third* set of bytes under that reference. [ESTABLISHED: file:line, both halves]
- **E19 — It could not be made byte-identical anyway.** `docker-publish.yml:855-857` records that `helm package` stamps tar headers with `time.Now()`, so an identical chart repackaged is never byte-identical. A "repair" therefore cannot restore the digest v0.2.0 consumers may have recorded; it can only add a fourth distinct artefact. [ESTABLISHED: file:line]
- **Judgement: repair is OUT OF SCOPE for this issue**, and not merely deferred — it is the wrong remedy. The correct remedy is forward-only and is a *release* decision, not a code change: see O1.

### Facts that were NOT established

- **U1 — Whether `git tag` is empty in the required `static` lane.** `nolte/gh-plumbing/.github/workflows/reusable-pre-commit.yaml@d51e51ec` uses `actions/checkout@v6.1.0` with **no** `fetch-depth` and **no** `fetch-tags` [ESTABLISHED: fetched file], so the documented default (single-commit shallow fetch, no tags) applies. The *consequence* — that `git tag --list 'v*'` returns an empty set there — was **not observed**; the observation that would settle it is a temporary `run: git tag --list 'v*' | wc -l` step in a CI run on this branch. It is not needed for the decision (see D2), only for the strength of the argument. Locally the checkout has 26 `v*` tags, which is precisely the asymmetry that makes a tag-derived rule dangerous.
- **U2 — Whether `helm push` would reject an OCI tag containing `-`.** Not observed (no push performed). E6 plus the OCI tag grammar (`[A-Za-z0-9_][A-Za-z0-9._-]*`) make it near-certain. Settling observation: the merge itself (E16) — which is exactly why P6 exists.
- **U3 — Whether the `0.3.0-dev` push will succeed end-to-end.** Not observable before merge. P6 is the observation.

## Scope

- **In scope**: (a) making `helm/kamerplanter/Chart.yaml` carry a develop-channel pre-release version so a non-tag push can never collide with a published release version; (b) a **falsifying** static guard in the required `static` lane that keeps it that way; (c) a release-side reservation so the guard's weaker decidable rule is actually *sufficient*; (d) the documentation and spec/comment consumers that the change invalidates or that assert something now false; (e) a post-merge live verification against GHCR.
- **Out of scope**:
  - Repairing `charts/kamerplanter:0.2.0` in place — prohibited by `continuous-delivery` §B (E18/E19). Forward-only remedy → **O1**.
  - The wrong chart registry path in `docs/{de,en}/deployment/{helm,kubernetes}.md` → **O4** (pre-existing, distinct root cause).
  - Retiring the known `changes`-fan-out gap documented at `docker-publish.yml:29-42` — named there, needs its own delivery decision.
  - Promoting any advisory security lane to required.
  - Changing `appVersion` on develop → **O5**.

## Route

- **Decision**: direct
- **Rationale**: One coherent outcome (a published version reference stops being overwritten), one PR strand, no new roadmap item. All six packages land in a single feature branch off `develop`. (Decided by the operator; not re-opened.)

## The guard — design decision, stated plainly

The obvious rule is *"the chart version on a non-tag ref must never equal a version that has been published as a release."* **That rule is not statically decidable, and every way of making it decidable makes the guard inert exactly where it must not be.** Three candidate sources for "which versions are published", and why each is rejected:

- **D1 — A live API call (`gh release list` / GHCR tags/list) from a pre-commit hook.** Rejected. It makes the required `static` lane depend on network reachability and on GitHub's availability; it fails closed on every offline commit or fails open on every blip. A gate that turns red for a reason unrelated to the diff gets `--no-verify`'d, and a gate that fails open is inert. Neither outcome is a guard.
- **D2 — Derive the set from git tags in the checkout.** Rejected, and this is the decisive one. The `static` lane checks out with `actions/checkout@v6.1.0` carrying no `fetch-depth`/`fetch-tags` (U1), i.e. the shallow default with no tags — while a developer's checkout has all 26. A rule whose *outcome depends on whether tags happened to be fetched* is **green locally and inert in CI**, which is the exact failure class this repository has paid for repeatedly ("Guard implementiert, aber inert"). Worse, a *draft* release has no git tag at all (`v0.2.1` is a draft right now, `gh release list` → `Draft`, and `git tag --list` does not contain it), so even a full fetch would permit a version that is about to become a release.
- **D3 — Hard-code the published set in the checker.** Rejected: it must be edited after every release, and a list nobody updates silently stops covering the newest release — which is precisely the version most likely to be collided with.

**Concluded rule (weaker, fully decidable, and sufficient):**

> `helm/*/Chart.yaml` `version` MUST parse as SemVer 2.0 **and** carry a pre-release identifier whose first dot-separated identifier is exactly `dev`.

Why it is enough:

1. The committed value is *only ever* published from a non-tag ref (E4) — the release path unconditionally overwrites it (E8).
2. A release version reference is `${REF_NAME#v}` for a tag `v<x>` (E3). If no release tag carries a `-dev` pre-release, then a `-dev` committed version can never equal a published one. **That premise is an assumption, not a fact — so P3 turns it into an enforced rule** at the one moment it is decidable (the tag ref itself, inside the workflow). Without P3 the guard claims more than it enforces; with it, the weaker rule is exactly as strong as the true rule for every reachable case.
3. Reserving the *first identifier* (`dev`) rather than "any pre-release" keeps `-rc1`-style releases legal while making P3's rejection narrow and exact.

**Falsification — the observation that proves the guard detects the real defect.** Stated as a requirement on P1, to be demonstrated in the PR body:

> `python3 scripts/check_chart_develop_version.py --chart <a copy of helm/kamerplanter/Chart.yaml as of 17aae5f58>` MUST exit non-zero and name `version 0.2.0` as carrying no `dev` pre-release. That file is the exact tree that produced the overwrite measured in E1. If the checker is green on that input, it does not detect the real defect and the package is not done.

Reproduce without mutating the tree: `git show 17aae5f58:helm/kamerplanter/Chart.yaml > /tmp/pre/Chart.yaml`.

**And the second, less obvious direction** — a checker that merely forbids the literal `0.2.0` would pass `version: 0.3.0` and reintroduce the defect at the next release. So P1 MUST also be demonstrated red on `version: 0.3.0` (a *different, non-colliding-today* release-shaped version), because the rule is "not a releasable version", not "not 0.2.0".

## Work packages

Specialists resolved by **description match** against the catalog present at planning time: `/home/nolte/repos/github/claude-shared/plugins/{nolte-engineering,nolte-claude-dev,nolte-media}/{agents,skills}/` and the project-local `.claude/agents/` + `.claude/skills/` [ESTABLISHED: directory listing + frontmatter `description` of each candidate]. `fullstack-developer` exists both as a project-local agent (`.claude/agents/fullstack-developer.md`, `distribution: project`, description explicitly names Helm charts) and as `nolte-engineering:fullstack-developer`; the project-local one wins at runtime and is the one named below.

### P1 — The guard: `check_chart_develop_version.py`, wired and proven red

- **Problem statement**: Nothing in the repository can observe that the committed chart version is a releasable version; the condition is visible only by pulling the OCI tag and diffing it (issue body, "Not currently observable"). Without a guard, P2 is a one-off correction that the next hand edit undoes silently.
- **Scope note — why script + hook + tests are ONE package and not three**: a checker that exists but is not wired into the required lane is the "guard implementiert, aber inert" failure this repository keeps paying for. Splitting them creates a state in which the package is "done" and the guard does nothing.
- **Acceptance criteria** (all four must hold; the first two are the falsification carrier):
  1. `git show 17aae5f58:helm/kamerplanter/Chart.yaml > /tmp/pre/Chart.yaml && python3 scripts/check_chart_develop_version.py --chart /tmp/pre/Chart.yaml` **exits non-zero** and names `0.2.0` as carrying no `dev` pre-release. That input is the exact tree that produced the overwrite measured in E1.
  2. The same command against a fixture carrying `version: 0.3.0` **also exits non-zero** — the rule is "not a releasable version", not "not the literal 0.2.0".
  3. `pre-commit run chart-develop-version --all-files` passes on the tree once P2 has landed, and fails on it before P2 has landed. The hook is registered in `.pre-commit-config.yaml` as a `repo: local` hook with `language: python`, `additional_dependencies: ['PyYAML>=6.0']`, `always_run: true`, `pass_filenames: false` — the same shape as the two sibling hooks at `.pre-commit-config.yaml:441-451` and `:479-487`, because the required `static` lane runs on a bare runner with none of the project's dependencies installed.
  4. `cd src/backend && pytest tests/unit/test_chart_develop_version_check.py` is green, with tests driven against **constructed fixtures in `tmp_path`** (never against the real `helm/`), loaded via `from tests.support.repo_scripts import load_repo_script`, and including an explicit `TestItCanFail` class asserting the checker goes red, names the file, and exits non-zero — mirroring `test_attest_registry_credentials_check.py:1-40`.
- **Interface requirements** (so the falsification above is runnable without mutating the tree, and so the checker matches its siblings): `--chart <path>` (repeatable; default = every `helm/*/Chart.yaml`), `--list`, `--json`. Escape hatch `# chart-develop-version-ok: <reason>` on the `version:` line or in the comment block directly above it, with a **mandatory** reason of more than one word — the identical convention to `# gate-integrity-ok:` and `# attest-credentials-ok:` (`scripts/check_attest_registry_credentials.py:124`, `:259-284`). One convention, not three.
- **Module docstring MUST record**: the measured incident (E1, with the two timestamps and the digest), why the strong rule was rejected (D1/D2/D3 above, including the shallow-checkout asymmetry), and that the sufficiency of the weak rule depends on P3.
- **Touched files / artifacts**: `scripts/check_chart_develop_version.py` (new), `.pre-commit-config.yaml` (new `repo: local` block with the incident comment, placed after the `attest-registry-credentials` block), `src/backend/tests/unit/test_chart_develop_version_check.py` (new)
- **Specialist**: `fullstack-developer` — description match: "turns a sharply-scoped requirement into production-ready, runnable code (no pseudocode or stubs) … plus matching tests"; the project-local pendant adds "bestehender Code refactored". `unit-test-generator` was considered and rejected: it scaffolds tests for an existing module and would leave the checker itself unwritten, splitting the package in exactly the way that produces an inert guard.
- **Depends on**: none

### P2 — Carry a develop-channel pre-release version in `Chart.yaml`

- **Problem statement**: `helm/kamerplanter/Chart.yaml:5` carries `0.2.0`, a published release version, and E4 shows that value *is* what every `helm/**` merge publishes.
- **Acceptance criteria**:
  1. `helm/kamerplanter/Chart.yaml` carries `version: 0.3.0-dev` (see O2 for the number choice).
  2. `python3 scripts/check_chart_develop_version.py` exits 0 on the tree, and `pre-commit run chart-develop-version --all-files` passes.
  3. `helm package helm/kamerplanter` produces `kamerplanter-0.3.0-dev.tgz` (already probed green in E9 against this exact version string).
  4. `helm lint helm/kamerplanter` is not newly broken.
  5. A comment **above** the `version:` key (not trailing it) records: this is the develop channel; it is rewritten to the release version by `docker-publish.yml:767` on a tag ref; it is rebuilt on every `helm/**` merge and therefore MUST NOT be pinned by a consumer; consumers needing immutability pin the released version or the chart digest.
  6. `appVersion` is left at `"1.0.0"` (O5).
- **Touched files / artifacts**: `helm/kamerplanter/Chart.yaml`
- **Specialist**: `fullstack-developer` — the project-local description names "Helm-Charts erstellt" explicitly. `deployment-chart-manage` was considered and rejected by description: its two operations are `provision` (greenfield chart) and `reconcile` (extend a chart after an *application* change adds env vars/ports/services). This is neither; nothing about the app changed.
- **Depends on**: P1 — so the guard is demonstrably red against the pre-fix `Chart.yaml` before the fix makes it green. Reversing the order forfeits the falsification.

### P3 — Reserve the `-dev` channel on the release side

- **Problem statement**: P1's rule ("carry a `dev` pre-release") is only *sufficient* if no release tag ever carries a `-dev` pre-release. Today that is an unenforced assumption. A guard whose soundness rests on an unenforced premise claims more than it enforces.
- **Acceptance criteria**:
  1. A new `scripts/ci/determine_chart_version.sh` reproduces the current logic of `docker-publish.yml:747-758` exactly — empty output for a non-tag ref, `${REF_NAME#v}` for `refs/tags/v*` — and **additionally exits non-zero with an `::error::` when the resolved version's pre-release begins with `dev`**.
  2. `docker-publish.yml`'s `Determine chart version` step calls the script instead of carrying the logic inline, with a comment naming #1222 and stating what the rejection protects.
  3. `cd src/backend && pytest tests/unit/test_determine_chart_version.py` is green over four cases invoked by `subprocess.run`: `refs/heads/develop` → empty, exit 0; `refs/tags/v0.3.0` → `0.3.0`, exit 0; `refs/tags/v0.3.0-rc1` → `0.3.0-rc1`, exit 0 (**RC releases stay legal**); `refs/tags/v0.3.0-dev` → exit non-zero.
  4. `pre-commit run workflow-gate-integrity --all-files` still passes (the new step can fail, so it is not a vacuous gate).
- **Note for the implementer**: there is currently **no** test in the repository for any `scripts/ci/*.sh` [ESTABLISHED: grep for `publish_release_asset|pin_chart_image_digests` under `src/backend/tests/` → no hits]. The `subprocess.run` idiom above is new; keep it minimal and put the reason in the test module docstring.
- **Touched files / artifacts**: `scripts/ci/determine_chart_version.sh` (new), `.github/workflows/docker-publish.yml` (`:747-758`), `src/backend/tests/unit/test_determine_chart_version.py` (new)
- **Specialist**: `fullstack-developer` — CI/infra code plus its tests; same description match as P1.
- **Depends on**: none (parallel to P1). If the operator drops this package (O3), P1's docstring MUST be amended to state that the premise is unenforced — the plan must not ship a guard that quietly overstates itself.

### P4 — Documentation: the develop channel, in DE and EN

- **Problem statement**: `docs/{de,en}/deployment/helm.md:22` mirrors `Chart.yaml` under an explicit `<!-- Source: -->` marker and is invalidated by P2. `argocd.md`'s `targetRevision: 0.2.0` examples were correct only because they matched `Chart.yaml`; after P2 the reason must be stated, and readers must be told the `-dev` tag exists and must never be pinned.
- **Acceptance criteria**:
  1. `docs/de/deployment/helm.md:19-24` and `docs/en/deployment/helm.md:19-24` show `version: 0.3.0-dev` and explain in one sentence that this is the develop channel, rewritten to the release version on a release tag.
  2. Both `helm.md` files gain an admonition stating that `charts/kamerplanter:0.3.0-dev` is **rewritten by every `helm/**` merge** and must never be pinned — deliberately mirroring the wording already used for images at `helm/kamerplanter/values.yaml:90` ("`latest` is rewritten by every push").
  3. Both `argocd.md` files gain a note at the first `targetRevision` example stating that `targetRevision` MUST name a **published release version** and never the develop channel tag, with the reason.
  4. Both `ci-cd.md` files extend the existing sentence at `:309` to state what develop publishes and under which tag.
  5. `targetRevision: 0.2.0` and `--version 0.2.0` are **left unchanged** — `0.2.0` is still the newest published release.
  6. DE is canonical and EN mirrors it 1:1 per `spec/style-guides/DOCS.md`; `task docs:build` (strict) passes.
- **Touched files / artifacts**: `docs/de/deployment/helm.md`, `docs/en/deployment/helm.md`, `docs/de/deployment/argocd.md`, `docs/en/deployment/argocd.md`, `docs/de/deployment/ci-cd.md`, `docs/en/deployment/ci-cd.md`
- **Specialist**: `mkdocs-documentation` (project-local) — description match: "Erstellt und pflegt endnutzerfreundliche, mehrsprachige Dokumentation im MkDocs-Material-Format gemaess NFR-005 … Aktiviere diesen Agenten wenn Dokumentationsseiten erstellt, aktualisiert oder uebersetzt werden sollen".
- **Depends on**: P2

### P5 — Correct the two stale claims outside `docs/`

- **Problem statement**: Two files assert something that is false, and one of them becomes *more* misleading after P2.
  - `.github/release-automation.yml:47` — "Chart `version` … should NOT be added: it versions the chart's own packaging contract and **moves independently of the application release**, which is why it reads 0.2.0 against an app at 1.0.0." Contradicted at `docker-publish.yml:767`, which sets `.version` **and** `.appVersion` to the release version on every release. The chart version does not move independently; it is forced equal.
  - `spec/style-guides/HELM.md:66` and `:551-560` (§13 "Chart-Versionierung & Publishing") present `version: 0.2.0` as the chart's shape and say nothing about the develop channel — so the style guide will contradict a gate that turns the required lane red.
- **Acceptance criteria**:
  1. The `release-automation.yml` rationale no longer claims independence; it states the measured coupling (`.version` and `.appVersion` are both overwritten from the tag) and, if the `appVersion` recommendation survives that correction, says why on the corrected premise.
  2. `HELM.md` §13 states the convention as a rule: the develop tree carries a `-dev` pre-release; the release tag rewrites `version` and `appVersion`; the guard is `scripts/check_chart_develop_version.py` in the required `static` lane. Its example blocks no longer show a bare `0.2.0` as the develop-tree value.
  3. `task precommit` passes (the spec/style-guide tree has its own hooks).
- **Specialist**: **no matching specialised agent — generalist remediation.** Checked and rejected by description: `mkdocs-documentation` is scoped to "Dokumentationsseiten … im MkDocs-Material-Format" (i.e. `docs/`), not `spec/style-guides/` or workflow-config comments; `fullstack-developer` is for production code; `nolte-claude-dev:*` are for skills/agents. This is prose correction in two config/spec files and should be done in-thread by the orchestrator.
- **Touched files / artifacts**: `.github/release-automation.yml`, `spec/style-guides/HELM.md`
- **Depends on**: P2

### P6 — Post-merge live verification against GHCR

- **Problem statement**: The merge is the first live proof (E15/E16), and E5 establishes that job status is not a proxy for what was published — the push succeeds before the step that failed in #1218. So the proof must be read from the registry.
- **Acceptance criteria** (all read anonymously, no auth needed — the same call used to establish E1):
  1. `GET ghcr.io/v2/nolte/charts/kamerplanter/tags/list` contains `0.3.0-dev`.
  2. `GET …/manifests/0.3.0-dev` returns `org.opencontainers.image.version: "0.3.0-dev"` and a `created` timestamp after the merge.
  3. **`GET …/manifests/0.2.0` still returns `created: 2026-08-18T14:09:14Z` and layer digest `sha256:d328e879db866ca8745302da2d210011ac664bc59357cbea079bb06a0997925e`** — unchanged from E1. This is the criterion that proves the defect is gone: a `helm/**` merge no longer touches the released tag.
  4. Recorded in the PR's Risk/rollout notes (per the pre-analysis artifact lifecycle, this file is `git rm`'d before merge, so the evidence must live somewhere that survives).
- **Specialist**: **no matching specialised agent — generalist verification**, owned by the orchestrating skill / operator. There is no read-the-registry-and-verify agent in the catalog; `deployment-bestpractices-reviewer` audits chart *content* against the deployment best-practices spec and would not make this observation.
- **Depends on**: P2, P3, P4, P5 (i.e. the merged PR)

## Dependency ordering

```
P1 ──▶ P2 ──▶ P4 ──┐
        │          ├──▶ P6   (P6 runs after the PR merges)
        └──▶ P5 ──┘
P3 (independent of P1/P2; must merge in the same PR)
```

- **P1 before P2 is load-bearing**, not stylistic: the guard's falsification is "red against the tree as it stands". Once P2 lands, that observation can only be reconstructed from a git object, which is weaker evidence and easy to skip.
- **P3 may be dispatched concurrently with P1** — disjoint files (`scripts/ci/`, `docker-publish.yml`, a distinct test file) with no shared symbol.
- **P4 and P5 are concurrent** with each other — disjoint file sets.
- Per `feedback_parallel_agents_shared_tree`, writing agents on the same worktree run **sequentially**; the concurrency above is a dependency statement, not a licence to run two writers at once on this tree.

## Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | **The chosen approach does not fully satisfy `continuous-delivery` §B.** `0.3.0-dev` is itself a *published version reference that will be rewritten on every `helm/**` merge*, and §B:53 admits no exception ("resolves to the same bytes forever"). The fix converts a **silent** violation on a release version into a **declared** one on a development channel — a large improvement, not a clean pass. See the refutation note below. | Declare it rather than pretend: the `-dev` marker, the docs admonition (P4 criterion 2) and the `Chart.yaml` comment (P2 criterion 5) all say the tag moves. Immutable addressing already exists for anyone who needs it: `Push chart to GHCR` captures the manifest digest (`docker-publish.yml:828-838`) and `Attest chart provenance` (`:839-845`) attests it, so `charts/kamerplanter@sha256:…` is pinnable — the same answer #987/#1024 gave for images. Recorded as a named deviation per NFR-018 §1, never as a clean bill. |
| R2 | Merging rebuilds `kamerplanter-backend:latest` (E17), which makes the digest pins in `values.yaml` stale and can trip the `chart-image-digest-freshness` nightly after its 3-day grace window if the Renovate write-back stalls. | Expected and designed-for, not a defect. Name it in the PR's rollout notes so a subsequent drift alert is not misread as caused by this change. |
| R3 | A red `publish-helm-charts` run does **not** mean nothing shipped (E5). Reading job status as the verification would repeat #1218's mistake. | P6 verifies against the registry, not against the run. Written into P6's acceptance criteria. |
| R4 | The guard becomes inert if the hook is added but not to the required lane, or if the checker is written to accept a path it never actually scans by default. | P1 acceptance criterion 3 exercises the hook itself (`pre-commit run chart-develop-version --all-files`), and criterion 1 exercises the default scan path. `static / Static CI Tests` is the required check and runs on every push to every branch (`.github/workflows/build-static-tests.yaml:4,20-22`). |
| R5 | **Security / supply-chain path touched.** P3 edits the publishing job of `docker-publish.yml` — the workflow that pushes and attests every artefact. A mistake there can break the release path or weaken attestation. | Run `code-security-reviewer` on the diff before the PR (its description: read-only OWASP/whole-codebase security review). Run it **from this worktree**, not the primary checkout — a prior run produced an empty diff because it read the primary checkout (`project_openapi_release_asset_765`). Also run `task precommit` and `task check`. |
| R6 | `helm push` could reject an OCI tag containing `-` (U2). | Low: E6 plus the OCI tag grammar. P6 criterion 1 is the observation that settles it; if it fails, the fallback is a non-hyphen channel encoding, and the guard rule would need restating. Named so a failure is diagnosed rather than puzzled over. |
| R7 | The next release still ships a chart whose `:0.2.0` predecessor is corrupt, and no consumer can tell. | Out of scope by E18/E19; surfaced as **O1** for an explicit operator decision rather than omitted. |

### Refutation recorded against the brief

The brief instructed: plan against the pre-release option, "if you find it unworkable, say so with evidence rather than quietly substituting another." **It is workable** — E8/E9/E10/E11/E12/E13/E14 show every mechanical consumer survives it, and E16 shows the first live push is harmless. But it is **not a complete satisfaction of `continuous-delivery` §B** (R1), and the plan says so rather than implying the issue is fully closed by it. The rejected option "skip the chart push entirely on non-tag refs" would satisfy §B outright; the rejected option "push develop under a distinct channel tag" would require an extra `oras`/`crane` retag step, because `helm push` derives the OCI tag from the chart version and offers no override (E6) — which is presumably why it costs more. Neither is re-proposed; both are recorded so the trade stays visible.

## Open questions

- **O1 — What to do about `charts/kamerplanter:0.2.0`, which serves develop's chart today.** Repair in place is *mechanically possible* (`workflow_dispatch` on ref `v0.2.0`) but **prohibited** by `spec/project/continuous-delivery/en.md:55`, and could not restore the original bytes anyway (E19). The spec-conformant remedy is forward-only and is a **release decision, not a code change**: publish `v0.2.1` (the draft already exists, created 2026-08-13T21:26:23Z) from a `develop` that carries this fix, and annotate the `v0.2.0` release body stating that its OCI chart tag was overwritten on 2026-08-18 and must not be trusted. Note that the #1218 decision "v0.1.0 and v0.2.0 are deliberately left unrepaired" (`release-assets-complete.yml:145`) was about *missing release assets* and does **not** cover a corrupted OCI tag — so this is a genuinely open decision, not a settled one. **Operator decides; not planned here.**
- **O2 — `0.3.0-dev` or `0.2.1-dev`?** A `v0.2.1` draft exists, so the next release is more likely `0.2.1` than `0.3.0`. `0.3.0-dev` (the brief's example) sorts above every published release, which keeps "newest" listings sane and does not key develop to a draft that may never ship; `0.2.1-dev` is more truthful about the intended next version. **Either satisfies the guard, and neither requires a periodic bump** — a stale `0.3.0-dev` after `v0.3.0` ships still carries a `dev` pre-release and still cannot collide, which is deliberate: a guard that demands a manual bump after every release becomes a chore that gets skipped. Planned as `0.3.0-dev` per the brief; say so if you want `0.2.1-dev`.
- **O3 — Keep P3?** It guards a near-zero-probability path (a human tagging `v0.3.0-dev`), and its cost is ~15 lines of shell plus a new test idiom. Its real value is that it converts the guard's *assumption* into an *enforced rule*. If dropped, P1's docstring must state the premise is unenforced (see P3's note) — the plan must not ship a guard that overstates itself.
- **O4 — Pre-existing docs defect, adjacent but distinct.** `docs/de/deployment/helm.md:11`, `docs/en/deployment/helm.md:11` and `docs/{de,en}/deployment/kubernetes.md:67,165` tell users to pull from `oci://ghcr.io/nolte/kamerplanter-helm/kamerplanter`. That package **does not exist**: `gh api /users/nolte/packages/container/kamerplanter-helm%2Fkamerplanter` → `404 Package not found`, while `…/charts%2Fkamerplanter` → `403 need read:packages scope` (i.e. it exists) [ESTABLISHED: command output]. The workflow pushes to `oci://ghcr.io/nolte/charts` (`docker-publish.yml:830`) and the release body template says `oci://ghcr.io/${OWNER}/charts/kamerplanter` (`:934`). `argocd.md` already uses the correct path. An operator following `kubernetes.md` today gets a failure. **Different root cause; recommended as a follow-up issue** rather than folded in, so this PR's falsification story stays about one thing. Confirm.
- **O5 — `appVersion` on develop.** It reads `"1.0.0"` and has since the initial commit, against a release line that reached `v0.2.0` (`release-automation.yml:29-31`). The release path overwrites it, so it is inert — but `release-automation.yml:47-48` calls it "the one version a consumer actually sees". Left unchanged here (out of scope, and changing it is the version-bearing-file decision that file explicitly defers). Flag if you want it in.
- **O6 — Nothing else blocks dispatch.** The requirements gate is an operator override (recorded); the issue is unambiguous; the repository conventions were detected and are named per package.

## Dispatch log

<!-- Appended during operation 5; one line per package once its specialist reports. -->
