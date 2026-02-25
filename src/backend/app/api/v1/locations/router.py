from fastapi import APIRouter, Depends, Query

from app.api.v1.locations.schemas import LocationCreate, LocationResponse
from app.common.dependencies import get_site_service
from app.domain.models.site import Location
from app.domain.services.site_service import SiteService

router = APIRouter(prefix="/locations", tags=["locations"])

@router.get("", response_model=list[LocationResponse])
def list_locations(site_key: str = Query(...), service: SiteService = Depends(get_site_service)):
    items = service.list_locations(site_key)
    return [LocationResponse(key=loc.key or "", **loc.model_dump(exclude={"key"})) for loc in items]

@router.get("/{key}", response_model=LocationResponse)
def get_location(key: str, service: SiteService = Depends(get_site_service)):
    loc = service.get_location(key)
    return LocationResponse(key=loc.key or "", **loc.model_dump(exclude={"key"}))

@router.post("", response_model=LocationResponse, status_code=201)
def create_location(body: LocationCreate, service: SiteService = Depends(get_site_service)):
    location = Location(**body.model_dump())
    created = service.create_location(location)
    return LocationResponse(key=created.key or "", **created.model_dump(exclude={"key"}))

@router.put("/{key}", response_model=LocationResponse)
def update_location(key: str, body: LocationCreate, service: SiteService = Depends(get_site_service)):
    location = Location(**body.model_dump())
    updated = service.update_location(key, location)
    return LocationResponse(key=updated.key or "", **updated.model_dump(exclude={"key"}))

@router.delete("/{key}", status_code=204)
def delete_location(key: str, service: SiteService = Depends(get_site_service)):
    service.delete_location(key)
