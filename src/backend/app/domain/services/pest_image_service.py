"""REQ-010 — user-contributed pest reference image service.

Phase 1 scope: a tenant-private gallery of user-uploaded photos attached to a
*global* pest record. The service composes the existing NFR-013 attachment
pipeline (EXIF strip, magic-byte / MIME whitelist, virus scan, SHA-256 dedup,
object storage) with a thin :class:`PestImageContribution` link document — it
never re-implements upload validation.

Authorization (tenant membership + RBAC attachment permission) and URI
construction happen in the API layer; this service assumes the caller is
already authorized for ``tenant_key`` / ``user_key`` and works purely on keys.
"""

from __future__ import annotations

from dataclasses import dataclass

import structlog

from app.common.enums import AttachmentCategory
from app.domain.engines.storage.thumbnail_generator import can_render
from app.domain.interfaces.pest_image_repository import IPestImageRepository
from app.domain.models.pest_image import PestImageContribution
from app.domain.services.attachment_service import AttachmentService
from app.domain.services.ipm_service import IpmService

logger = structlog.get_logger()

# REQ-010 — thumbnail rendition surfaced to the gallery. Must be one of
# ``THUMBNAIL_SIZES`` (512 is the medium "card" rendition).
GALLERY_THUMBNAIL_SIZE = 512


@dataclass(frozen=True)
class PestImageView:
    """A contribution paired with the data the API needs to build its response.

    ``mime_type`` lets the API decide whether a thumbnail rendition exists
    (non-renderable types get no ``thumbnail_uri``).
    """

    contribution: PestImageContribution
    mime_type: str
    has_thumbnail: bool


class PestImageService:
    """Contribute / list / delete tenant-private pest reference images."""

    def __init__(
        self,
        repo: IPestImageRepository,
        attachment_service: AttachmentService,
        ipm_service: IpmService,
    ) -> None:
        self._repo = repo
        self._attachments = attachment_service
        self._ipm = ipm_service

    async def contribute(
        self,
        *,
        tenant_key: str,
        user_key: str,
        pest_key: str,
        data: bytes,
        mime_type: str,
        filename: str,
        caption: str | None = None,
    ) -> PestImageView:
        """Upload an image and link it to a global pest as a tenant contribution.

        Order matters: the pest must exist first (``IpmService.get_pest`` raises
        ``NotFoundError`` otherwise — so an unknown pest never produces an orphan
        upload), then the attachment runs through the full NFR-013 pipeline
        (category ``PEST_REFERENCE``), then the link document is persisted.
        ``caption`` is normalised (trimmed; an empty/whitespace caption → ``None``).
        """
        # Validate the global pest exists *before* storing any bytes.
        self._ipm.get_pest(pest_key)

        attachment = await self._attachments.upload(
            tenant_key=tenant_key,
            user_key=user_key,
            data=data,
            mime_type=mime_type,
            original_filename=filename,
            category=AttachmentCategory.PEST_REFERENCE,
        )

        contribution = PestImageContribution(
            tenant_key=tenant_key,
            pest_key=pest_key,
            attachment_id=attachment.key or "",
            contributed_by=user_key,
            caption=_normalize_caption(caption),
        )
        created = self._repo.create(contribution)
        logger.info(
            "pest_image_contributed",
            tenant_key=tenant_key,
            user_key=user_key,
            pest_key=pest_key,
            contribution_id=created.key,
            attachment_id=attachment.key,
        )
        return self._to_view(created, attachment.mime_type)

    def list_for_pest(self, tenant_key: str, pest_key: str) -> list[PestImageView]:
        """Return the tenant's contributions for a pest as response-ready views."""
        contributions = self._repo.list_for_pest(tenant_key, pest_key)
        return [self._to_view(c, self._resolve_mime(c.attachment_id, tenant_key)) for c in contributions]

    async def delete(self, tenant_key: str, user_key: str, contribution_key: str) -> bool:
        """Delete a tenant-owned contribution and its underlying attachment.

        Tenant-scoped: a contribution belonging to another tenant is invisible
        and yields ``False`` (idempotent). The link document is removed first,
        then the attachment — so a failed attachment delete never strands a
        dangling reference (the attachment cleanup is itself idempotent).
        """
        contribution = self._repo.get(contribution_key, tenant_key)
        if contribution is None:
            return False

        self._repo.delete(contribution_key, tenant_key)
        await self._attachments.delete(contribution.attachment_id, tenant_key)
        logger.info(
            "pest_image_deleted",
            tenant_key=tenant_key,
            user_key=user_key,
            pest_key=contribution.pest_key,
            contribution_id=contribution_key,
            attachment_id=contribution.attachment_id,
        )
        return True

    def attachment_service_max_upload_bytes(self) -> int:
        """Expose the configured max upload size so the API can early-reject (SEC-005)."""
        return self._attachments.max_upload_bytes()

    # --- helpers -----------------------------------------------------

    def _resolve_mime(self, attachment_id: str, tenant_key: str) -> str:
        """Return the attachment's MIME type, or empty string if it is gone.

        A missing attachment (e.g. raced erasure) must not blow up the listing;
        an empty MIME simply means "no thumbnail" for that row.
        """
        from app.common.exceptions import AttachmentNotFoundError

        try:
            return self._attachments.get_attachment(attachment_id, tenant_key).mime_type
        except AttachmentNotFoundError:
            return ""

    def _to_view(self, contribution: PestImageContribution, mime_type: str) -> PestImageView:
        return PestImageView(
            contribution=contribution,
            mime_type=mime_type,
            has_thumbnail=can_render(mime_type),
        )


def _normalize_caption(caption: str | None) -> str | None:
    if caption is None:
        return None
    trimmed = caption.strip()
    return trimmed or None


__all__ = ["GALLERY_THUMBNAIL_SIZE", "PestImageService", "PestImageView"]
