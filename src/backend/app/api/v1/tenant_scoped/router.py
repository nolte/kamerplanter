"""Tenant-scoped router.

Mounts existing resource routers under /t/{tenant_slug}/ prefix.
All endpoints in this router require authentication and tenant membership.
The TenantContext is available via Depends(get_current_tenant).

Global resources (botanical_families, species, cultivars, IPM reference data)
remain at /api/v1/ without tenant scoping.
"""

from fastapi import APIRouter

from app.api.v1.feeding_events.router import router as feeding_events_router
from app.api.v1.fertilizers.router import router as fertilizers_router
from app.api.v1.harvest.router import router as harvest_router
from app.api.v1.nutrient_calculations.router import router as nutrient_calculations_router
from app.api.v1.nutrient_plans.router import router as nutrient_plans_router
from app.api.v1.plant_instances.router import router as plants_router
from app.api.v1.planting_runs.router import router as planting_runs_router
from app.api.v1.sites.router import router as sites_router
from app.api.v1.tanks.router import router as tanks_router
from app.api.v1.tasks.router import router as tasks_router
from app.api.v1.watering_events.router import router as watering_events_router

tenant_scoped_router = APIRouter(
    prefix="/t/{tenant_slug}",
    tags=["tenant-scoped"],
)

# Mount tenant-scoped resource routers
# These are the same routers as the global ones, but nested under /t/{tenant_slug}/
# During migration, both paths work. The tenant_slug path parameter is available
# for future use when services are updated to filter by tenant.
tenant_scoped_router.include_router(sites_router)
tenant_scoped_router.include_router(plants_router)
tenant_scoped_router.include_router(planting_runs_router)
tenant_scoped_router.include_router(tanks_router)
tenant_scoped_router.include_router(fertilizers_router)
tenant_scoped_router.include_router(nutrient_plans_router)
tenant_scoped_router.include_router(feeding_events_router)
tenant_scoped_router.include_router(nutrient_calculations_router)
tenant_scoped_router.include_router(watering_events_router)
tenant_scoped_router.include_router(harvest_router)
tenant_scoped_router.include_router(tasks_router)
