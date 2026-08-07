from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.api.mapping import to_response
from app.api.v1.lifecycle_configs.schemas import LifecycleCreate, LifecycleResponse
from app.common.auth import get_current_user
from app.common.dependencies import get_phase_service
from app.common.openapi_responses import AUTH_CRUD_RESPONSES
from app.domain.models.lifecycle import LifecycleConfig
from app.domain.services.phase_service import PhaseService

router = APIRouter(
    prefix="/species/{species_key}/lifecycle",
    tags=["lifecycle"],
    dependencies=[Depends(get_current_user)],
    responses=AUTH_CRUD_RESPONSES,
)


@router.get("", response_model=LifecycleResponse)
def get_lifecycle(
    species_key: Annotated[str, Path(description="Document key of the species.")],
    service: PhaseService = Depends(get_phase_service),
):
    """Return the lifecycle configuration of a species."""
    lc = service.get_lifecycle_by_species(species_key)
    return to_response(lc, LifecycleResponse)


@router.post("", response_model=LifecycleResponse, status_code=201)
def create_lifecycle(
    species_key: Annotated[str, Path(description="Document key of the species.")],
    body: LifecycleCreate,
    service: PhaseService = Depends(get_phase_service),
):
    """Create the lifecycle configuration for a species."""
    config = LifecycleConfig(species_key=species_key, **body.model_dump(exclude={"species_key"}))
    created = service.create_lifecycle(config)
    if body.phase_sequence_key:
        service.assign_phase_sequence(species_key, body.phase_sequence_key)
        created = service.get_lifecycle(created.key or "")
    return to_response(created, LifecycleResponse)


@router.put("/{key}", response_model=LifecycleResponse)
def update_lifecycle(
    species_key: Annotated[str, Path(description="Document key of the species.")],
    key: Annotated[str, Path(description="Document key of the lifecycle configuration.")],
    body: LifecycleCreate,
    service: PhaseService = Depends(get_phase_service),
):
    """Update a species' lifecycle configuration, optionally rebinding its phase sequence.

    ``phase_sequence_key`` is the documented, writable assignment point (issue #949).
    Supplying it re-points the species' ``HAS_PHASE_SEQUENCE`` edge — the binding the
    lifecycle engine actually resolves against — and syncs the stored field. Omitting
    it leaves the current binding untouched; it is never cleared by omission.
    """
    config = LifecycleConfig(species_key=species_key, **body.model_dump(exclude={"species_key"}))
    # Bind first: a non-existent sequence raises 404 here, before the lifecycle is
    # written, so a typo cannot leave a half-applied update behind.
    if body.phase_sequence_key:
        service.assign_phase_sequence(species_key, body.phase_sequence_key)
    updated = service.update_lifecycle(key, config)
    return to_response(updated, LifecycleResponse)
