from app.common.enums import SyncTrigger
from app.common.exceptions import NotFoundError
from app.domain.engines.enrichment_engine import EnrichmentEngine
from app.domain.interfaces.enrichment_repository import (
    IExternalMappingRepository,
    IExternalSourceRepository,
    ISyncRunRepository,
)
from app.domain.models.enrichment import ExternalMapping, ExternalSource, ExternalSpeciesData, SyncRun
from app.domain.services.adapter_registry import AdapterRegistry


class EnrichmentService:
    def __init__(
        self,
        source_repo: IExternalSourceRepository,
        mapping_repo: IExternalMappingRepository,
        sync_run_repo: ISyncRunRepository,
        engine: EnrichmentEngine,
    ) -> None:
        self._source_repo = source_repo
        self._mapping_repo = mapping_repo
        self._sync_run_repo = sync_run_repo
        self._engine = engine

    def list_sources(self) -> list[ExternalSource]:
        return self._source_repo.get_all()

    def get_source(self, source_key: str) -> ExternalSource:
        source = self._source_repo.get_by_source_key(source_key)
        if source is None:
            raise NotFoundError("ExternalSource", source_key)
        return source

    def trigger_sync(
        self, source_key: str, full_sync: bool = False, triggered_by: SyncTrigger = SyncTrigger.MANUAL
    ) -> SyncRun:
        adapter = AdapterRegistry.get(source_key)
        return self._engine.sync_source(adapter, full_sync=full_sync, triggered_by=triggered_by)

    def get_sync_history(self, source_key: str, limit: int = 20) -> list[SyncRun]:
        return self._sync_run_repo.get_by_source(source_key, limit=limit)

    def get_species_enrichments(self, species_key: str) -> list[ExternalMapping]:
        return self._mapping_repo.get_all_for_internal("species", species_key)

    def accept_enrichment(self, species_key: str, source_key: str, fields: list[str]) -> ExternalMapping:
        return self._engine.accept_fields(species_key, source_key, fields)

    def reject_enrichment(self, species_key: str, source_key: str, fields: list[str]) -> ExternalMapping:
        return self._engine.reject_fields(species_key, source_key, fields)

    def search_external(self, source_key: str, query: str) -> list[ExternalSpeciesData]:
        adapter = AdapterRegistry.get(source_key)
        return adapter.search_species(query)

    def get_source_health(self) -> dict[str, bool]:
        result: dict[str, bool] = {}
        for key in AdapterRegistry.all_keys():
            adapter = AdapterRegistry.get(key)
            try:
                result[key] = adapter.health_check()
            except Exception:
                result[key] = False
        return result
