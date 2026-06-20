"""REQ-044 — HTTP client for the self-hosted pest-inference backend.

Talks to the standalone inference-service (REQ-029-A), which hosts both the
few-shot DINOv2 symptom classifier (Modus 2) and the ONNX object detector
(Modus 1, D-FINE/RF-DETR + SAHI). Per-tile inference; the caller merges boxes.

NOTE(REQ-044 WP-3): the ``/pest/detect`` endpoint, the trained weights and the
cold-start few-shot index live in the inference-service repo and are externally
blocked (WP-1 license / WP-2 benchmark / WP-3 GBIF annotation). Until that is
deployed ``is_ready()`` returns False, so the self-hosted adapters report
themselves as unconfigured and the feature degrades gracefully.
"""

from typing import Any

import httpx
import structlog

logger = structlog.get_logger()

_DETECT_TIMEOUT_SECONDS = 30.0
_READY_TIMEOUT_SECONDS = 2.0


class PestDetectionInferenceClient:
    """Calls the self-hosted pest-inference service over HTTP."""

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    def is_ready(self) -> bool:
        """Whether the pest model is loaded and the index is reachable."""
        try:
            response = httpx.get(f"{self._base_url}/pest/ready", timeout=_READY_TIMEOUT_SECONDS)
        except httpx.HTTPError:
            return False
        return response.status_code == 200

    def detect(self, tile: bytes, *, mode: str, language: str = "de") -> list[dict[str, Any]]:
        """Run inference on one tile and return raw finding dicts.

        Each dict carries at least ``label``, ``category``, ``confidence`` and
        (for ``mode='direct'``) a normalized ``bounding_box``.
        """
        response = httpx.post(
            f"{self._base_url}/pest/detect",
            params={"mode": mode, "language": language},
            files={"image": ("tile.jpg", tile, "image/jpeg")},
            timeout=_DETECT_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("findings", [])

    def status(self) -> dict[str, Any]:
        """Return the few-shot index availability ({ready, index_count, model})."""
        response = httpx.get(f"{self._base_url}/pest/status", timeout=_READY_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()

    def coverage(self) -> list[dict[str, Any]]:
        """Per-class prototype counts. Returns [] when the service is unreachable."""
        try:
            response = httpx.get(f"{self._base_url}/pest/coverage", timeout=_DETECT_TIMEOUT_SECONDS)
            response.raise_for_status()
        except httpx.HTTPError:
            return []
        return response.json().get("classes", [])

    def list_prototypes(self, label: str, *, limit: int = 200, active_only: bool = False) -> dict[str, Any]:
        """List stored prototype provenance for a class (gallery source)."""
        try:
            response = httpx.get(
                f"{self._base_url}/pest/reference/{label}",
                params={"limit": limit, "active_only": active_only},
                timeout=_DETECT_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return {"label": label, "count": 0, "active_count": 0, "images": []}
        return response.json()

    def set_prototype_active(
        self, label: str, prototype_id: int, *, is_active: bool, reason: str | None = None
    ) -> dict[str, Any]:
        """Activate/deactivate one prototype (manual curation)."""
        response = httpx.patch(
            f"{self._base_url}/pest/reference/{label}/{prototype_id}",
            json={"is_active": is_active, "reason": reason},
            timeout=_DETECT_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()

    def upsert_prototype(
        self,
        image: bytes,
        *,
        label: str,
        category: str,
        source: str = "gbif",
        source_record_id: str | None = None,
        license: str | None = None,
        attribution: str | None = None,
        source_url: str | None = None,
    ) -> dict[str, Any]:
        """Index one few-shot prototype (the service embeds the image).

        Used by the dataset-acquisition pipeline (WP-3 cold start). Only the
        embedding + provenance are stored service-side; no image is persisted.
        """
        data = {
            "label": label,
            "category": category,
            "source": source,
        }
        for key, value in (
            ("source_record_id", source_record_id),
            ("license", license),
            ("attribution", attribution),
            ("source_url", source_url),
        ):
            if value is not None:
                data[key] = value
        response = httpx.post(
            f"{self._base_url}/pest/reference",
            data=data,
            files={"image": ("ref.jpg", image, "image/jpeg")},
            timeout=_DETECT_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()
