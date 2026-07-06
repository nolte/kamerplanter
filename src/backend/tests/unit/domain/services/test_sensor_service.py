from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.config.settings import settings
from app.domain.models.sensor import Sensor
from app.domain.models.site import Site
from app.domain.models.weather import WeatherForecast
from app.domain.services.sensor_service import SensorService


@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def mock_ha_client():
    return MagicMock()


@pytest.fixture
def service(mock_repo, mock_ha_client):
    return SensorService(mock_repo, mock_ha_client)


@pytest.fixture
def service_no_ha(mock_repo):
    return SensorService(mock_repo, None)


class TestGetLiveState:
    def test_no_ha_client(self, service_no_ha, mock_repo):
        mock_repo.find_by_tank.return_value = [
            Sensor(name="EC", metric_type="ec_ms", ha_entity_id="sensor.ec", tank_key="t1"),
        ]
        result = service_no_ha.get_live_state("t1")
        assert result["source"] == "unavailable"
        assert result["values"] == {}
        assert result["message"] == "Home Assistant not configured"

    def test_no_sensors(self, service, mock_repo, mock_ha_client):
        mock_repo.find_by_tank.return_value = []
        result = service.get_live_state("t1")
        assert result["source"] == "ha_live"
        assert result["values"] == {}
        assert result["errors"] == []

    def test_success(self, service, mock_repo, mock_ha_client):
        mock_repo.find_by_tank.return_value = [
            Sensor(name="EC Sensor", metric_type="ec_ms", ha_entity_id="sensor.tank_ec", tank_key="t1"),
        ]
        mock_ha_client.get_state.return_value = {
            "value": 1.45,
            "last_changed": "2026-03-01T10:00:00Z",
            "entity_id": "sensor.tank_ec",
            "unit": "mS/cm",
        }
        result = service.get_live_state("t1")
        assert result["source"] == "ha_live"
        assert "ec_ms" in result["values"]
        assert result["values"]["ec_ms"]["value"] == 1.45
        assert result["values"]["ec_ms"]["entity_id"] == "sensor.tank_ec"
        assert result["values"]["ec_ms"]["unit"] == "mS/cm"
        assert result["errors"] == []

    def test_ha_error(self, service, mock_repo, mock_ha_client):
        mock_repo.find_by_tank.return_value = [
            Sensor(name="EC Sensor", metric_type="ec_ms", ha_entity_id="sensor.tank_ec", tank_key="t1"),
        ]
        mock_ha_client.get_state.side_effect = Exception("Connection refused")
        result = service.get_live_state("t1")
        assert result["source"] == "ha_live"
        assert result["values"] == {}
        assert len(result["errors"]) == 1
        assert result["errors"][0]["entity_id"] == "sensor.tank_ec"
        assert "Connection refused" in result["errors"][0]["error"]

    def test_entity_unavailable(self, service, mock_repo, mock_ha_client):
        mock_repo.find_by_tank.return_value = [
            Sensor(name="EC Sensor", metric_type="ec_ms", ha_entity_id="sensor.tank_ec", tank_key="t1"),
        ]
        mock_ha_client.get_state.return_value = {
            "value": None,
            "last_changed": "2026-03-01T10:00:00Z",
            "entity_id": "sensor.tank_ec",
            "unit": None,
        }
        result = service.get_live_state("t1")
        assert result["source"] == "ha_live"
        assert result["values"] == {}  # value was None, not included
        assert result["errors"] == []

    def test_multiple_sensors(self, service, mock_repo, mock_ha_client):
        mock_repo.find_by_tank.return_value = [
            Sensor(name="EC", metric_type="ec_ms", ha_entity_id="sensor.ec", tank_key="t1"),
            Sensor(name="pH", metric_type="ph", ha_entity_id="sensor.ph", tank_key="t1"),
        ]
        mock_ha_client.get_state.side_effect = [
            {"value": 1.2, "last_changed": "2026-03-01T10:00:00Z", "entity_id": "sensor.ec", "unit": "mS/cm"},
            {"value": 6.1, "last_changed": "2026-03-01T10:01:00Z", "entity_id": "sensor.ph", "unit": "pH"},
        ]
        result = service.get_live_state("t1")
        assert len(result["values"]) == 2
        assert result["values"]["ec_ms"]["value"] == 1.2
        assert result["values"]["ph"]["value"] == 6.1

    def test_sensor_without_entity_id_skipped(self, service, mock_repo, mock_ha_client):
        mock_repo.find_by_tank.return_value = [
            Sensor(name="MQTT only", metric_type="ec_ms", mqtt_topic="tank/ec", tank_key="t1"),
        ]
        result = service.get_live_state("t1")
        assert result["source"] == "ha_live"
        assert result["values"] == {}
        mock_ha_client.get_state.assert_not_called()


