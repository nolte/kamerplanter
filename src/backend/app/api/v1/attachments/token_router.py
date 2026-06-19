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

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.common.dependencies import get_object_storage
from app.common.exceptions import InvalidTokenError, NotFoundError
from app.domain.interfaces.object_storage_adapter import IObjectStorageAdapter

router = APIRouter(prefix="/attachments/token", tags=["attachments"])


@router.get("/{token}")
async def redeem_token(
    token: str,
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

    try:
        stream = await storage.get_object(key)
    except NotFoundError as exc:
        raise InvalidTokenError("download token") from exc

    headers = {"Cache-Control": "private, max-age=86400"}
    disposition = payload.get("disposition")
    if disposition:
        headers["Content-Disposition"] = disposition
    return StreamingResponse(stream, headers=headers)
