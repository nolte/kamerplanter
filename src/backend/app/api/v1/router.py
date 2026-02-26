from fastapi import APIRouter

from app.api.v1.botanical_families.router import router as families_router
from app.api.v1.calculations.router import router as calculations_router
from app.api.v1.companion_planting.router import router as companion_router
from app.api.v1.crop_rotation.router import router as rotation_router
from app.api.v1.cultivars.router import router as cultivars_router
from app.api.v1.enrichment.router import router as enrichment_router
from app.api.v1.growth_phases.router import router as phases_router
from app.api.v1.health.router import router as health_router
from app.api.v1.lifecycle_configs.router import router as lifecycle_router
from app.api.v1.locations.router import router as locations_router
from app.api.v1.phases.router import router as phase_control_router
from app.api.v1.plant_instances.router import router as plants_router
from app.api.v1.planting_runs.router import router as planting_runs_router
from app.api.v1.profiles.router import router as profiles_router
from app.api.v1.sites.router import router as sites_router
from app.api.v1.slots.router import router as slots_router
from app.api.v1.species.router import router as species_router
from app.api.v1.substrates.router import router as substrates_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router)
api_router.include_router(families_router)
api_router.include_router(calculations_router)
api_router.include_router(companion_router)
api_router.include_router(rotation_router)
api_router.include_router(cultivars_router)
api_router.include_router(phases_router)
api_router.include_router(lifecycle_router)
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
