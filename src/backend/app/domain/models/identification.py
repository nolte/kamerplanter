"""REQ-029 §2 — domain models for persisted identification requests.

The user photo is **never** persisted (REQ-029 §5.2, REQ-029-A §10.1). Only the
request metadata, the (matched) suggestions and the selected rank are stored.
``image_hash`` is a truncated SHA-256 used for deduplication/audit, not the image.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

IdentificationStatus = Literal["completed", "failed"]


class IdentificationCandidate(BaseModel):
    """A single suggestion as stored in ``identification_requests.results``.

    Mirrors ``IdentificationSuggestion`` enriched with the local-master-data match.
    """

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


class IdentificationRequest(BaseModel):
    """A persisted identification request (no user image retained)."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str
    user_key: str
    adapter_key: str
    request_type: str = "identification"
    image_hash: str
    image_organ: str = "auto"
    status: IdentificationStatus = "completed"
    results: list[IdentificationCandidate] = Field(default_factory=list)
    selected_result_rank: int | None = None
    api_response_time_ms: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None
    image_deleted_at: datetime | None = None

    model_config = {"populate_by_name": True}
