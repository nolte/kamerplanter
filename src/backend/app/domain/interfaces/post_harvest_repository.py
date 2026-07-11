"""REQ-008 — persistence contract for post-harvest batches and their children."""

from abc import ABC, abstractmethod

from app.domain.models.post_harvest import (
    BurpingEvent,
    DryingProgress,
    MoldAlert,
    PostHarvestBatch,
    StorageObservation,
)


class IPostHarvestRepository(ABC):
    # ── Batches ──

    @abstractmethod
    def create_batch(self, batch: PostHarvestBatch) -> PostHarvestBatch: ...

    @abstractmethod
    def get_batch_or_raise(self, key: str) -> PostHarvestBatch: ...

    @abstractmethod
    def get_batch_by_key(self, key: str) -> PostHarvestBatch | None: ...

    @abstractmethod
    def update_batch(self, key: str, batch: PostHarvestBatch) -> PostHarvestBatch: ...

    @abstractmethod
    def delete_batch(self, key: str) -> bool: ...

    @abstractmethod
    def list_batches(
        self,
        tenant_key: str,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[PostHarvestBatch], int]: ...

    @abstractmethod
    def list_for_harvest_batch(
        self,
        harvest_batch_key: str,
        tenant_key: str,
    ) -> list[PostHarvestBatch]: ...

    # ── Drying progress ──

    @abstractmethod
    def create_drying_progress(self, progress: DryingProgress) -> DryingProgress: ...

    @abstractmethod
    def get_latest_drying_progress(self, batch_key: str) -> DryingProgress | None: ...

    @abstractmethod
    def list_drying_progress(self, batch_key: str) -> list[DryingProgress]: ...

    # ── Storage observations ──

    @abstractmethod
    def create_observation(self, observation: StorageObservation) -> StorageObservation: ...

    @abstractmethod
    def list_observations(self, batch_key: str) -> list[StorageObservation]: ...

    # ── Mold alerts ──

    @abstractmethod
    def create_mold_alert(self, alert: MoldAlert) -> MoldAlert: ...

    @abstractmethod
    def list_mold_alerts(self, batch_key: str) -> list[MoldAlert]: ...

    # ── Burping events ──

    @abstractmethod
    def create_burping_event(self, event: BurpingEvent) -> BurpingEvent: ...

    @abstractmethod
    def list_burping_events(self, batch_key: str) -> list[BurpingEvent]: ...
