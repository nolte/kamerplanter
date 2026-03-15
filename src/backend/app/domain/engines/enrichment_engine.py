import hashlib
import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import structlog

from app.common.enums import SyncStatus, SyncTrigger
from app.domain.models.enrichment import (
    ExternalMapping,
    ExternalSpeciesData,
    FieldMapping,
    SyncResult,
    SyncRun,
)

if TYPE_CHECKING:
    from app.data_access.arango.botanical_family_repository import ArangoBotanicalFamilyRepository
    from app.domain.interfaces.enrichment_repository import IExternalMappingRepository, ISyncRunRepository
    from app.domain.interfaces.external_source_adapter import ExternalSourceAdapter
    from app.domain.interfaces.species_repository import ISpeciesRepository

logger = structlog.get_logger()

ENRICHABLE_FIELDS = [
    "common_names",
    "genus",
    "growth_habit",
    "native_habitat",
    "hardiness_zones",
    "synonyms",
    "description",
    "taxonomic_authority",
    "taxonomic_status",
]


class EnrichmentEngine:
    def __init__(
        self,
        species_repo: ISpeciesRepository,
        mapping_repo: IExternalMappingRepository,
        sync_run_repo: ISyncRunRepository,
        family_repo: ArangoBotanicalFamilyRepository | None = None,
    ) -> None:
        self._species_repo = species_repo
        self._mapping_repo = mapping_repo
        self._sync_run_repo = sync_run_repo
        self._family_repo = family_repo

    def sync_source(
        self,
        adapter: ExternalSourceAdapter,
        full_sync: bool = False,
        triggered_by: SyncTrigger = SyncTrigger.MANUAL,
    ) -> SyncRun:
        run = self._sync_run_repo.create(
            SyncRun(
                source_key=adapter.source_key,
                status=SyncStatus.RUNNING,
                triggered_by=triggered_by,
                full_sync=full_sync,
                started_at=datetime.now(UTC),
            )
        )

        try:
            result = self._full_sync(adapter) if full_sync else self._incremental_sync(adapter)

            status = SyncStatus.SUCCESS if not result.errors else SyncStatus.PARTIAL
            run.status = status
            run.total_processed = result.total_processed
            run.new_mappings = result.new_mappings
            run.updated_mappings = result.updated_mappings
            run.errors = result.errors
            run.finished_at = datetime.now(UTC)

        except Exception as e:
            logger.error("sync_failed", source=adapter.source_key, error=str(e))
            run.status = SyncStatus.FAILED
            run.errors = [str(e)]
            run.finished_at = datetime.now(UTC)

        assert run.key is not None
        return self._sync_run_repo.update(run.key, run)

    def _incremental_sync(self, adapter: ExternalSourceAdapter) -> SyncResult:
        result = SyncResult()
        unmapped = self._mapping_repo.find_unmapped_species(adapter.source_key)

        for item in unmapped:
            species_key = item["_key"]
            scientific_name = item["scientific_name"]
            try:
                enriched = adapter.enrich_species(scientific_name, full_sync=False)
                if not enriched:
                    continue

                self._apply_enrichment(species_key, adapter.source_key, enriched)
                result.new_mappings += 1
            except Exception as e:
                result.errors.append(f"Failed to sync {scientific_name}: {e}")
            result.total_processed += 1

        return result

    def _full_sync(self, adapter: ExternalSourceAdapter) -> SyncResult:
        result = SyncResult()
        species_list, _ = self._species_repo.get_all(offset=0, limit=10000)

        for species in species_list:
            assert species.key is not None
            try:
                enriched = adapter.enrich_species(species.scientific_name, full_sync=True)
                if not enriched:
                    result.total_processed += 1
                    continue

                existing = self._mapping_repo.get_by_internal("species", species.key, adapter.source_key)

                if existing:
                    new_checksum = self._compute_checksum(enriched)
                    if existing.checksum != new_checksum:
                        self._apply_enrichment(species.key, adapter.source_key, enriched)
                        result.updated_mappings += 1
                else:
                    self._apply_enrichment(species.key, adapter.source_key, enriched)
                    result.new_mappings += 1
            except Exception as e:
                result.errors.append(f"Failed to sync {species.scientific_name}: {e}")
            result.total_processed += 1

        return result

    def _apply_enrichment(
        self, species_key: str, source_key: str, external_data: ExternalSpeciesData
    ) -> ExternalMapping:
        species = self._species_repo.get_by_key(species_key)
        if species is None:
            raise ValueError(f"Species {species_key} not found")

        field_mappings: dict[str, FieldMapping] = {}
        external_dict = external_data.model_dump()

        for field in ENRICHABLE_FIELDS:
            external_value = external_dict.get(field)
            if not external_value:
                continue

            local_value = getattr(species, field, None)
            is_empty = local_value is None or local_value == "" or local_value == []

            if is_empty:
                field_mappings[field] = FieldMapping(
                    external_value=external_value,
                    local_value=local_value,
                    confidence=0.9,
                    accepted=True,
                    accepted_at=datetime.now(UTC),
                )
                self._species_repo.update_field(species_key, field, external_value)
            else:
                field_mappings[field] = FieldMapping(
                    external_value=external_value,
                    local_value=local_value,
                    confidence=0.7,
                    accepted=False,
                )

        # family_key lookup: if external data has family_name and local family_key is empty
        if self._family_repo and external_data.family_name and not species.family_key:
            family = self._family_repo.get_by_name(external_data.family_name)
            if family and family.key:
                self._species_repo.update_field(species_key, "family_key", family.key)
                field_mappings["family_key"] = FieldMapping(
                    external_value=external_data.family_name,
                    local_value=None,
                    confidence=0.9,
                    accepted=True,
                    accepted_at=datetime.now(UTC),
                )

        existing = self._mapping_repo.get_by_internal("species", species_key, source_key)
        checksum = self._compute_checksum(external_data)

        if existing:
            existing.field_mappings = field_mappings
            existing.checksum = checksum
            existing.external_id = external_data.external_id
            assert existing.key is not None
            return self._mapping_repo.update(existing.key, existing)
        else:
            mapping = ExternalMapping(
                internal_collection="species",
                internal_key=species_key,
                source_key=source_key,
                external_id=external_data.external_id,
                field_mappings=field_mappings,
                checksum=checksum,
            )
            return self._mapping_repo.create(mapping)

    def accept_fields(self, species_key: str, source_key: str, fields: list[str]) -> ExternalMapping:
        mapping = self._mapping_repo.get_by_internal("species", species_key, source_key)
        if mapping is None:
            raise ValueError(f"No mapping found for species={species_key}, source={source_key}")

        for field in fields:
            fm = mapping.field_mappings.get(field)
            if fm and not fm.accepted and fm.external_value is not None:
                fm.accepted = True
                fm.accepted_at = datetime.now(UTC)
                self._species_repo.update_field(species_key, field, fm.external_value)

        assert mapping.key is not None
        return self._mapping_repo.update(mapping.key, mapping)

    def reject_fields(self, species_key: str, source_key: str, fields: list[str]) -> ExternalMapping:
        mapping = self._mapping_repo.get_by_internal("species", species_key, source_key)
        if mapping is None:
            raise ValueError(f"No mapping found for species={species_key}, source={source_key}")

        for field in fields:
            if field in mapping.field_mappings:
                del mapping.field_mappings[field]

        assert mapping.key is not None
        return self._mapping_repo.update(mapping.key, mapping)

    @staticmethod
    def _compute_checksum(data: ExternalSpeciesData) -> str:
        normalized = json.dumps(data.model_dump(), sort_keys=True, default=str)
        return hashlib.sha256(normalized.encode()).hexdigest()
