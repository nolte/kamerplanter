# Plan: Docker GHCR descriptions overhaul

Slug: `docker-ghcr-descriptions` · Branch: `chore/docker-ghcr-descriptions` (off `origin/develop`)

## Goal

Every published Kamerplanter container image must carry an
`org.opencontainers.image.description` that tells a reader **what the container
actually does in the Kamerplanter system** — not just a restatement of the
speaking image name (e.g. today "Kamerplanter embedding service" says nothing a
name doesn't already say). The improved text is a single concise English
sentence naming the container's concrete role. The description that GHCR shows
on the package page comes from the **index-level annotation** injected in
`.github/workflows/docker-publish.yml`; the in-file `LABEL` descriptions are
kept in sync so `docker inspect` and the registry page agree.

## Current state (researched)

- **Source of the GHCR-displayed description:** the `annotations:` block of the
  per-image `docker/metadata-action` step in
  `.github/workflows/docker-publish.yml`. `DOCKER_METADATA_ANNOTATIONS_LEVELS:
  manifest,index` is already set on every job — so the description already
  reaches the *index* level, which is what the GHCR package page renders. No
  workflow plumbing change is needed; only the text values.
- **8 published images** (each has its own `build-*` job + annotations block):
  `backend`, `frontend`, `vectordb`, `knowledge`, `embedding-service`,
  `inference-service`, `reranker-service`, `knowledge-service`.
- **Today's descriptions (verbatim, the thing to improve):**
  | Image | Current description |
  |---|---|
  | backend | `Kamerplanter backend API for plant lifecycle management` |
  | frontend | `Kamerplanter web frontend` |
  | vectordb | `Kamerplanter vector database for RAG knowledge retrieval` |
  | knowledge | `Kamerplanter RAG knowledge-base image` |
  | embedding-service | `Kamerplanter embedding service` |
  | inference-service | `Kamerplanter inference service` |
  | reranker-service | `Kamerplanter reranker service (BGE reranker v2 m3)` |
  | knowledge-service | `Kamerplanter knowledge service` |
- **In-file `LABEL org.opencontainers.image.description`** exists in the prod
  Dockerfiles (added during the 2026-07-10 Dockerfile audit remediation) and is
  overridden by the CI annotation at publish time — so both surfaces exist and
  should be aligned.
- Prior context: `.audits/dockerfile-audit/dockerfiles-2026-07-10.md` documents
  the label landscape; the dockerfile-audit skill's scanner explicitly checks
  that GHCR images wire index-level annotations (already satisfied here).

## Design decision (load-bearing)

**Edit the human-authored description *text* in two synchronized places per
image — the `annotations:` block in `docker-publish.yml` and the in-file
`LABEL … .description` in the Dockerfile — leaving all workflow/label *plumbing*
untouched.** English text, one concrete sentence per image describing its role
in the Kamerplanter architecture.

Confirmed open questions (answered before work start):
- **Scope → Annotations + in-file LABELs** (keep GHCR page and `docker inspect`
  consistent). *[confirmed]*
- **Language → English** (registry/GitHub-facing content, consistent with
  NFR-003 and existing descriptions). *[confirmed]*

Still to confirm **during** the work (verify, don't assume):
- The *exact* role wording per service must be grounded in each Dockerfile's
  header/base image, not guessed. Candidate wordings below are a starting point
  and MUST be checked against the actual Dockerfile + known architecture before
  writing.

### Candidate descriptions (draft — verify each against the Dockerfile first)

| Image | Draft description |
|---|---|
| backend | `Kamerplanter core API and business logic (FastAPI): plant lifecycle, phases, fertilizing, tasks and multi-tenant data` |
| frontend | `Kamerplanter web UI (React SPA served by nginx) for managing plants, locations, tasks and dashboards` |
| vectordb | `PostgreSQL + pgvector store holding the embedding vectors for Kamerplanter's RAG knowledge retrieval` |
| knowledge | `Seed/init image bundling the RAG knowledge-base YAML chunks loaded into Kamerplanter's vector store` |
| embedding-service | `ONNX text-embedding service turning knowledge and queries into vectors for Kamerplanter's RAG pipeline` |
| inference-service | `Plant/pest image-recognition service (few-shot DINOv2 + pgvector) for Kamerplanter health assessment` |
| reranker-service | `Cross-encoder reranker (BGE reranker v2 m3) that re-scores RAG retrieval hits for Kamerplanter` |
| knowledge-service | `Standalone RAG/LLM service answering plant-domain questions over Kamerplanter's knowledge base` |

## Work steps (ordered)

1. Read each of the 8 Dockerfiles' headers + `FROM`/base to confirm the actual
   role, then finalize each description sentence (correct any draft above).
2. Update the `annotations:` `org.opencontainers.image.description=…` line in
   each `build-*` job of `.github/workflows/docker-publish.yml` (8 edits).
3. Update the matching in-file `LABEL org.opencontainers.image.description` in
   each prod Dockerfile to the identical text (8 edits).
4. Sanity-check: no YAML break in the workflow (`yamllint` / `act` dry-run or at
   least a careful diff); grep that annotation text == label text per image.
5. Open a PR to `develop` via `pull-request-create` (chore). Note in the PR that
   GHCR package pages refresh only on the next publish of each image.

## Invariants / guardrails

- Source code & GitHub-facing content in **English** (NFR-003); German only for
  operator-facing chat.
- Do **not** touch label *plumbing*: keep `DOCKER_METADATA_ANNOTATIONS_LEVELS`,
  tags, `source`, `vendor`, `title`, digest-pinning, `USER`, etc. unchanged.
- Feature work happens only in this worktree; primary checkout stays on
  `develop`. Never commit from a `.claude/worktrees/` path.
- Only the `description` value changes — one concise, accurate sentence; avoid
  marketing fluff and avoid merely repeating the image name.

## Status / resume-anchor checklist

- [x] Worktree created (`chore/docker-ghcr-descriptions`)
- [x] Scope + language decided (annotations + in-file labels; English)
- [x] Requirement captured via `requirements-elicit` (`project/requirements/docker-ghcr-descriptions.md`; U_gate 0.85; focus = role+purpose)
- [x] Step 1 — confirm each service's role from its Dockerfile; finalize texts
- [x] Step 2 — update 8 `annotations` descriptions in `docker-publish.yml`
- [x] Step 3 — update 8 in-file `LABEL` descriptions in the prod Dockerfiles
- [x] Step 4 — validate (YAML parses OK; all 8 annotation==label synced; diff = description lines only, no plumbing)
- [ ] Step 5 — open PR to `develop` (`pull-request-create`)
