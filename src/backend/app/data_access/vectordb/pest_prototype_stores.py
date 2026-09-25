"""The two bindings of :class:`IPestPrototypeStore` (issue #1759).

``InferenceServicePestPrototypeStore`` deletes through the inference-service's
``POST /pest/reference/contributions/...`` routes and fails loud: every
transport or HTTP error becomes :class:`ExternalSourceError` whose text carries
the error class or status, never a key (the text is persisted on the retained
erasure record and logged, #1700). The erasure then records
``partially_completed`` with a backoff and skips the ArangoDB plan; the tenant
deletion keeps the tenant so it can be retried.

``NoopPestPrototypeStore`` is bound where the process reaches no
inference-service. It reads the persisted marker and refuses while a prototype
may have been indexed — the same shape as the #1753 reference-index no-op.
"""

from __future__ import annotations

import asyncio

import httpx
import structlog

from app.common.exceptions import ExternalSourceError, FeatureNotConfiguredError
from app.data_access.external.pest_inference_client import PestDetectionInferenceClient
from app.domain.interfaces.pest_prototype_store import IPestPrototypeContributionMarker, IPestPrototypeStore

logger = structlog.get_logger()

_SOURCE = "inference_service"

#: Keys per erase request; the inference-service refuses more than 1000.
ERASE_BATCH_SIZE = 500


def _erasure_failure(exc: httpx.HTTPError, scope: str) -> ExternalSourceError:
    cause = f"HTTP {exc.response.status_code}" if isinstance(exc, httpx.HTTPStatusError) else type(exc).__name__
    return ExternalSourceError(_SOURCE, f"pest-prototype {scope} erasure did not go through ({cause})")


class InferenceServicePestPrototypeStore(IPestPrototypeStore):
    """Deletes contributed pest prototypes through the inference-service."""

    binding = "inference_service"

    def __init__(self, client: PestDetectionInferenceClient) -> None:
        self._client = client

    async def delete_contributions(self, contribution_keys: list[str]) -> int:
        keys = list(contribution_keys)
        removed = 0
        try:
            # Bounded requests: the service refuses more than ERASE_BATCH_SIZE keys.
            for start in range(0, len(keys), ERASE_BATCH_SIZE):
                batch = keys[start : start + ERASE_BATCH_SIZE]
                removed += await asyncio.to_thread(self._client.erase_contributions, batch)
        except httpx.HTTPError as exc:
            raise _erasure_failure(exc, "contribution") from exc
        return removed

    async def delete_tenant_contributions(self, tenant_key: str) -> int:
        try:
            return await asyncio.to_thread(self._client.erase_tenant_contributions, tenant_key)
        except httpx.HTTPError as exc:
            raise _erasure_failure(exc, "tenant") from exc


class NoopPestPrototypeStore(IPestPrototypeStore):
    """Pest-prototype store for a process that reaches no inference-service."""

    binding = "noop"

    def __init__(self, marker: IPestPrototypeContributionMarker | None = None) -> None:
        # ``None`` only in tests of unrelated paths; the DI provider wires the marker.
        self._marker = marker

    def configuration_error(self) -> str | None:
        if self._marker is None:
            return None
        since = self._marker.pest_prototype_contributions_since()
        if since is None:
            return None
        return (
            f"Contributed pest-image prototypes may exist in the recognition index (since "
            f"{since.date().isoformat()}) but neither PEST_DETECTION_ENABLED nor INFERENCE_SERVICE_ENABLED "
            "is set in this process, so they cannot be erased. Set it, with INFERENCE_SERVICE_URL, on the "
            "backend and the celery-worker."
        )

    def _refuse_if_indexed(self) -> None:
        error = self.configuration_error()
        if error is not None:
            raise FeatureNotConfiguredError("pest_prototype_erasure", error)

    async def delete_contributions(self, contribution_keys: list[str]) -> int:
        if not contribution_keys:
            return 0
        self._refuse_if_indexed()
        logger.info("pest_prototype_cleanup_noop", scope="contributions", removed=0)
        return 0

    async def delete_tenant_contributions(self, tenant_key: str) -> int:
        self._refuse_if_indexed()
        logger.info("pest_prototype_cleanup_noop", scope="tenant", tenant_key=tenant_key, removed=0)
        return 0
