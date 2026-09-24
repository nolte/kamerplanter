---
artifact-type: issue-orchestration-analysis
repo: nolte/kamerplanter
issue: "1745"
classification: infra
secondary-classes: []
route: direct
status: approved
created: 2026-09-24
---

# Issue Orchestration — Pre-analysis (#1745)

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #1745 — reach: observation helpers for the two unprobed REQ-025 Art. 17 erasure paths (stored files, reference index)
- **Author**: nolte (repository owner, trusted)
- **Linked items**: #1717, #1743 (merged 57d4202f5), #1719, REQ-025
- **Prior art checked**: `gh pr list --search 1745` → none open; #1743 recorded both entries in `project/reach-probes/_not-constructible.yml`.

## Classification

- **Primary class**: infra (capability-reach tooling; not CI → no workflow-health hand-off)
- **Rationale**: the deliverable is test/observation tooling plus probes; product code is not changed by this issue.
- **Asserted cause verified**: the issue asserts the instruments are missing, not a product cause.
  - established: `ls scripts/reach/` at e44b68d26 has no `observe_storage_residue.py`, `.taskfiles/reach.yaml` has no `reach:vectordb:*`.
  - Erasure path, stored files — established: Phase 0 exists (`privacy_service.py` `_run_storage_cleanup` → `LocalFsStorageAdapter.strip_exif_for_user` / `delete_for_user`, categories from `local_fs_adapter._erasure_scope_categories`). `user_personal` maps to `()` because `AttachmentCategory` has no `profile`/`user_notes` (enums.py L1333-1351): the product stores no such file, so that scope has no referent.
  - Erasure path, reference index — established: Phase 0.5 calls `get_reference_index_store()` which unconditionally returns `NoopReferenceIndexStore` (dependencies.py L1948-1959; returns 0). The product does write `source='user_contributed'` rows with `contributed_by=<user>` into the inference-service's pgvector `species_embeddings` (`ReferenceImageService.contribute_user_reference` → `InferenceServiceClient.upsert_reference`, reference_image_service.py L246-256; migration 004). The inference-service exposes no delete-by-contributor endpoint (main.py: only `DELETE /reference/{species_key}`). Expectation before the run: the index probe will observe the row surviving.

## Requirements gate

Operator override (repository owner, 2026-09-24, full autonomy): the issue's acceptance list is the requirement; no `requirements-elicit` run.

## Scope

- **In scope**: storage seed + `observe_storage_residue.py`; `reach:vectordb:up/down` + reference-embedding seed + observer; two probes derived through `capability-reach-audit` (scanner drafts, pre-approved); T2 run recorded; bug issue for any non-`reached` result.
- **Out of scope**: fixing the erasure path (separate bug issue); changing expectations to match observations.

## Route

- **Decision**: direct — one outcome, one PR strand, no roadmap item.

## Work packages

### P1 — stored-file seed + storage-residue observer
- **Acceptance**: `task reach:seed:stored-files` writes one GPS-EXIF JPEG per attachment category through `AttachmentService.upload` (ingest strip disabled, standing in for `STORAGE_STRIP_EXIF=false`); `observe_storage_residue.py` prints raw per-category members; unit tests red-first.
- **Specialist**: nolte-engineering:fullstack-developer
- **Depends on**: none

### P2 — vectordb target + reference-embedding seed + observer
- **Acceptance**: `task reach:vectordb:up` runs `docker/vectordb` with the inference-service migrations; seed inserts one `user_contributed` row of the subject and one curated control row; observer prints raw members; unit tests red-first.
- **Specialist**: nolte-engineering:fullstack-developer
- **Depends on**: none (shares files with P1 → sequential in one dispatch)

### P3 — derive the two probes
- **Specialist**: skill nolte-engineering:capability-reach-audit (dispatching nolte-engineering:capability-reach-scanner); approval pre-given by the operator.
- **Depends on**: P1, P2

### P4 — T2 run + findings
- **Specialist**: the skill's bundled `reach_audit.py --include-t2`; bug issue(s) for non-`reached` results.
- **Depends on**: P3

## Dependency ordering

P1 → P2 → P3 → P4

## Risks

- Seeding bypasses the ingest strip: documented as a stand-in for the operator setting; the upload otherwise runs the production pipeline.
- Direct SQL seed of the embedding (no DINOv2 model in the stack): mirrors `SpeciesEmbeddingRepository.upsert_reference`'s column set.

## Open questions

none

## Dispatch log
