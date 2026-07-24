"""REQ-010 — global (cross-tenant) content endpoint for promoted pest images.

User-contributed pest reference images are stored as tenant-private attachments.
Once a platform admin *promotes* a contribution it becomes globally visible:
this router streams its pixels to **any authenticated user**, regardless of
tenant membership.

Security model (PFLICHT):

* This router is mounted WITHOUT a ``/t/{slug}`` prefix and uses NO tenant
  permission gate — promotion *is* the authorization. It requires only an
  authenticated user (``get_current_user``).
* It serves bytes ONLY for contributions whose ``status == PROMOTED``. Anything
  else — unknown id, ``PRIVATE``, vanished attachment — resolves to 404, so a
  private (own or foreign) image can never leak through this path.
* Attachment bytes are resolved against the contribution's *owning* tenant, but
  the caller's tenant is irrelevant: a promoted image is a global release.

Download responses reuse the same SEC-009 hardening + lazy-thumbnail behaviour
as the tenant attachment endpoint.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response
from fastapi.responses import StreamingResponse

from app.api.v1.attachments.response_headers import harden_download_headers
from app.common.auth import get_current_user
from app.common.dependencies import get_pest_image_service
from app.common.exceptions import NotFoundError, ValidationError
from app.common.openapi_responses import AUTH_RESPONSES, NOT_FOUND_RESPONSE
from app.domain.engines.storage.thumbnail_generator import THUMBNAIL_SIZES, can_render
from app.domain.models.user import User
from app.domain.services.pest_image_service import PestImageService

router = APIRouter(prefix="/ipm/pest-images", tags=["ipm"], responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE})


@router.get("/{contribution_id}")
async def get_promoted_pest_image(
    contribution_id: Annotated[str, Path(description="Key of the promoted pest-image contribution.")],
    _user: User = Depends(get_current_user),
    service: PestImageService = Depends(get_pest_image_service),
):
    """Stream the original bytes of a globally-promoted pest image.

    404 for any non-promoted / unknown contribution (the global gate).
    """
    content = service.resolve_promoted_content(contribution_id)
    if content is None:
        raise NotFoundError("PestImageContribution", contribution_id)

    attachment = content.attachment
    stream = await service.open_content_stream(content)
    headers = {
        "Cache-Control": "public, max-age=86400",
        "ETag": f'"{attachment.sha256}"',
    }
    # SEC-009 — nosniff always; non-image MIME types are forced to download.
    headers = harden_download_headers(headers, mime_type=attachment.mime_type)
    return StreamingResponse(stream, media_type=attachment.mime_type, headers=headers)


@router.get("/{contribution_id}/thumbnails/{size}")
async def get_promoted_pest_image_thumbnail(
    contribution_id: Annotated[str, Path(description="Key of the promoted pest-image contribution.")],
    size: Annotated[int, Path(description="Requested thumbnail edge length in pixels.")],
    _user: User = Depends(get_current_user),
    service: PestImageService = Depends(get_pest_image_service),
):
    """Stream a thumbnail rendition of a globally-promoted pest image.

    404 for any non-promoted / unknown contribution; 202 + lazy regeneration
    when the rendition is not yet materialised.
    """
    if size not in THUMBNAIL_SIZES:
        raise ValidationError(
            f"Unknown thumbnail size '{size}'. Allowed: {sorted(THUMBNAIL_SIZES)}.",
            details=[{"field": "size", "reason": "Unknown thumbnail size.", "code": "INVALID_THUMBNAIL_SIZE"}],
        )

    content = service.resolve_promoted_content(contribution_id)
    if content is None:
        raise NotFoundError("PestImageContribution", contribution_id)

    attachment = content.attachment
    try:
        stream = await service.open_content_thumbnail_stream(content, size)
    except NotFoundError:
        # Lazy regeneration (NFR-013 §8.2): re-trigger the task and 202 the caller.
        if can_render(attachment.mime_type):
            from app.tasks.storage_tasks import generate_thumbnails

            generate_thumbnails.delay(attachment.key, content.contribution.tenant_key)
        return Response(status_code=202)

    headers = {"Cache-Control": "public, max-age=86400"}
    # Thumbnails are always image/webp — nosniff, inline allowed (SEC-009).
    headers = harden_download_headers(headers, mime_type="image/webp")
    return StreamingResponse(stream, media_type="image/webp", headers=headers)
