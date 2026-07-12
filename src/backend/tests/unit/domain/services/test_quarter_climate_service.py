"""REQ-047 §3.7.3 / AC-22 — event-driven winter-quarter climate warning.

Covers the pure violation classifier, the care-engine gate (event-driven vs.
periodic fallback) and the :class:`QuarterClimateService` end-to-end over in-memory
fakes: a heating failure (too cold) / overheating (too warm) raises a single HIGH
``quarter_climate_check`` task, while a reading inside the band raises nothing.
"""

from datetime import UTC, datetime

from app.common.enums import (
    CareStyleType,
    HardinessRating,
    ReminderType,
    TaskPriority,
    WinterAction,
)
from app.domain.engines.care_reminder_engine import (
    CareReminderEngine,
    evaluate_quarter_climate_violation,
)
from app.domain.models.care_reminder import CareProfile
from app.domain.models.observation import SensorReading
from app.domain.models.overwintering_profile import OverwinteringProfile
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.sensor import Sensor
from app.domain.services.quarter_climate_service import QuarterClimateService

TENANT = "tenant-anna"


# ── Pure classifier ────────────────────────────────────────────────────────


def _profile(temp_min: float | None = 2.0, temp_max: float | None = 8.0) -> OverwinteringProfile:
    return OverwinteringProfile(
        plant_key="plant-1",
        hardiness_rating=HardinessRating.FROST_FREE,
        winter_action=WinterAction.MOVE_INDOORS,
        winter_action_month=10,
        winter_quarter_key="loc-quarter",
        winter_quarter_temp_min=temp_min,
        winter_quarter_temp_max=temp_max,
        tenant_key=TENANT,
    )


class TestViolationClassifier:
    def test_below_minimum_is_too_cold(self) -> None:
        assert evaluate_quarter_climate_violation(_profile(), -1.0) == "too_cold"

    def test_above_maximum_is_too_warm(self) -> None:
        assert evaluate_quarter_climate_violation(_profile(), 12.0) == "too_warm"

    def test_inside_band_is_none(self) -> None:
        assert evaluate_quarter_climate_violation(_profile(), 5.0) is None

    def test_missing_reading_is_none(self) -> None:
        assert evaluate_quarter_climate_violation(_profile(), None) is None

    def test_missing_bound_is_ignored(self) -> None:
        assert evaluate_quarter_climate_violation(_profile(temp_min=None), -20.0) is None


# ── Care-engine gate ────────────────────────────────────────────────────────


class TestQuarterClimateGate:
    def _care(self) -> CareProfile:
        return CareProfile(care_style=CareStyleType.OUTDOOR_PERENNIAL, plant_key="p1", dormancy_care_mode=True)

    def test_event_driven_violation_fires(self) -> None:
        engine = CareReminderEngine()
        assert engine.should_generate_reminder(
            self._care(),
            ReminderType.QUARTER_CLIMATE_CHECK,
            winter_quarter_temp_violation=True,
        )

    def test_event_driven_no_violation_suppresses(self) -> None:
        engine = CareReminderEngine()
        # Even with live data, an explicit no-violation blocks the reminder.
        assert not engine.should_generate_reminder(
            self._care(),
            ReminderType.QUARTER_CLIMATE_CHECK,
            winter_quarter_has_livedata=True,
            winter_quarter_temp_violation=False,
        )

    def test_periodic_fallback_when_no_violation_signal(self) -> None:
        engine = CareReminderEngine()
        assert engine.should_generate_reminder(
            self._care(),
            ReminderType.QUARTER_CLIMATE_CHECK,
            winter_quarter_has_livedata=True,
        )

    def test_not_in_dormancy_never_fires(self) -> None:
        engine = CareReminderEngine()
        care = CareProfile(care_style=CareStyleType.OUTDOOR_PERENNIAL, plant_key="p1", dormancy_care_mode=False)
        assert not engine.should_generate_reminder(
            care,
            ReminderType.QUARTER_CLIMATE_CHECK,
            winter_quarter_temp_violation=True,
        )


# ── Service end-to-end ───────────────────────────────────────────────────────


class _FakeOverwinteringRepo:
    def __init__(self, profile: OverwinteringProfile | None) -> None:
        self._profile = profile

    def get_profile_by_plant_key(self, plant_key):
        return self._profile


class _FakeCareRepo:
    def __init__(self, care: CareProfile | None) -> None:
        self._care = care

    def get_profile_by_plant_key(self, plant_key):
        return self._care


class _FakeSensorRepo:
    def __init__(self, sensors: list[Sensor]) -> None:
        self._sensors = sensors

    def find_by_location(self, location_key):
        return list(self._sensors)


class _FakeObservationRepo:
    def __init__(self, value: float | None) -> None:
        self._value = value

    def get_latest(self, sensor_key, tenant_key):
        if self._value is None:
            return None
        return SensorReading(
            time=datetime.now(UTC),
            tenant_key=tenant_key,
            sensor_key=sensor_key,
            sensor_type="air_temp_celsius",
            value=self._value,
        )


