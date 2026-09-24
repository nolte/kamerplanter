# Pre-analysis — issue #1753

- **Issue:** https://github.com/nolte/kamerplanter/issues/1753 (author `nolte`, repository owner — trusted)
- **Classification:** `security` (primary) — personal-data retention defect (Art. 17 GDPR, REQ-025 AK-OS-05, NFR-011); secondary `bug`.
- **Requirements gate:** operator override — the issue carries four checkable acceptance criteria and REQ-025 AK-OS-05 states the rule; standing operator authorisation 2026-09-24/25.
- **Route:** implement directly (one outcome, one PR strand, no roadmap item).

## Verified claims (established)

| Claim | Evidence |
|---|---|
| Interactive write path exists | `src/backend/app/domain/services/reference_image_service.py:181-271` (`contribute_user_reference` → `upsert_reference(source="user_contributed", contributed_by=user_key, tenant_key=…)`) |
| The write path is gated on `inference_service_enabled` | `src/backend/app/api/v1/recognition/tenant_router.py` `contribute_reference`: raises `AdapterNotAvailableError` when disabled |
| Gallery hook is a second, still-inert writer | `src/backend/app/tasks/reference_contribution_tasks.py:57` Guard 1 (`inference_service_enabled`) and `store.add_user_contribution` → Noop returns `False` |
| Row lands in pgvector with provenance | `src/inference-service/app/vectordb/repository.py:37-104`; migration `004_contribution_provenance.sql` |
| Erasure Phase 0.5 is bound to Noop unconditionally | `src/backend/app/common/dependencies.py:1948-1959` |
| Noop returns 0 and logs | `src/backend/app/data_access/vectordb/noop_reference_index_store.py:27-45` |
| Tenant deletion same gap | `src/backend/app/domain/services/tenant_service.py:333-339` |
| Inference-service has no delete-by-contributor/tenant | `src/inference-service/app/main.py:506` only `DELETE /reference/{species_key}` |
| A raising Phase 0.5 already yields `partially_completed` + backoff | `privacy_service.py` `_finalize_erasure` catches, `_record_failed_attempt`; `on_pre_arango_complete` only after phases succeed |
| Report records `reference_index_removed` but no binding | `src/backend/app/domain/models/privacy.py:491` |

## Diagnosis extensions (measured, beyond the issue)

- **Pest recognition embeddings** (`pest_embeddings`, `source="user_contributed"`) are only *deactivated* on erasure and inference errors are swallowed (`pest_image_recognition_cleanup.py:97-108`, `pest_inference_client.py:169-195`). Same defect class (erasure phase that cannot fail and does not delete) — out of scope here, follow-up issue.
- **Dedup provenance:** `upsert_reference` ON CONFLICT keeps the first contributor's `contributed_by`; a second user uploading byte-identical image gets no own row. Deletion by first contributor removes the shared row (privacy-conservative). Noted, no change.
- knowledge-service holds no user-keyed vectors (`grep user_key|tenant_key|contributed_by src/knowledge-service` → none).
- `identification_requests` is in the ArangoDB plan (`erasure_engine.py:515`).

## Scope

In: inference-service delete endpoints (by contributor, by tenant; `source='user_contributed'` only), backend real store bound when `inference_service_enabled`, binding named in the erasure report + log, fail-loud (raise), stale docstrings, reach wiring after #1754.
Out: gallery-hook write activation (store keeps its hook methods inert), pest-embedding erasure (follow-up), `id_recognition` EXIF scope (issue comment).

## Work packages

| ID | Package | Specialist | Depends |
|---|---|---|---|
| WP1 | inference-service `DELETE /reference/contributions?contributed_by=…[&tenant_key=…]` and `?tenant_key=…`, repo methods, tests | `fullstack-developer` (project) | — |
| WP2 | backend `InferenceServiceReferenceIndexStore` + client methods + DI binding + report binding + docstrings + unit/integration tests red-first | `fullstack-developer` (project) | WP1 |
| WP3 | reach wiring (`scripts/reach/vectordb.py` starts inference-service, backend env) after #1754 lands; probe run | generalist (reach harness) | WP2, #1754 |
| WP4 | security + GDPR review of the diff | `nolte-engineering:code-security-reviewer`, `nolte-engineering:gdpr-data-protection-reviewer` | WP2 |
