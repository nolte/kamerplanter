"""NFR-013 — tenant-scoped attachment endpoints.

Mounted under ``/api/v1/t/{tenant_slug}/attachments``. Every endpoint requires
tenant membership (``get_current_tenant``) and the RBAC action on the
``ATTACHMENT`` resource (REQ-024). Responses expose only ``attachment_id`` and
stable tenant-scoped URIs — never bucket / backend / storage-key details
(NFR-013 AC-04).

Security notes:

* ``presign-upload`` is intentionally disabled for ALL backends (SEC-003): a
  presigned PUT bypasses the server-side validation pipeline. Secure presigned
  upload would require a server-side post-upload validation step (S3 event →
  Celery re-validation) — tracked as follow-up work. Until then proxy upload is
  the only path.
* Uploads are read in bounded chunks with an early ``Content-Length`` reject so
  an oversized body never gets fully buffered into RAM (SEC-005).
* Download responses are hardened against MIME-sniffing / drive-by (SEC-009).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Query, Request, Response, UploadFile
from fastapi.responses import RedirectResponse, StreamingResponse

from app.api.v1.attachments.permissions import require_attachment_permission
from app.api.v1.attachments.response_headers import harden_download_headers
from app.api.v1.attachments.schemas import (
    AttachmentListResponse,
    AttachmentResponse,
    PresignDownloadResponse,
    PresignUploadRequest,
    PresignUploadResponse,
    ThumbnailUris,
)
from app.common.dependencies import get_attachment_service
from app.common.enums import AttachmentCategory
from app.common.exceptions import FileTooLargeError, InvalidFileTypeError, KamerplanterError, ValidationError
from app.common.pagination import PaginationParams, get_pagination
from app.core.permissions import Action
from app.domain.engines.storage.thumbnail_generator import THUMBNAIL_SIZES, can_render
from app.domain.models.attachment import Attachment
from app.domain.models.tenant_context import TenantContext
from app.domain.services.attachment_service import AttachmentService

router = APIRouter(prefix="/attachments", tags=["attachments"])

# Chunk size for the bounded streaming upload read (1 MiB).
_UPLOAD_CHUNK_SIZE = 1024 * 1024


def _parse_content_length(request: Request) -> int | None:
    """Return the request ``Content-Length`` as an int, or ``None`` if absent/invalid."""
    raw = request.headers.get("content-length")
    if raw is None or not raw.strip().isdigit():
        return None
    return int(raw)


async def _read_upload_bounded(file: UploadFile, max_bytes: int) -> bytes:
    """Read an ``UploadFile`` in bounded chunks, capping memory at ``max_bytes``.

    Raises ``FileTooLargeError`` as soon as the running byte count exceeds
    ``max_bytes`` — without buffering the rest of the body (SEC-005). Memory is
    therefore capped at ``max_bytes + one chunk``.
    """
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(_UPLOAD_CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise FileTooLargeError(max_bytes)
        chunks.append(chunk)
    return b"".join(chunks)


def _base_uri(tenant_slug: str, attachment_id: str) -> str:
    return f"/api/v1/t/{tenant_slug}/attachments/{attachment_id}"


def _to_response(attachment: Attachment, tenant_slug: str) -> AttachmentResponse:
    attachment_id = attachment.key or ""
    uri = _base_uri(tenant_slug, attachment_id)
    thumbnail_uris: ThumbnailUris | None = None
    if can_render(attachment.mime_type):
        small, medium, large = THUMBNAIL_SIZES
        thumbnail_uris = ThumbnailUris(
            small=f"{uri}/thumbnails/{small}",
            medium=f"{uri}/thumbnails/{medium}",
            large=f"{uri}/thumbnails/{large}",
        )
    return AttachmentResponse(
        attachment_id=attachment_id,
        category=attachment.category,
        mime_type=attachment.mime_type,
        byte_size=attachment.byte_size,
        original_filename=attachment.original_filename,
        uri=uri,
        thumbnail_uris=thumbnail_uris,
        created_at=attachment.created_at.isoformat() if attachment.created_at else None,
    )


def _parse_category(value: str) -> AttachmentCategory:
    try:
        return AttachmentCategory(value)
    except ValueError as exc:
        raise ValidationError(
            f"Unknown attachment category '{value}'.",
            details=[{"field": "category", "reason": "Unknown category.", "code": "INVALID_CATEGORY"}],
        ) from exc


@router.post("", response_model=AttachmentResponse, status_code=201)
async def upload_attachment(
    request: Request,
    file: UploadFile,
    category: str = Form(...),
    ctx: TenantContext = Depends(require_attachment_permission(Action.CREATE)),
    service: AttachmentService = Depends(get_attachment_service),
) -> AttachmentResponse:
    """Proxy-upload an attachment through the server-side validation pipeline."""
    parsed_category = _parse_category(category)
    mime_type = (file.content_type or "").lower().strip()
    if not mime_type:
        raise InvalidFileTypeError("", [])

    # SEC-005 — reject oversized uploads before reading the body into memory.
    max_bytes = service.max_upload_bytes()
    content_length = _parse_content_length(request)
    if content_length is not None and content_length > max_bytes:
        raise FileTooLargeError(max_bytes)
    # Defense in depth: stream the body in bounded chunks so a missing/forged
    # Content-Length cannot force the whole file into RAM before the size check.
    data = await _read_upload_bounded(file, max_bytes)

    attachment = await service.upload(
        tenant_key=ctx.tenant_key,
        user_key=ctx.user_key,
        data=data,
        mime_type=mime_type,
        original_filename=file.filename or "upload",
        category=parsed_category,
    )
    return _to_response(attachment, ctx.tenant_slug)


@router.post("/presign-upload", response_model=PresignUploadResponse)
def presign_upload(
    body: PresignUploadRequest,
    ctx: TenantContext = Depends(require_attachment_permission(Action.CREATE)),
    service: AttachmentService = Depends(get_attachment_service),
) -> PresignUploadResponse:
    """Presigned upload is deliberately not offered in B1 (SEC-003).

    A presigned PUT URL would let the client write arbitrary, unvalidated bytes
    straight into the bucket — bypassing the whole server-side pipeline
    (magic-byte, size, virus scan, EXIF strip). Until a server-side post-upload
    validation hook exists (S3 event → Celery re-validation; follow-up work),
    this endpoint returns 409 for ALL backends and the proxy upload
    (``POST /attachments``, full pipeline) is the only supported upload path —
    which NFR-013 explicitly defines as the safe fallback.
    """
    raise KamerplanterError(
        message="Presigned upload is not supported — use proxy upload (POST /attachments).",
        error_code="PRESIGN_UPLOAD_UNSUPPORTED",
        status_code=409,
    )


@router.get("", response_model=AttachmentListResponse)
def list_attachments(
    category: str | None = Query(default=None),
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(require_attachment_permission(Action.READ)),
    service: AttachmentService = Depends(get_attachment_service),
) -> AttachmentListResponse:
    """List the tenant's attachments, newest first, optionally filtered by category."""
    parsed_category = _parse_category(category) if category else None
    items, total = service.list(ctx.tenant_key, parsed_category, pagination.offset, pagination.limit)
    return AttachmentListResponse(
        items=[_to_response(a, ctx.tenant_slug) for a in items],
        total=total,
        offset=pagination.offset,
        limit=pagination.limit,
    )


