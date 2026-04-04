from arango.database import StandardDatabase

from app.config.settings import settings
from app.data_access.arango.auth_provider_repository import ArangoAuthProviderRepository
from app.data_access.arango.botanical_family_repository import ArangoBotanicalFamilyRepository
from app.data_access.arango.care_reminder_repository import ArangoCareReminderRepository
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
from app.data_access.arango.watering_log_repository import ArangoWateringLogRepository
from app.data_access.arango.watering_repository import ArangoWateringRepository
from app.data_access.external.console_email_adapter import ConsoleEmailAdapter
from app.data_access.external.smtp_email_adapter import SmtpEmailAdapter
from app.domain.engines.care_reminder_engine import CareReminderEngine
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
from app.domain.services.care_reminder_service import CareReminderService
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
from app.domain.services.watering_log_service import WateringLogService
from app.domain.services.watering_service import WateringService

_connection: ArangoConnection | None = None
_timescale_connection = None


def get_connection() -> ArangoConnection:
    global _connection
    if _connection is None:
        _connection = ArangoConnection(settings)
    return _connection


def get_timescale_connection():
    from app.data_access.timescale.connection import TimescaleConnection

    global _timescale_connection
    if not settings.timescaledb_enabled:
        return None
    if _timescale_connection is None:
        _timescale_connection = TimescaleConnection(settings)
    return _timescale_connection


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
    return PlantInstanceService(
        get_plant_repo(),
        get_site_repo(),
        rotation_validator,
        companion_engine,
        phase_repo=get_lifecycle_repo(),
    )


def get_phase_service() -> PhaseService:
    service = PhaseService(get_lifecycle_repo(), get_plant_repo())
    # REQ-006: Activate dormant tasks when a plant transitions to a new phase
    task_service = get_task_service()
    service.register_on_transition(task_service.activate_dormant_tasks_for_phase)
    return service


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


def get_plant_diary_repo():
    from app.data_access.arango.plant_diary_repository import ArangoPlantDiaryRepository

    return ArangoPlantDiaryRepository(get_db())


def get_plant_diary_service():
    from app.domain.services.plant_diary_service import PlantDiaryService

    return PlantDiaryService(
        diary_repo=get_plant_diary_repo(),
        run_repo=get_planting_run_repo(),
        plant_repo=get_plant_repo(),
    )


def get_planting_run_service() -> PlantingRunService:
    from app.domain.engines.watering_schedule_engine import WateringScheduleEngine

    return PlantingRunService(
        get_planting_run_repo(),
        get_plant_repo(),
        PlantingRunEngine(),
        watering_schedule_engine=WateringScheduleEngine(),
        nutrient_plan_repo=get_nutrient_plan_repo(),
        watering_repo=get_watering_repo(),
        phase_repo=get_lifecycle_repo(),
        site_repo=get_site_repo(),
    )


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
        site_repo=get_site_repo(),
    )


def get_feeding_service() -> FeedingService:
    return FeedingService(get_feeding_repo())


def get_watering_repo() -> ArangoWateringRepository:
    return ArangoWateringRepository(get_db())


def get_watering_service() -> WateringService:
    return WateringService(
        get_watering_repo(),
        WateringEngine(),
        get_site_repo(),
        run_repo=get_planting_run_repo(),
        task_repo=get_task_repo(),
        feeding_repo=get_feeding_repo(),
        nutrient_plan_repo=get_nutrient_plan_repo(),
        care_repo=get_care_reminder_repo(),
        plant_repo=get_plant_repo(),
        species_repo=get_species_repo(),
        substrate_repo=get_substrate_repo(),
        lifecycle_repo=get_lifecycle_repo(),
    )


def get_watering_log_repo() -> ArangoWateringLogRepository:
    return ArangoWateringLogRepository(get_db())


def get_watering_log_service() -> WateringLogService:
    return WateringLogService(
        get_watering_log_repo(),
        WateringEngine(),
        get_site_repo(),
        run_repo=get_planting_run_repo(),
        task_repo=get_task_repo(),
        nutrient_plan_repo=get_nutrient_plan_repo(),
        care_repo=get_care_reminder_repo(),
    )


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


def get_oauth_engine():
    from app.domain.engines.oauth_engine import OAuthEngine

    return OAuthEngine()


