# Group pre-analysis: 2026-09-25-model-image-correctness

> Run-scoped artifact. Committed on the integration branch, removed with a fix-forward
> `git rm` before the bundle merges. It must never reach the default branch, and it must
> never be hidden behind a `.gitignore` entry.

## Scope of this analysis

**Research question:** Does each pinned model image compute what its authors published
(truncation window included), and is that verified in CI for every pinned target, not
only the two shipped ones?

**The group's single logical change, in one sentence:** Every pinned model image
computes with the window its authors published and is built, started and compared
against its golden outputs in CI.

**Out of scope:** the reranker's 512 window (published values agree, see class sweep);
re-indexing any deployed vector store (deployed model is e5-large, window unchanged);
the RAG eval notebook's cosmetic `model` field (the service ignores it).

**Tier:** 2 — one repository, no published API contract changes (`/embed` shape unchanged).

## Members

| Issue | Class | Admitting predicate | Evidence |
|---|---|---|---|
| #1774 | bug | shared touch surface + dependency chain (its golden refresh is what #1764's new legs verify) | `docker/embedding-service/tokenization.py:21` `MAX_LENGTH = 512`; HF `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2@e8f8c211…/sentence_bert_config.json` → `max_seq_length: 128`; e5-small/-base/-large at their pins → `512` |
| #1764 | infra | shared touch surface (`docker-lint-build.yml`, `docker/*/golden/*.json`) + dependency chain | `.github/workflows/docker-lint-build.yml:283-297` build has no `target:` (→ last stage `minilm`); `:331` `target: bge-reranker-v2-m3` |

**Dependency ordering:** #1774 first (changes Dockerfile download stages and all four embedding golden files), then #1764 (matrix legs verify those refreshed goldens).

**Shared touch surface:** `docker/embedding-service/{Dockerfile,golden/*.json}`, `.github/workflows/docker-lint-build.yml`, `.github/lane-inputs/docker-lint-build--build-*-service.yaml`.

## Cause verification (#1774)

- Asserted: MiniLM published for 128. **Refined:** the pinned repository
  (`Xenova/…@2c4055b1…`) ships NO `sentence_bert_config.json` (siblings listed via
  `/api/models/<repo>/revision/<sha>`); its `tokenizer_config.json` says
  `model_max_length: 512`. The 128 lives only in the model authors' repository. So the
  per-model value cannot be read from the current pinned files — it needs a second
  pinned, sha256-verified fetch of the authors' `sentence_bert_config.json`.
- e5-small/-base/-large at their pins: `sentence_bert_config.json` present, `max_seq_length: 512`.

## Mode decision

**Mode:** A — single strand.

**Reason:** neither member is likely to need removal: both are operator-authored
correctness/CI work with no outstanding rejecting review; they share files, which favours
one strand.

## Structural finding

**Cluster shape:** class cluster.

**Root cause or defect class:** a model-specific property hard-coded as a service-wide
constant / checked only for the shipped subset — the service (and the golden reference
and its cross-check) assumed "every model = 512", and CI assumed "the shipped two stand
for all six".

**Process finding:** none new — the golden-guard design (#1763) already binds outputs
to pins; this group extends the binding to the truncation window.

**Preventive change:** the window is read from a pinned file at startup (fail loud), the
golden file records it, the guard binds it to the authors' library's own value
(`reference_check.max_seq_length`), and every pinned target is probed in CI.

**Recurrence fed to the portfolio loop:** n/a.

## Completeness matrix

| Member | Image source (Dockerfile/py) | Golden data | Guards/tests | CI workflow | Lane-inputs manifests | Docs |
|---|---|---|---|---|---|---|
| #1774 | `tokenization.py` reads `max_seq_length`; Dockerfile keeps `sentence_bert_config.json` (+sha256); check: build all 4 targets locally | refresh 4 embedding goldens + reference-check; check: `compute_model_golden_outputs.py` + guard | red-first unit tests in `test_embedding_service_feed.py`; golden guard binds window; check: guards lane | not applicable — no workflow change for #1774 alone | not applicable — reads unchanged (Dockerfile COPY set unchanged) | Dockerfile/README comments updated; check: grep |
| #1764 | not applicable — no image change | not applicable — consumes #1774's goldens | readiness/coverage guards must stay green; check: guards lane | matrix over all targets, scoped gha cache; check: CI run of all 6 legs | re-record via `lane-inputs.yml`; check: `Compare` green | step comments list the legs |

## Risks

- gha cache capacity: ~7 GB of model layers across six targets; per-leg scopes avoid clobbering but may evict. Cost: slower cold legs, not wrong results.
- Runner-minutes rise roughly 3x on model-service PRs only (path-filtered).

## Open questions for the operator

- none (operator pre-approved all gates, 2026-09-24/25).

## Member results

| Member | Specialist | Check | Actual output |
|---|---|---|---|

## Deviations

| Member | Kind | What changed |
|---|---|---|
