from fastapi import APIRouter

from app.api.v1.activities.router import router as activities_router
from app.api.v1.activity_plans.router import router as activity_plans_router
from app.api.v1.admin.settings.router import router as admin_settings_router
from app.api.v1.botanical_families.router import router as families_router
from app.api.v1.calculations.router import router as calculations_router
from app.api.v1.calendar.router import router as calendar_router
from app.api.v1.care_reminders.router import router as care_reminders_router
from app.api.v1.companion_planting.router import router as companion_router
from app.api.v1.crop_rotation.router import router as rotation_router
from app.api.v1.cultivars.router import router as cultivars_router
from app.api.v1.enrichment.router import router as enrichment_router
from app.api.v1.family_relationships.router import router as family_relationships_router
from app.api.v1.favorites.router import router as favorites_router
from app.api.v1.feeding_events.router import router as feeding_events_router
from app.api.v1.fertilizers.router import router as fertilizers_router
from app.api.v1.growth_phases.router import router as phases_router
from app.api.v1.harvest.router import router as harvest_router
from app.api.v1.health.router import router as health_router
from app.api.v1.imports.router import router as imports_router
from app.api.v1.ipm.router import router as ipm_router
from app.api.v1.lifecycle_configs.router import router as lifecycle_router
from app.api.v1.location_types.router import router as location_types_router
from app.api.v1.locations.router import router as locations_router
from app.api.v1.nutrient_calculations.router import router as nutrient_calculations_router
from app.api.v1.nutrient_plans.router import router as nutrient_plans_router
from app.api.v1.onboarding.router import router as onboarding_router
from app.api.v1.phases.router import router as phase_control_router
from app.api.v1.plant_instances.router import router as plants_router
from app.api.v1.planting_runs.router import router as planting_runs_router
from app.api.v1.profiles.router import router as profiles_router
from app.api.v1.sites.router import router as sites_router
from app.api.v1.slots.router import router as slots_router
from app.api.v1.species.router import router as species_router
from app.api.v1.starter_kits.router import router as starter_kits_router
from app.api.v1.substrates.router import router as substrates_router
from app.api.v1.tanks.router import router as tanks_router
from app.api.v1.tasks.router import router as tasks_router
from app.api.v1.tenant_scoped.router import tenant_scoped_router
from app.api.v1.tenants.router import router as tenants_router
from app.api.v1.user_preferences.router import router as user_preferences_router
from app.api.v1.users.router import router as users_router
from app.api.v1.watering_events.router import router as watering_events_router
from app.api.v1.watering_logs.router import router as watering_logs_router
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
api_router.include_router(locations_router)
api_router.include_router(phase_control_router)
api_router.include_router(plants_router)
api_router.include_router(planting_runs_router)
api_router.include_router(profiles_router)
api_router.include_router(sites_router)
api_router.include_router(slots_router)
api_router.include_router(species_router)
api_router.include_router(substrates_router)
api_router.include_router(enrichment_router)
api_router.include_router(family_relationships_router)
api_router.include_router(tanks_router)
api_router.include_router(fertilizers_router)
api_router.include_router(nutrient_plans_router)
api_router.include_router(feeding_events_router)
api_router.include_router(nutrient_calculations_router)
api_router.include_router(watering_events_router)
api_router.include_router(watering_logs_router)
api_router.include_router(ipm_router)
api_router.include_router(harvest_router)
api_router.include_router(tasks_router)
api_router.include_router(tenants_router)
api_router.include_router(tenant_scoped_router)
api_router.include_router(care_reminders_router)
api_router.include_router(onboarding_router)
api_router.include_router(starter_kits_router)
api_router.include_router(user_preferences_router)
api_router.include_router(imports_router)
api_router.include_router(calendar_router)
api_router.include_router(activities_router)
api_router.include_router(activity_plans_router)
api_router.include_router(favorites_router)