class _FakePlantRepo:
    def __init__(self, plant: PlantInstance | None) -> None:
        self._plant = plant

    def get_by_key(self, key):
        return self._plant


class _FakeTaskRepo:
    def __init__(self, existing_open: bool = False) -> None:
        self.created: list = []
        self._existing_open = existing_open

    def find_open_care_task(self, entity_key, reminder_type, tenant_key, *, include_completed_today=True):
        return object() if self._existing_open else None

    def create_task(self, task):
        self.created.append(task)
        return task


def _plant() -> PlantInstance:
    return PlantInstance(
        _key="plant-1",
        tenant_key=TENANT,
        instance_id="i1",
        species_key="species-1",
        planted_on=datetime(2024, 1, 1, tzinfo=UTC).date(),
        plant_name="Lemon tree",
    )


def _temp_sensor() -> Sensor:
    return Sensor(
        _key="sensor-temp",
        name="Quarter temp",
        metric_type="air_temp_celsius",
        location_key="loc-quarter",
        is_active=True,
    )


def _service(
    *,
    profile: OverwinteringProfile | None,
    care: CareProfile | None,
    sensors: list[Sensor],
    temp: float | None,
    plant: PlantInstance | None,
    existing_open: bool = False,
) -> tuple[QuarterClimateService, _FakeTaskRepo]:
    task_repo = _FakeTaskRepo(existing_open)
    service = QuarterClimateService(
        _FakeOverwinteringRepo(profile),
        _FakeCareRepo(care),
        _FakeSensorRepo(sensors),
        _FakeObservationRepo(temp),
        _FakePlantRepo(plant),
        task_repo,
    )
    return service, task_repo


def _dormant_care() -> CareProfile:
    return CareProfile(care_style=CareStyleType.OUTDOOR_PERENNIAL, plant_key="plant-1", dormancy_care_mode=True)


class TestQuarterClimateService:
    def test_too_cold_creates_high_task(self) -> None:
        service, task_repo = _service(
            profile=_profile(),
            care=_dormant_care(),
            sensors=[_temp_sensor()],
            temp=-2.0,
            plant=_plant(),
        )
        task = service.evaluate_plant("plant-1")

        assert task is not None
        assert task.priority == TaskPriority.HIGH
        assert task.entity_key == "plant-1"
        assert len(task_repo.created) == 1

    def test_reading_inside_band_creates_nothing(self) -> None:
        service, task_repo = _service(
            profile=_profile(),
            care=_dormant_care(),
            sensors=[_temp_sensor()],
            temp=5.0,
            plant=_plant(),
        )
        assert service.evaluate_plant("plant-1") is None
        assert task_repo.created == []

    def test_not_in_dormancy_creates_nothing(self) -> None:
        care = CareProfile(care_style=CareStyleType.OUTDOOR_PERENNIAL, plant_key="plant-1", dormancy_care_mode=False)
        service, task_repo = _service(
            profile=_profile(),
            care=care,
            sensors=[_temp_sensor()],
            temp=-5.0,
            plant=_plant(),
        )
        assert service.evaluate_plant("plant-1") is None
        assert task_repo.created == []

    def test_no_live_data_creates_nothing(self) -> None:
        service, task_repo = _service(
            profile=_profile(),
            care=_dormant_care(),
            sensors=[_temp_sensor()],
            temp=None,  # no reading
            plant=_plant(),
        )
        assert service.evaluate_plant("plant-1") is None
        assert task_repo.created == []

    def test_existing_open_task_is_not_duplicated(self) -> None:
        service, task_repo = _service(
            profile=_profile(),
            care=_dormant_care(),
            sensors=[_temp_sensor()],
            temp=-5.0,
            plant=_plant(),
            existing_open=True,
        )
        assert service.evaluate_plant("plant-1") is None
        assert task_repo.created == []

    def test_no_winter_quarter_creates_nothing(self) -> None:
        profile = _profile()
        profile = profile.model_copy(update={"winter_quarter_key": None})
        service, task_repo = _service(
            profile=profile,
            care=_dormant_care(),
            sensors=[_temp_sensor()],
            temp=-5.0,
            plant=_plant(),
        )
        assert service.evaluate_plant("plant-1") is None
        assert task_repo.created == []

    def test_water_temp_sensor_is_ignored(self) -> None:
        water_sensor = Sensor(
            name="Tank temp", metric_type="water_temp_celsius", location_key="loc-quarter", is_active=True
        )
        service, task_repo = _service(
            profile=_profile(),
            care=_dormant_care(),
            sensors=[water_sensor],
            temp=-5.0,
            plant=_plant(),
        )
        # No air-temperature sensor → no reading resolved → no task.
        assert service.evaluate_plant("plant-1") is None
        assert task_repo.created == []
