"""REQ-034 §7 — request/response schemas for the plant-instance photo gallery.

Responses reference a photo *only* by its ``attachment_id`` and stable,
tenant-scoped attachment URIs (``/api/v1/t/{slug}/attachments/{attachment_id}``
and its thumbnail variants). No bucket, storage key or backend is ever exposed
(REQ-034 AC-03/AC-04, NFR-013 AC-04). The frontend builds the gallery purely
from ``attachment_id`` + ``is_cover`` + the thumbnail URIs.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.api.v1.attachments.schemas import ThumbnailUris


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
    created_at: str | None = None


class PlantPhotoListResponse(BaseModel):
    """The plant-instance gallery: ordered photos plus the resolved cover id."""

    plant_instance_key: str
    cover_photo_ref: str | None = Field(
        default=None,
        description="Resolved cover attachment id (explicit cover or first photo).",
    )
    photos: list[PlantPhotoResponse]
