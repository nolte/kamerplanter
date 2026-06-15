"""REQ-029 §3.7 — API response schemas for plant identification."""

from typing import Any

from pydantic import BaseModel, Field


class AdapterStatus(BaseModel):
    """Status of a single identification adapter."""

    configured: bool
    healthy: bool = False
    supports_health: bool = False
    rate_limit_per_day: int | None = None


class IdentificationStatusResponse(BaseModel):
    """Status of all identification adapters (feature toggle for the frontend)."""

    available: bool
    supports_health: bool = False
    adapters: dict[str, AdapterStatus] = Field(default_factory=dict)


class SuggestionResponse(BaseModel):
    """A single enriched identification suggestion."""

    rank: int
    scientific_name: str
    common_names: list[str] = Field(default_factory=list)
    family: str | None = None
    genus: str | None = None
    confidence: float
    external_id: str
    image_url: str | None = None
    gbif_id: int | None = None
    matched_species_key: str | None = None
    species_in_database: bool = False
    auto_accept: bool = False


class IdentificationResponse(BaseModel):
    """Result of an identification request."""

    request_key: str | None = None
    is_plant: bool = True
    adapter_key: str | None = None
    suggestions: list[SuggestionResponse] = Field(default_factory=list)
    health_assessment: dict[str, Any] | None = None
    message: str | None = None


class ConfirmResponse(BaseModel):
    """Result of confirming an identification suggestion."""

    request_key: str
    matched_species_key: str | None = None
    scientific_name: str | None = None
    common_names: list[str] = Field(default_factory=list)
    confidence: float | None = None
    species_in_database: bool = False


class HistoryEntry(BaseModel):
    """A single identification-history entry."""

    request_key: str
    created_at: str | None = None
    adapter_key: str | None = None
    request_type: str | None = None
    image_organ: str | None = None
    status: str | None = None
    results: list[dict[str, Any]] = Field(default_factory=list)
    selected_result_rank: int | None = None
