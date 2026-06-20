"""REQ-029-A §3.4 — Self-hosted plant identification via DINOv2 embeddings.

Phase-2 priority adapter (ahead of the Pl@ntNet fallback). Delegates the heavy
lifting to the inference-service: it embeds the query image with DINOv2 and
matches it against the pgvector reference index, returning the top-k species.

Implements the REQ-029 ``PlantIdentificationAdapter`` interface (synchronous,
same as ``PlantNetAdapter``). Registered with the shared
``IdentificationAdapterRegistry``; the engine programs against the interface
only, so switching Phase 1 → Phase 2 is just registration + flipping
``IDENTIFICATION_PRIMARY_ADAPTER`` (REQ-029-A §0.1.1 point 5).

``external_id`` is namespaced ``local:<species_key>`` per the interface contract.
"""

import structlog

from app.config.settings import settings
from app.data_access.external.inference_service_client import InferenceServiceClient
from app.domain.interfaces.plant_identification_adapter import (
    HealthAssessment,
    IdentificationResult,
    IdentificationSuggestion,
    PlantIdentificationAdapter,
    PlantOrgan,
)
from app.domain.services.identification_registry import IdentificationAdapterRegistry

logger = structlog.get_logger()

ADAPTER_KEY = "local_embedding"


@IdentificationAdapterRegistry.register
class LocalEmbeddingAdapter(PlantIdentificationAdapter):
    """Self-hosted species identification via DINOv2 embedding matching."""

    adapter_key = ADAPTER_KEY
    supports_health_assessment = False  # task B is separate (REQ-029-A §6)
    rate_limit_per_day = None  # self-hosted → no external limit
    is_external = False  # self-hosted DINOv2 — no data egress (REQ-034 §4a.1)

    def __init__(self) -> None:
        self._client = InferenceServiceClient(settings.inference_service_url)

    def is_configured(self) -> bool:
        """Available when the self-hosted inference-service is enabled."""
        return settings.inference_service_enabled

    def identify(
        self,
        image_data: bytes,
        *,
        organ: PlantOrgan = PlantOrgan.AUTO,
        max_results: int = 5,
        include_health: bool = False,
        language: str = "de",
    ) -> IdentificationResult:
        result = self._client.match(image_data, k=max_results)

        suggestions: list[IdentificationSuggestion] = []
        for rank, match in enumerate(result.get("suggestions", []), start=1):
            species_key = match.get("species_key", "")
            suggestions.append(
                IdentificationSuggestion(
                    rank=match.get("rank", rank),
                    scientific_name=match.get("scientific_name", ""),
                    confidence=match.get("confidence", 0.0),
                    external_id=f"local:{species_key}",
                    raw_data=match,
                )
            )

        return IdentificationResult(
            suggestions=suggestions,
            health_assessment=None,
            is_plant=result.get("is_plant", bool(suggestions)),
        )

    def diagnose(
        self,
        image_data: bytes,
        *,
        language: str = "de",
    ) -> HealthAssessment:
        raise NotImplementedError(
            "Health assessment is out of scope for the local adapter (REQ-029-A §6 DiseaseClassifier)."
        )

    def health_check(self) -> bool:
        return settings.inference_service_enabled and self._client.is_ready()
