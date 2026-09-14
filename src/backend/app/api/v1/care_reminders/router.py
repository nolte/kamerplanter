from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.mapping import to_response
from app.api.v1.care_reminders.schemas import (
    CareConfirmationResponse,
    CareProfileResponse,
    CareProfileUpdate,
    ConfirmRequest,
    SnoozeRequest,
)
from app.common.auth import get_current_user, require_active_tenant_role
from app.common.dependencies import get_care_reminder_service
from app.common.enums import ReminderType, TenantRole
from app.common.openapi_responses import NOT_FOUND_RESPONSE, UNAUTHORIZED_RESPONSE
from app.common.plant_ownership import require_owned_plant
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.user import User
from app.domain.services.care_reminder_service import CareReminderService

router = APIRouter(
    prefix="/care-reminders",
    tags=["care-reminders"],
    # GATED ON PLANT OWNERSHIP, AT THE ROUTER (#1402 group C).
    #
    # Every one of the six operations here keys on a plant from the path, and none
    # resolved a tenant. `CareReminderService.confirm_reminder` *has* an ownership
    # check — `if tenant_key and self._plant_repo is not None:` — and the REST
    # router called it without a `tenant_key`, so the check never ran. An opt-in
    # guard that the one production caller does not opt into is the #1042 shape:
    # documented as enforced, wired nowhere. Its own comment says "when a caller
    # passes its `tenant_key` (the MCP path always does)"; the REST path did not.
    #
    # A confirmation then wrote a `WateringLog` stamped into the victim's tenant.
    #
    # Every route under this prefix carries `{plant_key}`, so the router-level
    # dependency binds on all six. See `app/common/plant_ownership.py` for why it
    # is here rather than in six signatures.
    dependencies=[Depends(get_current_user), Depends(require_owned_plant)],
    responses={**UNAUTHORIZED_RESPONSE, **NOT_FOUND_RESPONSE},
)


def _profile_to_response(p) -> CareProfileResponse:
    return to_response(p, CareProfileResponse)


def _confirmation_to_response(c) -> CareConfirmationResponse:
    return to_response(c, CareConfirmationResponse)


@router.get("/plants/{plant_key}/profile", response_model=CareProfileResponse)
def get_or_create_profile(
    plant_key: Annotated[str, Path(description="Document key of the plant.")],
    species_name: str | None = Query(None, description="Species name used to seed a new profile's presets."),
    botanical_family: str | None = Query(None, description="Botanical family used to seed a new profile's presets."),
    service: CareReminderService = Depends(get_care_reminder_service),
):
    """Return the plant's care profile, creating it from presets if absent."""
    profile = service.get_or_create_profile(plant_key, species_name, botanical_family)
    return _profile_to_response(profile)


@router.patch(
    "/plants/{plant_key}/profile",
    response_model=CareProfileResponse,
    dependencies=[Depends(require_active_tenant_role(TenantRole.GROWER))],
)
def update_profile(
    plant_key: Annotated[str, Path(description="Document key of the plant.")],
    body: CareProfileUpdate,
    user: User = Depends(get_current_user),
    service: CareReminderService = Depends(get_care_reminder_service),
):
    """Update the plant's care profile with the supplied fields."""
    updates = body.model_dump(exclude_none=True)
    updated = service.update_profile(plant_key, updates, user_key=user.key or "")
    return _profile_to_response(updated)


@router.post(
    "/plants/{plant_key}/confirm",
    response_model=CareConfirmationResponse,
    status_code=201,
    dependencies=[Depends(require_active_tenant_role(TenantRole.GROWER))],
)
def confirm_reminder(
    plant_key: Annotated[str, Path(description="Document key of the plant.")],
    body: ConfirmRequest,
    user: User = Depends(get_current_user),
    # Taken into the signature rather than left to the router-level gate alone.
    # `CareReminderService.confirm_reminder` carries its own SEC-001 ownership
    # re-check, guarded by `if tenant_key and ...` — and this, its only REST
    # caller, passed no `tenant_key`, so that check ran for the MCP path and never
    # here: a guard present in the service and inert on the route it was written
    # beside (the #1042 shape this issue exists to end). FastAPI caches the
    # dependency per request, so the plant is already resolved and this costs no
    # second lookup.
    plant: PlantInstance = Depends(require_owned_plant),
    service: CareReminderService = Depends(get_care_reminder_service),
):
    """Confirm a due care reminder and record the performed care."""
    fertilizers = [f.model_dump() for f in body.fertilizers_used] if body.fertilizers_used else None
    confirmation = service.confirm_reminder(
        plant_key,
        body.reminder_type,
        body.notes,
        volume_liters=body.volume_liters,
        fertilizers_used=fertilizers,
        measured_ec=body.measured_ec,
        measured_ph=body.measured_ph,
        tenant_key=plant.tenant_key,
        user_key=user.key or "",
    )
    return _confirmation_to_response(confirmation)


@router.post(
    "/plants/{plant_key}/snooze",
    response_model=CareConfirmationResponse,
    status_code=201,
    dependencies=[Depends(require_active_tenant_role(TenantRole.GROWER))],
)
def snooze_reminder(
    plant_key: Annotated[str, Path(description="Document key of the plant.")],
    body: SnoozeRequest,
    service: CareReminderService = Depends(get_care_reminder_service),
):
    """Snooze a due care reminder for the requested number of days."""
    confirmation = service.snooze_reminder(plant_key, body.reminder_type, body.snooze_days)
    return _confirmation_to_response(confirmation)


@router.get("/plants/{plant_key}/history", response_model=list[CareConfirmationResponse])
def get_confirmation_history(
    plant_key: Annotated[str, Path(description="Document key of the plant.")],
    reminder_type: ReminderType | None = Query(None, description="Filter the history by reminder type."),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of confirmations to return."),
    service: CareReminderService = Depends(get_care_reminder_service),
):
    """List the plant's care-confirmation history, optionally filtered by type."""
    history = service.get_confirmation_history(plant_key, reminder_type, limit)
    return [_confirmation_to_response(c) for c in history]


@router.post(
    "/plants/{plant_key}/reset-profile",
    response_model=CareProfileResponse,
    dependencies=[Depends(require_active_tenant_role(TenantRole.GROWER))],
)
def reset_profile(
    plant_key: Annotated[str, Path(description="Document key of the plant.")],
    species_name: str | None = Query(None, description="Species name used to re-seed the profile's presets."),
    botanical_family: str | None = Query(None, description="Botanical family used to re-seed the profile's presets."),
    service: CareReminderService = Depends(get_care_reminder_service),
):
    """Reset the plant's care profile back to its preset defaults."""
    profile = service.reset_profile(plant_key, species_name, botanical_family)
    return _profile_to_response(profile)