class TestCreateSensor:
    def test_create(self, service, mock_repo):
        sensor = Sensor(name="EC", metric_type="ec_ms", tank_key="t1")
        mock_repo.create.return_value = Sensor(
            _key="s1",
            name="EC",
            metric_type="ec_ms",
            tank_key="t1",
        )
        result = service.create_sensor(sensor)
        assert result.key == "s1"
        mock_repo.create.assert_called_once_with(sensor)


class TestDeleteSensor:
    def test_delete(self, service, mock_repo):
        mock_repo.delete.return_value = True
        result = service.delete_sensor("s1")
        assert result is True
        mock_repo.delete.assert_called_once_with("s1")


class TestGetSensorsForSite:
    def test_get_sensors_for_site(self, service, mock_repo):
        mock_repo.find_by_site.return_value = [
            Sensor(name="Weather Station", metric_type="temperature_celsius", site_key="site1"),
        ]
        result = service.get_sensors_for_site("site1")
        assert len(result) == 1
        assert result[0].site_key == "site1"
        mock_repo.find_by_site.assert_called_once_with("site1")

    def test_get_sensors_for_site_empty(self, service, mock_repo):
        mock_repo.find_by_site.return_value = []
        result = service.get_sensors_for_site("site1")
        assert result == []


class TestGetSensorsForLocation:
    def test_get_sensors_for_location(self, service, mock_repo):
        mock_repo.find_by_location.return_value = [
            Sensor(name="Tent Climate", metric_type="humidity_percent", location_key="loc1"),
        ]
        result = service.get_sensors_for_location("loc1")
        assert len(result) == 1
        assert result[0].location_key == "loc1"
        mock_repo.find_by_location.assert_called_once_with("loc1")


class TestGetLiveStateForSensors:
    def test_direct_sensor_list(self, service, mock_ha_client):
        sensors = [
            Sensor(name="Temp", metric_type="temperature_celsius", ha_entity_id="sensor.outdoor_temp", site_key="s1"),
        ]
        mock_ha_client.get_state.return_value = {
            "value": 22.5,
            "last_changed": "2026-03-01T12:00:00Z",
            "entity_id": "sensor.outdoor_temp",
            "unit": "°C",
        }
        result = service.get_live_state_for_sensors(sensors)
        assert result["source"] == "ha_live"
        assert result["values"]["temperature_celsius"]["value"] == 22.5

    def test_no_ha_client_returns_unavailable(self, service_no_ha):
        sensors = [
            Sensor(name="Temp", metric_type="temperature_celsius", ha_entity_id="sensor.temp", site_key="s1"),
        ]
        result = service_no_ha.get_live_state_for_sensors(sensors)
        assert result["source"] == "unavailable"
        assert result["message"] == "Home Assistant not configured"


