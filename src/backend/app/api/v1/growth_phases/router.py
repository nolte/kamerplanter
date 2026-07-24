from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.mapping import to_response
from app.api.v1.growth_phases.schemas import PhaseCreate, PhaseResponse
from app.common.auth import get_current_user
from app.common.dependencies import get_phase_service
from app.common.openapi_responses import NOT_FOUND_RESPONSE, UNAUTHORIZED_RESPONSE
from app.domain.models.lifecycle import GrowthPhase
from app.domain.services.phase_service import PhaseService

router = APIRouter(
    prefix="/growth-phases",
    tags=["growth-phases"],
    dependencies=[Depends(get_current_user)],
    responses={**UNAUTHORIZED_RESPONSE, **NOT_FOUND_RESPONSE},
)


@router.get("", response_model=list[PhaseResponse])
def list_phases(
    lifecycle_key: str = Query(..., description="Document key of the lifecycle whose phases to list."),
    service: PhaseService = Depends(get_phase_service),
):
    """List the growth phases of a lifecycle."""
    phases = service.get_phases(lifecycle_key)
    return [to_response(p, PhaseResponse) for p in phases]


@router.get("/{key}", response_model=PhaseResponse)
def get_phase(
    key: Annotated[str, Path(description="Document key of the growth phase.")],
    service: PhaseService = Depends(get_phase_service),
):
    """Return a single growth phase by key."""
    p = service.get_phase(key)
    return to_response(p, PhaseResponse)


@router.post("", response_model=PhaseResponse, status_code=201)
def create_phase(body: PhaseCreate, service: PhaseService = Depends(get_phase_service)):
    """Create a new growth phase."""
    phase = GrowthPhase(**body.model_dump())
    created = service.create_phase(phase)
    return to_response(created, PhaseResponse)


@router.put("/{key}", response_model=PhaseResponse)
def update_phase(
    key: Annotated[str, Path(description="Document key of the growth phase.")],
    body: PhaseCreate,
    service: PhaseService = Depends(get_phase_service),
):
    """Update an existing growth phase."""
    phase = GrowthPhase(**body.model_dump())
    updated = service.update_phase(key, phase)
    return to_response(updated, PhaseResponse)


@router.delete("/{key}", status_code=204)
def delete_phase(
    key: Annotated[str, Path(description="Document key of the growth phase.")],
    service: PhaseService = Depends(get_phase_service),
):
    """Delete a growth phase."""
    service.delete_phase(key)
