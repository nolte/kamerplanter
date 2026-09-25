# Pre-analysis: #1764 — CI builds and probes only the shipped model targets

- Group: 2026-09-25-model-image-correctness (Mode A); author `nolte` (trusted).
- Classification: `infra` (CI coverage gap, not a red run → not `workflow-health-triage`).
- Requirements gate: operator override (pre-approved); acceptance from the issue.
- Route: implement directly.

## Cause verification (established)

- `.github/workflows/docker-lint-build.yml` `build-embedding-service`: no `target:` → last stage `minilm`; `build-reranker-service`: `target: bge-reranker-v2-m3`.
- Baseline runner time (last 40 runs, `gh run view --json jobs`): embedding job 1.1–3.1 min (median ≈2.4), reranker 1.5–9.4 min (median ≈5.8).
- Red-first on a non-shipped target (local, 2026-09-25): scratch build of `ms-marco-minilm` with the quantized `onnx/model_quint8_avx2.onnx` of the SAME pinned revision (sha256 updated so the build passes) → `probe_model_service_contract.py` exit 1: `normal-en logits: max |Δ| 0.126 exceeds the golden tolerance 0.01`; the unmodified image → `max |Δ| 4.92e-06`, exit 0.

## Work packages

| id | problem | acceptance | files | specialist | deps |
|---|---|---|---|---|---|
| WP1 | matrix over every pinned target | both model jobs build/smoke/probe each target; per-target gha cache scope; path filters unchanged | `.github/workflows/docker-lint-build.yml` | nolte-shared:cicd-pipeline-design | #1774 |
| WP2 | class guard | a guard derives the pinned targets from the Dockerfiles and fails when a job's matrix misses one | `src/backend/tests/unit/guards/test_every_pinned_model_is_probed_in_ci.py` | nolte-engineering:fullstack-developer (generalist fallback) | WP1 |
| WP3 | lane-inputs re-record | `Compare` green on final head | `.github/lane-inputs/docker-lint-build--build-*-service.yaml` | no matching specialist — generalist (recorder workflow) | WP1 |
