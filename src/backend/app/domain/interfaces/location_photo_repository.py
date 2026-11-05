"""The photos of a bed (REQ-053 GP-FR-051, WP 8.18): the writes of ``Location.photo_refs`` / ``cover_photo_ref``.

Each write is **one transaction** that re-reads the location under its site's tenant (a ``Location`` carries no
``tenant_key``, #2107 - the site is the anchor) and decides on that snapshot, so a check in the service cannot be
outdated by the time the write lands. Adding a photo also **touches the attachment record** in the same
transaction: a concurrent ``remove_if_unreferenced`` of that record writes it too, so whichever commits second
conflicts instead of a bed naming a photo another request just deleted (the underlay's rule, #2545).

The outcome is a status, not an exception: which refusal a status becomes (404, 422 …) is the service's decision.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

#: What one photo write did. ``written`` and ``unchanged`` carry the bed's photos after the write.
type LocationPhotoWriteStatus = Literal[
    "written",
    "unchanged",
    "location_not_found",
    "attachment_not_found",
    "limit_reached",
    "not_a_photo",
]


@dataclass(frozen=True)
class LocationPhotoState:
    """The bed's photos as stored: newest first, the cover one of them (or ``None``)."""

    photo_refs: tuple[str, ...] = ()
    cover_photo_ref: str | None = None


@dataclass(frozen=True)
class LocationPhotoWrite:
    status: LocationPhotoWriteStatus
    state: LocationPhotoState | None = None


class ILocationPhotoRepository(ABC):
    @abstractmethod
    def add_photo(
        self, location_key: str, *, tenant_key: str, attachment_key: str, max_photos: int
    ) -> LocationPhotoWrite:
        """Put the tenant's ``location`` attachment first among the bed's photos; the first photo becomes the cover.

        ``unchanged`` when the bed already shows it, ``attachment_not_found`` unless the record exists under
        ``tenant_key`` with category ``location``, ``limit_reached`` when the bed holds ``max_photos`` already.
        """

    @abstractmethod
    def remove_photo(self, location_key: str, *, tenant_key: str, attachment_key: str) -> LocationPhotoWrite:
        """Drop the photo from the bed; the cover is cleared when it was that photo. ``not_a_photo`` if absent."""

    @abstractmethod
    def set_cover(self, location_key: str, *, tenant_key: str, attachment_key: str | None) -> LocationPhotoWrite:
        """Make one of the bed's photos its cover (``None`` clears it); ``not_a_photo`` for any other id."""


__all__ = [
    "ILocationPhotoRepository",
    "LocationPhotoState",
    "LocationPhotoWrite",
    "LocationPhotoWriteStatus",
]
