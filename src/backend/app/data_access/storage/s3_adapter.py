"""NFR-013 §2.1 / §4.2 — S3 / S3-compatible object-storage adapter.

Backend key: ``s3``. Works against any S3-compatible backend (AWS S3, MinIO,
Backblaze B2, Wasabi, Cloudflare R2, ...). Backend selection happens via
``STORAGE_BACKEND=s3`` and the ``STORAGE_S3_*`` env vars (NFR-013 §4.1).

boto3 is **synchronous**; every blocking call runs inside ``asyncio.to_thread``
so the adapter satisfies the async ``IObjectStorageAdapter`` contract without
blocking the event loop (no aiobotocore dependency required). boto3 is
imported lazily so the dependency only materializes when the s3 backend is
actually selected.

Server-side encryption is enabled automatically when ``kms_key_id`` is set
(``ServerSideEncryption=aws:kms``). ``force_tls`` blocks plain-HTTP endpoints
outside localhost (NFR-013 §4.1).
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

import structlog

from app.common.exceptions import NotFoundError
from app.domain.engines.storage.exif_stripper import (
    is_unsupported_photo_format,
    strip_exif,
)
from app.domain.interfaces.object_storage_adapter import IObjectStorageAdapter
from app.domain.models.storage import (
    S3_DEFAULT_CAPABILITIES,
    ObjectMetadata,
    ObjectRef,
    StorageCapabilities,
)

logger = structlog.get_logger()

BACKEND_KEY = "s3"

# Stream chunk size for get_object (256 KiB).
_CHUNK_SIZE = 256 * 1024


class S3StorageAdapter(IObjectStorageAdapter):
    """S3 / S3-compatible adapter (NFR-013 §4.2)."""

    def __init__(
        self,
        endpoint_url: str,
        region: str,
        bucket: str,
        access_key_id: str,
        secret_access_key: str,
        *,
        use_path_style: bool = False,
        kms_key_id: str | None = None,
        force_tls: bool = True,
        attachment_repo: Any = None,
    ) -> None:
        self._endpoint_url = endpoint_url
        self._region = region
        self._bucket = bucket
        self._access_key_id = access_key_id
        self._secret_access_key = secret_access_key
        self._use_path_style = use_path_style
        self._kms_key_id = kms_key_id or None
        self._force_tls = force_tls
        self._attachment_repo = attachment_repo
        if force_tls and endpoint_url.startswith("http://") and "localhost" not in endpoint_url:
            raise ValueError(
                "STORAGE_S3_FORCE_TLS=true blocks plain-HTTP endpoints outside localhost. "
                "Set STORAGE_S3_FORCE_TLS=false explicitly to opt in (NFR-013 §4.1)."
            )
        self._client: Any = None

    @property
    def capabilities(self) -> StorageCapabilities:
        return S3_DEFAULT_CAPABILITIES

    # --- boto3 client (lazy) -----------------------------------------

    def _get_client(self) -> Any:
        if self._client is None:
            import boto3
            from botocore.config import Config

            addressing = "path" if self._use_path_style else "auto"
            self._client = boto3.client(
                "s3",
                endpoint_url=self._endpoint_url or None,
                region_name=self._region or None,
                aws_access_key_id=self._access_key_id or None,
                aws_secret_access_key=self._secret_access_key or None,
                config=Config(s3={"addressing_style": addressing}),
            )
        return self._client

    def _encryption_args(self) -> dict[str, str]:
        if self._kms_key_id:
            return {"ServerSideEncryption": "aws:kms", "SSEKMSKeyId": self._kms_key_id}
        return {}

    # --- Sync boto3 primitives (run via to_thread) -------------------

    def _put_sync(self, key: str, data: bytes, mime_type: str, metadata: dict[str, str]) -> ObjectRef:
        client = self._get_client()
        kwargs: dict[str, Any] = {
            "Bucket": self._bucket,
            "Key": key,
            "Body": data,
            "ContentType": mime_type,
            "Metadata": metadata,
        }
        kwargs.update(self._encryption_args())
        response = client.put_object(**kwargs)
        etag = (response.get("ETag") or "").strip('"')
        return ObjectRef(key=key, etag=etag, size_bytes=len(data))

    def _get_sync(self, key: str) -> bytes:
        client = self._get_client()
        try:
            response = client.get_object(Bucket=self._bucket, Key=key)
        except client.exceptions.NoSuchKey as exc:
            raise NotFoundError("object", key) from exc
        return response["Body"].read()

    def _head_sync(self, key: str) -> ObjectMetadata:
        from botocore.exceptions import ClientError

        client = self._get_client()
        try:
            response = client.head_object(Bucket=self._bucket, Key=key)
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code")
            if code in ("404", "NoSuchKey", "NotFound"):
                raise NotFoundError("object", key) from exc
            raise
        last_modified = response.get("LastModified")
        return ObjectMetadata(
            key=key,
            size_bytes=response.get("ContentLength", 0),
            content_type=response.get("ContentType"),
            etag=(response.get("ETag") or "").strip('"'),
            last_modified=last_modified.isoformat() if last_modified is not None else None,
            user_metadata=response.get("Metadata", {}),
        )

    def _delete_sync(self, key: str) -> None:
        client = self._get_client()
        client.delete_object(Bucket=self._bucket, Key=key)

    def _delete_prefix_sync(self, prefix: str) -> int:
        client = self._get_client()
        paginator = client.get_paginator("list_objects_v2")
        deleted = 0
        for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
            objects = [{"Key": obj["Key"]} for obj in page.get("Contents", [])]
            if not objects:
                continue
            # S3 DeleteObjects caps at 1000 keys per request; a single page is
            # already <= 1000, so this is safe.
            client.delete_objects(Bucket=self._bucket, Delete={"Objects": objects})
            deleted += len(objects)
        return deleted

    def _list_sync(self, prefix: str, page_token: str | None) -> dict[str, Any]:
        client = self._get_client()
        kwargs: dict[str, Any] = {"Bucket": self._bucket, "Prefix": prefix}
        if page_token:
            kwargs["ContinuationToken"] = page_token
        response = client.list_objects_v2(**kwargs)
        keys = [obj["Key"] for obj in response.get("Contents", [])]
        next_token = response.get("NextContinuationToken") if response.get("IsTruncated") else None
        return {"keys": keys, "next_page_token": next_token}

    def _copy_sync(self, src_key: str, dst_key: str) -> None:
        client = self._get_client()
        kwargs: dict[str, Any] = {
            "Bucket": self._bucket,
            "Key": dst_key,
            "CopySource": {"Bucket": self._bucket, "Key": src_key},
        }
        kwargs.update(self._encryption_args())
        client.copy_object(**kwargs)

    def _health_sync(self) -> dict[str, Any]:
        from botocore.exceptions import BotoCoreError, ClientError

        client = self._get_client()
        try:
            client.head_bucket(Bucket=self._bucket)
            return {
                "backend": BACKEND_KEY,
                "endpoint_url": self._endpoint_url,
                "region": self._region,
                "bucket": self._bucket,
                "ready": True,
            }
        except (ClientError, BotoCoreError) as exc:
            return {
                "backend": BACKEND_KEY,
                "endpoint_url": self._endpoint_url,
                "region": self._region,
                "bucket": self._bucket,
                "ready": False,
                "reason": str(exc),
            }

    # --- IObjectStorageAdapter contract ------------------------------

    async def put_object(
        self,
        key: str,
        stream: AsyncIterator[bytes],
        mime_type: str,
        metadata: dict[str, str] | None = None,
    ) -> ObjectRef:
        chunks: list[bytes] = []
        async for chunk in stream:
            chunks.append(chunk)
        data = b"".join(chunks)
        ref = await asyncio.to_thread(self._put_sync, key, data, mime_type, metadata or {})
        logger.info("storage_put_object", backend=BACKEND_KEY, key=key, size_bytes=ref.size_bytes)
        return ref

    async def get_object(self, key: str) -> AsyncIterator[bytes]:
        data = await asyncio.to_thread(self._get_sync, key)

        async def _iter() -> AsyncIterator[bytes]:
            for i in range(0, len(data), _CHUNK_SIZE):
                yield data[i : i + _CHUNK_SIZE]

        return _iter()

    async def delete_object(self, key: str) -> None:
        await asyncio.to_thread(self._delete_sync, key)
        logger.info("storage_delete_object", backend=BACKEND_KEY, key=key)

    async def delete_prefix(self, prefix: str) -> int:
        # SEC-004 — mirror the local-fs guard: reject an empty / bare ``t/`` root
        # prefix before it reaches ``list_objects_v2(Prefix=...)``, where it
        # would match (and delete) every tenant's objects. Use the normalised
        # form so the prefix can never widen into a mass cross-tenant deletion.
        from app.data_access.storage.local_fs_adapter import _require_tenant_scoped_prefix

        normalized = _require_tenant_scoped_prefix(prefix)
        # Preserve the caller's trailing slash so the S3 listing stays scoped to
        # the tenant folder (``t/{key}/``) rather than sibling-key prefixes.
        safe_prefix = f"{normalized}/" if prefix.rstrip().endswith("/") else normalized
        count = await asyncio.to_thread(self._delete_prefix_sync, safe_prefix)
        logger.info("storage_delete_prefix", backend=BACKEND_KEY, prefix=safe_prefix, deleted=count)
        return count

    async def list_objects(self, prefix: str, page_token: str | None = None) -> dict[str, Any]:
        return await asyncio.to_thread(self._list_sync, prefix, page_token)

    async def head_object(self, key: str) -> ObjectMetadata:
        return await asyncio.to_thread(self._head_sync, key)

    def presign_upload_url(self, key: str, mime_type: str, ttl_seconds: int = 900) -> str:
        client = self._get_client()
        params: dict[str, Any] = {"Bucket": self._bucket, "Key": key, "ContentType": mime_type}
        if self._kms_key_id:
            params["ServerSideEncryption"] = "aws:kms"
            params["SSEKMSKeyId"] = self._kms_key_id
        return client.generate_presigned_url("put_object", Params=params, ExpiresIn=ttl_seconds)

    def presign_download_url(
        self,
        key: str,
        ttl_seconds: int = 900,
        response_disposition: str | None = None,
        *,
        tenant_key: str | None = None,
        attachment_id: str | None = None,
    ) -> str:
        # ``tenant_key`` / ``attachment_id`` are local-fs token claims; S3 native
        # presign signs the bucket key (which already carries the tenant prefix)
        # server-side, so the extra claims are intentionally ignored here.
        client = self._get_client()
        params: dict[str, Any] = {"Bucket": self._bucket, "Key": key}
        if response_disposition:
            params["ResponseContentDisposition"] = response_disposition
        return client.generate_presigned_url("get_object", Params=params, ExpiresIn=ttl_seconds)

    async def copy_object(self, src_key: str, dst_key: str) -> None:
        await asyncio.to_thread(self._copy_sync, src_key, dst_key)
        logger.info("storage_copy_object", backend=BACKEND_KEY, src=src_key, dst=dst_key)

    async def health_check(self) -> dict[str, Any]:
        return await asyncio.to_thread(self._health_sync)

    async def delete_for_user(self, tenant_key: str, user_key: str, scope: str) -> int:
        """REQ-025 erasure hook — delete every stored object owned by a user.

        Returns 0 until an attachment repository is wired (Lauf 2 DI provider).
        """
        if self._attachment_repo is None:
            return 0
        from app.data_access.storage.local_fs_adapter import _scope_to_categories

        categories = _scope_to_categories(scope)
        if categories is not None and not categories:
            return 0
        attachments = await asyncio.to_thread(self._attachment_repo.find_by_user, tenant_key, user_key, categories)
        deleted = 0
        for att in attachments:
            await self.delete_object(att.storage_key)
            deleted += 1
        logger.info(
            "storage_delete_for_user",
            backend=BACKEND_KEY,
            tenant_key=tenant_key,
            user_key=user_key,
            scope=scope,
            deleted=deleted,
        )
        return deleted

    async def strip_exif_for_user(self, tenant_key: str, user_key: str, scope: str) -> int:
        """REQ-025 erasure hook — strip EXIF from a user's images.

        HEIC/HEIF cannot be re-encoded without ``pillow-heif`` (SEC-005): such
        images are not stripped, counted as ``skipped_unsupported`` and logged
        per object (``exif_strip_unsupported_format``, mime type only) so the
        erasure audit surfaces the residual GPS/EXIF risk. Returns the number of
        images stripped.
        """
        if self._attachment_repo is None:
            return 0
        from app.data_access.storage.local_fs_adapter import _scope_to_categories

        categories = _scope_to_categories(scope)
        if categories is not None and not categories:
            return 0
        attachments = await asyncio.to_thread(self._attachment_repo.find_by_user, tenant_key, user_key, categories)
        rewritten = 0
        skipped_unsupported = 0
        for att in attachments:
            if not (att.mime_type or "").startswith("image/"):
                continue
            if is_unsupported_photo_format(att.mime_type):
                skipped_unsupported += 1
                logger.warning(
                    "exif_strip_unsupported_format",
                    backend=BACKEND_KEY,
                    tenant_key=tenant_key,
                    user_key=user_key,
                    mime_type=att.mime_type,
                )
                continue
            data = await asyncio.to_thread(self._get_sync, att.storage_key)
            stripped = await asyncio.to_thread(strip_exif, data, att.mime_type)
            await asyncio.to_thread(self._put_sync, att.storage_key, stripped, att.mime_type, {})
            rewritten += 1
        logger.info(
            "storage_strip_exif_for_user",
            backend=BACKEND_KEY,
            tenant_key=tenant_key,
            user_key=user_key,
            scope=scope,
            rewritten=rewritten,
            skipped_unsupported=skipped_unsupported,
        )
        return rewritten

    def set_attachment_repo(self, attachment_repo: Any) -> None:
        """Wire the attachments repository (used by the DI provider in Lauf 2)."""
        self._attachment_repo = attachment_repo
