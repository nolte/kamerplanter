"""REQ-029-A §4 — Models for license-compliant reference-image acquisition.

These models are DINOv2-specific (acquisition pipeline) and intentionally
separate from the Phase-1 ``identification`` models so the two concerns can
evolve independently.
"""

from enum import StrEnum

from pydantic import BaseModel, Field


class ReferenceLicense(StrEnum):
    """Normalised license classes relevant for reference-image reuse.

    Only ``CC0`` and ``CC_BY`` are accepted for indexing (REQ-029-A §4.1).
    ``CC_BY_NC`` (non-commercial), ``CC_BY_SA`` (share-alike) and ``UNKNOWN``
    are rejected — the default-safe stance from REQ-029-A §4.4.
    """

    CC0 = "CC0"
    CC_BY = "CC-BY"
    CC_BY_NC = "CC-BY-NC"
    CC_BY_SA = "CC-BY-SA"
    UNKNOWN = "unknown"


#: Licenses whose images may be embedded and indexed.
ACCEPTED_LICENSES: frozenset[ReferenceLicense] = frozenset({ReferenceLicense.CC0, ReferenceLicense.CC_BY})


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
