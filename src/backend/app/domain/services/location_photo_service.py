"""The photos of a bed (REQ-053 GP-FR-051, WP 8.18): list, add, remove, set the cover, discard after a bed delete.

A bed photo is an attachment of category ``location`` uploaded beforehand through ``POST /attachments`` (NFR-013:
size limit, magic bytes, EXIF/GPS strip, quota). This service links it to the bed (``Location.photo_refs``, newest
first) and keeps ``cover_photo_ref`` one of them. It is presentation: not part of the plan revision and never in
the plan's JSON export (decision bundle #2643 item 7, GP-FR-140).

**Tenant.** A ``Location`` has no ``tenant_key``; every method resolves the bed through its site
(``location_ownership.resolve_owned_location``) with ``*, tenant_key: str`` and no default (#2107), and the
repository re-reads it under the same tenant inside its transaction. An attachment that is absent, another
tenant's, of another category or outside its tenant's storage namespace answers one 422 ``reference.not_found``
(GP-NFR-058), so the response is no oracle for another tenant's attachments.

**Roles** (#2643 item 7). Linking a photo and choosing the cover need ``grower``; removing a photo needs
``grower`` for one's **own** upload and ``lead`` for another member's (or an erased member's).

**Removing a photo** deletes the attachment only when nothing else names it: the record goes through
:meth:`AttachmentService.delete_if_unreferenced` (the reference scan sees every bed, gallery, task, care event and
plan underlay), and its stored object only when no other record holds it (#1770). The bed's own reference is gone
by then. A failure there is logged, never raised: the bed's write has committed, and a 500 would make the client
retry a removal that no longer finds the photo. Deleting a whole bed (or its site) hands the photos it held to
:meth:`discard_released` after the commit, with the same rule.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Iterable
from typing import Protocol

import structlog

from app.common.enums import AttachmentCategory, TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError, PlanError, PlanValidationError
from app.common.log_privacy import log_tenant
from app.common.types import LocationKey
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.interfaces.attachment_repository import IAttachmentRepository
from app.domain.interfaces.location_photo_repository import (
    ILocationPhotoRepository,
    LocationPhotoState,
    LocationPhotoWrite,
)
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.models.attachment import Attachment
from app.domain.models.location_photo import LocationPhoto, LocationPhotoGallery
from app.domain.models.site import MAX_PHOTOS_PER_LOCATION, Location
from app.domain.services.attachment_service import AttachmentService
from app.domain.services.location_ownership import resolve_owned_location

logger = structlog.get_logger(__name__)

ERROR_REFERENCE_NOT_FOUND = "reference.not_found"
ERROR_PHOTO_LIMIT = "location.photo_limit_reached"
ERROR_COVER_NOT_A_PHOTO = "location.cover_not_a_photo"


class UnreferencedAttachmentDelete(Protocol):
    """``AttachmentService.delete_if_unreferenced``: the record goes unless a carrier names it, then its object."""

    async def delete_if_unreferenced(self, attachment_id: str, tenant_key: str) -> bool: ...


class LocationPhotoDiscard(Protocol):
    """What a bed or site delete needs after its commit: :meth:`LocationPhotoService.discard_released`."""

    async def discard_released(self, attachment_ids: Iterable[str], *, tenant_key: str) -> int: ...


class LocationPhotoService:
    def __init__(
        self,
        site_repo: ISiteRepository,
        photo_repo: ILocationPhotoRepository,
        attachment_repo: IAttachmentRepository,
        attachments: Callable[[], UnreferencedAttachmentDelete],
    ) -> None:
        self._sites = site_repo
        self._photos = photo_repo
        self._attachment_repo = attachment_repo
        # A provider: the attachment service (object storage, quota, rendition claims) is built only by a call that
        # has a photo to discard, so the bed delete and the reads stay free of it.
        self._attachments = attachments

    # ── helpers ───────────────────────────────────────────────────────────

    def _owned_location(self, key: LocationKey, *, tenant_key: str) -> Location:
        return resolve_owned_location(self._sites, key, tenant_key)

    @staticmethod
    def _require_editor(role: TenantRole) -> None:
        if not MembershipEngine.can_edit_resource(role):
            raise ForbiddenError("Requires at least grower role.")

    @staticmethod
    def _reference_not_found() -> PlanValidationError:
        return PlanValidationError([(None, "attachment_id", ERROR_REFERENCE_NOT_FOUND, {})])

    def _bed_photo(self, attachment_id: str, *, tenant_key: str) -> Attachment:
        """The tenant's own ``location`` attachment, else 422 ``reference.not_found``."""
        attachment = self._attachment_repo.get(attachment_id, tenant_key) if attachment_id else None
        if (
            attachment is None
            or attachment.category != AttachmentCategory.LOCATION
            or not AttachmentService.in_own_namespace(attachment)
        ):
            raise self._reference_not_found()
        return attachment

    @staticmethod
    def _may_remove(attachment: Attachment | None, *, user_key: str, role: TenantRole) -> bool:
        """Own upload from ``grower`` up, another member's (or an erased member's) only as ``lead`` (#2643 item 7)."""
        if not MembershipEngine.can_edit_resource(role):
            return False
        if MembershipEngine.can_delete_resource(role):
            return True
        # A stale reference (the record is gone) has no owner; any editor may clear it from the bed.
        return attachment is None or (bool(user_key) and attachment.created_by == user_key)

    def _view(
        self, location_key: str, state: LocationPhotoState, *, tenant_key: str, user_key: str, role: TenantRole
    ) -> LocationPhotoGallery:
        # Comprehensions, not ``append``: the write-route sweep cannot type a list receiver (its ceiling, #2039).
        found = [(ref, self._attachment_repo.get(ref, tenant_key)) for ref in state.photo_refs]
        photos = tuple(
            LocationPhoto(
                attachment=attachment,
                is_cover=ref == state.cover_photo_ref,
                can_remove=self._may_remove(attachment, user_key=user_key, role=role),
            )
            for ref, attachment in found
            if attachment is not None
        )
        return LocationPhotoGallery(
            location_key=location_key,
            cover_photo_ref=state.cover_photo_ref,
            photos=photos,
        )

    @staticmethod
    def _state_of(write: LocationPhotoWrite, location_key: str) -> LocationPhotoState:
        """The state a write left, or the refusal its status stands for."""
        if write.status == "location_not_found" or write.state is None:
            # Gone (or moved to another tenant's site) between the service's read and the transaction's.
            raise NotFoundError("Location", location_key)
        return write.state

    # ── read ──────────────────────────────────────────────────────────────

    def list_photos(
        self, key: LocationKey, *, tenant_key: str, user_key: str, role: TenantRole
    ) -> LocationPhotoGallery:
        """The bed's photos for any member (``viewer`` included), with ``can_remove`` for the caller."""
        location = self._owned_location(key, tenant_key=tenant_key)
        state = LocationPhotoState(photo_refs=tuple(location.photo_refs), cover_photo_ref=location.cover_photo_ref)
        return self._view(key, state, tenant_key=tenant_key, user_key=user_key, role=role)

    # ── writes ────────────────────────────────────────────────────────────

    def add_photo(
        self, key: LocationKey, attachment_id: str, *, tenant_key: str, user_key: str, role: TenantRole
    ) -> LocationPhotoGallery:
        """Link an uploaded ``location`` attachment to the bed, newest first; the first photo becomes the cover.

        Idempotent for a photo the bed already shows. 404 for a bed outside the tenant, 403 below ``grower``,
        422 ``reference.not_found`` for an attachment that is not the tenant's own bed photo, 422
        ``location.photo_limit_reached`` at :data:`MAX_PHOTOS_PER_LOCATION`.
        """
        self._owned_location(key, tenant_key=tenant_key)
        self._require_editor(role)
        self._bed_photo(attachment_id, tenant_key=tenant_key)
        write = self._photos.add_photo(
            key, tenant_key=tenant_key, attachment_key=attachment_id, max_photos=MAX_PHOTOS_PER_LOCATION
        )
        if write.status == "attachment_not_found":
            # Removed (or re-categorised) between the read above and the transaction.
            raise self._reference_not_found()
        if write.status == "limit_reached":
            raise PlanError(
                ERROR_PHOTO_LIMIT,
                f"A bed holds at most {MAX_PHOTOS_PER_LOCATION} photos.",
                status_code=422,
                field="attachment_id",
                limit=MAX_PHOTOS_PER_LOCATION,
                current=len(write.state.photo_refs) if write.state is not None else MAX_PHOTOS_PER_LOCATION,
            )
        state = self._state_of(write, key)
        if write.status == "written":
            logger.info(
                "location_photo_added",
                tenant=log_tenant(tenant_key),
                location_key=key,
                attachment_id=attachment_id,
                photo_count=len(state.photo_refs),
            )
        return self._view(key, state, tenant_key=tenant_key, user_key=user_key, role=role)

    def set_cover(
        self, key: LocationKey, attachment_id: str | None, *, tenant_key: str, user_key: str, role: TenantRole
    ) -> LocationPhotoGallery:
        """Make one of the bed's photos its cover, or clear the cover with ``None`` (``grower`` up).

        422 ``location.cover_not_a_photo`` for an id that is not one of the bed's photos.
        """
        self._owned_location(key, tenant_key=tenant_key)
        self._require_editor(role)
        write = self._photos.set_cover(key, tenant_key=tenant_key, attachment_key=attachment_id)
        if write.status == "not_a_photo":
            raise PlanError(
                ERROR_COVER_NOT_A_PHOTO,
                "The cover must be one of the bed's photos.",
                status_code=422,
                field="attachment_id",
            )
        state = self._state_of(write, key)
        return self._view(key, state, tenant_key=tenant_key, user_key=user_key, role=role)

    async def remove_photo(
        self, key: LocationKey, attachment_id: str, *, tenant_key: str, user_key: str, role: TenantRole
    ) -> LocationPhotoGallery:
        """Unlink a photo from the bed and delete it unless something else names it (see the module docstring).

        404 for a bed outside the tenant or a photo the bed does not show; 403 below ``grower``, and for another
        member's photo below ``lead``. The cover is cleared when it was this photo.
        """
        location = await asyncio.to_thread(self._owned_location, key, tenant_key=tenant_key)
        self._require_editor(role)
        if attachment_id not in location.photo_refs:
            raise NotFoundError("LocationPhoto", attachment_id)
        attachment = await asyncio.to_thread(self._attachment_repo.get, attachment_id, tenant_key)
        if not self._may_remove(attachment, user_key=user_key, role=role):
            raise ForbiddenError("Removing another member's photo requires the lead role.")
        write = await asyncio.to_thread(
            self._photos.remove_photo, key, tenant_key=tenant_key, attachment_key=attachment_id
        )
        if write.status == "not_a_photo":
            # Another request removed it meanwhile; the bed no longer shows it either way.
            raise NotFoundError("LocationPhoto", attachment_id)
        state = self._state_of(write, key)
        logger.info(
            "location_photo_removed",
            tenant=log_tenant(tenant_key),
            location_key=key,
            attachment_id=attachment_id,
            photo_count=len(state.photo_refs),
        )
        if attachment is not None and attachment.category == AttachmentCategory.LOCATION:
            await self._discard(attachment_id, tenant_key=tenant_key)
        return await asyncio.to_thread(self._view, key, state, tenant_key=tenant_key, user_key=user_key, role=role)

    # ── after a bed or site delete ────────────────────────────────────────

    async def discard_released(self, attachment_ids: Iterable[str], *, tenant_key: str) -> int:
        """Delete the photos a committed bed (or site) delete let go of, unless something else still names them.

        Only ``location`` attachments of the tenant are considered - an id of any other category is never deleted
        through this path. Each failure is logged and skipped; returns how many photos were deleted.
        """
        discarded = 0
        for attachment_id in _unique(attachment_ids):
            attachment = await asyncio.to_thread(self._attachment_repo.get, attachment_id, tenant_key)
            if attachment is None or attachment.category != AttachmentCategory.LOCATION:
                continue
            if await self._discard(attachment_id, tenant_key=tenant_key):
                discarded += 1
        return discarded

    async def _discard(self, attachment_id: str, *, tenant_key: str) -> bool:
        """``delete_if_unreferenced`` after the bed's write committed; a failure is logged, never raised."""
        try:
            provider = self._attachments
            deleter: UnreferencedAttachmentDelete = provider()
            deleted = await deleter.delete_if_unreferenced(attachment_id, tenant_key)
        except Exception as exc:  # noqa: BLE001 — the bed's write has committed; its response must not turn into a 500
            logger.warning(
                "location_photo_discard_failed",
                tenant=log_tenant(tenant_key),
                attachment_id=attachment_id,
                error_type=type(exc).__name__,
            )
            return False
        if deleted:
            logger.info("location_photo_discarded", tenant=log_tenant(tenant_key), attachment_id=attachment_id)
        return deleted


