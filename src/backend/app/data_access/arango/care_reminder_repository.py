from arango.database import StandardDatabase

from app.common.enums import ReminderType
from app.common.types import CareProfileKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.care_reminder_repository import ICareReminderRepository
from app.domain.models.care_reminder import CareConfirmation, CareProfile


class ArangoCareReminderRepository(ICareReminderRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.CARE_PROFILES)

    # ── CareProfile ────────────────────────────────────────────────────

    def get_profile_by_key(self, key: CareProfileKey) -> CareProfile | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        return CareProfile(**doc) if doc else None

    def get_profile_by_plant_key(self, plant_key: str) -> CareProfile | None:
        docs = self.find_by_field("plant_key", plant_key)
        if docs:
            return CareProfile(**docs[0])
        return None

    def create_profile(self, profile: CareProfile) -> CareProfile:
        doc = BaseArangoRepository.create(self, profile)
        return CareProfile(**doc)

    def update_profile(self, key: CareProfileKey, profile: CareProfile) -> CareProfile:
        doc = BaseArangoRepository.update(self, key, profile)
        return CareProfile(**doc)

    def delete_profile(self, key: CareProfileKey) -> bool:
        return BaseArangoRepository.delete(self, key)

    def get_all_profiles(self) -> list[CareProfile]:
        docs, _ = BaseArangoRepository.get_all(self, offset=0, limit=10000)
        return [CareProfile(**doc) for doc in docs]

    # ── CareConfirmation ───────────────────────────────────────────────

    def create_confirmation(self, confirmation: CareConfirmation) -> CareConfirmation:
        repo = BaseArangoRepository(self._db, col.CARE_CONFIRMATIONS)
        doc = repo.create(confirmation)
        return CareConfirmation(**doc)

    def get_confirmations_by_plant(
        self,
        plant_key: str,
        reminder_type: ReminderType | None = None,
        limit: int = 50,
    ) -> list[CareConfirmation]:
        repo = BaseArangoRepository(self._db, col.CARE_CONFIRMATIONS)
        if reminder_type:
            query = (
                f"FOR doc IN {col.CARE_CONFIRMATIONS} "
                f"FILTER doc.plant_key == @plant_key AND doc.reminder_type == @type "
                f"SORT doc.confirmed_at DESC LIMIT @limit RETURN doc"
            )
            cursor = self._db.aql.execute(
                query,
                bind_vars={"plant_key": plant_key, "type": reminder_type.value, "limit": limit},
            )
        else:
            query = (
                f"FOR doc IN {col.CARE_CONFIRMATIONS} "
                f"FILTER doc.plant_key == @plant_key "
                f"SORT doc.confirmed_at DESC LIMIT @limit RETURN doc"
            )
            cursor = self._db.aql.execute(
                query,
                bind_vars={"plant_key": plant_key, "limit": limit},
            )
        return [CareConfirmation(**repo._from_doc(doc)) for doc in cursor]

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
