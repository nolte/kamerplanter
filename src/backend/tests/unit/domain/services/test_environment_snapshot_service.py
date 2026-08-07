"""REQ-013 §2.3a — the environment snapshot resolved for a diary entry.

The chain is the REQ-005 one (location → site → weather → nothing), and the
tests below pin each level, the per-metric fallback between them, the staleness
bound, tenant isolation, and — most importantly — every way the capture is
allowed to fail. A capture that fails is never allowed to fail the *write*, so
"it degraded" is a first-class outcome here rather than an error path.
"""

from __future__ import annotations

import time
from datetime import UTC, date, datetime, timedelta

import pytest

from app.common.enums import DiaryEnvironmentOrigin, DiaryEnvironmentStatus
from app.domain.models.observation import SensorReading
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.sensor import Sensor
from app.domain.models.site import Site
from app.domain.models.weather import WeatherForecast
from app.domain.services.environment_snapshot_service import EnvironmentSnapshotService
from app.domain.services.sensor_service import SensorService

TENANT = "tenant-a"
FOREIGN_TENANT = "tenant-b"
PLANT = "plant-1"
LOCATION = "loc-1"
SITE = "site-1"

NOW = datetime(2026, 8, 3, 18, 22, 11, tzinfo=UTC)


def _iso(moment: datetime) -> str:
    return moment.isoformat().replace("+00:00", "Z")


# ── Doubles ──────────────────────────────────────────────────────────────────


class FakePlantRepo:
    def __init__(self, plants: dict[str, PlantInstance]) -> None:
        self.plants = plants

    def get_by_key(self, key: str) -> PlantInstance | None:
        return self.plants.get(key)


class FakeSensorRepo:
    def __init__(
        self,
        by_location: dict[str, list[Sensor]] | None = None,
        by_site: dict[str, list[Sensor]] | None = None,
    ) -> None:
        self._by_location = by_location or {}
        self._by_site = by_site or {}

    def find_by_location(self, location_key: str) -> list[Sensor]:
        return list(self._by_location.get(location_key, []))

    def find_by_site(self, site_key: str) -> list[Sensor]:
        return list(self._by_site.get(site_key, []))


class FakeHaClient:
    """Answers ``get_state`` from a canned map, and can be told to misbehave."""

    def __init__(self, states: dict[str, dict], *, raises: set[str] | None = None, delay: float = 0.0) -> None:
        self.states = states
        self.raises = raises or set()
        self.delay = delay
        self.calls: list[tuple[str, float | None]] = []

    def get_state(self, entity_id: str, *, timeout: float | None = None) -> dict | None:
        self.calls.append((entity_id, timeout))
        if self.delay:
            time.sleep(self.delay)
        if entity_id in self.raises:
            raise RuntimeError("Home Assistant unreachable")
        return self.states.get(entity_id)


class FakeObservationRepo:
    def __init__(self, latest: dict[tuple[str, str], SensorReading] | None = None, *, raises: bool = False) -> None:
        self._latest = latest or {}
        self._raises = raises

    def get_latest(self, sensor_key: str, tenant_key: str) -> SensorReading | None:
        if self._raises:
            raise RuntimeError("TimescaleDB down")
        return self._latest.get((sensor_key, tenant_key))


class FakeWeatherRepo:
    def __init__(self, by_site: dict[str, list[WeatherForecast]] | None = None, *, raises: bool = False) -> None:
        self._by_site = by_site or {}
        self._raises = raises

    def find_by_site(self, site_key: str, tenant_key: str) -> list[WeatherForecast]:
        if self._raises:
            raise RuntimeError("ArangoDB down")
        return [r for r in self._by_site.get(site_key, []) if r.tenant_key == tenant_key]


class FakeSiteRepo:
    def __init__(self, sites: dict[str, Site]) -> None:
        self._sites = sites

    def get_site_by_key(self, key: str) -> Site | None:
        return self._sites.get(key)


# ── Builders ─────────────────────────────────────────────────────────────────


def _plant(
    *,
    tenant_key: str = TENANT,
    location_key: str | None = LOCATION,
    site_key: str | None = SITE,
) -> PlantInstance:
    return PlantInstance(
        _key=PLANT,
        tenant_key=tenant_key,
        instance_id="P-1",
        species_key="solanum_lycopersicum",
        plant_name="Tomate",
        planted_on=date(2026, 4, 18),
        site_key=site_key,
        location_key=location_key,
        slot_key="slot-9",
    )


