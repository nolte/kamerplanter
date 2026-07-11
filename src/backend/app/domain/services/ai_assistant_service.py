"""REQ-031 §4.3 — ``AiAssistantService`` (KI orchestration).

Central service the KI endpoints call. Per request it runs the toggle/consent
guards, builds the PII-free context, talks to the Knowledge Service through the
async adapter, persists tip cache / conversations, and writes a hashed audit
entry. Knowledge-Service outages degrade to the rule-based fallback (W-011) and
still return HTTP 200.
"""

from __future__ import annotations

import time
from collections.abc import AsyncIterator, Callable
from datetime import UTC, datetime, timedelta

import structlog

from app.data_access.arango.ai_repository import (
    ArangoAiConversationRepository,
    ArangoAiProviderRepository,
    ArangoAiTipCacheRepository,
)
from app.data_access.external.knowledge_service_adapter import KnowledgeServiceUnavailableError
from app.domain.engines.ai_explain_engine import ExplainEngine
from app.domain.engines.ai_tip_engine import TipEngine
from app.domain.guards.consent_guard import AI_TENANT_DATA_ACCESS, ConsentGuard
from app.domain.interfaces.knowledge_service import (
    ConfidenceLevel,
    IKnowledgeService,
    QuestionContext,
)
from app.domain.models.ai_assistant import (
    AiConversation,
    AiResponse,
    AiTipCard,
    ConversationMessage,
    SourceReference,
)
from app.domain.models.tenant_context import TenantContext
from app.domain.services.ai_audit_logger import AiAuditLogger

logger = structlog.get_logger(__name__)

#: How long a generated tip card stays valid in the ArangoDB cache.
_TIP_TTL = timedelta(hours=24)
#: Conversation retention (§7.4).
_CONVERSATION_TTL = timedelta(days=90)

#: Context resolver signature: (tenant_key, context_type, context_key) -> context.
ContextResolver = Callable[[str, str, str], QuestionContext]


