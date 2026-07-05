from datetime import date

from arango.database import StandardDatabase

from app.common.enums import ReminderType, TaskCategory, TaskStatus
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

    # ── Dashboard count (REQ-009) ──────────────────────────────────────

    def count_due_on(self, tenant_key: str, today: date) -> int:
        """Count care reminders actionable for ``tenant_key`` on ``today``.

        Care reminders are not stored as standalone documents — a ``CareProfile``
        carries no ``tenant_key`` or ``due_date``, and the live reminder view is
        computed on the fly. Their *persisted, tenant-scoped, due-dated* form is a
        care-reminder ``Task`` (``category == care_reminder``), created by the
        care-reminder engine/service. This count therefore reads the tenant's open
        care-reminder tasks that are due today **or overdue** (``due_date <=
        today``), matching REQ-009 R3 (a single care count, so overdue is
        included).

        The tasks collection is bound via ``@@tasks`` (never interpolated) and
        filtered on ``tenant_key``; the empty-tenant sentinel is rejected up-front
        (SEC-B4). ``due_date`` is a datetime stored as an ISO string, compared on
        its ten-character calendar-date prefix so the count is timezone-offset
        agnostic; null due dates are excluded. Orphaned plant tasks (removed or
        missing plant) are excluded to match the user-facing queue.
        """
        self._require_tenant_key(tenant_key, "count_due_on")
        query = """
        RETURN LENGTH(
          FOR doc IN @@tasks
            FILTER doc.tenant_key == @tenant_key
            FILTER doc.category == @care_category
            FILTER doc.status IN @open_statuses
            FILTER doc.due_date != null
            FILTER LEFT(doc.due_date, 10) <= @today
            LET _plant = doc.entity_type == 'plant_instance'
              ? DOCUMENT(CONCAT(@plant_col, '/', doc.entity_key))
              : null
            FILTER doc.entity_type != 'plant_instance'
              OR (_plant != null AND _plant.removed_on == null)
            RETURN 1
        )
        """
        bind_vars = {
            "@tasks": col.TASKS,
            "tenant_key": tenant_key,
            "care_category": TaskCategory.CARE_REMINDER.value,
            "open_statuses": [TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value],
            "today": today.isoformat(),
            "plant_col": col.PLANT_INSTANCES,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return int(next(cursor, 0) or 0)

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