def _sensor(key: str, metric_type: str, *, entity: str | None = None, **kwargs) -> Sensor:
    return Sensor(
        _key=key,
        name=f"Sensor {key}",
        metric_type=metric_type,
        ha_entity_id=entity,
        **kwargs,
    )


def _live(value: float, *, entity: str, unit: str | None = "°C", age_minutes: float = 1.0) -> dict:
    return {
        "value": value,
        "last_changed": _iso(NOW - timedelta(days=1)),
        "last_updated": _iso(NOW - timedelta(days=1)),
        "last_reported": _iso(NOW - timedelta(minutes=age_minutes)),
        "entity_id": entity,
        "unit": unit,
    }


def _current_weather(
    *,
    temp: float | None = 24.0,
    humidity: float | None = 58.0,
    tenant_key: str = TENANT,
    age_minutes: float = 5.0,
    source: str = "open-meteo",
) -> WeatherForecast:
    return WeatherForecast(
        tenant_key=tenant_key,
        site_key=SITE,
        forecast_date=NOW.date(),
        temp_min_c=temp,
        temp_max_c=temp,
        humidity_percent=humidity,
        source=source,
        fetched_at=NOW - timedelta(minutes=age_minutes),
        data_kind="observed",
        is_current_conditions=True,
    )


def _build(
    *,
    plants: dict[str, PlantInstance] | None = None,
    location_sensors: list[Sensor] | None = None,
    site_sensors: list[Sensor] | None = None,
    ha: FakeHaClient | None = None,
    observations: FakeObservationRepo | None = None,
    weather: FakeWeatherRepo | None = None,
    sites: dict[str, Site] | None = None,
) -> EnvironmentSnapshotService:
    sensor_repo = FakeSensorRepo(
        by_location={LOCATION: location_sensors or []},
        by_site={SITE: site_sensors or []},
    )
    return EnvironmentSnapshotService(
        plant_repo=FakePlantRepo(plants or {PLANT: _plant()}),
        sensor_repo=sensor_repo,
        sensor_service=SensorService(sensor_repo, ha),
        observation_repo=observations,
        weather_forecast_repo=weather,
        site_repo=FakeSiteRepo(sites if sites is not None else {SITE: Site(_key=SITE, tenant_key=TENANT, name="Beet")}),
    )


@pytest.fixture(autouse=True)
def _frozen_now(monkeypatch):
    """Pin "now" so the staleness bound is testable without sleeping."""
    monkeypatch.setattr("app.domain.services.environment_snapshot_service.now_utc", lambda: NOW)


@pytest.fixture(autouse=True)
def _capture_settings(monkeypatch):
    monkeypatch.setattr(
        "app.domain.services.environment_snapshot_service.settings.diary_environment_capture_enabled",
        True,
    )
    monkeypatch.setattr(
        "app.domain.services.environment_snapshot_service.settings.diary_environment_max_age_minutes",
        60,
    )
    monkeypatch.setattr(
        "app.domain.services.environment_snapshot_service.settings.diary_environment_capture_timeout_seconds",
        3.0,
    )
    monkeypatch.setattr(
        "app.domain.services.environment_snapshot_service.settings.weather_enabled",
        True,
    )


# ── Level 1: the plant's own location ────────────────────────────────────────