class TestGetLocationFrostWarning:
    def _temp_sensor(self) -> Sensor:
        return Sensor(
            name="Air Temp",
            metric_type="temperature_celsius",
            ha_entity_id="sensor.loc_temp",
            location_key="loc1",
        )

    def test_frost_warning_true_below_threshold(self, service, mock_repo, mock_ha_client):
        mock_repo.find_by_location.return_value = [self._temp_sensor()]
        mock_ha_client.get_state.return_value = {
            "value": 1.0,
            "last_changed": "2026-03-01T02:00:00Z",
            "entity_id": "sensor.loc_temp",
            "unit": "°C",
        }
        result = service.get_location_frost_warning("loc1", tenant_key="")
        assert result["frost_warning"] is True
        assert result["temperature_celsius"] == 1.0
        assert result["threshold_celsius"] == 3.0
        assert result["source"] == "ha_live"
        assert result["entity_id"] == "sensor.loc_temp"
        mock_repo.find_by_location.assert_called_once_with("loc1")

    def test_frost_warning_false_above_threshold(self, service, mock_repo, mock_ha_client):
        mock_repo.find_by_location.return_value = [self._temp_sensor()]
        mock_ha_client.get_state.return_value = {
            "value": 12.5,
            "last_changed": "2026-03-01T14:00:00Z",
            "entity_id": "sensor.loc_temp",
            "unit": "°C",
        }
        result = service.get_location_frost_warning("loc1", tenant_key="")
        assert result["frost_warning"] is False
        assert result["source"] == "ha_live"

    def test_unknown_when_no_temperature_sensor(self, service, mock_repo, mock_ha_client):
        mock_repo.find_by_location.return_value = [
            Sensor(name="Humidity", metric_type="humidity_percent", ha_entity_id="sensor.hum", location_key="loc1"),
        ]
        mock_ha_client.get_state.return_value = {
            "value": 60.0,
            "last_changed": "2026-03-01T14:00:00Z",
            "entity_id": "sensor.hum",
            "unit": "%",
        }
        result = service.get_location_frost_warning("loc1", tenant_key="")
        assert result["frost_warning"] is None
        assert result["temperature_celsius"] is None
        assert result["source"] == "no_temperature"

    def test_unknown_when_temperature_state_non_numeric(self, service, mock_repo, mock_ha_client):
        # Home Assistant reports "unavailable"/"unknown" as the *value* of an
        # otherwise-live entity. That must not raise (→ 500); the endpoint reports
        # an honest unknown instead.
        mock_repo.find_by_location.return_value = [self._temp_sensor()]
        mock_ha_client.get_state.return_value = {
            "value": "unavailable",
            "last_changed": "2026-03-01T02:00:00Z",
            "entity_id": "sensor.loc_temp",
            "unit": "°C",
        }
        result = service.get_location_frost_warning("loc1", tenant_key="")
        assert result["frost_warning"] is None
        assert result["temperature_celsius"] is None
        assert result["source"] == "no_temperature"

    def test_unknown_when_ha_unavailable(self, service_no_ha, mock_repo):
        mock_repo.find_by_location.return_value = [self._temp_sensor()]
        result = service_no_ha.get_location_frost_warning("loc1", tenant_key="")
        assert result["frost_warning"] is None
        assert result["source"] == "unavailable"

    def test_custom_threshold_override(self, service, mock_repo, mock_ha_client):
        mock_repo.find_by_location.return_value = [self._temp_sensor()]
        mock_ha_client.get_state.return_value = {
            "value": 2.0,
            "last_changed": "2026-03-01T02:00:00Z",
            "entity_id": "sensor.loc_temp",
            "unit": "°C",
        }
        result = service.get_location_frost_warning("loc1", threshold_celsius=0.0, tenant_key="")
        assert result["frost_warning"] is False
        assert result["threshold_celsius"] == 0.0

    def test_forecast_fields_none_without_weather_repo(self, service, mock_repo, mock_ha_client):
        # No weather_forecast_repo injected → forecast fields None, reactive intact.
        mock_repo.find_by_location.return_value = [self._temp_sensor()]
        mock_ha_client.get_state.return_value = {
            "value": 1.0,
            "last_changed": "2026-03-01T02:00:00Z",
            "entity_id": "sensor.loc_temp",
            "unit": "°C",
        }
        result = service.get_location_frost_warning("loc1", site_key="site-1", tenant_key="t-1")
        assert result["frost_warning"] is True  # reactive unchanged
        assert result["forecast_frost_warning"] is None
        assert result["forecast_min_temperature"] is None
        assert result["forecast_expected_date"] is None
        assert result["forecast_source"] is None


