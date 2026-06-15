"""REQ-029 §3.7 — Tenant-scoped plant-identification API endpoints.

Mounted under /api/v1/t/{tenant_slug}/identification/.

- ``GET  /status``                    public (no auth) — feature toggle.
- ``POST /identify``                  JWT + tenant + consent ``plant_identification``.
- ``POST /identify/{key}/confirm``    JWT + tenant.
- ``GET  /history``                   JWT + tenant.

Photos are uploaded as multipart/form-data. Image bytes are never persisted;
EXIF is stripped in the service before any upload to an external adapter.
"""

import structlog
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile

from app.api.v1.recognition.schemas import (
    AdapterStatus,
    ConfirmResponse,
    HistoryEntry,
    IdentificationResponse,
    IdentificationStatusResponse,
)
from app.common.auth import get_current_tenant
from app.common.dependencies import get_identification_service
from app.common.exceptions import UnsupportedMediaTypeError
from app.domain.models.identification import PlantOrgan
from app.domain.models.tenant_context import TenantContext
from app.domain.services.identification_service import IdentificationService

logger = structlog.get_logger()

router = APIRouter(prefix="/identification", tags=["identification"])

_ALLOWED_CONTENT_TYPES = ("image/jpeg", "image/png")


@router.get("/status", response_model=IdentificationStatusResponse)
async def identification_status(
    tenant_slug: str,
    service: IdentificationService = Depends(get_identification_service),
) -> IdentificationStatusResponse:
    """Status of the identification services (available? healthy? rate limits?).

    Public (no auth) so the onboarding wizard can decide whether to show the
    camera buttons. Returns no user-specific data.
    """
    status = await service.get_status()
    adapters = {key: AdapterStatus(**value) for key, value in status.items()}
    return IdentificationStatusResponse(
        available=service.is_available(),
        supports_health=any(a.supports_health for a in adapters.values()),
        adapters=adapters,
    )


@router.post("/identify", response_model=IdentificationResponse)
async def identify_plant(
    tenant_slug: str,
    image: UploadFile = File(..., description="JPEG/PNG, max 5 MB"),
    organ: str = Form("auto", description="leaf, flower, fruit, bark, habit, auto"),
    include_health: bool = Form(False),
    language: str = Form("de"),
    ctx: TenantContext = Depends(get_current_tenant),
    service: IdentificationService = Depends(get_identification_service),
) -> IdentificationResponse:
    """Identify a plant from an image.

    Requires consent ``plant_identification`` (the image is sent to an external
    service). The image is never persisted; only a hash and the results are kept.
    """
    if image.content_type not in _ALLOWED_CONTENT_TYPES:
        raise UnsupportedMediaTypeError(image.content_type or "unknown", list(_ALLOWED_CONTENT_TYPES))

    image_data = await image.read()
    result = await service.identify_plant(
        image_data,
        organ=PlantOrgan(organ),
        include_health=include_health,
        language=language,
        tenant_key=ctx.tenant_key,
        user_key=ctx.user_key,
    )
    return IdentificationResponse(**result)


@router.post("/identify/{request_key}/confirm", response_model=ConfirmResponse)
async def confirm_identification(
    tenant_slug: str,
    request_key: str,
    selected_rank: int = Query(..., ge=1, le=10),
    ctx: TenantContext = Depends(get_current_tenant),
    service: IdentificationService = Depends(get_identification_service),
) -> ConfirmResponse:
    """Confirm an identification suggestion.

    The returned ``matched_species_key`` lets the client create a PlantInstance.
    """
    result = await service.confirm_identification(
        request_key,
        selected_rank,
        tenant_key=ctx.tenant_key,
    )
    return ConfirmResponse(**result)


@router.get("/history", response_model=list[HistoryEntry])
async def identification_history(
    tenant_slug: str,
    limit: int = Query(20, ge=1, le=100),
    ctx: TenantContext = Depends(get_current_tenant),
    service: IdentificationService = Depends(get_identification_service),
) -> list[HistoryEntry]:
    """Identification history of the current user within this tenant."""
    entries = service.get_history(
        tenant_key=ctx.tenant_key,
        user_key=ctx.user_key,
        limit=limit,
    )
    return [HistoryEntry(**entry) for entry in entries]
