"""REQ-029 — API request/response schemas for plant identification.

These schemas define the adapter-neutral API contract (REQ-029-A §0.1.1 point 5):
``external_id`` is namespaced (``plantnet:<id>`` now, ``local:<species_key>``
later) and the response shape is independent of the active adapter.
"""

from pydantic import BaseModel, Field


class AdapterStatus(BaseModel):
    """Per-adapter configuration/health state."""

    configured: bool
    supports_health: bool
    rate_limit_per_day: int | None = None


class IdentificationStatusResponse(BaseModel):
    """Status payload used by the frontend to toggle the camera UI."""

    available: bool
    primary_adapter: str
    active_adapter: str | None = None
    supports_health: bool = False
    adapters: dict[str, AdapterStatus] = Field(default_factory=dict)


class SuggestionResponse(BaseModel):
    """A single identification candidate in the response."""

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


class IdentifyResponse(BaseModel):
    """Result of an ``/identify`` call."""

    request_key: str | None = None
    is_plant: bool
    suggestions: list[SuggestionResponse] = Field(default_factory=list)
    message: str | None = None


class SelectResultResponse(BaseModel):
    """Result of a ``/select`` call — drives the 'create plant' step."""

    request_key: str
    selected_rank: int
    matched_species_key: str | None = None
    scientific_name: str
    common_names: list[str] = Field(default_factory=list)
    family: str | None = None
    genus: str | None = None
    gbif_id: int | None = None
    confidence: float
    species_in_database: bool


class ReferenceContributionResponse(BaseModel):
    """Result of contributing an identification photo as a species reference.

    Issue #447 — the DINOv2 few-shot reference-image opt-in. Only the embedding
    is indexed; the original image is never persisted (REQ-029-A §4.4).

    SEC-001: the contribution is accepted into a **quarantine** — ``accepted``
    means it was stored for review, ``pending_review`` that it does not yet
    affect the active recognition index and awaits platform-admin activation.
    """

    accepted: bool
    pending_review: bool = True
    species_key: str
    dim: int | None = None


class HistoryEntryResponse(BaseModel):
    """A single entry in the identification history."""

    key: str | None = None
    adapter_key: str
    request_type: str
    image_organ: str
    status: str
    results: list[SuggestionResponse] = Field(default_factory=list)
    selected_result_rank: int | None = None
    # Key of the plant instance created from this result, if any (#630). Lets the
    # history surface a link to the instance's detail page.
    plant_instance_key: str | None = None
    created_at: str | None = None


class LinkInstanceRequest(BaseModel):
    """Body of the ``/{request_key}/instance`` call (#630)."""

    plant_instance_key: str = Field(..., min_length=1)


class LinkInstanceResponse(BaseModel):
    """Result of linking an identification request to a created plant instance (#630)."""

    request_key: str
    plant_instance_key: str
