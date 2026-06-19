"""NFR-013 §2.1 — object-storage adapter registry.

Unlike the identification/source registries (which register zero-arg adapter
instances), storage adapters need construction arguments (filesystem root,
S3 credentials, ...). The registry therefore registers a **factory** per
backend key. ``get_for_backend(backend_key)`` builds a configured instance
from ``settings``.

Registering an adapter is done with the ``@StorageAdapterRegistry.register``
decorator on a factory function whose name (or explicit key) is the backend
key. The factory receives an optional ``attachment_repo`` so the DI layer
(Lauf 2) can wire DSGVO erasure lookups.

Backend selection is config-driven (``STORAGE_BACKEND``); no service/API
change is required to switch.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.config.settings import settings
from app.domain.interfaces.object_storage_adapter import IObjectStorageAdapter

#: A factory takes an optional attachment repo and returns a configured adapter.
StorageAdapterFactory = Callable[[Any], IObjectStorageAdapter]


class StorageAdapterRegistry:
    """Registry of storage-adapter factories keyed by backend key."""

    _factories: dict[str, StorageAdapterFactory] = {}

    @classmethod
    def register(cls, backend_key: str) -> Callable[[StorageAdapterFactory], StorageAdapterFactory]:
        """Class decorator registering a factory under ``backend_key``."""

        def _decorator(factory: StorageAdapterFactory) -> StorageAdapterFactory:
            cls._factories[backend_key] = factory
            return factory

        return _decorator

    @classmethod
    def get_for_backend(
        cls,
        backend_key: str | None = None,
        attachment_repo: Any = None,
    ) -> IObjectStorageAdapter:
        """Build a configured adapter for ``backend_key`` (default: ``settings.storage_backend``)."""
        key = backend_key or settings.storage_backend
        factory = cls._factories.get(key)
        if factory is None:
            raise KeyError(f"Unknown storage backend '{key}'. Available: {sorted(cls._factories.keys())}")
        return factory(attachment_repo)

    @classmethod
    def all_keys(cls) -> list[str]:
        return list(cls._factories.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear all registered factories (for testing)."""
        cls._factories = {}


def _resolve_localfs_signing_secret() -> str:
    """local-fs signing secret with fallback chain (NFR-013 §4.1)."""
    return settings.storage_localfs_signing_secret or settings.jwt_secret_key or settings.fernet_key


@StorageAdapterRegistry.register("local-fs")
def _build_local_fs(attachment_repo: Any = None) -> IObjectStorageAdapter:
    from app.data_access.storage.local_fs_adapter import LocalFsStorageAdapter

    return LocalFsStorageAdapter(
        root=settings.storage_local_fs_root,
        public_base_url=settings.storage_local_fs_public_base_url,
        signing_secret=_resolve_localfs_signing_secret(),
        max_object_size_bytes=settings.storage_max_file_size_mb * 1024 * 1024,
        attachment_repo=attachment_repo,
    )


@StorageAdapterRegistry.register("s3")
def _build_s3(attachment_repo: Any = None) -> IObjectStorageAdapter:
    from app.data_access.storage.s3_adapter import S3StorageAdapter

    return S3StorageAdapter(
        endpoint_url=settings.storage_s3_endpoint_url,
        region=settings.storage_s3_region,
        bucket=settings.storage_s3_bucket,
        access_key_id=settings.storage_s3_access_key_id,
        secret_access_key=settings.storage_s3_secret_access_key,
        use_path_style=settings.storage_s3_use_path_style,
        kms_key_id=settings.storage_s3_kms_key_id or None,
        force_tls=settings.storage_s3_force_tls,
        attachment_repo=attachment_repo,
    )
