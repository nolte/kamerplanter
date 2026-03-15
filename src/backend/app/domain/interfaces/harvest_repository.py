from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.common.types import HarvestBatchKey
    from app.domain.models.harvest import (
        HarvestBatch,
        HarvestIndicator,
        HarvestObservation,
        QualityAssessment,
        YieldMetric,
    )


class IHarvestRepository(ABC):
    @abstractmethod
    def get_all_indicators(self, offset: int = 0, limit: int = 50) -> tuple[list[HarvestIndicator], int]: ...

    @abstractmethod
    def create_indicator(self, indicator: HarvestIndicator) -> HarvestIndicator: ...

    @abstractmethod
    def get_indicators_for_species(self, species_key: str) -> list[HarvestIndicator]: ...

    @abstractmethod
    def create_observation(self, observation: HarvestObservation) -> HarvestObservation: ...

    @abstractmethod
    def get_observations_for_plant(
        self, plant_key: str, offset: int = 0, limit: int = 50,
    ) -> tuple[list[HarvestObservation], int]: ...

    @abstractmethod
    def get_latest_observations_by_indicator(self, plant_key: str) -> list[HarvestObservation]: ...

    @abstractmethod
    def get_all_batches(self, offset: int = 0, limit: int = 50) -> tuple[list[HarvestBatch], int]: ...

    @abstractmethod
    def get_batch_by_key(self, key: HarvestBatchKey) -> HarvestBatch | None: ...

    @abstractmethod
    def create_batch(self, batch: HarvestBatch) -> HarvestBatch: ...

    @abstractmethod
    def update_batch(self, key: HarvestBatchKey, batch: HarvestBatch) -> HarvestBatch: ...

    @abstractmethod
    def create_quality_assessment(self, assessment: QualityAssessment) -> QualityAssessment: ...

    @abstractmethod
    def get_quality_for_batch(self, batch_key: HarvestBatchKey) -> QualityAssessment | None: ...

    @abstractmethod
    def create_yield_metric(self, metric: YieldMetric) -> YieldMetric: ...

    @abstractmethod
    def get_yield_for_batch(self, batch_key: HarvestBatchKey) -> YieldMetric | None: ...

    @abstractmethod
    def get_yield_statistics_for_species(self, species_key: str, days_back: int = 365) -> dict: ...
