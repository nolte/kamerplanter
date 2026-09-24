# Group pre-analysis: 2026-09-24-ml-sidecar-hardening

> Run-scoped artifact. Committed on the integration branch, removed with a fix-forward
> `git rm` before the bundle merges. It must never reach the default branch, and it must
> never be hidden behind a `.gitignore` entry.

## Scope of this analysis

**Research question:** Which defects from the #1480 security review of the two ML
side-services (`docker/embedding-service`, `docker/reranker-service`) are real on
`origin/develop` 288432867, which of them exist in the sibling image as well, and what
is the smallest change that closes all of them without changing what either service
computes?

**The group's single logical change, in one sentence:** Harden the two ONNX ML
side-service images so that every model byte they ship is pinned and verified, and so
that they run with bounded input, a cgroup-sized thread budget, root-owned read-only
runtime files, no uv in the runtime image, and no port published beyond localhost.

**Out of scope:**
- `transformers` in `docker/embedding-service` (the reranker dropped it in #1480; the
  embedding service still tokenizes through `AutoTokenizer`). Swapping it is a separate
  parity question with its own tokenizer measurement, not a hardening of this change.
- Other Compose services that publish on all interfaces (ArangoDB 8529, Valkey 6379,
  pgvector 5433/5432, Ollama 11434, backend 8000, frontend 8080). Recorded under
  `## Class sweep` in the PR, not fixed here: several are the documented developer
  entry points, changing them is a separate decision.
