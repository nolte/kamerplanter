# Pre-analysis — issue #1752

- **Issue:** #1752 "embedding-service still ships transformers at runtime — tokenize with tokenizers as the reranker does since #1480"
- **Author:** nolte (repository owner — trusted)
- **Classification:** `security` (secondary: `infra`/dependencies). Rationale: removes a CVE-carrying runtime dependency from a shipped image; no behaviour change intended.
- **Route:** implement directly (one outcome, one PR strand, no roadmap item). Operator pre-approved all gates (2026-09-24/25).
- **Requirements gate:** operator override — the issue carries three testable acceptance criteria; no elicitation needed.

## Measured cause (acquire)

- `transformers` is imported exactly once at runtime: `docker/embedding-service/main.py:27` (`from transformers import AutoTokenizer`), used at `main.py:98` (`AutoTokenizer.from_pretrained(str(ONNX_PATH))`) and `main.py:183` (`_tokenizer([text], padding=True, truncation=True, max_length=512, return_tensors="np")`). **Established** by `grep -n transformers docker/embedding-service/*.py`.
- Nothing else in the image imports it (`feed.py`, `limits.py` only mention it in docstrings). **Established** (same grep).
- `sentencepiece`/`protobuf` are runtime deps only for transformers' slow tokenizer/conversion path; every shipped model carries `tokenizer.json` (Dockerfile allow_patterns + sha256 lines). **Established** by Dockerfile lines 115/148/184/225.
- => Only tokenization. Replacement per #1480 is applicable.

## In scope / out of scope

- In: runtime tokenizer swap, pyproject/uv.lock, Dockerfile comment on huggingface-hub, docstrings, README line, unit test for the loader if feasible, parity + trivy measurements.
- Out: model pins (unchanged; #1739/#1755 guards stay green), reranker, knowledge-service.

## Work packages

| id | problem | acceptance | files | specialist | deps |
|---|---|---|---|---|---|
| WP0 | Baseline: build 4 targets from develop | images `kp1752-old:<target>` exist | — | orchestrator (measurement) | — |
| WP1 | Replace AutoTokenizer with `tokenizers.Tokenizer` (pad token from tokenizer_config, truncation 512, padding, fail loud on missing pad) | tokenization parity 0 differing tensors (4 models × normal/>512/ragged/single × ids/mask/type_ids) | docker/embedding-service/main.py, feed.py | nolte-engineering:fullstack-developer | WP0 |
| WP2 | Drop transformers/sentencepiece/protobuf from runtime deps, relock uv 0.12.18 | `uv lock --check`; `transformers` absent from lock | pyproject.toml, uv.lock, Dockerfile comments, README | nolte-engineering:fullstack-developer | WP1 |
| WP3 | Verify: embedding parity old vs new image, smoke + contract probe ×4, trivy old vs new lock, guards lane | max \|Δ\| reported per model; probes green; guards green | — | orchestrator (measurement) | WP2 |

## Risks

- transformers 5.x AutoTokenizer may not be a thin wrapper of `tokenizer.json` (v5 rebuilt tokenizer classes) — parity must be measured, not assumed (**unestablished** until WP3 measurement).
- `token_type_ids`: AutoTokenizer for XLM-R returns none → feed zeros. `tokenizers` Encoding carries `type_ids`; must not change what the graph is fed.

## Results

(filled during orchestration)

### WP0 (orchestrator, measured 2026-09-25 on develop acb8ea872)

- Old images built: `kp1752-old:{e5-small,e5-base,e5-large,minilm}`; runtime transformers 5.17.0, tokenizers 0.23.2.
- Tokenization parity tokenizers vs AutoTokenizer 5.17.0: e5-small/base/large 39 tensors, 0 differ; **minilm 26 of 39 differ** — transformers 5.17.0 builds a WordPiece backend from the Unigram vocab (`tokenizer_class: BertTokenizer`) and maps nearly every word to `<unk>`. transformers 4.57.6 (BertTokenizerFast) == tokenizers for minilm (all three tensors). => refutes "only parity": the swap FIXES minilm.
- Embedding: old `/embed` vs model-level tokenizers reference: e5 ×3 max|Δ| 0; minilm max|Δ| 0.309, min cos 0.053; old minilm cos(tomato query, oleander text)=0.826 vs reference 0.192.
- trivy 0.74.0 old lock: 0 findings.

### WP1+WP2 (nolte-engineering:fullstack-developer) — hypothesis confirmed

- New `docker/embedding-service/tokenization.py` (`pad_token`, `load_tokenizer`, `MAX_LENGTH`); main.py wired; no `token_type_ids` passed (feed zeros as before).
- pyproject: -transformers -sentencepiece -protobuf (+build-group sentencepiece), +tokenizers>=0.22.0; lock 45 → 35 packages, removals only.
- 13 new unit tests; red-first vs old main.py/COPY line.

### WP3 (orchestrator)

- New images: e5 ×3 `/embed` new vs old max|Δ| 0; minilm new vs model-level reference 0 (vs old 0.309 — the fix).
- smoke + contract probe green ×4; trivy old 0 / new 0; transformers/sentencepiece absent from images.
- Class guard (generalist — small): `TestRuntimeTokenizer` in test_ml_sidecar_limits.py over every governed sidecar: runtime lock closure and module imports free of transformers. Red-first vs old lock+main.py: 2 failed (embedding), reranker passes.
