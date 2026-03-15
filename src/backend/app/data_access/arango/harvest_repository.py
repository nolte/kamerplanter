from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.harvest_repository import IHarvestRepository
from app.domain.models.harvest import (
    HarvestBatch,
    HarvestIndicator,
    HarvestObservation,
    QualityAssessment,
    YieldMetric,
)

if TYPE_CHECKING:
    from arango.database import StandardDatabase

    from app.common.types import HarvestBatchKey


class ArangoHarvestRepository(IHarvestRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.HARVEST_BATCHES)

    # ── Indicators ──

    def get_all_indicators(self, offset: int = 0, limit: int = 50) -> tuple[list[HarvestIndicator], int]:
        query = f"FOR doc IN {col.HARVEST_INDICATORS} SORT doc._key LIMIT {offset}, {limit} RETURN doc"
        count_query = f"FOR doc IN {col.HARVEST_INDICATORS} COLLECT WITH COUNT INTO total RETURN total"
        cursor = self._db.aql.execute(query)
        items = [HarvestIndicator(**self._from_doc(doc)) for doc in cursor]
        count_cursor = self._db.aql.execute(count_query)
        total = next(count_cursor, 0)
        return items, total

    def create_indicator(self, indicator: HarvestIndicator) -> HarvestIndicator:
        coll = self._db.collection(col.HARVEST_INDICATORS)
        data = self._to_doc(indicator)
        now = self._now()
        data["created_at"] = now
        data["updated_at"] = now
        result = coll.insert(data, return_new=True)
        ind = HarvestIndicator(**self._from_doc(result["new"]))

        if indicator.species_key:
            self.create_edge(
                col.HAS_HARVEST_INDICATOR,
                f"{col.SPECIES}/{indicator.species_key}",
                f"{col.HARVEST_INDICATORS}/{ind.key}",
            )
        return ind

    def get_indicators_for_species(self, species_key: str) -> list[HarvestIndicator]:
        query = (
            f"FOR doc IN {col.HARVEST_INDICATORS} "
            f"FILTER doc.species_key == @species_key "
            f"RETURN doc"
        )
        cursor = self._db.aql.execute(query, bind_vars={"species_key": species_key})
        return [HarvestIndicator(**self._from_doc(doc)) for doc in cursor]

    # ── Observations ──

    def create_observation(self, observation: HarvestObservation) -> HarvestObservation:
        coll = self._db.collection(col.HARVEST_OBSERVATIONS)
        data = self._to_doc(observation)
        now = self._now()
        data["created_at"] = now
        data["updated_at"] = now
        if not data.get("observed_at"):
            data["observed_at"] = now
        result = coll.insert(data, return_new=True)
        obs = HarvestObservation(**self._from_doc(result["new"]))

        obs_id = f"{col.HARVEST_OBSERVATIONS}/{obs.key}"
        self.create_edge(col.OBSERVED_FOR_HARVEST, f"{col.PLANT_INSTANCES}/{observation.plant_key}", obs_id)
        if observation.indicator_key:
            self.create_edge(col.USES_INDICATOR, obs_id, f"{col.HARVEST_INDICATORS}/{observation.indicator_key}")

        return obs

    def get_observations_for_plant(
        self, plant_key: str, offset: int = 0, limit: int = 50,
    ) -> tuple[list[HarvestObservation], int]:
        query = (
            f"FOR doc IN {col.HARVEST_OBSERVATIONS} "
            f"FILTER doc.plant_key == @plant_key "
            f"SORT doc.observed_at DESC "
            f"LIMIT {offset}, {limit} RETURN doc"
        )
        count_query = (
            f"FOR doc IN {col.HARVEST_OBSERVATIONS} "
            f"FILTER doc.plant_key == @plant_key "
            f"COLLECT WITH COUNT INTO total RETURN total"
        )
        cursor = self._db.aql.execute(query, bind_vars={"plant_key": plant_key})
        items = [HarvestObservation(**self._from_doc(doc)) for doc in cursor]
        count_cursor = self._db.aql.execute(count_query, bind_vars={"plant_key": plant_key})
        total = next(count_cursor, 0)
        return items, total

    def get_latest_observations_by_indicator(self, plant_key: str) -> list[HarvestObservation]:
        query = """
        FOR doc IN harvest_observations
            FILTER doc.plant_key == @plant_key
            COLLECT indicator = doc.indicator_key INTO group
            LET latest = FIRST(
                FOR g IN group
                    SORT g.doc.observed_at DESC
                    LIMIT 1
                    RETURN g.doc
            )
            RETURN latest
        """
        cursor = self._db.aql.execute(query, bind_vars={"plant_key": plant_key})
        return [HarvestObservation(**self._from_doc(doc)) for doc in cursor if doc]

    # ── Batches ──

    def get_all_batches(self, offset: int = 0, limit: int = 50) -> tuple[list[HarvestBatch], int]:
        docs, total = BaseArangoRepository.get_all(self, offset, limit)
        return [HarvestBatch(**doc) for doc in docs], total

    def get_batch_by_key(self, key: HarvestBatchKey) -> HarvestBatch | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        return HarvestBatch(**doc) if doc else None

    def create_batch(self, batch: HarvestBatch) -> HarvestBatch:
        doc = BaseArangoRepository.create(self, batch)
        hb = HarvestBatch(**doc)
        if batch.plant_key:
            plant_id = f"{col.PLANT_INSTANCES}/{batch.plant_key}"
            batch_id = f"{col.HARVEST_BATCHES}/{hb.key}"
            self.create_edge(col.HARVESTED_AS, plant_id, batch_id)
        return hb

    def update_batch(self, key: HarvestBatchKey, batch: HarvestBatch) -> HarvestBatch:
        doc = BaseArangoRepository.update(self, key, batch)
        return HarvestBatch(**doc)

    # ── Quality ──

    def create_quality_assessment(self, assessment: QualityAssessment) -> QualityAssessment:
        coll = self._db.collection(col.QUALITY_ASSESSMENTS)
        data = self._to_doc(assessment)
        now = self._now()
        data["created_at"] = now
        data["updated_at"] = now
        if not data.get("assessed_at"):
            data["assessed_at"] = now
        result = coll.insert(data, return_new=True)
        qa = QualityAssessment(**self._from_doc(result["new"]))

        self.create_edge(
            col.ASSESSED_BY_QUALITY,
            f"{col.HARVEST_BATCHES}/{assessment.batch_key}",
            f"{col.QUALITY_ASSESSMENTS}/{qa.key}",
        )
        return qa

    def get_quality_for_batch(self, batch_key: HarvestBatchKey) -> QualityAssessment | None:
        query = (
            f"FOR doc IN {col.QUALITY_ASSESSMENTS} "
            f"FILTER doc.batch_key == @batch_key "
            f"SORT doc.assessed_at DESC LIMIT 1 RETURN doc"
        )
        cursor = self._db.aql.execute(query, bind_vars={"batch_key": batch_key})
        doc = next(cursor, None)
        return QualityAssessment(**self._from_doc(doc)) if doc else None

    # ── Yield ──

    def create_yield_metric(self, metric: YieldMetric) -> YieldMetric:
        coll = self._db.collection(col.YIELD_METRICS)
        data = self._to_doc(metric)
        now = self._now()
        data["created_at"] = now
        data["updated_at"] = now
        result = coll.insert(data, return_new=True)
        ym = YieldMetric(**self._from_doc(result["new"]))

        self.create_edge(
            col.HAS_YIELD_METRIC,
            f"{col.HARVEST_BATCHES}/{metric.batch_key}",
            f"{col.YIELD_METRICS}/{ym.key}",
        )
        return ym

    def get_yield_for_batch(self, batch_key: HarvestBatchKey) -> YieldMetric | None:
        query = (
            f"FOR doc IN {col.YIELD_METRICS} "
            f"FILTER doc.batch_key == @batch_key "
            f"LIMIT 1 RETURN doc"
        )
        cursor = self._db.aql.execute(query, bind_vars={"batch_key": batch_key})
        doc = next(cursor, None)
        return YieldMetric(**self._from_doc(doc)) if doc else None

    def get_yield_statistics_for_species(self, species_key: str, days_back: int = 365) -> dict:
        cutoff = (datetime.now(UTC) - timedelta(days=days_back)).isoformat()
        query = """
        FOR hb IN harvest_batches
            FOR pi IN plant_instances
                FILTER pi._key == hb.plant_key
                FILTER pi.species_key == @species_key
                FILTER hb.harvest_date >= @cutoff
                FOR ym IN yield_metrics
                    FILTER ym.batch_key == hb._key
                    COLLECT species = @species_key
                    AGGREGATE avg_yield = AVG(ym.total_yield_g),
                              total_yield = SUM(ym.total_yield_g),
                              batch_count = COUNT(1),
                              avg_trim_waste = AVG(ym.trim_waste_percent)
                    RETURN {
                        species_key: species,
                        avg_yield_g: avg_yield,
                        total_yield_g: total_yield,
                        batch_count: batch_count,
                        avg_trim_waste_percent: avg_trim_waste
                    }
        """
        bind = {"species_key": species_key, "cutoff": cutoff}
        cursor = self._db.aql.execute(query, bind_vars=bind)
        result = next(cursor, None)
        return result or {
            "species_key": species_key,
            "avg_yield_g": 0,
            "total_yield_g": 0,
            "batch_count": 0,
            "avg_trim_waste_percent": 0,
        }
