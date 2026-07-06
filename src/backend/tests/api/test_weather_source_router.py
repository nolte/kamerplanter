"""API tests for the tenant-scoped REQ-046 weather-source router (PR-4).

Wires the router with mocked service + tenant context and asserts the HTTP
contract: masked responses (no ciphertext ever leaves, AC-8), the ownership
guard mapping to 403 (AC-11), the available list, the connection test never
500-ing (AC-7), and the HA entity pickers.
"""

from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.tenant_scoped.weather.tenant_router import router as weather_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_sensor_service, get_weather_source_service
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import ForbiddenError, KamerplanterError, NotFoundError
from app.domain.models.tenant_context import TenantContext
from app.domain.models.weather import (
    WeatherForecast,
    WeatherSourceConfig,
    WeatherSourceEntry,
    WeatherSourcePublicConfig,
)
from app.domain.services.weather_source_service import (
    AvailableWeatherSource,
    AvailableWeatherSources,
    WeatherTestResult,
)

TENANT_KEY = "t-test-1"
SITE_KEY = "site-1"
BASE = "/api/v1/t/test-slug"


def _ctx() -> TenantContext:
    return TenantContext(
        tenant_key=TENANT_KEY,
        tenant_slug="test-slug",
        user_key="user-1",
        role=TenantRole.GROWER,
    )


def _build_app(service) -> FastAPI:
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(weather_router, prefix=BASE)
    app.dependency_overrides[get_weather_source_service] = lambda: service
    app.dependency_overrides[get_current_tenant] = _ctx
    return app


def _config_with_owm_cipher() -> WeatherSourceConfig:
    return WeatherSourceConfig(
        site_key=SITE_KEY,
        tenant_key=TENANT_KEY,
        enabled=True,
        sources=[
            WeatherSourceEntry(
                source_name="openweathermap",
                kind="public",
                enabled=True,
                config=WeatherSourcePublicConfig(api_key_ref="TOP-SECRET-CIPHERTEXT", units_hint="metric"),
            )
        ],
        updated_at=datetime.now(tz=UTC),
        updated_by="user-1",
    )


def test_get_masks_owm_key():
    service = MagicMock()
    service.get_config.return_value = _config_with_owm_cipher()
    client = TestClient(_build_app(service))

    resp = client.get(f"{BASE}/sites/{SITE_KEY}/weather-source")

    assert resp.status_code == 200
    assert "TOP-SECRET-CIPHERTEXT" not in resp.text  # ciphertext never returned (AC-8)
    entry = resp.json()["sources"][0]
    assert entry["public_config"]["api_key_set"] is True
    assert "api_key" not in entry["public_config"]
    assert "api_key_ref" not in entry["public_config"]


def test_get_empty_config_returns_defaults():
    service = MagicMock()
    service.get_config.return_value = None
    client = TestClient(_build_app(service))

    resp = client.get(f"{BASE}/sites/{SITE_KEY}/weather-source")

    assert resp.status_code == 200
    body = resp.json()
    assert body["site_key"] == SITE_KEY
    assert body["sources"] == []


def test_put_round_trip_returns_masked():
    service = MagicMock()
    service.save_config.return_value = _config_with_owm_cipher()
    client = TestClient(_build_app(service))

    resp = client.put(
        f"{BASE}/sites/{SITE_KEY}/weather-source",
        json={
            "enabled": True,
            "sources": [
                {
                    "source_name": "openweathermap",
                    "kind": "public",
                    "enabled": True,
                    "public_config": {"api_key": "user-typed-key"},
                }
            ],
        },
    )

    assert resp.status_code == 200
    assert "TOP-SECRET-CIPHERTEXT" not in resp.text
    assert resp.json()["sources"][0]["public_config"]["api_key_set"] is True
    # The plaintext key reached the service, not the response.
    service.save_config.assert_called_once()


def test_put_invalid_body_is_422():
    service = MagicMock()
    client = TestClient(_build_app(service))

    resp = client.put(
        f"{BASE}/sites/{SITE_KEY}/weather-source",
        json={"sources": [{"kind": "public"}]},  # missing required source_name
    )

    assert resp.status_code == 422
    service.save_config.assert_not_called()


def test_foreign_site_returns_403():
    service = MagicMock()
    service.get_config.side_effect = ForbiddenError("This site belongs to a different tenant.")
    client = TestClient(_build_app(service))

    resp = client.get(f"{BASE}/sites/{SITE_KEY}/weather-source")

    assert resp.status_code == 403


def test_available_lists_sources_and_ha_flag():
    service = MagicMock()
    service.available_sources.return_value = AvailableWeatherSources(
        sources=[
            AvailableWeatherSource(source_name="open-meteo", kind="public", requires_api_key=False),
            AvailableWeatherSource(source_name="openweathermap", kind="public", requires_api_key=True),
            AvailableWeatherSource(source_name="ha_weather", kind="home_assistant", requires_api_key=False),
        ],
        ha_token_set=True,
    )
    client = TestClient(_build_app(service))

    resp = client.get(f"{BASE}/weather-sources/available")

    assert resp.status_code == 200
    body = resp.json()
    assert body["ha_token_set"] is True
    names = {s["source_name"] for s in body["sources"]}
    assert names == {"open-meteo", "openweathermap", "ha_weather"}


