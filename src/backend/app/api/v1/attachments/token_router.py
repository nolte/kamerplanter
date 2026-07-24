"""NFR-013 §4.2 — local-fs token-redemption endpoint.

When the storage backend cannot issue native presigned URLs (local-fs),
``presign_download_url`` returns a backend-signed token URL of the form
``{public_base_url}/{token}``. This router redeems that token: the token *is*
the authorization (no JWT / tenant context), so the handler verifies the HMAC
signature and embedded expiry, then streams the referenced object.

It is mounted **globally** (not tenant-scoped) at
``/api/v1/attachments/token/{token}`` so the signed URL is self-contained.

Presign-capable backends (S3) never route here — they redirect straight to the
object store — so a request reaching this endpoint with an S3 backend is simply
rejected as an invalid token.
"""

from __future__ import annotations

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Path
from fastapi.responses import StreamingResponse

from app.api.v1.attachments.response_headers import harden_download_headers
from app.common.dependencies import get_object_storage
from app.common.exceptions import InvalidTokenError, NotFoundError
from app.common.openapi_responses import UNAUTHORIZED_RESPONSE
from app.domain.interfaces.object_storage_adapter import IObjectStorageAdapter

logger = structlog.get_logger()

router = APIRouter(prefix="/attachments/token", tags=["attachments"], responses=UNAUTHORIZED_RESPONSE)


@router.get("/{token}")
async def redeem_token(
    token: Annotated[str, Path(description="Backend-signed download token to redeem.")],
    storage: IObjectStorageAdapter = Depends(get_object_storage),
):
    """Verify a local-fs signed download token and stream the object."""
    verify = getattr(storage, "verify_token", None)
    if verify is None:
        # Backend issues native presigned URLs; token redemption is not used.
        raise InvalidTokenError("download token")

    payload = verify(token)
    if payload is None or payload.get("op") != "download":
        raise InvalidTokenError("download token")

    key = payload.get("key")
    if not key:
        raise InvalidTokenError("download token")

    # SEC-001 — the token must be bound to a tenant whose prefix the storage key
    # actually lives under. A token forged/replayed for another tenant's key is
    # rejected even though the HMAC is valid for that tenant's secret.
    tenant_key = payload.get("tenant_key")
    if not tenant_key or not str(key).startswith(f"t/{tenant_key}/"):
        raise InvalidTokenError("download token")

    try:
        stream = await storage.get_object(key)
    except NotFoundError as exc:
        raise InvalidTokenError("download token") from exc

    # Audit the redemption with the tenant binding — never log the token itself.
    logger.info("attachment_token_download", tenant_key=tenant_key, attachment_id=payload.get("aid"))

    headers = {"Cache-Control": "private, max-age=86400"}
    disposition = payload.get("disposition")
    # Harden against content-sniffing / drive-by: force ``attachment`` for
    # non-image MIME types, always set ``X-Content-Type-Options: nosniff``
    # (SEC-009). ``mime_type`` is unknown here (no catalog lookup), so derive
    # safety from the requested disposition.
    headers = harden_download_headers(headers, mime_type=None, requested_disposition=disposition)
    return StreamingResponse(stream, headers=headers)
