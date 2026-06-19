"""NFR-013 §4.2 — object-storage adapter interface.

``IObjectStorageAdapter`` is the abstraction the service/engine layer programs
against. Concrete adapters live in ``app/data_access/storage/`` (``local-fs``,
``s3``) and are resolved from configuration via the ``StorageAdapterRegistry``
(NFR-013 §2.1). Switching backends is a config change
(``STORAGE_BACKEND=local-fs|s3``); no service/API change.

All methods are ``async`` except ``presign_upload_url`` / ``presign_download_url``,
which are pure URL construction and therefore synchronous.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from app.domain.models.storage import ObjectMetadata, ObjectRef, StorageCapabilities


class IObjectStorageAdapter(ABC):
    """Backend-neutral object-storage contract (NFR-013 §4.2)."""

    @property
    @abstractmethod
    def capabilities(self) -> StorageCapabilities:
        """Capability flags for graceful service-layer degradation."""

    @abstractmethod
    async def put_object(
        self,
        key: str,
        stream: AsyncIterator[bytes],
        mime_type: str,
        metadata: dict[str, str] | None = None,
    ) -> ObjectRef:
        """Store an object from an async byte stream. Returns an ``ObjectRef``."""

    @abstractmethod
    async def get_object(self, key: str) -> AsyncIterator[bytes]:
        """Return an async iterator yielding the object's bytes."""

    @abstractmethod
    async def delete_object(self, key: str) -> None:
        """Delete a single object. Idempotent — deleting a missing key is a no-op."""

    @abstractmethod
    async def delete_prefix(self, prefix: str) -> int:
        """Recursively delete every object under ``prefix``. Returns the count deleted."""

    @abstractmethod
    async def list_objects(self, prefix: str, page_token: str | None = None) -> dict[str, Any]:
        """List objects under ``prefix``.

        Returns a dict with keys ``keys`` (list[str]) and ``next_page_token``
        (str | None) for pagination continuation.
        """

    @abstractmethod
    async def head_object(self, key: str) -> ObjectMetadata:
        """Return metadata for a single object. Raises ``NotFoundError`` if absent."""

    @abstractmethod
    def presign_upload_url(self, key: str, mime_type: str, ttl_seconds: int = 900) -> str:
        """Return a URL the client can ``PUT`` to directly (or a signed proxy URL)."""

    @abstractmethod
    def presign_download_url(
        self,
        key: str,
        ttl_seconds: int = 900,
        response_disposition: str | None = None,
        *,
        tenant_key: str | None = None,
        attachment_id: str | None = None,
    ) -> str:
        """Return a URL the client can ``GET`` directly (or a signed proxy URL).

        ``tenant_key`` / ``attachment_id`` bind a backend-signed token to a
        tenant + attachment so a self-contained token URL cannot be replayed to
        stream another tenant's object (SEC-001). Native-presign backends (S3)
        ignore these extra claims — the bucket path itself already carries the
        tenant prefix and the URL is server-side signed.
        """

    @abstractmethod
    async def copy_object(self, src_key: str, dst_key: str) -> None:
        """Copy an object server-side (or via stream-pipe when unsupported)."""

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Probe backend readiness. Returns a structured status dict."""

    @abstractmethod
    async def delete_for_user(self, tenant_key: str, user_key: str, scope: str) -> int:
        """REQ-025 erasure hook — delete every object owned by a user within ``scope``.

        Walks the attachments index for ``tenant_key + created_by == user_key``
        and deletes matching objects. Returns the number of objects deleted.
        """

    @abstractmethod
    async def strip_exif_for_user(self, tenant_key: str, user_key: str, scope: str) -> int:
        """REQ-025 erasure hook — strip EXIF metadata from a user's images within ``scope``.

        Returns the number of objects rewritten.
        """