@router.get("/{attachment_id}")
async def download_attachment(
    attachment_id: str,
    ctx: TenantContext = Depends(require_attachment_permission(Action.READ)),
    service: AttachmentService = Depends(get_attachment_service),
):
    """Serve the original object.

    Presign-capable backends (S3) 307-redirect to a short-lived signed URL;
    otherwise the object is proxy-streamed with a private cache header and an
    ETag (= content SHA-256).
    """
    target = service.get_download(attachment_id, ctx.tenant_key)
    if target.redirect_url is not None:
        return RedirectResponse(url=target.redirect_url, status_code=307)

    stream = await service.open_stream(target.attachment)
    headers = {
        "Cache-Control": "private, max-age=86400",
        "ETag": f'"{target.attachment.sha256}"',
    }
    # SEC-009 — nosniff always; non-image MIME types are forced to download.
    headers = harden_download_headers(headers, mime_type=target.attachment.mime_type)
    return StreamingResponse(stream, media_type=target.attachment.mime_type, headers=headers)


@router.get("/{attachment_id}/presign-download", response_model=PresignDownloadResponse)
def presign_download(
    attachment_id: str,
    ctx: TenantContext = Depends(require_attachment_permission(Action.READ)),
    service: AttachmentService = Depends(get_attachment_service),
) -> PresignDownloadResponse:
    """Return an explicit signed/token download URL for the original object."""
    url = service.presign_download(attachment_id, ctx.tenant_key)
    return PresignDownloadResponse(download_url=url or "")


@router.get("/{attachment_id}/thumbnails/{size}")
async def download_thumbnail(
    attachment_id: str,
    size: int,
    ctx: TenantContext = Depends(require_attachment_permission(Action.READ)),
    service: AttachmentService = Depends(get_attachment_service),
):
    """Serve a thumbnail rendition; lazily regenerates a missing rendition."""
    from app.common.exceptions import NotFoundError

    if size not in THUMBNAIL_SIZES:
        raise ValidationError(
            f"Unknown thumbnail size '{size}'. Allowed: {sorted(THUMBNAIL_SIZES)}.",
            details=[{"field": "size", "reason": "Unknown thumbnail size.", "code": "INVALID_THUMBNAIL_SIZE"}],
        )
    attachment = service.get_attachment(attachment_id, ctx.tenant_key)
    try:
        stream = await service.open_thumbnail_stream(attachment, size)
    except NotFoundError:
        # Lazy regeneration (NFR-013 §8.2): re-trigger the task and 202 the caller.
        if can_render(attachment.mime_type):
            from app.tasks.storage_tasks import generate_thumbnails

            generate_thumbnails.delay(attachment_id, ctx.tenant_key)
        return Response(status_code=202)
    headers = {"Cache-Control": "private, max-age=86400"}
    # Thumbnails are always image/webp — nosniff, inline allowed (SEC-009).
    headers = harden_download_headers(headers, mime_type="image/webp")
    return StreamingResponse(stream, media_type="image/webp", headers=headers)


@router.delete("/{attachment_id}", status_code=204)
async def delete_attachment(
    attachment_id: str,
    ctx: TenantContext = Depends(require_attachment_permission(Action.DELETE)),
    service: AttachmentService = Depends(get_attachment_service),
) -> Response:
    """Delete an attachment and its thumbnails (idempotent)."""
    await service.delete(attachment_id, ctx.tenant_key)
    return Response(status_code=204)
