from fastapi import APIRouter

from app.api.v1.activities.router import router as activities_router
from app.api.v1.activity_plans.router import router as activity_plans_router
from app.api.v1.admin.settings.router import router as admin_settings_router
from app.api.v1.botanical_families.router import router as families_router
from app.api.v1.calculations.router import router as calculations_router
from app.api.v1.care_reminders.router import router as care_reminders_router
from app.api.v1.companion_planting.router import router as companion_router
from app.api.v1.crop_rotation.router import router as rotation_router
from app.api.v1.cultivars.router import router as cultivars_router
from app.api.v1.enrichment.router import router as enrichment_router
from app.api.v1.family_relationships.router import router as family_relationships_router
from app.api.v1.growth_phases.router import router as phases_router
from app.api.v1.health.router import router as health_router
from app.api.v1.imports.router import router as imports_router
from app.api.v1.ipm.router import router as ipm_router
from app.api.v1.lifecycle_configs.router import router as lifecycle_router
from app.api.v1.location_types.router import router as location_types_router
from app.api.v1.observations.router import router as observations_router
from app.api.v1.phases.router import router as phase_control_router
from app.api.v1.profiles.router import router as profiles_router
from app.api.v1.species.router import router as species_router
from app.api.v1.starter_kits.router import router as starter_kits_router
from app.api.v1.substrates.router import router as substrates_router
from app.api.v1.tenant_scoped.router import tenant_scoped_router
from app.api.v1.tenants.router import router as tenants_router
from app.api.v1.users.router import router as users_router
from app.config.settings import settings

api_router = APIRouter(prefix="/api/v1")


# ── REQ-027 Mode endpoint ───────────────────────────────────────────
mode_router = APIRouter(tags=["mode"])


@mode_router.get("/mode")
def get_mode():
    """Return current deployment mode and feature flags."""
    is_full = settings.kamerplanter_mode == "full"
    return {
        "mode": settings.kamerplanter_mode,
        "features": {
            "auth": is_full,
            "multi_tenant": is_full,
            "privacy_consent": is_full,
        },
    }


api_router.include_router(mode_router)

# Admin settings — available in both modes
api_router.include_router(admin_settings_router)

# Auth-related routers: only in full mode
if settings.kamerplanter_mode == "full":
    from app.api.v1.admin.oidc_providers.router import router as oidc_providers_router
    from app.api.v1.admin.platform.router import router as platform_admin_router
    from app.api.v1.auth.router import router as auth_router

    api_router.include_router(auth_router)
    api_router.include_router(oidc_providers_router)
    api_router.include_router(platform_admin_router)

api_router.include_router(users_router)
api_router.include_router(health_router)
api_router.include_router(families_router)
api_router.include_router(calculations_router)
api_router.include_router(companion_router)
api_router.include_router(rotation_router)
api_router.include_router(cultivars_router)
api_router.include_router(phases_router)
api_router.include_router(lifecycle_router)
api_router.include_router(location_types_router)
api_router.include_router(phase_control_router)
api_router.include_router(profiles_router)
api_router.include_router(species_router)
api_router.include_router(substrates_router)
api_router.include_router(enrichment_router)
api_router.include_router(family_relationships_router)
api_router.include_router(ipm_router)
api_router.include_router(tenants_router)
api_router.include_router(tenant_scoped_router)
api_router.include_router(care_reminders_router)
api_router.include_router(starter_kits_router)
api_router.include_router(imports_router)
api_router.include_router(activities_router)
api_router.include_router(activity_plans_router)
api_router.include_router(observations_router)

# ── Knowledge / RAG (conditional on vectordb) ──────────────────────
if settings.vectordb_enabled:
    from app.api.v1.knowledge.router import router as knowledge_router

    api_router.include_router(knowledge_router)
