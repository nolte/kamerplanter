"""REQ-029 §3.1 — Domain models (DTOs) for AI-based plant identification.

These models are the stable contract shared between adapters, the registry,
the service and the API layer. Signatures intentionally match REQ-029 §3.1 so
that a parallel branch (``feat/plant-identification``) can be merged with
minimal conflicts.
"""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class PlantOrgan(StrEnum):
    """Plant organ for identification (improves accuracy)."""

    LEAF = "leaf"
    FLOWER = "flower"
    FRUIT = "fruit"
    BARK = "bark"
    HABIT = "habit"
    AUTO = "auto"


class IdentificationSuggestion(BaseModel):
    """A single identification suggestion."""

    rank: int
    scientific_name: str
    common_names: list[str] = Field(default_factory=list)
    family: str | None = None
    genus: str | None = None
    confidence: float  # 0.0 – 1.0
    external_id: str
    image_url: str | None = None  # reference image from the service
    gbif_id: int | None = None
    raw_data: dict[str, Any] = Field(default_factory=dict)


class HealthIssue(BaseModel):
    """A detected disease or pest."""

    name: str
    scientific_name: str | None = None
    category: str  # "disease", "pest", "abiotic"
    confidence: float
    severity: str | None = None  # "low", "medium", "high"
    treatment_suggestions: list[str] = Field(default_factory=list)
    external_id: str | None = None
    raw_data: dict[str, Any] = Field(default_factory=dict)


class HealthAssessment(BaseModel):
    """Health assessment of a plant."""

    is_healthy: bool
    healthy_confidence: float
    diseases: list[HealthIssue] = Field(default_factory=list)
    pests: list[HealthIssue] = Field(default_factory=list)
    abiotic: list[HealthIssue] = Field(default_factory=list)


class IdentificationResult(BaseModel):
    """Overall result of an identification."""

    suggestions: list[IdentificationSuggestion] = Field(default_factory=list)
    health_assessment: HealthAssessment | None = None
    is_plant: bool = True  # False when no plant material was detected
    api_response_time_ms: int = 0


# ── Persistence models (REQ-029 §2) ────────────────────────────────────


class IdentificationRequest(BaseModel):
    """Persisted identification request (collection ``identification_requests``).

    Image bytes are never stored — only a hash and the (enriched) results.
    """

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str
    user_key: str
    adapter_key: str
    request_type: str = "identification"
    image_hash: str
    image_organ: str = PlantOrgan.AUTO.value
    status: str = "completed"
    results: list[dict[str, Any]] = Field(default_factory=list)
    selected_result_rank: int | None = None
    health_assessment: dict[str, Any] | None = None
    api_response_time_ms: int = 0
    image_deleted_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class DiagnosisRequest(BaseModel):
    """Persisted diagnosis request (collection ``diagnosis_requests``)."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str
    user_key: str
    adapter_key: str
    plant_instance_key: str | None = None
    image_hash: str
    status: str = "completed"
    health_assessment: dict[str, Any] | None = None
    api_response_time_ms: int = 0
    image_deleted_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class ReferenceImageJob(BaseModel):
    """Coverage report for reference-image acquisition per species (WS-4).

    Created here in WS-1 so the collection exists; populated by the
    acquisition pipeline (WS-4). No image bytes are stored.
    """

    key: str | None = Field(default=None, alias="_key")
    species_key: str
    scientific_name: str | None = None
    status: str = "pending"
    candidates_found: int = 0
    accepted: int = 0
    rejected_license: int = 0
    rejected_quality: int = 0
    license_breakdown: dict[str, int] = Field(default_factory=dict)
    usable_for_recognition: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
