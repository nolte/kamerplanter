"""Reference-index store backed by the inference-service (issue #1753).

The DINOv2 reference index (REQ-029-A) is the inference-service's pgvector
``species_embeddings`` table. The interactive contribution route writes
``source = 'user_contributed'`` rows there with ``contributed_by`` and
``tenant_key`` (``ReferenceImageService.contribute_user_reference``). This store
removes them again — for the Art. 17 erasure (REQ-025 Phase 0.5, AK-OS-05) by
contributor, for the tenant deletion (REQ-024) by tenant — through the
service's ``DELETE /reference/contributions/...`` endpoints, which bind every
delete to ``source = 'user_contributed'``.

**Fail-loud.** Every failure raises :class:`ExternalSourceError`. The erasure
then records ``partially_completed`` with a backoff and skips the ArangoDB plan
(``PrivacyService._finalize_erasure``); the tenant deletion keeps the tenant
record so the delete can be retried. The error text carries the transport
class or the HTTP status, never the URL: the URL holds the user / tenant key,
and the text is persisted on the retained erasure record and logged (#1700).

**Scope.** Only the two deletes are live. The REQ-034 §4 gallery hook's write
path (:meth:`add_user_contribution`, :meth:`count_pending_contributions`) is
*not* activated by this store — it stays the inert no-op it was, so binding
this store for the erasure does not start a second writer.
"""

from __future__ import annotations

import asyncio

import httpx
import structlog

from app.common.exceptions import ExternalSourceError
from app.data_access.external.inference_service_client import InferenceServiceClient
from app.domain.interfaces.reference_index_store import IReferenceIndexStore

logger = structlog.get_logger()

_SOURCE = "inference_service"


def _erasure_failure(exc: httpx.HTTPError, scope: str) -> ExternalSourceError:
    """Describe a failed delete without the URL (it carries the key)."""
    cause = f"HTTP {exc.response.status_code}" if isinstance(exc, httpx.HTTPStatusError) else type(exc).__name__
    return ExternalSourceError(_SOURCE, f"reference-index {scope} erasure did not go through ({cause})")


class InferenceServiceReferenceIndexStore(IReferenceIndexStore):
    """Deletes contributed reference vectors through the inference-service."""

    binding = "inference_service"

    def __init__(self, client: InferenceServiceClient) -> None:
        self._client = client

    async def delete_user_contributions(self, tenant_key: str | None, user_key: str) -> int:
        try:
            # The client is synchronous (httpx); keep the event loop free.
            return await asyncio.to_thread(self._client.delete_user_contributions, user_key, tenant_key=tenant_key)
        except httpx.HTTPError as exc:
            raise _erasure_failure(exc, "user") from exc

    async def delete_tenant_contributions(self, tenant_key: str) -> int:
        try:
            return await asyncio.to_thread(self._client.delete_tenant_contributions, tenant_key)
        except httpx.HTTPError as exc:
            raise _erasure_failure(exc, "tenant") from exc

    def count_pending_contributions(self, tenant_key: str) -> int:
        # The gallery hook's write path is inert (see module docstring), so it
        # has no backlog to cap.
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
        # REQ-034 §4 — the gallery hook stays a no-op; activating it is its own
        # decision (curation backlog, consent, rate limits), not part of #1753.
        logger.info(
            "reference_contribution_noop",
            reason="gallery-hook contribution path not activated",
            species_key=species_key,
            tenant_key=tenant_key,
        )
        return False
