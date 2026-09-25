"""No-op reference-index store — the binding where this process reaches no recognition index.

REQ-029-A's DINOv2 reference index lives in the inference-service's pgvector
``species_embeddings`` table. :func:`app.common.dependencies.get_reference_index_store`
binds this store in a process whose ``inference_service_enabled`` is unset, and
:class:`~app.data_access.vectordb.inference_reference_index_store.InferenceServiceReferenceIndexStore`
otherwise (issue #1753 — before it this store was bound unconditionally and an
erased user's contributions survived).

"No index in this process" is not "no contributions anywhere": the flag is read
per process, so a celery-worker without it, or any process after the flag was
switched off, lands here while contributions sit in the index (GDPR-001/002).
The store therefore reads the persisted contribution marker
(:class:`~app.domain.interfaces.reference_contribution_marker.IReferenceContributionMarker`):

* marker unset — no contribution was ever accepted; the deletes are a logged
  ``0``;
* marker set — the deletes raise :class:`FeatureNotConfiguredError` naming the
  settings to fix, so the erasure stays open and the tenant deletion refuses
  instead of reporting success; :meth:`configuration_error` says the same to
  the erasure's per-run check;
* marker read fails — the error propagates; a failure is never read as "unset".

``binding = "noop"`` names the store in the erasure report and log lines.
"""

from __future__ import annotations

import structlog

from app.common.exceptions import FeatureNotConfiguredError
from app.domain.interfaces.reference_contribution_marker import IReferenceContributionMarker
from app.domain.interfaces.reference_index_store import IReferenceIndexStore

logger = structlog.get_logger()


class NoopReferenceIndexStore(IReferenceIndexStore):
    """Reference-index store that does nothing (no recognition index deployed)."""

    binding = "noop"

    def __init__(self, marker: IReferenceContributionMarker | None = None) -> None:
        # ``None`` only where no marker exists to read (tests of unrelated
        # paths); the DI provider always wires the persisted one.
        self._marker = marker

    def configuration_error(self) -> str | None:
        if self._marker is None:
            return None
        since = self._marker.reference_contributions_since()
        if since is None:
            return None
        return (
            f"User contributions exist in the recognition reference index (since {since.date().isoformat()}) "
            "but INFERENCE_SERVICE_ENABLED is not set in this process, so they cannot be erased. "
            "Set INFERENCE_SERVICE_ENABLED and INFERENCE_SERVICE_URL on the backend and the celery-worker."
        )

    def _refuse_if_contributions_exist(self) -> None:
        error = self.configuration_error()
        if error is not None:
            raise FeatureNotConfiguredError("reference_index_erasure", error)

    async def delete_user_contributions(self, tenant_key: str | None, user_key: str) -> int:
        self._refuse_if_contributions_exist()
        logger.info(
            "reference_index_cleanup_noop",
            reason="inference-service not enabled; no contribution on record",
            scope="user",
            tenant_key=tenant_key,
            removed=0,
        )
        return 0

    async def delete_tenant_contributions(self, tenant_key: str) -> int:
        self._refuse_if_contributions_exist()
        logger.info(
            "reference_index_cleanup_noop",
            reason="inference-service not enabled; no contribution on record",
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
            reason="inference-service not enabled; no contribution on record",
            species_key=species_key,
            tenant_key=tenant_key,
            contributed_by=contributed_by,
        )
        return False
