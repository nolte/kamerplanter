# Issue Orchestration — Pre-analysis

Run-scoped; removed with `git rm` before the bundle merges. Member of group
`2026-09-24-ml-sidecar-hardening` (see `.audits/issue-batch-integration/2026-09-24-ml-sidecar-hardening/analysis.md`).

## Issue metadata

- Issue: #1724 — "embedding-service fetches four Hugging Face models without a commit pin"
- Labels: dependencies, security. Author: repository owner (trusted).

## Classification

- Primary: `security` — supply-chain integrity of shipped model bytes.
- Secondary: `infra` (Dockerfile).
- Operator confirmation: pre-approved 2026-09-24 (parent session).

## Requirements gate

No `project/requirements/` artefact. **Operator override recorded**: the issue carries
three testable acceptance criteria and the operator pre-approved all gates; the
behaviour to preserve is fully specified by "same embeddings as today's image".

## Cause verification (before first change)

- Asserted: four fetches carry no `revision=`. **Established**:
  `pytest tests/unit/guards/test_hf_model_fetches_pin_a_revision.py -q --max-skipped 0`
  on 288432867 → `65 passed`, including the four
  `test_every_allowance_names_an_unpinned_fetch` cases, which assert each entry names an
  UNPINNED fetch.
- Pin targets (HF API `/api/models/<repo>/revision/main`, 2026-09-24):
  e5-small `614241f622f53c4eeff9890bdc4f31cfecc418b3`, e5-base
  `d128750597153bb5987e10b1c3493a34e5a4502a`, e5-large
  `3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3`, Xenova MiniLM
  `2c4055b12046f11709e9df2c122e59ffbdc2f900`.

## Scope

In: the four dl-* stages, runtime `HF_HUB_OFFLINE=1`, guard allow-list, ADR-006 note.
Out: replacing `transformers` (separate parity question).

## Route

Implement directly — one outcome, one strand (the group's integration branch).

## Work packages

### P1 — measure parity reference
Build today's four targets; record sha256 of every kept file and embeddings for a fixed
input set. Specialist: none (measurement, orchestrator).

### P2 — pin + verify in the Dockerfile
Each stage: `revision=<sha>`, explicit per-file `mv`, `sha256sum -c --strict` in the same
RUN. Acceptance: all four targets build; kept files byte-identical to P1; embeddings
within 1e-6 (expected exact). Specialist: `nolte-engineering:fullstack-developer`.

### P3 — guard allow-list
Remove the four entries; keep stale-entry and non-vacuity tests meaningful when the list
is empty. Acceptance: red-first — new guard state against the OLD Dockerfile is red.
Specialist: `nolte-engineering:fullstack-developer`.

### P4 — docs
ADR-006 (DE/EN) pinning note. Specialist: `mkdocs-documentation`.

## Dependency ordering

P1 → P2 → P3; P4 after P2.

## Risks

HF `main` moved since the last image build → covered by P1 building the reference now.

## Dispatch log

(filled during implementation)
