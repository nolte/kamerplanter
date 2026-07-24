from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.api.mapping import to_response
from app.api.v1.location_types.schemas import (
    LocationTypeCreate,
    LocationTypeResponse,
    LocationTypeUpdate,
)
from app.common.auth import get_current_user
from app.common.dependencies import get_location_type_service
from app.common.openapi_responses import AUTH_CRUD_RESPONSES
from app.domain.models.location_type import LocationType
from app.domain.services.location_type_service import LocationTypeService

router = APIRouter(
    prefix="/location-types",
    tags=["location-types"],
    dependencies=[Depends(get_current_user)],
    responses=AUTH_CRUD_RESPONSES,
)


@router.get("", response_model=list[LocationTypeResponse])
def list_location_types(service: LocationTypeService = Depends(get_location_type_service)):
    """List all location types."""
    items = service.list_all()
    return [to_response(lt, LocationTypeResponse) for lt in items]


@router.get("/{key}", response_model=LocationTypeResponse)
def get_location_type(
    key: Annotated[str, Path(description="Document key of the location type.")],
    service: LocationTypeService = Depends(get_location_type_service),
):
    """Return a single location type by key."""
    lt = service.get(key)
    return to_response(lt, LocationTypeResponse)


@router.post("", response_model=LocationTypeResponse, status_code=201)
def create_location_type(body: LocationTypeCreate, service: LocationTypeService = Depends(get_location_type_service)):
    """Create a new location type."""
    lt = LocationType(**body.model_dump())
    created = service.create(lt)
    return to_response(created, LocationTypeResponse)


@router.put("/{key}", response_model=LocationTypeResponse)
def update_location_type(
    key: Annotated[str, Path(description="Document key of the location type.")],
    body: LocationTypeUpdate,
    service: LocationTypeService = Depends(get_location_type_service),
):
    """Update an existing location type."""
    lt = LocationType(**body.model_dump())
    updated = service.update(key, lt)
    return to_response(updated, LocationTypeResponse)


@router.delete("/{key}", status_code=204)
def delete_location_type(
    key: Annotated[str, Path(description="Document key of the location type.")],
    service: LocationTypeService = Depends(get_location_type_service),
):
    """Delete a location type."""
    service.delete(key)
