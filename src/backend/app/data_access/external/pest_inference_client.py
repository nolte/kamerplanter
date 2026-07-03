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

from app.config.settings import settings

logger = structlog.get_logger()

_DETECT_TIMEOUT_SECONDS = 30.0
# Tolerant readiness timeout: a single-CPU inference-service is saturated during
# an active acquisition run, so a 2 s probe times out and the admin card would
# falsely report "service unreachable" while it is actually working.
_READY_TIMEOUT_SECONDS = 6.0


class PestDetectionInferenceClient:
    """Calls the self-hosted pest-inference service over HTTP.

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

    def is_ready(self) -> bool:
        """Whether the pest model is loaded and the index is reachable."""
        try:
            response = httpx.get(
                f"{self._base_url}/pest/ready",
                headers=self._auth_headers(),
                timeout=_READY_TIMEOUT_SECONDS,
            )
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
            headers=self._auth_headers(),
            timeout=_DETECT_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("findings", [])

    def status(self) -> dict[str, Any]:
        """Return the few-shot index availability ({ready, index_count, model})."""
        response = httpx.get(
            f"{self._base_url}/pest/status",
            headers=self._auth_headers(),
            timeout=_READY_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()

    def coverage(self) -> list[dict[str, Any]]:
        """Per-class prototype counts. Returns [] when the service is unreachable."""
        try:
            response = httpx.get(
                f"{self._base_url}/pest/coverage",
                headers=self._auth_headers(),
                timeout=_DETECT_TIMEOUT_SECONDS,
            )
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
                headers=self._auth_headers(),
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
            headers=self._auth_headers(),
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

        Used by the dataset-acquisition pipeline (WP-3 cold start) and the
        REQ-010 promotion hook. Only the embedding + provenance are stored
        service-side; no image is persisted.
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
            headers=self._auth_headers(),
            timeout=_DETECT_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()

    def retract_prototype(self, *, label: str, source: str, source_record_id: str) -> int:
        """Deactivate every prototype matching a provenance (idempotent).

        The inference-service offers no "delete-one-by-provenance" route, so the
        retract is expressed via the curation primitive: list the class's
        prototypes, match those whose ``source`` + ``source_record_id`` identify
        the retracted contribution, and deactivate each via
        :meth:`set_prototype_active` (``is_active=False``) — which is exactly the
        curation gate a demoted user image must fall back behind. Returns the
        number of prototypes deactivated (``0`` when none matched, e.g. the
        upsert never reached the index or was already deactivated).
        """
        listing = self.list_prototypes(label)
        deactivated = 0
        for proto in listing.get("images", []):
            if proto.get("source") != source or proto.get("source_record_id") != source_record_id:
                continue
            if not proto.get("is_active", True):
                continue
            self.set_prototype_active(
                label,
                int(proto["id"]),
                is_active=False,
                reason="contribution_demoted",
            )
            deactivated += 1
        return deactivated
