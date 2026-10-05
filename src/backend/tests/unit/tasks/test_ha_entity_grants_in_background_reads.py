"""MT-015 (#2112): every background path skips a Home Assistant entity the tenant was not granted.

The beat tasks walk every tenant's rows against the operator's one instance. Each
row is checked against *its own* tenant's grants (one snapshot per run), and an
ungranted entity is never asked of Home Assistant — counted, not read:

* ``sync_tank_states_from_ha`` — tank sensors (tenant = the tank's);
* ``sync_actuator_states`` — actuator online polling (tenant = the actuator's);
* ``evaluate_control_rules`` — the location readings that drive a rule
  (tenant = the actuator's) — via ``_resolve_location_readings``;
* ``ActuatorService`` dispatch — an ungranted actuator is not switched; it
  degrades to the manual fallback task;
* ``WeatherSourceResolver`` — an ungranted mapped sensor stays unmapped, an
  ungranted ``weather.*`` entity makes the source unavailable (the chain moves on).

The ingest task has its own file (``test_sensor_ingestion_tasks.py``).
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.domain.models.weather import (
    HaSensorMapping,
    WeatherForecast,
    WeatherSourceConfig,
    WeatherSourceEntry,
    WeatherSourceHaConfig,
)
from tests.support.ha_entity_grants import grant_service

GRANTS = {"t1": {"sensor.tank_ec", "switch.fan", "sensor.tent_temp", "weather.home", "sensor.out_temp"}}


class _AskedHa:
    def __init__(self) -> None:
        self.asked: list[str] = []

    def get_state(self, entity_id: str, timeout: float | None = None) -> dict:  # noqa: ARG002
        self.asked.append(entity_id)
        return {"value": 1.5, "unit": None}


@pytest.fixture
def deps(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    module = ModuleType("app.common.dependencies")
    module.get_ha_client = MagicMock()  # type: ignore[attr-defined]
    module.get_sensor_repo = MagicMock()  # type: ignore[attr-defined]
    module.get_tank_repo = MagicMock()  # type: ignore[attr-defined]
    module.get_actuator_repo = MagicMock()  # type: ignore[attr-defined]
    module.get_ha_entity_grant_service = lambda: grant_service(GRANTS)  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "app.common.dependencies", module)
    from app.config.settings import settings

    monkeypatch.setattr(settings, "actuator_control_loop_enabled", True)
    return module


def _sensor(key: str, entity_id: str, metric: str = "ec_ms") -> SimpleNamespace:
    return SimpleNamespace(key=key, ha_entity_id=entity_id, metric_type=metric, is_active=True)


class TestTankSync:
    def test_only_the_tanks_granted_entities_are_read(self, deps: ModuleType) -> None:
        ha = _AskedHa()
        deps.get_ha_client.return_value = ha
        tank_repo = MagicMock()
        tank_repo.get_all.return_value = ([SimpleNamespace(key="tank-1", tenant_key="t1")], 1)
        deps.get_tank_repo.return_value = tank_repo
        deps.get_sensor_repo.return_value.find_by_tank.return_value = [
            _sensor("s1", "sensor.tank_ec"),
            _sensor("s2", "sensor.operator_door", metric="ph"),
        ]

        from app.tasks.tank_maintenance_tasks import sync_tank_states_from_ha

        result = sync_tank_states_from_ha()

        assert ha.asked == ["sensor.tank_ec"]
        assert result["not_granted"] == 1

    def test_a_tank_of_another_tenant_reads_nothing(self, deps: ModuleType) -> None:
        ha = _AskedHa()
        deps.get_ha_client.return_value = ha
        tank_repo = MagicMock()
        tank_repo.get_all.return_value = ([SimpleNamespace(key="tank-2", tenant_key="t2")], 1)
        deps.get_tank_repo.return_value = tank_repo
        deps.get_sensor_repo.return_value.find_by_tank.return_value = [_sensor("s1", "sensor.tank_ec")]

        from app.tasks.tank_maintenance_tasks import sync_tank_states_from_ha

        sync_tank_states_from_ha()

        assert ha.asked == []


class _Actuator(SimpleNamespace):
    def model_copy(self, update):
        return _Actuator(**{**vars(self), **update})


class TestActuatorStateSync:
    def test_an_ungranted_actuator_is_not_polled(self, deps: ModuleType) -> None:
        ha = _AskedHa()
        deps.get_ha_client.return_value = ha
        repo = MagicMock()
        repo.get_all.return_value = (
            [
                _Actuator(key="a1", tenant_key="t1", ha_entity_id="switch.fan", is_online=True),
                _Actuator(key="a2", tenant_key="t1", ha_entity_id="switch.operator_heater", is_online=True),
                _Actuator(key="a3", tenant_key="t2", ha_entity_id="switch.fan", is_online=True),
            ],
            3,
        )
        deps.get_actuator_repo.return_value = repo

        from app.tasks.actuator_tasks import sync_actuator_states

        result = sync_actuator_states.run()

        assert ha.asked == ["switch.fan"]
        assert result["not_granted"] == 2


class TestControlLoopReadings:
    def test_only_granted_sensors_drive_a_rule(self, deps: ModuleType) -> None:
        from app.tasks.actuator_tasks import _resolve_location_readings

        ha = _AskedHa()
        sensor_repo = MagicMock()
        sensor_repo.find_by_location.return_value = [
            _sensor("s1", "sensor.tent_temp", metric="temperature_celsius"),
            _sensor("s2", "sensor.operator_bedroom", metric="humidity_percent"),
        ]

        readings = _resolve_location_readings(
            sensor_repo, ha, "loc-1", tenant_key="t1", grants=grant_service(GRANTS).snapshot()
        )

        assert ha.asked == ["sensor.tent_temp"]
        assert readings == {"temperature_celsius": 1.5}


class TestActuatorDispatch:
    def _service(self, entity_id: str, tenant_key: str = "t1"):
        from app.domain.models.actuator import Actuator
        from app.domain.services.actuator_service import ActuatorService

        ha = MagicMock()
        task_repo = MagicMock()
        service = ActuatorService(
            MagicMock(), ha_client_factory=lambda: ha, task_repo=task_repo, ha_entity_grants=grant_service(GRANTS)
        )
        actuator = Actuator(
            _key="a1",
            name="Fan",
            actuator_type="exhaust_fan",
            protocol="home_assistant",
            ha_entity_id=entity_id,
            tenant_key=tenant_key,
            location_key="loc-1",
        )
        return service, actuator, ha

    def test_an_ungranted_entity_is_not_switched(self) -> None:
        service, actuator, ha = self._service("switch.operator_heater")

        ok, error = service._dispatch_home_assistant(actuator, "turn_on", None)

        assert ok is False and error is not None
        ha.call_service.assert_not_called()

    def test_another_tenants_grant_does_not_switch_it(self) -> None:
        service, actuator, ha = self._service("switch.fan", tenant_key="t2")

        ok, _ = service._dispatch_home_assistant(actuator, "turn_on", None)

        assert ok is False
        ha.call_service.assert_not_called()

    def test_a_granted_entity_is_switched(self) -> None:
        service, actuator, ha = self._service("switch.fan")

        async def _ok(*_a, **_k):
            return {}

        ha.call_service.side_effect = _ok

        ok, _ = service._dispatch_home_assistant(actuator, "turn_on", None)

        assert ok is True
        ha.call_service.assert_called_once()


class _HaAdapter:
    source_name = "ha_weather"
    kind = "home_assistant"
    requires_api_key = False
    seen: list[object] = []

    def __init__(self, ha_client) -> None:  # noqa: ARG002
        pass

    async def fetch_daily(self, *, latitude, longitude, config=None):  # noqa: ARG002
        type(self).seen.append(config)
        return [
            WeatherForecast(
                site_key="",
                forecast_date=datetime.now(tz=UTC).date(),
                source="ha_weather",
                fetched_at=datetime.now(tz=UTC),
            )
        ]


@pytest.fixture
def ha_weather_adapter():
    from app.domain.services.weather_adapter_registry import WeatherAdapterRegistry

    original = WeatherAdapterRegistry._adapters.copy()
    WeatherAdapterRegistry.clear()
    _HaAdapter.seen = []
    WeatherAdapterRegistry.register(_HaAdapter)  # type: ignore[arg-type]
    yield _HaAdapter
    WeatherAdapterRegistry._adapters = original


def _resolver():
    from app.domain.services.weather_source_resolver import WeatherSourceResolver

    return WeatherSourceResolver(MagicMock(), lambda: object(), ha_entity_gate=grant_service(GRANTS).snapshot())


def _ha_cfg(tenant_key: str, config: WeatherSourceHaConfig) -> WeatherSourceConfig:
    entry = WeatherSourceEntry(source_name="ha_weather", kind="home_assistant", enabled=True, config=config)
    return WeatherSourceConfig(site_key="site-1", tenant_key=tenant_key, sources=[entry])


class TestWeatherResolver:
    @pytest.mark.asyncio
    async def test_an_ungranted_mapped_sensor_stays_unmapped(self, ha_weather_adapter) -> None:
        mapping = HaSensorMapping(temp_current_entity="sensor.out_temp", humidity_entity="sensor.operator_bath")
        cfg = _ha_cfg("t1", WeatherSourceHaConfig(mode="sensor_mapping", sensor_mapping=mapping))

        records = await _resolver().resolve_daily(SimpleNamespace(gps_coordinates=(52.5, 13.4)), cfg)

        assert records
        (seen,) = ha_weather_adapter.seen
        assert seen.sensor_mapping.temp_current_entity == "sensor.out_temp"
        assert seen.sensor_mapping.humidity_entity is None

    @pytest.mark.asyncio
    async def test_an_ungranted_weather_entity_makes_the_source_unavailable(self, ha_weather_adapter) -> None:
        cfg = _ha_cfg("t2", WeatherSourceHaConfig(mode="weather_entity", weather_entity_id="weather.home"))

        records = await _resolver().resolve_daily(SimpleNamespace(gps_coordinates=(52.5, 13.4)), cfg)

        assert records == []
        assert ha_weather_adapter.seen == []

    @pytest.mark.asyncio
    async def test_a_granted_weather_entity_is_read(self, ha_weather_adapter) -> None:
        cfg = _ha_cfg("t1", WeatherSourceHaConfig(mode="weather_entity", weather_entity_id="weather.home"))

        records = await _resolver().resolve_daily(SimpleNamespace(gps_coordinates=(52.5, 13.4)), cfg)

        assert [r.source for r in records] == ["ha_weather"]
