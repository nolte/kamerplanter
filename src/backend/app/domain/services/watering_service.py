from datetime import UTC, date, datetime

import structlog

from app.common.enums import ApplicationMethod, ConfirmAction, ReminderType, TaskStatus
from app.common.exceptions import NotFoundError
from app.common.tenant_guard import verify_tenant_ownership
from app.common.types import LocationKey, PlantInstanceKey, WateringEventKey
from app.domain.engines.watering_engine import WateringEngine
from app.domain.engines.watering_volume_engine import VolumeSuggestion, WateringVolumeEngine
from app.domain.interfaces.phase_repository import IPhaseRepository
from app.domain.interfaces.phase_sequence_repository import IPhaseSequenceRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.interfaces.watering_repository import IWateringRepository
from app.domain.models.care_reminder import CareConfirmation
from app.domain.models.feeding_event import FeedingEvent
from app.domain.models.watering_event import WateringEvent

logger = structlog.get_logger(__name__)

# ── Soil-moisture sensor override (REQ-005) ────────────────────────────────
# The metric_type a soil-moisture sensor is registered under (free-form on the
# Sensor model). A live reading for the plant's location beats the static default.
SOIL_MOISTURE_METRIC = "soil_moisture"
# Volumetric water content (% VWC) thresholds. At/above WET the root zone is
# saturated → suppress the event; at/below DRY the full recommended volume stands;
# in between the volume scales linearly. Deliberately conservative — the override
# only ever *reduces* volume, so the waterlogging cap remains the upper bound.
_SENSOR_WET_MOISTURE_PCT = 70.0
_SENSOR_DRY_MOISTURE_PCT = 30.0


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
        phase_seq_repo: IPhaseSequenceRepository | None = None,
        sensor_service=None,
        irrigation_demand_repo=None,
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
        self._phase_seq_repo = phase_seq_repo
        self._sensor_service = sensor_service
        self._irrigation_demand_repo = irrigation_demand_repo

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
        event = self._repo.get_or_raise(key)
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
        et_net_demand_ml: float | None = None,
    ) -> VolumeSuggestion:
        """Suggest a watering volume for a plant based on its phase, species, substrate, and container.

        Gathers all relevant data from repositories and delegates to WateringVolumeEngine,
        then applies the REQ-005/037 override precedence — ``ET/sensor > static default``,
        with the ``waterlogging_tolerance`` cap (applied inside the resolver) as the
        upper bound:

        * ``et_net_demand_ml`` is the **REQ-037 evapotranspiration seam** — a computed
          net irrigation demand (ml) that, when supplied, replaces the static per-event
          volume. When it is ``None`` and an irrigation-demand repository is wired, the
          latest materialised :class:`IrrigationDemand` for the plant's run is resolved
          and its recommended volume is split across the run's active plants (REQ-037).
          A capped demand of ``0`` means "rain covered it — irrigate nothing".
        * a live soil-moisture sensor reading for the plant's location (REQ-005) scales
          the recommended volume down when the root zone is already wet.
        """

        plant = self._get_plant(plant_key)
        ref_date = reference_date or date.today()

        # Gather species watering guide + root-zone waterlogging tolerance
        species_vol_min: int | None = None
        species_vol_max: int | None = None
        species_seasonal: list[dict] | None = None
        waterlogging_tolerance: str | None = None
        if self._species_repo and plant.species_key:
            species = self._species_repo.get_by_key(plant.species_key)
            if species:
                waterlogging_tolerance = getattr(species, "waterlogging_tolerance", None)
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

        # Gather phase requirement profile — prefer PhaseSequence, fallback to LifecycleConfig
        phase_name: str | None = None
        phase_irrigation_vol: int | None = None
        if plant.current_phase_key:
            resolved_from_seq = False

            # Try PhaseSequence first: current_phase_key may be a PhaseSequenceEntry key
            if self._phase_seq_repo:
                entry = self._phase_seq_repo.get_entry_by_key(plant.current_phase_key)
                if entry:
                    defn = self._phase_seq_repo.get_definition_by_key(entry.phase_definition_key)
                    if defn:
                        phase_name = defn.name
                        resolved_from_seq = True

            # Fallback to LifecycleConfig
            if not resolved_from_seq and self._lifecycle_repo:
                lifecycle_repo: IPhaseRepository = self._lifecycle_repo
                growth_phase = lifecycle_repo.get_phase_by_key(plant.current_phase_key)
                if growth_phase:
                    phase_name = growth_phase.name
                if hasattr(lifecycle_repo, "get_requirement_profile"):
                    req_profile = lifecycle_repo.get_requirement_profile(plant.current_phase_key)
                    if req_profile and req_profile.irrigation_volume_ml_per_plant > 0:
                        phase_irrigation_vol = req_profile.irrigation_volume_ml_per_plant

        suggestion = self._volume_engine.suggest_volume(
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
            waterlogging_tolerance=waterlogging_tolerance,
            reference_date=ref_date,
            hemisphere=hemisphere,
        )

        # ── ET override (REQ-037 seam) — beats the static default when supplied ──
        if et_net_demand_ml is None:
            et_net_demand_ml = self._latest_irrigation_demand_ml(plant)
        if et_net_demand_ml is not None and et_net_demand_ml >= 0:
            suggestion = self._apply_volume_override(
                suggestion,
                new_volume_ml=et_net_demand_ml,
                source="evapotranspiration_demand",
                note=f"et_net_demand={round(et_net_demand_ml)}ml",
                allow_zero=True,  # an ET demand of 0 means "irrigate nothing", not 10 ml
            )

        # ── Live soil-moisture sensor override (REQ-005) — reduces when wet ──
        moisture = self._latest_soil_moisture_percent(plant_key)
        if moisture is not None:
            factor = self._moisture_volume_factor(moisture)
            if factor < 1.0:
                suggestion = self._apply_volume_override(
                    suggestion,
                    new_volume_ml=suggestion.volume_ml * factor,
                    source="sensor_soil_moisture",
                    note=f"soil_moisture={round(moisture)}%→x{factor:.2f}",
                    allow_zero=True,
                )

        return suggestion

    # ── Override helpers (REQ-005/037) ─────────────────────────────────────

    def _latest_irrigation_demand_ml(self, plant) -> float | None:  # noqa: ANN001 — PlantInstance
        """Per-plant ET net demand (ml) from the latest run-level IrrigationDemand.

        Resolves the plant's most recent planting run, reads the latest materialised
        :class:`IrrigationDemand` for it and splits the run's recommended volume
        (litres for the whole growing area) evenly across the run's active plants.
        Returns ``None`` when no repo/run/demand is available — the caller then keeps
        the static recommendation. A capped demand of ``0`` returns ``0.0`` (suppress).
        """
        if self._irrigation_demand_repo is None or self._run_repo is None:
            return None
        tenant_key = getattr(plant, "tenant_key", "") or ""
        plant_key = plant.key if hasattr(plant, "key") else None
        if not plant_key:
            return None
        try:
            runs = self._run_repo.get_runs_for_plant(plant_key)
        except Exception as exc:  # noqa: BLE001 — never fail volume suggestion on lookup error
            logger.warning("irrigation_demand_run_lookup_failed", plant_key=plant_key, error=str(exc))
            return None
        for run in runs:
            if not run.key:
                continue
            demand = self._irrigation_demand_repo.get_latest_for_run(run.key, tenant_key)
            if demand is None:
                continue
            plants = self._run_repo.get_run_plants(run.key, include_detached=False)
            plant_count = max(1, len([p for p in plants if p.get("_key")]))
            per_plant_liters = demand.recommended_volume_liters / plant_count
            return per_plant_liters * 1000.0
        return None

    def _latest_soil_moisture_percent(self, plant_key: PlantInstanceKey) -> float | None:
        """Latest live soil-moisture reading (% VWC) for the plant's location, or None.

        Resolves plant → slot → location, finds a ``soil_moisture`` sensor there and
        read-throughs its live Home Assistant state (REQ-005 semi-automatic tier).
        Returns None when no sensor service, location, sensor, or live value is available
        — the caller then falls back to the static recommendation.
        """
        if self._sensor_service is None:
            return None
        slot = self._site_repo.get_slot_for_plant(plant_key)
        if slot is None or not getattr(slot, "location_key", None):
            return None
        try:
            sensors = self._sensor_service.get_sensors_for_location(slot.location_key)
        except Exception as exc:
            # Don't fail the volume suggestion on a sensor-lookup error — fall back to
            # the static recommendation, but log so a real outage is distinguishable
            # from "location has no soil-moisture sensor".
            logger.warning(
                "soil_moisture_sensor_lookup_failed",
                plant_key=plant_key,
                location_key=slot.location_key,
                error=str(exc),
            )
            return None
        moisture_sensors = [
            s for s in sensors if s.metric_type == SOIL_MOISTURE_METRIC and getattr(s, "is_active", True)
        ]
        if not moisture_sensors:
            return None
        live = self._sensor_service.get_live_state_for_sensors(moisture_sensors)
        entry = (live.get("values") or {}).get(SOIL_MOISTURE_METRIC)
        value = entry.get("value") if entry else None
        # Avoid a tuple-except (a known ruff-format 0.15.x mangling trap) — narrow by type.
        if isinstance(value, bool):
            return None
        if isinstance(value, int | float):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return None
        return None

    @staticmethod
    def _moisture_volume_factor(moisture_percent: float) -> float:
        """Map a soil-moisture reading (% VWC) to a volume factor in [0, 1]."""
        if moisture_percent >= _SENSOR_WET_MOISTURE_PCT:
            return 0.0
        if moisture_percent <= _SENSOR_DRY_MOISTURE_PCT:
            return 1.0
        span = _SENSOR_WET_MOISTURE_PCT - _SENSOR_DRY_MOISTURE_PCT
        return (_SENSOR_WET_MOISTURE_PCT - moisture_percent) / span

    @staticmethod
    def _apply_volume_override(
        suggestion: VolumeSuggestion,
        *,
        new_volume_ml: float,
        source: str,
        note: str,
        allow_zero: bool = False,
    ) -> VolumeSuggestion:
        """Return a copy of the suggestion with an override applied to the volume.

        Scales min/max by the same ratio so the range keeps its shape, records the
        override in ``adjustments`` and re-labels ``source`` so the API surfaces which
        input drove the recommendation.
        """
        floor = 0 if allow_zero else 10
        new_ml = max(floor, round(new_volume_ml))
        prev_ml = suggestion.volume_ml
        scale = (new_ml / prev_ml) if prev_ml > 0 else 1.0
        return suggestion.model_copy(
            update={
                "volume_ml": new_ml,
                "volume_ml_min": max(floor, round(suggestion.volume_ml_min * scale)),
                "volume_ml_max": max(floor, round(suggestion.volume_ml_max * scale)),
                "source": source,
                "adjustments": [*suggestion.adjustments, note],
            }
        )

    def _get_plant(self, plant_key: PlantInstanceKey):
        """Look up a plant instance."""
        if self._plant_repo:
            plant = self._plant_repo.get_by_key(plant_key)
            if plant:
                return plant
        raise NotFoundError("PlantInstance", plant_key)
