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


class TestSigningSecretResolution:
    """SEC-004 — the known jwt_secret_key default must never sign tokens."""

    def _resolve(self):
        import app.data_access.storage.registry as registry_module

        return registry_module._resolve_localfs_signing_secret()

    def test_explicit_signing_secret_is_used(self, monkeypatch):
        from app.config import settings as settings_module

        monkeypatch.setattr(settings_module.settings, "storage_localfs_signing_secret", "strong-explicit-secret")
        assert self._resolve() == "strong-explicit-secret"

    def test_known_default_jwt_secret_is_rejected_and_ephemeral_generated(self, monkeypatch):
        import app.data_access.storage.registry as registry_module
        from app.config import settings as settings_module

        known_default = "change-me-in-production-use-openssl-rand-hex-32"
        monkeypatch.setattr(settings_module.settings, "storage_localfs_signing_secret", "")
        monkeypatch.setattr(settings_module.settings, "jwt_secret_key", known_default)
        monkeypatch.setattr(settings_module.settings, "fernet_key", "")

        warnings: list[tuple] = []
        monkeypatch.setattr(
            registry_module.logger,
            "warning",
            lambda *a, **k: warnings.append((a, k)),
        )

        secret = self._resolve()
        # An ephemeral hex secret is generated, never the known default string.
        assert secret != known_default
        assert len(secret) == 64  # secrets.token_hex(32)
        # A warning was emitted, and it never contains the secret value.
        assert warnings
        assert all(known_default not in str(w) and secret not in str(w) for w in warnings)

    def test_empty_chain_generates_ephemeral_secret(self, monkeypatch):
        from app.config import settings as settings_module

        monkeypatch.setattr(settings_module.settings, "storage_localfs_signing_secret", "")
        monkeypatch.setattr(settings_module.settings, "jwt_secret_key", "")
        monkeypatch.setattr(settings_module.settings, "fernet_key", "")
        secret = self._resolve()
        assert len(secret) == 64

    def test_strong_jwt_secret_is_accepted(self, monkeypatch):
        from app.config import settings as settings_module

        monkeypatch.setattr(settings_module.settings, "storage_localfs_signing_secret", "")
        monkeypatch.setattr(settings_module.settings, "jwt_secret_key", "a-strong-non-default-jwt-secret")
        assert self._resolve() == "a-strong-non-default-jwt-secret"
