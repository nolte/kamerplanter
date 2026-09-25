"""NFR-013 §5.1 — attachment upload / serve / delete service.

The ``AttachmentService`` owns the upload pipeline and depends only on the
backend-neutral :class:`IObjectStorageAdapter`, the
:class:`IAttachmentRepository`, and the storage engines. Authentication and
authorization happen in the API layer; this service assumes the caller is
already authorized for ``tenant_key`` / ``user_key``.

Upload pipeline order (NFR-013 §5.1) — every guard runs *before* any bytes are
written, so a rejected upload never leaves orphan objects:

  1. Quota check ............ StorageQuotaExceededError (409)
  2. MIME whitelist ......... InvalidFileTypeError (415)
  3. Magic-byte validation .. InvalidFileTypeError (415)
  4. Size limit ............. FileTooLargeError (413)
  5. Optional virus scan .... VirusScanRejectedError (422)
  6. SHA-256 + dedup ........ the uploader's own record for these bytes is
                              returned; another uploader gets a record of their
                              own over the already-stored object (#1770)
  7. EXIF strip (images)
  8. Build key + put_object
  9. Persist metadata
 10. Audit log (structlog; never logs bytes / URLs / filenames — NFR-013 §9.2)
 11. Trigger thumbnail task (images only)
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx
import structlog

from app.common.enums import AttachmentCategory, CaptureDevice
from app.common.exceptions import (
    FileTooLargeError,
    InvalidFileTypeError,
    StorageQuotaExceededError,
    ValidationError,
    VirusScanRejectedError,
)
from app.common.log_privacy import log_subject
from app.common.url_safety import validate_server_side_url
from app.config.settings import Settings
from app.domain.engines.storage.exif_stripper import ExifStripper
from app.domain.engines.storage.magic_byte_validator import _SNIFF_LEN, MagicByteValidator
from app.domain.engines.storage.storage_key_builder import StorageKeyBuilder
from app.domain.engines.storage.thumbnail_generator import (
    ThumbnailGenerator,
    can_render,
    rendition_keys,
    thumbnail_key,
)
from app.domain.interfaces.attachment_repository import IAttachmentRepository
from app.domain.interfaces.object_storage_adapter import IObjectStorageAdapter
from app.domain.models.attachment import Attachment

logger = structlog.get_logger()


@dataclass(frozen=True)
class DownloadTarget:
    """Result of :meth:`AttachmentService.get_download`.

    Exactly one serving strategy is populated:

    - ``redirect_url`` set → the API should 307-redirect (presign-capable backend).
    - ``redirect_url`` ``None`` → the API should proxy-stream via ``attachment``.
    """

    attachment: Attachment
    redirect_url: str | None


async def _bytes_stream(data: bytes) -> AsyncIterator[bytes]:
    yield data


class AttachmentService:
    """Upload / serve / delete attachments (NFR-013 §5.1)."""

    def __init__(
        self,
        storage: IObjectStorageAdapter,
        attachment_repo: IAttachmentRepository,
        settings: Settings,
        *,
        magic_validator: MagicByteValidator | None = None,
        exif_stripper: ExifStripper | None = None,
        thumbnail_generator: ThumbnailGenerator | None = None,
        key_builder: StorageKeyBuilder | None = None,
    ) -> None:
        self._storage = storage
        self._repo = attachment_repo
        self._settings = settings
        self._magic = magic_validator or MagicByteValidator()
        self._exif = exif_stripper or ExifStripper()
        self._thumbnails = thumbnail_generator or ThumbnailGenerator()
        self._keys = key_builder or StorageKeyBuilder()

    # --- Upload ------------------------------------------------------

    def max_upload_bytes(self) -> int:
        """Configured maximum upload size in bytes (NFR-013 §5.2)."""
        return self._settings.storage_max_file_size_mb * 1024 * 1024

    async def upload(
        self,
        *,
        tenant_key: str,
        user_key: str,
        data: bytes,
        mime_type: str,
        original_filename: str,
        category: AttachmentCategory,
        capture_device: CaptureDevice = CaptureDevice.UNKNOWN,
    ) -> Attachment:
        """Run the full upload pipeline and return the persisted attachment."""
        mime_type = (mime_type or "").lower().strip()
        max_bytes = self._settings.storage_max_file_size_mb * 1024 * 1024

        # 1. Quota check (count + total bytes against the tenant quota).
        self._enforce_quota(tenant_key, incoming_bytes=len(data))

        # 2. MIME whitelist (category-resolved).
        allowed = self._settings.allowed_mime_types_for_category(category.value)
        if mime_type not in allowed:
            raise InvalidFileTypeError(mime_type, allowed)

        # 3. Magic-byte validation (content must match declared MIME). Only the
        #    leading prefix is needed — passing a slice avoids decoding the whole
        #    body for text/csv sniffing (SEC-008).
        if not self._magic.is_valid(data[:_SNIFF_LEN], mime_type):
            raise InvalidFileTypeError(mime_type, allowed)

        # 4. Size limit.
        if len(data) > max_bytes:
            raise FileTooLargeError(max_bytes)

        # 5. Optional virus scan.
        if self._settings.storage_virus_scan_enabled:
            await self._virus_scan(data)

        # 6. SHA-256 + dedup (#1770). Two halves, because a record is an owner's
        #    claim and the object is only bytes. Re-uploading returns the
        #    uploader's own record for this category; anyone else — another
        #    member, or the same member in a category with a different retention
        #    rule — gets a record of their own that shares the stored object.
        #    Erasure selects records by ``created_by`` and ``category``, and bytes
        #    go only when the last record holding them does.
        sha256 = hashlib.sha256(data).hexdigest()
        own = self._repo.find_own_by_sha256(
            tenant_key=tenant_key, sha256=sha256, created_by=user_key, category=category
        )
        if own is not None:
            logger.info(
                "attachment_deduplicated",
                tenant_key=tenant_key,
                attachment_id=own.key,
                category=category.value,
                byte_size=own.byte_size,
            )
            return own
        held = self._repo.find_by_sha256(tenant_key, sha256)
        if held is not None and await self._object_exists(held.storage_key):
            return await self._link_to_stored_object(
                held,
                tenant_key=tenant_key,
                user_key=user_key,
                data=data,
                original_filename=original_filename,
                category=category,
                capture_device=capture_device,
            )

        # 7. EXIF strip for images (unless disabled).
        body = self._stored_body(data, mime_type)

        # 8. Build key + write bytes.
        created_at = datetime.now(UTC)
        storage_key = self._keys.build(
            tenant_key=tenant_key,
            category=category,
            mime_type=mime_type,
            created_at=created_at,
        )
        await self._storage.put_object(
            storage_key,
            _bytes_stream(body),
            mime_type,
            metadata={"tenant_key": tenant_key, "category": category.value},
        )

        # 9. Persist metadata.
        attachment = Attachment(
            tenant_key=tenant_key,
            mime_type=mime_type,
            byte_size=len(body),
            sha256=sha256,
            original_filename=original_filename,
            created_by=user_key,
            category=category,
            storage_key=storage_key,
            # Client-declared provenance (#1137). Recorded at ingestion because
            # EXIF is stripped in step 5 — a device hint not captured here is gone.
            capture_device=capture_device,
            created_at=created_at,
        )
        created = self._repo.create(attachment)

        # 10. Audit log — never log bytes / presign URLs / filename (NFR-013 §9.2).
        logger.info(
            "attachment_uploaded",
            tenant_key=tenant_key,
            subject=log_subject(user_key),
            attachment_id=created.key,
            category=category.value,
            byte_size=created.byte_size,
        )

        # 11. Trigger thumbnail generation (images only).
        if can_render(mime_type):
            self._dispatch_thumbnails(created.key, tenant_key)

        return created

    async def _link_to_stored_object(
        self,
        held: Attachment,
        *,
        tenant_key: str,
        user_key: str,
        data: bytes,
        original_filename: str,
        category: AttachmentCategory,
        capture_device: CaptureDevice,
    ) -> Attachment:
        """Give *user_key* a record of their own over the object *held* points at (#1770).

        Nothing of the other record is copied but the object's own properties —
        its key, type and size. The filename, caption and provenance are this
        uploader's, so neither learns the other's.

        A delete of the last other record can race this: it checks for other
        holders, finds none, and removes the object while this record is being
        written. The object is therefore checked again after the record exists
        and, if it is gone, written back from this upload's bytes — the same
        bytes, hence the same object. What stays open is the delete that removes
        the object *after* that second check; its window is the one between two
        storage calls of the deleting request.
        """
        created_at = datetime.now(UTC)
        created = self._repo.create(
            Attachment(
                tenant_key=tenant_key,
                mime_type=held.mime_type,
                byte_size=held.byte_size,
                sha256=held.sha256,
                original_filename=original_filename,
                created_by=user_key,
                category=category,
                storage_key=held.storage_key,
                capture_device=capture_device,
                created_at=created_at,
            )
        )
        restored = False
        if not await self._object_exists(held.storage_key):
            await self._storage.put_object(
                held.storage_key,
                _bytes_stream(self._stored_body(data, held.mime_type)),
                held.mime_type,
                metadata={"tenant_key": tenant_key, "category": category.value},
            )
            restored = True
        logger.info(
            "attachment_uploaded",
            tenant_key=tenant_key,
            subject=log_subject(user_key),
            attachment_id=created.key,
            category=category.value,
            byte_size=created.byte_size,
            shared_object=True,
            restored_object=restored,
        )
        # The renditions belong to the object, which already has them (or whose
        # first record's task is rendering them). Only a restored object needs
        # new ones.
        if restored and can_render(held.mime_type):
            self._dispatch_thumbnails(created.key, tenant_key)
        return created

    def _stored_body(self, data: bytes, mime_type: str) -> bytes:
        """The bytes the pipeline stores for *data*: EXIF-stripped images unless disabled."""
        if self._settings.storage_strip_exif and mime_type.startswith("image/"):
            return self._exif.strip(data, mime_type)
        return data

    async def _object_exists(self, storage_key: str) -> bool:
        from app.common.exceptions import NotFoundError

        try:
            await self._storage.head_object(storage_key)
        except NotFoundError:
            return False
        return True

    def _enforce_quota(self, tenant_key: str, *, incoming_bytes: int) -> None:
        quota_mb = self._settings.storage_tenant_quota_mb
        if quota_mb <= 0:
            return
        quota_bytes = quota_mb * 1024 * 1024
        used = self._repo.sum_bytes_by_tenant(tenant_key)
        if used + incoming_bytes > quota_bytes:
            raise StorageQuotaExceededError(tenant_key, float(quota_mb))

    async def _virus_scan(self, data: bytes) -> None:
        """Scan ``data`` via the configured scanner — fail-closed (SEC-006).

        The endpoint is validated against SSRF (https + public address only,
        blocking the cloud metadata IP and private ranges) on every use. When
        scanning is enabled and the scanner is unreachable, errors out, or
        returns an oversized/malformed response, the upload is **rejected**
        rather than silently let through.
        """
        endpoint = self._settings.storage_virus_scan_endpoint
        if not endpoint:
            # Scanning is enabled (caller checked) but no endpoint is configured:
            # fail-closed — do not let unscanned bytes through.
            raise VirusScanRejectedError("virus scanner endpoint not configured")

        # SSRF guard — reject internal/metadata targets before dialing.
        try:
            validate_server_side_url(endpoint, field="storage_virus_scan_endpoint")
        except ValidationError as exc:
            logger.warning("virus_scan_endpoint_rejected", reason="ssrf_validation_failed")
            raise VirusScanRejectedError("virus scanner endpoint is not a safe URL") from exc

        # Cap the response body so a hostile/misbehaving scanner cannot exhaust
        # memory (1 MiB is ample for a JSON verdict).
        max_response_bytes = 1024 * 1024
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    endpoint,
                    content=data,
                    headers={"Content-Type": "application/octet-stream"},
                )
                response.raise_for_status()
                body = response.content[: max_response_bytes + 1]
            if len(body) > max_response_bytes:
                raise VirusScanRejectedError("virus scanner response too large")
            payload = json.loads(body.decode("utf-8"))
        except VirusScanRejectedError:
            raise
        except (httpx.HTTPError, ValueError, UnicodeDecodeError) as exc:
            logger.warning("virus_scan_unavailable", reason=type(exc).__name__)
            raise VirusScanRejectedError("virus scan could not be completed") from exc

        if not isinstance(payload, dict) or not payload.get("clean", False):
            finding = payload.get("finding", "malware detected") if isinstance(payload, dict) else "malware detected"
            raise VirusScanRejectedError(str(finding))

    def _dispatch_thumbnails(self, attachment_id: str | None, tenant_key: str) -> None:
        if not attachment_id:
            return
        # Lazy import avoids a hard import cycle (tasks import dependencies which
        # import services) and keeps Celery optional at service-construction time.
        from app.tasks.storage_tasks import generate_thumbnails

        generate_thumbnails.delay(attachment_id, tenant_key)

    # --- Serve -------------------------------------------------------

    def get_attachment(self, attachment_id: str, tenant_key: str) -> Attachment:
        """Return an attachment in ``tenant_key`` or raise ``AttachmentNotFoundError``."""
        from app.common.exceptions import AttachmentNotFoundError

        attachment = self._repo.get(attachment_id, tenant_key)
        if attachment is None:
            raise AttachmentNotFoundError(attachment_id)
        return attachment

    def get_download(self, attachment_id: str, tenant_key: str) -> DownloadTarget:
        """Resolve the serving strategy for a download.

        For presign-capable backends (S3) returns a ``redirect_url``; otherwise
        signals proxy-streaming (caller uses :meth:`open_stream`).
        """
        attachment = self.get_attachment(attachment_id, tenant_key)
        if self._storage.capabilities.supports_presigned_download:
            url = self._storage.presign_download_url(
                attachment.storage_key,
                ttl_seconds=self._settings.storage_presign_ttl_seconds,
                response_disposition=f'inline; filename="{attachment_id}"',
                tenant_key=tenant_key,
                attachment_id=attachment_id,
            )
            return DownloadTarget(attachment=attachment, redirect_url=url)
        return DownloadTarget(attachment=attachment, redirect_url=None)

    def presign_download(self, attachment_id: str, tenant_key: str) -> str | None:
        """Return an explicit presign/token download URL, or ``None`` if unsupported."""
        attachment = self.get_attachment(attachment_id, tenant_key)
        # local-fs reports supports_presigned_download=False but still emits a
        # usable signed token URL — surface it so the FE has a direct link. The
        # token is bound to its tenant + attachment (SEC-001).
        return self._storage.presign_download_url(
            attachment.storage_key,
            ttl_seconds=self._settings.storage_presign_ttl_seconds,
            response_disposition=f'inline; filename="{attachment_id}"',
            tenant_key=tenant_key,
            attachment_id=attachment_id,
        )

    def presign_upload(self, tenant_key: str, category: AttachmentCategory, mime_type: str) -> str | None:
        """Return a presign upload URL when the backend supports it, else ``None``.

        Note: a presigned upload bypasses the server-side validation pipeline,
        so only presign-capable backends (S3) advertise it. local-fs returns
        ``None`` and the caller must use the proxy upload endpoint.
        """
        if not self._storage.capabilities.supports_presigned_upload:
            return None
        mime_type = (mime_type or "").lower().strip()
        allowed = self._settings.allowed_mime_types_for_category(category.value)
        if mime_type not in allowed:
            raise InvalidFileTypeError(mime_type, allowed)
        storage_key = self._keys.build(tenant_key=tenant_key, category=category, mime_type=mime_type)
        return self._storage.presign_upload_url(
            storage_key,
            mime_type,
            ttl_seconds=self._settings.storage_presign_ttl_seconds,
        )

    async def open_stream(self, attachment: Attachment) -> AsyncIterator[bytes]:
        """Return an async byte iterator for proxy-streaming the object."""
        return await self._storage.get_object(attachment.storage_key)

    async def open_thumbnail_stream(self, attachment: Attachment, size: int) -> AsyncIterator[bytes]:
        """Return a byte iterator for a thumbnail rendition.

        Raises ``NotFoundError`` (from the adapter) when the rendition does not
        exist yet — the API layer translates that into a lazy-regeneration 202.
        """
        key = thumbnail_key(attachment.storage_key, size)
        return await self._storage.get_object(key)

    def supports_presigned_download(self) -> bool:
        """Whether the configured backend can issue presigned download URLs."""
        return self._storage.capabilities.supports_presigned_download

    # --- Delete ------------------------------------------------------

    async def delete(self, attachment_id: str, tenant_key: str) -> bool:
        """Delete an attachment record, and its object and thumbnails when nothing else holds them.

        Deduplicated uploads share one stored object between the records of
        several uploaders (#1770). Deleting one record — a contribution withdrawn,
        a staged task photo removed, an orphan swept — removes that record only
        while another still points at the object; the object and its renditions
        go with the last record. The object is deleted before the record, so a
        failed storage call leaves the record for a retry.

        Idempotent: deleting an unknown id returns ``False`` without error.
        """
        attachment = self._repo.get(attachment_id, tenant_key)
        if attachment is None:
            return False

        shared = attachment.storage_key in self._repo.storage_keys_held_elsewhere(
            tenant_key=tenant_key, storage_keys=[attachment.storage_key], excluding=[attachment_id]
        )
        if not shared:
            await self._storage.delete_object(attachment.storage_key)
            for rendition in rendition_keys(attachment.storage_key, attachment.mime_type, self._thumbnails.sizes):
                await self._storage.delete_object(rendition)

        deleted = self._repo.delete(attachment_id, tenant_key)
        logger.info(
            "attachment_deleted",
            tenant_key=tenant_key,
            attachment_id=attachment_id,
            category=attachment.category.value,
            shared_object_retained=shared,
        )
        return deleted

    def deletable_from_task(
        self, attachment_id: str, task_key: str, tenant_key: str, *, actor_key: str, is_lead: bool
    ) -> bool:
        """Whether this task's photo route may destroy *attachment_id* (#1393).

        Two questions, because one does not cover both photos this route sees.

        **Is it shared?** One record can be referenced from several tasks, plant
        galleries and diary entries (a re-upload returns the uploader's own record;
        records written before #1770 were shared across uploaders too), so "it is a task photo and no
        *task* links it" — which this route used to ask — cheerfully destroyed a
        gallery's cover. Anything referencing it other than the named task refuses.

        **Does the task key in the path mean anything?** For a photo the named task
        references, yes: it is that task's documentation, and whoever may delete the
        tenant's attachments may delete it. For a *staged* photo it does not. A
        staged upload is in no ``photo_refs`` at all until completion writes it
        (#1388), so the first question is vacuously satisfied for it through **any**
        task key of the tenant — one the caller has no involvement with, one another
        member is filling in right now. The path segment reads like a scope and was
        not one.

        So a photo nothing references belongs to whoever uploaded it, and only they
        may destroy it through this route. That is the staging area's own owner, and
        it is the same person the control is rendered for: ``PhotoUpload`` shows the
        remove button only for ids staged in the current session. A lead who genuinely
        needs to remove someone else's attachment has ``DELETE /attachments/{id}``.

        **Which role reaches which half.** The route admits anyone who may *create* an
        attachment — lead and grower — and the split lives here instead. Growers are
        the role that completes tasks and uploads the photos, and gating the whole
        route on ``ATTACHMENT``/``DELETE`` meant a grower's remove button removed the
        photo from their form and left the stored object behind for ever: the leak
        #1393 exists to close, on its most common path, with the sweep that would
        collect it shipped disabled. Undoing one's own not-yet-submitted upload is not
        the irreversible destruction of a record that REQ-024 §1a.1 reserves to leads,
        and the ``"task"`` branch above keeps that reservation exactly where it is.

        A second member staging the *same bytes* gets a record of their own
        (#1770), so their remove button removes their record; the stored object
        stays for as long as the first member's record holds it
        (:meth:`delete`).
        """
        # One repository call, not three. The two questions differ only in whether the
        # named task counts as a reference, and asking them separately re-ran the whole
        # nine-collection scan for each — inside an interactive request.
        state, created_by = self._repo.task_photo_delete_state(attachment_id, tenant_key, task_key=task_key)
        if state == "task":
            # The task's completion record. REQ-024 §1a.1 makes destroying a record the
            # irreversibility boundary, so this half stays lead-only.
            return is_lead
        if state == "staged":
            # Not a record yet: nothing references it, and abandoning the form leaves
            # it for the orphan sweep. Withdrawing it is the undo of the CREATE the
            # uploader was already permitted to make, so their own role does not need
            # to reach further than that — but it must be *their* upload.
            return created_by == actor_key
        # "shared" — another carrier holds it — or "missing". No role overrides this:
        # sha256 deduplication means destroying it would strand a reference elsewhere.
        return False

    # --- List --------------------------------------------------------

    def list(
        self,
        tenant_key: str,
        category: AttachmentCategory | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Attachment], int]:
        """Return a paginated, newest-first attachment listing for the tenant."""
        return self._repo.list_by_tenant(tenant_key, category, offset, limit)


__all__ = ["AttachmentService", "DownloadTarget"]
