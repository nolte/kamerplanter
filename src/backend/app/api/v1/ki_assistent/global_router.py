"""REQ-031 §5.2 — global platform-admin KI endpoints (``/ai/*``).

Knowledge-Service operations that are not tenant-scoped. Stage-1 operator flag
applies (404 when disabled); platform-admin auth is required.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.v1.ki_assistent.deps import require_ai_feature_flag
from app.api.v1.ki_assistent.schemas import HealthResponse
from app.common.auth import require_platform_admin
from app.common.dependencies import get_ai_assistant_service
from app.common.openapi_responses import AUTH_RESPONSES, NOT_FOUND_RESPONSE
from app.domain.services.ai_assistant_service import AiAssistantService

router = APIRouter(
    prefix="/ai",
    tags=["ki-assistent-admin"],
    dependencies=[Depends(require_ai_feature_flag), Depends(require_platform_admin)],
    responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE},
)


@router.get("/knowledge-service/health", response_model=HealthResponse)
async def knowledge_service_health(
    service: AiAssistantService = Depends(get_ai_assistant_service),
) -> HealthResponse:
    """Report Knowledge-Service readiness (platform-admin only)."""
    return HealthResponse(healthy=await service.health_check())
