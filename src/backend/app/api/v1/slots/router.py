from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Query

from app.api.v1.slots.schemas import SlotCreate, SlotResponse
from app.common.dependencies import get_site_service
from app.domain.models.site import Slot

if TYPE_CHECKING:
    from app.domain.services.site_service import SiteService

router = APIRouter(prefix="/slots", tags=["slots"])


@router.get("", response_model=list[SlotResponse])
def list_slots(location_key: str = Query(...), service: SiteService = Depends(get_site_service)):
    items = service.list_slots(location_key)
    return [SlotResponse(key=s.key or "", **s.model_dump(exclude={"key"})) for s in items]


@router.get("/{key}", response_model=SlotResponse)
def get_slot(key: str, service: SiteService = Depends(get_site_service)):
    s = service.get_slot(key)
    return SlotResponse(key=s.key or "", **s.model_dump(exclude={"key"}))


@router.post("", response_model=SlotResponse, status_code=201)
def create_slot(body: SlotCreate, service: SiteService = Depends(get_site_service)):
    slot = Slot(**body.model_dump())
    created = service.create_slot(slot)
    return SlotResponse(key=created.key or "", **created.model_dump(exclude={"key"}))


@router.put("/{key}", response_model=SlotResponse)
def update_slot(key: str, body: SlotCreate, service: SiteService = Depends(get_site_service)):
    slot = Slot(**body.model_dump())
    updated = service.update_slot(key, slot)
    return SlotResponse(key=updated.key or "", **updated.model_dump(exclude={"key"}))


@router.delete("/{key}", status_code=204)
def delete_slot(key: str, service: SiteService = Depends(get_site_service)):
    service.delete_slot(key)
