from fastapi import APIRouter, Depends

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
    return LifecycleResponse(key=lc.key or "", **lc.model_dump(exclude={"key"}))


@router.post("", response_model=LifecycleResponse, status_code=201)
def create_lifecycle(species_key: str, body: LifecycleCreate, service: PhaseService = Depends(get_phase_service)):
    config = LifecycleConfig(species_key=species_key, **body.model_dump(exclude={"species_key"}))
    created = service.create_lifecycle(config)
    return LifecycleResponse(key=created.key or "", **created.model_dump(exclude={"key"}))


@router.put("/{key}", response_model=LifecycleResponse)
def update_lifecycle(
    species_key: str,
    key: str,
    body: LifecycleCreate,
    service: PhaseService = Depends(get_phase_service),
):
    config = LifecycleConfig(species_key=species_key, **body.model_dump(exclude={"species_key"}))
    updated = service.update_lifecycle(key, config)
    return LifecycleResponse(key=updated.key or "", **updated.model_dump(exclude={"key"}))
