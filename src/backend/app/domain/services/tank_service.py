from app.common.enums import IrrigationSystem
from app.common.exceptions import NotFoundError, ValidationError
from app.common.types import MaintenanceScheduleKey, TankKey
from app.domain.engines.tank_engine import TankEngine
from app.domain.interfaces.tank_repository import ITankRepository
from app.domain.models.tank import MaintenanceLog, MaintenanceSchedule, Tank, TankState


class TankService:
    def __init__(self, repo: ITankRepository, engine: TankEngine) -> None:
        self._repo = repo
        self._engine = engine

    # ── Tank CRUD ──────────────────────────────────────────────────────

    def list_tanks(
        self, offset: int = 0, limit: int = 50, filters: dict | None = None,
    ) -> tuple[list[Tank], int]:
        return self._repo.get_all(offset, limit, filters)

    def get_tank(self, key: TankKey) -> Tank:
        tank = self._repo.get_by_key(key)
        if tank is None:
            raise NotFoundError("Tank", key)
        return tank

    def create_tank(
        self,
        tank: Tank,
        irrigation_system: IrrigationSystem | None = None,
        create_default_schedules: bool = True,
    ) -> Tank:
        # Validate assignment if location has irrigation info
        if irrigation_system is not None:
            self._engine.validate_tank_assignment(tank.tank_type, irrigation_system)

        created = self._repo.create(tank)

        # Create default maintenance schedules
        if create_default_schedules and created.key:
            defaults = self._engine.get_default_schedules(tank.tank_type)
            for d in defaults:
                schedule = MaintenanceSchedule(
                    tank_key=created.key,
                    maintenance_type=d["type"],
                    interval_days=d["interval_days"],
                    priority=d["priority"],
                    reminder_days_before=min(3, d["interval_days"] - 1),
                )
                self._repo.create_schedule(schedule)

        return created

    def update_tank(self, key: TankKey, data: dict) -> Tank:
        tank = self.get_tank(key)
        allowed_fields = {
            "name", "tank_type", "volume_liters", "material",
            "has_lid", "has_air_pump", "has_circulation_pump",
            "has_heater", "installed_on", "notes",
        }
        for field, value in data.items():
            if field in allowed_fields:
                setattr(tank, field, value)
        return self._repo.update(key, tank)

    def delete_tank(self, key: TankKey) -> bool:
        self.get_tank(key)  # ensure exists
        return self._repo.delete(key)

    # ── State management ───────────────────────────────────────────────

    def record_state(self, tank_key: TankKey, state: TankState) -> TankState:
        tank = self.get_tank(tank_key)
        state.tank_key = tank_key

        # Validate and auto-calculate fill level
        fill_liters, fill_percent = self._engine.validate_fill_level(
            tank.volume_liters, state.fill_level_liters, state.fill_level_percent,
        )
        state.fill_level_liters = fill_liters
        state.fill_level_percent = fill_percent

        return self._repo.create_state(state)

    def get_states(
        self, tank_key: TankKey, offset: int = 0, limit: int = 50,
    ) -> list[TankState]:
        self.get_tank(tank_key)
        return self._repo.get_states(tank_key, offset, limit)

    def get_latest_state(self, tank_key: TankKey) -> TankState | None:
        self.get_tank(tank_key)
        return self._repo.get_latest_state(tank_key)

    # ── Alerts ─────────────────────────────────────────────────────────

    def get_alerts(self, tank_key: TankKey) -> list[dict]:
        tank = self.get_tank(tank_key)
        state = self._repo.get_latest_state(tank_key)
        if state is None:
            return []
        return self._engine.check_alerts(tank, state)

    # ── Maintenance logging ────────────────────────────────────────────

    def log_maintenance(self, tank_key: TankKey, log: MaintenanceLog) -> MaintenanceLog:
        self.get_tank(tank_key)
        log.tank_key = tank_key
        return self._repo.create_maintenance_log(log)

    def get_maintenance_history(
        self, tank_key: TankKey, offset: int = 0, limit: int = 50,
    ) -> list[MaintenanceLog]:
        self.get_tank(tank_key)
        return self._repo.get_maintenance_logs(tank_key, offset, limit)

    # ── Due maintenance ────────────────────────────────────────────────

    def get_due_maintenances(self, tank_key: TankKey) -> list[dict]:
        self.get_tank(tank_key)
        schedules = self._repo.get_schedules(tank_key)
        results = []
        for schedule in schedules:
            if not schedule.is_active:
                continue
            last_log = self._repo.get_last_maintenance_by_type(
                tank_key, schedule.maintenance_type.value,
            )
            info = self._engine.calculate_next_maintenance(schedule, last_log)
            info["tank_key"] = tank_key
            results.append(info)
        return results

    def get_all_due_maintenances(self) -> list[dict]:
        """Get due maintenances across all tanks."""
        tanks, _total = self._repo.get_all(offset=0, limit=1000)
        results = []
        for tank in tanks:
            if tank.key:
                tank_dues = self.get_due_maintenances(tank.key)
                for due in tank_dues:
                    due["tank_name"] = tank.name
                results.extend(tank_dues)
        return results

    # ── Schedule CRUD ──────────────────────────────────────────────────

    def create_schedule(self, tank_key: TankKey, schedule: MaintenanceSchedule) -> MaintenanceSchedule:
        self.get_tank(tank_key)
        schedule.tank_key = tank_key
        return self._repo.create_schedule(schedule)

    def get_schedules(self, tank_key: TankKey) -> list[MaintenanceSchedule]:
        self.get_tank(tank_key)
        return self._repo.get_schedules(tank_key)

    def update_schedule(self, key: MaintenanceScheduleKey, data: dict) -> MaintenanceSchedule:
        existing = self._repo.get_schedule_by_key(key)
        if existing is None:
            raise NotFoundError("MaintenanceSchedule", key)
        allowed_fields = {
            "interval_days", "reminder_days_before", "is_active",
            "priority", "auto_create_task", "instructions",
        }
        for field, value in data.items():
            if field in allowed_fields:
                setattr(existing, field, value)

        # Re-validate after updates
        if existing.reminder_days_before >= existing.interval_days:
            raise ValidationError(
                f"reminder_days_before ({existing.reminder_days_before}) "
                f"must be less than interval_days ({existing.interval_days})"
            )

        return self._repo.update_schedule(key, existing)

    def delete_schedule(self, key: MaintenanceScheduleKey) -> bool:
        existing = self._repo.get_schedule_by_key(key)
        if existing is None:
            raise NotFoundError("MaintenanceSchedule", key)
        return self._repo.delete_schedule(key)

    # ── Relationships ──────────────────────────────────────────────────

    def link_feeds_from(self, tank_key: TankKey, source_tank_key: TankKey) -> None:
        self.get_tank(tank_key)
        self.get_tank(source_tank_key)
        if tank_key == source_tank_key:
            raise ValidationError("A tank cannot feed from itself.")
        self._repo.link_feeds_from(tank_key, source_tank_key)
