"""NFR-013 §5.1 — attachment upload / serve / delete service.

The ``AttachmentService`` owns the upload pipeline and depends only on the
backend-neutral :class:`IObjectStorageAdapter`, the
:class:`IAttachmentRepository`, and the storage engines. Authentication and
authorization happen in the API layer; this service assumes the caller is
already authorized for ``tenant_key`` / ``user_key``.

Upload pipeline order (NFR-013 §5.1) — every guard runs *before* any bytes are
written, so a rejected upload never leaves orphan objects:

  1. Quota check ............ StorageQuotaExceededError (409)
  2. MIME whitelist ......... InvalidFileTypeError (415) — while EXIF
                              stripping is on, also for an image type the
                              strip cannot re-encode (HEIC/HEIF, GIF; #2139)
  3. Magic-byte validation .. InvalidFileTypeError (415)
     Pixel ceiling (images) .. ImagePixelLimitError (413) — from the header,
                               before anything is decoded (#2108)
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

import asyncio
import hashlib
import json
from collections.abc import AsyncIterator, Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast
from uuid import UUID

import httpx
import structlog
from pydantic import BaseModel

from app.common.enums import AttachmentCategory, CaptureDevice, EntitlementDimension
from app.common.exceptions import (
    ClientEventDeletedError,
    ClientEventMismatchError,
    DuplicateError,
    FileTooLargeError,
    InvalidFileTypeError,
    ValidationError,
    VirusScanRejectedError,
    WriteConflictError,
)
from app.common.image_bounds import STORED_IMAGE_MAX_PIXELS, image_dimensions
from app.common.log_privacy import log_subject, log_tenant
from app.common.url_safety import validate_server_side_url
from app.config.settings import Settings
from app.domain.engines.storage.exif_stripper import ExifStripper, is_strippable_format, strip_exif
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
from app.domain.interfaces.rendition_dispatch_claims import IRenditionDispatchClaims
from app.domain.interfaces.storage_release_retry_repository import IStorageReleaseRetryRepository
from app.domain.models.attachment import Attachment
from app.domain.models.client_event import (
    ClientEventStamp,
    client_event_digest,
    is_client_event_conflict,
    same_digest,
)
from app.domain.services.entitlement_service import EntitlementService

logger = structlog.get_logger()


@dataclass(frozen=True)
class UploadOutcome:
    """An upload with a ``client_event_id`` (REQ-053 WP 9.3): the record, and whether it was stored before."""

    attachment: Attachment
    replayed: bool = False
    #: ``True`` only for a record this upload wrote - not a replay, not the uploader's own record (#1770 dedup);
    #: what a caller feeds on (the DINOv2 reference, REQ-034 §4) happens once per record.
    created: bool = False
    #: What the caller's ``admit`` check answered (e.g. the plant whose gallery quota it checked); ``None`` when
    #: it did not run (a replay) or there was none.
    admitted: object = None


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


def accepted_mime_types(settings: Settings, category: str) -> list[str]:
    """The types this installation stores for *category*.

    The category whitelist, minus - while EXIF stripping is on - every image type the strip cannot re-encode
    (#2139): it would be stored with its EXIF/GPS block, whatever a per-category override admits. The upload
    pipeline and the tenant-archive import (#2715 item 3) both ask here, so neither admits what the other refuses.
    """
    allowed = settings.allowed_mime_types_for_category(category)
    if settings.storage_strip_exif:
        allowed = [m for m in allowed if not m.startswith("image/") or is_strippable_format(m)]
    return allowed


def stored_body(settings: Settings, data: bytes, mime_type: str, *, stripper: ExifStripper | None = None) -> bytes:
    """The bytes this installation stores for *data*: EXIF-stripped images unless ``STORAGE_STRIP_EXIF`` is off.

    Shared by the upload pipeline and the tenant-archive import (#2715 item 3), so an imported photo keeps no more
    metadata than an uploaded one. Raises ``ImagePixelLimitError`` above the decode ceiling (#2108).
    """
    if settings.storage_strip_exif and mime_type.startswith("image/"):
        return (stripper or ExifStripper()).strip(data, mime_type)
    return data


def imported_object_body(settings: Settings, data: bytes, mime_type: str) -> bytes:
    """The bytes a tenant-archive import stores for an object of *mime_type* (#2715 item 3 and its review).

    An archive object was **stored** by some installation, so it is judged like a stored object, not an upload:

    * a strippable image type (JPEG/PNG/WEBP) is stripped under the stored-object ceiling
      (``STORED_IMAGE_MAX_PIXELS``, 80 MPx - objects stored before #2108 were admitted under Pillow's defaults), and
      **strictly**: bytes that do not decode as the claimed format raise
      :class:`~app.domain.engines.storage.exif_stripper.UnreadableImageError`, never come back unstripped;
    * every other admitted type (a document, or an image type the strip cannot re-encode that the category's
      whitelist admits - HEIC/GIF stored before #2139) is kept as it is: the import does not refuse what the
      installation held lawfully before.

    With ``STORAGE_STRIP_EXIF`` off nothing is re-encoded, as for an upload.
    """
    if settings.storage_strip_exif and is_strippable_format(mime_type):
        return strip_exif(data, mime_type, max_pixels=STORED_IMAGE_MAX_PIXELS, strict=True)
    return data


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
        rendition_claims: IRenditionDispatchClaims | None = None,
        entitlements: EntitlementService | None = None,
        release_retries: IStorageReleaseRetryRepository | None = None,
    ) -> None:
        self._storage = storage
        self._repo = attachment_repo
        # #2630 — where a delete that failed after the record was gone is owed; ``None``: the failure propagates.
        self._release_retries = release_retries
        self._settings = settings
        # REQ-056 §7.4 (#2142) — the tenant's storage quota comes from its plan (``null`` = the instance
        # setting ``STORAGE_TENANT_QUOTA_MB``). ``get_attachment_service`` wires the plan resolution; a service
        # built without one holds every tenant to the instance setting of ``settings``, as before #2142.
        self._entitlements = entitlements or EntitlementService(plan_repo=None, tenant_repo=None, settings=settings)
        self._magic = magic_validator or MagicByteValidator()
        self._exif = exif_stripper or ExifStripper()
        self._thumbnails = thumbnail_generator or ThumbnailGenerator()
        self._keys = key_builder or StorageKeyBuilder()
        # #2108 — the thumbnail-dispatch claim. Production passes the shared
        # Valkey store (``get_attachment_service``); a service built without one
        # still dispatches at most once per attachment and window for its own
        # lifetime.
        if rendition_claims is None:
            from app.data_access.external.rendition_dispatch_claims import MemoryRenditionDispatchClaims

            rendition_claims = MemoryRenditionDispatchClaims()
        self._rendition_claims = rendition_claims

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
        reuse_own_record: bool = True,
    ) -> Attachment:
        """Run the full upload pipeline and return the persisted attachment.

        ``reuse_own_record=False`` gives this upload a record of its own even when
        the uploader already holds one for these bytes in this category — for a
        caller whose record's lifetime is one carrier's (a pest-image
        contribution deletes its attachment record when it is withdrawn, so two
        contributions of one photo must not share one record, #1770).
        """
        attachment, _created = await self._pipeline(
            tenant_key=tenant_key,
            user_key=user_key,
            data=data,
            mime_type=mime_type,
            original_filename=original_filename,
            category=category,
            capture_device=capture_device,
            reuse_own_record=reuse_own_record,
            stamp=None,
            sha256=None,
        )
        return attachment

    async def _pipeline(
        self,
        *,
        tenant_key: str,
        user_key: str,
        data: bytes,
        mime_type: str,
        original_filename: str,
        category: AttachmentCategory,
        capture_device: CaptureDevice,
        reuse_own_record: bool,
        stamp: ClientEventStamp | None,
        sha256: str | None,
    ) -> tuple[Attachment, bool]:
        """The upload pipeline; ``(record, created)`` - ``False`` when the #1770 dedup handed back an own record.

        ``stamp`` (REQ-053 WP 9.3) is stored on a record this upload creates; the unique index
        ``(tenant_key, client_event_id)`` then refuses a concurrent twin (:class:`DuplicateError`), and the twin's
        freshly written object is deleted again. ``sha256`` is the bytes' hash when the caller has it already.
        """
        mime_type = (mime_type or "").lower().strip()
        max_bytes = self._settings.storage_max_file_size_mb * 1024 * 1024

        # 1. Quota check (count + total bytes against the tenant quota).
        self._enforce_quota(tenant_key, incoming_bytes=len(data))

        # 2. MIME whitelist (category-resolved).
        allowed = self.accepted_mime_types(category.value)
        if mime_type not in allowed:
            raise InvalidFileTypeError(mime_type, allowed)

        # 3. Magic-byte validation (content must match declared MIME). Only the
        #    leading prefix is needed — passing a slice avoids decoding the whole
        #    body for text/csv sniffing (SEC-008).
        if not self._magic.is_valid(data[:_SNIFF_LEN], mime_type):
            raise InvalidFileTypeError(mime_type, allowed)

        #    Pixel ceiling (#2108): read from the header, before anything —
        #    the EXIF strip, the thumbnail task — decodes the image. Also when
        #    EXIF stripping is disabled: the thumbnail task decodes regardless.
        if mime_type.startswith("image/"):
            self._enforce_pixel_ceiling(data)

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
        sha256 = sha256 or hashlib.sha256(data).hexdigest()
        own = (
            self._repo.find_own_by_sha256(tenant_key=tenant_key, sha256=sha256, created_by=user_key, category=category)
            if reuse_own_record
            else None
        )
        if own is not None:
            logger.info(
                "attachment_deduplicated",
                tenant=log_tenant(tenant_key),
                attachment_id=own.key,
                category=category.value,
                byte_size=own.byte_size,
            )
            return own, False
        held = self._repo.find_by_sha256(tenant_key, sha256)
        # Only an object stored under the type this upload was validated as: the
        # linked record is served with the object's type, and the whitelist and
        # magic-byte check above ran for *this* category and type.
        if held is not None and held.mime_type == mime_type and await self._object_exists(held.storage_key):
            linked = await self._link_to_stored_object(
                held,
                tenant_key=tenant_key,
                user_key=user_key,
                data=data,
                original_filename=original_filename,
                category=category,
                capture_device=capture_device,
                stamp=stamp,
            )
            return linked, True

        # 7. EXIF strip for images (unless disabled).
        body = self.stored_body(data, mime_type)

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
            client_event_id=stamp.client_event_id if stamp else None,
            client_event_digest=stamp.digest if stamp else None,
            created_at=created_at,
        )
        try:
            created = self._repo.create(attachment)
        except DuplicateError, WriteConflictError:
            # A concurrent attempt of the same buffered upload won the unique index (WP 9.3): the object written
            # above belongs to no record. Remove it; the caller reads the winner.
            await self._delete_object_quietly(storage_key, tenant_key=tenant_key)
            raise

        # 10. Audit log — never log bytes / presign URLs / filename (NFR-013 §9.2).
        logger.info(
            "attachment_uploaded",
            tenant=log_tenant(tenant_key),
            subject=log_subject(user_key),
            attachment_id=created.key,
            category=category.value,
            byte_size=created.byte_size,
        )

        # 11. Trigger thumbnail generation (images only).
        if can_render(mime_type):
            self._dispatch_thumbnails(created)

        return created, True

    @staticmethod
    def _upload_stamp(
        client_event_id: UUID,
        *,
        user_key: str,
        sha256: str,
        category: AttachmentCategory,
        scope: Mapping[str, str] | None,
    ) -> ClientEventStamp:
        """The id and digest of a buffered upload: uploader, category, the bytes' hash and the carrier (``scope``)."""
        digest = client_event_digest(
            {"user": user_key, "category": category.value, "sha256": sha256, "scope": dict(scope or {})}
        )
        return ClientEventStamp(str(client_event_id), digest)

    def _replayed_upload(self, stamp: ClientEventStamp, *, tenant_key: str) -> Attachment | None:
        stored = self._repo.find_by_client_event_id(tenant_key=tenant_key, client_event_id=stamp.client_event_id)
        if stored is None:
            return None
        if not same_digest(stored.client_event_digest, stamp.digest):
            raise ClientEventMismatchError()
        return stored

    async def upload_once(
        self,
        *,
        tenant_key: str,
        user_key: str,
        data: bytes,
        mime_type: str,
        original_filename: str,
        category: AttachmentCategory,
        client_event_id: UUID | None,
        capture_device: CaptureDevice = CaptureDevice.UNKNOWN,
        scope: Mapping[str, str] | None = None,
        admit: Callable[[], object] | None = None,
    ) -> UploadOutcome:
        """:meth:`upload` with the replay rule of a buffered upload (REQ-053 WP 9.3).

        Without a ``client_event_id`` this is :meth:`upload`. With one, the record of an earlier attempt is answered
        (``replayed``) **before** ``admit`` runs - the caller's quota or gallery check, so a replay of a stored
        photo is answered even when the gallery is full by now. A deleted record's id answers 404
        ``client_event.deleted``. Otherwise the pipeline runs and stamps the id on the record it creates; a
        concurrent twin loses the unique index and answers the winner's record. When the #1770 dedup hands back the
        uploader's own record, a record without an id is stamped with this one, a record with this id is a replay.
        ``created`` is ``True`` only for a record this call wrote. 409 ``client_event.payload_mismatch`` when the id
        names other bytes, another category, another uploader or another carrier (``scope``).
        """
        sha256: str | None = None
        stamp: ClientEventStamp | None = None
        if client_event_id is not None:
            sha256 = hashlib.sha256(data).hexdigest()
            stamp = self._upload_stamp(
                client_event_id, user_key=user_key, sha256=sha256, category=category, scope=scope
            )
            stored = self._replayed_upload(stamp, tenant_key=tenant_key)
            if stored is not None:
                return UploadOutcome(stored, replayed=True)
            if self._repo.client_event_tombstones([stamp.client_event_id], tenant_key=tenant_key):
                raise ClientEventDeletedError()
        admitted = admit() if admit is not None else None
        try:
            attachment, created = await self._pipeline(
                tenant_key=tenant_key,
                user_key=user_key,
                data=data,
                mime_type=mime_type,
                original_filename=original_filename,
                category=category,
                capture_device=capture_device,
                reuse_own_record=True,
                stamp=stamp,
                sha256=sha256,
            )
        except DuplicateError as exc:
            if stamp is None or not is_client_event_conflict(exc.details):
                raise
            return self._lost_race(stamp, tenant_key=tenant_key, error=exc)
        except WriteConflictError as exc:
            if stamp is None:
                raise
            return self._lost_race(stamp, tenant_key=tenant_key, error=exc)
        if stamp is None or created:
            return UploadOutcome(attachment, created=created, admitted=admitted)
        return self._own_record_outcome(attachment, stamp, tenant_key=tenant_key)

    def _lost_race(self, stamp: ClientEventStamp, *, tenant_key: str, error: Exception) -> UploadOutcome:
        """A twin of this buffered upload stored first: answer its record (re-raise ``error`` if there is none)."""
        stored = self._replayed_upload(stamp, tenant_key=tenant_key)
        if stored is None:
            raise error
        logger.info("attachment_upload_replayed", tenant=log_tenant(tenant_key), attachment_id=stored.key)
        return UploadOutcome(stored, replayed=True)

    def _own_record_outcome(self, own: Attachment, stamp: ClientEventStamp, *, tenant_key: str) -> UploadOutcome:
        """The #1770 dedup handed back the uploader's own record for these bytes: stamp it, or read it as a replay."""
        if own.client_event_id == stamp.client_event_id:
            # A concurrent twin of this very upload created it a moment ago.
            if not same_digest(own.client_event_digest, stamp.digest):
                raise ClientEventMismatchError()
            return UploadOutcome(own, replayed=True)
        if own.client_event_id is None:
            try:
                stamped = self._repo.stamp_client_event(
                    own.key or "", tenant_key=tenant_key, client_event_id=stamp.client_event_id, digest=stamp.digest
                )
            except (DuplicateError, WriteConflictError) as exc:
                return self._lost_race(stamp, tenant_key=tenant_key, error=exc)
            if stamped:
                # Through the pydantic base (the call-graph sweep's blind-spot ceiling, #2039).
                record: BaseModel = own
                update = {"client_event_id": stamp.client_event_id, "client_event_digest": stamp.digest}
                return UploadOutcome(cast("Attachment", record.model_copy(update=update)))
            stored = self._replayed_upload(stamp, tenant_key=tenant_key)  # a twin stamped it first
            if stored is not None:
                return UploadOutcome(stored, replayed=True)
        # The record belongs to another buffered upload of the same bytes: answer it, keep its id.
        return UploadOutcome(own)

    async def _delete_object_quietly(self, storage_key: str, *, tenant_key: str) -> None:
        """Remove the object a refused record would have held, unless a record holds it after all (#1770).

        A failure is logged, never raised - the caller's error is the one to answer, and the orphan sweep is the
        backstop.
        """
        if self._repo.storage_keys_held_elsewhere(tenant_key=tenant_key, storage_keys=[storage_key], excluding=[]):
            return
        try:
            await self._storage.delete_object(storage_key)
        except Exception as exc:  # noqa: BLE001 - the caller's error is the one to answer
            logger.warning("attachment_orphan_delete_failed", error_type=type(exc).__name__)

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
        stamp: ClientEventStamp | None = None,
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
                client_event_id=stamp.client_event_id if stamp else None,
                client_event_digest=stamp.digest if stamp else None,
                created_at=created_at,
            )
        )
        restored = False
        if not await self._object_exists(held.storage_key):
            await self._storage.put_object(
                held.storage_key,
                _bytes_stream(self.stored_body(data, held.mime_type)),
                held.mime_type,
                metadata={"tenant_key": tenant_key, "category": category.value},
            )
            restored = True
        logger.info(
            "attachment_uploaded",
            tenant=log_tenant(tenant_key),
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
            self._dispatch_thumbnails(created)
        return created

    @staticmethod
    def _enforce_pixel_ceiling(data: bytes) -> None:
        """Raise ``ImagePixelLimitError`` (413) for an image above the decode ceiling.

        A header Pillow cannot read is left to the steps that follow: the EXIF
        strip passes such bytes through unchanged, as it did before #2108.
        """
        try:
            image_dimensions(data)
        except OSError, ValueError:
            return

    def accepted_mime_types(self, category: str) -> list[str]:
        """:func:`accepted_mime_types` under this service's settings."""
        return accepted_mime_types(self._settings, category)

    def stored_body(self, data: bytes, mime_type: str) -> bytes:
        """:func:`stored_body` under this service's settings and EXIF stripper."""
        return stored_body(self._settings, data, mime_type, stripper=self._exif)

    async def _object_exists(self, storage_key: str) -> bool:
        from app.common.exceptions import NotFoundError

        try:
            await self._storage.head_object(storage_key)
        except NotFoundError:
            return False
        return True

    def _enforce_quota(self, tenant_key: str, *, incoming_bytes: int) -> None:
        """409 ``STORAGE_QUOTA_EXCEEDED`` when the upload would take the tenant past its storage quota.

        The quota is the tenant's plan's (REQ-056 §7.2 ``storage_mb``); ``0`` = unlimited, and then no sum
        is read. Counted before the write, as before #2142.
        """
        self._entitlements.require(
            tenant_key,
            EntitlementDimension.STORAGE_MB,
            projected=lambda: self._repo.sum_bytes_by_tenant(tenant_key) + incoming_bytes,
        )

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

    def _dispatch_thumbnails(self, attachment: Attachment) -> None:
        self.request_thumbnails(attachment)

    def request_thumbnails(self, attachment: Attachment) -> bool:
        """Queue the renditions of *attachment* at most once per window (#2108).

        ``True`` when a rendition can still come (the caller answers 202),
        ``False`` when none ever will (404) — see
        :func:`app.tasks.storage_tasks.request_thumbnails`.
        """
        # Lazy import avoids a hard import cycle (tasks import dependencies which
        # import services) and keeps Celery optional at service-construction time.
        from app.tasks.storage_tasks import request_thumbnails

        return request_thumbnails(attachment, self._rendition_claims)

    # --- Serve -------------------------------------------------------

    def get_attachment(self, attachment_id: str, tenant_key: str) -> Attachment:
        """Return an attachment in ``tenant_key`` or raise ``AttachmentNotFoundError``."""
        from app.common.exceptions import AttachmentNotFoundError

        attachment = self._repo.get(attachment_id, tenant_key)
        if attachment is None:
            raise AttachmentNotFoundError(attachment_id)
        return attachment

    @staticmethod
    def in_own_namespace(attachment: Attachment) -> bool:
        """Whether the record's object lies under ``t/<its tenant>/`` (#2138 review SEC-004).

        Every key the service builds does (:class:`StorageKeyBuilder`). A record whose key points
        elsewhere — written by anything but this service, an import above all — must never serve,
        sign or delete another tenant's object.
        """
        tenant_key = attachment.tenant_key
        key = attachment.storage_key
        prefix = f"t/{tenant_key}/"
        return bool(tenant_key) and key.startswith(prefix) and ".." not in key[len(prefix) :].split("/")

    def _require_own_namespace(self, attachment: Attachment) -> Attachment:
        from app.common.exceptions import AttachmentNotFoundError

        if not self.in_own_namespace(attachment):
            logger.warning("attachment_outside_namespace", tenant=log_tenant(attachment.tenant_key))
            raise AttachmentNotFoundError(attachment.key or "")
        return attachment

    def get_download(self, attachment_id: str, tenant_key: str) -> DownloadTarget:
        """Resolve the serving strategy for a download.

        For presign-capable backends (S3) returns a ``redirect_url``; otherwise
        signals proxy-streaming (caller uses :meth:`open_stream`).
        """
        attachment = self._require_own_namespace(self.get_attachment(attachment_id, tenant_key))
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
        attachment = self._require_own_namespace(self.get_attachment(attachment_id, tenant_key))
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
        """Return an async byte iterator for proxy-streaming the object (only from the record's own namespace)."""
        self._require_own_namespace(attachment)
        return await self._storage.get_object(attachment.storage_key)

    async def open_thumbnail_stream(self, attachment: Attachment, size: int) -> AsyncIterator[bytes]:
        """Return a byte iterator for a thumbnail rendition.

        Raises ``NotFoundError`` (from the adapter) when the rendition does not
        exist yet — the API layer translates that into a lazy-regeneration 202.
        """
        self._require_own_namespace(attachment)
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
        if not self.in_own_namespace(attachment):
            # #2138 review SEC-004 — the record goes, an object outside its tenant's namespace stays.
            logger.warning("attachment_outside_namespace", tenant=log_tenant(tenant_key))
            return self._repo.delete(attachment_id, tenant_key)

        shared = attachment.storage_key in self._repo.storage_keys_held_elsewhere(
            tenant_key=tenant_key, storage_keys=[attachment.storage_key], excluding=[attachment_id]
        )
        if not shared:
            for key in self._object_keys(attachment):
                await self._storage.delete_object(key)

        deleted = self._repo.delete(attachment_id, tenant_key)
        if shared and attachment.storage_key not in self._repo.storage_keys_held_elsewhere(
            tenant_key=tenant_key, storage_keys=[attachment.storage_key], excluding=[]
        ):
            # The other holder went meanwhile — two deletes of an object's last two
            # records each saw the other one. Asked again once this record is gone,
            # at least one of them sees no holder, so the object does not outlive
            # every record (#1770 review SEC-001).
            shared = await self._release_object(attachment, tenant_key)
        logger.info(
            "attachment_deleted",
            tenant=log_tenant(tenant_key),
            attachment_id=attachment_id,
            category=attachment.category.value,
            shared_object_retained=shared,
        )
        return deleted

    async def delete_if_unreferenced(self, attachment_id: str, tenant_key: str) -> bool:
        """Delete the attachment unless a carrier still references it (a redacted care event let go of it, #2400).

        The reference scan is the one the task-photo route and the orphan sweep share (the tenant-scoped scan of
        :meth:`IAttachmentRepository.task_photo_delete_state`): a photo another task, plant gallery, diary entry,
        care event or site underlay still names stays — sha256 deduplication gives one stored object to several
        carriers, and deleting it would strand their references. Idempotent: an unknown id returns ``False``.

        **The record goes first, in the transaction of the scan** (:meth:`IAttachmentRepository.remove_if_unreferenced`,
        #2545): a separate scan and delete let a carrier written between them point at nothing. A write committed on
        the record while the remove is open makes it conflict (``WriteConflictError``), and the conflict does not say
        whether that writer names the record: a carrier binding it does (``set_site_underlay``), a writer that only
        updates it does not (``mark_renditions_failed``, #2630). **The remove is therefore tried once more**, in a
        fresh transaction whose scan sees the committed write: a carrier now naming the record keeps it (the scan
        answers ``None``), a writer that does not lets it go. Exactly two attempts, no loop; a second conflict (a
        writer still open, or a new one) keeps the picture — the safe direction — and logs
        ``attachment_delete_skipped_concurrent_write``.

        The stored object follows unless another record holds it; a storage call failing after the
        commit leaves an object no record holds — never a reference to a missing picture. That object is recorded
        as an owed release (#2630) and the reconciliation run deletes exactly it later, unless a record holds it
        again by then; the global ``STORAGE_RECONCILE_DELETE_ENABLED`` stays off.

        The repository calls are synchronous (python-arango) and run in a worker thread, off the event loop.
        """
        try:
            removed = await asyncio.to_thread(self._repo.remove_if_unreferenced, attachment_id, tenant_key)
        except WriteConflictError:
            # A committed rival write is read by the second transaction's scan, which decides (#2630); a rival
            # still open conflicts again and the picture stays.
            logger.info("attachment_delete_retried_after_conflict", tenant=log_tenant(tenant_key))
            try:
                removed = await asyncio.to_thread(self._repo.remove_if_unreferenced, attachment_id, tenant_key)
            except WriteConflictError:
                logger.info("attachment_delete_skipped_concurrent_write", tenant=log_tenant(tenant_key))
                return False
        if removed is None:
            return False
        shared = await self._release_object(removed, tenant_key)
        logger.info(
            "attachment_deleted",
            tenant=log_tenant(tenant_key),
            attachment_id=attachment_id,
            category=removed.category.value,
            shared_object_retained=shared,
        )
        return True

    async def _release_object(self, attachment: Attachment, tenant_key: str) -> bool:
        """Delete the stored object and renditions of an already removed record; ``True`` when they were kept.

        Kept while another record holds the object (#1770), asked after this record is gone so the last of two
        concurrent deletes sees no holder; never deleted outside the record's own namespace (#2138 SEC-004).
        """
        if not self.in_own_namespace(attachment):
            logger.warning("attachment_outside_namespace", tenant=log_tenant(tenant_key))
            return True
        held = await asyncio.to_thread(
            self._repo.storage_keys_held_elsewhere,
            tenant_key=tenant_key,
            storage_keys=[attachment.storage_key],
            excluding=[],
        )
        if attachment.storage_key in held:
            return True
        # The record was committed away before this runs, so a storage error can no longer roll anything back: the
        # object would stay with no record holding it (#2630). Every key is tried; each failed one is recorded as an
        # owed release, which the reconciliation run retries for exactly that object (operator decision 2026-11-09,
        # not the global ``STORAGE_RECONCILE_DELETE_ENABLED``). Without a retry store, or when recording fails too,
        # the error propagates as before.
        failed: list[str] = []
        error: Exception | None = None
        for key in self._object_keys(attachment):
            try:
                await self._storage.delete_object(key)
            except Exception as exc:  # noqa: BLE001 — every key is tried; the failures are owed below
                failed.append(key)
                error = error or exc
                # The exception type only: a storage error text embeds the object path (tenant).
                logger.warning("attachment_object_release_failed", error_type=type(exc).__name__)
        if error is None:
            return False
        if self._release_retries is None:
            raise error
        await asyncio.to_thread(self._release_retries.owe_release, tenant_key=tenant_key, object_keys=failed)
        logger.info("attachment_object_release_owed", tenant=log_tenant(tenant_key), objects=len(failed))
        return False

    def _object_keys(self, attachment: Attachment) -> list[str]:
        """The stored object of *attachment* and its renditions."""
        return [
            attachment.storage_key,
            *rendition_keys(attachment.storage_key, attachment.mime_type, self._thumbnails.sizes),
        ]

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
