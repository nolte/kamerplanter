# Pre-analysis — issue #1763

- **Issue:** #1763 — model images: contract probe checks only vector shape — add golden outputs per pinned model
- **Author:** nolte (repository owner → trusted)
- **Primary class:** `bug` — a CI verification gap let a silently wrong image (pre-#1758 MiniLM, transformers 5 → `<unk>` tokens) pass every check.
- **Secondary class:** `infra` (CI probe + guard). Not routed to `workflow-health-triage`: no red run to triage, the work is a new assertion.
- **Requirements gate:** operator override (repository owner, 2026-09-24/25: full autonomy, every gate pre-approved). The issue carries three checkable acceptance criteria; no `project/requirements/` artefact elicited.
- **Route:** implement directly — one outcome, one PR strand, no roadmap item.

## Verified premises (established)

- `scripts/ci/probe_model_service_contract.py` asserts shape/dimension/norm/distinctness for `/embed` and only the top-ranked index for `/rerank` (read on `origin/develop` e4631b962).
- Governed models = the Hugging Face fetch stages in `docker/embedding-service/Dockerfile` (`dl-e5-small`, `dl-e5-base`, `dl-e5-large`, `dl-minilm`) and `docker/reranker-service/Dockerfile` (`dl-bge-reranker-v2-m3`, `dl-ms-marco-minilm`), each pinned by `revision=` and sha256-verified (#1724/#1739, guard `test_hf_model_fetches_pin_a_revision.py`).
- CI (`docker-lint-build.yml`) builds and probes only `minilm` (embedding, default last stage) and `bge-reranker-v2-m3` (reranker, explicit target) — the same targets `docker-publish.yml` ships.

## Scope

In: golden files per governed model (6), generator script, probe comparison with measured tolerance, pin-binding guard, red-first on the pre-#1758 MiniLM image.
Out: building the four non-shipped targets in CI (follow-up issue).

## Work packages

| id | problem | acceptance | files | specialist |
|----|---------|-----------|-------|------------|
| WP1 | goldens + generator | 6 golden files computed from pinned artefacts, method recorded | `scripts/ci/compute_model_golden_outputs.py`, `docker/*/golden/*.json` | generalist (see note) |
| WP2 | probe compares | probe fails outside tolerance, passes all 6 current images; red on pre-#1758 MiniLM | `scripts/ci/probe_model_service_contract.py`, workflow comments | generalist |
| WP3 | pin guard | pin/sha change without refreshed golden fails | `src/backend/tests/unit/guards/test_model_golden_outputs_match_pins.py` | generalist |

Ordering: WP1 → WP2 → WP3.

Note: no matching specialised agent — generalist remediation. The packages are measurement-bound (local image builds, run-to-run variance, red-first against a rebuilt image); splitting them across a dispatched implementer would duplicate the measurement context.