class TestLocationLevel:
    def test_temperature_and_humidity_are_captured_with_provenance(self):
        service = _build(
            location_sensors=[
                _sensor("s-temp", "temperature_celsius", entity="sensor.zelt_temp"),
                _sensor("s-hum", "humidity_percent", entity="sensor.zelt_hum"),
            ],
            ha=FakeHaClient(
                {
                    "sensor.zelt_temp": _live(31.2, entity="sensor.zelt_temp"),
                    "sensor.zelt_hum": _live(28.0, entity="sensor.zelt_hum", unit="%"),
                }
            ),
        )

        snapshot = service.capture_for_plant(PLANT, tenant_key=TENANT)

        assert snapshot.status is DiaryEnvironmentStatus.CAPTURED
        assert snapshot.captured_at == NOW
        by_metric = {r.metric_type: r for r in snapshot.readings}
        assert set(by_metric) == {"temperature_celsius", "humidity_percent"}
        temp = by_metric["temperature_celsius"]
        assert temp.value == 31.2
        assert temp.unit == "°C"
        assert temp.source == "ha_auto"
        assert temp.sensor_key == "s-temp"
        assert temp.origin is DiaryEnvironmentOrigin.LOCATION
        # AK: ``measured_at`` is the reading's own instant, not the capture's.
        assert temp.measured_at == NOW - timedelta(minutes=1)
        assert temp.measured_at < snapshot.captured_at

    def test_inactive_sensor_is_ignored(self):
        service = _build(
            location_sensors=[_sensor("s-temp", "temperature_celsius", entity="sensor.t", is_active=False)],
            ha=FakeHaClient({"sensor.t": _live(21.0, entity="sensor.t")}),
        )

        snapshot = service.capture_for_plant(PLANT, tenant_key=TENANT)

        assert snapshot.readings == []
        assert snapshot.status is DiaryEnvironmentStatus.NO_SOURCE

    def test_every_metric_is_captured_not_just_a_curated_set(self):
        # There is no allow-list: a CO2 probe on the plant's location is part of
        # the environment the plant is standing in, and dropping it would waste
        # the one datum the grower actually paid for.
        service = _build(
            location_sensors=[_sensor("s-co2", "co2_ppm", entity="sensor.co2")],
            ha=FakeHaClient({"sensor.co2": _live(1180.0, entity="sensor.co2", unit="ppm")}),
        )

        snapshot = service.capture_for_plant(PLANT, tenant_key=TENANT)

        assert [(r.metric_type, r.value, r.unit) for r in snapshot.readings] == [("co2_ppm", 1180.0, "ppm")]

    def test_two_sensors_of_one_metric_yield_one_reading(self):
        service = _build(
            location_sensors=[
                _sensor("s-a", "temperature_celsius", entity="sensor.a"),
                _sensor("s-b", "temperature_celsius", entity="sensor.b"),
            ],
            ha=FakeHaClient(
                {
                    "sensor.a": _live(21.0, entity="sensor.a"),
                    "sensor.b": _live(23.0, entity="sensor.b"),
                }
            ),
        )

        snapshot = service.capture_for_plant(PLANT, tenant_key=TENANT)

        assert len(snapshot.readings) == 1


class TestPersistedObservationFallback:
    def test_unavailable_live_state_falls_back_to_the_stored_reading(self):
        # Home Assistant reports ``unavailable`` as a non-numeric state, which
        # ``get_live_state_for_sensors`` drops — the entry must still get a value.
        service = _build(
            location_sensors=[_sensor("s-temp", "temperature_celsius", entity="sensor.t")],
            ha=FakeHaClient({"sensor.t": {"value": None, "last_reported": _iso(NOW), "entity_id": "sensor.t"}}),
            observations=FakeObservationRepo(
                {
                    ("s-temp", TENANT): SensorReading(
                        time=NOW - timedelta(minutes=12),
                        tenant_key=TENANT,
                        sensor_key="s-temp",
                        sensor_type="temperature_celsius",
                        value=19.4,
                        unit="°C",
                        source="mqtt_auto",
                    )
                }
            ),
        )

        snapshot = service.capture_for_plant(PLANT, tenant_key=TENANT)

        assert snapshot.status is DiaryEnvironmentStatus.CAPTURED
        reading = snapshot.readings[0]
        assert reading.value == 19.4
        # The stored provenance verbatim: promoting a ``manual``/``mqtt_auto``
        # reading to ``ha_auto`` because it came out of the time series is exactly
        # the provenance loss this feature exists to prevent (REQ-005 §1).
        assert reading.source == "mqtt_auto"
        assert reading.measured_at == NOW - timedelta(minutes=12)

    def test_home_assistant_not_configured_is_not_a_failure(self):
        # ``ha_client=None`` is a perfectly ordinary deployment. It must read as
        # "captured from the time series", never as "the capture broke".
        service = _build(
            location_sensors=[_sensor("s-temp", "temperature_celsius")],
            ha=None,
            observations=FakeObservationRepo(
                {
                    ("s-temp", TENANT): SensorReading(
                        time=NOW - timedelta(minutes=3),
                        tenant_key=TENANT,
                        sensor_key="s-temp",
                        sensor_type="temperature_celsius",
                        value=20.1,
                        source="manual",
                    )
                }
            ),
        )

        snapshot = service.capture_for_plant(PLANT, tenant_key=TENANT)

        assert snapshot.status is DiaryEnvironmentStatus.CAPTURED
        assert snapshot.readings[0].source == "manual"

    def test_no_timeseries_repository_still_produces_a_clean_answer(self):
        service = _build(
            location_sensors=[_sensor("s-temp", "temperature_celsius")],
            ha=None,
            observations=None,
        )

        snapshot = service.capture_for_plant(PLANT, tenant_key=TENANT)

        assert snapshot.status is DiaryEnvironmentStatus.NO_SOURCE
        assert snapshot.readings == []


