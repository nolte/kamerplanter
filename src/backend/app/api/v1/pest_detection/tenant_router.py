"""REQ-044 §6 — tenant-scoped pest-detection endpoints.

Mounted under /api/v1/t/{tenant_slug}/pests/. Reads (``/status``, ``/history``)
are open to every tenant member via ``get_current_tenant``; the detect and
feedback writes require grower or above (``require_tenant_role``, #1333) and
``create-inspection`` goes through ``require_permission`` like the rest of IPM
(REQ-049 §2.3). ``/detect`` strips EXIF and tiles
the image before any inference; the cloud path additionally enforces the
``pest_detection_cloud`` consent inside the service. No endpoint ever triggers a
treatment (§0) — at most an IPM inspection is suggested.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Path, Query, UploadFile

from app.api.v1.pest_detection.schemas import (
    CreateInspectionResponse,
    FeedbackRequest,
    PestDetectionResponse,
    PestDetectionStatusResponse,
)
from app.common.auth import get_current_tenant, require_permission, require_tenant_role
from app.common.dependencies import get_pest_detection_service
from app.common.enums import CaptureDevice, TenantRole
from app.common.exceptions import UnsupportedMediaTypeError
from app.common.openapi_responses import NOT_FOUND_RESPONSE
from app.core.permissions import Action, ResourceType
from app.domain.models.tenant_context import TenantContext
from app.domain.services.pest_detection_service import PestDetectionService

router = APIRouter(prefix="/pests", tags=["pest-detection"], responses=NOT_FOUND_RESPONSE)

_ALLOWED_CONTENT_TYPES = frozenset({"image/jpeg", "image/png"})


@router.get("/status", response_model=PestDetectionStatusResponse)
def pest_detection_status(
    ctx: TenantContext = Depends(get_current_tenant),
    service: PestDetectionService = Depends(get_pest_detection_service),
) -> PestDetectionStatusResponse:
    """Report which pest-detection adapter is active (or none → button hidden)."""
    return PestDetectionStatusResponse(**service.get_status())


@router.post("/detect", response_model=PestDetectionResponse)
async def detect_pests_global(
    image: UploadFile,
    language: str = Form("de", description="Language code for the returned finding labels and disclaimer."),
    capture_device: CaptureDevice = Form(
        CaptureDevice.UNKNOWN,
        description=(
            "Which physical device produced the image (#1137). A microscope frame "
            "and a phone frame are different image distributions and favour "
            "opposite detection modes; recording which is which keeps HITL feedback "
            "and accuracy analysis separable. Client-declared, optional, and never "
            "an input to adapter choice or access."
        ),
    ),
    # Ab Gärtner (#1333, REQ-049 §2.3). Same argument as #1256/#1260 made for
    # `POST /identification/identify`, unchanged: detecting is a write — it
    # persists a `pest_detections` record whose key powers HITL feedback — AND it
    # sends a photo to a third-party adapter on the cloud path. A role that may
    # not create domain data must not be able to release data out of the
    # installation either, and a viewer could do it in a loop.
    #
    # `require_permission(IPM_TREATMENT, CREATE)` was rejected although the
    # fourth route in this file uses it: a detection is not a treatment (§0 says
    # so explicitly), and gating it as one would make the permission matrix
    # claim something false about what happened.
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: PestDetectionService = Depends(get_pest_detection_service),
) -> PestDetectionResponse:
    """Detect pests/symptoms in a photo without binding to a plant (REQ-044 §7).

    Plant-agnostic entry point for the standalone pest-detection page. The image
    recognition is identical to the plant-bound flow — only the plant binding is
    dropped (``plant_instance_key=None``), so no IPM inspection is suggested and
    the result is not attached to any plant history. The detection is still
    persisted (so the returned ``key`` powers HITL feedback) and always carries a
    disclaimer. Same feature gate, adapter resolution and consent rules as the
    plant-bound endpoint.
    """
    content_type = (image.content_type or "").lower().strip()
    if content_type not in _ALLOWED_CONTENT_TYPES:
        raise UnsupportedMediaTypeError(content_type, sorted(_ALLOWED_CONTENT_TYPES))

    image_data = await image.read()
    result = service.detect_pests(
        image_data,
        tenant_key=ctx.tenant_key,
        user_key=ctx.user_key,
        plant_instance_key=None,
        language=language,
        capture_device=capture_device,
    )
    return PestDetectionResponse(**result)


@router.post("/plants/{plant_key}/detect", response_model=PestDetectionResponse)
async def detect_pests(
    plant_key: Annotated[str, Path(description="Document key of the plant instance.")],
    image: UploadFile,
    language: str = Form("de", description="Language code for the returned finding labels and disclaimer."),
    capture_device: CaptureDevice = Form(
        CaptureDevice.UNKNOWN,
        description=(
            "Which physical device produced the image (#1137). A microscope frame "
            "and a phone frame are different image distributions and favour "
            "opposite detection modes; recording which is which keeps HITL feedback "
            "and accuracy analysis separable. Client-declared, optional, and never "
            "an input to adapter choice or access."
        ),
    ),
    # Ab Gärtner (#1333, REQ-049 §2.3). Same argument as #1256/#1260 made for
    # `POST /identification/identify`, unchanged: detecting is a write — it
    # persists a `pest_detections` record whose key powers HITL feedback — AND it
    # sends a photo to a third-party adapter on the cloud path. A role that may
    # not create domain data must not be able to release data out of the
    # installation either, and a viewer could do it in a loop.
    #
    # `require_permission(IPM_TREATMENT, CREATE)` was rejected although the
    # fourth route in this file uses it: a detection is not a treatment (§0 says
    # so explicitly), and gating it as one would make the permission matrix
    # claim something false about what happened.
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: PestDetectionService = Depends(get_pest_detection_service),
) -> PestDetectionResponse:
    """Detect pests (Mode 1) and/or symptoms (Mode 2) in an uploaded photo.

    JPEG/PNG, max 8 MB. EXIF is stripped before processing, the image is tiled
    (mandatory), and the result always carries a disclaimer and never persists
    the image. Cloud detection requires the ``pest_detection_cloud`` consent.
    """
    content_type = (image.content_type or "").lower().strip()
    if content_type not in _ALLOWED_CONTENT_TYPES:
        raise UnsupportedMediaTypeError(content_type, sorted(_ALLOWED_CONTENT_TYPES))

    image_data = await image.read()
    result = service.detect_pests(
        image_data,
        tenant_key=ctx.tenant_key,
        user_key=ctx.user_key,
        plant_instance_key=plant_key,
        language=language,
        capture_device=capture_device,
    )
    return PestDetectionResponse(**result)


@router.get("/plants/{plant_key}/history", response_model=list[PestDetectionResponse])
def detection_history(
    plant_key: Annotated[str, Path(description="Document key of the plant instance.")],
    limit: int = Query(20, ge=1, le=100, description="Maximum number of recent detections to return."),
    ctx: TenantContext = Depends(get_current_tenant),
    service: PestDetectionService = Depends(get_pest_detection_service),
) -> list[PestDetectionResponse]:
    """Return the recent pest detections for a plant (no images retained)."""
    entries = service.get_history(tenant_key=ctx.tenant_key, plant_instance_key=plant_key, limit=limit)
    return [PestDetectionResponse(**e) for e in entries]


@router.post("/detections/{detection_key}/feedback", response_model=PestDetectionResponse)
def submit_feedback(
    detection_key: Annotated[str, Path(description="Document key of the pest detection.")],
    body: FeedbackRequest,
    # Ab Gärtner (#1333). Feedback corrects the recorded outcome of an existing
    # detection, so the fitting predicate is `can_edit_resource` — lead or
    # grower, which `require_tenant_role(GROWER)` is by rank. A viewer altering
    # someone else's recorded finding is the same "read-only role writes"
    # defect as the two routes above.
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: PestDetectionService = Depends(get_pest_detection_service),
) -> PestDetectionResponse:
    """Human-in-the-loop feedback: confirmed / wrong / was a beneficial (§5.3)."""
    result = service.submit_feedback(
        detection_key,
        tenant_key=ctx.tenant_key,
        finding_label=body.finding_label,
        confirmed=body.confirmed,
        actual_label=body.actual_label,
        was_beneficial=body.was_beneficial,
    )
    return PestDetectionResponse(**result)


@router.post("/detections/{detection_key}/create-inspection", response_model=CreateInspectionResponse, status_code=201)
def create_inspection(
    detection_key: Annotated[str, Path(description="Document key of the pest detection.")],
    plant_key: str = Query(..., description="Plant instance the inspection belongs to"),
    ctx: TenantContext = Depends(require_permission(ResourceType.IPM_TREATMENT, Action.CREATE)),
    service: PestDetectionService = Depends(get_pest_detection_service),
) -> CreateInspectionResponse:
    """Create a REQ-010 inspection from a detection. Never a treatment (§0)."""
    result = service.create_inspection(detection_key, tenant_key=ctx.tenant_key, plant_key=plant_key)
    return CreateInspectionResponse(**result)
