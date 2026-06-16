"""REQ-029 — public (non-tenant) plant-identification endpoints.

Only the status endpoint is public so the frontend (incl. onboarding) can
discover whether the feature is configured before requiring auth/tenant
context. All processing endpoints are tenant-scoped (see ``tenant_router``).
"""

from fastapi import APIRouter, Depends

from app.api.v1.recognition.schemas import IdentificationStatusResponse
from app.common.dependencies import get_identification_service
from app.domain.services.identification_service import IdentificationService

router = APIRouter(prefix="/recognition", tags=["recognition"])


@router.get("/status", response_model=IdentificationStatusResponse)
def identification_status(
    service: IdentificationService = Depends(get_identification_service),
) -> IdentificationStatusResponse:
    """Return identification feature availability and per-adapter status.

    No authentication required so the camera UI can be toggled before login
    (REQ-029 §3.7). Graceful degradation: when nothing is configured,
    ``available`` is False and the frontend hides all camera entry points.
    """
    return IdentificationStatusResponse(**service.get_status())
