from datetime import UTC, date, datetime

from app.common.enums import ApplicationMethod, ConfirmAction, ReminderType, TaskStatus
from app.common.exceptions import NotFoundError
from app.common.tenant_guard import verify_tenant_ownership
from app.common.types import LocationKey, PlantInstanceKey, WateringEventKey
from app.domain.engines.watering_engine import WateringEngine
from app.domain.engines.watering_volume_engine import VolumeSuggestion, WateringVolumeEngine
from app.domain.interfaces.phase_repository import IPhaseRepository
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
        volume_engine: WateringVolumeEngine | None = None,
        plant_repo=None,
        species_repo=None,
        substrate_repo=None,
        lifecycle_repo=None,
    ) -> None:
        self._repo = repo
        self._engine = engine
        self._site_repo = site_repo
        self._run_repo = run_repo
        self._task_repo = task_repo
        self._feeding_repo = feeding_repo
        self._nutrient_plan_repo = nutrient_plan_repo
        self._care_repo = care_repo
        self._volume_engine = volume_engine or WateringVolumeEngine()
        self._plant_repo = plant_repo
        self._species_repo = species_repo
        self._substrate_repo = substrate_repo
        self._lifecycle_repo = lifecycle_repo

    # ── Create ─────────────────────────────────────────────────────────

    def create_event(self, event: WateringEvent) -> dict:
        """Create a watering event and return it with any warnings."""
        # Look up irrigation system from the first plant's placement
        irrigation_system = None
        first_plant_key = event.plant_keys[0]
        slot = self._site_repo.get_slot_for_plant(first_plant_key)
        if slot is not None:
            location = self._site_repo.get_location_by_key(slot.location_key)
            if location is not None:
                irrigation_system = location.irrigation_system

        warnings = self._engine.validate_and_warn(event, irrigation_system)
        created = self._repo.create(event)
        return {"event": created, "warnings": warnings}

    # ── Read ───────────────────────────────────────────────────────────

    def get_event(self, key: WateringEventKey, tenant_key: str = "") -> WateringEvent:
        event = self._repo.get_by_key(key)
        if event is None:
            raise NotFoundError("WateringEvent", key)
        if tenant_key:
            verify_tenant_ownership(event, tenant_key, "WateringEvent")
        return event

    def list_events(
        self,
        offset: int = 0,
        limit: int = 50,
        tenant_key: str = "",
    ) -> tuple[list[WateringEvent], int]:
        return self._repo.get_all(offset, limit, tenant_key=tenant_key)

    def get_by_plant(
        self,
        plant_key: PlantInstanceKey,
        offset: int = 0,
        limit: int = 50,
    ) -> list[WateringEvent]:
        return self._repo.get_by_plant(plant_key, offset, limit)

    def get_by_location(
        self,
        location_key: LocationKey,
        offset: int = 0,
        limit: int = 50,
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
        channel_id: str | None = None,
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
        plant_keys = [p["_key"] for p in plants if p.get("_key")]
        if not plant_keys:
            raise ValueError("No active plants found in run")

        # Create watering event
        now = datetime.now(UTC)
        event = WateringEvent(
            watered_at=now,
            application_method=watering_schedule.application_method if watering_schedule else ApplicationMethod.DRENCH,
            volume_liters=volume_liters or 1.0,
            plant_keys=plant_keys,
            nutrient_plan_key=plan_key,
            measured_ec=measured_ec,
            measured_ph=measured_ph,
            task_key=task_key,
            channel_id=channel_id,
        )
        created_event = self._repo.create(event)

        # Create feeding events for each plant
        feeding_events_created = 0
        if self._feeding_repo and plan:
            for plant in plants:
                plant_key = plant.get("_key", "")
                if plant_key:
                    method = watering_schedule.application_method if watering_schedule else ApplicationMethod.DRENCH
                    event_key = created_event.key if hasattr(created_event, "key") else None
                    feeding = FeedingEvent(
                        plant_key=plant_key,
                        timestamp=now,
                        application_method=method,
                        volume_applied_liters=volume_liters or 1.0,
                        watering_event_key=event_key,
                        channel_id=channel_id,
                    )
                    self._feeding_repo.create(feeding)
                    feeding_events_created += 1

        # Complete the task
        task_completed = False
        task_doc = self._task_repo.get_by_key(task_key)
        if task_doc:
            self._task_repo.update_fields(
                task_key,
                {
                    "status": TaskStatus.COMPLETED.value,
                    "completed_at": now.isoformat(),
                },
            )
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

    # ── Volume suggestion ─────────────────────────────────────────────

    def suggest_volume(
        self,
        plant_key: PlantInstanceKey,
        reference_date: date | None = None,
        hemisphere: str = "north",
    ) -> VolumeSuggestion:
        """Suggest a watering volume for a plant based on its phase, species, substrate, and container.

        Gathers all relevant data from repositories and delegates to WateringVolumeEngine.
        """

        plant = self._get_plant(plant_key)
        ref_date = reference_date or date.today()

        # Gather species watering guide
        species_vol_min: int | None = None
        species_vol_max: int | None = None
        species_seasonal: list[dict] | None = None
        if self._species_repo and plant.species_key:
            species = self._species_repo.get_by_key(plant.species_key)
            if species:
                # Check cultivar override first
                guide = None
                if plant.cultivar_key and hasattr(self._species_repo, "get_cultivar_by_key"):
                    cultivar = self._species_repo.get_cultivar_by_key(plant.cultivar_key)
                    if cultivar and cultivar.watering_guide_override:
                        guide = cultivar.watering_guide_override
                if guide is None and species.watering_guide:
                    guide = species.watering_guide
                if guide:
                    species_vol_min = guide.volume_ml_min
                    species_vol_max = guide.volume_ml_max
                    species_seasonal = (
                        [adj.model_dump() for adj in guide.seasonal_adjustments] if guide.seasonal_adjustments else None
                    )

        # Gather substrate properties
        water_retention = None
        water_holding_capacity = None
        irrigation_strategy = None
        substrate_type = plant.substrate_type_override
        if self._substrate_repo and plant.substrate_key:
            substrate = self._substrate_repo.get_substrate_by_key(plant.substrate_key)
            if substrate:
                substrate_type = substrate_type or substrate.type
                water_retention = substrate.water_retention
                water_holding_capacity = substrate.water_holding_capacity_percent
                irrigation_strategy = substrate.irrigation_strategy

        # Gather phase requirement profile
        phase_name: str | None = None
        phase_irrigation_vol: int | None = None
        if self._lifecycle_repo and plant.current_phase_key:
            lifecycle_repo: IPhaseRepository = self._lifecycle_repo
            growth_phase = lifecycle_repo.get_phase_by_key(plant.current_phase_key)
            if growth_phase:
                phase_name = growth_phase.name
            if hasattr(lifecycle_repo, "get_requirement_profile"):
                req_profile = lifecycle_repo.get_requirement_profile(plant.current_phase_key)
                if req_profile and req_profile.irrigation_volume_ml_per_plant > 0:
                    phase_irrigation_vol = req_profile.irrigation_volume_ml_per_plant

        return self._volume_engine.suggest_volume(
            container_volume_liters=plant.container_volume_liters,
            substrate_type=substrate_type,
            water_retention=water_retention,
            water_holding_capacity_percent=water_holding_capacity,
            irrigation_strategy=irrigation_strategy,
            phase_name=phase_name,
            phase_irrigation_volume_ml=phase_irrigation_vol,
            species_volume_ml_min=species_vol_min,
            species_volume_ml_max=species_vol_max,
            species_seasonal_adjustments=species_seasonal,
            reference_date=ref_date,
            hemisphere=hemisphere,
        )

    def _get_plant(self, plant_key: PlantInstanceKey):
        """Look up a plant instance."""
        if self._plant_repo:
            plant = self._plant_repo.get_by_key(plant_key)
            if plant:
                return plant
        raise NotFoundError("PlantInstance", plant_key)