# ── Staleness ────────────────────────────────────────────────────────────────


class TestStalenessBound:
    def test_live_reading_older_than_the_bound_is_not_captured(self):
        service = _build(
            location_sensors=[_sensor("s-temp", "temperature_celsius", entity="sensor.t")],
            ha=FakeHaClient({"sensor.t": _live(22.0, entity="sensor.t", age_minutes=61)}),
        )

        snapshot = service.capture_for_plant(PLANT, tenant_key=TENANT)

        assert snapshot.readings == []
        assert snapshot.status is DiaryEnvironmentStatus.NO_SOURCE

    def test_stored_reading_older_than_the_bound_is_not_captured(self):
        service = _build(
            location_sensors=[_sensor("s-temp", "temperature_celsius")],
            ha=None,
            observations=FakeObservationRepo(
                {
                    ("s-temp", TENANT): SensorReading(
                        time=NOW - timedelta(hours=26),
                        tenant_key=TENANT,
                        sensor_key="s-temp",
                        sensor_type="temperature_celsius",
                        value=22.0,
                        source="ha_auto",
                    )
                }
            ),
        )

        snapshot = service.capture_for_plant(PLANT, tenant_key=TENANT)

        assert snapshot.readings == []

    def test_freshness_comes_from_last_reported_not_last_changed(self):
        # A healthy sensor reporting a constant 22.0 °C keeps a ``last_changed``
        # that is hours old. Judging it by that would drop every stable reading —
        # exactly the values a climate snapshot most wants.
        service = _build(
            location_sensors=[_sensor("s-temp", "temperature_celsius", entity="sensor.t")],
            ha=FakeHaClient(
                {
                    "sensor.t": {
                        "value": 22.0,
                        "last_changed": _iso(NOW - timedelta(hours=9)),
                        "last_updated": _iso(NOW - timedelta(hours=9)),
                        "last_reported": _iso(NOW - timedelta(seconds=30)),
                        "entity_id": "sensor.t",
                        "unit": "°C",
                    }
                }
            ),
        )

        snapshot = service.capture_for_plant(PLANT, tenant_key=TENANT)

        assert [r.value for r in snapshot.readings] == [22.0]
        assert snapshot.readings[0].measured_at == NOW - timedelta(seconds=30)

    def test_a_reading_without_any_timestamp_is_not_captured(self):
        # Unfalsifiable freshness. Treating it as "now" is the one thing the
        # bound exists to prevent.
        service = _build(
            location_sensors=[_sensor("s-temp", "temperature_celsius", entity="sensor.t")],
            ha=FakeHaClient({"sensor.t": {"value": 22.0, "entity_id": "sensor.t", "unit": "°C"}}),
        )

        snapshot = service.capture_for_plant(PLANT, tenant_key=TENANT)

        assert snapshot.readings == []


# ── Level 2: the site ────────────────────────────────────────────────────────


