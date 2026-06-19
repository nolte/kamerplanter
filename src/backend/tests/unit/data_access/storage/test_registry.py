"""NFR-013 §2.1 — storage adapter registry resolution."""

import importlib

import pytest

from app.data_access.storage.local_fs_adapter import LocalFsStorageAdapter
from app.data_access.storage.s3_adapter import S3StorageAdapter


@pytest.fixture
def registry():
    """Re-import the registry module so its factory registrations are present."""
    import app.data_access.storage.registry as registry_module

    importlib.reload(registry_module)
    return registry_module.StorageAdapterRegistry


class TestStorageAdapterRegistry:
    def test_builds_local_fs_adapter(self, registry, monkeypatch):
        from app.config import settings as settings_module

        monkeypatch.setattr(settings_module.settings, "storage_local_fs_root", "/tmp/kp-test-attachments")
        monkeypatch.setattr(settings_module.settings, "storage_localfs_signing_secret", "secret")
        adapter = registry.get_for_backend("local-fs")
        assert isinstance(adapter, LocalFsStorageAdapter)

    def test_builds_s3_adapter(self, registry, monkeypatch):
        from app.config import settings as settings_module

        monkeypatch.setattr(settings_module.settings, "storage_s3_bucket", "bk")
        monkeypatch.setattr(settings_module.settings, "storage_s3_force_tls", False)
        adapter = registry.get_for_backend("s3")
        assert isinstance(adapter, S3StorageAdapter)

    def test_unknown_backend_raises(self, registry):
        with pytest.raises(KeyError, match="Unknown storage backend"):
            registry.get_for_backend("does-not-exist")

    def test_all_keys_contains_both_backends(self, registry):
        keys = registry.all_keys()
        assert "local-fs" in keys
        assert "s3" in keys

    def test_default_backend_from_settings(self, registry, monkeypatch):
        from app.config import settings as settings_module

        monkeypatch.setattr(settings_module.settings, "storage_backend", "local-fs")
        monkeypatch.setattr(settings_module.settings, "storage_localfs_signing_secret", "secret")
        adapter = registry.get_for_backend()
        assert isinstance(adapter, LocalFsStorageAdapter)
