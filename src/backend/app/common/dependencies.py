
from arango.database import StandardDatabase

from app.config.settings import settings
from app.data_access.arango.botanical_family_repository import ArangoBotanicalFamilyRepository
from app.data_access.arango.connection import ArangoConnection
from app.data_access.arango.enrichment_repository import (
    ArangoExternalMappingRepository,
    ArangoExternalSourceRepository,
    ArangoSyncRunRepository,
)
from app.data_access.arango.graph_repository import ArangoGraphRepository
from app.data_access.arango.lifecycle_repository import ArangoLifecycleRepository
from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository
from app.data_access.arango.planting_run_repository import ArangoPlantingRunRepository
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.data_access.arango.species_repository import ArangoSpeciesRepository
from app.data_access.arango.substrate_repository import ArangoSubstrateRepository
from app.domain.engines.companion_planting_engine import CompanionPlantingEngine
from app.domain.engines.crop_rotation_validator import CropRotationValidator
from app.domain.engines.enrichment_engine import EnrichmentEngine
from app.domain.engines.planting_run_engine import PlantingRunEngine
from app.domain.services.enrichment_service import EnrichmentService
from app.domain.services.phase_service import PhaseService
from app.domain.services.plant_instance_service import PlantInstanceService
from app.domain.services.planting_run_service import PlantingRunService
from app.domain.services.site_service import SiteService
from app.domain.services.species_service import SpeciesService
from app.domain.services.substrate_service import SubstrateService

_connection: ArangoConnection | None = None


def get_connection() -> ArangoConnection:
    global _connection
    if _connection is None:
        _connection = ArangoConnection(settings)
    return _connection


def get_db() -> StandardDatabase:
    return get_connection().db


def get_species_repo() -> ArangoSpeciesRepository:
    return ArangoSpeciesRepository(get_db())


def get_family_repo() -> ArangoBotanicalFamilyRepository:
    return ArangoBotanicalFamilyRepository(get_db())


def get_lifecycle_repo() -> ArangoLifecycleRepository:
    return ArangoLifecycleRepository(get_db())


def get_site_repo() -> ArangoSiteRepository:
    return ArangoSiteRepository(get_db())


def get_substrate_repo() -> ArangoSubstrateRepository:
    return ArangoSubstrateRepository(get_db())


def get_plant_repo() -> ArangoPlantInstanceRepository:
    return ArangoPlantInstanceRepository(get_db())


def get_graph_repo() -> ArangoGraphRepository:
    return ArangoGraphRepository(get_db())


def get_species_service() -> SpeciesService:
    return SpeciesService(get_species_repo(), get_graph_repo())


def get_site_service() -> SiteService:
    return SiteService(get_site_repo())


def get_substrate_service() -> SubstrateService:
    return SubstrateService(get_substrate_repo())


def get_plant_instance_service() -> PlantInstanceService:
    rotation_validator = CropRotationValidator(get_plant_repo(), get_species_repo())
    companion_engine = CompanionPlantingEngine(get_graph_repo(), get_plant_repo(), get_species_repo())
    return PlantInstanceService(get_plant_repo(), get_site_repo(), rotation_validator, companion_engine)


def get_phase_service() -> PhaseService:
    return PhaseService(get_lifecycle_repo(), get_plant_repo())


def get_source_repo() -> ArangoExternalSourceRepository:
    return ArangoExternalSourceRepository(get_db())


def get_mapping_repo() -> ArangoExternalMappingRepository:
    return ArangoExternalMappingRepository(get_db())


def get_sync_run_repo() -> ArangoSyncRunRepository:
    return ArangoSyncRunRepository(get_db())


def get_enrichment_engine() -> EnrichmentEngine:
    return EnrichmentEngine(get_species_repo(), get_mapping_repo(), get_sync_run_repo(), get_family_repo())


def get_enrichment_service() -> EnrichmentService:
    return EnrichmentService(get_source_repo(), get_mapping_repo(), get_sync_run_repo(), get_enrichment_engine())


def get_planting_run_repo() -> ArangoPlantingRunRepository:
    return ArangoPlantingRunRepository(get_db())


def get_planting_run_service() -> PlantingRunService:
    return PlantingRunService(get_planting_run_repo(), get_plant_repo(), PlantingRunEngine())


def close_connection() -> None:
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None