- `.github/lane-inputs/` manifests (issue #1730 owns the refresh; operator instruction).
- `src/inference-service` (not a sidecar of this pair; its model is fetched via
  `torch.hub`, outside the HF guard's corpus).

**Tier:** 2 — two services plus chart/compose/CI in one repository, no published
cross-repository contract. The HTTP contract of `/rerank` and `/embed` gains bounds,
but both services' only caller is `src/knowledge-service` in this repository.

## Members

| Issue | Class | Admitting predicate | Evidence |
|---|---|---|---|
| #1724 | security | thematic coupling (both from the #1480 security review of the ML side-services) + shared touch surface | `docker/embedding-service/Dockerfile` dl-* stages; guard `_UNPINNED_ALLOWED` in `src/backend/tests/unit/guards/test_hf_model_fetches_pin_a_revision.py:386-391` names all four fetches → "#1724" |
| #1725 | security | thematic coupling + shared touch surface | `docker/reranker-service/main.py` `RerankRequest` (only `top_k` bounded); `docker-compose.yml:113-114` `"8081:8081"`; runtime stage `chown -R 1000:1000 /app`; `helm/kamerplanter/values-dev-ki.yaml:127-128,178-179` `readOnlyRootFilesystem: false` |

**Dependency ordering:** #1724 first, then #1725. Both change the runtime stage of
`docker/embedding-service/Dockerfile` (#1724 adds `HF_HUB_OFFLINE` and the verified
model copy; #1725 restructures the stage so uv leaves it and files stay root-owned).
Doing the pin first keeps the parity measurement against today's runtime stage free of
the #1725 restructure.

**Shared touch surface:** `docker/embedding-service/Dockerfile` (both),
`docker/embedding-service/main.py` (#1725 scope extension), and — through the scope
decision below — `helm/kamerplanter/values-dev-ki.yaml` for both controllers.

## Scope decision: the embedding-service siblings of #1725

#1725 names only the reranker. Measured on `origin/develop` 288432867, the embedding
service carries the SAME pre-existing weaknesses (the #1402/#948 lesson: a guard fixed
at one of two siblings is the drift class):

| #1725 finding | reranker | embedding | decision |
|---|---|---|---|
| unbounded request body | `RerankRequest.query/documents` | `EmbedRequest.texts/prefix/model` unbounded (`main.py:39-42`) | IN scope — same change |
| `intra_op_num_threads = os.cpu_count()` | `main.py` `_preload` | `main.py:66` identical | IN scope |
| concurrent `session.run` per request | yes (sync route, threadpool) | yes | IN scope — serialize inference |
| `chown -R 1000:1000 /app` + `COPY --chown=1000` | yes | yes (identical runtime stage) | IN scope |
| `/bin/uv` in runtime image | yes | yes | IN scope |
| `readOnlyRootFilesystem: false` in chart | `values-dev-ki.yaml:127-128` | `values-dev-ki.yaml:178-179` | IN scope |
| port published on all interfaces in Compose | `docker-compose.yml:114` | not in Compose at all | reranker only; embedding `not applicable` |

The bounds need the caller to respect them. The embedding caller
(`src/knowledge-service/app/ingestor.py:118`) sends ALL chunks of one YAML file in one
call; today's corpus maximum is 16 chunks/file and 3525 chars/chunk (measured over
`spec/knowledge/rag/**/*.yaml`, 61 files, 432 chunks). A service-side count cap alone
would turn a future larger file into an ingest failure, so
`src/knowledge-service/app/embedding.py` `embed_batch` slices its request below the cap.

## Mode decision

**Mode:** A — single strand.

**Reason:** Both members share the embedding runtime stage, so sub-branches would
manufacture conflicts. Neither member's acceptance is uncertain: #1724 pins the
revision today's image already downloads (parity is measured byte-for-byte before the
pin), and #1725's criteria are mechanically checkable in this run. The security review
that could reject a member runs on the bundle before it is declared ready.

## Structural finding

**Cluster shape:** class cluster — "a hardening applied to one sibling image and not
to the other", plus "a trust decision (pin, bound, ownership) that lived only at the
call site".

**Root cause or defect class:** Both images were written as copies of one template
(identical runtime stage, identical `_preload`), and every hardening since (#1374 lock,
#1480 pin + verify, #1609 readiness) was applied per-image by whoever touched one. The
reranker got the pin in #1480; the embedding service got an allow-list entry.

**Process finding:** none new — the drift class is already recorded (memory:
"Guard opt-in am Aufrufort → Drift zwischen Geschwistern"). The preventive change for
THIS pair is structural: the new limits test is parametrized over both service
directories, so a bound or thread-budget rule applied to one image and not the other
is red.

**Preventive change:** `src/backend/tests/unit/guards/test_ml_sidecar_limits.py`
(new) runs the same assertions against both services' `limits.py`; the HF-pin guard's
allow-list becomes empty and stays enforced.

**Recurrence fed to the portfolio loop:** sibling-drift class, 1 more occurrence
(already tracked; no new issue).

## Completeness matrix

| Member | Source (services) | Tests / guards | Config (Compose, chart, CI) | Docs | Spec | Generated index |
|---|---|---|---|---|---|---|
| #1724 | `docker/embedding-service/Dockerfile` four dl-* stages: `revision=<40-hex>`, explicit `mv`, `sha256sum -c --strict`; runtime `HF_HUB_OFFLINE=1`; check: `docker build --target <each>` + parity script | `test_hf_model_fetches_pin_a_revision.py`: allow-list emptied, stale/vacuity tests kept meaningful; check: guards lane with `--max-skipped 0`, red-first against develop Dockerfile | not applicable — no Compose/chart/CI reference names a revision | `docs/{de,en}/adr/006-*.md` pinning note; check: `mkdocs build --strict` | not applicable — ADR-006 is the governing record, no spec names HF revisions | not applicable — lane-inputs refresh owned by #1730 (operator) |
| #1725 | `docker/reranker-service/{main.py,limits.py,Dockerfile}` and the embedding siblings: request bounds → 422, `cpu_budget()` from affinity+cgroup, inference lock, runtime stage without uv, root-owned files; `src/knowledge-service/app/embedding.py` slices batches; check: image build + live probe (/ready, /rerank normal/empty/over-limit, /embed) under `--read-only --cap-drop ALL --user 1000` | new `test_ml_sidecar_limits.py` (both services, loaded from the same file production imports); knowledge-service `test_embedding.py` slicing; `test_model_images_prove_readiness.py` still green; check: pytest, red-first | `docker-compose.yml` `127.0.0.1:8081:8081`; `values-dev-ki.yaml` `readOnlyRootFilesystem: true` + `/tmp` emptyDir for both controllers; `scripts/ci/smoke_model_image.sh` HTTP form runs read-only; check: `docker compose config`, `helm template`, smoke script | `ai-architecture.md` (DE/EN) request bounds; `docker-quickstart.md` (DE/EN) localhost-only note; check: `mkdocs build --strict` | not applicable — REQ-031/NFR text does not fix a request bound or port binding for these services (grep: no hit) | not applicable — #1730 |

## Risks

- Parity: if HF `main` moved since the last image build, "today's image" and the pin
  differ. Mitigation: build the reference image in this run and compare sha256 of every
  kept file plus embeddings.
- `--read-only` could break a library that writes on import (transformers cache dir,
  Python bytecode). Mitigation: run both images read-only locally and in CI smoke.
- A bound below a real caller's input would turn a working RAG query into a fallback.
  Mitigation: bounds derived from measured caller maxima (see scope decision).

## Open questions for the operator

- none blocking (all gates pre-approved 2026-09-24).

## Member results

| Member | Specialist | Check | Actual output |
|---|---|---|---|
| #1724 | cause verification (orchestrator) | `pytest tests/unit/guards/test_hf_model_fetches_pin_a_revision.py -q --max-skipped 0` on 288432867 | `65 passed` incl. 4× `test_every_allowance_names_an_unpinned_fetch` → the four fetches ARE unpinned (cause established) |
| #1724 | measurement (orchestrator) | sha256 of every kept file, today's image (`kp-sidecar-before-emb:<t>`, built from 288432867) vs pinned (`kp-sidecar-1724-emb:<t>`) | e5-small / e5-base / e5-large / minilm: `files identical: YES` ×4 |
| #1724 | measurement (orchestrator) | model-level embeddings (same 7 inputs, `passage: ` prefix, identical AutoTokenizer+ORT path) before vs after | max abs diff `0.0` for all four models |
| #1724 | measurement (orchestrator) | `/embed` endpoint before vs after | e5-base `0.0`, e5-large `0.0`, minilm `0.0`; e5-small before = **HTTP 500** (see Deviations), after = 200, max abs diff vs before-model-level `5.9e-08` (JSON float round-trip) |
| #1724 | `nolte-engineering:fullstack-developer` | guard red-first: new guard vs develop Dockerfile (via `cp`) | `5 failed, 82 passed` (non-vacuity names the 4 unpinned fetches; 4× `test_fetch_names_a_commit` `revision=None`); sha check removed on e5-base → `1 failed, 90 passed`; minilm fetch removed → `1 failed, 65 passed` (per-Dockerfile minimum); restored → `91 passed` |
| #1724 | `nolte-engineering:fullstack-developer` | feed test vs develop `main.py` (via `cp`) | `3 failed, 6 passed` (wiring tests); restored `9 passed`; all guards + feed `1088 passed, 49 deselected` |
| #1725 | cause verification (orchestrator) | `docker run --cpus 2 <reranker develop>` | `cpu_count 8 affinity 8 cpu.max 200000 100000` → 8 threads under a 2-CPU limit (cause established; embedding identical code) |
| #1725 | cause verification (orchestrator) | as UID 1000 in both develop images: `test -w`; `ls /bin/uv` | `WRITABLE /app/main.py`, `/app`, model files (both images); `/bin/uv` present (both) |
| #1725 | cause verification (orchestrator) | `docker compose --profile vectordb config` reranker ports | `{target: 8081, published: "8081"}`, no host_ip → all interfaces |
| #1725 | cause verification (orchestrator) | `-m 4g --cpus 2`, docs >512 tokens, POST /rerank N=20/100/400 | `200 in 112 s` / `OOMKilled` / `OOMKilled` — issue said "a few thousand"; measured: 100 already OOMs |
| #1725 | measurement (orchestrator) | e5-large POST /embed N=16/64, same limits | `200 in 70 s` / `OOMKilled` |
| #1725 | measurement (orchestrator) | per-call batch size B in-container, N=20 reranker / N=16 e5-large | B=full 56.5 s/47.9 s, 3001/2293 MiB; B=4 54.8/42.2 s, 1852/1845 MiB; **B=1 31.9/24.7 s, 1595/1650 MiB**; outputs vs full batch max abs diff `0.0`, same ranking |

## Deviations

| Member | Kind | What changed |
|---|---|---|
| #1724 | local adaptation | Found while measuring parity: `--target e5-small` answers `/ready` 200 and every `/embed` 500 (`Required inputs (['token_type_ids']) are missing from input feed`). Its graph declares `token_type_ids`, its XLM-R tokenizer never returns it; main.py fed it only "if in encoded". Fixed in the same strand (feed built from the graph's inputs, zeros when the tokenizer produces none — the models' own default), because the group's parity AC and the operator's "prove the embedding endpoint" cannot be met through a 500. Admission, mode and ordering unaffected. Deployed dev target e5-large and CI's default target minilm were NOT affected (measured 200). |
| #1725 | local adaptation | Count bounds alone do not bound memory (N=100 OOMs at 4Gi, N=64 for e5-large). Added per-sequence inference (B=1, measured exact and faster) + one inference lock per process, in both images. |
| #1725 | local adaptation | Embedding caller slices `embed_batch` (≤32/request) so the service cap (64) can never refuse a larger corpus file. |
