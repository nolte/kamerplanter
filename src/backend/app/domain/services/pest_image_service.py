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
from typing import TYPE_CHECKING

import structlog

from app.common.enums import AttachmentCategory, PestImageStatus
from app.domain.engines.storage.thumbnail_generator import can_render
from app.domain.interfaces.pest_image_repository import IPestImageRepository
from app.domain.models.pest_image import PestImageContribution
from app.domain.services.attachment_service import AttachmentService
from app.domain.services.ipm_service import IpmService

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from app.data_access.external.pest_inference_client import PestDetectionInferenceClient

logger = structlog.get_logger()

# REQ-010 — thumbnail rendition surfaced to the gallery. Must be one of
# ``THUMBNAIL_SIZES`` (512 is the medium "card" rendition).
GALLERY_THUMBNAIL_SIZE = 512


@dataclass(frozen=True)
class PestImageView:
    """A contribution paired with the data the API needs to build its response.

    ``mime_type`` lets the API decide whether a thumbnail rendition exists
    (non-renderable types get no ``thumbnail_uri``). ``is_own`` distinguishes
    the requesting tenant's own contributions (served via tenant-scoped
    attachment URIs) from foreign *promoted* contributions (served via the
    global content endpoint).
    """

    contribution: PestImageContribution
    mime_type: str
    has_thumbnail: bool
    is_own: bool = True

    @property
    def is_active(self) -> bool:
        """Curation state of the underlying contribution (deselected → ``False``)."""
        return self.contribution.is_active


@dataclass(frozen=True)
class PestInspectionImageView:
    """A read-only pest-detail gallery photo sourced from a tenant inspection.

    Unlike :class:`PestImageView` this is not a curated contribution: it is a
    real attachment referenced by an :class:`Inspection` whose
    ``detected_pest_keys`` includes the pest. It is always the calling tenant's
    own data (``is_own=True``), served through tenant-scoped attachment URIs and
    never deletable / promotable through the gallery. ``attachment_id`` doubles
    as the stable client key.
    """

    attachment_id: str
    mime_type: str
    has_thumbnail: bool


@dataclass(frozen=True)
class PestRecognitionImageView:
    """A read-only, GLOBAL reference image of the pest's recognition index.

    REQ-010 / REQ-044 — surfaces the *active* few-shot prototype provenances of
    a pest's detection class. Unlike contributions / inspections **no pixel is
    stored locally**: the image lives at an external, CC-licensed ``source_url``
    (GBIF / iNaturalist / Wikimedia). It is never the calling tenant's data
    (``is_own=False``), never deletable, and the CC-BY ``attribution`` /
    ``license`` must be displayed next to the image. ``prototype_id`` is the
    inference-service row id and yields the stable client key
    (``recognition:{prototype_id}``).
    """

    prototype_id: int
    source_url: str
    attribution: str | None = None
    license: str | None = None
    # Curation state of the inference-service prototype. Always ``True`` in the
    # default (active-only) gallery; may be ``False`` in the admin curation view
    # (``include_inactive=True``), where deselected prototypes are surfaced too.
    is_active: bool = True


@dataclass(frozen=True)
class PestImageContent:
    """The resolved bytes-source for serving a (promoted) contribution globally."""

    contribution: PestImageContribution
    attachment: object  # app.domain.models.attachment.Attachment (avoid import cycle)


