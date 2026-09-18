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
from app.common.openapi_responses import (
    FORBIDDEN_RESPONSE,
    NOT_FOUND_RESPONSE,
    UNAUTHORIZED_RESPONSE,
    VALIDATION_RESPONSE,
)
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
    species_name: Annotated[
        str | None,
        Query(
            deprecated=True,
            description=(
                "Deprecated and ignored (#1489): the presets are resolved from the "
                "plant's own species. Accepted so an existing client is not broken."
            ),
        ),
    ] = None,
    service: CareReminderService = Depends(get_care_reminder_service),
):
    """Return the plant's care profile, generating presets if absent — without storing them.

    A read. `may_create=False` is what makes that true: an absent profile is
    generated and returned, and nothing is written, so every member may call this
    including a viewer (#1422 round 2).

    **The preset inputs are no longer taken from the client** (#1489). Two query
    parameters used to seed the generated presets; measured 2026-09-17, the frontend
    sends `species_name` and never `botanical_family`, and `species_name` takes part
    in no decision the engine makes. So the family — the one that *did* decide — was
    supplied by nobody and every generated profile came out `TROPICAL`.
    `botanical_family` is therefore gone (no client sent it) and `species_name` is
    kept deprecated and ignored, which is exactly what it always was.
    """
    del species_name  # accepted for compatibility; the service resolves its own inputs
    # `may_create=False`: this is a read, and a read does not write. Round 1 of the
    # #1422 review gated the whole operation instead, which took the *read* away from
    # viewers — `get_or_create_profile` returns an existing profile untouched, so a
    # viewer opening the care tab of an already-profiled plant got a 403 and the
    # frontend a permanently spinning skeleton. The gate belonged on the write, and
    # the write is now simply not performed.
    profile = service.get_or_create_profile(plant_key, may_create=False)
    return _profile_to_response(profile)


@router.patch(
    "/plants/{plant_key}/profile",
    response_model=CareProfileResponse,
    dependencies=[Depends(require_active_tenant_role(TenantRole.GROWER))],
    responses={**FORBIDDEN_RESPONSE, **VALIDATION_RESPONSE},
)
def update_profile(
    plant_key: Annotated[str, Path(description="Document key of the plant.")],
    body: CareProfileUpdate,
    user: User = Depends(get_current_user),
    service: CareReminderService = Depends(get_care_reminder_service),
):
    """Update the plant's care profile with the supplied fields.

    **A field the body omits is left unchanged; a field the body sends as `null` is
    cleared** (#1506). The two are different requests, and only `notes` and
    `water_quality_hint` may be cleared — they are the profile's only nullable
    fields. `null` for any other field is answered with `422`, because the profile
    has no `null` to store for it; omit the field instead.

    Editing a watering, fertilising, pest-check, humidity or repotting interval also
    reschedules the plant's matching **pending** care task and resets the matching
    adaptive-learned interval (#622).
    """
    # `exclude_unset`, not `exclude_none` (#1506). Every field of `CareProfileUpdate`
    # defaults to `None` for "not supplied", so `exclude_none` collapsed the two cases
    # a PATCH has to distinguish: a field the body omitted and a field the body sent as
    # `null`. The second is a clear — the care form sends `notes: null` the moment the
    # user empties the box — and it was dropped here, one layer above the merge-mode
    # repository that would have dropped it again. `model_fields_set` (what
    # `exclude_unset` reads) is the only thing that knows the difference; a `null` for a
    # field the profile cannot hold as one is refused by the schema with 422, so nothing
    # unwritable reaches the service.
    updates = body.model_dump(exclude_unset=True)
    updated = service.update_profile(plant_key, updates, user_key=user.key or "")
    return _profile_to_response(updated)


@router.post(
    "/plants/{plant_key}/confirm",
    response_model=CareConfirmationResponse,
    status_code=201,
    dependencies=[Depends(require_active_tenant_role(TenantRole.GROWER))],
    responses=FORBIDDEN_RESPONSE,
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
    responses=FORBIDDEN_RESPONSE,
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
    responses=FORBIDDEN_RESPONSE,
)
def reset_profile(
    plant_key: Annotated[str, Path(description="Document key of the plant.")],
    service: CareReminderService = Depends(get_care_reminder_service),
):
    """Reset the plant's care profile back to its preset defaults.

    Both query parameters this route used to take are gone (#1489): measured
    2026-09-17, `careReminders.resetProfile` sends neither, so the reset a user
    reaches *because* the presets look wrong re-seeded them from the same
    `TROPICAL` fallback that made them look wrong. The service resolves the
    plant's species and family itself.
    """
    profile = service.reset_profile(plant_key)
    return _profile_to_response(profile)
