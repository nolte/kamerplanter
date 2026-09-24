"""REQ-029-A / REQ-034 §5 — reference-index store interface (DINOv2 / pgvector).

The reference index holds per-species DINOv2 embedding vectors used by the
self-hosted plant recognition (REQ-029-A). It lives in the inference-service's
pgvector ``species_embeddings`` table. Some of those vectors are
**user-contributed** (``source == 'user_contributed'``): an interactive
contribution (``POST /t/{slug}/identification/reference``) writes them with the
provenance fields ``contributed_by``, ``tenant_key`` and ``contributed_at``.

This interface lets the GDPR erasure pipeline (REQ-025 Phase 0.5) and the
tenant deletion (REQ-024) remove a user's / tenant's contributed vectors
*before* the ArangoDB deletion, without knowing whether the deployment runs the
inference-service at all. Two bindings exist, chosen by
:func:`app.common.dependencies.get_reference_index_store`:

* ``inference_service`` —
  :class:`~app.data_access.vectordb.inference_reference_index_store.InferenceServiceReferenceIndexStore`,
  whenever ``inference_service_enabled`` is set (issue #1753);
* ``noop`` —
  :class:`~app.data_access.vectordb.noop_reference_index_store.NoopReferenceIndexStore`,
  where no index is deployed and so no contribution can exist.

Every implementation names itself in :attr:`IReferenceIndexStore.binding`; the
erasure report, the erasure record and the log lines carry that name so a run
against the no-op is distinguishable from a real one.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar


class IReferenceIndexStore(ABC):
    """Contract for the DINOv2 reference index (REQ-029-A species_embeddings)."""

    #: Which physical index this store reaches, as reported by the erasure
    #: (``"inference_service"`` / ``"noop"``). Every concrete store overrides it.
    binding: ClassVar[str] = "unbound"

    @abstractmethod
    async def delete_user_contributions(self, tenant_key: str | None, user_key: str) -> int:
        """REQ-025 Phase 0.5 — delete a user's contributed embeddings.

        Removes every vector with ``source == 'user_contributed'`` AND
        ``contributed_by == user_key`` (scoped to ``tenant_key`` when given).
        Curated references stay untouched. Returns the number of vectors
        removed. A store that reaches a real index MUST raise when the delete
        does not go through — the erasure then records ``partially_completed``
        and skips the ArangoDB plan (AK-OS-05).
        """

    @abstractmethod
    async def delete_tenant_contributions(self, tenant_key: str) -> int:
        """REQ-024/-025 — delete every contributed embedding of a whole tenant.

        Removes every vector with ``source == 'user_contributed'`` AND
        ``tenant_key == X``. Returns the number of vectors removed. Raises
        when the delete does not go through, so the tenant record stays and the
        deletion can be retried.
        """

    @abstractmethod
    def count_pending_contributions(self, tenant_key: str) -> int:
        """REQ-034 §4.3 (SR-005a) — count a tenant's open ``pending_review`` contributions.

        Used by the reference-contribution hook (Guard 5) to cap the curation
        backlog per tenant. Returns ``0`` while the hook's write path is inert
        (every binding today). Synchronous to match the Celery task call site.
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
        is a no-op. No binding stores anything today: the gallery hook's write
        path is not activated (only the interactive contribution route writes).
        Implementations must never raise on a routine no-op.
        """
