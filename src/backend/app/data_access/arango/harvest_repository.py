from datetime import UTC, datetime, timedelta

from arango.database import StandardDatabase

from app.common.types import HarvestBatchKey
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


class ArangoHarvestRepository(BaseArangoRepository[HarvestBatch], IHarvestRepository):
    # Base collection HARVEST_BATCHES is tenant-scoped; harvest indicators are a
    # global catalog queried through dedicated raw-AQL methods, not get_all.
    is_tenant_scoped = True
    _model_cls = HarvestBatch

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.HARVEST_BATCHES)
        self._indicators = BaseArangoRepository[HarvestIndicator](db, col.HARVEST_INDICATORS, HarvestIndicator)
        self._observations = BaseArangoRepository[HarvestObservation](db, col.HARVEST_OBSERVATIONS, HarvestObservation)
        self._quality = BaseArangoRepository[QualityAssessment](db, col.QUALITY_ASSESSMENTS, QualityAssessment)
        self._yield = BaseArangoRepository[YieldMetric](db, col.YIELD_METRICS, YieldMetric)

    # ── Indicators ──

    def get_all_indicators(self, offset: int = 0, limit: int = 50) -> tuple[list[HarvestIndicator], int]:
        return self._indicators.get_all(offset, limit)

    def create_indicator(self, indicator: HarvestIndicator) -> HarvestIndicator:
        ind = self._indicators.create(indicator)

        if indicator.species_key:
            self.create_edge(
                col.HAS_HARVEST_INDICATOR,
                f"{col.SPECIES}/{indicator.species_key}",
                f"{col.HARVEST_INDICATORS}/{ind.key}",
            )
        return ind

    def get_indicators_for_species(self, species_key: str) -> list[HarvestIndicator]:
        return self._indicators.find_by_field("species_key", species_key)

    # ── Observations ──

    def create_observation(self, observation: HarvestObservation) -> HarvestObservation:
        obs = self._observations.create(observation, default_now_fields=("observed_at",))

        obs_id = f"{col.HARVEST_OBSERVATIONS}/{obs.key}"
        self.create_edge(col.OBSERVED_FOR_HARVEST, f"{col.PLANT_INSTANCES}/{observation.plant_key}", obs_id)
        if observation.indicator_key:
            self.create_edge(col.USES_INDICATOR, obs_id, f"{col.HARVEST_INDICATORS}/{observation.indicator_key}")

        return obs

    #: Body shared by the observation count and the observation page, so the two
    #: can never drift apart. Filtering only the page would still leak the
    #: *number* of another tenant's observations through ``total`` (#927).
    #:
    #: ``HarvestObservation`` carries no ``tenant_key`` of its own, so the
    #: predicate is taken from the plant the observation is about — the plant is
    #: tenant-scoped and is the thing the caller names in the URL. This is a real
    #: data-access-layer filter, no schema change and no migration.
    _OBSERVATIONS_FOR_PLANT_BODY = """
    FOR doc IN @@observations
      FILTER doc.plant_key == @plant_key
      LET plant = DOCUMENT(CONCAT(@plants, "/", @plant_key))
      FILTER plant != null AND plant.tenant_key == @tenant_key
    """

    def get_observations_for_plant(
        self,
        plant_key: str,
        offset: int = 0,
        limit: int = 50,
        *,
        tenant_key: str,
    ) -> tuple[list[HarvestObservation], int]:
        """A plant's harvest observations **inside one tenant** (#927).

        #927 names only :meth:`get_latest_observations_by_indicator` and files it
        under "callers do check". Neither is accurate for this pair:
        ``GET /t/{slug}/harvest/plants/{plant_key}/observations`` and
        ``…/readiness`` forward the URL key without resolving the plant against
        the caller's tenant at all, so both were exploitable exactly like the five
        named endpoints.
        """
        self._require_tenant_key(tenant_key, "get_observations_for_plant")
        bind_vars = {
            "@observations": col.HARVEST_OBSERVATIONS,
            "plants": col.PLANT_INSTANCES,
            "plant_key": plant_key,
            "tenant_key": tenant_key,
        }
        count_cursor = self._db.aql.execute(
            f"{self._OBSERVATIONS_FOR_PLANT_BODY} COLLECT WITH COUNT INTO cnt RETURN cnt",
            bind_vars=bind_vars,
        )
        total = next(count_cursor, 0)

        cursor = self._db.aql.execute(
            f"{self._OBSERVATIONS_FOR_PLANT_BODY} SORT doc.observed_at DESC LIMIT @offset, @limit RETURN doc",
            bind_vars={**bind_vars, "offset": offset, "limit": limit},
        )
        items = [HarvestObservation(**self._from_doc(doc)) for doc in cursor]
        return items, total

    def get_latest_observations_by_indicator(self, plant_key: str, *, tenant_key: str) -> list[HarvestObservation]:
        """Newest observation per indicator for a plant, **inside one tenant** (#927).

        Same plant-anchored predicate as :meth:`get_observations_for_plant`; this
        is the query behind the harvest-readiness assessment.
        """
        self._require_tenant_key(tenant_key, "get_latest_observations_by_indicator")
        query = f"""
        {self._OBSERVATIONS_FOR_PLANT_BODY}
            COLLECT indicator = doc.indicator_key INTO group
            LET latest = FIRST(
                FOR g IN group
                    SORT g.doc.observed_at DESC
                    LIMIT 1
                    RETURN g.doc
            )
            RETURN latest
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@observations": col.HARVEST_OBSERVATIONS,
                "plants": col.PLANT_INSTANCES,
                "plant_key": plant_key,
                "tenant_key": tenant_key,
            },
        )
        return [HarvestObservation(**self._from_doc(doc)) for doc in cursor if doc]

    # ── Batches ──

    def get_all_batches(
        self,
        offset: int = 0,
        limit: int = 50,
        tenant_key: str | None = None,
    ) -> tuple[list[HarvestBatch], int]:
        return super().get_all(offset, limit, tenant_key=tenant_key)

    def get_batch_by_key(self, key: HarvestBatchKey) -> HarvestBatch | None:
        return super().get_by_key(key)

    def get_batch_or_raise(self, key: HarvestBatchKey) -> HarvestBatch:
        return super().get_or_raise(key)

    def create_batch(self, batch: HarvestBatch) -> HarvestBatch:
        hb = super().create(batch)
        if batch.plant_key:
            plant_id = f"{col.PLANT_INSTANCES}/{batch.plant_key}"
            batch_id = f"{col.HARVEST_BATCHES}/{hb.key}"
            self.create_edge(col.HARVESTED_AS, plant_id, batch_id)
        return hb

    def batch_id_exists(self, batch_id: str) -> bool:
        """Report whether any batch already uses ``batch_id``.

        The ``batch_id`` unique index is global (not tenant-scoped), so this
        lookup is deliberately un-scoped to mirror the constraint the generated
        identifier must satisfy.
        """
        if not batch_id:
            return False
        return bool(self.find_by_field("batch_id", batch_id, limit=1, offset=0))

    def update_batch(self, key: HarvestBatchKey, batch: HarvestBatch) -> HarvestBatch:
        return super().update(key, batch)

    # ── Quality ──

    def create_quality_assessment(self, assessment: QualityAssessment) -> QualityAssessment:
        qa = self._quality.create(assessment, default_now_fields=("assessed_at",))

        self.create_edge(
            col.ASSESSED_BY_QUALITY,
            f"{col.HARVEST_BATCHES}/{assessment.batch_key}",
            f"{col.QUALITY_ASSESSMENTS}/{qa.key}",
        )
        return qa

    def get_quality_for_batch(self, batch_key: HarvestBatchKey) -> QualityAssessment | None:
        results = self._quality.find_by_field(
            "batch_key", batch_key, sort="assessed_at", sort_direction="DESC", offset=0, limit=1
        )
        return results[0] if results else None

    # ── Yield ──

    def create_yield_metric(self, metric: YieldMetric) -> YieldMetric:
        ym = self._yield.create(metric)

        self.create_edge(
            col.HAS_YIELD_METRIC,
            f"{col.HARVEST_BATCHES}/{metric.batch_key}",
            f"{col.YIELD_METRICS}/{ym.key}",
        )
        return ym

    def get_yield_for_batch(self, batch_key: HarvestBatchKey) -> YieldMetric | None:
        return self._yield.find_one_by_field("batch_key", batch_key)

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
