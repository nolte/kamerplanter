"""REQ-031 §5.1 — tenant-scoped KI-Assistent endpoints (``/ai/*``).

Mounted under ``/api/v1/t/{tenant_slug}/ai``. Every route runs the three-stage
toggle: stage 1 (operator flag → 404) and stage 2 (tenant setting → 403) via the
router-level ``require_ai_tenant_enabled`` dependency; stage 3 (consent → 403) is
enforced inside the service per endpoint class (§1.3).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
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
from app.common.auth import get_current_tenant, meets_tenant_role, require_tenant_role
from app.common.dependencies import get_ai_assistant_service
from app.common.enums import TenantRole
from app.common.openapi_responses import NOT_FOUND_RESPONSE
from app.domain.models.ai_assistant import AiResponse, AiTenantSettings, AiTipCard
from app.domain.models.tenant_context import TenantContext
from app.domain.services.ai_assistant_service import AiAssistantService

router = APIRouter(
    prefix="/ai",
    tags=["ai-assistant"],
    dependencies=[Depends(require_ai_tenant_enabled)],
    responses=NOT_FOUND_RESPONSE,
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


def _may_refresh(ctx: TenantContext) -> bool:
    """Whether ``ctx`` passes the gate on the regeneration routes below.

    Rank is the only axis left to report, and the precondition is what makes that
    true: this is only ever evaluated inside a handler of **this router**, whose
    `dependencies=[Depends(require_ai_tenant_enabled)]` has already answered both
    other stages of the REQ-031 §1.3 toggle — 404 when the operator flag is off,
    403 when the tenant has KI disabled. A caller who would fail either of them
    never receives a body to read this flag out of. The consent stage is symmetric
    for the same reason: `get_tips` requires `ai_tenant_data_access` itself, so a
    caller without it gets a 403 on the read rather than a flag they cannot use.

    Measured, not assumed — `tests/api/test_ai_tip_reads_are_gated.py` drives all
    three refusals against the mounted router, because the dependency this leans
    on is declared on the router and an edit to the handler signature would not
    show it moving.

    What remains is `require_tenant_role(GROWER)`, read out of the same predicate
    the gate decides on rather than restated, so the flag on the response and the
    gate on the ``POST`` cannot disagree.
    """
    return meets_tenant_role(ctx.role, TenantRole.GROWER)


@router.get("/tips", response_model=TipListResponse)
def get_tips(
    context_type: str = Query(..., description="Context entity type the tips relate to (e.g. plant, location)."),
    context_key: str = Query(..., description="Document key of the context entity."),
    ctx: TenantContext = Depends(get_current_tenant),
    service: AiAssistantService = Depends(get_ai_assistant_service),
) -> TipListResponse:
    """Stored context tip cards. Consent ``ai_tenant_data_access``.

    A **read**: it never generates and never writes (#1461). An empty ``tips``
    with ``refresh_available: true`` is the answer for "nothing generated yet,
    and you may ask for it" — the regeneration is ``POST /ai/tips/refresh``.
    """
    tips = service.get_tips(ctx, context_type=context_type, context_key=context_key)
    return TipListResponse(tips=[_tip_schema(t) for t in tips], refresh_available=_may_refresh(ctx))


@router.post("/tips/refresh", response_model=TipListResponse)
def refresh_tips(
    context_type: str = Query(..., description="Context entity type the tips relate to (e.g. plant, location)."),
    context_key: str = Query(..., description="Document key of the context entity."),
    language: str = Query("de", description="Preferred answer language (ISO 639-1)."),
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    ai_settings: AiTenantSettings = Depends(require_ai_tenant_enabled),
    service: AiAssistantService = Depends(get_ai_assistant_service),
) -> TipListResponse:
    """Generate tips for a context. Consent ``ai_tenant_data_access``."""
    tips = service.refresh_tips(
        ctx,
        context_type=context_type,
        context_key=context_key,
        language=language,
        allow_cloud=ai_settings.ai_allow_cloud_providers,
    )
    return TipListResponse(tips=[_tip_schema(t) for t in tips], refresh_available=True)


@router.post("/tips/{tip_key}/dismiss", status_code=204)
def dismiss_tip(
    tip_key: Annotated[str, Path(description="Document key of the tip card.")],
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: AiAssistantService = Depends(get_ai_assistant_service),
) -> None:
    """Dismiss a tip card so it is no longer shown."""
    service.dismiss_tip(ctx, tip_key)


@router.post("/tips/{tip_key}/acted-on", status_code=204)
def acted_on_tip(
    tip_key: Annotated[str, Path(description="Document key of the tip card.")],
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: AiAssistantService = Depends(get_ai_assistant_service),
) -> None:
    """Mark a tip card as acted on."""
    service.mark_tip_acted_on(ctx, tip_key)


# ── Daily tip ───────────────────────────────────────────────────────


@router.get("/daily-tip", response_model=TipCardSchema | None)
def get_daily_tip(
    ctx: TenantContext = Depends(get_current_tenant),
    service: AiAssistantService = Depends(get_ai_assistant_service),
) -> TipCardSchema | None:
    """Today's stored daily tip, or ``null``. Consent ``ai_tenant_data_access``.

    A **read**: it never generates and never writes (#1461). ``null`` means
    nothing has been generated for today; ``POST /ai/daily-tip/refresh`` is what
    generates it.
    """
    tip = service.get_daily_tip(ctx)
    return _tip_schema(tip) if tip else None


@router.post("/daily-tip/refresh", response_model=TipCardSchema | None)
def refresh_daily_tip(
    language: str = Query("de", description="Preferred answer language (ISO 639-1)."),
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    ai_settings: AiTenantSettings = Depends(require_ai_tenant_enabled),
    service: AiAssistantService = Depends(get_ai_assistant_service),
) -> TipCardSchema | None:
    """Generate today's daily tip. Consent ``ai_tenant_data_access``.

    Idempotent for the day: an already-generated card is returned rather than
    regenerated, so a second click is not a second LLM call.
    """
    tip = service.refresh_daily_tip(ctx, language=language, allow_cloud=ai_settings.ai_allow_cloud_providers)
    return _tip_schema(tip) if tip else None


@router.post("/daily-tip/dismiss", status_code=204)
def dismiss_daily_tip(
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: AiAssistantService = Depends(get_ai_assistant_service),
) -> None:
    """Dismiss today's personalised daily tip."""
    service.dismiss_daily_tip(ctx)


# ── Explain ─────────────────────────────────────────────────────────


@router.post("/explain", response_model=AiResponseSchema)
def explain(
    body: ExplainRequest,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    ai_settings: AiTenantSettings = Depends(require_ai_tenant_enabled),
    service: AiAssistantService = Depends(get_ai_assistant_service),
) -> AiResponseSchema:
    """ "Why?" answer for a concrete recommendation. Consent ``ai_tenant_data_access``."""
    response = service.explain(
        ctx,
        subject_type=body.subject_type,
        subject_key=body.subject_key,
        question_template_id=body.question_template_id,
        language=body.language or "de",
        allow_cloud=ai_settings.ai_allow_cloud_providers,
    )
    return _response_schema(response)


# ── Chat (SSE) ──────────────────────────────────────────────────────


@router.get("/conversations", response_model=list[ConversationSummary])
def list_conversations(
    ctx: TenantContext = Depends(get_current_tenant),
    service: AiAssistantService = Depends(get_ai_assistant_service),
) -> list[ConversationSummary]:
    """List the current user's KI-Assistent conversations."""
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
    """Start a new KI-Assistent conversation."""
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
    conversation_key: Annotated[str, Path(description="Document key of the conversation.")],
    body: ChatMessageRequest,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    ai_settings: AiTenantSettings = Depends(require_ai_tenant_enabled),
    service: AiAssistantService = Depends(get_ai_assistant_service),
) -> StreamingResponse:
    """Send a chat message; the answer streams back as SSE (§5.4)."""
    generator = service.stream_chat(
        ctx,
        conversation_key=conversation_key,
        message=body.message,
        language=body.language or "de",
        allow_cloud=ai_settings.ai_allow_cloud_providers,
    )
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.delete("/conversations/{conversation_key}", status_code=204)
def delete_conversation(
    conversation_key: Annotated[str, Path(description="Document key of the conversation.")],
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
    """List the AI providers available to this tenant."""
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
