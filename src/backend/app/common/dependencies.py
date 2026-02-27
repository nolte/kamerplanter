from arango.database import StandardDatabase

from app.config.settings import settings
from app.data_access.arango.auth_provider_repository import ArangoAuthProviderRepository
from app.data_access.arango.botanical_family_repository import ArangoBotanicalFamilyRepository
from app.data_access.arango.connection import ArangoConnection
from app.data_access.arango.enrichment_repository import (
    ArangoExternalMappingRepository,
    ArangoExternalSourceRepository,
    ArangoSyncRunRepository,
)
from app.data_access.arango.feeding_repository import ArangoFeedingRepository
from app.data_access.arango.fertilizer_repository import ArangoFertilizerRepository
from app.data_access.arango.graph_repository import ArangoGraphRepository
from app.data_access.arango.harvest_repository import ArangoHarvestRepository
from app.data_access.arango.invitation_repository import ArangoInvitationRepository
from app.data_access.arango.ipm_repository import ArangoIpmRepository
from app.data_access.arango.lifecycle_repository import ArangoLifecycleRepository
from app.data_access.arango.location_assignment_repository import ArangoLocationAssignmentRepository
from app.data_access.arango.membership_repository import ArangoMembershipRepository
from app.data_access.arango.nutrient_plan_repository import ArangoNutrientPlanRepository
from app.data_access.arango.oidc_config_repository import ArangoOidcConfigRepository
from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository
from app.data_access.arango.planting_run_repository import ArangoPlantingRunRepository
from app.data_access.arango.refresh_token_repository import ArangoRefreshTokenRepository
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.data_access.arango.species_repository import ArangoSpeciesRepository
from app.data_access.arango.substrate_repository import ArangoSubstrateRepository
from app.data_access.arango.tank_repository import ArangoTankRepository
from app.data_access.arango.task_repository import ArangoTaskRepository
from app.data_access.arango.tenant_repository import ArangoTenantRepository
from app.data_access.arango.user_repository import ArangoUserRepository
from app.data_access.arango.watering_repository import ArangoWateringRepository
from app.data_access.external.console_email_adapter import ConsoleEmailAdapter
from app.data_access.external.smtp_email_adapter import SmtpEmailAdapter
from app.domain.engines.companion_planting_engine import CompanionPlantingEngine
from app.domain.engines.crop_rotation_validator import CropRotationValidator
from app.domain.engines.dependency_resolver import DependencyResolver
from app.domain.engines.enrichment_engine import EnrichmentEngine
from app.domain.engines.hst_validator import HSTValidator
from app.domain.engines.inspection_scheduler import InspectionScheduler
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.nutrient_plan_engine import NutrientPlanValidator
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.planting_run_engine import PlantingRunEngine
from app.domain.engines.quality_scoring_engine import QualityScoringEngine
from app.domain.engines.readiness_engine import ReadinessEngine
from app.domain.engines.resistance_engine import ResistanceManager
from app.domain.engines.safety_interval_engine import SafetyIntervalValidator
from app.domain.engines.tank_engine import TankEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.engines.watering_engine import WateringEngine
from app.domain.interfaces.email_service import IEmailService
from app.domain.services.auth_service import AuthService
from app.domain.services.enrichment_service import EnrichmentService
from app.domain.services.feeding_service import FeedingService
from app.domain.services.fertilizer_service import FertilizerService
from app.domain.services.harvest_service import HarvestService
from app.domain.services.ipm_service import IpmService
from app.domain.services.nutrient_plan_service import NutrientPlanService
from app.domain.services.phase_service import PhaseService
from app.domain.services.plant_instance_service import PlantInstanceService
from app.domain.services.planting_run_service import PlantingRunService
from app.domain.services.site_service import SiteService
from app.domain.services.species_service import SpeciesService
from app.domain.services.substrate_service import SubstrateService
from app.domain.services.tank_service import TankService
from app.domain.services.task_service import TaskService
from app.domain.services.tenant_service import TenantService
from app.domain.services.user_service import UserService
from app.domain.services.watering_service import WateringService

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
    rotation_validator = CropRotationValidator(get_plant_repo(), get_species_repo(), get_graph_repo())
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


def get_tank_repo() -> ArangoTankRepository:
    return ArangoTankRepository(get_db())


def get_tank_service() -> TankService:
    return TankService(get_tank_repo(), TankEngine())


def get_fertilizer_repo() -> ArangoFertilizerRepository:
    return ArangoFertilizerRepository(get_db())


