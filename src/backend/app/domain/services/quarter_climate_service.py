"""REQ-047 §3.7.3 / AC-22 — event-driven winter-quarter climate warning.

While a plant is in the dormancy-care mode (``CareProfile.dormancy_care_mode``),
this service compares the winter quarter's *live* temperature against the profile's
``winter_quarter_temp_min`` / ``winter_quarter_temp_max`` band and raises a HIGH
``quarter_climate_check`` care task the moment the band is violated — a heating
failure (too cold → the plant freezes) or overheating (too warm → premature
budding). This is the event-driven upgrade over the periodic AC-13 check.

The task is created through the shared care-reminder helpers
(:func:`build_care_reminder_task` + :meth:`ITaskRepository.find_open_care_task`), so
it is tenant-scoped and idempotent exactly like every other care reminder.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import structlog

from app.common.enums import ReminderType, TaskPriority
from app.domain.engines.care_reminder_engine import evaluate_quarter_climate_violation
from app.domain.services.care_reminder_service import build_care_reminder_task

if TYPE_CHECKING:
    from app.domain.interfaces.care_reminder_repository import ICareReminderRepository
    from app.domain.interfaces.observation_repository import IObservationRepository
    from app.domain.interfaces.overwintering_profile_repository import IOverwinteringProfileRepository
    from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
    from app.domain.interfaces.sensor_repository import ISensorRepository
    from app.domain.interfaces.task_repository import ITaskRepository
    from app.domain.models.task import Task

logger = structlog.get_logger(__name__)


class QuarterClimateService:
    def __init__(
        self,
        overwintering_repo: IOverwinteringProfileRepository,
        care_repo: ICareReminderRepository,
        sensor_repo: ISensorRepository,
        observation_repo: IObservationRepository,
        plant_repo: IPlantInstanceRepository,
        task_repo: ITaskRepository,
    ) -> None:
        self._overwintering_repo = overwintering_repo
        self._care_repo = care_repo
        self._sensor_repo = sensor_repo
        self._observation_repo = observation_repo
        self._plant_repo = plant_repo
        self._task_repo = task_repo

    def evaluate_plant(self, plant_key: str) -> Task | None:
        """Emit a HIGH ``quarter_climate_check`` task iff the quarter band is violated.

        Returns the created :class:`Task`, or ``None`` when the plant is not in
        dormancy-care, has no winter quarter / temperature band, the quarter carries
        no fresh temperature reading, the reading is inside the band, or an
        equivalent open task already exists (idempotent).
        """
        plant = self._plant_repo.get_by_key(plant_key)
        if plant is None:
            return None

        profile = self._overwintering_repo.get_profile_by_plant_key(plant_key)
        if profile is None or not profile.winter_quarter_key:
            return None
        if profile.winter_quarter_temp_min is None and profile.winter_quarter_temp_max is None:
            return None

        care = self._care_repo.get_profile_by_plant_key(plant_key)
        if care is None or not care.dormancy_care_mode:
            return None

        current_temp_c = self._latest_quarter_temp(profile.winter_quarter_key, plant.tenant_key)
        violation = evaluate_quarter_climate_violation(profile, current_temp_c)
        if violation is None:
            return None

        # Idempotent: never stack a second open quarter-climate task on the plant.
        if self._task_repo.find_open_care_task(plant_key, ReminderType.QUARTER_CLIMATE_CHECK, plant.tenant_key):
            return None

        plant_label = plant.plant_name or plant.instance_id or plant_key
        today = datetime.now(UTC)
        task = build_care_reminder_task(
            plant_key=plant_key,
            plant_label=plant_label,
            tenant_key=plant.tenant_key,
            reminder_type=ReminderType.QUARTER_CLIMATE_CHECK,
            due_date=today,
            instruction=self._instruction(plant_label, violation, current_temp_c, profile),
            priority=TaskPriority.HIGH,
        )
        created = self._task_repo.create_task(task)
        logger.info(
            "quarter_climate_violation",
            plant_key=plant_key,
            violation=violation,
            temperature_c=current_temp_c,
        )
        return created

    # ── Helpers ─────────────────────────────────────────────────────────

    def _latest_quarter_temp(self, location_key: str, tenant_key: str) -> float | None:
        """Freshest air-temperature reading at the winter quarter, or ``None``.

        Scans the sensors attached to the quarter location for an active
        temperature sensor (metric type mentions "temp", excluding water-temperature
        probes) and returns its latest observation value. Tenant-scoped through the
        observation repository so a foreign reading can never leak in.
        """
        sensors = self._sensor_repo.find_by_location(location_key)
        for sensor in sensors:
            if not sensor.is_active or not sensor.key or not self._is_air_temperature(sensor.metric_type):
                continue
            reading = self._observation_repo.get_latest(sensor.key, tenant_key)
            if reading is not None:
                return reading.value
        return None

    @staticmethod
    def _is_air_temperature(metric_type: str) -> bool:
        metric = metric_type.lower()
        return "temp" in metric and "water" not in metric

    @staticmethod
    def _instruction(plant_label: str, violation: str, temp_c: float | None, profile) -> str:  # noqa: ANN001
        reading = f"{temp_c:.1f} °C" if temp_c is not None else "unknown"
        if violation == "too_cold":
            bound = profile.winter_quarter_temp_min
            return (
                f"Winter quarter of {plant_label} is too cold ({reading}, below the {bound} °C minimum) — "
                "check the heating so the plant does not freeze."
            )
        bound = profile.winter_quarter_temp_max
        return (
            f"Winter quarter of {plant_label} is too warm ({reading}, above the {bound} °C maximum) — "
            "cool/ventilate it so the plant does not break dormancy prematurely."
        )
