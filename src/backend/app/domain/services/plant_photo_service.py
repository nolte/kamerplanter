"""REQ-034 §2.1 — plant-instance photo gallery service.

Sits on top of the NFR-013 attachment fundament (:class:`AttachmentService`,
:class:`IAttachmentRepository`) and the REQ-013 plant instance
(:class:`IPlantInstanceRepository`). It owns the *fachliche* link between a
gallery photo (an attachment with ``category == plant``) and a plant instance:

- linking enforces the REQ-034 §2.1 consistency rules — an ``attachment_id`` may
  only enter ``photo_refs`` when the attachment exists, is ``category == plant``
  and carries the **same** ``tenant_key`` as the instance (cross-category /
  cross-tenant protection);
- ``cover_photo_ref`` MUST be an element of ``photo_refs`` (422 otherwise);
- the per-instance gallery quota (``STORAGE_MAX_PHOTOS_PER_INSTANCE``) is
  enforced *before* a photo is linked (the API enforces it before the upload so
  no orphan bytes are written);
- deleting a photo hard-deletes the attachment (bytes + thumbnails + metadata)
  via :class:`AttachmentService` and removes it from ``photo_refs`` /
  ``cover_photo_ref``;
- deleting a whole plant instance cascades the hard-delete to every referenced
  attachment (no orphan storage bytes — REQ-034 §2.1 / AC-08).

Authentication and RBAC happen in the API layer; this service assumes the
caller is already authorised for ``tenant_key``.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import structlog

from app.common.enums import AttachmentCategory
from app.common.exceptions import (
    NotFoundError,
    PhotoQuotaExceededError,
    ValidationError,
)
from app.common.tenant_guard import verify_tenant_ownership
from app.config.settings import Settings
from app.domain.interfaces.attachment_repository import UNSET, IAttachmentRepository, _Unset
from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
from app.domain.models.attachment import CAPTION_MAX_LENGTH, Attachment
from app.domain.models.plant_instance import PlantInstance
from app.domain.services.attachment_service import AttachmentService

logger = structlog.get_logger()


class PlantPhotoService:
    """Link / unlink / cover / list gallery photos of a plant instance."""

    def __init__(
        self,
        plant_repo: IPlantInstanceRepository,
        attachment_repo: IAttachmentRepository,
        attachment_service: AttachmentService,
        settings: Settings,
    ) -> None:
        self._plants = plant_repo
        self._attachments = attachment_repo
        self._attachment_service = attachment_service
        self._settings = settings

    # ── Internal helpers ──────────────────────────────────────────────

    def _get_instance(self, key: str, tenant_key: str) -> PlantInstance:
        plant = self._plants.get_by_key(key)
        if plant is None:
            raise NotFoundError("PlantInstance", key)
        verify_tenant_ownership(plant, tenant_key, "PlantInstance")
        return plant

    def _resolve_plant_attachment(self, attachment_id: str, tenant_key: str) -> Attachment:
        """Return a tenant-owned ``category == plant`` attachment or raise.

        Enforces REQ-034 §2.1: an attachment may only be linked when it exists,
        belongs to ``tenant_key`` (cross-tenant guard) and is in the ``plant``
        category (cross-category guard). ``IAttachmentRepository.get`` already
        scopes by tenant (returns ``None`` for a foreign tenant), so a missing
        *or* foreign attachment both surface as ``NotFoundError``.
        """
        attachment = self._attachments.get(attachment_id, tenant_key)
        if attachment is None:
            raise NotFoundError("Attachment", attachment_id)
        if attachment.category != AttachmentCategory.PLANT:
            raise ValidationError(
                "Attachment is not a plant photo and cannot be linked to a plant instance.",
                details=[
                    {
                        "field": "attachment_id",
                        "reason": f"Attachment '{attachment_id}' has category "
                        f"'{attachment.category.value}', expected 'plant'.",
                        "code": "INVALID_ATTACHMENT_CATEGORY",
                    }
                ],
            )
        return attachment

    def _enforce_photo_quota(self, plant: PlantInstance) -> None:
        # Known limitation (security review SEC-001, Low): this read-then-update
        # is not atomic against concurrent uploads on the same instance, so N
        # parallel uploads can moderately exceed the cap. Tolerated for a gallery
        # feature (same user/tenant, RBAC-gated); a hard guarantee would need an
        # atomic AQL `UPDATE ... FILTER LENGTH(photo_refs) < @limit` and is left
        # as a follow-up rather than risking the well-tested link path now.
        limit = self._settings.storage_max_photos_per_instance
        if limit > 0 and len(plant.photo_refs) >= limit:
            raise PhotoQuotaExceededError(plant.key or "unknown", limit)

    # ── Quota pre-check (called by the API before uploading) ──────────

    def assert_can_add_photo(self, key: str, tenant_key: str) -> PlantInstance:
        """Validate the instance exists and the gallery quota is not exhausted.

        Run *before* the upload so a rejected upload never writes orphan bytes
        (REQ-034 §3 / AC-15). Returns the resolved instance for reuse.
        """
        plant = self._get_instance(key, tenant_key)
        self._enforce_photo_quota(plant)
        return plant

    # ── Link ──────────────────────────────────────────────────────────

    def link_photo(self, key: str, attachment_id: str, tenant_key: str) -> PlantInstance:
        """Append a freshly uploaded plant photo to the instance gallery.

        Enforces category/tenant consistency (REQ-034 §2.1) and the per-instance
        quota. Idempotent: re-linking an already-present attachment is a no-op.
        Newest photo is prepended (display order is newest-first, §2.1).
        """
        plant = self._get_instance(key, tenant_key)
        self._resolve_plant_attachment(attachment_id, tenant_key)

        if attachment_id in plant.photo_refs:
            return plant

        self._enforce_photo_quota(plant)
        plant.photo_refs = [attachment_id, *plant.photo_refs]
        if plant.cover_photo_ref is None:
            plant.cover_photo_ref = attachment_id

        updated = self._plants.update(key, plant)
        logger.info(
            "plant_photo_linked",
            tenant_key=tenant_key,
            plant_instance_key=key,
            attachment_id=attachment_id,
            photo_count=len(updated.photo_refs),
        )
        return updated

    # ── Cover ─────────────────────────────────────────────────────────

    def set_cover(self, key: str, attachment_id: str, tenant_key: str) -> PlantInstance:
        """Mark ``attachment_id`` as the gallery cover photo (REQ-034 §2.1).

        Raises 422 when the attachment is not part of ``photo_refs``.
        """
        plant = self._get_instance(key, tenant_key)
        if attachment_id not in plant.photo_refs:
            raise ValidationError(
                "Cover photo must be one of the instance's gallery photos.",
                details=[
                    {
                        "field": "cover_photo_ref",
                        "reason": f"Attachment '{attachment_id}' is not linked to this plant instance.",
                        "code": "COVER_NOT_IN_GALLERY",
                    }
                ],
            )
        plant.cover_photo_ref = attachment_id
        updated = self._plants.update(key, plant)
        logger.info(
            "plant_photo_cover_set",
            tenant_key=tenant_key,
            plant_instance_key=key,
            attachment_id=attachment_id,
        )
        return updated

    # ── Edit metadata (caption / taken_on) ────────────────────────────

    def update_photo_metadata(
        self,
        key: str,
        attachment_id: str,
        tenant_key: str,
        *,
        caption: str | None | _Unset = UNSET,
        taken_on: date | None | _Unset = UNSET,
    ) -> Attachment:
        """REQ-034 §2.1 v1.2 — patch a gallery photo's caption / capture date.

        True PATCH: only the explicitly-passed fields are written; an omitted
        field is left untouched, an explicit ``None`` clears it. Guards mirror
        the cover/delete paths — the instance must be tenant-owned and the photo
        must be linked to it (``attachment_id in photo_refs``), otherwise 404.

        Validation (422):

        - ``caption`` length must not exceed :data:`CAPTION_MAX_LENGTH`;
        - ``taken_on`` must not lie in the future.

        Returns the updated attachment.
        """
        plant = self._get_instance(key, tenant_key)
        if attachment_id not in plant.photo_refs:
            raise NotFoundError("PlantPhoto", attachment_id)

        if not isinstance(caption, _Unset) and caption is not None and len(caption) > CAPTION_MAX_LENGTH:
            raise ValidationError(
                f"Caption must not exceed {CAPTION_MAX_LENGTH} characters.",
                details=[
                    {
                        "field": "caption",
                        "reason": f"Caption has {len(caption)} characters, the maximum is {CAPTION_MAX_LENGTH}.",
                        "code": "CAPTION_TOO_LONG",
                    }
                ],
            )

        if not isinstance(taken_on, _Unset) and taken_on is not None and taken_on > datetime.now(UTC).date():
            raise ValidationError(
                "Capture date must not be in the future.",
                details=[
                    {
                        "field": "taken_on",
                        "reason": f"Capture date '{taken_on.isoformat()}' is in the future.",
                        "code": "TAKEN_ON_IN_FUTURE",
                    }
                ],
            )

        updated = self._attachments.update_metadata(
            attachment_id,
            tenant_key,
            caption=caption,
            taken_on=taken_on,
        )
        if updated is None:
            # The id is in photo_refs but the attachment metadata is gone — a
            # stale reference; surface it as a missing photo rather than 500.
            raise NotFoundError("PlantPhoto", attachment_id)

        logger.info(
            "plant_photo_metadata_updated",
            tenant_key=tenant_key,
            plant_instance_key=key,
            attachment_id=attachment_id,
            caption_set=not isinstance(caption, _Unset),
            taken_on_set=not isinstance(taken_on, _Unset),
        )
        return updated

    # ── List ──────────────────────────────────────────────────────────

    def list_photos(self, key: str, tenant_key: str) -> tuple[PlantInstance, list[Attachment]]:
        """Return the instance plus its gallery attachments in display order.

        Photos are returned newest-first by ``attachments.created_at``; the
        ``cover_photo_ref`` (or the first element) is the cover. Stale ids — an
        attachment that no longer exists — are silently skipped (best-effort
        gallery; the data is reconciled on the next link/delete).
        """
        plant = self._get_instance(key, tenant_key)
        photos: list[Attachment] = []
        for attachment_id in plant.photo_refs:
            attachment = self._attachments.get(attachment_id, tenant_key)
            if attachment is not None:
                photos.append(attachment)
        photos.sort(key=lambda a: (a.created_at is not None, a.created_at), reverse=True)
        return plant, photos

    # ── Delete a single photo ─────────────────────────────────────────

    async def delete_photo(self, key: str, attachment_id: str, tenant_key: str) -> PlantInstance:
        """Hard-delete a gallery photo and unlink it (REQ-034 §5 / AC-07).

        Removes the attachment bytes + thumbnails + metadata via the attachment
        service, then drops the id from ``photo_refs`` and re-resolves the cover
        when the deleted photo was the cover. Raises 404 when the photo is not
        linked to this instance.
        """
        plant = self._get_instance(key, tenant_key)
        if attachment_id not in plant.photo_refs:
            raise NotFoundError("PlantPhoto", attachment_id)

        # Hard-delete the bytes/thumbnails/metadata (idempotent in the service).
        await self._attachment_service.delete(attachment_id, tenant_key)

        plant.photo_refs = [ref for ref in plant.photo_refs if ref != attachment_id]
        if plant.cover_photo_ref == attachment_id:
            plant.cover_photo_ref = plant.photo_refs[0] if plant.photo_refs else None

        updated = self._plants.update(key, plant)
        logger.info(
            "plant_photo_deleted",
            tenant_key=tenant_key,
            plant_instance_key=key,
            attachment_id=attachment_id,
            photo_count=len(updated.photo_refs),
        )
        return updated

    # ── Cascade on instance deletion ──────────────────────────────────

    async def delete_all_photos(self, plant: PlantInstance, tenant_key: str) -> int:
        """Hard-delete every gallery photo of an instance (REQ-034 §2.1 / AC-08).

        Called by the plant-instance removal path so no orphan storage bytes
        remain. Idempotent and best-effort: an already-missing attachment is a
        no-op. Returns the number of attachments removed.
        """
        removed = 0
        for attachment_id in list(plant.photo_refs):
            if await self._attachment_service.delete(attachment_id, tenant_key):
                removed += 1
        if removed:
            logger.info(
                "plant_photos_cascade_deleted",
                tenant_key=tenant_key,
                plant_instance_key=plant.key,
                removed=removed,
            )
        return removed


__all__ = ["PlantPhotoService"]