class AiAssistantService:
    """Orchestrates KI tips, daily tip, explain, chat and provider reads."""

    def __init__(
        self,
        *,
        knowledge_adapter: IKnowledgeService,
        consent_guard: ConsentGuard,
        audit_logger: AiAuditLogger,
        tip_cache_repo: ArangoAiTipCacheRepository,
        conversation_repo: ArangoAiConversationRepository,
        provider_repo: ArangoAiProviderRepository,
        context_resolver: ContextResolver | None = None,
        tip_engine: TipEngine | None = None,
        explain_engine: ExplainEngine | None = None,
    ) -> None:
        self._ks = knowledge_adapter
        self._consent = consent_guard
        self._audit = audit_logger
        self._tip_cache = tip_cache_repo
        self._conversations = conversation_repo
        self._providers = provider_repo
        self._resolve_context = context_resolver or (lambda _t, _ct, _ck: QuestionContext())
        self._tips = tip_engine or TipEngine()
        self._explain = explain_engine or ExplainEngine()

    # ── Provider helpers ───────────────────────────────────────────────

    def _provider_flags(self, tenant_key: str, provider_key: str | None) -> tuple[str, str, bool]:
        """Resolve ``(provider_key, provider_type, uses_cloud)`` for a tenant.

        Defaults to a local Ollama profile when no provider is configured, so a
        fresh tenant never accidentally counts as cloud processing.
        """
        provider = self._providers.get_default(tenant_key, provider_key)
        if provider is None:
            return ("", "ollama", False)
        uses_cloud = provider.provider_type != "ollama"
        return (provider.key or "", provider.provider_type, uses_cloud)

    # ── Tips ───────────────────────────────────────────────────────────

    def get_tips(
        self,
        ctx: TenantContext,
        *,
        context_type: str,
        context_key: str,
        language: str = "de",
        force: bool = False,
    ) -> list[AiTipCard]:
        """Return tip cards for a plant/run context (cache-first, §4.4).

        Requires ``ai_tenant_data_access``. On a Knowledge-Service outage returns
        rule-based fallback tips (HTTP 200) and audits ``knowledge_service_error``.
        """
        self._consent.require_consent(ctx.user_key, AI_TENANT_DATA_ACCESS)

        if force:
            self._tip_cache.invalidate_context(ctx.tenant_key, context_type, context_key)
        else:
            cached = self._tip_cache.find_valid(ctx.tenant_key, context_type, context_key)
            if cached:
                return cached

        question_context = self._resolve_context(ctx.tenant_key, context_type, context_key)
        question = self._tips.build_question(question_context, language)
        provider_key, provider_type, uses_cloud = self._provider_flags(ctx.tenant_key, None)
        started = time.monotonic()

        try:
            result = self._run_ask(question, question_context, language)
        except KnowledgeServiceUnavailableError:
            fallback = self._tips.rule_based_fallback(
                tenant_key=ctx.tenant_key,
                context_type=context_type,
                context_key=context_key,
                context=question_context,
                language=language,
            )
            self._audit.record(
                tenant_key=ctx.tenant_key,
                user_key=ctx.user_key,
                endpoint="tips",
                question=question,
                answer_length=sum(len(t.body) for t in fallback),
                context_type=context_type,
                context_key=context_key,
                provider_type=provider_type,
                uses_tenant_data=True,
                uses_cloud_provider=uses_cloud,
                latency_ms=int((time.monotonic() - started) * 1000),
                status="knowledge_service_error",
                error_class="knowledge_service_unavailable",
            )
            return fallback

        card = AiTipCard(
            tenant_key=ctx.tenant_key,
            context_type=context_type,  # type: ignore[arg-type]
            context_key=context_key,
            tip_type="care",
            priority="medium",
            title=self._first_line(result.answer),
            body=result.answer,
            sources=self._tips.to_sources(result.sources),
            language=language,  # type: ignore[arg-type]
            uses_tenant_data=True,
            confidence=question_context.confidence,
            provider_key=provider_key,
            model_name=result.model_name,
            generated_at=datetime.now(UTC),
            valid_until=datetime.now(UTC) + _TIP_TTL,
        )
        persisted = self._tip_cache.create(card)
        self._audit.record(
            tenant_key=ctx.tenant_key,
            user_key=ctx.user_key,
            endpoint="tips",
            question=question,
            answer_length=len(result.answer),
            context_type=context_type,
            context_key=context_key,
            model_name=result.model_name,
            provider_type=provider_type,
            uses_tenant_data=True,
            uses_cloud_provider=uses_cloud,
            latency_ms=int((time.monotonic() - started) * 1000),
            status="ok",
        )
        return [persisted]

    def get_daily_tip(self, ctx: TenantContext, *, language: str = "de") -> AiTipCard | None:
        """Return a single daily tip for the dashboard (cache until midnight)."""
        self._consent.require_consent(ctx.user_key, AI_TENANT_DATA_ACCESS)
        today = datetime.now(UTC).date().isoformat()
        cached = self._tip_cache.find_valid(ctx.tenant_key, "daily", today)
        if cached:
            return cached[0]

        question_context = self._resolve_context(ctx.tenant_key, "daily", today)
        question = self._tips.build_question(question_context, language)
        provider_key, provider_type, uses_cloud = self._provider_flags(ctx.tenant_key, None)
        started = time.monotonic()
        try:
            result = self._run_ask(question, question_context, language)
        except KnowledgeServiceUnavailableError:
            self._audit.record(
                tenant_key=ctx.tenant_key,
                user_key=ctx.user_key,
                endpoint="daily-tip",
                question=question,
                answer_length=0,
                provider_type=provider_type,
                uses_tenant_data=True,
                uses_cloud_provider=uses_cloud,
                latency_ms=int((time.monotonic() - started) * 1000),
                status="knowledge_service_error",
                error_class="knowledge_service_unavailable",
            )
            return None

        midnight = datetime.combine(datetime.now(UTC).date() + timedelta(days=1), datetime.min.time(), tzinfo=UTC)
        card = AiTipCard(
            tenant_key=ctx.tenant_key,
            context_type="daily",
            context_key=today,
            tip_type="optimization",
            priority="low",
            title=self._first_line(result.answer),
            body=result.answer,
            sources=self._tips.to_sources(result.sources),
            language=language,  # type: ignore[arg-type]
            uses_tenant_data=True,
            confidence=question_context.confidence,
            provider_key=provider_key,
            model_name=result.model_name,
            generated_at=datetime.now(UTC),
            valid_until=midnight,
        )
        persisted = self._tip_cache.create(card)
        self._audit.record(
            tenant_key=ctx.tenant_key,
            user_key=ctx.user_key,
            endpoint="daily-tip",
            question=question,
            answer_length=len(result.answer),
            model_name=result.model_name,
            provider_type=provider_type,
            uses_tenant_data=True,
            uses_cloud_provider=uses_cloud,
            latency_ms=int((time.monotonic() - started) * 1000),
            status="ok",
        )
        return persisted

    def dismiss_tip(self, ctx: TenantContext, tip_key: str) -> None:
        """Mark a tip as dismissed (tenant-scoped)."""
        tip = self._tip_cache.get_by_key(tip_key)
        if tip is None or tip.tenant_key != ctx.tenant_key:
            return
        tip.dismissed_at = datetime.now(UTC)
        tip.dismissed_by = ctx.user_key
        self._tip_cache.update(tip_key, tip)

    def dismiss_daily_tip(self, ctx: TenantContext) -> None:
        """Dismiss today's daily tip for the tenant (persists for the rest of day)."""
        today = datetime.now(UTC).date().isoformat()
        for tip in self._tip_cache.find_valid(ctx.tenant_key, "daily", today):
            if tip.key:
                self.dismiss_tip(ctx, tip.key)

    def mark_tip_acted_on(self, ctx: TenantContext, tip_key: str) -> None:
        """Mark a tip as acted on (tenant-scoped)."""
        tip = self._tip_cache.get_by_key(tip_key)
        if tip is None or tip.tenant_key != ctx.tenant_key:
            return
        tip.acted_on_at = datetime.now(UTC)
        self._tip_cache.update(tip_key, tip)

    # ── Explain ────────────────────────────────────────────────────────

    def explain(
        self,
        ctx: TenantContext,
        *,
        subject_type: str,
        subject_key: str,
        question_template_id: str,
        slots: dict | None = None,
        language: str = "de",
    ) -> AiResponse:
        """Generate a "why?" answer for a concrete recommendation (§4.5)."""
        self._consent.require_consent(ctx.user_key, AI_TENANT_DATA_ACCESS)
        question = self._explain.build_question(question_template_id, language, slots or {})
        if question is None:
            # Unknown template — deterministic message, no KS call.
            return AiResponse(
                answer_text=(
                    "No explanation template is available for this recommendation."
                    if language == "en"
                    else "Fuer diese Empfehlung ist keine Erklaerungsvorlage hinterlegt."
                ),
                language=language,  # type: ignore[arg-type]
                uses_tenant_data=True,
                confidence=ConfidenceLevel.NONE,
                generated_at=datetime.now(UTC),
            )

        question_context = self._resolve_context(ctx.tenant_key, subject_type, subject_key)
        provider_key, provider_type, uses_cloud = self._provider_flags(ctx.tenant_key, None)
        started = time.monotonic()
        try:
            result = self._run_ask(question, question_context, language)
        except KnowledgeServiceUnavailableError:
            self._audit.record(
                tenant_key=ctx.tenant_key,
                user_key=ctx.user_key,
                endpoint="explain",
                question=question,
                answer_length=0,
                context_type=subject_type,
                context_key=subject_key,
                provider_type=provider_type,
                uses_tenant_data=True,
                uses_cloud_provider=uses_cloud,
                latency_ms=int((time.monotonic() - started) * 1000),
                status="knowledge_service_error",
                error_class="knowledge_service_unavailable",
            )
            return AiResponse(
                answer_text=(
                    "The knowledge assistant is temporarily unavailable. Please try again shortly."
                    if language == "en"
                    else "Der Wissensassistent ist gerade nicht erreichbar. Bitte versuche es gleich erneut."
                ),
                language=language,  # type: ignore[arg-type]
                uses_tenant_data=True,
                confidence=ConfidenceLevel.NONE,
                generated_at=datetime.now(UTC),
            )

        self._audit.record(
            tenant_key=ctx.tenant_key,
            user_key=ctx.user_key,
            endpoint="explain",
            question=question,
            answer_length=len(result.answer),
            context_type=subject_type,
            context_key=subject_key,
            model_name=result.model_name,
            provider_type=provider_type,
            uses_tenant_data=True,
            uses_cloud_provider=uses_cloud,
            latency_ms=int((time.monotonic() - started) * 1000),
            status="ok",
        )
        return self._to_response(
            result,
            language=language,
            uses_tenant_data=True,
            uses_cloud_provider=uses_cloud,
            confidence=question_context.confidence,
            provider_type=provider_type,
        )

    # ── Public / Light-mode ask ─────────────────────────────────────────

    async def ask_public(self, question: str, *, language: str = "de") -> AiResponse:
        """Light-mode knowledge answer — strictly ``context=null`` (§5.3).

        No tenant context, no consent, no user. The audit entry uses the shared
        ``public`` tenant marker and ``user_key=null``.
        """
        started = time.monotonic()
        try:
            result = await self._ks.ask(
                question,
                context=None,
                doc_language="all",
                prompt_language=language,
            )
        except KnowledgeServiceUnavailableError:
            self._audit.record(
                tenant_key="public",
                user_key=None,
                endpoint="public.ask",
                question=question,
                answer_length=0,
                uses_tenant_data=False,
                latency_ms=int((time.monotonic() - started) * 1000),
                status="knowledge_service_error",
                error_class="knowledge_service_unavailable",
            )
            return AiResponse(
                answer_text=(
                    "The knowledge assistant is temporarily unavailable."
                    if language == "en"
                    else "Der Wissensassistent ist gerade nicht erreichbar."
                ),
                language=language,  # type: ignore[arg-type]
                uses_tenant_data=False,
                confidence=ConfidenceLevel.NONE,
                generated_at=datetime.now(UTC),
            )

        self._audit.record(
            tenant_key="public",
            user_key=None,
            endpoint="public.ask",
            question=question,
            answer_length=len(result.answer),
            model_name=result.model_name,
            provider_type=result.provider_type or "ollama",
            uses_tenant_data=False,
            latency_ms=int((time.monotonic() - started) * 1000),
            status="ok",
        )
        return self._to_response(
            result,
            language=language,
            uses_tenant_data=False,
            uses_cloud_provider=False,
            confidence=ConfidenceLevel.HIGH,
            provider_type=result.provider_type or "ollama",
        )

    async def health_check(self) -> bool:
        """Proxy the Knowledge-Service readiness (circuit-breaker aware)."""
        return await self._ks.health_check()

    # ── Conversations / Chat (SSE) ──────────────────────────────────────

    def list_conversations(self, ctx: TenantContext) -> list[AiConversation]:
        return self._conversations.list_for_user(ctx.tenant_key, ctx.user_key)

    def get_conversation(self, ctx: TenantContext, key: str) -> AiConversation | None:
        conv = self._conversations.get_by_key(key)
        if conv is None or conv.tenant_key != ctx.tenant_key:
            return None
        return conv

    def create_conversation(
        self,
        ctx: TenantContext,
        *,
        context_type: str = "general",
        context_key: str | None = None,
        language: str = "de",
    ) -> AiConversation:
        self._consent.require_consent(ctx.user_key, AI_TENANT_DATA_ACCESS)
        now = datetime.now(UTC)
        conv = AiConversation(
            tenant_key=ctx.tenant_key,
            user_key=ctx.user_key,
            context_type=context_type,  # type: ignore[arg-type]
            context_key=context_key,
            language=language,  # type: ignore[arg-type]
            expires_at=now + _CONVERSATION_TTL,
        )
        return self._conversations.create(conv)

    def delete_conversation(self, ctx: TenantContext, key: str) -> bool:
        """DSGVO Art. 17 — hard-delete a tenant-owned conversation (§7.5)."""
        conv = self._conversations.get_by_key(key)
        if conv is None or conv.tenant_key != ctx.tenant_key:
            return False
        return self._conversations.delete(key)

    async def stream_chat(
        self,
        ctx: TenantContext,
        *,
        conversation_key: str,
        message: str,
        language: str = "de",
    ) -> AsyncIterator[str]:
        """Yield the assistant answer token-wise as SSE ``data:`` frames (§5.4).

        The Knowledge Service answers in one shot; the backend streams the answer
        word-by-word so the client renders progressively. A trailing ``event:
        done`` frame carries the metadata for the ``<AIResponse>`` envelope.
        """
        self._consent.require_consent(ctx.user_key, AI_TENANT_DATA_ACCESS)
        conv = self.get_conversation(ctx, conversation_key)
        if conv is None:
            yield _sse_event("error", '{"detail":"conversation_not_found"}')
            return

        question_context = self._resolve_context(ctx.tenant_key, conv.context_type, conv.context_key or "")
        provider_key, provider_type, uses_cloud = self._provider_flags(ctx.tenant_key, conv.provider_key or None)
        started = time.monotonic()
        try:
            result = await self._ks.ask(
                message,
                context=question_context,
                doc_language="all",
                prompt_language=language,
            )
        except KnowledgeServiceUnavailableError:
            self._audit.record(
                tenant_key=ctx.tenant_key,
                user_key=ctx.user_key,
                endpoint="chat",
                question=message,
                answer_length=0,
                context_type=conv.context_type,
                context_key=conv.context_key,
                provider_type=provider_type,
                uses_tenant_data=True,
                uses_cloud_provider=uses_cloud,
                latency_ms=int((time.monotonic() - started) * 1000),
                status="knowledge_service_error",
                error_class="knowledge_service_unavailable",
            )
            yield _sse_event("error", '{"detail":"knowledge_service_error"}')
            return

        for token in result.answer.split(" "):
            yield _sse_event("token", token + " ")

        sources = [
            SourceReference(
                source_key=c.source_key,
                source_type=c.source_type,
                title=c.title,
                score=c.score,
                language=c.language,
            )
            for c in result.sources
        ]
        self._persist_turn(conv, message, result.answer, sources, result.model_name, provider_key)
        self._audit.record(
            tenant_key=ctx.tenant_key,
            user_key=ctx.user_key,
            endpoint="chat",
            question=message,
            answer_length=len(result.answer),
            context_type=conv.context_type,
            context_key=conv.context_key,
            model_name=result.model_name,
            provider_type=provider_type,
            uses_tenant_data=True,
            uses_cloud_provider=uses_cloud,
            latency_ms=int((time.monotonic() - started) * 1000),
            status="ok",
        )
        response = self._to_response(
            result,
            language=language,
            uses_tenant_data=True,
            uses_cloud_provider=uses_cloud,
            confidence=question_context.confidence,
            provider_type=provider_type,
        )
        yield _sse_event("done", response.model_dump_json())

    def _persist_turn(
        self,
        conv: AiConversation,
        message: str,
        answer: str,
        sources: list[SourceReference],
        model_name: str,
        provider_key: str,
    ) -> None:
        now = datetime.now(UTC)
        conv.messages.append(ConversationMessage(role="user", content=message, timestamp=now))
        conv.messages.append(
            ConversationMessage(role="assistant", content=answer, timestamp=now, source_chunks=sources)
        )
        conv.message_count = len(conv.messages)
        conv.model_name = model_name
        conv.provider_key = provider_key
        if conv.key:
            self._conversations.update(conv.key, conv)

    # ── Providers ──────────────────────────────────────────────────────

    def list_providers(self, ctx: TenantContext):
        """List tenant + system providers (API keys never serialised)."""
        return self._providers.list_for_tenant(ctx.tenant_key)

    # ── Internals ──────────────────────────────────────────────────────

    def _run_ask(self, question: str, context: QuestionContext, language: str):
        """Sync bridge to the async KS adapter for the non-streaming endpoints.

        Only a context with actual master values is forwarded; an empty context
        is sent as ``None`` so the KS treats it as a pure knowledge question.
        """
        ks_context = context if (context.species or context.phase) else None
        return _run_sync(
            self._ks.ask(
                question,
                context=ks_context,
                doc_language="all",
                prompt_language=language,
            )
        )

    def _to_response(
        self,
        result,
        *,
        language: str,
        uses_tenant_data: bool,
        uses_cloud_provider: bool,
        confidence: ConfidenceLevel,
        provider_type: str,
    ) -> AiResponse:
        return AiResponse(
            answer_text=result.answer,
            sources=[
                SourceReference(
                    source_key=c.source_key,
                    source_type=c.source_type,
                    title=c.title,
                    score=c.score,
                    language=c.language,
                )
                for c in result.sources
            ],
            language=language,  # type: ignore[arg-type]
            uses_tenant_data=uses_tenant_data,
            uses_cloud_provider=uses_cloud_provider,
            confidence=confidence,
            model_name=result.model_name,
            provider_type=provider_type,
            kb_version=result.kb_version,
            generated_at=datetime.now(UTC),
        )

    @staticmethod
    def _first_line(text: str, *, limit: int = 80) -> str:
        """Derive a compact title from the first sentence/line of an answer."""
        first = text.strip().split("\n", 1)[0]
        if len(first) > limit:
            first = first[: limit - 1].rstrip() + "…"
        return first or "Tipp"


def _sse_event(event: str, data: str) -> str:
    """Format a single Server-Sent-Event frame."""
    return f"event: {event}\ndata: {data}\n\n"


def _run_sync(coro):
    """Run an async coroutine to completion from a sync context.

    The non-streaming endpoints (``/tips``, ``/daily-tip``, ``/explain``) are
    declared as sync FastAPI handlers (they run in a threadpool), so bridging the
    async KS adapter here keeps the service API sync while reusing one adapter.

    Uses a dedicated event loop and restores the thread's previous loop
    afterwards, rather than :func:`asyncio.run` (which resets the loop to
    ``None`` and would leak across a shared-thread test session).
    """
    import asyncio

    try:
        previous_loop = asyncio.get_event_loop_policy().get_event_loop()
    except RuntimeError:
        previous_loop = None

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
        if previous_loop is not None:
            asyncio.set_event_loop(previous_loop)