TENANT_KEY = "t-1"
SITE_KEY = "site-1"


def _site(gps=(52.5, 13.4), tenant_key=TENANT_KEY) -> Site:
    return Site(_key=SITE_KEY, tenant_key=tenant_key, name="Garden", gps_coordinates=gps)


def _forecast(day_offset: int, temp_min_c: float | None, source: str = "open-meteo") -> WeatherForecast:
    return WeatherForecast(
        site_key=SITE_KEY,
        forecast_date=datetime.now(UTC).date() + timedelta(days=day_offset),
        temp_min_c=temp_min_c,
        temp_max_c=None if temp_min_c is None else temp_min_c + 8.0,
        source=source,
        fetched_at=datetime(2026, 7, 5, 6, 0, 0),
    )


@pytest.fixture
def mock_forecast_repo():
    return MagicMock()


@pytest.fixture
def mock_site_repo():
    repo = MagicMock()
    repo.get_site_by_key.return_value = _site()
    return repo


@pytest.fixture
def forecast_service(mock_repo, mock_ha_client, mock_forecast_repo, mock_site_repo):
    return SensorService(
        mock_repo,
        mock_ha_client,
        weather_forecast_repo=mock_forecast_repo,
        site_repo=mock_site_repo,
    )


@pytest.fixture(autouse=True)
def _weather_enabled(monkeypatch):
    monkeypatch.setattr(settings, "weather_enabled", True)
    monkeypatch.setattr(settings, "frost_forecast_threshold_celsius", 2.0)
    monkeypatch.setattr(settings, "frost_forecast_horizon_days", 2)


