"""NFR-013 §4.2 — shared DTOs for the object-storage adapter contract.

These types are backend-neutral and shared by every ``IObjectStorageAdapter``
implementation (``local-fs``, ``s3``, ...). Keeping them in the domain layer
(rather than next to a concrete adapter) lets the service layer and both
adapters depend on the same definitions without importing a concrete adapter.
"""

from __future__ import annotations

from dataclasses import dataclass

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
    """NFR-013 §4.2 capability flags surfaced to the service layer.

    The S3 adapter advertises native support for every operation; the
    local-fs adapter reports ``False`` for pre-sign and server-side copy,
    which forces the service layer to fall back to a backend-proxy upload /
    stream-pipe copy (NFR-013 §4.2).
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


def local_fs_capabilities(max_object_size_bytes: int) -> StorageCapabilities:
    """Capabilities for the local-fs adapter.

    Pre-sign and server-side copy are not natively supported; the adapter
    emulates download/upload URLs via backend-signed token URLs and copies
    by streaming bytes (NFR-013 §4.2).
    """
    return StorageCapabilities(
        supports_presigned_upload=False,
        supports_presigned_download=False,
        supports_server_side_copy=False,
        supports_server_side_encryption=False,
        supports_versioning=False,
        supports_lifecycle_rules=False,
        max_object_size_bytes=max_object_size_bytes,
        requires_per_user_oauth=False,
    )