class PestImageService:
    """Contribute / list / delete tenant-private pest reference images."""

    def __init__(
        self,
        repo: IPestImageRepository,
        attachment_service: AttachmentService,
        ipm_service: IpmService,
        inference_client: PestDetectionInferenceClient | None = None,
    ) -> None:
        self._repo = repo
        self._attachments = attachment_service
        self._ipm = ipm_service
        # Optional: only wired when the recognition index may be queried. The
        # gallery degrades gracefully (no recognition tiles) when it is ``None``
        # or the ``pest_detection_enabled`` feature flag is off.
        self._inference_client = inference_client

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

    def list_for_pest(self, tenant_key: str, pest_key: str, *, include_inactive: bool = False) -> list[PestImageView]:
        """Return the combined gallery for a pest from the tenant's perspective.

        Two sources are merged:

        * the tenant's **own** contributions (any status), served via tenant-
          scoped attachment URIs (``is_own=True``);
        * all **promoted** contributions of *other* tenants, served via the
          global content endpoint (``is_own=False``).

        An own contribution that is itself promoted stays ``is_own=True`` (it
        keeps its tenant URI). The two sources are deduplicated by contribution
        key so a promoted own image never appears twice. Newest first.

        ``include_inactive`` is a platform-admin-only curation flag (the API
        enforces the privilege): when ``True`` deselected contributions are
        returned too (dimmed in the UI); the default hides them for everyone.
        """
        own = self._repo.list_for_pest(tenant_key, pest_key, include_inactive=include_inactive)
        own_keys = {c.key for c in own}
        foreign_promoted = [
            c
            for c in self._repo.list_promoted_for_pest(pest_key, include_inactive=include_inactive)
            if c.tenant_key != tenant_key and c.key not in own_keys
        ]

        views: list[PestImageView] = [
            self._to_view(c, self._resolve_mime(c.attachment_id, tenant_key), is_own=True) for c in own
        ]
        # Foreign promoted images: resolve MIME against the *owning* tenant.
        views += [
            self._to_view(c, self._resolve_mime(c.attachment_id, c.tenant_key), is_own=False) for c in foreign_promoted
        ]
        views.sort(key=_created_sort_key, reverse=True)
        return views

    def list_inspection_images_for_pest(self, tenant_key: str, pest_key: str) -> list[PestInspectionImageView]:
        """Return read-only inspection photos of a pest for the tenant gallery.

        REQ-010 — surfaces the real photos (``Inspection.photo_refs``) of the
        calling tenant's inspections that detected ``pest_key``. The pest is
        validated to exist first (consistent 404 with the contribution path).
        The id list is already deduplicated + newest-first by the repository; a
        vanished attachment (raced erasure) is silently dropped so a stale ref
        never blows up the listing. Strict tenant isolation is enforced in the
        AQL filter — only ``tenant_key``'s inspections are scanned.
        """
        self._ipm.get_pest(pest_key)
        attachment_ids = self._ipm.get_inspection_photo_refs_for_pest(tenant_key, pest_key)

        views: list[PestInspectionImageView] = []
        for attachment_id in attachment_ids:
            mime_type = self._resolve_mime(attachment_id, tenant_key)
            if not mime_type:
                # Attachment metadata is gone (stale ref) — skip rather than
                # surfacing an un-renderable, broken tile.
                continue
            views.append(
                PestInspectionImageView(
                    attachment_id=attachment_id,
                    mime_type=mime_type,
                    has_thumbnail=can_render(mime_type),
                )
            )
        return views

    def list_recognition_images_for_pest(
        self, pest_key: str, *, include_inactive: bool = False
    ) -> list[PestRecognitionImageView]:
        """Return the GLOBAL recognition reference images of a pest (read-only).

        REQ-010 / REQ-044 — surfaces the *active* few-shot prototype provenances
        of the pest's detection class (``Pest.detection_slug``). The pest is
        validated to exist first (consistent 404 with the other gallery paths).

        Best-effort and privacy-gated: an empty list is returned — never an
        error — when

        * the pest carries no ``detection_slug`` (it is not part of the
          recognition taxonomy);
        * no inference client is wired or ``pest_detection_enabled`` is off
          (Default-Privacy);
        * the inference-service is unreachable / errors (the client itself
          already swallows ``httpx`` errors into an empty payload, but any
          unexpected error is caught here too so a recognition hiccup can never
          break the rest of the gallery).

        Only rows that actually carry an external ``source_url`` are surfaced (no
        pixel is ever stored locally). Newest-/index-order is preserved as
        returned by the inference-service.
        """
        pest = self._ipm.get_pest(pest_key)
        detection_slug = pest.detection_slug
        if not detection_slug:
            return []

        from app.config.settings import settings

        if self._inference_client is None or not settings.pest_detection_enabled:
            return []

        try:
            payload = self._inference_client.list_prototypes(detection_slug, active_only=not include_inactive)
        except Exception as exc:  # noqa: BLE001 — best-effort: a recognition outage must not break the gallery
            logger.warning(
                "pest_recognition_images_unavailable",
                pest_key=pest_key,
                detection_slug=detection_slug,
                error=str(exc),
            )
            return []

        views: list[PestRecognitionImageView] = []
        for row in payload.get("images", []):
            source_url = row.get("source_url")
            prototype_id = row.get("id")
            if not source_url or prototype_id is None:
                # No external URL → nothing to render (no pixel is stored).
                continue
            views.append(
                PestRecognitionImageView(
                    prototype_id=int(prototype_id),
                    source_url=source_url,
                    attribution=row.get("attribution"),
                    license=row.get("license"),
                    # Missing flag (active-only payload) → active.
                    is_active=bool(row.get("is_active", True)),
                )
            )
        return views

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

    # --- moderation (platform-admin, cross-tenant) -------------------

    def list_all_for_pest(self, pest_key: str) -> list[PestImageView]:
        """Return *every* tenant's contributions for a pest (admin moderation).

        Validates the global pest exists first. MIME is resolved against each
        contribution's *owning* tenant. The API exposes provenance
        (``tenant_key`` / ``contributed_by``) and status from the contribution.
        """
        self._ipm.get_pest(pest_key)
        contributions = self._repo.list_all_for_pest(pest_key)
        return [
            self._to_view(c, self._resolve_mime(c.attachment_id, c.tenant_key), is_own=False) for c in contributions
        ]

    def set_promotion(self, *, contribution_key: str, promote: bool, admin_user_key: str) -> PestImageView | None:
        """Promote / demote a contribution to/from global visibility (idempotent).

        Returns the updated view, or ``None`` when the contribution is unknown.
        Promotion is the trigger point for the later recognition wiring — see
        :meth:`_on_promotion_changed`.
        """
        existing = self._repo.get_by_key(contribution_key)
        if existing is None:
            return None

        target = PestImageStatus.PROMOTED if promote else PestImageStatus.PRIVATE
        updated = self._repo.set_status(
            contribution_key,
            target,
            promoted_by=admin_user_key if promote else None,
        )
        if updated is None:
            return None

        logger.info(
            "pest_image_promotion_changed",
            contribution_id=contribution_key,
            tenant_key=updated.tenant_key,
            pest_key=updated.pest_key,
            status=updated.status.value,
            admin_user_key=admin_user_key,
        )
        # Only fire the side-effect on an actual transition (idempotent calls
        # that don't change the status do not re-enqueue recognition work).
        if existing.status != updated.status:
            self._on_promotion_changed(updated, promoted=promote)

        return self._to_view(updated, self._resolve_mime(updated.attachment_id, updated.tenant_key), is_own=False)

    def set_active(self, *, contribution_key: str, is_active: bool, admin_user_key: str) -> PestImageView | None:
        """Deselect / re-include a contribution from the gallery (idempotent).

        Pure display curation: deactivating a *promoted* contribution hides it
        from the gallery but leaves the recognition index untouched (only the
        promote/demote path mutates the index — see
        :meth:`_on_promotion_changed`). Returns the updated view, or ``None``
        when the contribution is unknown.
        """
        existing = self._repo.get_by_key(contribution_key)
        if existing is None:
            return None

        updated = self._repo.set_active(contribution_key, is_active)
        if updated is None:
            return None

        if existing.is_active != updated.is_active:
            logger.info(
                "pest_image_active_changed",
                contribution_id=contribution_key,
                tenant_key=updated.tenant_key,
                pest_key=updated.pest_key,
                is_active=updated.is_active,
                admin_user_key=admin_user_key,
            )
        return self._to_view(updated, self._resolve_mime(updated.attachment_id, updated.tenant_key), is_own=False)

    def _on_promotion_changed(self, contribution: PestImageContribution, *, promoted: bool) -> None:
        """Recognition-index wiring for a promotion transition (REQ-010 P2).

        When a contribution is promoted it becomes globally visible and is a
        candidate reference image for the few-shot pest-recognition index
        (REQ-029-A / inference-service ``/pest/reference`` + pgvector
        embeddings); when demoted it must be retracted from that index.

        The actual indexing runs **async** in a Celery task so the admin
        promotion response is never blocked and a recognition-service hiccup can
        never fail the moderation request — only the embedding + provenance are
        stored service-side (no pixel persists, REQ-044 §8). Default-Privacy:
        nothing is dispatched while ``pest_detection_enabled`` is off; the task
        re-checks the flag too, so this gate is belt-and-suspenders.
        """
        from app.config.settings import settings

        if not settings.pest_detection_enabled:
            logger.info(
                "pest_image_recognition_hook_skipped",
                contribution_id=contribution.key,
                pest_key=contribution.pest_key,
                action="index_upsert" if promoted else "index_retract",
                reason="pest_detection_disabled",
            )
            return

        if contribution.key is None:
            return

        # Imported lazily to keep the service free of a hard Celery dependency
        # (tests construct the service with in-memory doubles only).
        from app.tasks.pest_image_tasks import (
            index_promoted_pest_image_task,
            retract_promoted_pest_image_task,
        )

        task = index_promoted_pest_image_task if promoted else retract_promoted_pest_image_task
        task.delay(contribution.key)
        logger.info(
            "pest_image_recognition_hook_dispatched",
            contribution_id=contribution.key,
            pest_key=contribution.pest_key,
            attachment_id=contribution.attachment_id,
            action="index_upsert" if promoted else "index_retract",
        )

    # --- global (cross-tenant) content for promoted images -----------

    def resolve_promoted_content(self, contribution_key: str) -> PestImageContent | None:
        """Resolve a *promoted* contribution to its attachment for global serving.

        Returns ``None`` when the contribution is missing, not promoted, or its
        attachment has vanished — the API maps every such case to 404 so a
        ``PRIVATE`` (or foreign-private) image can never be served globally.
        Attachment resolution uses the contribution's *owning* ``tenant_key``;
        no caller-tenant gate applies because ``PROMOTED`` is a global release.
        """
        from app.common.exceptions import AttachmentNotFoundError

        contribution = self._repo.get_by_key(contribution_key)
        if contribution is None or contribution.status != PestImageStatus.PROMOTED:
            return None
        try:
            attachment = self._attachments.get_attachment(contribution.attachment_id, contribution.tenant_key)
        except AttachmentNotFoundError:
            return None
        return PestImageContent(contribution=contribution, attachment=attachment)

    async def open_content_stream(self, content: PestImageContent) -> AsyncIterator[bytes]:
        """Proxy-stream the original bytes of a resolved promoted contribution."""
        return await self._attachments.open_stream(content.attachment)

    async def open_content_thumbnail_stream(self, content: PestImageContent, size: int) -> AsyncIterator[bytes]:
        """Proxy-stream a thumbnail rendition of a resolved promoted contribution.

        Raises ``NotFoundError`` (from the storage adapter) when the rendition
        has not been generated yet — the API translates that into the same
        lazy-regeneration 202 the tenant attachment endpoint uses.
        """
        return await self._attachments.open_thumbnail_stream(content.attachment, size)

    # --- DSGVO erasure (REQ-025) -------------------------------------

    async def delete_all_for_tenant(self, tenant_key: str) -> int:
        """Hard-delete every contribution + attachment of a tenant (erasure).

        The attachment bytes are removed via the tenant-scoped attachment
        service (idempotent); the link documents are then dropped in one AQL
        sweep. Returns the number of contributions removed.
        """
        contributions = self._repo.list_for_tenant(tenant_key)
        for c in contributions:
            await self._attachments.delete(c.attachment_id, tenant_key)
        removed = self._repo.delete_for_tenant(tenant_key)
        logger.info("pest_images_deleted_for_tenant", tenant_key=tenant_key, removed=removed)
        return removed

    async def delete_all_for_user(self, user_key: str) -> int:
        """Hard-delete every contribution + attachment a user authored (erasure).

        A user may have contributed across several tenants; each contribution's
        attachment is deleted against its own ``tenant_key`` and the link
        document is removed. Returns the number of contributions removed.
        """
        contributions = self._repo.list_for_user(user_key)
        for c in contributions:
            await self._attachments.delete(c.attachment_id, c.tenant_key)
            if c.key is not None:
                self._repo.delete(c.key, c.tenant_key)
        logger.info("pest_images_deleted_for_user", user_key=user_key, removed=len(contributions))
        return len(contributions)

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

    def _to_view(self, contribution: PestImageContribution, mime_type: str, *, is_own: bool = True) -> PestImageView:
        return PestImageView(
            contribution=contribution,
            mime_type=mime_type,
            has_thumbnail=can_render(mime_type),
            is_own=is_own,
        )


def _created_sort_key(view: PestImageView) -> str:
    """Stable, total-order sort key for mixed (possibly ``None``) ``created_at``.

    ``None`` sorts oldest (empty string < any ISO timestamp) so newest-first
    ordering places undated rows last without ever comparing ``None`` values.
    """
    created = view.contribution.created_at
    return created.isoformat() if created is not None else ""


def _normalize_caption(caption: str | None) -> str | None:
    if caption is None:
        return None
    trimmed = caption.strip()
    return trimmed or None


__all__ = [
    "GALLERY_THUMBNAIL_SIZE",
    "PestImageContent",
    "PestImageService",
    "PestImageView",
    "PestInspectionImageView",
    "PestRecognitionImageView",
]
