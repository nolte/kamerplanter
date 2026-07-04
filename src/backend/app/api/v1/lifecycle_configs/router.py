from fastapi import APIRouter, Depends

from app.api.mapping import to_response
from app.api.v1.lifecycle_configs.schemas import LifecycleCreate, LifecycleResponse
from app.common.auth import get_current_user
from app.common.dependencies import get_phase_service
from app.domain.models.lifecycle import LifecycleConfig
from app.domain.services.phase_service import PhaseService

router = APIRouter(
    prefix="/species/{species_key}/lifecycle",
    tags=["lifecycle"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=LifecycleResponse)
def get_lifecycle(species_key: str, service: PhaseService = Depends(get_phase_service)):
    lc = service.get_lifecycle_by_species(species_key)
    return to_response(lc, LifecycleResponse)


@router.post("", response_model=LifecycleResponse, status_code=201)
def create_lifecycle(species_key: str, body: LifecycleCreate, service: PhaseService = Depends(get_phase_service)):
    config = LifecycleConfig(species_key=species_key, **body.model_dump(exclude={"species_key"}))
    created = service.create_lifecycle(config)
    return to_response(created, LifecycleResponse)


@router.put("/{key}", response_model=LifecycleResponse)
def update_lifecycle(
    species_key: str,
    key: str,
    body: LifecycleCreate,
    service: PhaseService = Depends(get_phase_service),
):
    config = LifecycleConfig(species_key=species_key, **body.model_dump(exclude={"species_key"}))
    updated = service.update_lifecycle(key, config)
    return to_response(updated, LifecycleResponse)