def get_encryption_engine():
    from app.domain.engines.encryption_engine import EncryptionEngine

    return EncryptionEngine(settings.fernet_key)


def get_oauth_state_store():
    from app.data_access.external.redis_oauth_state import RedisOAuthStateStore

    return RedisOAuthStateStore(settings.redis_url)


def get_api_key_repo():
    from app.data_access.arango.api_key_repository import ArangoApiKeyRepository

    return ArangoApiKeyRepository(get_db())


def get_auth_provider():
    if settings.kamerplanter_mode == "light":
        from app.domain.engines.light_auth_provider import LightAuthProvider

        return LightAuthProvider(get_user_repo())
    from app.domain.engines.full_auth_provider import FullAuthProvider

    return FullAuthProvider(get_token_engine(), get_user_repo(), get_auth_service())


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
        session_token_expire_hours=settings.session_token_expire_hours,
        tenant_service=get_tenant_service(),
        require_email_verification=settings.require_email_verification,
        oauth_engine=get_oauth_engine(),
        oauth_state_store=get_oauth_state_store(),
        api_key_repo=get_api_key_repo(),
        oidc_config_repo=get_oidc_config_repo(),
        encryption_engine=get_encryption_engine(),
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


# ── REQ-022 Care Reminder dependencies ─────────────────────────────


# ── REQ-020 Onboarding dependencies ────────────────────────────────


def get_favorites_service():
    from app.domain.services.favorites_service import FavoritesService

    return FavoritesService(get_db())


def get_starter_kit_service():
    from app.domain.services.starter_kit_service import StarterKitService

    return StarterKitService(get_db())


def get_onboarding_service():
    from app.domain.services.onboarding_service import OnboardingService

    return OnboardingService(get_db(), get_starter_kit_service())


def get_user_preference_service():
    from app.domain.services.user_preference_service import UserPreferenceService

    return UserPreferenceService(get_db())


def get_care_reminder_repo() -> ArangoCareReminderRepository:
    return ArangoCareReminderRepository(get_db())


def get_care_reminder_service() -> CareReminderService:
    return CareReminderService(
        get_care_reminder_repo(),
        CareReminderEngine(),
        get_task_repo(),
        watering_log_repo=get_watering_log_repo(),
        plant_repo=get_plant_repo(),
        lifecycle_repo=get_lifecycle_repo(),
    )


# ── REQ-032 Print dependencies ──────────────────────────────────────


def get_print_service():
    from app.domain.services.print_service import PrintService

    return PrintService(
        nutrient_plan_service=get_nutrient_plan_service(),
        care_reminder_service=get_care_reminder_service(),
        fertilizer_repo=get_fertilizer_repo(),
        plant_repo=get_plant_repo(),
        species_repo=get_species_repo(),
        site_repo=get_site_repo(),
        app_base_url=settings.app_base_url,
    )


# ── REQ-012 Import dependencies ──────────────────────────────────────


def get_import_job_repo():
    from app.data_access.arango.import_job_repository import ArangoImportJobRepository

    return ArangoImportJobRepository(get_db())


def get_import_service():
    from app.domain.services.import_service import ImportService

    return ImportService(get_import_job_repo(), get_species_repo(), get_family_repo())


# ── REQ-015 Calendar dependencies ───────────────────────────────────


def get_calendar_feed_repo():
    from app.data_access.arango.calendar_feed_repository import ArangoCalendarFeedRepository

    return ArangoCalendarFeedRepository(get_db())


def get_calendar_aggregation_engine():
    from app.domain.engines.calendar_aggregation_engine import CalendarAggregationEngine

    return CalendarAggregationEngine(get_db())


def get_calendar_service():
    from app.domain.services.calendar_service import CalendarService

    return CalendarService(
        get_calendar_feed_repo(),
        get_calendar_aggregation_engine(),
        species_repo=get_species_repo(),
        site_repo=get_site_repo(),
        planting_run_service=get_planting_run_service(),
    )


# ── REQ-005 Sensor dependencies ───────────────────────────────────


def get_sensor_repo():
    from app.data_access.arango.sensor_repository import ArangoSensorRepository

    return ArangoSensorRepository(get_db())


def get_system_settings_repo():
    from app.data_access.arango.system_settings_repository import ArangoSystemSettingsRepository

    return ArangoSystemSettingsRepository(get_db())