class TestSiteLevel:
    def test_site_sensor_answers_when_the_location_has_none(self):
        service = _build(
            location_sensors=[],
            site_sensors=[_sensor("s-site", "temperature_celsius", entity="sensor.site")],
            ha=FakeHaClient({"sensor.site": _live(17.5, entity="sensor.site")}),
        )

        snapshot = service.capture_for_plant(PLANT, tenant_key=TENANT)

        assert [r.origin for r in snapshot.readings] == [DiaryEnvironmentOrigin.SITE]
        assert snapshot.readings[0].value == 17.5

    def test_fallback_is_per_metric_not_per_level(self):
        # The location covers temperature, the site covers humidity: REQ-005 §2's
        # chain is walked per metric, so the entry gets both.
        service = _build(
            location_sensors=[_sensor("s-temp", "temperature_celsius", entity="sensor.lt")],
            site_sensors=[
                _sensor("s-site-temp", "temperature_celsius", entity="sensor.st"),
                _sensor("s-site-hum", "humidity_percent", entity="sensor.sh"),
            ],
            ha=FakeHaClient(
                {
                    "sensor.lt": _live(24.0, entity="sensor.lt"),
                    "sensor.st": _live(11.0, entity="sensor.st"),
                    "sensor.sh": _live(64.0, entity="sensor.sh", unit="%"),
                }
            ),
        )

        snapshot = service.capture_for_plant(PLANT, tenant_key=TENANT)

        by_metric = {r.metric_type: r for r in snapshot.readings}
        # The closer level wins for the metric it answers …
        assert by_metric["temperature_celsius"].origin is DiaryEnvironmentOrigin.LOCATION
        assert by_metric["temperature_celsius"].value == 24.0
        # … and the site still contributes the one it does not.
        assert by_metric["humidity_percent"].origin is DiaryEnvironmentOrigin.SITE

    def test_a_plant_without_a_location_starts_at_the_site(self):
        # A slot has no sensor level of its own — ``Sensor`` cannot attach to one.
        service = _build(
            plants={PLANT: _plant(location_key=None)},
            site_sensors=[_sensor("s-site", "temperature_celsius", entity="sensor.site")],
            ha=FakeHaClient({"sensor.site": _live(17.5, entity="sensor.site")}),
        )

        snapshot = service.capture_for_plant(PLANT, tenant_key=TENANT)

        assert [r.origin for r in snapshot.readings] == [DiaryEnvironmentOrigin.SITE]


# ── Level 3: current outdoor conditions ──────────────────────────────────────


class TestWeatherLevel:
    def test_current_conditions_fill_temperature_and_humidity(self):
        service = _build(weather=FakeWeatherRepo({SITE: [_current_weather()]}))

        snapshot = service.capture_for_plant(PLANT, tenant_key=TENANT)

        assert snapshot.status is DiaryEnvironmentStatus.CAPTURED
        by_metric = {r.metric_type: r for r in snapshot.readings}
        assert by_metric["temperature_celsius"].value == 24.0
        assert by_metric["temperature_celsius"].origin is DiaryEnvironmentOrigin.WEATHER
        # The adapter's own name, verbatim: "which service said so" is not
        # recoverable from the REQ-005 ``weather_api`` class alone (REQ-046).
        assert by_metric["temperature_celsius"].source == "open-meteo"
        assert by_metric["temperature_celsius"].sensor_key is None
        assert by_metric["humidity_percent"].value == 58.0

    def test_weather_only_fills_metrics_no_sensor_answered(self):
        service = _build(
            location_sensors=[_sensor("s-temp", "temperature_celsius", entity="sensor.t")],
            ha=FakeHaClient({"sensor.t": _live(26.0, entity="sensor.t")}),
            weather=FakeWeatherRepo({SITE: [_current_weather()]}),
        )

        snapshot = service.capture_for_plant(PLANT, tenant_key=TENANT)

        by_metric = {r.metric_type: r for r in snapshot.readings}
        assert by_metric["temperature_celsius"].origin is DiaryEnvironmentOrigin.LOCATION
        assert by_metric["humidity_percent"].origin is DiaryEnvironmentOrigin.WEATHER

    def test_forecast_records_are_not_current_conditions(self):
        forecast = _current_weather()
        forecast.is_current_conditions = False

        service = _build(weather=FakeWeatherRepo({SITE: [forecast]}))

        snapshot = service.capture_for_plant(PLANT, tenant_key=TENANT)

        assert snapshot.readings == []
        assert snapshot.status is DiaryEnvironmentStatus.NO_SOURCE

    def test_stale_weather_record_is_not_captured(self):
        service = _build(weather=FakeWeatherRepo({SITE: [_current_weather(age_minutes=180)]}))

        snapshot = service.capture_for_plant(PLANT, tenant_key=TENANT)

        assert snapshot.readings == []

    def test_weather_disabled_skips_the_level(self, monkeypatch):
        monkeypatch.setattr(
            "app.domain.services.environment_snapshot_service.settings.weather_enabled",
            False,
        )
        service = _build(weather=FakeWeatherRepo({SITE: [_current_weather()]}))

        snapshot = service.capture_for_plant(PLANT, tenant_key=TENANT)

        assert snapshot.readings == []


# ── Level 4: nothing ─────────────────────────────────────────────────────────


