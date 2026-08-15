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
  6. SHA-256 + dedup ........ returns existing attachment (no re-write)
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
from app.common.url_safety import validate_server_side_url
from app.config.settings import Settings
from app.domain.engines.storage.exif_stripper import ExifStripper
from app.domain.engines.storage.magic_byte_validator import _SNIFF_LEN, MagicByteValidator
from app.domain.engines.storage.storage_key_builder import StorageKeyBuilder
from app.domain.engines.storage.thumbnail_generator import (
    ThumbnailGenerator,
    can_render,
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

        # 6. SHA-256 + dedup.
        sha256 = hashlib.sha256(data).hexdigest()
        existing = self._repo.find_by_sha256(tenant_key, sha256)
        if existing is not None:
            logger.info(
                "attachment_deduplicated",
                tenant_key=tenant_key,
                attachment_id=existing.key,
                category=category.value,
                byte_size=existing.byte_size,
            )
            return existing

        # 7. EXIF strip for images (unless disabled).
        body = data
        if self._settings.storage_strip_exif and mime_type.startswith("image/"):
            body = self._exif.strip(data, mime_type)

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
            user_key=user_key,
            attachment_id=created.key,
            category=category.value,
            byte_size=created.byte_size,
        )

        # 11. Trigger thumbnail generation (images only).
        if can_render(mime_type):
            self._dispatch_thumbnails(created.key, tenant_key)

        return created

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
        """Delete an attachment, its thumbnails, and its catalog record.

        Idempotent: deleting an unknown id returns ``False`` without error.
        """
        attachment = self._repo.get(attachment_id, tenant_key)
        if attachment is None:
            return False

        await self._storage.delete_object(attachment.storage_key)
        if can_render(attachment.mime_type):
            for thumb in self._thumbnails.sizes:
                await self._storage.delete_object(thumbnail_key(attachment.storage_key, thumb))

        deleted = self._repo.delete(attachment_id, tenant_key)
        logger.info(
            "attachment_deleted",
            tenant_key=tenant_key,
            attachment_id=attachment_id,
            category=attachment.category.value,
        )
        return deleted

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
