from datetime import date, datetime
from uuid import uuid4

from app.common.datetimes import ensure_aware_utc, now_utc
from app.common.enums import TerminationType
from app.common.exceptions import KarenzViolationError, NotFoundError
from app.common.tenant_guard import verify_tenant_ownership
from app.domain.engines.phase_transition_engine import PhaseTransitionEngine
from app.domain.engines.quality_scoring_engine import QualityScoringEngine
from app.domain.engines.readiness_engine import ReadinessEngine
from app.domain.interfaces.harvest_repository import IHarvestRepository
from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
from app.domain.interfaces.planting_run_repository import IPlantingRunRepository
from app.domain.models.harvest import (
    HarvestBatch,
    HarvestIndicator,
    HarvestObservation,
    QualityAssessment,
    YieldMetric,
)
from app.domain.models.plant_instance import PlantInstance
from app.domain.services.ipm_service import IpmService


class HarvestService:
    def __init__(
        self,
        repo: IHarvestRepository,
        ipm_service: IpmService,
        readiness_engine: ReadinessEngine,
        quality_engine: QualityScoringEngine,
        plant_repo: IPlantInstanceRepository | None = None,
        run_repo: IPlantingRunRepository | None = None,
        phase_engine: PhaseTransitionEngine | None = None,
    ) -> None:
        self._repo = repo
        self._ipm = ipm_service
        self._readiness = readiness_engine
        self._quality = quality_engine
        # REQ-007 / REQ-003 E5 — the explicit "Ernte abschließen" action ends a
        # plant's lifecycle through the phase engine. Optional so the batch/karenz
        # tests can build the service without them; the complete-* methods raise a
        # clear error if invoked while unwired.
        self._plant_repo = plant_repo
        self._run_repo = run_repo
        self._phase_engine = phase_engine

    # ── Indicators ──

    def list_indicators(self, offset: int = 0, limit: int = 50) -> tuple[list[HarvestIndicator], int]:
        return self._repo.get_all_indicators(offset, limit)

    def create_indicator(self, indicator: HarvestIndicator) -> HarvestIndicator:
        return self._repo.create_indicator(indicator)

    def get_indicators_for_species(self, species_key: str) -> list[HarvestIndicator]:
        return self._repo.get_indicators_for_species(species_key)

    # ── Observations ──

    def record_observation(self, plant_key: str, observation: HarvestObservation) -> HarvestObservation:
        observation.plant_key = plant_key
        return self._repo.create_observation(observation)

    def get_observations(
        self,
        plant_key: str,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[HarvestObservation], int]:
        return self._repo.get_observations_for_plant(plant_key, offset, limit)

    # ── Readiness Assessment ──

    def assess_readiness(self, plant_key: str) -> dict:
        observations = self._repo.get_latest_observations_by_indicator(plant_key)
        if not observations:
            return {
                "overall_score": 0,
                "recommendation": "immature",
                "estimated_days": None,
                "indicators": [],
            }

        indicator_keys = {obs.indicator_key for obs in observations if obs.indicator_key}
        # Build reliability map
        reliabilities: dict[str, float] = {}
        for obs in observations:
            if obs.indicator_key:
                reliabilities[obs.indicator_key] = 0.5  # Default

        # Try to get actual reliability scores from indicators
        for _key in indicator_keys:
            indicators = self._repo.get_all_indicators(0, 1000)
            for ind in indicators[0]:
                if ind.key in indicator_keys:
                    reliabilities[ind.key or ""] = ind.reliability_score

        obs_dicts = [
            {
                "indicator_key": obs.indicator_key,
                "ripeness_assessment": obs.ripeness_assessment,
                "days_to_harvest_estimate": obs.days_to_harvest_estimate,
            }
            for obs in observations
        ]
        return self._readiness.assess_readiness(obs_dicts, reliabilities)

    # ── Harvest Batches (with Karenz-Gate) ──

    def list_batches(self, offset: int = 0, limit: int = 50, tenant_key: str = "") -> tuple[list[HarvestBatch], int]:
        return self._repo.get_all_batches(offset, limit, tenant_key=tenant_key)

    def get_batch(self, key: str, tenant_key: str = "") -> HarvestBatch:
        batch = self._repo.get_batch_or_raise(key)
        if tenant_key:
            verify_tenant_ownership(batch, tenant_key, "HarvestBatch")
        return batch

    def create_harvest_batch(self, plant_key: str, batch: HarvestBatch) -> HarvestBatch:
        """Create a harvest batch -- enforces Karenz-Gate.

        When the caller leaves ``batch_id`` blank a deterministic, collision-free
        identifier is generated so a second batch for the same plant on the same
        day no longer trips the unique ``batch_id`` index (issue #744).
        """
        batch.plant_key = plant_key
        harvest_date = ensure_aware_utc(batch.harvest_date) or now_utc()

        # KARENZ-GATE: check safety intervals
        can_harvest, blocking = self._ipm.check_harvest_safety(plant_key, harvest_date)
        if not can_harvest:
            first_blocker = blocking[0]
            raise KarenzViolationError(
                first_blocker["active_ingredient"],
                first_blocker["days_remaining"],
            )

        if not batch.batch_id.strip():
            batch.batch_id = self._generate_batch_id(plant_key, harvest_date)

        return self._repo.create_batch(batch)

    def _generate_batch_id(self, plant_key: str, harvest_date: datetime) -> str:
        """Build a deterministic, collision-free ``batch_id`` for a blank input.

        Base form is ``HARVEST-<YYYYMMDD>-<plant_key>``. If a batch for the same
        plant already exists on that day, a numeric suffix (``-2``, ``-3`` …) is
        appended until a free identifier is found; an exhausted range falls back
        to a short random suffix. The unique ``batch_id`` index stays the
        authoritative backstop against concurrent races.
        """
        day = harvest_date.strftime("%Y%m%d")
        base = f"HARVEST-{day}-{plant_key or 'unassigned'}"
        if not self._repo.batch_id_exists(base):
            return base
        for suffix in range(2, 1000):
            candidate = f"{base}-{suffix}"
            if not self._repo.batch_id_exists(candidate):
                return candidate
        return f"{base}-{uuid4().hex[:8]}"

    def update_batch(self, key: str, data: dict) -> HarvestBatch:
        existing = self.get_batch(key)
        allowed = {
            "harvest_type",
            "wet_weight_g",
            "estimated_dry_weight_g",
            "actual_dry_weight_g",
            "quality_grade",
            "harvester",
            "notes",
        }
        for field, value in data.items():
            if field in allowed:
                setattr(existing, field, value)
        return self._repo.update_batch(key, existing)

    # ── Explicit harvest completion (REQ-007 / REQ-003 E5) ──

    def complete_harvest(
        self,
        plant_key: str,
        tenant_key: str = "",
        on_date: date | None = None,
    ) -> PlantInstance:
        """Explicitly finish a plant's harvest and end its lifecycle.

        This is the operator's explicit "done" signal. It transitions the plant
        instance to its terminal ``harvested`` state through the phase engine —
        which freezes the open phase-history entry and sets
        ``termination_type=HARVESTED`` + ``removed_on`` — never a raw state write
        and never a backward transition. Creating harvest batches never
        auto-terminates: partial/multiple harvests (several open batches) stay
        allowed and are independent of this call (Karenz is gated per batch, not
        here). Idempotent: an already-terminated or already-removed plant is
        returned unchanged, so a double-complete cannot re-terminate it.
        """
        if self._plant_repo is None or self._phase_engine is None:
            raise RuntimeError("complete_harvest requires plant_repo and phase_engine to be wired")

        plant = self._plant_repo.get_by_key(plant_key)
        if plant is None:
            raise NotFoundError("PlantInstance", plant_key)
        if tenant_key:
            verify_tenant_ownership(plant, tenant_key, "PlantInstance")

        if plant.termination_type is not None or plant.removed_on is not None:
            return plant

        return self._phase_engine.terminate(plant_key, TerminationType.HARVESTED, on_date=on_date)

    def complete_harvest_for_run(
        self,
        run_key: str,
        tenant_key: str = "",
        on_date: date | None = None,
    ) -> dict:
        """Explicitly finish a whole run's harvest.

        Terminates every *still-active* instance of the run as ``harvested`` via
        the phase engine. An instance counts as active while neither
        ``removed_on`` nor ``termination_type`` is set; already-terminated or
        removed instances are skipped (no double-/backward transition). Detached
        (standalone) plants are excluded — they are managed on their own path.
        """
        if self._run_repo is None or self._plant_repo is None or self._phase_engine is None:
            raise RuntimeError("complete_harvest_for_run requires run_repo, plant_repo and phase_engine to be wired")

        run = self._run_repo.get_or_raise(run_key)
        if tenant_key:
            verify_tenant_ownership(run, tenant_key, "PlantingRun")

        completed: list[str] = []
        for row in self._run_repo.get_run_plants(run_key, include_detached=False):
            plant_key = row.get("_key") or row.get("key", "")
            if not plant_key:
                continue
            plant = self._plant_repo.get_by_key(plant_key)
            if plant is None:
                continue
            if plant.termination_type is not None or plant.removed_on is not None:
                continue
            self._phase_engine.terminate(plant_key, TerminationType.HARVESTED, on_date=on_date)
            completed.append(plant_key)

        return {
            "run_key": run_key,
            "completed_count": len(completed),
            "completed_keys": completed,
        }

    # ── Quality Assessment ──

    def create_quality_assessment(self, batch_key: str, assessment: QualityAssessment) -> QualityAssessment:
        self.get_batch(batch_key)
        assessment.batch_key = batch_key

        score, grade = self._quality.calculate_overall_score(
            assessment.appearance_score,
            assessment.aroma_score,
            assessment.color_score,
            assessment.defects,
        )
        assessment.overall_score = score
        assessment.grade = grade
        return self._repo.create_quality_assessment(assessment)

    def get_quality(self, batch_key: str) -> QualityAssessment | None:
        return self._repo.get_quality_for_batch(batch_key)

    # ── Yield Metrics ──

    def create_yield_metric(self, batch_key: str, metric: YieldMetric) -> YieldMetric:
        self.get_batch(batch_key)
        metric.batch_key = batch_key
        return self._repo.create_yield_metric(metric)

    def get_yield(self, batch_key: str) -> YieldMetric | None:
        return self._repo.get_yield_for_batch(batch_key)

    def get_yield_stats(self, species_key: str, days_back: int = 365) -> dict:
        return self._repo.get_yield_statistics_for_species(species_key, days_back)
