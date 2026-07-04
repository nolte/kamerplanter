from arango.database import StandardDatabase

from app.common.enums import ReminderType
from app.common.types import CareProfileKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.care_reminder_repository import ICareReminderRepository
from app.domain.models.care_reminder import CareConfirmation, CareProfile


class ArangoCareReminderRepository(BaseArangoRepository[CareProfile], ICareReminderRepository):
    _model_cls = CareProfile

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.CARE_PROFILES)
        self._confirmations = BaseArangoRepository[CareConfirmation](db, col.CARE_CONFIRMATIONS, CareConfirmation)

    # ── CareProfile ────────────────────────────────────────────────────

    def get_profile_by_key(self, key: CareProfileKey) -> CareProfile | None:
        return super().get_by_key(key)

    def get_profile_by_plant_key(self, plant_key: str) -> CareProfile | None:
        return self.find_one_by_field("plant_key", plant_key)

    def create_profile(self, profile: CareProfile) -> CareProfile:
        return super().create(profile)

    def update_profile(self, key: CareProfileKey, profile: CareProfile) -> CareProfile:
        return super().update(key, profile)

    def delete_profile(self, key: CareProfileKey) -> bool:
        return super().delete(key)

    def get_all_profiles(self) -> list[CareProfile]:
        profiles, _ = super().get_all(offset=0, limit=10000)
        return profiles

    # ── CareConfirmation ───────────────────────────────────────────────

    def create_confirmation(self, confirmation: CareConfirmation) -> CareConfirmation:
        return self._confirmations.create(confirmation)

    def get_confirmations_by_plant(
        self,
        plant_key: str,
        reminder_type: ReminderType | None = None,
        limit: int = 50,
    ) -> list[CareConfirmation]:
        extra_filters = [("reminder_type", "==", reminder_type.value)] if reminder_type else None
        return self._confirmations.find_by_field(
            "plant_key",
            plant_key,
            sort="confirmed_at",
            sort_direction="DESC",
            offset=0,
            limit=limit,
            extra_filters=extra_filters,
        )

    def get_last_confirmation(
        self,
        plant_key: str,
        reminder_type: ReminderType,
    ) -> CareConfirmation | None:
        results = self.get_confirmations_by_plant(plant_key, reminder_type, limit=1)
        return results[0] if results else None

    # ── Edge operations ────────────────────────────────────────────────

    def create_profile_edge(self, plant_key: str, profile_key: str) -> None:
        plant_id = f"{col.PLANT_INSTANCES}/{plant_key}"
        profile_id = f"{col.CARE_PROFILES}/{profile_key}"
        self.create_edge(col.HAS_CARE_PROFILE, plant_id, profile_id)

    def create_confirmation_edges(
        self,
        confirmation_key: str,
        profile_key: str,
        plant_key: str,
    ) -> None:
        confirmation_id = f"{col.CARE_CONFIRMATIONS}/{confirmation_key}"
        profile_id = f"{col.CARE_PROFILES}/{profile_key}"
        plant_id = f"{col.PLANT_INSTANCES}/{plant_key}"
        self.create_edge(col.CONFIRMS_CARE, confirmation_id, profile_id)
        self.create_edge(col.CARE_EVENT_FOR, confirmation_id, plant_id)
