from fastapi import APIRouter, Depends, Query

from app.api.v1.starter_kits.schemas import StarterKitResponse
from app.common.auth import get_current_user
from app.common.dependencies import get_starter_kit_service
from app.domain.services.starter_kit_service import StarterKitService

router = APIRouter(prefix="/starter-kits", tags=["starter-kits"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[StarterKitResponse])
def list_starter_kits(
    difficulty: str | None = Query(None),
    service: StarterKitService = Depends(get_starter_kit_service),
):
    kits = service.list_kits(difficulty)
    return [StarterKitResponse(key=k.key or "", **k.model_dump(exclude={"key"})) for k in kits]


@router.get("/{kit_id}", response_model=StarterKitResponse)
def get_starter_kit(
    kit_id: str,
    service: StarterKitService = Depends(get_starter_kit_service),
):
    kit = service.get_kit_by_id(kit_id)
    return StarterKitResponse(key=kit.key or "", **kit.model_dump(exclude={"key"}))
