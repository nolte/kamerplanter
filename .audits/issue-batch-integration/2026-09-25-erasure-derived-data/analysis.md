# Group pre-analysis: 2026-09-25-erasure-derived-data

> Run-scoped artifact. Committed on the integration branch, removed with a fix-forward
> `git rm` before the bundle merges.

## Scope of this analysis

**Research question:** Which personal-data derivatives does an Art. 17 / tenant erasure leave behind while reporting success, beyond the reference index fixed in #1753 (PR #1761)?

**The group's single logical change, in one sentence:** Make the erasure remove every derivative it creates from a user's image — the promoted/demoted pest-recognition prototypes in `pest_embeddings` and the WebP renditions next to each erased original — and fail loud instead of reporting success when it cannot.

**Out of scope:** Sharing semantics of sha256-deduplicated storage objects (pre-existing, unchanged); the demote path keeping a deactivated vector for non-erasure demotion (curation, not erasure); DPO legal question whether a pest vector is personal data once link documents are gone (we treat it as personal data, like #1753).

**Tier:** 3 — crosses a service contract (backend ↔ inference-service HTTP API: new endpoints).

## Members

| Issue | Class | Admitting predicate | Evidence |
|---|---|---|---|
| #1759 | security (bug) | thematic coupling (same defect class as #1753, erasure derivative) + dependency chain on #1761 | `pest_image_recognition_cleanup.py:94-108` swallow; `pest_inference_client.py:169-195` deactivate-only; `:86` PROMOTED-only; `pest_image_tasks.py:116` provenance |
| #1760 | security (bug) | thematic coupling (same class) + shared touch surface (erasure Phase 0, `privacy_service._run_storage_cleanup`) | `local_fs_adapter.py:392-396`, `s3_adapter.py:333-337` delete originals only; `attachment_service.py:366-369` single delete removes renditions |

**Dependency ordering:** independent of each other; #1759 depends on #1761 (store/report pattern). Order: #1760 → #1759.

**Shared touch surface:** `privacy_service.py` (erasure report / pre-ArangoDB phase), erasure tests, privacy docs, reach probe `observe_storage_residue.py`.

## Mode decision

**Mode:** A — single strand. **Reason:** both members are accepted bug fixes with no external dependency beyond #1761, which the branch is stacked on.

## Structural finding

**Cluster shape:** class cluster.

**Root cause or defect class:** an erasure phase enumerates the *primary* object (original file / contribution document) and forgets derivatives created from it by an asynchronous pipeline (thumbnail task, promotion-index task), and/or treats the derivative's removal as best-effort so the erasure still records `completed`.

**Process finding:** the erasure inventory (`erasure_engine.STORAGE_CLEANUP_RULES`, `AccountErasureReport`) lists primaries only; derivative writers (`storage_tasks.generate_thumbnails`, `pest_image_tasks._index_promoted`) have no declared erasure counterpart. Already tracked by #1581/#1753 class sweep — no new process issue.

**Preventive change:** every derivative has a delete in the same adapter method as its primary; the pest step reports a binding and fails loud.

**Recurrence fed to the portfolio loop:** "erasure phase cannot fail / misses derivative" — 3rd occurrence (#1753, #1759, #1760).

## Completeness matrix

| Member | Source | Tests | Docs | Config / Helm | Reach probes | Spec |
|---|---|---|---|---|---|---|
| #1759 | inference-service erase endpoints on `pest_embeddings`; backend pest store (fail-loud, binding) wired into privacy + tenant service; report field; check: unit tests | red-first unit (backend + inference-service); check: `pytest` | privacy / data-retention DE+EN erasure scope; check: `mkdocs build --strict` | not applicable — pest flag parity already on backend+worker? verify; check: guard lane | pest-embedding observation if reach stack hosts it | not applicable — REQ-025 already demands removal of derived data |
| #1760 | `delete_for_user` in both adapters deletes renditions; check: unit tests | red-first adapter tests with generated renditions | privacy doc mentions thumbnails; check: `mkdocs build --strict` | not applicable — no config | storage probe seeds an image with renditions | not applicable |

## Risks

- A deployment with pest detection disabled but earlier-indexed prototypes: a fail-loud store must not block every erasure forever — binding decided like #1753 (marker).
- Stacked on an unmerged PR (#1761): rebase needed when it squashes.

## Open questions for the operator

- none (full autonomy granted 2026-09-24/25).

## Member results

| Member | Specialist | Check | Actual output |
|---|---|---|---|

## Deviations

| Member | Kind | What changed |
|---|---|---|
