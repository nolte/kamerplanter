"""REQ-029 §3.1 — Adapter interface for AI-based plant identification.

Separate from ``ExternalSourceAdapter`` (REQ-011): that interface covers
text-based master-data enrichment, whereas this one covers image-based
identification of unknown plants. Both share the registry/adapter pattern
but expose different contracts.
"""

from abc import ABC, abstractmethod

from app.domain.models.identification import (
    HealthAssessment,
    IdentificationResult,
    PlantOrgan,
)


class PlantIdentificationAdapter(ABC):
    """Base adapter for AI-based plant identification services.

    Concrete adapters expose ``adapter_key``, ``supports_health_assessment``
    and ``rate_limit_per_day`` as class attributes (not properties), so the
    registry can read them without instantiating where avoidable.
    """

    @property
    @abstractmethod
    def adapter_key(self) -> str:
        """Unique key of the service (e.g. ``'plantnet'``)."""

    @property
    @abstractmethod
    def supports_health_assessment(self) -> bool:
        """True if the service supports disease/pest diagnosis."""

    @property
    @abstractmethod
    def rate_limit_per_day(self) -> int | None:
        """Maximum requests per day, ``None`` meaning unlimited."""

    @abstractmethod
    async def identify(
        self,
        image_data: bytes,
        *,
        organ: PlantOrgan = PlantOrgan.AUTO,
        max_results: int = 5,
        include_health: bool = False,
        language: str = "de",
    ) -> IdentificationResult:
        """Identify a plant from an image.

        Args:
            image_data: JPEG/PNG image bytes (EXIF already stripped by caller).
            organ: Plant organ visible in the image (improves accuracy).
            max_results: Maximum number of suggestions.
            include_health: Request a health assessment alongside identification.
            language: Language for common names and treatment hints.

        Returns:
            ``IdentificationResult`` with ranked suggestions.
        """

    @abstractmethod
    async def diagnose(
        self,
        image_data: bytes,
        *,
        language: str = "de",
    ) -> HealthAssessment:
        """Diagnose diseases/pests from an image.

        Args:
            image_data: JPEG/PNG image bytes (EXIF already stripped by caller).
            language: Language for diagnosis texts.

        Returns:
            ``HealthAssessment`` with detected problems.

        Raises:
            NotImplementedError: If the adapter does not support diagnosis.
        """

    async def health_check(self) -> bool:
        """Check whether the service is reachable / configured."""
        return True
