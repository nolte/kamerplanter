"""API tests for the REQ-046 central weather-provider admin endpoints.

Covers:
  * ``GET /admin/weather-providers`` returns the masked effective config — no
    plaintext / ciphertext of the global OWM key, only ``*_set`` presence.
  * ``PUT`` encrypts a new global key and preserves the stored ciphertext on an
    empty / masked value; an unknown default source → 422.
  * ``POST /{source_name}/test`` returns ``reachable`` on success and an error
    (never a 500) on a broken provider.
  * ``require_platform_admin`` gates read/write/test (full mode rejects a
    non-admin; light mode lets the anonymous system user through).
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from app.api.v1.admin.weather_providers.router import router as weather_router
from app.common import auth as auth_mod
from app.common.auth import require_platform_admin
from app.common.dependencies import get_weather_settings_service
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler, validation_error_handler
from app.common.exceptions import KamerplanterError
from app.domain.engines.encryption_engine import EncryptionEngine
from app.domain.models.system_settings import SystemSettings, WeatherProviderSettings
from app.domain.services.weather_settings_service import WeatherSettingsService


def _set_env(env: MagicMock) -> None:
    env.open_meteo_enabled = True
    env.open_meteo_base_url = "https://env.open-meteo/v1"
    env.dwd_enabled = True
    env.dwd_base_url = "https://env.dwd"
    env.openweathermap_enabled = True
    env.openweathermap_base_url = "https://env.owm"
    env.weather_fetch_timeout_s = 20
    env.weather_default_public_source = "open-meteo"


def _admin_user() -> SimpleNamespace:
    return SimpleNamespace(key="user_admin")


def _service(stored: SystemSettings | None = None, *, engine: EncryptionEngine | None = None):
    repo = MagicMock()
    repo.get.return_value = stored
    repo.upsert.side_effect = lambda s: s
    eng = engine or EncryptionEngine(Fernet.generate_key().decode())
    return WeatherSettingsService(repo, eng), repo


def _build_app(service: WeatherSettingsService) -> FastAPI:
    app = FastAPI()
    app.include_router(weather_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[get_weather_settings_service] = lambda: service
    app.dependency_overrides[require_platform_admin] = _admin_user
    return app


def _patch_env():
    return patch("app.domain.services.weather_settings_service.env_settings")


def test_get_masks_global_key_and_reports_presence():
    engine = EncryptionEngine(Fernet.generate_key().decode())
    cipher = engine.encrypt("global-secret")
    stored = SystemSettings(
        weather_providers=WeatherProviderSettings(openweathermap_global_api_key_encrypted=cipher),
    )
    service, _ = _service(stored=stored, engine=engine)
    with _patch_env() as env:
        _set_env(env)
        client = TestClient(_build_app(service))
        resp = client.get("/api/v1/admin/weather-providers")
    assert resp.status_code == 200
    body = resp.json()
    # Neither the plaintext nor the stored ciphertext of the global key leaks.
    assert "global-secret" not in resp.text
    assert cipher not in resp.text
    assert body["openweathermap_global_api_key_set"] is True
    names = {p["source_name"] for p in body["providers"]}
    assert names == {"open-meteo", "dwd", "openweathermap"}
    # Attribution is surfaced per provider.
    owm = next(p for p in body["providers"] if p["source_name"] == "openweathermap")
    assert owm["attribution"]


def test_get_reports_absent_global_key():
    service, _ = _service(stored=None)
    with _patch_env() as env:
        _set_env(env)
        client = TestClient(_build_app(service))
        resp = client.get("/api/v1/admin/weather-providers")
    assert resp.status_code == 200
    body = resp.json()
    assert body["openweathermap_global_api_key_set"] is False
    assert body["default_public_source"] == "open-meteo"


def test_put_encrypts_new_global_key():
    engine = EncryptionEngine(Fernet.generate_key().decode())
    service, repo = _service(stored=None, engine=engine)
    with _patch_env() as env:
        _set_env(env)
        client = TestClient(_build_app(service))
        resp = client.put(
            "/api/v1/admin/weather-providers",
            json={"openweathermap_global_api_key": "fresh-key", "dwd_enabled": False},
        )
    assert resp.status_code == 200
    upserted = repo.upsert.call_args[0][0]
    cipher = upserted.weather_providers.openweathermap_global_api_key_encrypted
    assert cipher != "fresh-key"
    assert engine.decrypt(cipher) == "fresh-key"
    assert upserted.weather_providers.dwd_enabled is False
    # The response never echoes the plaintext key.
    assert "fresh-key" not in resp.text


def test_put_masked_key_keeps_existing_ciphertext():
    stored = SystemSettings(
        weather_providers=WeatherProviderSettings(openweathermap_global_api_key_encrypted="stored-cipher"),
    )
    service, repo = _service(stored=stored)
    with _patch_env() as env:
        _set_env(env)
        client = TestClient(_build_app(service))
        resp = client.put(
            "/api/v1/admin/weather-providers",
            # Public IP literal → passes the SSRF guard offline (no DNS needed).
            json={"openweathermap_global_api_key": "••••", "open_meteo_base_url": "https://8.8.8.8/v1"},
        )
    assert resp.status_code == 200
    upserted = repo.upsert.call_args[0][0]
    assert upserted.weather_providers.openweathermap_global_api_key_encrypted == "stored-cipher"
    assert upserted.weather_providers.open_meteo_base_url == "https://8.8.8.8/v1"


def test_put_rejects_ssrf_base_url():
    # SEC-W1: an operator-set base_url that resolves to an internal / metadata
    # address must be rejected (422) before persistence.
    service, repo = _service(stored=None)
    with _patch_env() as env:
        _set_env(env)
        client = TestClient(_build_app(service))
        resp = client.put(
            "/api/v1/admin/weather-providers",
            json={"dwd_base_url": "https://169.254.169.254/latest/meta-data"},
        )
    assert resp.status_code == 422
    repo.upsert.assert_not_called()


def test_put_unknown_default_source_returns_422():
    service, repo = _service(stored=None)
    with _patch_env() as env:
        _set_env(env)
        client = TestClient(_build_app(service))
        resp = client.put("/api/v1/admin/weather-providers", json={"default_public_source": "gdrive"})
    # Literal type rejects the value at the schema layer → 422, nothing persisted.
    assert resp.status_code == 422
    repo.upsert.assert_not_called()


def test_put_rejects_extra_fields():
    service, repo = _service(stored=None)
    with _patch_env() as env:
        _set_env(env)
        client = TestClient(_build_app(service))
        resp = client.put(
            "/api/v1/admin/weather-providers",
            json={"openweathermap_global_api_key_encrypted": "smuggled"},
        )
    assert resp.status_code == 422
    repo.upsert.assert_not_called()


def test_test_endpoint_reachable():
    service, _ = _service(stored=None)
    fake_result = SimpleNamespace(reachable=True, preview=[], error=None)
    with (
        _patch_env() as env,
        patch.object(service, "test_provider", new=AsyncMock(return_value=fake_result)),
    ):
        _set_env(env)
        client = TestClient(_build_app(service))
        resp = client.post("/api/v1/admin/weather-providers/open-meteo/test")
    assert resp.status_code == 200
    assert resp.json()["reachable"] is True


def test_test_endpoint_broken_provider_no_500():
    service, _ = _service(stored=None)
    fake_result = SimpleNamespace(reachable=False, preview=[], error="Source did not return any data.")
    with (
        _patch_env() as env,
        patch.object(service, "test_provider", new=AsyncMock(return_value=fake_result)),
    ):
        _set_env(env)
        client = TestClient(_build_app(service))
        resp = client.post("/api/v1/admin/weather-providers/dwd/test")
    assert resp.status_code == 200
    body = resp.json()
    assert body["reachable"] is False
    assert body["error"]


# ── require_platform_admin gating (no override) ─────────────────────────


def _build_app_with_real_gating(service: WeatherSettingsService, tenant_service: MagicMock) -> FastAPI:
    from app.common.auth import get_current_user
    from app.common.dependencies import get_tenant_service

    app = FastAPI()
    app.include_router(weather_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[get_weather_settings_service] = lambda: service
    app.dependency_overrides[get_current_user] = _admin_user
    app.dependency_overrides[get_tenant_service] = lambda: tenant_service
    return app


def test_get_requires_platform_admin_full_mode(monkeypatch):
    monkeypatch.setattr(auth_mod.settings, "kamerplanter_mode", "full")
    service, _ = _service(stored=None)
    tenant_service = MagicMock()
    tenant_service.get_membership.return_value = SimpleNamespace(role=TenantRole.VIEWER, is_active=True)
    with _patch_env() as env:
        _set_env(env)
        client = TestClient(_build_app_with_real_gating(service, tenant_service))
        resp = client.get("/api/v1/admin/weather-providers")
    assert resp.status_code == 403


def test_put_requires_platform_admin_full_mode(monkeypatch):
    monkeypatch.setattr(auth_mod.settings, "kamerplanter_mode", "full")
    service, repo = _service(stored=None)
    tenant_service = MagicMock()
    tenant_service.get_membership.return_value = SimpleNamespace(role=TenantRole.GROWER, is_active=True)
    with _patch_env() as env:
        _set_env(env)
        client = TestClient(_build_app_with_real_gating(service, tenant_service))
        resp = client.put("/api/v1/admin/weather-providers", json={"dwd_enabled": False})
    assert resp.status_code == 403
    repo.upsert.assert_not_called()


def test_put_allows_system_user_in_light_mode(monkeypatch):
    monkeypatch.setattr(auth_mod.settings, "kamerplanter_mode", "light")
    service, repo = _service(stored=None)
    tenant_service = MagicMock()
    with _patch_env() as env:
        _set_env(env)
        client = TestClient(_build_app_with_real_gating(service, tenant_service))
        resp = client.put("/api/v1/admin/weather-providers", json={"dwd_enabled": False})
    assert resp.status_code == 200
    # Light mode must not consult tenant memberships at all.
    tenant_service.get_membership.assert_not_called()
    repo.upsert.assert_called_once()
