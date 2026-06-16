"""REQ-029 — tenant-scoped plant-identification endpoints.

Mounted under /api/v1/t/{tenant_slug}/identification/. All endpoints require
authentication and tenant membership via ``get_current_tenant``. ``/identify``
additionally enforces the ``plant_identification`` consent inside the service
(REQ-029-A §0.1.1 point 2) before any photo leaves the instance.
"""

from fastapi import APIRouter, Depends, Form, Query, UploadFile

from app.api.v1.recognition.schemas import (
    HistoryEntryResponse,
    IdentifyResponse,
    SelectResultResponse,
    SuggestionResponse,
)
from app.common.auth import get_current_tenant
from app.common.dependencies import get_identification_service
from app.common.exceptions import UnsupportedMediaTypeError
from app.domain.interfaces.plant_identification_adapter import PlantOrgan
from app.domain.models.tenant_context import TenantContext
from app.domain.services.identification_service import IdentificationService

router = APIRouter(prefix="/identification", tags=["identification"])

_ALLOWED_CONTENT_TYPES = frozenset({"image/jpeg", "image/png"})


def _parse_organ(value: str) -> PlantOrgan:
    try:
        return PlantOrgan(value)
    except ValueError as exc:
        raise UnsupportedMediaTypeError(value, [o.value for o in PlantOrgan]) from exc


@router.post("/identify", response_model=IdentifyResponse)
async def identify_plant(
    image: UploadFile,
    organ: str = Form("auto", description="leaf, flower, fruit, bark, habit, auto"),
    language: str = Form("de"),
    ctx: TenantContext = Depends(get_current_tenant),
    service: IdentificationService = Depends(get_identification_service),
) -> IdentifyResponse:
    """Identify a plant from an uploaded image (JPEG/PNG, max 5 MB).

    Consent ``plant_identification`` is a hard precondition: the photo is sent
    to Pl@ntNet (Phase-1 primary), EXIF-stripped and normalized beforehand, and
    is never persisted. Returns rank-sorted suggestions for explicit selection.
    """
    content_type = (image.content_type or "").lower().strip()
    if content_type not in _ALLOWED_CONTENT_TYPES:
        raise UnsupportedMediaTypeError(content_type, sorted(_ALLOWED_CONTENT_TYPES))

    image_data = await image.read()
    parsed_organ = _parse_organ(organ)

    result = service.identify_plant(
        image_data,
        organ=parsed_organ,
        language=language,
        tenant_key=ctx.tenant_key,
        user_key=ctx.user_key,
    )
    return IdentifyResponse(**result)


@router.post("/{request_key}/select", response_model=SelectResultResponse)
def select_result(
    request_key: str,
    selected_rank: int = Query(..., ge=1, le=10),
    ctx: TenantContext = Depends(get_current_tenant),
    service: IdentificationService = Depends(get_identification_service),
) -> SelectResultResponse:
    """Persist the user's explicit candidate choice (REQ-029-A §0.1.1 point 3).

    The returned ``matched_species_key`` / scientific name drives the
    'create plant' step (PlantInstance + species link). No silent auto-create.
    """
    result = service.select_result(
        request_key,
        selected_rank,
        tenant_key=ctx.tenant_key,
    )
    return SelectResultResponse(**result)


@router.get("/history", response_model=list[HistoryEntryResponse])
def identification_history(
    limit: int = Query(20, ge=1, le=100),
    ctx: TenantContext = Depends(get_current_tenant),
    service: IdentificationService = Depends(get_identification_service),
) -> list[HistoryEntryResponse]:
    """Return the current user's recent identification requests (no images)."""
    entries = service.get_history(
        tenant_key=ctx.tenant_key,
        user_key=ctx.user_key,
        limit=limit,
    )
    return [
        HistoryEntryResponse(
            key=e.get("key"),
            adapter_key=e["adapter_key"],
            request_type=e["request_type"],
            image_organ=e["image_organ"],
            status=e["status"],
            results=[SuggestionResponse(**r) for r in e.get("results", [])],
            selected_result_rank=e.get("selected_result_rank"),
            created_at=str(e["created_at"]) if e.get("created_at") else None,
        )
        for e in entries
    ]
