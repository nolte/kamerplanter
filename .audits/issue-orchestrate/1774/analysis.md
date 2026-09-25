# Pre-analysis: #1774 — embedding-service truncates MiniLM at 512 although published for 128

- Group: 2026-09-25-model-image-correctness (Mode A); author `nolte` (repository owner, trusted).
- Classification: `bug` — the service computes an embedding outside the model's published window.
- Requirements gate: operator override (repository owner, 2026-09-24/25: every gate pre-approved); acceptance is the issue's own checklist.
- Route: implement directly (one outcome, one PR strand, no roadmap item).

## Cause verification (established)

- `docker/embedding-service/tokenization.py:21` `MAX_LENGTH = 512`, applied to every model (`load_tokenizer`).
- HF API, siblings of `Xenova/paraphrase-multilingual-MiniLM-L12-v2@2c4055b1…`: no `sentence_bert_config.json`; `tokenizer_config.json` `model_max_length: 512`.
- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2@e8f8c211226b894fcb81acc59f3b34ba3efd5f42` `sentence_bert_config.json`: `max_seq_length: 128`.
- e5-small `614241f6…`, e5-base `d1287505…`, e5-large `3d7cfbda…`: `sentence_bert_config.json` `max_seq_length: 512`.
- MiniLM in RAG eval: unestablished → measured: eval runs through knowledge-service against the deployed embedding image (`skaffold.yaml:167` `target: e5-large`, `helm/kamerplanter/values-dev-ki.yaml:72`); the notebook's `"model": "all-MiniLM-L6-v2"` field is echoed, never used (`main.py` `EmbedResponse(model=req.model)`). MiniLM is not used by the RAG eval.

## Work packages

| id | problem | acceptance | files | specialist | deps |
|---|---|---|---|---|---|
| WP1 | window per model from pinned files | `load_tokenizer` truncates at `sentence_bert_config.json` `max_seq_length`, fails loud when absent/invalid; red-first unit tests via the production loader | `docker/embedding-service/{tokenization.py,main.py,Dockerfile,README.md}`, `src/backend/tests/unit/test_embedding_service_feed.py` | nolte-engineering:fullstack-developer | — |
| WP2 | golden reference + guard bind the window | reference reads the image's `sentence_bert_config.json`; `reference-check` uses sentence-transformers' own `max_seq_length`; guard requires `max_seq_length` == `reference_check.max_seq_length` and a long case past the window; multi-fetch download stage supported | `scripts/ci/compute_model_golden_outputs.py`, `src/backend/tests/unit/guards/test_model_golden_outputs_match_pins.py` | nolte-engineering:fullstack-developer | WP1 |
| WP3 | refresh golden outputs | 4 embedding goldens regenerated from rebuilt images + reference-check; probe green on all 4 locally | `docker/embedding-service/golden/*.json` | no matching specialist — generalist (needs local docker + torch env) | WP1, WP2 |
