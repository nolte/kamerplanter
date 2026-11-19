# Group pre-analysis: 2026-11-19-zap-nginx-20020

> Run-scoped artifact. Committed on the integration branch, removed with a fix-forward
> `git rm` before the bundle merges. It must never reach the default branch, and it must
> never be hidden behind a `.gitignore` entry.

## Scope of this analysis

**Research question:** Why does ZAP rule `20020` fire on the frontend image since
`c110636d`, and what one change makes the post-merge scan on `develop` green again?

**The group's single logical change, in one sentence:** Pull the frontend's nginx base
image from the repository upstream now publishes to (`nginx/nginx-unprivileged`) at the
patched 1.31.9, so ZAP finding `20020` clears, Renovate sees nginx updates again, and the
post-merge scan stops filing one identical issue per merged commit.

**Out of scope:** `server_tokens off` (it would hide the version from rule 20020 and blind
the only signal that caught this; operator may overturn at the gate). A suppression row in
`tests/security/zap-rules.tsv` (not needed, a fixed image exists). The red ZAP nightly
(run 44484452708, setup step `HTTP 403`) and `e2e-nightly` (#3032): different causes.
Historical mentions of the old image name in `project/requirements/*.md` and the Renovate
dashboard fixtures (records of past state).

**Tier:** 2 — one repository, no published contract changes.

## Members

Handed on by `issue-backlog-partition` (`.audits/issue-backlog-partition/2026-11-19-zap.md`);
records re-checked against the live issues, none corrected.

| Issue | Class | Admitting predicate | Evidence |
|---|---|---|---|
| #3040, #3043, #3045, #3049, #3051, #3052, #3054, #3055, #3058, #3059 | security | thematic coupling | each body carries the same single finding line `` `20020` — nginx Version with Known Vulnerabilities (1 instance(s)) on http://frontend:8080 `` (`gh issue view <n> --json body`); author `github-actions[bot]` (untrusted, template text, no instruction); no comments, no linked PR |

**Dependency ordering:** independent — one change resolves all ten.

**Shared touch surface:** `src/frontend/Dockerfile:47`.

## Mode decision

**Mode:** A — single strand.

**Reason:** no member can be removed independently; all ten are reports of one cause.

**Working copy:** created after approval via `task worktree:add -- fix/2026-11-19-zap-nginx-20020`.

## Structural finding

**Cluster shape:** symptom cluster (confirms the partition's provisional kind; type `fix` confirmed).

**Asserted cause — verified.** The issues assert that the served nginx version has known
vulnerabilities. Measured:

- `baseline-report.json` of run 44546770694, alert 20020: evidence `nginx/1.31.7`, "10 known
  vulnerabilities: 0 critical, 3 high, 4 medium, 3 low" — CVE-2026-113425, -118899, -123007,
  -120967, -121810, -123633, -123634, -120993, -123640, -125283.
- `https://nginx.org/en/CHANGES`: "Changes with nginx 1.31.9 — 18 Nov 2026" lists all ten as
  fixed; `security_advisories.html`: "Not vulnerable: 1.31.9+", "Vulnerable: …-1.31.8".
  The advisories were published 2026-11-18, which is why run 44375296721 (18:57Z) still
  printed `PASS … [20020]` and run 44390022212 (20:20Z) printed `WARN-NEW` against an
  unchanged image digest and an unchanged `ZAP_IMAGE` digest.

**Root cause beneath the symptom.** `src/frontend/Dockerfile:47` pins
`nginxinc/nginx-unprivileged:1.31-alpine@sha256:b5047b9b…`. That Docker Hub repository is
frozen: its newest tag is `1.31.7-alpine` (2026-10-19), and
`https://hub.docker.com/v2/repositories/nginxinc/nginx-unprivileged/tags/1.31.8-alpine` and
`…/1.31.9-alpine` both return 404. Upstream (`nginxinc/docker-nginx-unprivileged` README
lines 25–30) now publishes to `nginx/nginx-unprivileged`: Docker Hub
`nginx/nginx-unprivileged:1.31-alpine` = `1.31.9-alpine`, pushed 2026-11-18T20:01Z, digest
`sha256:60214a103e6f38e953ff957f34b1f2e97a9db801ab2df3821da955d0fe6cadd6`; GHCR
`ghcr.io/nginx/nginx-unprivileged` carries `1.31.8-alpine` and `1.31.9-alpine` too. So the
project already missed 1.31.8 (2026-10-21) and Renovate would never have offered 1.31.9:
`renovate.json5:805` and the Dockerfile both name the dead repository.

**Exposure of the running config (my reading, not a test):** `src/frontend/nginx.conf`
listens on plain `8080`, no `ssl_*`, `http2`, `http3`, `resolver`, `alias`, mail or stream;
it does use `try_files` (line 64, without `alias`) and `proxy_pass`. Most of the ten need
features this config does not enable. That lowers urgency, it does not replace the bump.

**Second cause, for the ten-fold issue count:** `.github/workflows/security-zap-postmerge.yml:489`
calls `issues.create` unconditionally; nothing looks for an open issue with the same findings.

**Process finding:** a base image whose upstream repository was renamed keeps resolving and
keeps its digest, so neither Renovate nor `Renovate Health` reports anything; the only
alarm was a CVE scanner a month later. No rule in the repository checks that a pinned
image's repository still receives pushes.

**Preventive change:** a scheduled freshness check over the pinned third-party images
(newest tag of the pinned repository older than N days while the upstream project has
released → fail). Not in this lane — proposed as its own issue (operator question 2).

**Recurrence fed to the portfolio loop:** class "pin on an abandoned upstream coordinate",
count 1 (first recorded here).

## Plan approval

**Authorised by:** `2026-11-19-zap-nginx-20020/plan-approval` — approved by the operator 2026-11-19 (all five work packages; `server_tokens off` left out; process finding filed as its own issue).

**Group requirement artifact:** not applicable — symptom cluster.

## Work packages (one strand, in order)

1. `src/frontend/Dockerfile:47` → `FROM nginx/nginx-unprivileged:1.31-alpine@sha256:60214a10…cadd6 AS prod`
   (digest re-read with `docker buildx imagetools inspect` in the lane before it is written).
2. `renovate.json5:805` → `'nginx/nginx-unprivileged'` (keeps the image in the `third-party images` group).
3. `scripts/ci/probe_proxy_body_limit.sh:45,47` — the `sed` pattern and error text name
   `nginxinc\/nginx-unprivileged`; with the new name the probe would find no image and fail.
4. `docs/de/deployment/ci-cd.md:328`, `docs/en/deployment/ci-cd.md:328` — the quoted `FROM` line.
5. `security-zap-postmerge.yml` issue step: before `issues.create`, list open issues labelled
   `zap` whose title starts with `[zap-postmerge]`; if one has the same finding lines, add a
   comment with commit and run URL instead of opening a new issue. Bound: stays within the
   existing `github-script` step (no checkout, no new permission); if it needs more than
   ~20 lines it is filed as an issue instead (operator decision 2026-11-19).

## Completeness matrix

Rows collapse to one: every member is resolved by the same change.

| Member | Source (image) | Spec | Tests / guards | Docs | Config / workflows | Existing installations / upgrade / rollback |
|---|---|---|---|---|---|---|
| #3040 … #3059 (all ten) | `src/frontend/Dockerfile:47` new repository + digest; check: `docker build --target prod src/frontend` then `docker run … nginx -v` prints `nginx/1.31.9`, and `curl -sI` on `:8080` shows `Server: nginx/1.31.9` | not applicable — NFR-015 and NFR-009 already require what the change restores; no rule text changes | `scripts/ci/probe_proxy_body_limit.sh` pattern follows the new name; check: run the probe (`task` target in `.taskfiles/deploy.yaml:97`) and read its exit code. Backend guards that read `renovate.json5` / the workflow: `.venv/bin/python -m pytest tests/unit/guards -k "renovate or zap"` | `docs/{de,en}/deployment/ci-cd.md:328`; check: `grep -c nginxinc docs/*/deployment/ci-cd.md` → 0 | `renovate.json5:805`; check: `npx --yes renovate-config-validator renovate.json5`. Workflow de-dup; check: `actionlint` + `scripts/check_untrusted_checkout_permissions.py`. Final proof only after merge: the post-merge run on the squash commit prints `PASS … [20020]` — recorded as *not yet run* in the lane | upgraded state: an installation pulling the next frontend image gets nginx 1.31.9 from the same image line (same uid 101, port 8080, same paths — same Dockerfile project upstream); health gate: the chart's frontend probes; rollback restores the 1.31.7 image, nothing persisted is touched; note 1.31.9 "Change: header lines without a colon are rejected" and stricter chunked-framing limits apply to client requests through the proxy; check: probe script (413 limit) + e2e-smoke on the PR |

## Risks

- nginx 1.31.9 rejects malformed header lines and over-framed chunked bodies; a client that
  relied on either gets a 400. Covered only as far as e2e-smoke and the body-limit probe go.
- The new repository is the same upstream build, but that is taken from the README, not from
  a diff of the two images; the lane compares `nginx -V` and the image config (user, ports, entrypoint).
- The de-dup compares finding text; a wording change in `zap_gate.py` output opens a new issue (acceptable, fails open).

## Open questions for the operator

1. `server_tokens off`: left out on purpose (keeps rule 20020 able to see the version). Add it anyway?
2. File the process finding (no freshness check for pinned third-party image repositories) as its own issue?

## Member results

| Member | Specialist | Check | Actual output |
|---|---|---|---|
| — | — | — | filled during implementation |

## Deviations

| Member | Kind | What changed |
|---|---|---|

## Findings

| Finding | Source | Outcome | Reproduction | Issue |
|---|---|---|---|---|
