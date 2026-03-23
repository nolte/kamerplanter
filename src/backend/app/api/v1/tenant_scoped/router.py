"""Tenant-scoped router.

Mounts tenant-aware resource routers under /t/{tenant_slug}/ prefix.
All endpoints in this router require authentication and tenant membership.
The TenantContext is available via Depends(get_current_tenant).

Global resources (botanical_families, species, cultivars, IPM reference data)
remain at /api/v1/ without tenant scoping.
"""

from fastapi import APIRouter

from app.api.v1.calendar.tenant_router import router as tenant_calendar_router
from app.api.v1.favorites.tenant_router import router as tenant_favorites_router
from app.api.v1.feeding_events.tenant_router import router as tenant_feeding_events_router
from app.api.v1.fertilizers.tenant_router import router as tenant_fertilizers_router
from app.api.v1.harvest.tenant_router import router as tenant_harvest_router
from app.api.v1.ipm.tenant_router import router as tenant_ipm_router
from app.api.v1.locations.tenant_router import router as tenant_locations_router
from app.api.v1.notifications.tenant_router import router as tenant_notifications_router
from app.api.v1.nutrient_calculations.router import router as nutrient_calculations_router
from app.api.v1.nutrient_plans.tenant_router import router as tenant_nutrient_plans_router
from app.api.v1.onboarding.tenant_router import router as tenant_onboarding_router
from app.api.v1.plant_instances.tenant_router import router as tenant_plants_router
from app.api.v1.planting_runs.tenant_router import router as tenant_planting_runs_router
from app.api.v1.sites.tenant_router import router as tenant_sites_router
from app.api.v1.slots.tenant_router import router as tenant_slots_router
from app.api.v1.starter_kits.tenant_router import router as tenant_starter_kits_router
from app.api.v1.tanks.tenant_router import router as tenant_tanks_router
from app.api.v1.tasks.tenant_router import router as tenant_tasks_router
from app.api.v1.user_preferences.tenant_router import router as tenant_user_preferences_router
from app.api.v1.watering_events.tenant_router import router as tenant_watering_events_router
from app.api.v1.watering_logs.tenant_router import router as tenant_watering_logs_router

tenant_scoped_router = APIRouter(
    prefix="/t/{tenant_slug}",
    tags=["tenant-scoped"],
)

# Mount tenant-scoped resource routers
# These routers enforce tenant isolation via get_current_tenant() dependency.
tenant_scoped_router.include_router(tenant_sites_router)
tenant_scoped_router.include_router(tenant_locations_router)
tenant_scoped_router.include_router(tenant_slots_router)
tenant_scoped_router.include_router(tenant_plants_router)
tenant_scoped_router.include_router(tenant_planting_runs_router)
tenant_scoped_router.include_router(tenant_tanks_router)
tenant_scoped_router.include_router(tenant_fertilizers_router)
tenant_scoped_router.include_router(tenant_nutrient_plans_router)
tenant_scoped_router.include_router(tenant_feeding_events_router)
tenant_scoped_router.include_router(nutrient_calculations_router)
tenant_scoped_router.include_router(tenant_watering_events_router)
tenant_scoped_router.include_router(tenant_watering_logs_router)
tenant_scoped_router.include_router(tenant_harvest_router)
tenant_scoped_router.include_router(tenant_tasks_router)
tenant_scoped_router.include_router(tenant_ipm_router)
tenant_scoped_router.include_router(tenant_calendar_router)
tenant_scoped_router.include_router(tenant_starter_kits_router)
tenant_scoped_router.include_router(tenant_onboarding_router)
tenant_scoped_router.include_router(tenant_favorites_router)
tenant_scoped_router.include_router(tenant_notifications_router)
tenant_scoped_router.include_router(tenant_user_preferences_router)