def _unique(attachment_ids: Iterable[str]) -> list[str]:
    """The ids in their order, each once."""
    return list({attachment_id: None for attachment_id in attachment_ids})


async def release_location_photos(
    photos: Callable[[], LocationPhotoDiscard] | None, attachment_ids: Iterable[str], *, tenant_key: str
) -> None:
    """The step a committed bed or site delete runs for the photos it let go of; never raises (WP 8.18).

    The delete has committed when this runs, so a failure (storage, the reference scan's time budget, the database)
    is logged and the delete still succeeds - a 500 made the client retry into a 404 that never reaches the photos
    again. ``photos`` is ``None`` for a service built without the attachment side (a test, a tool): then the photos
    stay as records until the tenant erasure, and the log says so.
    """
    released = _unique(attachment_ids)
    if not released:
        return
    if photos is None:
        logger.warning("location_photos_not_discarded", tenant=log_tenant(tenant_key), count=len(released))
        return
    try:
        discard: LocationPhotoDiscard = photos()
        await discard.discard_released(released, tenant_key=tenant_key)
    except Exception as exc:  # noqa: BLE001 — the delete has committed; its response must not turn into a 500
        logger.warning(
            "location_photos_discard_failed",
            tenant=log_tenant(tenant_key),
            count=len(released),
            error_type=type(exc).__name__,
        )


__all__ = [
    "ERROR_COVER_NOT_A_PHOTO",
    "ERROR_PHOTO_LIMIT",
    "ERROR_REFERENCE_NOT_FOUND",
    "LocationPhotoDiscard",
    "LocationPhotoService",
    "UnreferencedAttachmentDelete",
    "release_location_photos",
]