def test_test_endpoint_reachable_with_preview():
    service = MagicMock()
    service.test_source = AsyncMock()
    service.test_source.return_value = WeatherTestResult(
        reachable=True,
        preview=[
            WeatherForecast(
                site_key="",
                forecast_date=datetime.now(tz=UTC).date(),
                source="open-meteo",
                fetched_at=datetime.now(tz=UTC),
                temp_min_c=4.0,
                temp_max_c=11.0,
            )
        ],
    )
    client = TestClient(_build_app(service))

    resp = client.post(
        f"{BASE}/sites/{SITE_KEY}/weather-sources/test",
        json={"source_name": "open-meteo", "kind": "public"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["reachable"] is True
    assert len(body["preview"]) == 1
    assert body["preview"][0]["source"] == "open-meteo"


def test_test_endpoint_unreachable_no_500():
    service = MagicMock()
    service.test_source = AsyncMock()
    service.test_source.return_value = WeatherTestResult(reachable=False, error="Connection refused")
    client = TestClient(_build_app(service))

    resp = client.post(
        f"{BASE}/sites/{SITE_KEY}/weather-sources/test",
        json={"source_name": "openweathermap", "kind": "public", "public_config": {"api_key": "bad"}},
    )

    assert resp.status_code == 200  # a broken source is a 200 result, not a 500
    body = resp.json()
    assert body["reachable"] is False
    assert body["error"] == "Connection refused"


def test_ha_weather_entities():
    service = MagicMock()
    service.list_ha_weather_entities.return_value = [
        {"entity_id": "weather.home", "friendly_name": "Home Weather", "state": "sunny"}
    ]
    client = TestClient(_build_app(service))

    resp = client.get(f"{BASE}/ha/weather-entities")

    assert resp.status_code == 200
    assert resp.json()[0]["entity_id"] == "weather.home"


def test_ha_sensor_entities_empty_without_token():
    service = MagicMock()
    service.list_ha_sensor_entities.return_value = []
    client = TestClient(_build_app(service))

    resp = client.get(f"{BASE}/ha/sensor-entities")

    assert resp.status_code == 200
    assert resp.json() == []


# ── Forecast read endpoint (Issue #392, R7) ────────────────────────────────


def _build_forecast_app(sensor_service, source_service=None) -> FastAPI:
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(weather_router, prefix=BASE)
    app.dependency_overrides[get_sensor_service] = lambda: sensor_service
    # The forecast read enforces site ownership at the API layer (defense-in-depth);
    # an owned site passes the guard silently, so default to a permissive mock.
    app.dependency_overrides[get_weather_source_service] = lambda: source_service or MagicMock()
    app.dependency_overrides[get_current_tenant] = _ctx
    return app


def test_site_weather_forecast_returns_payload():
    sensor_service = MagicMock()
    sensor_service.get_site_weather_forecast.return_value = {
        "site_key": SITE_KEY,
        "forecasts": [
            {
                "forecast_date": date(2026, 7, 6),
                "temp_min_c": -1.5,
                "temp_max_c": 6.0,
                "precipitation_mm": 0.0,
                "wind_speed_kmh": 10.0,
                "humidity_percent": 80.0,
                "weather_code": "clear",
                "source": "open-meteo",
                "data_kind": "forecast",
            }
        ],
        "forecast_frost_warning": True,
        "forecast_min_temperature": -1.5,
        "forecast_expected_date": date(2026, 7, 6),
        "forecast_source": "open-meteo",
    }
    client = TestClient(_build_forecast_app(sensor_service))

    resp = client.get(f"{BASE}/sites/{SITE_KEY}/weather-forecast")

    assert resp.status_code == 200
    body = resp.json()
    assert body["site_key"] == SITE_KEY
    assert len(body["forecasts"]) == 1
    assert body["forecasts"][0]["source"] == "open-meteo"
    assert body["forecasts"][0]["data_kind"] == "forecast"
    assert body["forecast_frost_warning"] is True
    assert body["forecast_expected_date"] == "2026-07-06"
    sensor_service.get_site_weather_forecast.assert_called_once_with(SITE_KEY, TENANT_KEY)


def test_site_weather_forecast_graceful_empty():
    sensor_service = MagicMock()
    sensor_service.get_site_weather_forecast.return_value = {
        "site_key": SITE_KEY,
        "forecasts": [],
        "forecast_frost_warning": None,
        "forecast_min_temperature": None,
        "forecast_expected_date": None,
        "forecast_source": None,
    }
    client = TestClient(_build_forecast_app(sensor_service))

    resp = client.get(f"{BASE}/sites/{SITE_KEY}/weather-forecast")

    assert resp.status_code == 200
    body = resp.json()
    assert body["forecasts"] == []
    assert body["forecast_frost_warning"] is None


def test_site_weather_forecast_foreign_site_403():
    # Defense-in-depth: a foreign site is rejected at the API layer (403) and the
    # forecast service is never consulted — no cross-tenant forecast leak.
    sensor_service = MagicMock()
    source_service = MagicMock()
    source_service.verify_site_owned.side_effect = ForbiddenError("This site belongs to a different tenant.")
    client = TestClient(_build_forecast_app(sensor_service, source_service))

    resp = client.get(f"{BASE}/sites/{SITE_KEY}/weather-forecast")

    assert resp.status_code == 403
    sensor_service.get_site_weather_forecast.assert_not_called()


def test_site_weather_forecast_unknown_site_404():
    sensor_service = MagicMock()
    source_service = MagicMock()
    source_service.verify_site_owned.side_effect = NotFoundError("Site", SITE_KEY)
    client = TestClient(_build_forecast_app(sensor_service, source_service))

    resp = client.get(f"{BASE}/sites/{SITE_KEY}/weather-forecast")

    assert resp.status_code == 404
    sensor_service.get_site_weather_forecast.assert_not_called()
