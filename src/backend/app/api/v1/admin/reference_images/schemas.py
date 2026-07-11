"""REQ-029-A §4 — Admin API schemas for reference-image acquisition."""

from typing import Literal

from pydantic import BaseModel, Field

# Reasons an admin can give when deselecting a reference image. Free text would
# defeat reporting; the frontend offers these as a select.
ExclusionReason = Literal[
    "blurry",
    "wrong_organ",
    "wrong_species",
    "duplicate",
    "irrelevant",
    "manual",
]


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


class CurationImage(BaseModel):
    """One reference image in the admin curation view (incl. deselected ones).

    ``source_url`` is ``None`` for interactive user contributions (issue #447):
    their original image is never persisted, so the row is surfaced purely for
    curation. Their provenance (``contributed_by`` / ``tenant_key`` /
    ``contributed_at``) lets the admin curate quarantined contributions with
    attribution before activating or rejecting them.
    """

    id: int
    source_url: str | None = None
    license: str | None = None
    attribution: str | None = None
    organ: str | None = None
    source: str | None = None
    is_active: bool = True
    exclusion_reason: str | None = None
    contributed_by: str | None = None
    tenant_key: str | None = None
    contributed_at: str | None = None


class CurationImageList(BaseModel):
    """All reference images for a species, for manual curation."""

    species_key: str
    count: int
    active_count: int
    images: list[CurationImage]


class SetImageActiveRequest(BaseModel):
    """Deselect (``is_active=False``) or re-include a reference image."""

    is_active: bool
    reason: ExclusionReason | None = None


class SetImageActiveResponse(BaseModel):
    """Result of toggling a reference image's active flag."""

    species_key: str
    id: int
    is_active: bool
