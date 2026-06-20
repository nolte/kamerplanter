"""API tests for the NFR-013 storage admin settings endpoints.

Covers:
  * ``PUT /admin/settings/storage`` persists only non-secret fields.
  * ``GET /admin/settings`` embeds the storage block and NEVER leaks secrets.
  * ``POST /admin/settings/storage/test`` calls the adapter ``health_check``.
  * ``require_platform_admin`` gates write/test/delete (full mode rejects a
    non-admin; light mode lets the anonymous system user through).
  * An unknown backend yields HTTP 422 (no persistence).
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.admin.settings.router import router as settings_router
from app.common import auth as auth_mod
from app.common.auth import get_current_user, require_platform_admin
from app.common.dependencies import get_system_settings_service
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError
from app.domain.models.system_settings import StorageSettings, SystemSettings
from app.domain.services.system_settings_service import SystemSettingsService


def _set_storage_env_defaults(env: MagicMock) -> None:
    env.storage_backend = "local-fs"
    env.storage_local_fs_root = "/data/attachments"
    env.storage_local_fs_public_base_url = ""
    env.storage_s3_endpoint_url = ""
    env.storage_s3_region = ""
    env.storage_s3_bucket = ""
    # A configured S3 secret in env — must never appear in any response.
    env.storage_s3_access_key_id = "AKIAEXAMPLEKEY"
    env.storage_s3_secret_access_key = "super-secret-s3-value-XYZ"
    env.storage_s3_use_path_style = False
    env.storage_s3_kms_key_id = ""
    env.storage_s3_force_tls = True
    # HA + plantnet bits the shared response builder also reads.
    env.plantnet_api_key = ""
    env.ha_url = ""
    env.ha_access_token = ""
    env.ha_timeout = 10


def _admin_user() -> SimpleNamespace:
    return SimpleNamespace(key="user_admin")


def _service(stored: SystemSettings | None = None) -> tuple[SystemSettingsService, MagicMock]:
    repo = MagicMock()
    repo.get.return_value = stored if stored is not None else SystemSettings()
    repo.upsert.side_effect = lambda s: s
    return SystemSettingsService(repo), repo


def _build_app(service: SystemSettingsService) -> FastAPI:
    app = FastAPI()
    app.include_router(settings_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[get_system_settings_service] = lambda: service
    # Bypass the membership lookup — the gating itself is covered separately.
    app.dependency_overrides[require_platform_admin] = _admin_user
    # The shared GET endpoint uses get_current_user; stub it so no header is needed.
    app.dependency_overrides[get_current_user] = _admin_user
    return app


def test_get_settings_includes_storage_without_secret_leak():
    service, _repo = _service()
    with patch("app.domain.services.system_settings_service.env_settings") as env:
        _set_storage_env_defaults(env)
        client = TestClient(_build_app(service))
        resp = client.get("/api/v1/admin/settings")
    assert resp.status_code == 200
    storage = resp.json()["storage"]
    assert storage["backend"] == "local-fs"
    # Credential VALUES must never be present anywhere in the payload.
    assert "AKIAEXAMPLEKEY" not in resp.text
    assert "super-secret-s3-value-XYZ" not in resp.text
    # Only presence flags are exposed.
    assert storage["s3_access_key_id_configured"] is True
    assert storage["s3_secret_access_key_configured"] is True
    assert "s3_access_key_id" not in storage
    assert "s3_secret_access_key" not in storage


def test_put_persists_non_secret_fields():
    service, repo = _service()
    with patch("app.domain.services.system_settings_service.env_settings") as env:
        _set_storage_env_defaults(env)
        client = TestClient(_build_app(service))
        resp = client.put(
            "/api/v1/admin/settings/storage",
            json={
                "backend": "s3",
                "s3_endpoint_url": "https://s3.eu-central-1.amazonaws.com",
                "s3_region": "eu-central-1",
                "s3_bucket": "kamerplanter-prod",
                "s3_use_path_style": False,
            },
        )
    assert resp.status_code == 200
    repo.upsert.assert_called_once()
    upserted = repo.upsert.call_args[0][0]
    assert upserted.storage.backend == "s3"
    assert upserted.storage.s3_bucket == "kamerplanter-prod"
    assert upserted.storage.s3_region == "eu-central-1"


def test_put_rejects_secret_fields_in_payload():
    """The update schema has no credential fields → extra keys are ignored."""
    service, repo = _service()
    with patch("app.domain.services.system_settings_service.env_settings") as env:
        _set_storage_env_defaults(env)
        client = TestClient(_build_app(service))
        resp = client.put(
            "/api/v1/admin/settings/storage",
            json={"backend": "s3", "s3_access_key_id": "HACK", "s3_secret_access_key": "HACK2"},
        )
    assert resp.status_code == 200
    upserted = repo.upsert.call_args[0][0]
    # Secret fields are NOT modelled, so they cannot have been persisted.
    assert not hasattr(upserted.storage, "s3_access_key_id")
    assert "HACK" not in resp.text


def test_put_unknown_backend_returns_422():
    service, repo = _service()
    with patch("app.domain.services.system_settings_service.env_settings") as env:
        _set_storage_env_defaults(env)
        client = TestClient(_build_app(service))
        resp = client.put("/api/v1/admin/settings/storage", json={"backend": "gdrive"})
    # Literal type rejects the value at the schema layer → 422, nothing persisted.
    assert resp.status_code == 422
    repo.upsert.assert_not_called()


def test_test_endpoint_calls_health_check_local_fs():
    service, _repo = _service()
    fake_adapter = MagicMock()
    fake_adapter.health_check = AsyncMock(return_value={"backend": "local-fs", "ready": True})
    with (
        patch("app.domain.services.system_settings_service.env_settings") as env,
        patch("app.api.v1.admin.settings.router.build_storage_test_adapter", return_value=fake_adapter) as builder,
    ):
        _set_storage_env_defaults(env)
        client = TestClient(_build_app(service))
        resp = client.post("/api/v1/admin/settings/storage/test", json={"backend": "local-fs"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["backend"] == "local-fs"
    assert body["writable"] is True
    fake_adapter.health_check.assert_awaited_once()
    # The builder receives the layered config, never a credential field.
    config = builder.call_args[0][0]
    assert "s3_secret_access_key" not in config


def test_test_endpoint_reports_failure_without_leaking_internals():
    service, _repo = _service()
    with (
        patch("app.domain.services.system_settings_service.env_settings") as env,
        patch(
            "app.api.v1.admin.settings.router.build_storage_test_adapter",
            side_effect=RuntimeError("boto3 NoCredentialsError: AKIAEXAMPLEKEY rejected"),
        ),
    ):
        _set_storage_env_defaults(env)
        client = TestClient(_build_app(service))
        resp = client.post("/api/v1/admin/settings/storage/test", json={"backend": "s3"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is False
    # The raw exception (which could carry a key) must never reach the client.
    assert "AKIAEXAMPLEKEY" not in resp.text
    assert "boto3" not in resp.text


def test_delete_resets_storage_override():
    stored = SystemSettings(storage=StorageSettings(backend="s3", s3_bucket="old"))
    service, repo = _service(stored)
    with patch("app.domain.services.system_settings_service.env_settings") as env:
        _set_storage_env_defaults(env)
        client = TestClient(_build_app(service))
        resp = client.delete("/api/v1/admin/settings/storage")
    assert resp.status_code == 204
    upserted = repo.upsert.call_args[0][0]
    assert upserted.storage.backend is None
    assert upserted.storage.s3_bucket is None


# ── require_platform_admin gating (no override) ─────────────────────────


def _build_app_with_real_gating(service: SystemSettingsService, tenant_service: MagicMock) -> FastAPI:
    from app.common.dependencies import get_tenant_service

    app = FastAPI()
    app.include_router(settings_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[get_system_settings_service] = lambda: service
    app.dependency_overrides[get_current_user] = _admin_user
    app.dependency_overrides[get_tenant_service] = lambda: tenant_service
    return app


def test_put_requires_platform_admin_full_mode(monkeypatch):
    monkeypatch.setattr(auth_mod.settings, "kamerplanter_mode", "full")
    service, repo = _service()
    tenant_service = MagicMock()
    tenant_service.get_membership.return_value = SimpleNamespace(role=TenantRole.GROWER, is_active=True)
    with patch("app.domain.services.system_settings_service.env_settings") as env:
        _set_storage_env_defaults(env)
        client = TestClient(_build_app_with_real_gating(service, tenant_service))
        resp = client.put("/api/v1/admin/settings/storage", json={"backend": "s3"})
    assert resp.status_code == 403
    repo.upsert.assert_not_called()


def test_put_allows_system_user_in_light_mode(monkeypatch):
    monkeypatch.setattr(auth_mod.settings, "kamerplanter_mode", "light")
    service, repo = _service()
    tenant_service = MagicMock()
    with patch("app.domain.services.system_settings_service.env_settings") as env:
        _set_storage_env_defaults(env)
        client = TestClient(_build_app_with_real_gating(service, tenant_service))
        resp = client.put("/api/v1/admin/settings/storage", json={"backend": "local-fs"})
    assert resp.status_code == 200
    # Light mode must not consult tenant memberships at all.
    tenant_service.get_membership.assert_not_called()
    repo.upsert.assert_called_once()


@pytest.mark.parametrize("path", ["/api/v1/admin/settings/storage"])
def test_test_requires_platform_admin_full_mode(monkeypatch, path):
    monkeypatch.setattr(auth_mod.settings, "kamerplanter_mode", "full")
    service, _repo = _service()
    tenant_service = MagicMock()
    tenant_service.get_membership.return_value = None
    with patch("app.domain.services.system_settings_service.env_settings") as env:
        _set_storage_env_defaults(env)
        client = TestClient(_build_app_with_real_gating(service, tenant_service))
        resp = client.post(f"{path}/test", json={"backend": "local-fs"})
    assert resp.status_code == 403
