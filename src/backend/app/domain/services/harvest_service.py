from datetime import datetime

from app.common.exceptions import KarenzViolationError, NotFoundError
from app.domain.engines.quality_scoring_engine import QualityScoringEngine
from app.domain.engines.readiness_engine import ReadinessEngine
from app.domain.interfaces.harvest_repository import IHarvestRepository
from app.domain.models.harvest import (
    HarvestBatch,
    HarvestIndicator,
    HarvestObservation,
    QualityAssessment,
    YieldMetric,
)
from app.domain.services.ipm_service import IpmService


class HarvestService:
    def __init__(
        self,
        repo: IHarvestRepository,
        ipm_service: IpmService,
        readiness_engine: ReadinessEngine,
        quality_engine: QualityScoringEngine,
    ) -> None:
        self._repo = repo
        self._ipm = ipm_service
        self._readiness = readiness_engine
        self._quality = quality_engine

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
        self, plant_key: str, offset: int = 0, limit: int = 50,
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

    def list_batches(self, offset: int = 0, limit: int = 50) -> tuple[list[HarvestBatch], int]:
        return self._repo.get_all_batches(offset, limit)

    def get_batch(self, key: str) -> HarvestBatch:
        batch = self._repo.get_batch_by_key(key)
        if not batch:
            raise NotFoundError("HarvestBatch", key)
        return batch

    def create_harvest_batch(self, plant_key: str, batch: HarvestBatch) -> HarvestBatch:
        """Create a harvest batch -- enforces Karenz-Gate."""
        batch.plant_key = plant_key
        harvest_date = batch.harvest_date or datetime.now()

        # KARENZ-GATE: check safety intervals
        can_harvest, blocking = self._ipm.check_harvest_safety(plant_key, harvest_date)
        if not can_harvest:
            first_blocker = blocking[0]
            raise KarenzViolationError(
                first_blocker["active_ingredient"],
                first_blocker["days_remaining"],
            )

        return self._repo.create_batch(batch)

    def update_batch(self, key: str, data: dict) -> HarvestBatch:
        existing = self.get_batch(key)
        allowed = {"harvest_type", "wet_weight_g", "estimated_dry_weight_g",
                    "actual_dry_weight_g", "quality_grade", "harvester", "notes"}
        for field, value in data.items():
            if field in allowed:
                setattr(existing, field, value)
        return self._repo.update_batch(key, existing)

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
