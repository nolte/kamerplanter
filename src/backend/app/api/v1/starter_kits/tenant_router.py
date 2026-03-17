from fastapi import APIRouter, Depends, Query

from app.api.v1.starter_kits.schemas import (
    SpeciesAvailability,
    StarterKitResponse,
    StarterKitTenantResponse,
)
from app.common.auth import get_current_tenant
from app.common.dependencies import get_starter_kit_service
from app.domain.models.tenant_context import TenantContext
from app.domain.services.starter_kit_service import StarterKitService

router = APIRouter(prefix="/starter-kits", tags=["starter-kits"])


@router.get("", response_model=list[StarterKitResponse])
def list_starter_kits_for_tenant(
    difficulty: str | None = Query(None),
    ctx: TenantContext = Depends(get_current_tenant),
    service: StarterKitService = Depends(get_starter_kit_service),
):
    kits = service.list_kits_for_tenant(ctx.tenant_key, difficulty)
    return [StarterKitResponse(key=k.key or "", **k.model_dump(exclude={"key"})) for k in kits]


@router.get("/{kit_id}", response_model=StarterKitTenantResponse)
def get_starter_kit_for_tenant(
    kit_id: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: StarterKitService = Depends(get_starter_kit_service),
):
    detail = service.get_kit_detail_for_tenant(kit_id, ctx.tenant_key)
    kit = detail["kit"]
    return StarterKitTenantResponse(
        key=kit.key or "",
        species_availability=[SpeciesAvailability(**sa) for sa in detail["species_availability"]],
        **kit.model_dump(exclude={"key"}),
    )
