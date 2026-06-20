"""REQ-034 §7 — request/response schemas for the plant-instance photo gallery.

Responses reference a photo *only* by its ``attachment_id`` and stable,
tenant-scoped attachment URIs (``/api/v1/t/{slug}/attachments/{attachment_id}``
and its thumbnail variants). No bucket, storage key or backend is ever exposed
(REQ-034 AC-03/AC-04, NFR-013 AC-04). The frontend builds the gallery purely
from ``attachment_id`` + ``is_cover`` + the thumbnail URIs.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from app.api.v1.attachments.schemas import ThumbnailUris
from app.domain.models.attachment import CAPTION_MAX_LENGTH, QualityRating


class PlantPhotoMetadataUpdate(BaseModel):
    """REQ-034 §2.1 v1.2 — PATCH body for a gallery photo's editable metadata.

    True PATCH semantics: a field that is **omitted** from the request leaves the
    stored value untouched, while an explicit ``null`` clears it. The router uses
    ``model_fields_set`` to tell the two apart, so both ``caption`` and
    ``taken_on`` default to ``None`` here only to make them optional in the body.
    ``caption`` length is bounded at the schema layer; ``taken_on`` "not in the
    future" is enforced in the service (it needs the current date).
    """

    caption: str | None = Field(
        default=None,
        max_length=CAPTION_MAX_LENGTH,
        description="Free-text caption (max 500 chars). Pass null to clear it.",
    )
    taken_on: date | None = Field(
        default=None,
        description="Capture date (ISO 8601, not in the future). Pass null to fall back to the upload date.",
    )


class QualitySuggestionResponse(BaseModel):
    """One recognition suggestion shown with a quality verdict (REQ-034 §4a.2)."""

    scientific_name: str
    confidence: float = Field(description="Model confidence, 0.0-1.0.")
    external_id: str | None = None


class QualityAssessmentResponse(BaseModel):
    """REQ-034 §4a.2 — a photo's persisted image-quality verdict (Ampel)."""

    adapter: str = Field(description="Adapter that produced the verdict (e.g. 'plantnet').")
    assessed_at: str
    is_plant: bool
    rating: QualityRating = Field(description="Traffic light: good | fair | poor.")
    expected_species_matched: bool | None = Field(
        default=None,
        description="Whether the plant's known species was among the top suggestions; null when no species is set.",
    )
    suggestions: list[QualitySuggestionResponse] = Field(default_factory=list)


class PlantPhotoResponse(BaseModel):
    """A single gallery photo of a plant instance (REQ-034 §7)."""

    attachment_id: str
    uri: str = Field(description="Stable download URI for the original object.")
    thumbnail_uris: ThumbnailUris | None = Field(
        default=None,
        description="Thumbnail renditions (may still be generating right after upload).",
    )
    is_cover: bool = Field(description="Whether this photo is the instance cover photo.")
    mime_type: str
    byte_size: int
    # REQ-034 §2.1 v1.2 — user-editable metadata. ``taken_on`` may be null; the
    # display fallback (``taken_on ?? created_at``) is applied in the frontend so
    # the stored capture date stays honest (never silently overwritten).
    caption: str | None = None
    taken_on: str | None = None
    # REQ-034 §4a.2 — last image-quality verdict, or null until one is requested.
    quality_assessment: QualityAssessmentResponse | None = None
    created_at: str | None = None


class PlantPhotoAssessRequest(BaseModel):
    """REQ-034 §4a.1 — body for triggering a photo-quality assessment."""

    adapter: Literal["plantnet", "local_embedding"] = Field(
        description="Recognition path: 'plantnet' (external, consent) or 'local_embedding' (self-hosted DINOv2).",
    )


class AssessmentAdapterResponse(BaseModel):
    """REQ-034 §4a.1 — one selectable recognition adapter for the picker."""

    key: str
    available: bool = Field(description="Whether the adapter is usable here right now.")
    external: bool = Field(description="Whether choosing it sends the photo to a third party.")
    requires_consent: bool = Field(description="Whether triggering it needs the third-party-transfer consent.")


class AssessmentAdaptersResponse(BaseModel):
    """REQ-034 §4a.1 — the adapter choices for the quality-assessment UI."""

    adapters: list[AssessmentAdapterResponse]


class PlantPhotoListResponse(BaseModel):
    """The plant-instance gallery: ordered photos plus the resolved cover id."""

    plant_instance_key: str
    cover_photo_ref: str | None = Field(
        default=None,
        description="Resolved cover attachment id (explicit cover or first photo).",
    )
    photos: list[PlantPhotoResponse]
