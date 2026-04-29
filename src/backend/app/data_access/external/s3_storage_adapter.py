"""NFR-013 S3 / S3-compatible object-storage adapter (scaffolding).

Implements the storage adapter contract from NFR-013 §4.2 against any
S3-compatible backend: AWS S3, MinIO, Backblaze B2, Wasabi, Cloudflare
R2, etc. Backend selection happens via ``STORAGE_BACKEND=s3`` and the
``STORAGE_S3_*`` env vars (see NFR-013 §4.1).

This module is intentionally split into:

- ``S3StorageAdapter`` — concrete adapter that delegates to ``aiobotocore``
  via lazy import. boto3 / aiobotocore are not in the base requirements
  yet; the dependency lands the first time this adapter is actually
  instantiated in a deployment that selects the s3 backend. Until then
  the adapter is importable but raises a clear error on use.
- ``StorageCapabilities`` — capability flags surfaced to the service
  layer (NFR-013 §4.2).
- ``ObjectRef`` / ``ObjectMetadata`` — DTOs.

Out of scope (follow-up PRs):

- Pre-sign URL generation with KMS / SSE config.
- ``delete_for_user`` + ``strip_exif_for_user`` — depend on the
  ``attachments`` repository which is not yet wired up.
- ClamAV virus-scan integration (``STORAGE_VIRUS_SCAN_*`` env vars).
- Helm values for ``storage.s3.*`` (NFR-013 §4.1).

The adapter explicitly conforms to the NFR-013 §4.2 method names so a
service layer written against ``IObjectStorageAdapter`` can swap between
s3 and the (not yet implemented) ``local-fs`` adapter without changes.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel


@dataclass(frozen=True)
class ObjectRef:
    """Lightweight handle returned by ``put_object``."""

    key: str
    etag: str
    size_bytes: int


@dataclass(frozen=True)
class ObjectMetadata:
    """Metadata payload returned by ``head_object``."""

    key: str
    size_bytes: int
    content_type: str | None
    etag: str
    last_modified: str | None
    user_metadata: dict[str, str]


class StorageCapabilities(BaseModel):
    """NFR-013 §4.2 capability flags.

    The S3 adapter advertises native support for every operation; the
    local-fs adapter (see follow-up) reports ``False`` for pre-sign and
    server-side copy, which forces the service layer to fall back to a
    backend-proxy upload / stream-pipe copy.
    """

    supports_presigned_upload: bool
    supports_presigned_download: bool
    supports_server_side_copy: bool
    supports_server_side_encryption: bool
    supports_versioning: bool
    supports_lifecycle_rules: bool
    max_object_size_bytes: int
    requires_per_user_oauth: bool


S3_DEFAULT_CAPABILITIES = StorageCapabilities(
    supports_presigned_upload=True,
    supports_presigned_download=True,
    supports_server_side_copy=True,
    supports_server_side_encryption=True,
    supports_versioning=True,
    supports_lifecycle_rules=True,
    max_object_size_bytes=5 * 1024 * 1024 * 1024,  # 5 GiB single PUT (S3 limit)
    requires_per_user_oauth=False,
)


class S3StorageAdapter:
    """S3 / S3-compatible adapter (scaffolding).

    The methods below match the NFR-013 §4.2 contract. Each one defers to
    a lazily-imported ``aiobotocore`` session so the dependency only
    materialises when an environment actually selects ``STORAGE_BACKEND=s3``.
    The full method bodies will land in the follow-up that wires the
    attachments repository, virus-scan hook, and Helm values.
    """

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
    ) -> None:
        self._endpoint_url = endpoint_url
        self._region = region
        self._bucket = bucket
        self._access_key_id = access_key_id
        self._secret_access_key = secret_access_key
        self._use_path_style = use_path_style
        self._kms_key_id = kms_key_id
        self._force_tls = force_tls
        if force_tls and endpoint_url.startswith("http://") and "localhost" not in endpoint_url:
            raise ValueError(
                "STORAGE_S3_FORCE_TLS=true blocks plain-HTTP endpoints outside localhost. "
                "Set STORAGE_S3_FORCE_TLS=false explicitly to opt in (NFR-013 §4.1)."
            )

    @property
    def capabilities(self) -> StorageCapabilities:
        return S3_DEFAULT_CAPABILITIES

    # --- Adapter contract (NFR-013 §4.2) -----------------------------

    async def put_object(
        self,
        key: str,
        stream: AsyncIterator[bytes],
        mime_type: str,
        metadata: dict[str, str] | None = None,
    ) -> ObjectRef:
        raise NotImplementedError(
            "S3StorageAdapter.put_object — body lands with REQ-025 export upload PR; see NFR-013 §4.2 for the contract."
        )

    async def get_object(self, key: str) -> AsyncIterator[bytes]:
        raise NotImplementedError("S3StorageAdapter.get_object — pending REQ-025 download PR.")

    async def delete_object(self, key: str) -> None:
        raise NotImplementedError("S3StorageAdapter.delete_object — pending NFR-013 cleanup PR.")

    async def delete_prefix(self, prefix: str) -> int:
        raise NotImplementedError("S3StorageAdapter.delete_prefix — pending NFR-013 cleanup PR.")

    async def list_objects(self, prefix: str, page_token: str | None = None) -> dict[str, Any]:
        raise NotImplementedError("S3StorageAdapter.list_objects — pending follow-up.")

    async def head_object(self, key: str) -> ObjectMetadata:
        raise NotImplementedError("S3StorageAdapter.head_object — pending follow-up.")

    def presign_upload_url(self, key: str, mime_type: str, ttl_seconds: int = 900) -> str:
        raise NotImplementedError("S3StorageAdapter.presign_upload_url — pending follow-up.")

    def presign_download_url(
        self,
        key: str,
        ttl_seconds: int = 900,
        response_disposition: str | None = None,
    ) -> str:
        raise NotImplementedError("S3StorageAdapter.presign_download_url — pending follow-up.")

    async def copy_object(self, src_key: str, dst_key: str) -> None:
        raise NotImplementedError("S3StorageAdapter.copy_object — pending follow-up.")

    async def health_check(self) -> dict[str, Any]:
        """Probe the bucket. Returns a structured status dict."""
        return {
            "backend": "s3",
            "endpoint_url": self._endpoint_url,
            "region": self._region,
            "bucket": self._bucket,
            "ready": False,
            "reason": "scaffolding — aiobotocore not wired yet (NFR-013 follow-up)",
        }

    async def delete_for_user(self, tenant_key: str, user_key: str, scope: str) -> int:
        """REQ-025 erasure hook — see NFR-013 §4.2 W-007.

        Walks the attachments index for ``tenant_key + created_by == user_key``
        and deletes objects matching ``scope``. Bound to the attachments
        repository wiring in the REQ-025 frontend follow-up; returns 0
        until then.
        """
        return 0

    async def strip_exif_for_user(self, tenant_key: str, user_key: str, scope: str) -> int:
        """REQ-025 erasure hook — see NFR-013 §4.2 W-007.

        Removes EXIF GPS / serial / timestamp from every image whose
        attachment metadata matches the given ``tenant_key`` +
        ``user_key``. Stubbed until the attachments repo wiring lands.
        """
        return 0
