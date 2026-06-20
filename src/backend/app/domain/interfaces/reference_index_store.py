"""REQ-029-A / REQ-034 §5 — reference-index store interface (DINOv2 / pgvector).

The reference index holds per-species DINOv2 embedding vectors used by the
self-hosted plant recognition (REQ-029-A). Some of those vectors are
**user-contributed** (``source == 'user_contributed'``): they are derived from a
user's gallery photos and carry provenance fields (``contributed_by``,
``tenant_key``, ``contributed_at``).

This interface exists so the GDPR erasure pipeline (REQ-025 Phase 0.5) can
remove a user's / tenant's contributed vectors *before* the ArangoDB deletion,
without the erasure task knowing whether the physical pgvector index has been
built yet (DINOv2 is Phase 2 of REQ-029-A and may not exist).

The default binding is the no-op store below: it satisfies the contract,
emits a structured log so the hook is observable, and returns ``0``. Once the
real pgvector ``species_embeddings`` store ships, register a concrete
implementation in the DI provider — no erasure-task change required.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class IReferenceIndexStore(ABC):
    """Contract for the DINOv2 reference index (REQ-029-A species_embeddings)."""

    @abstractmethod
    async def delete_user_contributions(self, tenant_key: str | None, user_key: str) -> int:
        """REQ-025 Phase 0.5 — delete a user's contributed embeddings.

        Removes every vector with ``source == 'user_contributed'`` AND
        ``contributed_by == user_key`` (scoped to ``tenant_key`` when given).
        Curated references stay untouched. Returns the number of vectors
        removed.
        """

    @abstractmethod
    async def delete_tenant_contributions(self, tenant_key: str) -> int:
        """REQ-024/-025 — delete every contributed embedding of a whole tenant.

        Removes every vector with ``source == 'user_contributed'`` AND
        ``tenant_key == X``. Returns the number of vectors removed.
        """

    @abstractmethod
    def count_pending_contributions(self, tenant_key: str) -> int:
        """REQ-034 §4.3 (SR-005a) — count a tenant's open ``pending_review`` contributions.

        Used by the reference-contribution hook (Guard 5) to cap the curation
        backlog per tenant. Returns ``0`` while the physical index is absent.
        Synchronous to match the Celery task call site.
        """

    @abstractmethod
    def add_user_contribution(
        self,
        *,
        species_key: str,
        scientific_name: str,
        image_data: bytes,
        tenant_key: str,
        contributed_by: str,
    ) -> bool:
        """REQ-034 §4.1 — add a user-contributed reference embedding (curation-gated).

        The embedding is computed by the self-hosted inference service from
        ``image_data`` and persisted with ``source == 'user_contributed'``,
        ``is_active == False`` and the provenance fields (SR-003). The original
        image is **never** persisted — only the vector + provenance.

        Returns ``True`` when a contribution was stored, ``False`` when the path
        is a no-op (physical index absent — Phase 1). Implementations must never
        raise on a routine no-op.
        """
