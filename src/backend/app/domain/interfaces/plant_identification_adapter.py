"""REQ-029 §3.1 — Adapter interface and result models for plant identification.

This interface is deliberately separate from ``ExternalSourceAdapter`` (REQ-011):
- REQ-011 performs text-based search and sync of *existing* master data.
- REQ-029 performs image-based identification of *unknown* plants.

The interface is the Phase-2 bridge (REQ-029-A §0.1.1 point 5): the engine
programs against this abstraction only. Switching to the self-hosted DINOv2
adapter in Phase 2 means registering another implementation and flipping the
``IDENTIFICATION_PRIMARY_ADAPTER`` setting — no engine/service/API change.
"""

from abc import ABC, abstractmethod
from enum import StrEnum

from pydantic import BaseModel, Field


class PlantOrgan(StrEnum):
    """Plant organ depicted in the image (improves identification accuracy)."""

    LEAF = "leaf"
    FLOWER = "flower"
    FRUIT = "fruit"
    BARK = "bark"
    HABIT = "habit"
    AUTO = "auto"


class IdentificationSuggestion(BaseModel):
    """A single identification candidate returned by an adapter.

    ``external_id`` is adapter-neutral and namespaced (REQ-029-A §0.1.1 point 5):
    ``plantnet:<gbifId>`` in Phase 1, ``local:<species_key>`` in Phase 2.
    """

    rank: int
    scientific_name: str
    common_names: list[str] = Field(default_factory=list)
    family: str | None = None
    genus: str | None = None
    confidence: float  # 0.0 - 1.0
    external_id: str
    image_url: str | None = None  # reference image provided by the service
    gbif_id: int | None = None
    raw_data: dict = Field(default_factory=dict)


class HealthIssue(BaseModel):
    """A detected disease or pest (Phase 2 / Plant.id opt-in only)."""

    name: str
    scientific_name: str | None = None
    category: str  # "disease", "pest", "abiotic"
    confidence: float
    severity: str | None = None  # "low", "medium", "high"
    treatment_suggestions: list[str] = Field(default_factory=list)
    external_id: str | None = None
    raw_data: dict = Field(default_factory=dict)


class HealthAssessment(BaseModel):
    """Health evaluation of a plant (Phase 2 / Plant.id opt-in only)."""

    is_healthy: bool
    healthy_confidence: float
    diseases: list[HealthIssue] = Field(default_factory=list)
    pests: list[HealthIssue] = Field(default_factory=list)
    abiotic: list[HealthIssue] = Field(default_factory=list)


class IdentificationResult(BaseModel):
    """Overall result of an identification call."""

    suggestions: list[IdentificationSuggestion] = Field(default_factory=list)
    health_assessment: HealthAssessment | None = None
    is_plant: bool = True  # False when no plant material was detected
    api_response_time_ms: int = 0


class PlantIdentificationAdapter(ABC):
    """Base adapter for AI-based plant identification.

    Concrete adapters expose three class-level capability attributes
    (``adapter_key``, ``supports_health_assessment``, ``rate_limit_per_day``)
    plus ``identify`` / ``diagnose`` methods. ``is_configured`` reports whether
    the adapter has the credentials it needs to run.
    """

    #: Unique key of the service, e.g. ``"plantnet"``. Class attribute, not a property.
    adapter_key: str = ""
    #: Whether the service supports health/disease assessment.
    supports_health_assessment: bool = False
    #: Maximum requests per day, ``None`` = unbounded.
    rate_limit_per_day: int | None = None

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True when the adapter has all credentials needed to run."""

    @abstractmethod
    def identify(
        self,
        image_data: bytes,
        *,
        organ: PlantOrgan = PlantOrgan.AUTO,
        max_results: int = 5,
        include_health: bool = False,
        language: str = "de",
    ) -> IdentificationResult:
        """Identify a plant from image bytes.

        Args:
            image_data: JPEG/PNG image bytes (already EXIF-stripped/normalized).
            organ: Plant organ depicted (improves accuracy).
            max_results: Maximum number of suggestions to return.
            include_health: Request a health assessment as well (if supported).
            language: Language for common names and treatment texts.

        Returns:
            IdentificationResult with rank-sorted suggestions.
        """

    @abstractmethod
    def diagnose(
        self,
        image_data: bytes,
        *,
        language: str = "de",
    ) -> HealthAssessment:
        """Diagnose diseases/pests from image bytes.

        Raises:
            NotImplementedError: when the adapter does not support health
                assessment (e.g. PlantNet in Phase 1).
        """

    def health_check(self) -> bool:
        """Report whether the adapter is reachable/usable. Default: configured."""
        return self.is_configured()
