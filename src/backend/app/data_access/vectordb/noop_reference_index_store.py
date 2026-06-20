"""No-op reference-index store — default binding until pgvector ships.

REQ-029-A's DINOv2 reference index (``species_embeddings`` in pgvector) is
Phase 2 and is not built yet. Until it exists there are no user-contributed
embeddings to remove, so the GDPR erasure Phase 0.5 (REQ-025 §3.5, AK-OS-05)
must still resolve to a working — but empty — cleanup path.

This store implements :class:`IReferenceIndexStore` as a robust no-op: it logs
the call (so the hook is observable in the erasure audit trail) and returns
``0``. Swapping in the real pgvector store is a single DI-provider change
(:func:`app.common.dependencies.get_reference_index_store`) — the erasure task
and the engine rules stay unchanged.
"""

from __future__ import annotations

import structlog

from app.domain.interfaces.reference_index_store import IReferenceIndexStore

logger = structlog.get_logger()


class NoopReferenceIndexStore(IReferenceIndexStore):
    """Reference-index store that does nothing (pgvector index absent)."""

    async def delete_user_contributions(self, tenant_key: str | None, user_key: str) -> int:
        logger.info(
            "reference_index_cleanup_noop",
            reason="pgvector species_embeddings index not yet built (REQ-029-A Phase 2)",
            scope="user",
            tenant_key=tenant_key,
            user_key=user_key,
            removed=0,
        )
        return 0

    async def delete_tenant_contributions(self, tenant_key: str) -> int:
        logger.info(
            "reference_index_cleanup_noop",
            reason="pgvector species_embeddings index not yet built (REQ-029-A Phase 2)",
            scope="tenant",
            tenant_key=tenant_key,
            removed=0,
        )
        return 0

    def count_pending_contributions(self, tenant_key: str) -> int:
        # No physical index yet → no backlog. The hook's Guard 5 therefore never
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
        # REQ-034 §4 — full no-op until the pgvector reference index ships
        # (REQ-029-A Phase 2). Logged so the hook stays observable; no embedding
        # is computed, no image leaves the instance, nothing is persisted.
        logger.info(
            "reference_contribution_noop",
            reason="pgvector species_embeddings index not yet built (REQ-029-A Phase 2)",
            species_key=species_key,
            tenant_key=tenant_key,
            contributed_by=contributed_by,
        )
        return False
