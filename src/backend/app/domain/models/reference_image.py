"""REQ-029-A §4 — Models for license-compliant reference-image acquisition.

These models are DINOv2-specific (acquisition pipeline) and intentionally
separate from the Phase-1 ``identification`` models so the two concerns can
evolve independently.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ReferenceLicense(StrEnum):
    """Normalised license classes relevant for reference-image reuse.

    ``CC0`` and ``CC_BY`` are always accepted for indexing (REQ-029-A §4.1).
    ``CC_BY_NC`` (non-commercial) is accepted *conditionally* — only while the
    application runs non-commercially (see ``ACCEPTED_LICENSES_NONCOMMERCIAL``
    and ``is_acceptable``; pest-image-sources-analysis.md §4.3).

    The remaining classes — ``CC_BY_SA`` (share-alike copyleft), ``CC_BY_ND``
    (no-derivatives), ``CC_BY_NC_SA``, ``CC_BY_NC_ND`` and ``UNKNOWN`` — stay
    rejected unconditionally. Copyleft/no-derivative obligations create
    redistribution risk regardless of commercial use, so the non-commercial
    flag never relaxes them.
    """

    CC0 = "CC0"
    CC_BY = "CC-BY"
    CC_BY_NC = "CC-BY-NC"
    CC_BY_SA = "CC-BY-SA"
    CC_BY_ND = "CC-BY-ND"
    CC_BY_NC_SA = "CC-BY-NC-SA"
    CC_BY_NC_ND = "CC-BY-NC-ND"
    UNKNOWN = "unknown"


#: Licenses whose images may always be embedded and indexed (commercial-safe).
ACCEPTED_LICENSES: frozenset[ReferenceLicense] = frozenset({ReferenceLicense.CC0, ReferenceLicense.CC_BY})

#: Additional licenses acceptable ONLY while the application runs
#: non-commercially. CC-BY-NC is redistributable-with-attribution for
#: non-commercial use; ``is_acceptable(..., allow_noncommercial=True)`` gates it.
#: NEVER add a copyleft (-SA) or no-derivatives (-ND) class here — those stay
#: rejected even non-commercially (pest-image-sources-analysis.md §4.3).
ACCEPTED_LICENSES_NONCOMMERCIAL: frozenset[ReferenceLicense] = ACCEPTED_LICENSES | frozenset(
    {ReferenceLicense.CC_BY_NC}
)


class MediaCandidate(BaseModel):
    """A single candidate reference image returned by a media source."""

    url: str
    license: ReferenceLicense
    source: str = "gbif"
    source_record_id: str | None = None
    attribution: str | None = None
    organ: str | None = None
    format: str | None = None


class AcquisitionResult(BaseModel):
    """Per-species outcome of a reference-image acquisition run (REQ-029-A §5.2)."""

    species_key: str
    scientific_name: str | None = None
    candidates_found: int = 0
    accepted: int = 0
    rejected_license: int = 0
    rejected_quality: int = 0
    rejected_error: int = 0
    license_breakdown: dict[str, int] = Field(default_factory=dict)
    usable_for_recognition: bool = False
    # First accepted image, promoted to the species' representative thumbnail.
    representative_url: str | None = None
    representative_attribution: str | None = None
    representative_license: str | None = None


class ReferenceImageJob(BaseModel):
    """Coverage report for reference-image acquisition per species (REQ-029-A §5.2).

    Stores only the per-species outcome (counts, license breakdown, usability),
    never any image bytes. Keyed deterministically by species (see repository).
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
