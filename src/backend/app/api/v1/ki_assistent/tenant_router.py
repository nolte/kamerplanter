"""REQ-031 §5.1 — tenant-scoped KI-Assistent endpoints (``/ai/*``).

Mounted under ``/api/v1/t/{tenant_slug}/ai``. Every route runs the three-stage
toggle: stage 1 (operator flag → 404) and stage 2 (tenant setting → 403) via the
router-level ``require_ai_tenant_enabled`` dependency; stage 3 (consent → 403) is
enforced inside the service per endpoint class (§1.3).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.api.v1.ki_assistent.deps import require_ai_tenant_enabled
from app.api.v1.ki_assistent.schemas import (
    AiResponseSchema,
    ChatMessageRequest,
    ConversationCreateRequest,
    ConversationSummary,
    ExplainRequest,
    ProviderSummary,
    SourceRefSchema,
    TipCardSchema,
    TipListResponse,
)
from app.common.auth import get_current_tenant
from app.common.dependencies import get_ai_assistant_service
from app.domain.models.ai_assistant import AiResponse, AiTipCard
from app.domain.models.tenant_context import TenantContext
from app.domain.services.ai_assistant_service import AiAssistantService

router = APIRouter(
    prefix="/ai",
    tags=["ki-assistent"],
    dependencies=[Depends(require_ai_tenant_enabled)],
)


def _tip_schema(tip: AiTipCard) -> TipCardSchema:
    return TipCardSchema(
        key=tip.key,
        context_type=tip.context_type,
        context_key=tip.context_key,
        tip_type=tip.tip_type,
        priority=tip.priority,
        title=tip.title,
        body=tip.body,
        action_url=tip.action_url,
        sources=[SourceRefSchema(**s.model_dump()) for s in tip.sources],
        language=tip.language,
        language_mismatch_warning=tip.language_mismatch_warning,
        uses_tenant_data=tip.uses_tenant_data,
        confidence=tip.confidence,
        model_name=tip.model_name,
        generated_at=tip.generated_at,
    )


def _response_schema(response: AiResponse) -> AiResponseSchema:
    return AiResponseSchema(
        answer_text=response.answer_text,
        sources=[SourceRefSchema(**s.model_dump()) for s in response.sources],
        language=response.language,
        language_mismatch_warning=response.language_mismatch_warning,
        uses_tenant_data=response.uses_tenant_data,
        uses_cloud_provider=response.uses_cloud_provider,
        confidence=response.confidence,
        fallback_species=response.fallback_species,
        cultivar_hint=response.cultivar_hint,
        model_name=response.model_name,
        provider_type=response.provider_type,
        kb_version=response.kb_version,
        generated_at=response.generated_at,
    )


# ── Tips ────────────────────────────────────────────────────────────


@router.get("/tips", response_model=TipListResponse)
def get_tips(
    context_type: str = Query(...),
    context_key: str = Query(...),
    language: str = Query("de"),
    ctx: TenantContext = Depends(get_current_tenant),
    service: AiAssistantService = Depends(get_ai_assistant_service),
) -> TipListResponse:
    """Context tip cards (cache-first). Consent ``ai_tenant_data_access``."""
    tips = service.get_tips(ctx, context_type=context_type, context_key=context_key, language=language)
    return TipListResponse(tips=[_tip_schema(t) for t in tips])


@router.post("/tips/refresh", response_model=TipListResponse)
def refresh_tips(
    context_type: str = Query(...),
    context_key: str = Query(...),
    language: str = Query("de"),
    ctx: TenantContext = Depends(get_current_tenant),
    service: AiAssistantService = Depends(get_ai_assistant_service),
) -> TipListResponse:
    """Force-regenerate tips for a context. Consent ``ai_tenant_data_access``."""
    tips = service.get_tips(ctx, context_type=context_type, context_key=context_key, language=language, force=True)
    return TipListResponse(tips=[_tip_schema(t) for t in tips])


@router.post("/tips/{tip_key}/dismiss", status_code=204)
def dismiss_tip(
    tip_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: AiAssistantService = Depends(get_ai_assistant_service),
) -> None:
    service.dismiss_tip(ctx, tip_key)


@router.post("/tips/{tip_key}/acted-on", status_code=204)
def acted_on_tip(
    tip_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: AiAssistantService = Depends(get_ai_assistant_service),
) -> None:
    service.mark_tip_acted_on(ctx, tip_key)


# ── Daily tip ───────────────────────────────────────────────────────


@router.get("/daily-tip", response_model=TipCardSchema | None)
def get_daily_tip(
    language: str = Query("de"),
    ctx: TenantContext = Depends(get_current_tenant),
    service: AiAssistantService = Depends(get_ai_assistant_service),
) -> TipCardSchema | None:
    """A single personalised daily tip. Consent ``ai_tenant_data_access``."""
    tip = service.get_daily_tip(ctx, language=language)
    return _tip_schema(tip) if tip else None


@router.post("/daily-tip/dismiss", status_code=204)
def dismiss_daily_tip(
    ctx: TenantContext = Depends(get_current_tenant),
    service: AiAssistantService = Depends(get_ai_assistant_service),
) -> None:
    service.dismiss_daily_tip(ctx)


# ── Explain ─────────────────────────────────────────────────────────


@router.post("/explain", response_model=AiResponseSchema)
def explain(
    body: ExplainRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: AiAssistantService = Depends(get_ai_assistant_service),
) -> AiResponseSchema:
    """ "Why?" answer for a concrete recommendation. Consent ``ai_tenant_data_access``."""
    response = service.explain(
        ctx,
        subject_type=body.subject_type,
        subject_key=body.subject_key,
        question_template_id=body.question_template_id,
        language=body.language or "de",
    )
    return _response_schema(response)


# ── Chat (SSE) ──────────────────────────────────────────────────────


@router.get("/conversations", response_model=list[ConversationSummary])
def list_conversations(
    ctx: TenantContext = Depends(get_current_tenant),
    service: AiAssistantService = Depends(get_ai_assistant_service),
) -> list[ConversationSummary]:
    return [
        ConversationSummary(
            key=c.key,
            title=c.title,
            context_type=c.context_type,
            context_key=c.context_key,
            message_count=c.message_count,
            updated_at=c.updated_at,
        )
        for c in service.list_conversations(ctx)
    ]


@router.post("/conversations", response_model=ConversationSummary)
def create_conversation(
    body: ConversationCreateRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: AiAssistantService = Depends(get_ai_assistant_service),
) -> ConversationSummary:
    conv = service.create_conversation(
        ctx,
        context_type=body.context_type,
        context_key=body.context_key,
        language=body.language or "de",
    )
    return ConversationSummary(
        key=conv.key,
        title=conv.title,
        context_type=conv.context_type,
        context_key=conv.context_key,
        message_count=conv.message_count,
        updated_at=conv.updated_at,
    )


@router.post("/conversations/{conversation_key}/messages")
async def send_message(
    conversation_key: str,
    body: ChatMessageRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: AiAssistantService = Depends(get_ai_assistant_service),
) -> StreamingResponse:
    """Send a chat message; the answer streams back as SSE (§5.4)."""
    generator = service.stream_chat(
        ctx,
        conversation_key=conversation_key,
        message=body.message,
        language=body.language or "de",
    )
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.delete("/conversations/{conversation_key}", status_code=204)
def delete_conversation(
    conversation_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: AiAssistantService = Depends(get_ai_assistant_service),
) -> None:
    """DSGVO Art. 17 — delete a conversation immediately (§7.5)."""
    service.delete_conversation(ctx, conversation_key)


# ── Providers ───────────────────────────────────────────────────────


@router.get("/providers", response_model=list[ProviderSummary])
def list_providers(
    ctx: TenantContext = Depends(get_current_tenant),
    service: AiAssistantService = Depends(get_ai_assistant_service),
) -> list[ProviderSummary]:
    return [
        ProviderSummary(
            key=p.key,
            provider_type=p.provider_type,
            display_name=p.display_name,
            model_name=p.model_name,
            requires_consent=p.requires_consent,
            is_default=p.is_default,
            is_system=p.tenant_key is None,
        )
        for p in service.list_providers(ctx)
    ]