class TestLocationFrostWarningForecast:
    def _temp_sensor(self) -> Sensor:
        return Sensor(
            name="Air Temp",
            metric_type="temperature_celsius",
            ha_entity_id="sensor.loc_temp",
            location_key="loc1",
        )

    def _wire_reactive(self, mock_repo, mock_ha_client, temp=10.0):
        mock_repo.find_by_location.return_value = [self._temp_sensor()]
        mock_ha_client.get_state.return_value = {
            "value": temp,
            "last_changed": "2026-07-05T02:00:00Z",
            "entity_id": "sensor.loc_temp",
            "unit": "°C",
        }

    def test_forecast_frost_in_horizon_sets_fields(
        self, forecast_service, mock_repo, mock_ha_client, mock_forecast_repo
    ):
        self._wire_reactive(mock_repo, mock_ha_client, temp=10.0)
        mock_forecast_repo.find_by_site.return_value = [_forecast(0, 8.0), _forecast(1, -1.5)]
        result = forecast_service.get_location_frost_warning("loc1", site_key=SITE_KEY, tenant_key=TENANT_KEY)
        # Reactive path unchanged (10 °C above threshold).
        assert result["frost_warning"] is False
        # Proactive path detects the in-horizon frost.
        assert result["forecast_frost_warning"] is True
        assert result["forecast_min_temperature"] == -1.5
        assert result["forecast_expected_date"] == datetime.now(UTC).date() + timedelta(days=1)
        assert result["forecast_source"] == "open-meteo"

    def test_tenant_isolation_find_by_site_called_with_tenant(
        self, forecast_service, mock_repo, mock_ha_client, mock_forecast_repo
    ):
        self._wire_reactive(mock_repo, mock_ha_client)
        mock_forecast_repo.find_by_site.return_value = []
        forecast_service.get_location_frost_warning("loc1", site_key=SITE_KEY, tenant_key=TENANT_KEY)
        mock_forecast_repo.find_by_site.assert_called_once_with(SITE_KEY, TENANT_KEY)

    def test_weather_disabled_yields_none(
        self, forecast_service, mock_repo, mock_ha_client, mock_forecast_repo, monkeypatch
    ):
        monkeypatch.setattr(settings, "weather_enabled", False)
        self._wire_reactive(mock_repo, mock_ha_client)
        mock_forecast_repo.find_by_site.return_value = [_forecast(1, -5.0)]
        result = forecast_service.get_location_frost_warning("loc1", site_key=SITE_KEY, tenant_key=TENANT_KEY)
        assert result["forecast_frost_warning"] is None
        mock_forecast_repo.find_by_site.assert_not_called()

    def test_no_gps_yields_none(self, forecast_service, mock_repo, mock_ha_client, mock_forecast_repo, mock_site_repo):
        mock_site_repo.get_site_by_key.return_value = _site(gps=None)
        self._wire_reactive(mock_repo, mock_ha_client)
        result = forecast_service.get_location_frost_warning("loc1", site_key=SITE_KEY, tenant_key=TENANT_KEY)
        assert result["forecast_frost_warning"] is None
        mock_forecast_repo.find_by_site.assert_not_called()

    def test_foreign_tenant_site_yields_none(
        self, forecast_service, mock_repo, mock_ha_client, mock_forecast_repo, mock_site_repo
    ):
        mock_site_repo.get_site_by_key.return_value = _site(tenant_key="other-tenant")
        self._wire_reactive(mock_repo, mock_ha_client)
        result = forecast_service.get_location_frost_warning("loc1", site_key=SITE_KEY, tenant_key=TENANT_KEY)
        assert result["forecast_frost_warning"] is None
        mock_forecast_repo.find_by_site.assert_not_called()

    def test_no_site_key_yields_none(self, forecast_service, mock_repo, mock_ha_client, mock_forecast_repo):
        self._wire_reactive(mock_repo, mock_ha_client)
        result = forecast_service.get_location_frost_warning("loc1", tenant_key=TENANT_KEY)
        assert result["forecast_frost_warning"] is None
        mock_forecast_repo.find_by_site.assert_not_called()

    def test_empty_tenant_key_does_not_leak_owned_site(
        self, forecast_service, mock_repo, mock_ha_client, mock_forecast_repo, mock_site_repo
    ):
        # Fail-closed: an empty tenant_key must NOT read forecasts of a site that
        # belongs to a real tenant (the former ``tenant_key and ...`` short-circuit
        # bypassed the guard for an empty tenant_key).
        mock_site_repo.get_site_by_key.return_value = _site(tenant_key=TENANT_KEY)
        self._wire_reactive(mock_repo, mock_ha_client)
        result = forecast_service.get_location_frost_warning("loc1", site_key=SITE_KEY, tenant_key="")
        assert result["forecast_frost_warning"] is None
        mock_forecast_repo.find_by_site.assert_not_called()

    def test_empty_tenant_key_matches_light_mode_site(
        self, forecast_service, mock_repo, mock_ha_client, mock_forecast_repo, mock_site_repo
    ):
        # Light mode: an empty tenant_key legitimately matches a site whose own
        # tenant_key is likewise empty, so the forecast read still proceeds.
        mock_site_repo.get_site_by_key.return_value = _site(tenant_key="")
        self._wire_reactive(mock_repo, mock_ha_client)
        mock_forecast_repo.find_by_site.return_value = [_forecast(1, -2.0)]
        result = forecast_service.get_location_frost_warning("loc1", site_key=SITE_KEY, tenant_key="")
        assert result["forecast_frost_warning"] is True
        mock_forecast_repo.find_by_site.assert_called_once_with(SITE_KEY, "")

    def test_uses_utc_today_for_horizon(self, forecast_service, mock_repo, mock_ha_client, mock_forecast_repo):
        # The read path must anchor its horizon on the UTC calendar day (matching
        # the notification task) rather than server-local time.
        self._wire_reactive(mock_repo, mock_ha_client)
        utc_today = datetime.now(UTC).date()
        mock_forecast_repo.find_by_site.return_value = [
            WeatherForecast(
                site_key=SITE_KEY,
                forecast_date=utc_today,
                temp_min_c=-1.0,
                temp_max_c=5.0,
                source="open-meteo",
                fetched_at=datetime(2026, 7, 5, 6, 0, 0),
            )
        ]
        result = forecast_service.get_location_frost_warning("loc1", site_key=SITE_KEY, tenant_key=TENANT_KEY)
        assert result["forecast_frost_warning"] is True
        assert result["forecast_expected_date"] == utc_today

    def test_repo_exception_never_raises(self, forecast_service, mock_repo, mock_ha_client, mock_forecast_repo):
        # A forecast-repo failure must degrade to None, never bubble to a 500.
        self._wire_reactive(mock_repo, mock_ha_client, temp=1.0)
        mock_forecast_repo.find_by_site.side_effect = RuntimeError("db down")
        result = forecast_service.get_location_frost_warning("loc1", site_key=SITE_KEY, tenant_key=TENANT_KEY)
        assert result["frost_warning"] is True  # reactive intact
        assert result["forecast_frost_warning"] is None


