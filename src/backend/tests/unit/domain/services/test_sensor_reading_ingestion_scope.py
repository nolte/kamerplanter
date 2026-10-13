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


# ── #1944: a sensor that is gone or on its way out takes no reading ───────────


class _Mutable(_Sensors):
    """The sensor store, with per-test sensors the test can remove or mark."""

    def __init__(self) -> None:
        self._sensors = dict(_Sensors._sensors)


class _Series(_Readings):
    """A readings store that records the purge and can run something between the check and the insert."""

    def __init__(self, before_insert=None) -> None:
        super().__init__()
        self.before_insert = before_insert
        self.purged: list[tuple[str, str]] = []

    def insert(self, reading) -> None:
        if self.before_insert is not None:
            self.before_insert()
        super().insert(reading)

    def insert_batch(self, readings) -> int:
        if self.before_insert is not None:
            self.before_insert()
        return super().insert_batch(readings)

    def delete_by_sensor(self, sensor_key: str, tenant_key: str) -> int:
        self.purged.append((sensor_key, tenant_key))
        return 0


def _racing(sensors: _Mutable, store: _Series) -> ObservationService:
    return ObservationService(store, sensors, tank_repo=_Tanks(), site_anchors=FakeSiteRepo())  # type: ignore[arg-type]


def test_a_reading_that_finds_its_sensor_gone_after_the_insert_is_purged_and_refused() -> None:
    sensors = _Mutable()
    store = _Series(before_insert=lambda: sensors._sensors.pop("s_site_own"))

    with pytest.raises(NotFoundError):
        _racing(sensors, store).record_reading(_reading("s_site_own"), tenant_key=OWN)

    assert store.purged == [("s_site_own", OWN)], "the row the reading just wrote must go with the series"


def test_a_batch_that_finds_its_sensor_gone_after_the_insert_is_purged_and_refused() -> None:
    sensors = _Mutable()
    store = _Series(before_insert=lambda: sensors._sensors.pop("s_tank_own"))

    with pytest.raises(NotFoundError):
        _racing(sensors, store).record_readings_batch("s_tank_own", [_reading("s_tank_own")], tenant_key=OWN)

    assert store.purged == [("s_tank_own", OWN)]


def test_a_reading_whose_sensor_stays_is_not_purged() -> None:
    sensors = _Mutable()
    store = _Series()

    _racing(sensors, store).record_reading(_reading("s_site_own"), tenant_key=OWN)

    assert (len(store.inserted), store.purged) == (1, [])


@pytest.mark.parametrize("sensor", ["s_tank_own", "s_site_own", "s_loc_own"])
def test_a_sensor_whose_delete_began_takes_no_reading(sensor: str) -> None:
    sensors = _Mutable()
    sensors._sensors[sensor] = sensors._sensors[sensor].model_copy(update={"deletion_pending": True})
    store = _Series()
    service = _racing(sensors, store)

    with pytest.raises(NotFoundError):
        service.record_reading(_reading(sensor), tenant_key=OWN)
    with pytest.raises(NotFoundError):
        service.record_readings_batch(sensor, [_reading(sensor)], tenant_key=OWN)

    assert store.inserted == []
    assert service.owning_tenant_key(sensor) is None


@pytest.mark.parametrize(
    ("sensor", "owner"),
    [
        ("s_tank_own", OWN),
        ("s_tank_foreign", "t_b"),
        ("s_site_own", OWN),
        ("s_loc_own", OWN),
        ("s_orphan", None),
        ("no-such-sensor", None),
    ],
)
def test_the_owner_of_a_sensor_is_its_parents_tenant(sensor: str, owner: str | None) -> None:
    """The Home Assistant poll stored every reading under ``''`` because a sensor document has no tenant_key."""
    assert _racing(_Mutable(), _Series()).owning_tenant_key(sensor) == owner
