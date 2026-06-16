"""REQ-029-A §4 — Admin API schemas for reference-image acquisition."""

from pydantic import BaseModel, Field


class AcquireResponse(BaseModel):
    """Result of dispatching an acquisition job."""

    status: str  # "queued"
    scope: str  # "all" | "species"
    species_key: str | None = None
    task_id: str | None = None


class CoverageEntry(BaseModel):
    """Per-species coverage summary from ``reference_image_jobs``."""

    species_key: str
    scientific_name: str | None = None
    accepted: int = 0
    candidates_found: int = 0
    usable_for_recognition: bool = False
    license_breakdown: dict[str, int] = Field(default_factory=dict)


class CoverageReport(BaseModel):
    """Aggregated reference-image coverage across all acquired species."""

    total_species: int
    usable_species: int
    entries: list[CoverageEntry]
