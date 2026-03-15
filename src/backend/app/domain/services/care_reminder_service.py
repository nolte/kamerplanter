from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.common.enums import ApplicationMethod, ConfirmAction, ReminderType, TaskCategory, TaskPriority, TaskStatus
from app.common.exceptions import NotFoundError
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.interfaces.care_reminder_repository import ICareReminderRepository
from app.domain.models.care_reminder import CareConfirmation, CareDashboardEntry, CareProfile
from app.domain.models.task import Task
from app.domain.models.watering_log import WateringLog, WateringLogFertilizer

if TYPE_CHECKING:
    from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
    from app.domain.interfaces.task_repository import ITaskRepository
    from app.domain.interfaces.watering_log_repository import IWateringLogRepository


class CareReminderService:
    def __init__(
        self,
        care_repo: ICareReminderRepository,
        engine: CareReminderEngine,
        task_repo: "ITaskRepository | None" = None,
        watering_log_repo: "IWateringLogRepository | None" = None,
        plant_repo: "IPlantInstanceRepository | None" = None,
    ) -> None:
        self._repo = care_repo
        self._engine = engine
        self._task_repo = task_repo
        self._watering_log_repo = watering_log_repo
        self._plant_repo = plant_repo

    def get_or_create_profile(
        self,
        plant_key: str,
        species_name: str | None = None,
        botanical_family: str | None = None,
    ) -> CareProfile:
        """Get existing profile or auto-generate one."""
        profile = self._repo.get_profile_by_plant_key(plant_key)
        if profile is not None:
            return profile

        new_profile = self._engine.auto_generate_profile(
            species_name=species_name,
            botanical_family=botanical_family,
            plant_key=plant_key,
        )
        created = self._repo.create_profile(new_profile)
        if created.key:
            self._repo.create_profile_edge(plant_key, created.key)
        return created

    def update_profile(self, plant_key: str, updates: dict) -> CareProfile:
        profile = self._repo.get_profile_by_plant_key(plant_key)
        if profile is None:
            raise NotFoundError("CareProfile", plant_key)

        data = profile.model_dump()
        data.update(updates)
        updated = CareProfile(**data)
        return self._repo.update_profile(profile.key or "", updated)

    def confirm_reminder(
        self,
        plant_key: str,
        reminder_type: ReminderType,
        notes: str | None = None,
        *,
        volume_liters: float | None = None,
        fertilizers_used: list[dict] | None = None,
        measured_ec: float | None = None,
        measured_ph: float | None = None,
    ) -> CareConfirmation:
        profile = self._repo.get_profile_by_plant_key(plant_key)
        if profile is None:
            profile = self.get_or_create_profile(plant_key)

        now = datetime.now(UTC)
        watering_log_key: str | None = None
        is_feeding_type = reminder_type in (ReminderType.WATERING, ReminderType.FERTILIZING)
        effective_volume = volume_liters or 1.0

        # Create a single WateringLog for watering/fertilizing confirmations
        if is_feeding_type and self._watering_log_repo is not None:
            slot_keys = self._resolve_slot_keys(plant_key)
            ferts = [
                WateringLogFertilizer(
                    fertilizer_key=f["fertilizer_key"],
                    ml_per_liter=f["ml_applied"],
                )
                for f in (fertilizers_used or [])
            ]
            watering_log = WateringLog(
                logged_at=now,
                application_method=ApplicationMethod.DRENCH,
                volume_liters=effective_volume,
                slot_keys=slot_keys or ["default"],
                plant_keys=[plant_key],
                ec_before=measured_ec,
                ph_before=measured_ph,
                fertilizers_used=ferts,
                notes=notes,
            )
            created_log = self._watering_log_repo.create(watering_log)
            watering_log_key = created_log.key

        confirmation = CareConfirmation(
            plant_key=plant_key,
            care_profile_key=profile.key or "",
            reminder_type=reminder_type,
            action=ConfirmAction.CONFIRMED,
            confirmed_at=now,
            watering_log_key=watering_log_key,
            notes=notes,
            interval_at_time=self._get_current_interval(profile, reminder_type),
        )
        created = self._repo.create_confirmation(confirmation)
        if created.key and profile.key:
            self._repo.create_confirmation_edges(created.key, profile.key, plant_key)

        # Apply adaptive learning
        if profile.adaptive_learning_enabled:
            history = self._repo.get_confirmations_by_plant(plant_key, reminder_type, limit=10)
            learned = self._engine.apply_adaptive_learning(profile, reminder_type, history)
            if learned is not None:
                if reminder_type == ReminderType.WATERING:
                    self._repo.update_profile(profile.key or "", CareProfile(
                        **{**profile.model_dump(), "watering_interval_learned": learned},
                    ))
                elif reminder_type == ReminderType.FERTILIZING:
                    self._repo.update_profile(profile.key or "", CareProfile(
                        **{**profile.model_dump(), "fertilizing_interval_learned": learned},
                    ))

        # Auto-create next watering task if opted in
        if (
            reminder_type == ReminderType.WATERING
            and profile.auto_create_watering_task
        ):
            self.ensure_next_watering_task(profile, created)

        return created

    def _resolve_slot_keys(self, plant_key: str) -> list[str]:
        """Look up the slot_key for a plant instance."""
        if self._plant_repo is None:
            return []
        plant = self._plant_repo.get_by_key(plant_key)
        if plant is not None and plant.slot_key:
            return [plant.slot_key]
        return []

    def snooze_reminder(
        self,
        plant_key: str,
        reminder_type: ReminderType,
        snooze_days: int = 1,
    ) -> CareConfirmation:
        profile = self._repo.get_profile_by_plant_key(plant_key)
        if profile is None:
            profile = self.get_or_create_profile(plant_key)

        confirmation = CareConfirmation(
            plant_key=plant_key,
            care_profile_key=profile.key or "",
            reminder_type=reminder_type,
            action=ConfirmAction.SNOOZED,
            confirmed_at=datetime.now(UTC),
            snooze_days=snooze_days,
        )
        created = self._repo.create_confirmation(confirmation)
        if created.key and profile.key:
            self._repo.create_confirmation_edges(created.key, profile.key, plant_key)
        return created

    def get_care_dashboard(
        self,
        plant_data: list[dict],
        hemisphere: str = "north",
    ) -> list[CareDashboardEntry]:
        """Build care dashboard from plant data.

        plant_data: list of dicts with keys: plant_key, plant_name, species_name,
                    botanical_family, current_phase, has_nutrient_plan
        """
        entries: list[CareDashboardEntry] = []

        for plant in plant_data:
            plant_key = plant["plant_key"]
            profile = self.get_or_create_profile(
                plant_key,
                species_name=plant.get("species_name"),
                botanical_family=plant.get("botanical_family"),
            )

            for rt in ReminderType:
                if not self._engine.should_generate_reminder(
                    profile, rt, plant.get("current_phase"), hemisphere,
                    has_nutrient_plan=plant.get("has_nutrient_plan", False),
                ):
                    continue

                last = self._repo.get_last_confirmation(plant_key, rt)
                due_date = self._engine.calculate_due_date(
                    profile, rt, last, plant.get("current_phase"), hemisphere,
                )
                urgency = self._engine.calculate_urgency(due_date)

                if urgency in ("overdue", "due_today", "upcoming"):
                    entries.append(CareDashboardEntry(
                        plant_key=plant_key,
                        plant_name=plant.get("plant_name", ""),
                        species_name=plant.get("species_name"),
                        reminder_type=rt,
                        urgency=urgency,
                        due_date=due_date.isoformat() if due_date else None,
                        care_profile_key=profile.key or "",
                    ))

        # Sort: overdue first, then due_today, then upcoming
        urgency_order = {"overdue": 0, "due_today": 1, "upcoming": 2}
        entries.sort(key=lambda e: urgency_order.get(e.urgency, 3))
        return entries

    def reset_profile(
        self,
        plant_key: str,
        species_name: str | None = None,
        botanical_family: str | None = None,
    ) -> CareProfile:
        """Reset profile to species/family defaults."""
        profile = self._repo.get_profile_by_plant_key(plant_key)
        if profile is None:
            raise NotFoundError("CareProfile", plant_key)

        new_profile = self._engine.auto_generate_profile(
            species_name=species_name,
            botanical_family=botanical_family,
            plant_key=plant_key,
        )
        new_data = new_profile.model_dump(exclude={"key", "created_at", "updated_at"})
        reset = CareProfile(**{**profile.model_dump(), **new_data})
        return self._repo.update_profile(profile.key or "", reset)

    def get_confirmation_history(
        self,
        plant_key: str,
        reminder_type: ReminderType | None = None,
        limit: int = 50,
    ) -> list[CareConfirmation]:
        return self._repo.get_confirmations_by_plant(plant_key, reminder_type, limit)

    def ensure_next_watering_task(
        self,
        profile: CareProfile,
        last_confirmation: CareConfirmation | None = None,
        hemisphere: str = "north",
    ) -> Task | None:
        """Ensure exactly one pending watering task exists for this plant.

        Called after watering confirmation and by the daily Celery task.
        Returns the created task or None if one already exists.
        """
        if self._task_repo is None:
            return None

        plant_key = profile.plant_key
        rt_value = ReminderType.WATERING.value
        name_suffix = f"\u2014 {rt_value}"

        # Check for existing pending/in_progress watering task
        existing = self._task_repo.find_by_field("plant_key", plant_key)
        has_pending = any(
            t.get("category") == TaskCategory.CARE_REMINDER.value
            and t.get("name", "").endswith(name_suffix)
            and t.get("status") in (TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value)
            for t in existing
        )
        if has_pending:
            return None

        # Calculate next due date
        if last_confirmation is None:
            last_confirmation = self._repo.get_last_confirmation(
                plant_key, ReminderType.WATERING,
            )

        due_date = self._engine.calculate_due_date(
            profile, ReminderType.WATERING, last_confirmation,
            hemisphere=hemisphere,
        )
        if due_date is None:
            return None

        due_dt = datetime(due_date.year, due_date.month, due_date.day, tzinfo=UTC)

        # Resolve plant name for user-friendly display
        plant_label = plant_key
        if self._plant_repo is not None:
            plant = self._plant_repo.get_by_key(plant_key)
            if plant is not None:
                plant_label = plant.plant_name or plant.instance_id or plant_key

        interval = profile.watering_interval_learned or profile.watering_interval_days

        task = Task(
            name=f"{plant_label} \u2014 {rt_value}",
            instruction=f"Water {plant_label} (every {interval} days).",
            category=TaskCategory.CARE_REMINDER,
            plant_key=plant_key,
            due_date=due_dt,
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
        )
        return self._task_repo.create_task(task)

    def _get_current_interval(self, profile: CareProfile, reminder_type: ReminderType) -> int | None:
        if reminder_type == ReminderType.WATERING:
            return profile.watering_interval_learned or profile.watering_interval_days
        if reminder_type == ReminderType.FERTILIZING:
            return profile.fertilizing_interval_learned or profile.fertilizing_interval_days
        return None