def get_system_settings_service():
    from app.domain.services.system_settings_service import SystemSettingsService

    return SystemSettingsService(get_system_settings_repo())


def get_ha_client():
    from app.data_access.external.ha_client import HomeAssistantClient

    try:
        svc = get_system_settings_service()
        effective = svc.get_effective_ha_settings()
    except Exception:
        # Collection may not exist yet — fall back to env
        effective = {
            "ha_url": settings.ha_url,
            "ha_access_token": settings.ha_access_token,
            "ha_timeout": settings.ha_timeout,
        }
    url = effective["ha_url"]
    if not url:
        return None
    return HomeAssistantClient(str(url), str(effective["ha_access_token"]), int(effective["ha_timeout"]))


def get_observation_repo():
    conn = get_timescale_connection()
    if conn is None:
        from app.data_access.timescale.null_observation_repository import NullObservationRepository

        return NullObservationRepository()
    from app.data_access.timescale.observation_repository import TimescaleObservationRepository

    return TimescaleObservationRepository(conn.pool)


def get_observation_service():
    from app.domain.services.observation_service import ObservationService

    return ObservationService(get_observation_repo(), get_sensor_repo())


def get_sensor_service():
    from app.domain.services.sensor_service import SensorService

    return SensorService(get_sensor_repo(), get_ha_client())


# ── REQ-002 LocationType dependencies ───────────────────────────────


def get_location_type_repo():
    from app.data_access.arango.location_type_repository import ArangoLocationTypeRepository

    return ArangoLocationTypeRepository(get_db())


def get_location_type_service():
    from app.domain.services.location_type_service import LocationTypeService

    return LocationTypeService(get_location_type_repo())


# ── Activity dependencies ──────────────────────────────────────────


def get_activity_repo():
    from app.data_access.arango.activity_repository import ArangoActivityRepository

    return ArangoActivityRepository(get_db())


def get_activity_service():
    from app.domain.services.activity_service import ActivityService

    return ActivityService(get_activity_repo())


def get_activity_plan_service():
    from app.domain.engines.activity_plan_engine import ActivityPlanEngine
    from app.domain.services.activity_plan_service import ActivityPlanService

    return ActivityPlanService(
        engine=ActivityPlanEngine(),
        activity_repo=get_activity_repo(),
        phase_repo=get_lifecycle_repo(),
        task_repo=get_task_repo(),
        planting_run_repo=get_planting_run_repo(),
        species_repo=get_species_repo(),
        family_repo=get_family_repo(),
    )


# ── REQ-030 Notification dependencies ────────────────────────────────


def get_notification_repo():
    from app.data_access.arango.notification_repository import ArangoNotificationRepository

    return ArangoNotificationRepository(get_db())


def get_notification_preference_repo():
    from app.data_access.arango.notification_preference_repository import (
        ArangoNotificationPreferenceRepository,
    )

    return ArangoNotificationPreferenceRepository(get_db())


def _get_redis_client():
    """Get a Redis client for notification dedup and caching."""
    import redis

    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


def get_notification_service():
    from app.domain.engines.notification_channel_registry import NotificationChannelRegistry
    from app.domain.engines.notification_engine import NotificationEngine
    from app.domain.services.notification_service import NotificationService

    engine = NotificationEngine(
        notification_repo=get_notification_repo(),
        preference_repo=get_notification_preference_repo(),
        channel_registry=NotificationChannelRegistry,
        redis_client=_get_redis_client(),
    )
    return NotificationService(
        engine=engine,
        notification_repo=get_notification_repo(),
        preference_repo=get_notification_preference_repo(),
    )


# ── Knowledge Service client ─────────────────────────────────────


def get_knowledge_client():
    """Return a KnowledgeServiceClient or None if disabled."""
    if not settings.knowledge_service_enabled:
        return None

    from app.data_access.external.knowledge_service_client import KnowledgeServiceClient

    return KnowledgeServiceClient(base_url=settings.knowledge_service_url)


def close_timescale_connection() -> None:
    global _timescale_connection
    if _timescale_connection is not None:
        _timescale_connection.close()
        _timescale_connection = None


def close_connection() -> None:
    global _connection
    close_timescale_connection()
    if _connection is not None:
        _connection.close()
        _connection = None
