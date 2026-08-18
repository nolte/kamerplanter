---
artifact-type: issue-orchestration-analysis
repo: nolte/kamerplanter
issue: 1218
classification: bug
secondary-classes: [infra]
route: direct
status: draft
created: 2026-08-18
---

# Issue Orchestration — Pre-analysis

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #1218 — publish-helm-charts has failed since the v0.2.0 release: chart provenance attestation errors, and every release since is missing its chart asset
- **URL**: https://github.com/nolte/kamerplanter/issues/1218
- **Labels**: bug, release, deployment
- **Linked items**: #1210 (delivery invisibility, the issue this was found while orchestrating), #1217 (the PR that recorded it in its risk notes), #886 (the change that introduced the defect — established below), #987/#1024/#1026 (the chart-pin lineage the chart job's comments reference)
- **Prior art checked**: no open PR touches `.github/workflows/docker-publish.yml` (`gh pr list` — none matching); no `project/features/` entry and no `project/roadmap.md` item covers chart publication; no requirement artifact under `project/requirements/` for this issue. Two closely-related mechanisms already exist in the tree and are the design template for the visibility half: `scripts/ci/check_release_lag.py` + `.github/workflows/release-lag.yml` (#1210) and `scripts/ci/check_digest_freshness.py` + `.github/workflows/chart-image-digest-freshness.yml` (#1026).

## Classification

- **Primary class**: bug
- **Secondary class(es)**: infra
- **Rationale**: a delivery workflow does not do what it says it does; the fix is a workflow/credential change plus the observability that would have surfaced it. Operator declined the `workflow-health-triage` short-circuit — triage is already complete by measurement (a workflow defect, not a flake, an outage, or a stale pin).

## Requirements gate

No artifact under `project/requirements/`. **Operator override recorded**, on the basis of a confirmed scope plus a root cause measured at `file:line` and at registry level rather than assumed. Everything the implementation needs to know is in §Measured grounding below, each item marked ESTABLISHED or UNESTABLISHED per `spec/claude/claim-provenance/`.

## Measured grounding

All workflow line numbers are `.github/workflows/docker-publish.yml` at the head of this worktree (`ca6d5d91b`), which matches `origin/develop` for that file.

### G-1 — The root cause is the credential *store*, not a permission scope. ESTABLISHED.

`actions/attest@508db95` (the action `actions/attest-build-provenance@4d10147` delegates to; both SHAs read from the run log of 31955579431, "Set up job") resolves registry credentials in exactly one place. From its bundled `dist/index.js` at line 62801-62824, fetched at that pinned SHA:

```js
const getRegistryCredentials = (imageName) => {
    const { registry } = parseImageName(imageName);
    const dockerConfigFile = path.join(os.homedir(), '.docker', 'config.json');
    ...
    const credKey = Object.keys(dockerConfig.auths || {}).find((key) => canonicalizeRegistry(key) === target);
    const creds = credKey ? dockerConfig.auths?.[credKey] : undefined;
    if (!creds) {
        throw new Error(`No credentials found for registry ${registry}`);
    }
```

The chart job's only login is line 787, `helm registry login`, which writes Helm's own store (`$HELM_REGISTRY_CONFIG`, default `~/.config/helm/registry/config.json`) and never `~/.docker/config.json`. The eight image jobs use `docker/login-action@dbcb813` (lines 113, 198, 273, 348, 423, 498, 573, 649), which writes the Docker store. That single difference is the whole defect.

The **exact** error string matters and narrows it further: the action distinguishes `No credential file found at <path>` (file absent) from `No credentials found for registry <registry>` (file present, no matching `auths` key). The observed error is the second one — run 31955579431, `Attest chart provenance`, `2026-08-16T15:25:24.4754750Z ##[error]Error: No credentials found for registry ghcr.io`. So `~/.docker/config.json` exists on the runner and simply has no `ghcr.io` entry, which is precisely what a `docker login` would add.

**Contrast measurement, same run family.** On the `v0.2.0` tag run 31729355999 all eight image jobs — same `runs-on: ubuntu-latest`, same action at the same pinned SHA, same `push-to-registry: true`, same registry — **succeeded** (`gh run view 31729355999 --json jobs`: eight `success`, `publish-helm-charts (kamerplanter)` `failure`). The only variable between the succeeding eight and the failing one is which credential store was written.

### G-2 — REFUTED: the issue's `packages: write` hypothesis. ESTABLISHED.

The issue body asks "whether `push-to-registry: true` requires a `packages: write` scope the job does not carry". It carries it. Lines 730-736 grant `contents: write`, `packages: write`, `id-token: write`, `attestations: write`, and the run log confirms it at runtime (`Set up job`, `2026-08-16T15:25:14.0862161Z Attestations: write`). This hypothesis is closed; do not spend time on it.

### G-3 — REFUTED: the issue's "helm push reported no digest" hypothesis. ESTABLISHED.

The issue quotes the `v0.2.0` run as having "emitted, immediately before the error": `::error::helm push reported no digest — refusing to attest a chart we cannot identify.` That line in the log is the **echoed script source** inside the step's `##[group]Run` block (it carries the `^[[36;1m` command-echo colour escape, as do the neighbouring lines `digest=$(grep -oE ...)` and `echo "Chart digest: $digest"`). It is not an emitted error.

Both failing runs captured a digest and printed it:

| Run | Digest line |
|---|---|
| 31729355999 (`v0.2.0`) | `2026-08-13T18:21:10.2295464Z Chart digest: sha256:f328fdc28ee548cdc1a6e117f52f3268cda2f47f8a9d811dca1b669cafee5604` |
| 31955579431 (`develop`) | `2026-08-16T15:25:23.3945054Z Chart digest: sha256:52f8df5f3e3e39ce526c897180817c87240f558dd959879a09a438b654ed34fc` |

`Push chart to GHCR` reports `success` in both. The no-digest branch has never fired. The chart *does* reach GHCR.

### G-4 — REFUTED and EXPANDED: this did not start at v0.2.0, and the loss is larger than one asset. ESTABLISHED.

`Attest chart provenance` was introduced on **2026-08-01** by commit `3054b7d96` — `fix(ci): attest published artifacts and stop trusting the chart pin (#886)` (`git log -S 'Attest chart provenance' -- .github/workflows/docker-publish.yml`). Every release published after that date is affected, which is **two**, not one:

| Tag | Published | Assets present (`gh release view <tag> --json assets`) |
|---|---|---|
| v0.0.23 | 2026-07-23 | `default.env.example-0.0.23`, `docker-compose-0.0.23.yml`, `kamerplanter-0.0.23.tgz` |
| v0.0.24 | 2026-07-30 | `default.env.example-0.0.24`, `docker-compose-0.0.24.yml`, `kamerplanter-0.0.24.tgz`, `openapi.json` |
| **v0.1.0** | **2026-08-06** | **`openapi.json` only** |
| **v0.2.0** | **2026-08-13** | **`openapi.json` only** |

The regression window brackets #886 exactly.

And the loss per affected release is not one asset but four things, because the failure propagates one job further than the issue states. `update-release-assets` (line 837) declares `needs: [... publish-helm-charts]` with `!contains(needs.*.result, 'failure')`, so it is **skipped** whenever the chart job fails — measured on run 31729355999, where `update-release-assets` reports `skipped`. That job is the sole producer of:

1. `docker-compose-<version>.yml`
2. `.env.example-<version>`
3. the release body's **Packages** block (the `<!-- kp:packages:begin -->` … `<!-- kp:packages:end -->` section with the image list, the chart pull command and the `gh attestation verify` instructions)

…on top of the chart `.tgz` lost inside the chart job itself. Confirmed on the live release: `gh release view v0.2.0 --json body | grep -c 'kp:packages:begin'` returns **0**. The published v0.2.0 release therefore tells a consumer nothing about where its images or its chart live, and its own documented `curl -LO .../docker-compose-0.2.0.yml` instructions are absent along with the file they point at.

### G-5 — PARTIALLY REFUTED: how the failure was actually invisible. ESTABLISHED.

The brief states the failure is invisible because a skipped job reads as green. Half of that is right and the load-bearing half is not:

- The runs where the chart job **executed** were **red at run level**: `gh run list --workflow=docker-publish.yml` gives `31955164085` = `failure` and `31955579431` = `failure` (both `push`/`develop`, 2026-08-16). They were not green.
- The runs where it was **skipped** (no `helm/**` in the diff) are green, correctly — `31952783594`, `31954503183`, `32126819049`, and the three most recent runs `32140717296`, `32142079463` are all `success`.

So the accurate statement of the invisibility is: **a red post-merge delivery run alerts nobody**, and because the chart job only executes on the minority of pushes that touch `helm/**` or on a tag, the redness is intermittent and reads like noise rather than a standing defect. There is no `workflow_run` observer anywhere in the tree (`grep -l 'workflow_run:' .github/workflows/*.yml` → no matches), and `docker-publish.yml` is a post-merge workflow, so it never turns a pull request red either. That is the gap the visibility half must close.

### G-6 — The `KNOWN GAP` class does NOT apply to the chart job. ESTABLISHED, two ways.

The brief asked whether the header's `KNOWN GAP` reasoning (a job combining `always()` with `needs.changes.outputs.<x> == 'true'` while never consulting `needs.changes.result`) applies to `publish-helm-charts`. It does not.

1. By reading: the job's `if:` at lines 724-728 consults `needs.*.result` for **both** hazards — `!contains(needs.*.result, 'failure')` and `!contains(needs.*.result, 'cancelled')` — and `needs.*` includes `changes`. A failed `changes` therefore makes the run red on `changes` itself and skips the chart job; it cannot produce a false green. The header comment already says as much ("The two publishing jobs at the bottom are already guarded").
2. By running the repository's own linter: `python3 scripts/check_workflow_gate_integrity.py --json` reports `sites: 19`, `justified: 19`, `unjustified: 0`, and **`publish-helm-charts` does not appear among the sites at all**. The eight `build-*` jobs do, each carrying the `needs follow-up` marker.

The eight-job `KNOWN GAP` remains open and remains out of scope here (see §Open questions, Q3).

### G-7 — Merging this fix will, by itself, trigger no run. ESTABLISHED.

`on.push.paths` (lines 6-11) lists `src/backend/**`, `src/frontend/**`, `docker/**`, `spec/knowledge/rag/**`, `helm/**`. `.github/workflows/**` is **not** in the list. A pull request that changes only `docker-publish.yml` produces no `docker-publish` run on merge. This is why the verification strategy in §Verifying the fix without cutting a release cannot be "merge it and watch develop".

### G-8 — A pre-existing immutability defect, found while planning. ESTABLISHED, out of scope.

`helm/kamerplanter/Chart.yaml` line 5 reads `version: 0.2.0`. On a non-tag ref the chart job skips `Update chart version for release` (line 761, `if: steps.version.outputs.version != ''`), so `helm package` uses that literal `0.2.0` and `helm push` publishes `oci://ghcr.io/nolte/charts/kamerplanter:0.2.0`. Every merge to `develop` touching `helm/**` therefore **overwrites the OCI chart tag of a published release**, which is the exact rule `scripts/ci/publish_release_asset.sh` cites in its header (`spec/project/continuous-delivery` §B: a published version reference must resolve to the same bytes forever). Out of scope for #1218; recorded as Q2.

## Scope

- **In scope**, both halves as confirmed by the operator:
  1. **Fix the attestation.** Restore provenance attestation for the chart, and with it `Upload chart as release asset` and the downstream `update-release-assets` job (G-4 shows the second is part of the same loss).
  2. **Fix the visibility.** A defect in the delivery lane must not be able to sit for 17 days again (2026-08-01 → 2026-08-18). Designed against the repository's existing conventions: `scripts/check_workflow_gate_integrity.py` in the required `static / Static CI Tests` lane (NFR-018 §2 — a check that cannot fail must not exist), and the deduped-alert-issue shape of `release-lag.yml` / `chart-image-digest-freshness.yml`.
- **Out of scope**:
  - **Retroactively uploading the missing assets for already-published releases (v0.1.0, v0.2.0).** Operator decision: fix forward plus visibility, do not touch published releases. This interacts with P4 and forces a design constraint there — see R-4.
  - The `KNOWN GAP` in the eight `build-*` job conditions (Q3). Named, still open, unrelated failure path.
  - The chart-tag overwrite of G-8 (Q2). Real defect, different subject, needs its own decision.
  - Anything about #1210's stale production instance. The production ArgoCD `Application` reads the chart from git at a release tag, not from the OCI package; fixing this delivers nothing to the cluster, exactly as the issue says.

## Route

- **Decision**: direct
- **Rationale**: one coherent outcome (the chart-publication path publishes completely and fails loudly), one PR strand, no new roadmap item. The visibility packages are the same outcome's observability, not a second outcome — the operator scoped them together deliberately, on the grounds that a delivery fix nobody can see fail is the thing that produced this issue.

## Work packages

### P1 — Give the chart job a Docker-store credential

- **Problem statement**: `actions/attest-build-provenance` with `push-to-registry: true` reads `~/.docker/config.json` (G-1); the chart job only ever writes Helm's store, so the attest step fails, and it takes `Upload chart as release asset` and the whole `update-release-assets` job down with it (G-4).
- **Design** (prescriptive, because the alternatives were considered and rejected):
  - **Add** a `docker/login-action@dbcb813823bdd20940b903addbd779551569679f # v4.6.0` step to `publish-helm-charts` before `Attest chart provenance`, with `registry: ${{ env.REGISTRY }}`, `username: ${{ github.actor }}`, `password: ${{ secrets.GITHUB_TOKEN }}` — byte-identical in shape and pin to the eight image jobs, so the two paths stop differing.
  - **Keep** the existing `helm registry login` (line 787). `helm push` reads `$HELM_REGISTRY_CONFIG`, not the Docker store; removing it breaks the push. The step needs a comment saying **why two logins to the same registry coexist**, in the house style, or the next tidy-up deletes one of them.
  - **Rejected alternative**: setting `HELM_REGISTRY_CONFIG=$HOME/.docker/config.json` and keeping one login. It would work — Helm's registry config is Docker-config-shaped — but it depends on an undocumented format coincidence, has Helm rewrite a file the Docker tooling owns, and diverges from the eight jobs beside it instead of converging on them. Record the rejection in the comment.
  - **Rejected alternative**: hand-writing the `auths` entry with `jq`/`base64` in a `run:` step. Puts a token through shell quoting for no benefit; `docker/login-action` masks it and logs out in its post-step.
- **Acceptance criteria** (all falsifiable):
  1. `publish-helm-charts` contains a `docker/login-action` step pinned to the same SHA as the eight image jobs, positioned before `Attest chart provenance`, and `helm registry login` still exists. *Falsified by*: P2's checker (see below) exits non-zero.
  2. On the runtime dispatch of §Verifying the fix, the chart job reports `Attest chart provenance` = `success`, and the `subject-digest` in that step's `with:` block equals the `Chart digest: sha256:…` printed by `Push chart to GHCR` in the same run. *Falsified by*: any other conclusion, or a mismatch between the two digests.
  3. In that same dispatch, `Upload chart as release asset` is no longer `skipped` (it is `skipped` only by its own `startsWith(github.ref, 'refs/tags/v')` condition on a branch dispatch, which is correct — so state the observed reason explicitly rather than asserting success).
  4. `gh attestation verify oci://ghcr.io/nolte/charts/kamerplanter:<dispatch-version> --repo nolte/kamerplanter` exits 0 against the chart pushed by that dispatch. *Falsified by*: a non-zero exit or "no attestations found".
  5. The final diff of the PR touches `.github/workflows/docker-publish.yml` **only** — in particular `helm/kamerplanter/Chart.yaml` is unchanged, so the temporary version bump used for the dispatch (see §Verifying the fix) is reverted. *Falsified by*: `git diff --name-only origin/develop...HEAD` listing anything else.
- **Touched files / artifacts**: `.github/workflows/docker-publish.yml`
- **Specialist**: `nolte-shared:cicd-pipeline-design` — its description is the exact match: "Writes and patches workflow files in the target repository", auditing against `spec/project/continuous-delivery/` (artifact immutability, **provenance**) and `spec/project/github-actions-best-practices/` (digest pinning, least-privilege permissions, **short-lived credentials**).
- **Depends on**: P2 (for the red-first evidence only — see the dependency note; P1's own edit needs nothing)

### P2 — Static guard: an attesting job must carry a Docker-store login (the falsification carrier)

- **Problem statement**: the coupling that broke here is invisible in the YAML — nothing states that `push-to-registry: true` presupposes a Docker-store login in the same job. P1 alone restores the behaviour and leaves the trap armed: the next person who removes the "redundant" second login re-breaks it, and will find out at the next release. This package converts the runtime failure into a pull-request-observable one, which is also what makes the fix provable without cutting a release.
- **Design**: mirror `scripts/check_workflow_gate_integrity.py` exactly — it is the established pattern and it already runs where this needs to run.
  - New `scripts/check_attest_registry_credentials.py`. Rule: for every job containing a step `uses: actions/attest-build-provenance@…` (or `actions/attest@…`) whose `with.push-to-registry` is true, that job MUST also contain a step that populates the Docker credential store for the same registry — `uses: docker/login-action@…`, or an alternative justified in place by a `# attest-credentials-ok: <reason>` marker with the same minimum-reason discipline the gate-integrity checker uses (`JUSTIFICATION_MARKER`, `MIN_JUSTIFICATION_CHARS = 12`). Standard library plus PyYAML only; `--list` and `--json` modes; exit 0 / 1 / 2 like its sibling. The header must state the mechanism (the `dist/index.js` credential lookup of G-1) and the incident, in the house style.
  - Wire it into `.pre-commit-config.yaml` as a repo-local hook beside `workflow-gate-integrity` (block at line ~441): `language: python`, `additional_dependencies: ['PyYAML>=6.0']`, `always_run: true`, `pass_filenames: false`. That places it in `static / Static CI Tests`, which `.github/workflows/build-static-tests.yaml` runs on **every push to every branch** and which is one of the two required contexts on `develop`.
  - New `src/backend/tests/unit/test_attest_registry_credentials_check.py`, loading the script via `from tests.support.repo_scripts import load_repo_script` and driving **constructed** workflows in `tmp_path` — never the real `.github/workflows`, for the reason the sibling test's docstring gives. It MUST carry a `TestItCanFail` class and a `TestTheIncident` class that reconstructs the pre-fix `publish-helm-charts` shape (a `helm registry login` `run:` step plus an attest step with `push-to-registry: true`) and pins that it is a finding.
- **Acceptance criteria** (all falsifiable, all observable on an ordinary pull request):
  1. **Red-first, against the real defect**: `git show origin/develop:.github/workflows/docker-publish.yml` into a temp dir, run the checker over it → exit 1, and the finding names job `publish-helm-charts` and the file. Capture that output in the PR body. *Falsified by*: exit 0.
  2. Run over the tree after P1 → exit 0.
  3. `pytest src/backend/tests/unit/test_attest_registry_credentials_check.py` green, including `TestItCanFail` and `TestTheIncident`.
  4. **Explicit falsification step, named**: delete the `docker/login-action` step from `publish-helm-charts` and run `task precommit`. The hook `attest-registry-credentials` **fails** and names the job; `static / Static CI Tests` would go red on that push. Restore the step and it passes. Record both observations in the PR body. *This is the package that proves the fix can be proven wrong.*
  5. `python3 scripts/check_workflow_gate_integrity.py` still reports `unjustified: 0` after the change (the new hook must not itself become a gate that cannot fail).
- **Touched files / artifacts**: `scripts/check_attest_registry_credentials.py` (new), `.pre-commit-config.yaml`, `src/backend/tests/unit/test_attest_registry_credentials_check.py` (new)
- **Specialist**: `nolte-engineering:fullstack-developer` — "implements features end-to-end across backend, frontend, and **infrastructure**, plus matching tests… against the consuming project's own tech stack, layout, and quality bar, detected at runtime". A Python checker plus its pytest suite plus a pre-commit wiring is that, and the runtime-detection requirement is what makes it copy the sibling's conventions rather than invent new ones.
- **Depends on**: none to author. Dispatch it **before** P1 so acceptance criterion 1 (red against the real, unfixed file) is a live observation rather than a reconstruction.

### P3 — Alert when the delivery lane goes red

- **Problem statement**: G-5 — runs 31955164085 and 31955579431 were red on `develop` for two days and nobody was told. `docker-publish.yml` is post-merge, so it can never turn a pull request red, and no `workflow_run` observer exists in the tree. This is the same failure class as #1210: a fact that is true, recorded, and unobserved.
- **Design**: a new `.github/workflows/delivery-run-alert.yml`, modelled on `release-lag.yml`'s alert half.
  - Trigger `on.workflow_run` with `workflows: ["Build & Publish Container Images"]` (the literal `name:` at line 1 of `docker-publish.yml`) and `types: [completed]`, plus `workflow_dispatch` with a `run_id` input (see AC 3 — this input is what makes the observer testable at all).
  - **Do not** gate the job with `if: github.event.workflow_run.conclusion == 'failure'`. A job that only exists on failure is skipped on success, and a skipped job reads green — the exact shape `scripts/check_workflow_gate_integrity.py` refuses. Run the job unconditionally and let the **script/step body** decide open-vs-close, so an API error can still make this run red. This mirrors `release-lag.yml`'s "hard errors exit non-zero here ⇒ the run goes red and the issue step below no-ops" contract (NFR-018 §2).
  - Behaviour: on `conclusion == 'failure'` for `develop` or a `refs/tags/v*` head, open **or update** the single deduped issue carrying a `delivery-lane-failure` label, naming the run URL, the failing job(s) and the failing step(s); on a subsequent `success`, comment and **close** it. `permissions: { issues: write, contents: read }` — nothing wider. `concurrency: { group: delivery-run-alert, cancel-in-progress: false }`, for the reason `release-lag.yml` states (two runs must not both act on the alert issue).
  - `workflow_run` executes the **default branch's** copy of the workflow, so this observer is inert until it merges — see R-3.
- **Acceptance criteria**:
  1. New `src/backend/tests/unit/test_workflow_run_references.py` asserts that every `on.workflow_run.workflows[*]` entry across `.github/workflows/` resolves to the `name:` of a workflow file that exists in the tree. *Falsified by*: renaming `Build & Publish Container Images` or mistyping it → the test goes red on the pull request. Without this, a typo silently produces an observer that observes nothing, which is the identical failure class this package exists to close.
  2. `python3 scripts/check_workflow_gate_integrity.py` reports `unjustified: 0` after the change (no `|| true`, no `continue-on-error: true`, no `needs.<x>.outputs` under an override without `.result`).
  3. **Runtime proof, no release needed**: `gh workflow run delivery-run-alert.yml --ref <branch> -f run_id=31955579431` (a measured failure) opens the alert issue naming that run and its failing step `Attest chart provenance`; a second dispatch with `-f run_id=32142079463` (a measured success) closes it. Both observations recorded in the PR body; the test issue is closed afterwards. *Falsified by*: no issue, an issue on the success case, or no close on recovery.
- **Touched files / artifacts**: `.github/workflows/delivery-run-alert.yml` (new), `src/backend/tests/unit/test_workflow_run_references.py` (new)
- **Specialist**: `nolte-shared:cicd-pipeline-design`
- **Depends on**: none

### P4 — Check the *outcome*: a published release carries its expected assets

- **Problem statement**: P3 watches the process (did the run go red). This watches the result (does the release actually have its artifacts). The distinction is load-bearing in this repository, whose named failure class is "a skipped step reads as green": `update-release-assets` was `skipped`, not failed, and the only place the loss is visible is the release page itself (G-4). A process check would not have caught a variant where the job is green and an asset is still absent.
- **Design**: modelled 1:1 on `scripts/ci/check_release_lag.py` + `.github/workflows/release-lag.yml`.
  - New `scripts/ci/check_release_assets.py`: for the newest **published** (non-draft, non-prerelease) release, assert the expected asset set — `kamerplanter-<version>.tgz`, `docker-compose-<version>.yml`, `.env.example-<version>`, `openapi.json` — and that the body contains the `<!-- kp:packages:begin -->` marker. Writes `release-assets-report.json` and exits 0 on a **determined** result; on an API error / unparseable payload it raises, prints `::error::`, exits non-zero and writes **no** report (fail-loud, NFR-018 §2 — an undetermined check is not a clean check, and a transient blip must not spam the tracker).
  - New `.github/workflows/release-assets-complete.yml`: scheduled daily at an hour not already taken (00:00 Nuclei, 01:00/01:17/01:30 security+E2E, 06:00 digest freshness, 09:00 release lag — pick e.g. 10:00 UTC and say why in the header), plus `workflow_dispatch`. `permissions: { contents: read, issues: write }` — unlike `release-lag.yml` this needs no draft visibility, so it must **not** copy that file's `contents: write`. Deduped open/update/close alert issue under a `release-assets-incomplete` label.
  - **Floor** (see R-4): only releases published **at or after** a configured floor are evaluated, defaulting to the first tag published after this fix merges. Without it the check opens an alert on v0.2.0 on day one and it stays open forever, because retro-fixing published releases is out of scope. The floor is a documented, dated decision in the script header, not a silent skip.
- **Acceptance criteria**:
  1. `src/backend/tests/unit/test_release_assets_check.py` green, with a `TestTheIncident` class built from the **measured** payloads: v0.2.0 (`assets == ["openapi.json"]`, body without the packages marker) ⇒ `alert == true` naming exactly the three missing assets plus the missing body block; v0.0.24 (`assets == ["default.env.example-0.0.24", "docker-compose-0.0.24.yml", "kamerplanter-0.0.24.tgz", "openapi.json"]`) ⇒ `alert == false`. Pinning both directions against real data is what stops the check certifying nothing. *Falsified by*: making the v0.2.0 case pass.
  2. A test pins the floor behaviour in both directions: a release published before the floor is not evaluated; one published after it is.
  3. An induced API error (a double raising) produces exit != 0 and **no** report file. *Falsified by*: a green exit or a report written on error.
  4. `workflow_dispatch` of the workflow on the branch completes and its verdict matches what the unit tests predict for the current release state.
  5. `python3 scripts/check_workflow_gate_integrity.py` reports `unjustified: 0` after the change.
- **Touched files / artifacts**: `scripts/ci/check_release_assets.py` (new), `.github/workflows/release-assets-complete.yml` (new), `src/backend/tests/unit/test_release_assets_check.py` (new)
- **Specialist**: `nolte-engineering:fullstack-developer` (script + tests + workflow, in the project's own detected conventions); the workflow half is re-checked by P5.
- **Depends on**: none. **Independently droppable** — see Q1.

### P5 — Read-only CI/CD review of the resulting workflow surface

- **Problem statement**: this strand adds two workflows and edits a third, on a delivery lane where a mistake is invisible until a release. It should be read by something whose only job is to find that.
- **Acceptance criteria**: the reviewer returns no Critical finding against `docker-publish.yml`, `delivery-run-alert.yml` and `release-assets-complete.yml`; every Warning is either fixed or answered in the PR body with a reason. Specifically confirmed: action SHAs pinned to digests, `permissions` least-privilege per job, `concurrency` present on both new alerting workflows, no untrusted `workflow_run` payload field interpolated into a `run:` or a script body (read via `process.env` / `github.event` in `github-script`, as `release-lag.yml` already does for `RUN_URL`).
- **Touched files / artifacts**: none (read-only report)
- **Specialist**: `nolte-shared:cicd-pipeline-reviewer` — "Read-only audit … stage sequence and omissions, floating references and unpinned actions, permission scope, untrusted-input handling, … artifact immutability and provenance. Returns severity-classified findings with file:line; applies no edits."
- **Depends on**: P1, P3, P4

## Dependency ordering

```
P2 ──▶ P1 ──┐
            ├──▶ P5
P3 ─────────┤
P4 ─────────┘
```

- **P2 first**, so its checker is red against the genuine unfixed `origin/develop` file before P1 exists. Red-first is the only thing that proves the guard measures the defect rather than a neighbouring statement.
- **P1** second; P2's checker turning green is P1's static acceptance criterion, and the workflow dispatch of §Verifying the fix is its runtime one.
- **P3** and **P4** are independent of both and of each other; they may be dispatched concurrently with P2/P1. Their file sets are disjoint (P3: `delivery-run-alert.yml`, `test_workflow_run_references.py`; P4: `check_release_assets.py`, `release-assets-complete.yml`, `test_release_assets_check.py`; P2: `check_attest_registry_credentials.py`, `.pre-commit-config.yaml`, `test_attest_registry_credentials_check.py`; P1: `docker-publish.yml`). **One shared-file caveat**: only P2 touches `.pre-commit-config.yaml`. If P3 or P4 ends up needing a hook there, serialise that edit — per the recorded convention that writing agents on a shared tree run sequentially.
- **P5** last, after P1/P3/P4 have landed in the branch.

## Verifying the fix without cutting a release

The operator asked this explicitly, and G-7 makes it sharper than expected: **merging this PR triggers no `docker-publish` run at all**, because `.github/workflows/**` is not in the workflow's `on.push.paths`. "Merge it and watch develop" is not available. Three layers, in increasing cost:

**V1 — static, on every pull request (free, permanent).** P2's checker. It reproduces the exact precondition the runtime failure depends on and runs in the required `static / Static CI Tests` lane on every push to every branch. It proves the *invariant*, not the runtime behaviour — so it is necessary and not sufficient.

**V2 — runtime, pre-merge, recommended.** `workflow_dispatch` is already in the chart job's condition (line 728), so a dispatch on the feature branch executes the real job with the real action against the real registry:

```bash
gh workflow run docker-publish.yml --ref fix/issue-1218-chart-attestation
```

Measured side effects, so the operator can consent to them rather than discover them:

- All eight image jobs run (their conditions also name `github.event_name == 'workflow_dispatch'`). They push `type=sha` and `type=ref,event=branch` tags. They do **not** touch `latest`: `type=raw,value=latest,enable={{is_default_branch}}` (line 127) is false on a feature branch. The branch-named tags are registry litter, removable afterwards.
- The chart job runs and pushes `oci://ghcr.io/nolte/charts/kamerplanter` at whatever `helm/kamerplanter/Chart.yaml` says — currently `0.2.0`, i.e. **the tag of a published release** (G-8).

**Therefore: bump `helm/kamerplanter/Chart.yaml` to a throwaway pre-release version (e.g. `0.2.0-issue1218.1`) on the branch before dispatching, and revert it before the PR merges** (P1 acceptance criterion 5 enforces the revert). This exercises the attest path end to end while touching no published reference, and gives a clean subject for `gh attestation verify oci://ghcr.io/nolte/charts/kamerplanter:0.2.0-issue1218.1 --repo nolte/kamerplanter`. It is strictly better than dispatching as-is, and better than waiting for a release.

**V3 — the observers, self-testable.** P3 is dispatchable against a historical `run_id`, so it can be proven against measured run 31955579431 (failure) and 32142079463 (success) without any release. P4 is dispatchable and unit-tested against the measured v0.2.0 and v0.0.24 payloads.

Note for after the merge: the **next** release tag is the first time the full path (chart asset upload + `update-release-assets` + the Packages block) runs for real, because those steps are tag-gated. V2 cannot cover them; P4 is what covers them, after the fact, within a day.

## Risks

- **R-1 — the fix is one "tidy-up" away from being undone.** Two logins to the same registry in one job looks redundant and is not. *Mitigation*: P2 is exactly this mitigation, and it is the reason P2 is a package rather than a nice-to-have; plus the mandatory rationale comment in P1.
- **R-2 — the verification dispatch overwrites a published chart tag.** *Mitigation*: the temporary pre-release version bump in V2, plus P1 acceptance criterion 5 asserting `Chart.yaml` is unchanged in the final diff. Note the same overwrite already happens on every `helm/**` merge to `develop` (G-8) — the dispatch adds no new class of harm, but this plan should not normalise it; see Q2.
- **R-3 — P3 is inert until it reaches `develop`.** `workflow_run` runs the default branch's copy, so the observer cannot observe anything from a feature branch. *Mitigation*: the `run_id` dispatch input (P3 AC 3) makes it provable pre-merge; and the PR body must state plainly that the trigger itself first arms on merge.
- **R-4 — P4 will alert on v0.2.0 immediately, and nobody is going to fix v0.2.0.** Retro-fixing published releases is explicitly out of scope, so an unfloored check produces a permanently-open issue, which trains everyone to ignore the label — worse than no check. *Mitigation*: the documented floor in P4's design, with its date and its reason in the script header, and a unit test pinning both sides of it.
- **R-5 — security review.** Assessed and **not required as a package**. The change introduces no new secret, no new permission scope, and no new trust boundary: it adds a `docker/login-action` step with `secrets.GITHUB_TOKEN`, identical to eight steps already in the same file, and the action masks the token and logs out in its post-step. The two new workflows take `issues: write` (narrower than `release-lag.yml`'s `contents: write`) and must read `workflow_run` payload fields via `process.env` / `github.event` rather than interpolating them into a script body — that specific untrusted-input check is delegated to P5 (`cicd-pipeline-reviewer`, whose description names untrusted-input handling). If P3's implementation ends up interpolating any run-supplied string into a `run:` block, escalate to `nolte-engineering:code-security-reviewer` before the PR.
- **R-6 — scope inflation.** Four build packages on a one-line root cause is a lot. The counterweight is measured: this defect survived 17 days and two published releases (G-4) because nothing observed it. P4 is the package to drop first if the strand needs to shrink (Q1); P2 is the one to keep under all circumstances, because it is the only package that makes the fix falsifiable.
- **R-7 — a merge conflict on `.pre-commit-config.yaml`.** It is a busy shared file. *Mitigation*: only P2 edits it; rebase before the PR.

## Open questions

- **Q1 — keep P4?** P3 (process) already alerts on any red delivery run; P4 (outcome) additionally catches a green run that nevertheless left a release incomplete, which is the shape that actually occurred here (`update-release-assets` was *skipped*, not failed). Recommendation: keep it, because "skipped reads as green" is this repository's most expensive recurring class. Drop it if a minimal strand is wanted — it has no dependents except P5.
- **Q2 — file a separate issue for G-8?** Every `helm/**` merge to `develop` republishes `oci://ghcr.io/nolte/charts/kamerplanter:0.2.0`, overwriting the chart of a published release, against `spec/project/continuous-delivery` §B as quoted in `scripts/ci/publish_release_asset.sh`. Found while planning, deliberately out of scope, needs its own decision (a `0.0.0-dev` / branch-suffixed develop version is the obvious shape).
- **Q3 — the `KNOWN GAP` follow-up is still open.** The eight `build-*` jobs still combine `always()` with `needs.changes.outputs.<x>` and never consult `needs.changes.result`; all eight carry the `needs follow-up` marker (measured: `check_workflow_gate_integrity.py --json`, 8 of 19 justified sites). It does **not** affect the chart job (G-6) and is not in this strand. Does it want its own issue, or is it already tracked?
- **Q4 — confirm P4's floor.** Recommendation: the first tag published after this PR merges. Confirm, and confirm that v0.1.0 and v0.2.0 stay unrepaired (the recorded out-of-scope decision) rather than being silently expected to alert.
- **Q5 — is the reduced consequence in G-4 worth an issue-body correction?** The issue says one asset is missing since v0.2.0; measured, it is three assets plus the release-notes Packages block, missing since v0.1.0. A comment on #1218 stating the corrected scope before the PR would keep the trail honest.

## Dispatch log

<!-- Appended during operation 5; one line per package once its specialist reports.
     <YYYY-MM-DD> P<k> dispatched to <subagent_type> — <result one-liner> -->
