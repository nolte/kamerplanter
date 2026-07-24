"""REQ-031 §5.3 — Light-mode public KI endpoints (``/public/ai/*``).

No auth, no tenant, strictly ``context=null`` at the Knowledge Service (§5.3).
IP rate-limited via the shared app limiter. Stage-1 operator flag still applies
(404 when ``AI_FEATURES_ENABLED=false``).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.api.v1.auth.router import limiter
from app.api.v1.ki_assistent.deps import require_ai_feature_flag
from app.api.v1.ki_assistent.schemas import (
    AiResponseSchema,
    HealthResponse,
    PublicAskRequest,
    SourceRefSchema,
)
from app.common.dependencies import get_ai_assistant_service
from app.common.openapi_responses import NOT_FOUND_RESPONSE
from app.config.settings import settings
from app.domain.services.ai_assistant_service import AiAssistantService

router = APIRouter(
    prefix="/public/ai",
    tags=["ki-assistent-public"],
    dependencies=[Depends(require_ai_feature_flag)],
    responses=NOT_FOUND_RESPONSE,
)

_PUBLIC_RATE_LIMIT = f"{settings.ai_public_rate_limit_per_min}/minute"


@router.post("/ask", response_model=AiResponseSchema)
@limiter.limit(_PUBLIC_RATE_LIMIT)
async def public_ask(
    request: Request,
    body: PublicAskRequest,
    service: AiAssistantService = Depends(get_ai_assistant_service),
) -> AiResponseSchema:
    """Answer a free-form knowledge question with no tenant/user context (§5.3)."""
    response = await service.ask_public(body.question, language=body.language or "de")
    return AiResponseSchema(
        answer_text=response.answer_text,
        sources=[SourceRefSchema(**s.model_dump()) for s in response.sources],
        language=response.language,
        language_mismatch_warning=response.language_mismatch_warning,
        uses_tenant_data=response.uses_tenant_data,
        uses_cloud_provider=response.uses_cloud_provider,
        confidence=response.confidence,
        model_name=response.model_name,
        provider_type=response.provider_type,
        kb_version=response.kb_version,
        generated_at=response.generated_at,
    )


@router.get("/health", response_model=HealthResponse)
async def public_health(
    service: AiAssistantService = Depends(get_ai_assistant_service),
) -> HealthResponse:
    """Knowledge-Service availability probe (light-mode, unauthenticated)."""
    return HealthResponse(healthy=await service.health_check())
