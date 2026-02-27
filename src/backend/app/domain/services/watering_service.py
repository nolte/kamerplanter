from datetime import UTC, datetime

from app.common.enums import ApplicationMethod, ConfirmAction, ReminderType, TaskCategory, TaskStatus
from app.common.exceptions import NotFoundError
from app.common.types import LocationKey, SlotKey, WateringEventKey
from app.domain.engines.watering_engine import WateringEngine
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.interfaces.watering_repository import IWateringRepository
from app.domain.models.care_reminder import CareConfirmation
from app.domain.models.feeding_event import FeedingEvent
from app.domain.models.watering_event import WateringEvent


class WateringService:
    def __init__(
        self,
        repo: IWateringRepository,
        engine: WateringEngine,
        site_repo: ISiteRepository,
        run_repo=None,
        task_repo=None,
        feeding_repo=None,
        nutrient_plan_repo=None,
        care_repo=None,
    ) -> None:
        self._repo = repo
        self._engine = engine
        self._site_repo = site_repo
        self._run_repo = run_repo
        self._task_repo = task_repo
        self._feeding_repo = feeding_repo
        self._nutrient_plan_repo = nutrient_plan_repo
        self._care_repo = care_repo

    # ── Create ─────────────────────────────────────────────────────────

    def create_event(self, event: WateringEvent) -> dict:
        """Create a watering event and return it with any warnings."""
        # Look up irrigation system from the slot's location
        irrigation_system = None
        first_slot = self._site_repo.get_slot_by_key(event.slot_keys[0])
        if first_slot is not None:
            location = self._site_repo.get_location_by_key(first_slot.location_key)
            if location is not None:
                irrigation_system = location.irrigation_system

        warnings = self._engine.validate_and_warn(event, irrigation_system)
        created = self._repo.create(event)
        return {"event": created, "warnings": warnings}

    # ── Read ───────────────────────────────────────────────────────────

    def get_event(self, key: WateringEventKey) -> WateringEvent:
        event = self._repo.get_by_key(key)
        if event is None:
            raise NotFoundError("WateringEvent", key)
        return event

    def list_events(
        self, offset: int = 0, limit: int = 50,
    ) -> tuple[list[WateringEvent], int]:
        return self._repo.get_all(offset, limit)

    def get_by_slot(
        self, slot_key: SlotKey, offset: int = 0, limit: int = 50,
    ) -> list[WateringEvent]:
        return self._repo.get_by_slot(slot_key, offset, limit)

    def get_by_location(
        self, location_key: LocationKey, offset: int = 0, limit: int = 50,
    ) -> list[WateringEvent]:
        return self._repo.get_by_location(location_key, offset, limit)

    def get_stats(self, location_key: LocationKey) -> dict:
        return self._repo.get_stats_by_location(location_key)

    # ── Confirm / Quick-confirm ─────────────────────────────────────────

    def confirm_watering(
        self,
        run_key: str,
        task_key: str,
        measured_ec: float | None = None,
        measured_ph: float | None = None,
        volume_liters: float | None = None,
        overrides: dict | None = None,
    ) -> dict:
        """Confirm a scheduled watering task: create WateringEvent + FeedingEvents, complete task."""
        if self._run_repo is None or self._task_repo is None:
            raise ValueError("confirm_watering requires run_repo and task_repo")

        # Get run and plan info
        plan_key = self._run_repo.get_run_nutrient_plan_key(run_key)
        plan = None
        watering_schedule = None
        if plan_key and self._nutrient_plan_repo:
            plan = self._nutrient_plan_repo.get_by_key(plan_key)
            if plan and hasattr(plan, "watering_schedule"):
                watering_schedule = plan.watering_schedule

        # Get plants in the run
        plants = self._run_repo.get_run_plants(run_key, include_detached=False)
        slot_keys = list({p.get("slot_key", "") for p in plants if p.get("slot_key")})
        if not slot_keys:
            slot_keys = ["default"]

        # Create watering event
        now = datetime.now(UTC)
        event = WateringEvent(
            watered_at=now,
            application_method=watering_schedule.application_method if watering_schedule else ApplicationMethod.DRENCH,
            volume_liters=volume_liters or 1.0,
            slot_keys=slot_keys,
            nutrient_plan_key=plan_key,
            measured_ec=measured_ec,
            measured_ph=measured_ph,
            task_key=task_key,
        )
        created_event = self._repo.create(event)

        # Create feeding events for each plant
        feeding_events_created = 0
        if self._feeding_repo and plan:
            for plant in plants:
                plant_key = plant.get("_key", "")
                if plant_key:
                    method = (
                        watering_schedule.application_method
                        if watering_schedule
                        else ApplicationMethod.DRENCH
                    )
                    event_key = created_event.key if hasattr(created_event, "key") else None
                    feeding = FeedingEvent(
                        plant_key=plant_key,
                        timestamp=now,
                        application_method=method,
                        volume_applied_liters=volume_liters or 1.0,
                        watering_event_key=event_key,
                    )
                    self._feeding_repo.create(feeding)
                    feeding_events_created += 1

        # Complete the task
        task_completed = False
        task_doc = self._task_repo.get_by_key(task_key)
        if task_doc:
            self._task_repo.update_fields(task_key, {
                "status": TaskStatus.COMPLETED.value,
                "completed_at": now.isoformat(),
            })
            task_completed = True

        # Create care confirmation for each plant
        if self._care_repo:
            for plant in plants:
                plant_key = plant.get("_key", "")
                if plant_key:
                    confirmation = CareConfirmation(
                        plant_key=plant_key,
                        reminder_type=ReminderType.WATERING,
                        action=ConfirmAction.CONFIRMED,
                        confirmed_at=now,
                        task_key=task_key,
                    )
                    self._care_repo.create_confirmation(confirmation)

        return {
            "watering_event_key": created_event.key if hasattr(created_event, "key") else "",
            "feeding_events_created": feeding_events_created,
            "task_completed": task_completed,
            "warnings": [],
        }

    def quick_confirm_watering(self, run_key: str, task_key: str) -> dict:
        """Quick confirm using plan defaults — no overrides."""
        return self.confirm_watering(run_key, task_key)
