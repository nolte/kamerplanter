from abc import ABC, abstractmethod

from app.common.types import (
    LocationKey,
    MaintenanceScheduleKey,
    TankKey,
)
from app.domain.models.tank import MaintenanceLog, MaintenanceSchedule, Tank, TankFillEvent, TankState


class ITankRepository(ABC):
    # ── Tank CRUD ──────────────────────────────────────────────────────

    @abstractmethod
    def get_all(
        self, offset: int = 0, limit: int = 50, filters: dict | None = None,
    ) -> tuple[list[Tank], int]:
        ...

    @abstractmethod
    def get_by_key(self, key: TankKey) -> Tank | None:
        ...

    @abstractmethod
    def create(self, tank: Tank) -> Tank:
        ...

    @abstractmethod
    def update(self, key: TankKey, tank: Tank) -> Tank:
        ...

    @abstractmethod
    def delete(self, key: TankKey) -> bool:
        ...

    # ── Edge operations ────────────────────────────────────────────────

    @abstractmethod
    def link_to_location(self, tank_key: TankKey, location_key: LocationKey) -> None:
        ...

    @abstractmethod
    def update_location(
        self,
        tank_key: TankKey,
        old_location_key: LocationKey | None,
        new_location_key: LocationKey | None,
    ) -> None:
        ...

    @abstractmethod
    def link_supply(self, tank_key: TankKey, location_key: LocationKey) -> None:
        ...

    @abstractmethod
    def link_feeds_from(self, tank_key: TankKey, source_tank_key: TankKey) -> None:
        ...

    # ── State CRUD ─────────────────────────────────────────────────────

    @abstractmethod
    def create_state(self, state: TankState) -> TankState:
        ...

    @abstractmethod
    def get_states(
        self, tank_key: TankKey, offset: int = 0, limit: int = 50,
    ) -> list[TankState]:
        ...

    @abstractmethod
    def get_latest_state(self, tank_key: TankKey) -> TankState | None:
        ...

    # ── MaintenanceLog CRUD ────────────────────────────────────────────

    @abstractmethod
    def create_maintenance_log(self, log: MaintenanceLog) -> MaintenanceLog:
        ...

    @abstractmethod
    def get_maintenance_logs(
        self, tank_key: TankKey, offset: int = 0, limit: int = 50,
    ) -> list[MaintenanceLog]:
        ...

    @abstractmethod
    def get_last_maintenance_by_type(
        self, tank_key: TankKey, maintenance_type: str,
    ) -> MaintenanceLog | None:
        ...

    # ── Schedule CRUD ──────────────────────────────────────────────────

    @abstractmethod
    def create_schedule(self, schedule: MaintenanceSchedule) -> MaintenanceSchedule:
        ...

    @abstractmethod
    def get_schedules(self, tank_key: TankKey) -> list[MaintenanceSchedule]:
        ...

    @abstractmethod
    def get_schedule_by_key(self, key: MaintenanceScheduleKey) -> MaintenanceSchedule | None:
        ...

    @abstractmethod
    def update_schedule(
        self, key: MaintenanceScheduleKey, schedule: MaintenanceSchedule,
    ) -> MaintenanceSchedule:
        ...

    @abstractmethod
    def delete_schedule(self, key: MaintenanceScheduleKey) -> bool:
        ...

    # ── Fill Events ──────────────────────────────────────────────────────

    @abstractmethod
    def create_fill_event(self, event: TankFillEvent) -> TankFillEvent:
        ...

    @abstractmethod
    def get_fill_events(
        self, tank_key: TankKey, offset: int = 0, limit: int = 50,
    ) -> list[TankFillEvent]:
        ...

    @abstractmethod
    def get_latest_fill_event(self, tank_key: TankKey) -> TankFillEvent | None:
        ...

    @abstractmethod
    def get_latest_full_change(self, tank_key: TankKey) -> TankFillEvent | None:
        ...

    @abstractmethod
    def get_fill_event_stats(
        self, tank_key: TankKey, start_date: str | None = None, end_date: str | None = None,
    ) -> dict:
        ...

    # ── Queries ────────────────────────────────────────────────────────

    @abstractmethod
    def get_tanks_for_location(self, location_key: LocationKey) -> list[Tank]:
        ...

    @abstractmethod
    def get_active_auto_create_schedules(self) -> list[MaintenanceSchedule]:
        ...

    @abstractmethod
    def get_active_nutrient_plans(self, tank_key: TankKey) -> list[dict]:
        """Resolve Tank → Location → active PlantingRuns → NutrientPlan + current PhaseEntries."""
        ...
