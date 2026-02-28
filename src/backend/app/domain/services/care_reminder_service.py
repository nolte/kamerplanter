from datetime import UTC, datetime

from app.common.enums import ConfirmAction, ReminderType
from app.common.exceptions import NotFoundError
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.interfaces.care_reminder_repository import ICareReminderRepository
from app.domain.models.care_reminder import CareConfirmation, CareDashboardEntry, CareProfile


class CareReminderService:
    def __init__(
        self,
        care_repo: ICareReminderRepository,
        engine: CareReminderEngine,
    ) -> None:
        self._repo = care_repo
        self._engine = engine

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
    ) -> CareConfirmation:
        profile = self._repo.get_profile_by_plant_key(plant_key)
        if profile is None:
            raise NotFoundError("CareProfile", plant_key)

        confirmation = CareConfirmation(
            plant_key=plant_key,
            care_profile_key=profile.key or "",
            reminder_type=reminder_type,
            action=ConfirmAction.CONFIRMED,
            confirmed_at=datetime.now(UTC),
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

        return created

    def snooze_reminder(
        self,
        plant_key: str,
        reminder_type: ReminderType,
        snooze_days: int = 1,
    ) -> CareConfirmation:
        profile = self._repo.get_profile_by_plant_key(plant_key)
        if profile is None:
            raise NotFoundError("CareProfile", plant_key)

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
                    botanical_family, current_phase
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

    def _get_current_interval(self, profile: CareProfile, reminder_type: ReminderType) -> int | None:
        if reminder_type == ReminderType.WATERING:
            return profile.watering_interval_learned or profile.watering_interval_days
        if reminder_type == ReminderType.FERTILIZING:
            return profile.fertilizing_interval_learned or profile.fertilizing_interval_days
        return None
