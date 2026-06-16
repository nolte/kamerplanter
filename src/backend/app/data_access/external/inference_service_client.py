"""HTTP client for the inference-service microservice (REQ-029-A §3).

The inference-service owns the ONNX DINOv2 model and the pgvector reference
index. This client exposes:

- ``match`` / ``is_ready`` — async, used on the identification request path
  (``LocalEmbeddingAdapter``, WS-3).
- ``embed`` / ``embed_batch`` / ``upsert_reference`` — sync, used by the
  Celery reference-image acquisition pipeline (WS-4).

The split mirrors the call sites: identification runs inside async FastAPI
handlers, while acquisition runs inside synchronous Celery tasks.
"""

from typing import Any

import httpx
import structlog

logger = structlog.get_logger(__name__)

_MATCH_TIMEOUT_SECONDS = 30.0
_EMBED_TIMEOUT_SECONDS = 120.0
_READY_TIMEOUT_SECONDS = 5.0


class InferenceServiceClient:
    """Calls the standalone inference-service via HTTP."""

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

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
            timeout=_MATCH_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()

    def is_ready(self) -> bool:
        """Check whether the model is loaded and the index is reachable."""
        try:
            response = httpx.get(f"{self._base_url}/ready", timeout=_READY_TIMEOUT_SECONDS)
            return response.status_code == 200
        except Exception:  # noqa: BLE001 — readiness must never raise
            return False

    def list_references(self, species_key: str, *, limit: int = 50) -> list[dict[str, Any]]:
        """List stored reference image provenance for a species (gallery source).

        Returns ``[]`` (never raises) when the service is unreachable or has no
        index yet, so the UI degrades to "no images" instead of erroring.
        """
        try:
            response = httpx.get(
                f"{self._base_url}/reference/{species_key}",
                params={"limit": limit},
                timeout=_MATCH_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            return response.json().get("images", [])
        except Exception:  # noqa: BLE001 — a missing gallery must not break the page
            logger.info("inference_list_references_failed", species_key=species_key)
            return []

    # ── Acquisition path (sync, WS-4) ──────────────────────────────────

    def embed(self, image_data: bytes) -> list[float]:
        """Compute a single embedding (used during reference indexing)."""
        response = httpx.post(
            f"{self._base_url}/embed",
            files={"image": ("ref.jpg", image_data, "image/jpeg")},
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
        image_data: bytes | None = None,
        embedding: list[float] | None = None,
    ) -> dict[str, Any]:
        """Persist a reference embedding + provenance (no original image stored)."""
        data: dict[str, Any] = {
            "species_key": species_key,
            "scientific_name": scientific_name,
            "source": source,
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
        if embedding is not None:
            import json

            data["embedding"] = json.dumps(embedding)

        files = {"image": ("ref.jpg", image_data, "image/jpeg")} if image_data is not None else None
        response = httpx.post(
            f"{self._base_url}/reference",
            data=data,
            files=files,
            timeout=_EMBED_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()
