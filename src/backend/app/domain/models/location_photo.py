"""The photos of a bed as a caller sees them (REQ-053 GP-FR-051, WP 8.18).

A projection, not a stored document: the bed holds the ids (``Location.photo_refs`` / ``cover_photo_ref``), the
attachment records hold the metadata. ``LocationPhoto`` is also the entity a missing bed photo is reported as
(``NotFoundError("LocationPhoto", …)`` -> ``details[0].entity == "location_photo"``), deliberately not
``attachment``: the client de-stages a task photo on ``attachment`` (#1437), and a bed photo must not trigger that.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.domain.models.attachment import Attachment
from app.domain.models.site import MAX_PHOTOS_PER_LOCATION


class LocationPhoto(BaseModel):
    """One photo of the bed: the record, whether it is the cover, whether the caller may remove it."""

    model_config = ConfigDict(frozen=True)

    attachment: Attachment
    is_cover: bool
    can_remove: bool


class LocationPhotoGallery(BaseModel):
    """The bed's photos, newest first. ``photos`` skips a reference whose attachment is gone (a stale id)."""

    model_config = ConfigDict(frozen=True)

    location_key: str
    cover_photo_ref: str | None
    photos: tuple[LocationPhoto, ...]
    max_photos: int = MAX_PHOTOS_PER_LOCATION
