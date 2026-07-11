"""REQ-008 — ArangoDB repository for the post-harvest batch lifecycle.

The primary ``POST_HARVEST_BATCHES`` collection is tenant-scoped (REQ-024): list
queries require a ``tenant_key`` and the base class refuses to run an unscoped
list (SEC-B4). Child documents (drying progress, observations, mold alerts,
burping events) are always reached through a tenant-owned batch, so they are
filtered by ``batch_key`` and never leak across tenants.
"""

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.post_harvest_repository import IPostHarvestRepository
from app.domain.models.post_harvest import (
    BurpingEvent,
    DryingProgress,
    MoldAlert,
    PostHarvestBatch,
    StorageObservation,
)


class ArangoPostHarvestRepository(BaseArangoRepository[PostHarvestBatch], IPostHarvestRepository):
    is_tenant_scoped = True
    _model_cls = PostHarvestBatch

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.POST_HARVEST_BATCHES)
        self._drying = BaseArangoRepository[DryingProgress](db, col.DRYING_PROGRESS, DryingProgress)
        self._observations = BaseArangoRepository[StorageObservation](db, col.STORAGE_OBSERVATIONS, StorageObservation)
        self._alerts = BaseArangoRepository[MoldAlert](db, col.MOLD_ALERTS, MoldAlert)
        self._burping = BaseArangoRepository[BurpingEvent](db, col.BURPING_EVENTS, BurpingEvent)

    # ── Batches ──

    def create_batch(self, batch: PostHarvestBatch) -> PostHarvestBatch:
        created = super().create(batch, default_now_fields=("started_at",))
        if batch.harvest_batch_key:
            self.create_edge(
                col.POST_HARVEST_OF,
                f"{col.HARVEST_BATCHES}/{batch.harvest_batch_key}",
                f"{col.POST_HARVEST_BATCHES}/{created.key}",
            )
        return created

    def get_batch_or_raise(self, key: str) -> PostHarvestBatch:
        return super().get_or_raise(key)

    def get_batch_by_key(self, key: str) -> PostHarvestBatch | None:
        return super().get_by_key(key)

    def update_batch(self, key: str, batch: PostHarvestBatch) -> PostHarvestBatch:
        return super().update(key, batch)

    def delete_batch(self, key: str) -> bool:
        return super().delete(key)

    def list_batches(
        self,
        tenant_key: str,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[PostHarvestBatch], int]:
        self._require_tenant_key(tenant_key, "list_batches")
        return super().get_all(offset, limit, tenant_key=tenant_key)

    def list_for_harvest_batch(
        self,
        harvest_batch_key: str,
        tenant_key: str,
    ) -> list[PostHarvestBatch]:
        self._require_tenant_key(tenant_key, "list_for_harvest_batch")
        return self.get_page(
            filters=[
                ("harvest_batch_key", "==", harvest_batch_key),
                ("tenant_key", "==", tenant_key),
            ],
            sort="created_at",
            sort_direction="DESC",
        )[0]

    # ── Drying progress ──

    def create_drying_progress(self, progress: DryingProgress) -> DryingProgress:
        created = self._drying.create(progress, default_now_fields=("recorded_at",))
        self.create_edge(
            col.HAS_DRYING_PROGRESS,
            f"{col.POST_HARVEST_BATCHES}/{progress.batch_key}",
            f"{col.DRYING_PROGRESS}/{created.key}",
        )
        return created

    def get_latest_drying_progress(self, batch_key: str) -> DryingProgress | None:
        results = self._drying.find_by_field(
            "batch_key", batch_key, sort="recorded_at", sort_direction="DESC", offset=0, limit=1
        )
        return results[0] if results else None

    def list_drying_progress(self, batch_key: str) -> list[DryingProgress]:
        return self._drying.find_by_field("batch_key", batch_key, sort="recorded_at", sort_direction="DESC")

    # ── Storage observations ──

    def create_observation(self, observation: StorageObservation) -> StorageObservation:
        created = self._observations.create(observation, default_now_fields=("observed_at",))
        self.create_edge(
            col.HAS_STORAGE_OBSERVATION,
            f"{col.POST_HARVEST_BATCHES}/{observation.batch_key}",
            f"{col.STORAGE_OBSERVATIONS}/{created.key}",
        )
        return created

    def list_observations(self, batch_key: str) -> list[StorageObservation]:
        return self._observations.find_by_field("batch_key", batch_key, sort="observed_at", sort_direction="DESC")

    # ── Mold alerts ──

    def create_mold_alert(self, alert: MoldAlert) -> MoldAlert:
        created = self._alerts.create(alert, default_now_fields=("triggered_at",))
        self.create_edge(
            col.TRIGGERED_MOLD_ALERT,
            f"{col.POST_HARVEST_BATCHES}/{alert.batch_key}",
            f"{col.MOLD_ALERTS}/{created.key}",
        )
        return created

    def list_mold_alerts(self, batch_key: str) -> list[MoldAlert]:
        return self._alerts.find_by_field("batch_key", batch_key, sort="triggered_at", sort_direction="DESC")

    # ── Burping events ──

    def create_burping_event(self, event: BurpingEvent) -> BurpingEvent:
        created = self._burping.create(event, default_now_fields=("burped_at",))
        self.create_edge(
            col.HAS_BURPING_EVENT,
            f"{col.POST_HARVEST_BATCHES}/{event.batch_key}",
            f"{col.BURPING_EVENTS}/{created.key}",
        )
        return created

    def list_burping_events(self, batch_key: str) -> list[BurpingEvent]:
        return self._burping.find_by_field("batch_key", batch_key, sort="burped_at", sort_direction="DESC")
