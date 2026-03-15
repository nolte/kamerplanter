from datetime import UTC, date, datetime, timedelta

from app.common.enums import PlantingRunStatus
from app.common.exceptions import InvalidRunStateError, NotFoundError
from app.common.types import PlantID, PlantingRunKey
from app.domain.engines.planting_run_engine import PlantingRunEngine
from app.domain.engines.watering_schedule_engine import WateringScheduleEngine
from app.domain.interfaces.phase_repository import IPhaseRepository
from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
from app.domain.interfaces.planting_run_repository import IPlantingRunRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.models.phase import PhaseHistory
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.planting_run import PlantingRun, PlantingRunEntry


class PlantingRunService:
    def __init__(
        self,
        run_repo: IPlantingRunRepository,
        plant_repo: IPlantInstanceRepository,
        engine: PlantingRunEngine,
        watering_schedule_engine: WateringScheduleEngine | None = None,
        nutrient_plan_repo=None,
        watering_repo=None,
        phase_repo: IPhaseRepository | None = None,
        site_repo: ISiteRepository | None = None,
    ) -> None:
        self._repo = run_repo
        self._plant_repo = plant_repo
        self._engine = engine
        self._schedule_engine = watering_schedule_engine or WateringScheduleEngine()
        self._nutrient_plan_repo = nutrient_plan_repo
        self._watering_repo = watering_repo
        self._phase_repo = phase_repo
        self._site_repo = site_repo

    # ── Run CRUD ──────────────────────────────────────────────────────

    def list_runs(
        self,
        offset: int = 0,
        limit: int = 50,
        filters: dict | None = None,
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
                run.run_type,
                entries,
                run.source_plant_key,
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
        old_location_key = run.location_key
        allowed_fields = {"name", "notes", "planned_start_date", "location_key"}
        for field, value in data.items():
            if field in allowed_fields:
                setattr(run, field, value)
        updated = self._repo.update(key, run)

        # When location changes on an active run, reassign plants to new slots
        new_location_key = updated.location_key
        if old_location_key != new_location_key and updated.status in (
            PlantingRunStatus.ACTIVE,
            PlantingRunStatus.HARVESTING,
        ):
            self._reassign_plant_slots(key, old_location_key, new_location_key)

        return updated

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
        self,
        run_key: PlantingRunKey,
        entry_key: str,
        entry: PlantingRunEntry,
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
            run.run_type,
            entries,
            run.source_plant_key,
        )

        location_key = run.location_key or "LOC"
        existing_ids = set()
        if run.location_key:
            existing_ids = self._repo.get_existing_ids_at_location(run.location_key)

        plant_specs = self._engine.generate_plant_ids(location_key, entries, existing_ids)

        # Resolve available slots at the run's location
        available_slots = self._get_available_slots(run.location_key)

        # Resolve initial phase per species from lifecycle config
        initial_phases: dict[str, tuple[str, str]] = {}  # species_key -> (phase_key, phase_name)
        if self._phase_repo:
            for entry in entries:
                if entry.species_key not in initial_phases:
                    lifecycle = self._phase_repo.get_lifecycle_by_species(entry.species_key)
                    if lifecycle:
                        growth_phases = self._phase_repo.get_phases_by_lifecycle(lifecycle.key)
                        if growth_phases:
                            first = min(growth_phases, key=lambda gp: gp.sequence_order)
                            initial_phases[entry.species_key] = (first.key or "", first.name)

        now = datetime.now(UTC)
        created_plants = []
        for i, spec in enumerate(plant_specs):
            slot_key = available_slots[i].key if i < len(available_slots) else None
            phase_key, phase_name = initial_phases.get(spec["species_key"], ("", "seedling"))
            plant = PlantInstance(
                instance_id=spec["instance_id"],
                species_key=spec["species_key"],
                cultivar_key=spec.get("cultivar_key"),
                slot_key=slot_key,
                planted_on=date.today(),
                current_phase_key=phase_key or None,
                current_phase_started_at=now,
            )
            created = self._plant_repo.create(plant)
            if created.key:
                self._repo.link_run_to_plant(run_key, created.key)
                # Create initial phase history entry
                if self._phase_repo:
                    history = PhaseHistory(
                        plant_instance_key=created.key,
                        phase_key=phase_key,
                        phase_name=phase_name,
                        entered_at=now,
                        transition_reason="initial",
                    )
                    self._phase_repo.create_phase_history(history)
            # Mark slot as occupied
            if slot_key and self._site_repo:
                slot = available_slots[i]
                slot.currently_occupied = True
                self._site_repo.update_slot(slot_key, slot)
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
            "slots_assigned": min(len(available_slots), len(created_plants)),
        }

    # ── Slot helpers ────────────────────────────────────────────────────

    def _get_available_slots(self, location_key: str | None) -> list:
        """Return unoccupied slots at the given location, sorted by slot_id."""
        if not location_key or not self._site_repo:
            return []
        slots = self._site_repo.get_slots_by_location(location_key)
        return sorted(
            [s for s in slots if not s.currently_occupied and s.key],
            key=lambda s: s.slot_id,
        )

    def _reassign_plant_slots(
        self,
        run_key: PlantingRunKey,
        old_location_key: str | None,
        new_location_key: str | None,
    ) -> None:
        """Clear slot assignments from old location and assign to new location's slots."""
        if not self._site_repo:
            return

        plants_raw = self._repo.get_run_plants(run_key, include_detached=False)

        # Release old slots
        for p in plants_raw:
            slot_key = p.get("slot_key")
            if slot_key:
                plant_key = p.get("_key") or p.get("key", "")
                plant = self._plant_repo.get(plant_key)
                if plant:
                    plant.slot_key = None
                    self._plant_repo.update(plant_key, plant)
                slot = self._site_repo.get_slot_by_key(slot_key)
                if slot:
                    slot.currently_occupied = False
                    self._site_repo.update_slot(slot_key, slot)

        # Assign to new location's available slots
        available_slots = self._get_available_slots(new_location_key)
        for i, p in enumerate(plants_raw):
            if i >= len(available_slots):
                break
            plant_key = p.get("_key") or p.get("key", "")
            plant = self._plant_repo.get(plant_key)
            if plant and available_slots[i].key:
                plant.slot_key = available_slots[i].key
                self._plant_repo.update(plant_key, plant)
                available_slots[i].currently_occupied = True
                self._site_repo.update_slot(available_slots[i].key, available_slots[i])

    def batch_transition(
        self,
        run_key: PlantingRunKey,
        target_phase_key: str,
        target_phase_name: str,
        exclude_keys: set[str] | None = None,
    ) -> dict:
        """Batch phase transition for all eligible plants in the run."""
        run = self.get_run(run_key)
        if run.status not in (PlantingRunStatus.ACTIVE, PlantingRunStatus.HARVESTING):
            raise InvalidRunStateError("batch_transition", run.status.value)

        plants = self._repo.get_run_plants(run_key, include_detached=False)
        eligible, skipped = self._engine.filter_transition_eligible(
            plants,
            target_phase_name,
            exclude_keys,
        )

        transitioned = []
        failed = []
        for plant in eligible:
            plant_key = plant.get("_key", "")
            try:
                existing = self._plant_repo.get_by_key(plant_key)
                if existing:
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

    def batch_remove(
        self,
        run_key: PlantingRunKey,
        reason: str = "batch_remove",
        target_status: str | None = None,
    ) -> dict:
        """Remove all active plants from the run and transition to target status.

        If *target_status* is ``None`` the status is auto-determined:
        ``COMPLETED`` when the run is already in HARVESTING, ``CANCELLED``
        otherwise.
        """
        run = self.get_run(run_key)
        if run.status not in (PlantingRunStatus.ACTIVE, PlantingRunStatus.HARVESTING):
            raise InvalidRunStateError("batch_remove", run.status.value)

        # Resolve final status
        if target_status is not None:
            final = PlantingRunStatus(target_status)
            if final not in (PlantingRunStatus.COMPLETED, PlantingRunStatus.CANCELLED):
                raise InvalidRunStateError("batch_remove", target_status)
        else:
            final = (
                PlantingRunStatus.COMPLETED
                if run.status == PlantingRunStatus.HARVESTING
                else PlantingRunStatus.CANCELLED
            )

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

        run.status = final
        run.completed_at = datetime.now(UTC)
        self._repo.update(run_key, run)

        return {
            "run_key": run_key,
            "removed_count": len(removed),
            "removed_keys": removed,
            "final_status": final.value,
        }

    # ── Phase summaries ─────────────────────────────────────────────

    def get_phase_summary(self, run_key: PlantingRunKey) -> dict:
        summaries = self._repo.get_batch_phase_summaries([run_key])
        return self._build_phase_summary(summaries.get(run_key, []))

    def get_batch_phase_summaries(self, run_keys: list[str]) -> dict[str, dict]:
        raw = self._repo.get_batch_phase_summaries(run_keys)
        return {k: self._build_phase_summary(v) for k, v in raw.items()}

    @staticmethod
    def _build_phase_summary(phases: list[dict]) -> dict:
        all_phases = {p["phase"]: p["cnt"] for p in phases if p.get("phase")}
        total = sum(all_phases.values())
        dominant_phase = None
        dominant_count = 0
        for phase, cnt in all_phases.items():
            if cnt > dominant_count:
                dominant_phase = phase
                dominant_count = cnt
        return {
            "dominant_phase": dominant_phase,
            "dominant_phase_count": dominant_count,
            "total_plant_count": total,
            "all_phases": all_phases,
        }

    # ── Phase timeline ─────────────────────────────────────────────────

    def get_phase_timeline(self, run_key: PlantingRunKey) -> list[dict]:
        """Build per-species phase timeline with completed/current/projected phases."""
        self.get_run(run_key)
        if self._phase_repo is None:
            return []

        entries = self._repo.get_entries(run_key)
        plants_raw = self._repo.get_run_plants(run_key, include_detached=False)

        # Group plants by species_key
        species_plants: dict[str, list[dict]] = {}
        for p in plants_raw:
            sk = p.get("species_key", "")
            species_plants.setdefault(sk, []).append(p)

        # Unique species from entries
        species_keys = list({e.species_key for e in entries})

        timelines = []
        for species_key in species_keys:
            sp_plants = species_plants.get(species_key, [])
            if not sp_plants:
                continue

            # Get lifecycle + phases for this species
            lifecycle = self._phase_repo.get_lifecycle_by_species(species_key)
            if lifecycle is None or lifecycle.key is None:
                continue

            growth_phases = self._phase_repo.get_phases_by_lifecycle(lifecycle.key)
            growth_phases.sort(key=lambda gp: gp.sequence_order)
            if not growth_phases:
                continue

            # Pick representative plant (first one)
            rep_plant = sp_plants[0]
            rep_key = rep_plant.get("_key", "")
            rep_current_phase = rep_plant.get("current_phase", "")

            # Load phase history for representative plant
            history = self._phase_repo.get_phase_history(rep_key)
            history_by_phase: dict[str, dict] = {}
            for h in history:
                history_by_phase[h.phase_name] = {
                    "entered_at": h.entered_at,
                    "exited_at": h.exited_at,
                    "actual_duration_days": h.actual_duration_days,
                }

            # Build timeline entries
            now = datetime.now(UTC)
            phase_entries = []
            last_end: datetime | None = None
            for gp in growth_phases:
                h = history_by_phase.get(gp.name)
                exited = h.get("exited_at") if h else None
                exited_in_past = exited is not None and (exited if exited.tzinfo else exited.replace(tzinfo=UTC)) <= now
                if h and exited_in_past:
                    # Completed phase (exited_at is in the past)
                    phase_entries.append(
                        {
                            "phase_key": gp.key or "",
                            "phase_name": gp.name,
                            "display_name": gp.display_name or gp.name,
                            "description": gp.description or "",
                            "sequence_order": gp.sequence_order,
                            "typical_duration_days": gp.typical_duration_days,
                            "status": "completed",
                            "actual_entered_at": h["entered_at"],
                            "actual_exited_at": h["exited_at"],
                            "actual_duration_days": h.get("actual_duration_days"),
                            "projected_start": None,
                            "projected_end": None,
                        }
                    )
                    last_end = h["exited_at"]
                elif gp.name == rep_current_phase or (h and h.get("entered_at") and not exited_in_past):
                    # Current phase (either matches plant's current_phase, or has
                    # entered_at set with exited_at in the future / not yet set)
                    entered = h["entered_at"] if h else None
                    if entered is None:
                        # Fallback: use current_phase_started_at from plant
                        started_str = rep_plant.get("current_phase_started_at")
                        if started_str:
                            if isinstance(started_str, str):
                                entered = datetime.fromisoformat(started_str)
                            else:
                                entered = started_str
                    # Use future exited_at as projected end, otherwise compute from typical duration
                    proj_end_dt = (
                        exited
                        if (exited and not exited_in_past)
                        else ((entered + timedelta(days=gp.typical_duration_days)) if entered else None)
                    )
                    phase_entries.append(
                        {
                            "phase_key": gp.key or "",
                            "phase_name": gp.name,
                            "display_name": gp.display_name or gp.name,
                            "description": gp.description or "",
                            "sequence_order": gp.sequence_order,
                            "typical_duration_days": gp.typical_duration_days,
                            "status": "current",
                            "actual_entered_at": entered,
                            "actual_exited_at": exited if (exited and not exited_in_past) else None,
                            "actual_duration_days": None,
                            "projected_start": None,
                            "projected_end": proj_end_dt,
                        }
                    )
                    if proj_end_dt:
                        last_end = proj_end_dt
                    elif entered:
                        last_end = entered + timedelta(days=gp.typical_duration_days)
                else:
                    # Projected phase (future)
                    proj_start = last_end
                    proj_end = (proj_start + timedelta(days=gp.typical_duration_days)) if proj_start else None
                    phase_entries.append(
                        {
                            "phase_key": gp.key or "",
                            "phase_name": gp.name,
                            "display_name": gp.display_name or gp.name,
                            "description": gp.description or "",
                            "sequence_order": gp.sequence_order,
                            "typical_duration_days": gp.typical_duration_days,
                            "status": "projected",
                            "actual_entered_at": None,
                            "actual_exited_at": None,
                            "actual_duration_days": None,
                            "projected_start": proj_start,
                            "projected_end": proj_end,
                        }
                    )
                    if proj_end:
                        last_end = proj_end

            timelines.append(
                {
                    "species_key": species_key,
                    "species_name": None,
                    "lifecycle_key": lifecycle.key,
                    "plant_count": len(sp_plants),
                    "phases": phase_entries,
                }
            )

        return timelines

    # ── Batch phase date editing ─────────────────────────────────────

    def batch_update_phase_dates(
        self,
        run_key: PlantingRunKey,
        phase_key: str,
        entered_at: datetime | None = None,
        exited_at: datetime | None = None,
    ) -> dict:
        """Update phase history dates for ALL plants in the run that have a matching phase_key."""
        run = self.get_run(run_key)
        if run.status not in (PlantingRunStatus.ACTIVE, PlantingRunStatus.HARVESTING):
            raise InvalidRunStateError("batch_update_phase_dates", run.status.value)

        if self._phase_repo is None:
            raise ValueError("Phase repository not available")

        if entered_at is not None and exited_at is not None and entered_at >= exited_at:
            raise ValueError("entered_at must be before exited_at")

        plants_raw = self._repo.get_run_plants(run_key, include_detached=False)
        updated_count = 0
        skipped_count = 0

        for plant_data in plants_raw:
            plant_key = plant_data.get("_key", "")
            if not plant_key:
                skipped_count += 1
                continue

            history_entries = self._phase_repo.get_phase_history(plant_key)
            matched = None
            for h in history_entries:
                if h.phase_key == phase_key:
                    matched = h
                    break

            if matched is None or matched.key is None:
                skipped_count += 1
                continue

            if entered_at is not None:
                matched.entered_at = entered_at
            if exited_at is not None:
                matched.exited_at = exited_at

            # Recalculate duration
            if matched.exited_at is not None:
                delta = matched.exited_at - matched.entered_at
                matched.actual_duration_days = delta.days
            else:
                matched.actual_duration_days = None

            self._phase_repo.update_phase_history(matched.key, matched)

            # Update plant's current_phase_started_at if this is the open phase
            if matched.exited_at is None and entered_at is not None:
                plant = self._plant_repo.get_by_key(plant_key)
                if plant:
                    plant.current_phase_started_at = entered_at
                    self._plant_repo.update(plant_key, plant)

            updated_count += 1

        return {
            "run_key": run_key,
            "phase_key": phase_key,
            "updated_count": updated_count,
            "skipped_count": skipped_count,
        }

    # ── Plant management ──────────────────────────────────────────────

    def get_plants(self, run_key: PlantingRunKey, include_detached: bool = False) -> list[dict]:
        self.get_run(run_key)
        return self._repo.get_run_plants(run_key, include_detached)

    def detach_plant(self, run_key: PlantingRunKey, plant_key: PlantID, reason: str) -> None:
        self.get_run(run_key)
        self._repo.detach_plant(run_key, plant_key, reason)

    def get_runs_for_plant(self, plant_key: PlantID) -> list[PlantingRun]:
        return self._repo.get_runs_for_plant(plant_key)

    # ── Nutrient plan assignment ───────────────────────────────────────

    def assign_nutrient_plan(self, run_key: PlantingRunKey, plan_key: str, assigned_by: str = "") -> dict:
        self.get_run(run_key)
        return self._repo.assign_nutrient_plan(run_key, plan_key, assigned_by)

    def get_nutrient_plan(self, run_key: PlantingRunKey) -> dict | None:
        self.get_run(run_key)
        plan_key = self._repo.get_run_nutrient_plan_key(run_key)
        if plan_key is None:
            return None
        if self._nutrient_plan_repo is not None:
            plan = self._nutrient_plan_repo.get_by_key(plan_key)
            if plan:
                return plan.model_dump(mode="json") if hasattr(plan, "model_dump") else plan
        return {"key": plan_key}

    def remove_nutrient_plan(self, run_key: PlantingRunKey) -> bool:
        self.get_run(run_key)
        return self._repo.remove_nutrient_plan(run_key)

    def _build_channel_calendars(
        self,
        plan_key: str,
        run_key: PlantingRunKey,
        days_ahead: int,
    ) -> list[dict]:
        """Build per-channel watering calendars from phase entry schedules.

        Channels with the same channel_id across different phases are merged
        so that each physical channel appears only once with combined dates.
        """
        if self._nutrient_plan_repo is None:
            return []
        phase_entries = self._nutrient_plan_repo.get_phase_entries(plan_key)
        today = date.today()

        merged: dict[str, dict] = {}
        for entry in phase_entries:
            for ch in entry.delivery_channels:
                if not ch.enabled or ch.schedule is None:
                    continue
                last_date = None
                if self._watering_repo is not None:
                    last_date = self._watering_repo.get_last_watering_date_for_run(run_key)
                ch_dates = self._schedule_engine.get_next_watering_dates(
                    ch.schedule,
                    today,
                    days_ahead,
                    last_date,
                )
                method = ch.application_method
                method_str = method.value if hasattr(method, "value") else str(method)
                phase = entry.phase_name
                phase_str = phase.value if hasattr(phase, "value") else str(phase)

                if ch.channel_id in merged:
                    date_set = set(merged[ch.channel_id]["dates"])
                    date_set.update(d.isoformat() for d in ch_dates)
                    merged[ch.channel_id]["dates"] = sorted(date_set)
                else:
                    merged[ch.channel_id] = {
                        "channel_id": ch.channel_id,
                        "label": ch.label or ch.channel_id,
                        "application_method": method_str,
                        "phase_name": phase_str,
                        "dates": sorted(d.isoformat() for d in ch_dates),
                        "times_per_day": ch.schedule.times_per_day,
                    }
        return list(merged.values())

    def get_watering_schedule(self, run_key: PlantingRunKey, days_ahead: int = 14) -> dict:
        """Get watering schedule calendar for the next N days."""
        self.get_run(run_key)
        plan_key = self._repo.get_run_nutrient_plan_key(run_key)
        if plan_key is None:
            return {"run_key": run_key, "has_schedule": False, "dates": []}

        plan = None
        if self._nutrient_plan_repo is not None:
            plan = self._nutrient_plan_repo.get_by_key(plan_key)

        has_plan_schedule = (
            plan is not None and hasattr(plan, "watering_schedule") and plan.watering_schedule is not None
        )

        channel_calendars = self._build_channel_calendars(plan_key, run_key, days_ahead)

        if not has_plan_schedule and not channel_calendars:
            return {"run_key": run_key, "has_schedule": False, "dates": []}

        # Plan-level dates (only when no channel-specific schedules override)
        plan_dates: list[str] = []
        if has_plan_schedule and not channel_calendars:
            last_watering_date = None
            if self._watering_repo is not None:
                last_watering_date = self._watering_repo.get_last_watering_date_for_run(run_key)
            today = date.today()
            dates = self._schedule_engine.get_next_watering_dates(
                plan.watering_schedule,
                today,
                days_ahead,
                last_watering_date,
            )
            plan_dates = [d.isoformat() for d in dates]

        schedule_dump = None
        if has_plan_schedule:
            schedule_dump = plan.watering_schedule.model_dump(mode="json")

        plan_times_per_day = 1
        if has_plan_schedule:
            plan_times_per_day = plan.watering_schedule.times_per_day

        return {
            "run_key": run_key,
            "has_schedule": True,
            "plan_key": plan_key,
            "plan_name": plan.name if plan else "",
            "schedule": schedule_dump,
            "dates": plan_dates,
            "channel_calendars": channel_calendars,
            "times_per_day": plan_times_per_day,
        }
