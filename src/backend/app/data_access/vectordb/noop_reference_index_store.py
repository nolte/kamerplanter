"""No-op reference-index store — the binding where no recognition index is deployed.

REQ-029-A's DINOv2 reference index lives in the inference-service's pgvector
``species_embeddings`` table. A deployment with ``inference_service_enabled``
unset runs no inference-service, and the only writer of user contributions
(the interactive contribution route) refuses there — so no contributed vector
can exist and the GDPR erasure Phase 0.5 (REQ-025 §3.5, AK-OS-05) and the tenant
deletion correctly remove nothing.

:func:`app.common.dependencies.get_reference_index_store` binds this store only
in that case; with the inference-service enabled it binds
:class:`~app.data_access.vectordb.inference_reference_index_store.InferenceServiceReferenceIndexStore`
(issue #1753 — before it this store was bound unconditionally and an erased
user's contributions survived). The store logs each call and reports
``binding = "noop"``, so the erasure report shows that no index was reached.
"""

from __future__ import annotations

import structlog

from app.domain.interfaces.reference_index_store import IReferenceIndexStore

logger = structlog.get_logger()


class NoopReferenceIndexStore(IReferenceIndexStore):
    """Reference-index store that does nothing (no recognition index deployed)."""

    binding = "noop"

    async def delete_user_contributions(self, tenant_key: str | None, user_key: str) -> int:
        logger.info(
            "reference_index_cleanup_noop",
            reason="inference-service not enabled; no reference index deployed",
            scope="user",
            tenant_key=tenant_key,
            removed=0,
        )
        return 0

    async def delete_tenant_contributions(self, tenant_key: str) -> int:
        logger.info(
            "reference_index_cleanup_noop",
            reason="inference-service not enabled; no reference index deployed",
            scope="tenant",
            tenant_key=tenant_key,
            removed=0,
        )
        return 0

    def count_pending_contributions(self, tenant_key: str) -> int:
        # No index deployed → no backlog. The hook's Guard 5 therefore never
        # rejects on backlog while the store is a no-op.
        return 0

    def add_user_contribution(
        self,
        *,
        species_key: str,
        scientific_name: str,
        image_data: bytes,
        tenant_key: str,
        contributed_by: str,
    ) -> bool:
        # REQ-034 §4 — full no-op: no index is deployed on this instance. Logged
        # so the hook stays observable; no embedding is computed, no image
        # leaves the instance, nothing is persisted.
        logger.info(
            "reference_contribution_noop",
            reason="inference-service not enabled; no reference index deployed",
            species_key=species_key,
            tenant_key=tenant_key,
            contributed_by=contributed_by,
        )
        return False
