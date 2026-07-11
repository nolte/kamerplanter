"""REQ-038 — HTTP client for the self-hosted disease-classifier endpoint.

Talks to the standalone inference-service (REQ-029-A), which hosts the ONNX
disease classifier and the PlantCV phenotype pipeline behind ``/classify/disease``
and ``/disease/*``. Only the raw payload is returned; the engine applies the
confidence gates and IPM mapping. Every request carries the shared service token
(AP-4, INF-S2) and an explicit timeout (NFR-007).
"""

from typing import Any

import httpx
import structlog

from app.config.settings import settings

logger = structlog.get_logger()

_CLASSIFY_TIMEOUT_SECONDS = 60.0
# Tolerant readiness probe: a single-CPU inference-service is saturated during an
# active inference, so a short probe would falsely report "unreachable".
_STATUS_TIMEOUT_SECONDS = 6.0


class CvDiagnosisInferenceClient:
    """Calls the self-hosted disease-classifier endpoints over HTTP."""

    def __init__(self, base_url: str, *, service_token: str | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._service_token = service_token if service_token is not None else settings.internal_service_token

    def _auth_headers(self) -> dict[str, str]:
        if not self._service_token:
            return {}
        return {"Authorization": f"Bearer {self._service_token}"}

    def is_ready(self) -> bool:
        """Whether the disease classifier is enabled and its model is loaded."""
        try:
            response = httpx.get(
                f"{self._base_url}/disease/ready",
                headers=self._auth_headers(),
                timeout=_STATUS_TIMEOUT_SECONDS,
            )
        except httpx.HTTPError:
            return False
        return response.status_code == 200

    def status(self) -> dict[str, Any]:
        """Return the classifier availability snapshot ({ready, enabled, ...}).

        Returns a fail-safe "unavailable" dict when the service is unreachable so
        the caller never crashes on a status card render.
        """
        try:
            response = httpx.get(
                f"{self._base_url}/disease/status",
                headers=self._auth_headers(),
                timeout=_STATUS_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return {"ready": False, "enabled": False, "class_count": 0, "phenotype_available": False}
        return response.json()

    def classify(self, image: bytes, *, k: int = 5, with_phenotype: bool = False) -> dict[str, Any]:
        """Run the disease classifier on one image and return the raw payload.

        The payload carries ``classifications``, ``model_meta``, an optional
        ``phenotype`` block and an always-present ``disclaimer``.
        """
        response = httpx.post(
            f"{self._base_url}/classify/disease",
            params={"k": k, "phenotype": with_phenotype},
            files={"image": ("photo.jpg", image, "image/jpeg")},
            headers=self._auth_headers(),
            timeout=_CLASSIFY_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()