class TestGetSiteWeatherForecast:
    def test_returns_in_horizon_rows_and_summary(self, forecast_service, mock_forecast_repo):
        mock_forecast_repo.find_by_site.return_value = [
            _forecast(0, 5.0),
            _forecast(1, -2.0),
            _forecast(3, -9.0),  # beyond horizon → excluded from rows and summary
        ]
        result = forecast_service.get_site_weather_forecast(SITE_KEY, TENANT_KEY)
        assert result["site_key"] == SITE_KEY
        # Only in-horizon rows (offsets 0 and 1), sorted by date.
        assert [row["forecast_date"] for row in result["forecasts"]] == [
            datetime.now(UTC).date(),
            datetime.now(UTC).date() + timedelta(days=1),
        ]
        assert result["forecasts"][0]["data_kind"] == "forecast"
        assert result["forecast_frost_warning"] is True
        assert result["forecast_expected_date"] == datetime.now(UTC).date() + timedelta(days=1)
        assert result["forecast_min_temperature"] == -2.0

    def test_tenant_scoped_read(self, forecast_service, mock_forecast_repo):
        mock_forecast_repo.find_by_site.return_value = []
        forecast_service.get_site_weather_forecast(SITE_KEY, TENANT_KEY)
        mock_forecast_repo.find_by_site.assert_called_once_with(SITE_KEY, TENANT_KEY)

    def test_graceful_empty_without_repo(self, mock_repo, mock_ha_client):
        service = SensorService(mock_repo, mock_ha_client)
        result = service.get_site_weather_forecast(SITE_KEY, TENANT_KEY)
        assert result["forecasts"] == []
        assert result["forecast_frost_warning"] is None

    def test_graceful_empty_when_no_gps(self, forecast_service, mock_forecast_repo, mock_site_repo):
        mock_site_repo.get_site_by_key.return_value = _site(gps=None)
        result = forecast_service.get_site_weather_forecast(SITE_KEY, TENANT_KEY)
        assert result["forecasts"] == []
        assert result["forecast_frost_warning"] is None
        mock_forecast_repo.find_by_site.assert_not_called()

    def test_repo_exception_returns_empty(self, forecast_service, mock_forecast_repo):
        mock_forecast_repo.find_by_site.side_effect = RuntimeError("db down")
        result = forecast_service.get_site_weather_forecast(SITE_KEY, TENANT_KEY)
        assert result["forecasts"] == []
        assert result["forecast_frost_warning"] is None
