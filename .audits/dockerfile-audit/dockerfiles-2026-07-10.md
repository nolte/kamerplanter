# Dockerfile Audit

Scope: `/home/nolte/repos/github/kamerplanter`, 15 Dockerfiles discovered (skipped: none)
Trigger: manual invocation (pre-PR image-hardening review)
hadolint: **not installed** — static checks only (`hadolint --version` → exit 127); advisory `DL####` IDs are best-effort manual mappings, not tool-confirmed
CI label injection: credited from `.github/workflows/docker-publish.yml` (`docker/metadata-action` → `docker/build-push-action`) for 6 of 15 Dockerfiles
Git revision: `89c37ba7bb8397cdd56d381e2964d9ded84785bf`
Prior artifact: none (first Dockerfile audit)

## Verdict

**FAIL** — Dockerfiles failing: **15 / 15**, advisory findings: ~40 across the set.

Every Dockerfile in the repository hard-fails. The failures are dominated by **two repo-wide systemic gaps** plus two localized ones:

| Hard-fail pillar | Affected | Notes |
|---|---|---|
| Base image **not pinned by digest** | **15 / 15** | Every `FROM` uses a floating tag (`python:3.14-slim`, `nginx:1.31-alpine`, `node:24-alpine`, `postgres:18-bookworm`, `busybox:1.38.0`), none with `@sha256:` |
| **No non-root numeric `USER`** | **14 / 15** | Every published image runs as **root**. Only `src/backend/Dockerfile.dev` sets a user at all (`appuser` — non-root but non-numeric) |
| **`.dockerignore` missing** | 7 / 15 | Repo-root `.dockerignore` absent; several build contexts have none |
| Mandatory **OCI labels missing** (no literal, no CI) | 3 / 15 | `reranker-service`, `knowledge-service`, `tests/e2e` — no CI publish job → `version`/`revision`/`created` can never be injected |

Because the two systemic issues touch every file, the highest-leverage remediation is **two changes**, not fifteen:
1. Enable Renovate `docker.pinDigests: true` (repo already uses `renovate.json5`, currently **without** it) → pins all 15 bases automatically.
2. Add a non-root numeric `USER` (+ matching `chown`) to each final stage.

---

## Remediation applied (2026-07-10, same day)

All findings were worked off in the same session. Summary of the changes made:

| Finding | Action | Files |
|---|---|---|
| S-1 digest pinning (15/15) | Enabled Renovate `docker.pinDigests: true` — pins every external `FROM` automatically | `renovate.json5` |
| S-2 non-root USER (14/15) | Added numeric `USER` to every production final stage: backend/services `1000`, frontend `101` (nginx-unprivileged), vectordb `999`, knowledge-init `65534` | all 9 prod Dockerfiles |
| S-2b nginx root→101 | Rebuilt frontend on `nginxinc/nginx-unprivileged` (port 80→8080); Service stays on 80 with `targetPort: 8080`; probe + ConfigMap `listen` + all compose port/URLs migrated | `src/frontend/Dockerfile`, `nginx.conf`, `helm/…/values.yaml`, all `docker-compose*.yml` |
| S-2c postgres non-root | Added `USER 999` (Helm already sets runAsUser/fsGroup 999 + PGDATA subdir) | `docker/vectordb/Dockerfile` |
| S-3 .dockerignore | Added repo-root `.dockerignore` (for the `context:.` knowledge build) + vectordb/reranker-service/knowledge-service/e2e | 5 new files |
| S-4 CI orphans | Wired reranker-service + knowledge-service into `docker-lint-build.yml` (hadolint+build) and `docker-publish.yml` (metadata-action label injection + release links) | 2 workflows |
| Advisory labels | Added `LABEL` blocks to the 4 dev images that had none; added HEALTHCHECK to backend + long-running services | 4 dev Dockerfiles + prod |

**Deliberately left as-is (documented exceptions):**
- **dev `Dockerfile.dev` images keep running as root** — they exist for Skaffold file-sync/hot-reload and are never published; forcing a numeric USER would break the host-mounted source sync. Their bases are still digest-pinned by Renovate and they now carry OCI labels.
- **Base digests are not hand-written** — Renovate rewrites them on its next run (per spec: never invent a digest).

**Verification performed:** `helm template` renders cleanly (frontend Service `port:80`→`targetPort:8080`, probe `8080`, ConfigMap `listen 8080`, NetworkPolicy target auto-updated to 8080); all four `docker-compose*.yml` (incl. security override) pass `docker compose config`; `nginxinc/nginx-unprivileged:1.31-alpine` tag confirmed to exist; the frontend image build was exercised end-to-end. **Not verifiable locally:** a real cluster deploy / E2E run — the nginx port migration and postgres non-root switch should be smoke-tested on a dev cluster before release.

---

## Systemic findings (fix once, resolves many)