class TestNoSource:
    def test_a_plant_nothing_covers_yields_an_empty_captured_snapshot(self):
        service = _build()

        snapshot = service.capture_for_plant(PLANT, tenant_key=TENANT)

        assert snapshot.readings == []
        # ``no_source`` and not ``unavailable``: the chain ran and the honest
        # answer is that nothing measures this plant. No fabricated 0.0.
        assert snapshot.status is DiaryEnvironmentStatus.NO_SOURCE
        assert snapshot.captured_at == NOW

    def test_a_plant_with_neither_site_nor_location(self):
        service = _build(plants={PLANT: _plant(location_key=None, site_key=None)})

        snapshot = service.capture_for_plant(PLANT, tenant_key=TENANT)

        assert snapshot.status is DiaryEnvironmentStatus.NO_SOURCE


# ── Failure behaviour ────────────────────────────────────────────────────────


class TestDegradedCapture:
    def test_home_assistant_error_is_reported_as_unavailable(self):
        service = _build(
            location_sensors=[_sensor("s-temp", "temperature_celsius", entity="sensor.t")],
            ha=FakeHaClient({}, raises={"sensor.t"}),
        )

        snapshot = service.capture_for_plant(PLANT, tenant_key=TENANT)

        # Distinguishable from ``no_source``: nothing here says the plant is
        # unmonitored, only that we could not reach the monitor.
        assert snapshot.status is DiaryEnvironmentStatus.UNAVAILABLE
        assert snapshot.readings == []

    def test_a_partial_failure_keeps_what_did_answer(self):
        service = _build(
            location_sensors=[
                _sensor("s-temp", "temperature_celsius", entity="sensor.t"),
                _sensor("s-hum", "humidity_percent", entity="sensor.h"),
            ],
            ha=FakeHaClient({"sensor.t": _live(25.0, entity="sensor.t")}, raises={"sensor.h"}),
        )

        snapshot = service.capture_for_plant(PLANT, tenant_key=TENANT)

        assert snapshot.status is DiaryEnvironmentStatus.UNAVAILABLE
        # A non-empty list under ``unavailable`` is what "partial" looks like.
        assert [r.metric_type for r in snapshot.readings] == ["temperature_celsius"]

    def test_observation_repository_failure_degrades_but_does_not_raise(self):
        service = _build(
            location_sensors=[_sensor("s-temp", "temperature_celsius")],
            ha=None,
            observations=FakeObservationRepo(raises=True),
        )

        snapshot = service.capture_for_plant(PLANT, tenant_key=TENANT)

        assert snapshot.status is DiaryEnvironmentStatus.UNAVAILABLE

    def test_weather_repository_failure_degrades_but_does_not_raise(self):
        service = _build(weather=FakeWeatherRepo(raises=True))

        snapshot = service.capture_for_plant(PLANT, tenant_key=TENANT)

        assert snapshot.status is DiaryEnvironmentStatus.UNAVAILABLE

    def test_an_unknown_plant_degrades_instead_of_raising(self):
        service = _build(plants={})

        snapshot = service.capture_for_plant("no-such-plant", tenant_key=TENANT)

        assert snapshot.status is DiaryEnvironmentStatus.UNAVAILABLE
        assert snapshot.readings == []

    def test_capture_disabled_is_not_attempted(self, monkeypatch):
        monkeypatch.setattr(
            "app.domain.services.environment_snapshot_service.settings.diary_environment_capture_enabled",
            False,
        )
        service = _build(
            location_sensors=[_sensor("s-temp", "temperature_celsius", entity="sensor.t")],
            ha=FakeHaClient({"sensor.t": _live(22.0, entity="sensor.t")}),
        )

        snapshot = service.capture_for_plant(PLANT, tenant_key=TENANT)

        assert snapshot.status is DiaryEnvironmentStatus.NOT_ATTEMPTED
        assert snapshot.captured_at is None


