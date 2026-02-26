from datetime import UTC, date, datetime

from app.common.enums import PlantingRunStatus
from app.common.exceptions import InvalidRunStateError, NotFoundError
from app.common.types import PlantID, PlantingRunKey
from app.domain.engines.planting_run_engine import PlantingRunEngine
from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
from app.domain.interfaces.planting_run_repository import IPlantingRunRepository
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.planting_run import PlantingRun, PlantingRunEntry


class PlantingRunService:
    def __init__(
        self,
        run_repo: IPlantingRunRepository,
        plant_repo: IPlantInstanceRepository,
        engine: PlantingRunEngine,
    ) -> None:
        self._repo = run_repo
        self._plant_repo = plant_repo
        self._engine = engine

    # ── Run CRUD ──────────────────────────────────────────────────────

    def list_runs(
        self, offset: int = 0, limit: int = 50, filters: dict | None = None,
    ) -> tuple[list[PlantingRun], int]:
        return self._repo.get_all(offset, limit, filters)

    def get_run(self, key: PlantingRunKey) -> PlantingRun:
        run = self._repo.get_by_key(key)
        if run is None:
            raise NotFoundError("PlantingRun", key)
        return run

    def create_run(self, run: PlantingRun, entries: list[PlantingRunEntry] | None = None) -> PlantingRun:
        run.status = PlantingRunStatus.PLANNED
        total_qty = 0
        if entries:
            self._engine.validate_run_type_constraints(
                run.run_type, entries, run.source_plant_key,
            )
            total_qty = sum(e.quantity for e in entries)
        run.planned_quantity = total_qty
        created = self._repo.create(run)
        if entries and created.key:
            for entry in entries:
                entry.run_key = created.key
                self._repo.create_entry(entry)
        return created

    def update_run(self, key: PlantingRunKey, data: dict) -> PlantingRun:
        run = self.get_run(key)
        allowed_fields = {"name", "notes", "planned_start_date"}
        for field, value in data.items():
            if field in allowed_fields:
                setattr(run, field, value)
        return self._repo.update(key, run)

    def delete_run(self, key: PlantingRunKey) -> bool:
        run = self.get_run(key)
        if run.status != PlantingRunStatus.PLANNED:
            raise InvalidRunStateError("delete", run.status.value)
        return self._repo.delete(key)

    # ── Status transitions ────────────────────────────────────────────

    def _transition_status(self, key: PlantingRunKey, target: PlantingRunStatus) -> PlantingRun:
        run = self.get_run(key)
        self._engine.validate_status_transition(run.status, target)
        run.status = target
        now = datetime.now(UTC)
        if target == PlantingRunStatus.ACTIVE and run.started_at is None:
            run.started_at = now
        if target in (PlantingRunStatus.COMPLETED, PlantingRunStatus.CANCELLED):
            run.completed_at = now
        return self._repo.update(key, run)

    # ── Entry management ──────────────────────────────────────────────

    def list_entries(self, run_key: PlantingRunKey) -> list[PlantingRunEntry]:
        self.get_run(run_key)
        return self._repo.get_entries(run_key)

    def add_entry(self, run_key: PlantingRunKey, entry: PlantingRunEntry) -> PlantingRunEntry:
        run = self.get_run(run_key)
        if run.status != PlantingRunStatus.PLANNED:
            raise InvalidRunStateError("add_entry", run.status.value)
        entry.run_key = run_key
        created = self._repo.create_entry(entry)
        # Update planned_quantity
        entries = self._repo.get_entries(run_key)
        run.planned_quantity = sum(e.quantity for e in entries)
        self._repo.update(run_key, run)
        return created

    def update_entry(
        self, run_key: PlantingRunKey, entry_key: str, entry: PlantingRunEntry,
    ) -> PlantingRunEntry:
        run = self.get_run(run_key)
        if run.status != PlantingRunStatus.PLANNED:
            raise InvalidRunStateError("update_entry", run.status.value)
        existing = self._repo.get_entry_by_key(entry_key)
        if existing is None:
            raise NotFoundError("PlantingRunEntry", entry_key)
        updated = self._repo.update_entry(entry_key, entry)
        # Update planned_quantity
        entries = self._repo.get_entries(run_key)
        run.planned_quantity = sum(e.quantity for e in entries)
        self._repo.update(run_key, run)
        return updated

    def delete_entry(self, run_key: PlantingRunKey, entry_key: str) -> bool:
        run = self.get_run(run_key)
        if run.status != PlantingRunStatus.PLANNED:
            raise InvalidRunStateError("delete_entry", run.status.value)
        existing = self._repo.get_entry_by_key(entry_key)
        if existing is None:
            raise NotFoundError("PlantingRunEntry", entry_key)
        result = self._repo.delete_entry(entry_key)
        # Update planned_quantity
        entries = self._repo.get_entries(run_key)
        run.planned_quantity = sum(e.quantity for e in entries)
        self._repo.update(run_key, run)
        return result

    # ── Batch operations ──────────────────────────────────────────────

    def create_plants(self, run_key: PlantingRunKey) -> dict:
        """Batch-create PlantInstances from run entries."""
        run = self.get_run(run_key)
        if run.status != PlantingRunStatus.PLANNED:
            raise InvalidRunStateError("create_plants", run.status.value)

        entries = self._repo.get_entries(run_key)
        if not entries:
            raise ValueError("Run has no entries.")

        self._engine.validate_run_type_constraints(
            run.run_type, entries, run.source_plant_key,
        )

        location_key = run.location_key or "LOC"
        existing_ids = set()
        if run.location_key:
            existing_ids = self._repo.get_existing_ids_at_location(run.location_key)

        plant_specs = self._engine.generate_plant_ids(location_key, entries, existing_ids)

        created_plants = []
        for spec in plant_specs:
            plant = PlantInstance(
                instance_id=spec["instance_id"],
                species_key=spec["species_key"],
                cultivar_key=spec.get("cultivar_key"),
                slot_key=None,
                planted_on=date.today(),
                current_phase="seedling",
            )
            created = self._plant_repo.create(plant)
            if created.key:
                self._repo.link_run_to_plant(run_key, created.key)
            created_plants.append(created)

        # Transition to active
        run.actual_quantity = len(created_plants)
        run.status = PlantingRunStatus.ACTIVE
        run.started_at = datetime.now(UTC)
        self._repo.update(run_key, run)

        return {
            "run_key": run_key,
            "created_count": len(created_plants),
            "plant_keys": [p.key for p in created_plants if p.key],
            "instance_ids": [p.instance_id for p in created_plants],
        }

    def batch_transition(
        self, run_key: PlantingRunKey, target_phase_key: str, target_phase_name: str,
        exclude_keys: set[str] | None = None,
    ) -> dict:
        """Batch phase transition for all eligible plants in the run."""
        run = self.get_run(run_key)
        if run.status not in (PlantingRunStatus.ACTIVE, PlantingRunStatus.HARVESTING):
            raise InvalidRunStateError("batch_transition", run.status.value)

        plants = self._repo.get_run_plants(run_key, include_detached=False)
        eligible, skipped = self._engine.filter_transition_eligible(
            plants, target_phase_name, exclude_keys,
        )

        transitioned = []
        failed = []
        for plant in eligible:
            plant_key = plant.get("_key", "")
            try:
                existing = self._plant_repo.get_by_key(plant_key)
                if existing:
                    existing.current_phase = target_phase_name
                    existing.current_phase_key = target_phase_key
                    existing.current_phase_started_at = datetime.now(UTC)
                    self._plant_repo.update(plant_key, existing)
                    transitioned.append(plant_key)
            except Exception:
                failed.append(plant_key)

        return {
            "run_key": run_key,
            "target_phase": target_phase_name,
            "transitioned_count": len(transitioned),
            "skipped_count": len(skipped),
            "failed_count": len(failed),
            "transitioned_keys": transitioned,
            "skipped_keys": [p.get("_key", "") for p in skipped],
            "failed_keys": failed,
        }

    def batch_remove(self, run_key: PlantingRunKey, reason: str = "batch_remove") -> dict:
        """Remove all active plants from the run and complete it."""
        run = self.get_run(run_key)
        if run.status not in (PlantingRunStatus.ACTIVE, PlantingRunStatus.HARVESTING):
            raise InvalidRunStateError("batch_remove", run.status.value)

        plants = self._repo.get_run_plants(run_key, include_detached=False)
        removed = []
        for plant in plants:
            plant_key = plant.get("_key", "")
            try:
                existing = self._plant_repo.get_by_key(plant_key)
                if existing and existing.removed_on is None:
                    existing.removed_on = date.today()
                    self._plant_repo.update(plant_key, existing)
                    removed.append(plant_key)
            except Exception:
                pass

        # Transition to completed
        run.status = PlantingRunStatus.COMPLETED
        run.completed_at = datetime.now(UTC)
        self._repo.update(run_key, run)

        return {
            "run_key": run_key,
            "removed_count": len(removed),
            "removed_keys": removed,
        }

    # ── Plant management ──────────────────────────────────────────────

    def get_plants(self, run_key: PlantingRunKey, include_detached: bool = False) -> list[dict]:
        self.get_run(run_key)
        return self._repo.get_run_plants(run_key, include_detached)

    def detach_plant(self, run_key: PlantingRunKey, plant_key: PlantID, reason: str) -> None:
        self.get_run(run_key)
        self._repo.detach_plant(run_key, plant_key, reason)
