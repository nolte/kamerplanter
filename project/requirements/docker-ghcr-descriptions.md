# Requirements — Docker/GHCR image descriptions overhaul

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/ (authoritative source at
claude-shared/spec/project/requirements-elicitation/en.md).
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back
or an authoritative operator answer.
-->

- **Working copy / branch:** `chore/docker-ghcr-descriptions` (off `origin/develop`)
- **Plan:** `.resume/docker-ghcr-descriptions/plan.md`
- **Governing constraint:** NFR-003 (source & GitHub-facing content in English)

## Bounded context

- **What:** Rewrite the human-authored `org.opencontainers.image.description` text
  for every published Kamerplanter container image so each reads as **one concise
  English sentence naming the container's concrete role *and* purpose** in the
  Kamerplanter system — not a restatement of the speaking image name (today
  "Kamerplanter embedding service" adds nothing a name doesn't). The text is
  maintained in **two synchronized places per image**: the `annotations:` block of
  the per-image `docker/metadata-action` step in
  `.github/workflows/docker-publish.yml` (this is what the GHCR package page
  renders, because `DOCKER_METADATA_ANNOTATIONS_LEVELS: manifest,index` already
  pushes it to the index level) and the in-file `LABEL
  org.opencontainers.image.description` in the prod Dockerfile (what `docker
  inspect` shows).
- **For whom:** People reading a Kamerplanter image on the GHCR package page or via
  `docker inspect` — operators, contributors, and anyone auditing the image set —
  who need to know at a glance what each container does.
- **8 published images (each its own `build-*` job):** `backend`, `frontend`,
  `vectordb`, `knowledge`, `embedding-service`, `inference-service`,
  `reranker-service`, `knowledge-service`.
- **Explicitly out of scope:** No label/workflow *plumbing* changes —
  `DOCKER_METADATA_ANNOTATIONS_LEVELS`, tags, `source`, `vendor`, `title`,
  digest-pinning, `USER`, ports all stay untouched. Only the `description` **value**
  changes. The non-published `tests/e2e/Dockerfile` (also carries a description
  label) is not a GHCR image and is left alone. No new images, no code changes.

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question
  budget = `3` (spec defaults; the requirement arrived code-grounded in the plan
  with the two load-bearing decisions — scope and language — already recorded
  `[confirmed]`, so the default risk posture applies and only one genuine
  specification question remained).
- `U_gate = min_d c_d` over required dimensions = **0.85**
- Termination: `saturation` (every required dimension ≥ `τ_high`; a single
  decision turn resolved the only open specification uncertainty — the
  description **focus** — via teach-back).

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.90 | interpretation | Two-place edit (annotations + LABEL) per image confirmed against `docker-publish.yml:98…449` and the 8 prod Dockerfiles; teach-back accepted |
| `non_functional` | yes | 0.90 | interpretation | English (NFR-003), one concise sentence, no marketing fluff, must not merely repeat the image name — confirmed |
| `constraints` | yes | 0.90 | interpretation | Plumbing untouched (`ANNOTATIONS_LEVELS`, tags, `source`, `title`, `vendor`, digest-pin, `USER`) — confirmed from plan invariants |
| `domain_objects` | yes | 0.90 | interpretation | The 8 images, the `annotations:` block, the in-file `LABEL …description` — enumerated from source |
| `actors` | yes | 0.85 | interpretation | GHCR package-page reader / `docker inspect` reader (operators, contributors) — identified |
| `acceptance_criteria` | yes | 0.85 | specification→resolved | Annotation text == label text per image; YAML intact; each sentence grounded in its Dockerfile; describes role+purpose |
| `edge_cases` | yes | 0.82 | interpretation | GHCR page refreshes only on next publish of each image; multi-target images (embedding/reranker) name the CI-default model; `knowledge` is an init/seed container, not a service |
| `scope_boundaries` | yes | 0.90 | specification→resolved | Only the description value; no plumbing, no code, `tests/e2e` excluded — authoritative answer |

_Self-consistency (`k≥2`) evidence event:_ two independent sketches of the
description **focus** diverged — sketch A (technical-role only: "FastAPI service
exposing the REST API") vs. sketch B (role **and** purpose: "core REST API and
business logic … for plant lifecycle, phases, fertilizing"). The divergence was
the ambiguity signal; it was resolved authoritatively to **role + purpose**
(operator answer "mach es für rolle und zweck").

## Requirements

<!-- EARS/CNL form; tagged confirmed/assumed with traceability. -->

- **R1 (per-image description text)** — For each of the 8 published images, the
  `org.opencontainers.image.description` SHALL be a single concise English
  sentence stating the container's concrete role **and** its purpose in the
  Kamerplanter system, grounded in that image's Dockerfile (base image, entrypoint,
  function), and SHALL NOT merely restate the speaking image name.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: plan Goal + teach-back "rolle und zweck"

- **R2 (two-place synchronization)** — WHEN the description of an image is changed,
  the framework SHALL apply the **identical** text in both the `annotations:` block
  of that image's `build-*` job in `.github/workflows/docker-publish.yml` and the
  in-file `LABEL org.opencontainers.image.description` of its prod Dockerfile, so
  the GHCR package page and `docker inspect` agree.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: plan Design decision (scope = annotations + in-file labels) `[confirmed]`

- **R3 (English only)** — Every description value SHALL be in English, per NFR-003
  (source & GitHub-facing content in English).
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: plan Invariants + NFR-003 `[confirmed]`

- **R4 (plumbing untouched)** — The change SHALL modify only the `description`
  value; `DOCKER_METADATA_ANNOTATIONS_LEVELS`, tags, `source`, `vendor`, `title`,
  digest pins, `USER`, and ports SHALL remain byte-for-byte unchanged.
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: plan Invariants

- **R5 (acceptance)** — The change SHALL be accepted only when, per image, the
  annotation text equals the label text, the workflow YAML remains parseable, and
  each sentence is verifiable against its Dockerfile. The PR SHALL note that GHCR
  package pages refresh only on the next publish of each image.
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: plan Work steps 4–5

- **R6 (multi-target & init-image accuracy)** — For multi-target images the
  description SHALL reflect the CI-default target (embedding-service → e5 family;
  reranker-service → BGE reranker v2 m3), and `knowledge` SHALL be described as an
  init/seed container (busybox copying knowledge YAMLs into a shared volume), not
  as a running service.
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: Dockerfile grounding (`docker/embedding-service`, `docker/reranker-service`, `docker/knowledge`)

### Final description text (grounded, role + purpose)

| Image | Final description |
|---|---|
| backend | `Kamerplanter core REST API and business logic (FastAPI) for plant lifecycle, phases, fertilizing, tasks and multi-tenant data` |
| frontend | `Kamerplanter web UI (React single-page app served by nginx) for managing plants, locations, tasks and dashboards` |
| vectordb | `PostgreSQL with the pgvector extension storing Kamerplanter's embedding vectors for RAG knowledge retrieval` |
| knowledge | `Init container that seeds Kamerplanter's RAG knowledge-base YAML files into a shared volume for the vector store` |
| embedding-service | `ONNX multilingual text-embedding service turning knowledge and queries into vectors for Kamerplanter's RAG pipeline` |
| inference-service | `Plant/pest image-recognition service (DINOv2 ONNX embeddings + pgvector matching) for Kamerplanter health assessment` |
| reranker-service | `ONNX cross-encoder reranker (BGE reranker v2 m3) that re-scores RAG retrieval hits for Kamerplanter` |
| knowledge-service | `Standalone RAG/LLM service answering plant-domain questions over Kamerplanter's knowledge base` |

## Surviving assumptions / open risks

- **GHCR page latency (R5).** The package-page description only updates on the next
  publish of each image; this is inherent to how GHCR renders the index annotation
  and is called out in the PR rather than fixed here.
- **Multi-target model naming (R6, `c_d = 0.82`).** embedding-service and
  reranker-service ship several model targets; the description names the CI-default
  model. If CI later changes its default target, the description would drift —
  acceptable residual, noted here.
