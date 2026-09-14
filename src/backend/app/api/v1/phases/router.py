from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path

from app.api.mapping import to_response
from app.api.v1.phases.schemas import (
    CurrentPhaseResponse,
    PhaseHistoryDateUpdate,
    PhaseHistoryResponse,
    TransitionRequest,
)
from app.api.v1.plant_instances.schemas import PlantResponse
from app.common.auth import get_current_user, require_active_tenant_role
from app.common.dependencies import get_phase_service, get_plant_instance_service
from app.common.enums import TenantRole
from app.common.openapi_responses import NOT_FOUND_RESPONSE, UNAUTHORIZED_RESPONSE
from app.common.plant_ownership import require_owned_plant
from app.domain.services.phase_service import PhaseService
from app.domain.services.plant_instance_service import PlantInstanceService

# GATED ON PLANT OWNERSHIP, AT THE ROUTER (#1402 group C).
#
# Every operation here takes a plant key from the path and, until this, handed it
# to a by-key lookup with no tenant anywhere: `PhaseService.transition_phase` takes
# no `tenant_key`, and resolution ends in `BaseArangoRepository.get_or_raise`. Any
# authenticated caller could transition another tenant's plant — `force: true`
# included, firing the post-transition callbacks — read its phase history, edit a
# history entry's dates, or delete one.
#
# All FIVE operations, not the two #1402 names: the reads leak another tenant's
# phase history just as the writes change it.
#
# On the router rather than per handler, because eleven signatures across two
# routers is the opt-in drift this repository keeps paying for. See
# `app/common/plant_ownership.py`.
router = APIRouter(
    prefix="/plant-instances/{plant_key}/phases",
    tags=["phases"],
    dependencies=[Depends(get_current_user), Depends(require_owned_plant)],
    responses={**UNAUTHORIZED_RESPONSE, **NOT_FOUND_RESPONSE},
)


@router.get("/current", response_model=CurrentPhaseResponse)
def get_current_phase(
    plant_key: Annotated[str, Path(description="Document key of the plant instance.")],
    service: PhaseService = Depends(get_phase_service),
):
    """Return the plant instance's current phase snapshot."""
    result = service.get_current_phase(plant_key)
    return CurrentPhaseResponse(**result)


@router.post(
    "/transition", response_model=PlantResponse, dependencies=[Depends(require_active_tenant_role(TenantRole.GROWER))]
)
def transition_phase(
    plant_key: Annotated[str, Path(description="Document key of the plant instance.")],
    body: TransitionRequest,
    service: PhaseService = Depends(get_phase_service),
    plant_service: PlantInstanceService = Depends(get_plant_instance_service),
):
    """Transition a plant instance to a target phase."""
    plant = service.transition_phase(plant_key, body.target_phase_key, body.reason, force=body.force)
    phase_name = plant_service.resolve_phase_name(plant.current_phase_key or "")
    return to_response(plant, PlantResponse, current_phase=phase_name)


@router.get("/history", response_model=list[PhaseHistoryResponse])
def get_phase_history(
    plant_key: Annotated[str, Path(description="Document key of the plant instance.")],
    service: PhaseService = Depends(get_phase_service),
):
    """List the plant instance's phase-transition history."""
    history = service.get_phase_history(plant_key)
    return [to_response(h, PhaseHistoryResponse) for h in history]


@router.patch(
    "/history/{history_key}",
    response_model=PhaseHistoryResponse,
    dependencies=[Depends(require_active_tenant_role(TenantRole.GROWER))],
)
def update_phase_history_dates(
    plant_key: Annotated[str, Path(description="Document key of the plant instance.")],
    history_key: Annotated[str, Path(description="Document key of the phase-history entry.")],
    body: PhaseHistoryDateUpdate,
    service: PhaseService = Depends(get_phase_service),
):
    """Adjust the entered/exited dates of a phase-history entry."""
    if body.entered_at is None and body.exited_at is None:
        raise HTTPException(status_code=422, detail="At least one of entered_at or exited_at must be provided")
    try:
        h = service.update_phase_history_dates(plant_key, history_key, body.entered_at, body.exited_at)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return to_response(h, PhaseHistoryResponse)


@router.delete(
    "/history/{history_key}", status_code=204, dependencies=[Depends(require_active_tenant_role(TenantRole.LEAD))]
)
def delete_phase_history(
    plant_key: Annotated[str, Path(description="Document key of the plant instance.")],
    history_key: Annotated[str, Path(description="Document key of the phase-history entry.")],
    service: PhaseService = Depends(get_phase_service),
):
    """Delete a phase-history entry of a plant instance."""
    try:
        service.delete_phase_history(plant_key, history_key)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