def get_nutrient_plan_repo() -> ArangoNutrientPlanRepository:
    return ArangoNutrientPlanRepository(get_db())


def get_feeding_repo() -> ArangoFeedingRepository:
    return ArangoFeedingRepository(get_db())


def get_fertilizer_service() -> FertilizerService:
    return FertilizerService(get_fertilizer_repo())


def get_nutrient_plan_service() -> NutrientPlanService:
    return NutrientPlanService(
        get_nutrient_plan_repo(),
        get_fertilizer_repo(),
        NutrientPlanValidator(),
    )


def get_feeding_service() -> FeedingService:
    return FeedingService(get_feeding_repo())


def get_watering_repo() -> ArangoWateringRepository:
    return ArangoWateringRepository(get_db())


def get_watering_service() -> WateringService:
    return WateringService(get_watering_repo(), WateringEngine(), get_site_repo())


def get_ipm_repo() -> ArangoIpmRepository:
    return ArangoIpmRepository(get_db())


def get_ipm_service() -> IpmService:
    return IpmService(
        get_ipm_repo(),
        SafetyIntervalValidator(),
        ResistanceManager(),
        InspectionScheduler(),
    )


def get_harvest_repo() -> ArangoHarvestRepository:
    return ArangoHarvestRepository(get_db())


def get_harvest_service() -> HarvestService:
    return HarvestService(
        get_harvest_repo(),
        get_ipm_service(),
        ReadinessEngine(),
        QualityScoringEngine(),
    )


def get_task_repo() -> ArangoTaskRepository:
    return ArangoTaskRepository(get_db())


def get_task_service() -> TaskService:
    return TaskService(
        get_task_repo(),
        HSTValidator(),
        DependencyResolver(),
    )


# ── REQ-023 Auth dependencies ───────────────────────────────────────


def get_user_repo() -> ArangoUserRepository:
    return ArangoUserRepository(get_db())


def get_auth_provider_repo() -> ArangoAuthProviderRepository:
    return ArangoAuthProviderRepository(get_db())


def get_refresh_token_repo() -> ArangoRefreshTokenRepository:
    return ArangoRefreshTokenRepository(get_db())


def get_oidc_config_repo() -> ArangoOidcConfigRepository:
    return ArangoOidcConfigRepository(get_db())


def get_token_engine() -> TokenEngine:
    return TokenEngine(settings.jwt_secret_key, settings.jwt_algorithm)


def get_password_engine() -> PasswordEngine:
    return PasswordEngine()


def get_email_service() -> IEmailService:
    if settings.email_adapter == "smtp":
        return SmtpEmailAdapter(
            host=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password,
            from_email=settings.smtp_from_email,
            use_tls=settings.smtp_use_tls,
        )
    return ConsoleEmailAdapter()


def get_auth_service() -> AuthService:
    return AuthService(
        user_repo=get_user_repo(),
        auth_provider_repo=get_auth_provider_repo(),
        refresh_token_repo=get_refresh_token_repo(),
        password_engine=get_password_engine(),
        token_engine=get_token_engine(),
        throttle_engine=LoginThrottleEngine(),
        email_service=get_email_service(),
        frontend_url=settings.frontend_url,
        access_token_expire_minutes=settings.access_token_expire_minutes,
        refresh_token_expire_days=settings.refresh_token_expire_days,
        tenant_service=get_tenant_service(),
        require_email_verification=settings.require_email_verification,
    )


def get_user_service() -> UserService:
    return UserService(get_user_repo(), get_refresh_token_repo())


# ── REQ-024 Tenant dependencies ──────────────────────────────────────


def get_tenant_repo() -> ArangoTenantRepository:
    return ArangoTenantRepository(get_db())


def get_membership_repo() -> ArangoMembershipRepository:
    return ArangoMembershipRepository(get_db())


def get_invitation_repo() -> ArangoInvitationRepository:
    return ArangoInvitationRepository(get_db())


def get_assignment_repo() -> ArangoLocationAssignmentRepository:
    return ArangoLocationAssignmentRepository(get_db())


def get_tenant_service() -> TenantService:
    return TenantService(
        tenant_repo=get_tenant_repo(),
        membership_repo=get_membership_repo(),
        invitation_repo=get_invitation_repo(),
        assignment_repo=get_assignment_repo(),
        tenant_engine=TenantEngine(),
        membership_engine=MembershipEngine(),
        invitation_engine=InvitationEngine(),
    )


def close_connection() -> None:
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None
