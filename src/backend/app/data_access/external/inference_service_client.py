"""HTTP client for the inference-service microservice (REQ-029-A §3).

The inference-service owns the ONNX DINOv2 model and the pgvector reference
index. This client exposes:

- ``match`` / ``is_ready`` — async, used on the identification request path
  (``LocalEmbeddingAdapter``, WS-3).
- ``embed`` / ``embed_batch`` / ``upsert_reference`` — sync, used by the
  Celery reference-image acquisition pipeline (WS-4).
- ``delete_user_contributions`` / ``delete_tenant_contributions`` — sync, used
  by the GDPR erasure (REQ-025 Phase 0.5) and the tenant deletion (REQ-024)
  through :class:`InferenceServiceReferenceIndexStore` (issue #1753).

The split mirrors the call sites: identification runs inside async FastAPI
handlers, while acquisition runs inside synchronous Celery tasks.
"""

from typing import Any

import httpx
import structlog

from app.config.settings import settings

logger = structlog.get_logger(__name__)

_MATCH_TIMEOUT_SECONDS = 30.0
_EMBED_TIMEOUT_SECONDS = 120.0
_READY_TIMEOUT_SECONDS = 5.0
_ERASURE_TIMEOUT_SECONDS = 30.0


def _require_key(name: str, value: str | None) -> str:
    """Return *value*, or refuse a missing/blank erasure key before any request.

    A blank key would ask the service for an unscoped erasure (it refuses with
    422 too); refusing here keeps the request from being sent at all. The
    message names the field, never the value.
    """
    if value is None or not value.strip():
        msg = f"{name} must be a non-blank key; refusing an unscoped erasure"
        raise ValueError(msg)
    return value


