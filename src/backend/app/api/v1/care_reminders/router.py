from fastapi import APIRouter, Depends, Query

from app.api.v1.care_reminders.schemas import (
    CareConfirmationResponse,
    CareDashboardEntryResponse,
    CareProfileResponse,
    CareProfileUpdate,
    ConfirmRequest,
    SnoozeRequest,
)
from app.common.auth import get_current_user
from app.common.dependencies import get_care_reminder_service
from app.common.enums import ReminderType
from app.domain.services.care_reminder_service import CareReminderService

router = APIRouter(prefix="/care-reminders", tags=["care-reminders"], dependencies=[Depends(get_current_user)])


def _profile_to_response(p) -> CareProfileResponse:
    return CareProfileResponse(key=p.key or "", **p.model_dump(exclude={"key"}))


def _confirmation_to_response(c) -> CareConfirmationResponse:
    return CareConfirmationResponse(key=c.key or "", **c.model_dump(exclude={"key"}))


@router.get("/dashboard", response_model=list[CareDashboardEntryResponse])
def get_care_dashboard(
    hemisphere: str = Query("north", pattern="^(north|south)$"),
    service: CareReminderService = Depends(get_care_reminder_service),
):
    # In a full implementation this would query plant instances with their species/family data.
    # For now, return entries based on existing profiles.
    entries = service.get_care_dashboard([], hemisphere)
    return [CareDashboardEntryResponse(**e.model_dump()) for e in entries]


@router.get("/plants/{plant_key}/profile", response_model=CareProfileResponse)
def get_or_create_profile(
    plant_key: str,
    species_name: str | None = Query(None),
    botanical_family: str | None = Query(None),
    service: CareReminderService = Depends(get_care_reminder_service),
):
    profile = service.get_or_create_profile(plant_key, species_name, botanical_family)
    return _profile_to_response(profile)


@router.patch("/plants/{plant_key}/profile", response_model=CareProfileResponse)
def update_profile(
    plant_key: str,
    body: CareProfileUpdate,
    service: CareReminderService = Depends(get_care_reminder_service),
):
    updates = body.model_dump(exclude_none=True)
    updated = service.update_profile(plant_key, updates)
    return _profile_to_response(updated)


@router.post("/plants/{plant_key}/confirm", response_model=CareConfirmationResponse, status_code=201)
def confirm_reminder(
    plant_key: str,
    body: ConfirmRequest,
    service: CareReminderService = Depends(get_care_reminder_service),
):
    fertilizers = [f.model_dump() for f in body.fertilizers_used] if body.fertilizers_used else None
    confirmation = service.confirm_reminder(
        plant_key,
        body.reminder_type,
        body.notes,
        volume_liters=body.volume_liters,
        fertilizers_used=fertilizers,
        measured_ec=body.measured_ec,
        measured_ph=body.measured_ph,
    )
    return _confirmation_to_response(confirmation)


@router.post("/plants/{plant_key}/snooze", response_model=CareConfirmationResponse, status_code=201)
def snooze_reminder(
    plant_key: str,
    body: SnoozeRequest,
    service: CareReminderService = Depends(get_care_reminder_service),
):
    confirmation = service.snooze_reminder(plant_key, body.reminder_type, body.snooze_days)
    return _confirmation_to_response(confirmation)


@router.get("/plants/{plant_key}/history", response_model=list[CareConfirmationResponse])
def get_confirmation_history(
    plant_key: str,
    reminder_type: ReminderType | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    service: CareReminderService = Depends(get_care_reminder_service),
):
    history = service.get_confirmation_history(plant_key, reminder_type, limit)
    return [_confirmation_to_response(c) for c in history]


@router.post("/plants/{plant_key}/reset-profile", response_model=CareProfileResponse)
def reset_profile(
    plant_key: str,
    species_name: str | None = Query(None),
    botanical_family: str | None = Query(None),
    service: CareReminderService = Depends(get_care_reminder_service),
):
    profile = service.reset_profile(plant_key, species_name, botanical_family)
    return _profile_to_response(profile)
