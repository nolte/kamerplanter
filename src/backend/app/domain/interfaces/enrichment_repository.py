from abc import ABC, abstractmethod

from app.common.types import ExternalMappingKey, SourceKey, SyncRunKey
from app.domain.models.enrichment import ExternalMapping, ExternalSource, SyncRun


class IExternalSourceRepository(ABC):
    @abstractmethod
    def get_all(self) -> list[ExternalSource]: ...

    @abstractmethod
    def get_by_key(self, key: SourceKey) -> ExternalSource | None: ...

    @abstractmethod
    def get_by_source_key(self, source_key: str) -> ExternalSource | None: ...

    @abstractmethod
    def create(self, source: ExternalSource) -> ExternalSource: ...

    @abstractmethod
    def update(self, key: SourceKey, source: ExternalSource) -> ExternalSource: ...


class IExternalMappingRepository(ABC):
    @abstractmethod
    def get_by_key(self, key: ExternalMappingKey) -> ExternalMapping | None: ...

    @abstractmethod
    def get_by_internal(
        self, internal_collection: str, internal_key: str, source_key: str
    ) -> ExternalMapping | None: ...

    @abstractmethod
    def get_all_for_internal(self, internal_collection: str, internal_key: str) -> list[ExternalMapping]: ...

    @abstractmethod
    def create(self, mapping: ExternalMapping) -> ExternalMapping: ...

    @abstractmethod
    def update(self, key: ExternalMappingKey, mapping: ExternalMapping) -> ExternalMapping: ...

    @abstractmethod
    def find_unmapped_species(self, source_key: str) -> list[dict[str, str]]: ...


class ISyncRunRepository(ABC):
    @abstractmethod
    def create(self, run: SyncRun) -> SyncRun: ...

    @abstractmethod
    def update(self, key: SyncRunKey, run: SyncRun) -> SyncRun: ...

    @abstractmethod
    def get_by_source(self, source_key: str, limit: int = 20) -> list[SyncRun]: ...