class InferenceServiceClient:
    """Calls the standalone inference-service via HTTP.

    Every request carries the shared service token as an
    ``Authorization: Bearer <token>`` header (AP-4, INF-S2). The token defaults
    to ``settings.internal_service_token`` so all call sites are authenticated
    without threading it through; it can be overridden per instance (tests).
    """

    def __init__(self, base_url: str, *, service_token: str | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._service_token = service_token if service_token is not None else settings.internal_service_token

    def _auth_headers(self) -> dict[str, str]:
        """Build the service-token auth header (empty when no token is set)."""
        if not self._service_token:
            return {}
        return {"Authorization": f"Bearer {self._service_token}"}

    # ── Identification path ────────────────────────────────────────────
    # Synchronous to match the REQ-029 PlantIdentificationAdapter interface
    # (the engine/service/adapters are all sync).

    def match(self, image_data: bytes, *, k: int = 5) -> dict[str, Any]:
        """Embed an image and return the top-k matching species.

        Response shape (REQ-029-A §3.3):
            ``{"suggestions": [{"rank", "species_key", "scientific_name",
            "score", "confidence"}], "is_plant": bool, "model": str}``
        """
        response = httpx.post(
            f"{self._base_url}/match",
            params={"k": k},
            files={"image": ("query.jpg", image_data, "image/jpeg")},
            headers=self._auth_headers(),
            timeout=_MATCH_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()

    def is_ready(self) -> bool:
        """Check whether the model is loaded and the index is reachable."""
        try:
            response = httpx.get(
                f"{self._base_url}/ready",
                headers=self._auth_headers(),
                timeout=_READY_TIMEOUT_SECONDS,
            )
            return response.status_code == 200
        except Exception:  # noqa: BLE001 — readiness must never raise
            return False

    def modelinfo(self) -> dict[str, Any] | None:
        """Return the model metadata ({model, dim, input_size, license, checksum}).

        Returns ``None`` (never raises) when the service is unreachable, so a
        status view degrades gracefully.
        """
        try:
            response = httpx.get(
                f"{self._base_url}/modelinfo",
                headers=self._auth_headers(),
                timeout=_READY_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            return response.json()
        except Exception:  # noqa: BLE001 — status must never raise
            return None

    def list_references(
        self,
        species_key: str,
        *,
        limit: int = 50,
        active_only: bool = False,
        include_contributions: bool = False,
    ) -> list[dict[str, Any]]:
        """List stored reference image provenance for a species (gallery source).

        With ``active_only`` the deselected images are omitted (public gallery);
        without it every image is returned with its ``is_active`` flag so the
        admin curation view can offer re-inclusion. With ``include_contributions``
        (admin curation only) the quarantined user contributions (issue #447),
        which carry no ``source_url``, are also surfaced with their provenance so
        they can be activated/rejected.

        Returns ``[]`` (never raises) when the service is unreachable or has no
        index yet, so the UI degrades to "no images" instead of erroring.
        """
        try:
            response = httpx.get(
                f"{self._base_url}/reference/{species_key}",
                params={
                    "limit": limit,
                    "active_only": active_only,
                    "include_contributions": include_contributions,
                },
                headers=self._auth_headers(),
                timeout=_MATCH_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            return response.json().get("images", [])
        except Exception:  # noqa: BLE001 — a missing gallery must not break the page
            logger.info("inference_list_references_failed", species_key=species_key)
            return []

    def set_reference_active(
        self,
        species_key: str,
        embedding_id: int,
        *,
        is_active: bool,
        reason: str | None = None,
    ) -> dict[str, Any]:
        """Activate/deactivate one reference image (manual curation, REQ-029-A).

        Unlike ``list_references`` this propagates errors (``raise_for_status``)
        so an admin action that fails surfaces instead of silently no-op'ing. A
        404 from the service (unknown image) bubbles up as an HTTPStatusError.
        """
        response = httpx.patch(
            f"{self._base_url}/reference/{species_key}/{embedding_id}",
            json={"is_active": is_active, "reason": reason},
            headers=self._auth_headers(),
            timeout=_MATCH_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()

    # ── Acquisition path (sync, WS-4) ──────────────────────────────────

    def embed(self, image_data: bytes) -> list[float]:
        """Compute a single embedding (used during reference indexing)."""
        response = httpx.post(
            f"{self._base_url}/embed",
            files={"image": ("ref.jpg", image_data, "image/jpeg")},
            headers=self._auth_headers(),
            timeout=_EMBED_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()["embedding"]

    def embed_batch(self, images: list[bytes]) -> list[list[float]]:
        """Compute embeddings for several reference images at once."""
        files = [("images", (f"ref_{i}.jpg", data, "image/jpeg")) for i, data in enumerate(images)]
        response = httpx.post(
            f"{self._base_url}/embed/batch",
            files=files,
            headers=self._auth_headers(),
            timeout=_EMBED_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()["embeddings"]

    def upsert_reference(
        self,
        *,
        species_key: str,
        scientific_name: str,
        source: str,
        organ: str | None = None,
        source_record_id: str | None = None,
        license: str | None = None,  # noqa: A002 — matches the API field name
        attribution: str | None = None,
        source_url: str | None = None,
        is_active: bool = True,
        contributed_by: str | None = None,
        tenant_key: str | None = None,
        image_data: bytes | None = None,
        embedding: list[float] | None = None,
    ) -> dict[str, Any]:
        """Persist a reference embedding + provenance (no original image stored).

        ``is_active=False`` quarantines the row (SEC-001): it stays out of
        ``/match`` until a platform admin activates it. ``contributed_by`` /
        ``tenant_key`` record an interactive user contribution's provenance so it
        can be attributed and GDPR-erased (SEC-005).
        """
        data: dict[str, Any] = {
            "species_key": species_key,
            "scientific_name": scientific_name,
            "source": source,
            # Booleans must be sent as their lowercase string form for multipart.
            "is_active": str(is_active).lower(),
        }
        if organ:
            data["organ"] = organ
        if source_record_id:
            data["source_record_id"] = source_record_id
        if license:
            data["license"] = license
        if attribution:
            data["attribution"] = attribution
        if source_url:
            data["source_url"] = source_url
        if contributed_by:
            data["contributed_by"] = contributed_by
        if tenant_key:
            data["tenant_key"] = tenant_key
        if embedding is not None:
            import json

            data["embedding"] = json.dumps(embedding)

        files = {"image": ("ref.jpg", image_data, "image/jpeg")} if image_data is not None else None
        response = httpx.post(
            f"{self._base_url}/reference",
            data=data,
            files=files,
            headers=self._auth_headers(),
            timeout=_EMBED_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()

    # ── GDPR erasure (sync, issue #1753) ───────────────────────────────
    # Both calls propagate every failure (``raise_for_status``): an erasure
    # that cannot reach the index must not report success. The keys travel in
    # the JSON body — never in the URL, which httpx logs at INFO here and
    # uvicorn logs on the service side (SEC-001, #1700).

    def delete_user_contributions(self, contributed_by: str, *, tenant_key: str | None = None) -> int:
        """Delete one user's ``user_contributed`` reference embeddings (REQ-025 AK-OS-05).

        ``tenant_key`` narrows the delete to one tenant; ``None`` reaches every
        tenant. Curated references are never touched — the service binds its
        DELETE to ``source = 'user_contributed'``. Returns the rows deleted.

        Raises:
            ValueError: ``contributed_by`` is blank, or ``tenant_key`` is given
                but blank. Nothing is sent.
            httpx.HTTPError: The service is unreachable or answered non-2xx.
        """
        _require_key("contributed_by", contributed_by)
        if tenant_key is not None:
            _require_key("tenant_key", tenant_key)
        response = httpx.post(
            f"{self._base_url}/reference/contributions/erase-by-contributor",
            json={"contributed_by": contributed_by, "tenant_key": tenant_key},
            headers=self._auth_headers(),
            timeout=_ERASURE_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return int(response.json()["deleted"])

    def delete_tenant_contributions(self, tenant_key: str) -> int:
        """Delete every ``user_contributed`` reference embedding of a tenant (REQ-024).

        Returns the rows deleted.

        Raises:
            ValueError: ``tenant_key`` is blank. Nothing is sent.
            httpx.HTTPError: The service is unreachable or answered non-2xx.
        """
        _require_key("tenant_key", tenant_key)
        response = httpx.post(
            f"{self._base_url}/reference/contributions/erase-by-tenant",
            json={"tenant_key": tenant_key},
            headers=self._auth_headers(),
            timeout=_ERASURE_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return int(response.json()["deleted"])