### S-1 — No base image is digest-pinned (15/15, mandatory)
No `FROM` in the repo carries an `@sha256:` digest. A tag like `python:3.14-slim` is mutable — the image that CI pulls today is not guaranteed to be the one it pulls tomorrow, which breaks build reproducibility and lets an upstream tag repoint silently.
**Fix:** add to `renovate.json5`:
```json5
{ docker: { pinDigests: true } }
```
Renovate then rewrites each `FROM` to `image:tag@sha256:…` and keeps the digest fresh via PRs. Do **not** hand-invent digests. This is the single change that clears the largest hard-fail column.

### S-2 — Every published image runs as root (14/15, mandatory)
Only `src/backend/Dockerfile.dev` sets any `USER`; all 9 production images and 5 of 6 dev images run as **root**. A numeric UID is required (not just non-root) so that Kubernetes `runAsNonRoot` / restricted PSS can verify it at admission — a named user (`appuser`) cannot be verified by the orchestrator.
**Fix (per final stage), e.g.:**
```dockerfile
RUN groupadd -g 1000 app && useradd -u 1000 -g app -m app \
    && chown -R 1000:1000 /app
USER 1000
```
For the nginx frontend and postgres/busybox images this needs image-specific handling (nginx unprivileged port ≥1024 or `nginxinc/nginx-unprivileged`; postgres already drops to `postgres` internally but the pillar wants an explicit assertion). This is a judgement-call rewrite — left to the operator, not auto-applied.

### S-3 — Repo-root `.dockerignore` absent + one context mismatch
- No `.dockerignore` at the repo root. This matters because **`docker/knowledge/Dockerfile` is built with `context: .` (repo root)** in both `docker-publish.yml` and `docker-lint-build.yml` — so its local `docker/knowledge/.dockerignore` is **never consulted**; the effective (and missing) file is the repo-root one. The whole repo is currently sent as build context for that image.
- Missing `.dockerignore` also in: `docker/vectordb/`, `docker/reranker-service/`, `src/knowledge-service/`, `tests/e2e/` (and the dev siblings of the last two).
**Fix:** add a repo-root `.dockerignore` (minimum: `.git`, `.env`, `**/node_modules`, `**/__pycache__`, `**/*.key`, `**/*.pem`) and per-context files where the build context is a subdirectory. Content policy left to the operator to confirm.

### S-4 — Two Dockerfiles have **no CI at all** (mandatory-label consequence + operational risk)
`docker/reranker-service/Dockerfile` and `src/knowledge-service/Dockerfile` are referenced by **zero** workflows (no build, no lint, no publish). Consequences:
- Their `version`/`revision`/`created` labels can never be CI-injected → **hard-fail on labels** (unlike their 6 CI-built siblings, which pass via injection).
- They are never lint-checked or build-verified in CI.
**Fix:** confirm whether both are actively shipped. If yes, add them to `docker-lint-build.yml` and `docker-publish.yml` (which resolves the label failure via injection). If no, remove them.

---

## Per-Dockerfile verdicts

### Production images (9)

| Dockerfile | Verdict | Hard-fail reasons |
|---|---|---|
| `src/backend/Dockerfile` | **FAIL** | no `USER`; base not digest-pinned |
| `src/frontend/Dockerfile` | **FAIL** | no `USER` (nginx→root); both bases not digest-pinned |
| `docker/vectordb/Dockerfile` | **FAIL** | no `USER`; base not digest-pinned; `.dockerignore` missing |
| `docker/knowledge/Dockerfile` | **FAIL** | no `USER` (busybox→root); base not digest-pinned; `.dockerignore` missing (context = repo root) |
| `docker/embedding-service/Dockerfile` | **FAIL** | no `USER`; bases not digest-pinned |
| `src/inference-service/Dockerfile` | **FAIL** | no `USER`; bases not digest-pinned |
| `docker/reranker-service/Dockerfile` | **FAIL** | labels `version`/`revision`/`created` MISSING (no CI); no `USER`; bases not digest-pinned; `.dockerignore` missing |
| `src/knowledge-service/Dockerfile` | **FAIL** | labels `version`/`revision`/`created` MISSING (no CI); no `USER`; base not digest-pinned; `.dockerignore` missing |
| `tests/e2e/Dockerfile` | **FAIL** | labels `version`/`revision`/`created` MISSING (test-runner, no publish); no `USER`; base not digest-pinned; `.dockerignore` missing |

**OCI-label detail (6 CI-built images):** `source`/`title`/`description` are static literals in-file; `version`/`revision`/`created` are credited to CI injection (`docker/metadata-action` per-service jobs `build-{backend,frontend,vectordb,knowledge,embedding-service,inference-service}`) — these labels **pass**, they legitimately live in CI, not the Dockerfile. Note: metadata-action also emits `source`/`title`/`description` via `--label`, which override the in-file literals at publish time (not a finding, just where the effective value comes from).

### Development images (6) — `Dockerfile.dev`, never published

