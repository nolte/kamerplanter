"""A reading is recorded only for a sensor of the caller's tenant — #1871 B6.

``POST /t/{slug}/observations/sensors/{sensor_key}/readings`` checked only that
the sensor *existed* (a foreign sensor answered 201, an unknown one 404 — an
existence oracle), and ``…/readings/batch`` checked nothing. A sensor carries no
``tenant_key``: its tenant is its parent's — a tank (``Tank.tenant_key``), a site
(``Site.tenant_key``) or a location (through its site, #1397).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.common.enums import TankType
from app.common.exceptions import NotFoundError
from app.domain.models.observation import SensorReading
from app.domain.models.sensor import Sensor
from app.domain.models.tank import Tank
from app.domain.services.observation_service import ObservationService
from tests.unit.domain.services.test_site_service_location_tenant import OWN, FakeSiteRepo


class _Sensors:
    _sensors = {
        "s_tank_own": Sensor(_key="s_tank_own", name="EC", metric_type="ec_ms", tank_key="tank_own"),
        "s_tank_foreign": Sensor(_key="s_tank_foreign", name="EC", metric_type="ec_ms", tank_key="tank_foreign"),
        "s_site_own": Sensor(_key="s_site_own", name="T", metric_type="ec_ms", site_key="site_own"),
        "s_site_foreign": Sensor(_key="s_site_foreign", name="T", metric_type="ec_ms", site_key="site_foreign"),
        "s_loc_own": Sensor(_key="s_loc_own", name="H", metric_type="ec_ms", location_key="loc_own"),
        "s_loc_foreign": Sensor(_key="s_loc_foreign", name="H", metric_type="ec_ms", location_key="loc_foreign"),
        "s_orphan": Sensor(_key="s_orphan", name="?", metric_type="ec_ms"),
    }

    def get(self, key: str):
        return self._sensors.get(key)


class _Tanks:
    _tanks = {
        "tank_own": Tank(_key="tank_own", tenant_key=OWN, name="A", tank_type=TankType.NUTRIENT, volume_liters=1),
        "tank_foreign": Tank(
            _key="tank_foreign", tenant_key="t_b", name="B", tank_type=TankType.NUTRIENT, volume_liters=1
        ),
    }

    def get_by_key(self, key: str):
        return self._tanks.get(key)


class _Readings:
    def __init__(self) -> None:
        self.inserted: list = []

    def insert(self, reading) -> None:
        self.inserted.append(reading)

    def insert_batch(self, readings) -> int:
        self.inserted.extend(readings)
        return len(readings)


def _service(store: _Readings) -> ObservationService:
    return ObservationService(store, _Sensors(), tank_repo=_Tanks(), site_anchors=FakeSiteRepo())  # type: ignore[arg-type]


def _reading(sensor: str) -> SensorReading:
    return SensorReading(time=datetime.now(tz=UTC), tenant_key=OWN, sensor_key=sensor, sensor_type="ec", value=1.2)


@pytest.mark.parametrize("sensor", ["s_tank_foreign", "s_site_foreign", "s_loc_foreign", "s_orphan", "no-such-sensor"])
def test_a_reading_for_a_sensor_that_is_not_the_tenants_is_refused(sensor: str) -> None:
    store = _Readings()
    service = _service(store)

    with pytest.raises(NotFoundError):
        service.record_reading(_reading(sensor), tenant_key=OWN)
    with pytest.raises(NotFoundError):
        service.record_readings_batch(sensor, [_reading(sensor)], tenant_key=OWN)

    assert store.inserted == []


@pytest.mark.parametrize("sensor", ["s_tank_own", "s_site_own", "s_loc_own"])
def test_readings_for_an_own_sensor_are_recorded(sensor: str) -> None:
    store = _Readings()
    service = _service(store)

    service.record_reading(_reading(sensor), tenant_key=OWN)
    service.record_readings_batch(sensor, [_reading(sensor), _reading(sensor)], tenant_key=OWN)

    assert len(store.inserted) == 3
