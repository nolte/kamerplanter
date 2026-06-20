"""REQ-034 §7 — request/response schemas for the plant-instance photo gallery.

Responses reference a photo *only* by its ``attachment_id`` and stable,
tenant-scoped attachment URIs (``/api/v1/t/{slug}/attachments/{attachment_id}``
and its thumbnail variants). No bucket, storage key or backend is ever exposed
(REQ-034 AC-03/AC-04, NFR-013 AC-04). The frontend builds the gallery purely
from ``attachment_id`` + ``is_cover`` + the thumbnail URIs.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from app.api.v1.attachments.schemas import ThumbnailUris
from app.domain.models.attachment import CAPTION_MAX_LENGTH


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
    created_at: str | None = None


class PlantPhotoListResponse(BaseModel):
    """The plant-instance gallery: ordered photos plus the resolved cover id."""

    plant_instance_key: str
    cover_photo_ref: str | None = Field(
        default=None,
        description="Resolved cover attachment id (explicit cover or first photo).",
    )
    photos: list[PlantPhotoResponse]
