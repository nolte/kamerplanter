from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.mapping import to_response
from app.api.v1.starter_kits.schemas import StarterKitResponse
from app.common.auth import get_current_user
from app.common.dependencies import get_starter_kit_service
from app.common.openapi_responses import NOT_FOUND_RESPONSE, UNAUTHORIZED_RESPONSE
from app.domain.services.starter_kit_service import StarterKitService

router = APIRouter(
    prefix="/starter-kits",
    tags=["starter-kits"],
    dependencies=[Depends(get_current_user)],
    responses={**UNAUTHORIZED_RESPONSE, **NOT_FOUND_RESPONSE},
)


@router.get("", response_model=list[StarterKitResponse])
def list_starter_kits(
    difficulty: str | None = Query(None, description="Filter starter kits by difficulty level."),
    service: StarterKitService = Depends(get_starter_kit_service),
):
    """List the available starter kits, optionally filtered by difficulty."""
    kits = service.list_kits(difficulty)
    return [to_response(k, StarterKitResponse) for k in kits]


@router.get("/{kit_id}", response_model=StarterKitResponse)
def get_starter_kit(
    kit_id: Annotated[str, Path(description="Identifier of the starter kit.")],
    service: StarterKitService = Depends(get_starter_kit_service),
):
    """Return a single starter kit by id."""
    kit = service.get_kit_by_id(kit_id)
    return to_response(kit, StarterKitResponse)
