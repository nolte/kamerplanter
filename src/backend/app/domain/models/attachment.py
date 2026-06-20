"""NFR-013 §2.2 — domain model for a stored attachment.

An ``Attachment`` is the catalog record that maps a logical upload (a diary
photo, an IPM image, an export archive, ...) to a physical object in the
configured storage backend (``storage_key``). The bytes live in object storage;
this document carries only the metadata needed for listing, deduplication
(``sha256``), DSGVO erasure lookups (``tenant_key`` + ``created_by``) and
serving (``mime_type`` / ``byte_size``).
"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.common.enums import AttachmentCategory

# REQ-034 §2.1 — upper bound for the user-editable gallery photo caption.
CAPTION_MAX_LENGTH = 500

# REQ-034 §4a.2 — the derived photo-quality traffic light.
QualityRating = Literal["good", "fair", "poor"]


class QualitySuggestion(BaseModel):
    """One recognition suggestion captured in a quality assessment (REQ-034 §4a.2).

    A trimmed-down copy of an ``IdentificationSuggestion`` — only the fields the
    user needs to understand *why* a photo got its rating are kept (the species
    name, the model's confidence and the namespaced adapter id). The full
    identification history is deliberately **not** persisted here (the gallery
    assessment is anzeigend, not an identification record — §4a vs §4).
    """

    scientific_name: str
    confidence: float  # 0.0 - 1.0
    external_id: str | None = None


class QualityAssessment(BaseModel):
    """REQ-034 §4a.2 — the on-demand image-quality verdict stored on a photo.

    Derived from an ``IdentificationResult`` plus the plant's expected species
    and persisted on the attachment so it stays visible in the gallery/lightbox
    afterwards (and can be re-triggered, overwriting the previous verdict).
    ``expected_species_matched`` is ``None`` when the plant has no
    ``species_key`` (no soll/ist comparison was possible — the rating then rests
    on ``is_plant`` + top-1 confidence only, §4a.2).
    """

    adapter: str
    assessed_at: datetime
    is_plant: bool
    rating: QualityRating
    expected_species_matched: bool | None = None
    suggestions: list[QualitySuggestion] = Field(default_factory=list)


class Attachment(BaseModel):
    """A catalog record for one object in the storage backend."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str
    mime_type: str
    byte_size: int
    sha256: str
    original_filename: str
    created_by: str
    category: AttachmentCategory
    storage_key: str
    # REQ-034 §2.1 v1.2 — generic, user-editable photo metadata. Populated for
    # gallery photos (``category == plant``); every other category leaves them
    # ``None``. ``caption`` is a free-text note (<= 500 chars); ``taken_on`` is
    # the capture date the user may override (default/fallback: the upload
    # ``created_at``; the display fallback lives in the frontend). EXIF capture
    # time is unavailable here because EXIF is stripped on upload (NFR-013 §6.4).
    caption: str | None = None
    taken_on: date | None = None
    # REQ-034 §4a.2 — last image-quality assessment (Ampel + top suggestions).
    # Populated on demand for gallery photos; ``None`` until the user triggers
    # an assessment. Re-running overwrites it.
    quality_assessment: QualityAssessment | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