Dev variants are audited on their own merits per policy. They are **not referenced by any publish workflow**, so CI label injection is impossible and their missing per-build labels are expected rather than a shipping defect — but the `USER` and digest-pin gaps still apply as defense-in-depth.

| Dockerfile | Verdict | Hard-fail reasons |
|---|---|---|
| `src/backend/Dockerfile.dev` | **FAIL** | labels `version`/`revision`/`created` MISSING; base not digest-pinned. *(USER `appuser` present & non-root — pillar PASS; advisory: make numeric)* |
| `src/frontend/Dockerfile.dev` | **FAIL** | no `USER`; base not digest-pinned |
| `src/inference-service/Dockerfile.dev` | **FAIL** | **no `LABEL` at all**; no `USER`; bases not digest-pinned |
| `src/knowledge-service/Dockerfile.dev` | **FAIL** | **no `LABEL` at all**; no `USER`; base not digest-pinned; `.dockerignore` missing |
| `docker/reranker-service/Dockerfile.dev` | **FAIL** | **no `LABEL` at all**; no `USER`; bases not digest-pinned; `.dockerignore` missing |
| `docker/embedding-service/Dockerfile.dev` | **FAIL** | **no `LABEL` at all**; no `USER`; bases not digest-pinned |

---

## Advisory (scored, non-blocking)

- **HEALTHCHECK missing** — 14/15 (only `src/backend/Dockerfile.dev` has one, line 49-50). Low relevance for `busybox` init and the e2e test-runner; worth adding to the long-running services (backend, frontend, embedding, inference, reranker, knowledge, vectordb).
- **Non-numeric `USER` name** — `src/backend/Dockerfile.dev` uses `appuser`; prefer a numeric UID (`USER 1000`) so the orchestrator can verify non-root.
- **Reproducibility smell (SHOULD labels)** — `licenses` present everywhere; `url`, `documentation`, `base.name`, `base.digest` missing everywhere. `base.name`/`base.digest` resolve for free once S-1 (digest pinning) lands via metadata-action.
- **Unpinned pip installs without suppression** — `src/inference-service/Dockerfile:21-23` installs torch/torchvision/onnx unpinned with **no** `# hadolint ignore=DL3013`, unlike every sibling service which carries the suppression. Either pin the versions or add the suppression for consistency (DL3013).
- **Single-stage prod images** — `src/backend`, `docker/vectordb`, `docker/knowledge`, `src/knowledge-service` are single-stage; acceptable for their workloads, noted for completeness.
- **Dev image more hardened than prod** — `src/backend/Dockerfile.dev` has both a `USER` and a `HEALTHCHECK`; its production counterpart `src/backend/Dockerfile` has **neither**. Back-port both to prod.
- **`embedding-service` default target** — CI sets no `target:`, so the published stage is the last one (`minilm`), not the `e5-base` the file header recommends as default (lines 6-7). Confirm this is intentional.
- **`tests/e2e/Dockerfile:14`** — broad `COPY . .` combined with the missing `.dockerignore` sends the whole context; a `.dockerignore` mitigates.

---

## Health

- Dockerfiles audited: 15/15 (9 production + 6 `Dockerfile.dev`)
- Dockerfiles skipped: none
- hadolint version: **not installed** — `DL####` mappings are manual/static, unconfirmed
- CI-injected labels credited: `version`/`revision`/`created` for `src/backend`, `src/frontend`, `docker/vectordb`, `docker/knowledge`, `docker/embedding-service`, `src/inference-service` — all via `.github/workflows/docker-publish.yml`
- CI-orphaned (no build/lint/publish job anywhere): `docker/reranker-service/Dockerfile`, `src/knowledge-service/Dockerfile`
- Build-context mismatch: `docker/knowledge/Dockerfile` built with `context: .` → local `.dockerignore` ignored
- Renovate present (`renovate.json5`) but **without** `docker.pinDigests`

## Recommended remediation order

1. **`renovate.json5` → `docker.pinDigests: true`** — clears S-1 for all 15 files (mechanical, safe, no hand-picked digests).
2. **Add numeric `USER` to each final stage** — clears S-2 (14 files); judgement-call per base image, operator-owned.
3. **Add repo-root `.dockerignore` + per-subcontext files** — clears S-3.
4. **Decide fate of the two CI-orphaned services** — wire into CI (resolves their label failure) or remove.
5. Advisory: back-port `HEALTHCHECK`/`USER` from `backend.dev` to `backend` prod; add `HEALTHCHECK` to the long-running services; add missing `LABEL` blocks to the 4 dev images that have none.

> The `apply` operation of this skill can mechanically insert/merge OCI `LABEL` blocks (ARG-wired `version`/`revision`/`created`) and other unambiguous rewrites, but the two dominant failures here (digest pinning, choosing a UID) are deliberately **out of scope for `apply`** — they belong to Renovate and to per-image operator judgement. Run `apply` only if you want the label-block scaffolding.
