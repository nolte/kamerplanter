"""REQ-029-A §3.4 — Self-hosted plant identification via DINOv2 embeddings.

Priority-1 adapter (ahead of the Pl@ntNet fallback). Delegates the heavy
lifting to the inference-service: it embeds the query image with DINOv2 and
matches it against the pgvector reference index, returning the top-k species.

The adapter is deliberately I/O-only. It is instantiated with no arguments by
``IdentificationAdapterRegistry`` on every request (``get_available``), so the
constructor must stay cheap — it only builds an HTTP client (no connection is
opened until a call is made). Species master-data enrichment (common names,
matched species key) is performed by ``IdentificationService`` against the
scientific name, so no ArangoDB access is needed here.
"""

import structlog

from app.config.settings import settings
from app.data_access.external.inference_service_client import InferenceServiceClient
from app.domain.interfaces.plant_identification_adapter import PlantIdentificationAdapter
from app.domain.models.identification import (
    HealthAssessment,
    IdentificationResult,
    IdentificationSuggestion,
    PlantOrgan,
)
from app.domain.services.identification_adapter_registry import IdentificationAdapterRegistry

logger = structlog.get_logger()


@IdentificationAdapterRegistry.register
class LocalEmbeddingAdapter(PlantIdentificationAdapter):
    """Self-hosted species identification via DINOv2 embedding matching."""

    adapter_key = "local_embedding"
    supports_health_assessment = False  # Aufgabe B is separate (REQ-029-A §6)
    rate_limit_per_day = None  # self-hosted → no external limit

    def __init__(self) -> None:
        self._client = InferenceServiceClient(settings.inference_service_url)
        self._enabled = settings.inference_service_enabled
        # Registry availability is key-based: a disabled adapter reports an
        # empty "_api_key" and is therefore treated as unavailable. An enabled
        # adapter has no key attribute → always available (self-hosted).
        if not self._enabled:
            self._api_key = ""

    async def identify(
        self,
        image_data: bytes,
        *,
        organ: PlantOrgan = PlantOrgan.AUTO,
        max_results: int = 5,
        include_health: bool = False,
        language: str = "de",
    ) -> IdentificationResult:
        result = await self._client.match(image_data, k=max_results)

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

    async def diagnose(
        self,
        image_data: bytes,
        *,
        language: str = "de",
    ) -> HealthAssessment:
        raise NotImplementedError(
            "Health assessment is out of scope for the local adapter (REQ-029-A §6 DiseaseClassifier)."
        )

    async def health_check(self) -> bool:
        return self._enabled and await self._client.is_ready()