class TestLatencyBudget:
    def test_the_capture_stays_inside_its_budget(self, monkeypatch):
        monkeypatch.setattr(
            "app.domain.services.environment_snapshot_service.settings.diary_environment_capture_timeout_seconds",
            0.2,
        )
        ha = FakeHaClient(
            {f"sensor.{i}": _live(20.0, entity=f"sensor.{i}") for i in range(6)},
            delay=0.05,
        )
        service = _build(
            location_sensors=[_sensor(f"s-{i}", f"metric_{i}", entity=f"sensor.{i}") for i in range(6)],
            ha=ha,
        )

        started = time.monotonic()
        snapshot = service.capture_for_plant(PLANT, tenant_key=TENANT)
        elapsed = time.monotonic() - started

        # The budget is a wall-clock ceiling on the whole capture, not a per-call
        # timeout: six 50 ms entities would take 300 ms unbounded.
        assert elapsed < 0.35
        assert snapshot.status is DiaryEnvironmentStatus.UNAVAILABLE
        # Whatever arrived in time is kept — the create path is not punished for
        # a slow sensor by losing the fast ones too.
        assert snapshot.readings

    def test_the_persisted_fallback_is_bounded_too(self, monkeypatch):
        # The time-series read is only *usually* local. A budget that covered
        # only the Home Assistant half would be a ceiling with a hole in it.
        monkeypatch.setattr(
            "app.domain.services.environment_snapshot_service.settings.diary_environment_capture_timeout_seconds",
            0.05,
        )

        class SlowObservationRepo(FakeObservationRepo):
            def get_latest(self, sensor_key: str, tenant_key: str):
                time.sleep(0.05)
                return super().get_latest(sensor_key, tenant_key)

        latest = {
            (f"s-{i}", TENANT): SensorReading(
                time=NOW,
                tenant_key=TENANT,
                sensor_key=f"s-{i}",
                sensor_type=f"metric_{i}",
                value=20.0,
                source="ha_auto",
            )
            for i in range(8)
        }
        service = _build(
            location_sensors=[_sensor(f"s-{i}", f"metric_{i}") for i in range(8)],
            ha=None,
            observations=SlowObservationRepo(latest),
        )

        started = time.monotonic()
        snapshot = service.capture_for_plant(PLANT, tenant_key=TENANT)
        elapsed = time.monotonic() - started

        # Eight 50 ms reads would be 400 ms unbounded.
        assert elapsed < 0.25
        assert snapshot.status is DiaryEnvironmentStatus.UNAVAILABLE

    def test_each_outbound_call_is_capped_by_the_remaining_budget(self):
        ha = FakeHaClient({"sensor.t": _live(22.0, entity="sensor.t")})
        service = _build(
            location_sensors=[_sensor("s-temp", "temperature_celsius", entity="sensor.t")],
            ha=ha,
        )

        service.capture_for_plant(PLANT, tenant_key=TENANT)

        assert len(ha.calls) == 1
        _entity, timeout = ha.calls[0]
        assert timeout is not None
        assert 0 < timeout <= 3.0


# ── Tenant isolation ─────────────────────────────────────────────────────────


class TestTenantIsolation:
    def test_a_foreign_plant_never_yields_readings(self):
        service = _build(
            plants={PLANT: _plant(tenant_key=FOREIGN_TENANT)},
            location_sensors=[_sensor("s-temp", "temperature_celsius", entity="sensor.t")],
            ha=FakeHaClient({"sensor.t": _live(22.0, entity="sensor.t")}),
        )

        snapshot = service.capture_for_plant(PLANT, tenant_key=TENANT)

        assert snapshot.readings == []
        assert snapshot.status is DiaryEnvironmentStatus.UNAVAILABLE

    def test_observation_reads_are_scoped_to_the_callers_tenant(self):
        # The stored reading exists — under the *other* tenant's key. A repository
        # keyed only by ``sensor_key`` would hand it over.
        service = _build(
            location_sensors=[_sensor("s-temp", "temperature_celsius")],
            ha=None,
            observations=FakeObservationRepo(
                {
                    ("s-temp", FOREIGN_TENANT): SensorReading(
                        time=NOW,
                        tenant_key=FOREIGN_TENANT,
                        sensor_key="s-temp",
                        sensor_type="temperature_celsius",
                        value=99.0,
                        source="ha_auto",
                    )
                }
            ),
        )

        snapshot = service.capture_for_plant(PLANT, tenant_key=TENANT)

        assert snapshot.readings == []

    def test_a_site_of_another_tenant_contributes_no_weather(self):
        service = _build(
            weather=FakeWeatherRepo({SITE: [_current_weather(tenant_key=FOREIGN_TENANT)]}),
            sites={SITE: Site(_key=SITE, tenant_key=FOREIGN_TENANT, name="Fremdes Beet")},
        )

        snapshot = service.capture_for_plant(PLANT, tenant_key=TENANT)

        assert snapshot.readings == []
