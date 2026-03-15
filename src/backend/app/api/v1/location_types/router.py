from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends

from app.api.v1.location_types.schemas import (
    LocationTypeCreate,
    LocationTypeResponse,
    LocationTypeUpdate,
)
from app.common.dependencies import get_location_type_service
from app.domain.models.location_type import LocationType

if TYPE_CHECKING:
    from app.domain.services.location_type_service import LocationTypeService

router = APIRouter(prefix="/location-types", tags=["location-types"])


@router.get("", response_model=list[LocationTypeResponse])
def list_location_types(service: LocationTypeService = Depends(get_location_type_service)):
    items = service.list_all()
    return [LocationTypeResponse(key=lt.key or "", **lt.model_dump(exclude={"key"})) for lt in items]


@router.get("/{key}", response_model=LocationTypeResponse)
def get_location_type(key: str, service: LocationTypeService = Depends(get_location_type_service)):
    lt = service.get(key)
    return LocationTypeResponse(key=lt.key or "", **lt.model_dump(exclude={"key"}))


@router.post("", response_model=LocationTypeResponse, status_code=201)
def create_location_type(body: LocationTypeCreate, service: LocationTypeService = Depends(get_location_type_service)):
    lt = LocationType(**body.model_dump())
    created = service.create(lt)
    return LocationTypeResponse(key=created.key or "", **created.model_dump(exclude={"key"}))


@router.put("/{key}", response_model=LocationTypeResponse)
def update_location_type(
    key: str,
    body: LocationTypeUpdate,
    service: LocationTypeService = Depends(get_location_type_service),
):
    lt = LocationType(**body.model_dump())
    updated = service.update(key, lt)
    return LocationTypeResponse(key=updated.key or "", **updated.model_dump(exclude={"key"}))


@router.delete("/{key}", status_code=204)
def delete_location_type(key: str, service: LocationTypeService = Depends(get_location_type_service)):
    service.delete(key)
