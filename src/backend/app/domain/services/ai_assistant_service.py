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
from typing import Any, get_args

import structlog

from app.common.exceptions import AiDisabledError, ExternalSourceError, NotFoundError, ValidationError
from app.data_access.arango.ai_repository import (
    ArangoAiConversationRepository,
    ArangoAiProviderRepository,
    ArangoAiTipCacheRepository,
)
from app.data_access.external.knowledge_service_adapter import KnowledgeServiceUnavailableError
from app.domain.engines.ai_explain_engine import ExplainEngine
from app.domain.engines.ai_tip_engine import TipEngine
from app.domain.guards.consent_guard import (
    AI_CLOUD_PROCESSING,
    AI_KNOWLEDGE_QUESTION,
    AI_TENANT_DATA_ACCESS,
    ConsentGuard,
)
from app.domain.interfaces.knowledge_service import (
    ConfidenceLevel,
    IKnowledgeService,
    QuestionContext,
)
from app.domain.models.ai_assistant import (
    AiConversation,
    AiResponse,
    AiTipCard,
    ContextType,
    ConversationMessage,
    KnowledgeAnswer,
    SourceReference,
)
from app.domain.models.tenant_context import TenantContext
from app.domain.services.ai_audit_logger import AiAuditLogger
from app.domain.services.ai_call_budget import AiCallBudget

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
        call_budget: AiCallBudget,
        knowledge_adapter: IKnowledgeService,
        consent_guard: ConsentGuard,
        audit_logger: AiAuditLogger,
        tip_cache_repo: ArangoAiTipCacheRepository,
        conversation_repo: ArangoAiConversationRepository,
        provider_repo: ArangoAiProviderRepository,
        context_resolver: ContextResolver | None = None,
        tip_engine: TipEngine | None = None,
        explain_engine: ExplainEngine | None = None,
        plant_repo: Any | None = None,
        planting_run_repo: Any | None = None,
        task_lookup: Callable[[str], Any] | None = None,
        feeding_event_lookup: Callable[[str], Any] | None = None,
    ) -> None:
        # #1872 C9: a plant / run context key is resolved under the tenant before
        # anything stores it (tip cards, conversations, audit) or a resolver reads it.
        self._context_owners: dict[str, tuple[str, Callable[[str], Any] | None]] = {
            "plant_instance": ("PlantInstance", plant_repo.get_by_key if plant_repo is not None else None),
            "planting_run": ("PlantingRun", planting_run_repo.get_by_key if planting_run_repo is not None else None),
            # explain() subjects that name an entity (security review of #1872, S2).
            "task": ("Task", task_lookup),
            "feeding_event": ("FeedingEvent", feeding_event_lookup),
        }
        # #2110 (MT-013): required, not optional — a service built without it
        # would make every LLM call of this class unbounded again, silently.
        self._budget = call_budget
        self._ks = knowledge_adapter
        self._consent = consent_guard
        self._audit = audit_logger
        self._tip_cache = tip_cache_repo
        self._conversations = conversation_repo
        self._providers = provider_repo
        self._resolve_context = context_resolver or (lambda _t, _ct, _ck: QuestionContext())
        self._tips = tip_engine or TipEngine()
        self._explain = explain_engine or ExplainEngine()

    def _require_owned_context(self, tenant_key: str, context_type: str, context_key: str | None) -> None:
        """404 unless a plant / run context key belongs to *tenant_key* (#1872 C9).

        The key was stored on tip cards, conversations and the audit log as given,
        and handed to the context resolver. Inert while production wires no
        resolver — the check keeps it that way once one is wired. Other context
        types (``general``, ``daily``, ``term``, ``explain``) name no entity.
        Fails closed without the repository.
        """
        owner = self._context_owners.get(context_type)
        if owner is None or not context_key:
            return
        name, lookup = owner
        entity = lookup(context_key) if lookup is not None else None
        if entity is None or getattr(entity, "tenant_key", None) != tenant_key:
            raise NotFoundError(name, context_key)

    # ── Provider helpers ───────────────────────────────────────────────

    def _resolve_provider(
        self,
        ctx: TenantContext,
        provider_key: str | None,
        *,
        allow_cloud: bool,
    ) -> tuple[str, str, bool]:
        """Resolve ``(provider_key, provider_type, uses_cloud)`` and enforce the
        cloud gate BEFORE any LLM call (SEC-001).

        Two independent controls run here:

        * **Tenant flag** — when ``ai_allow_cloud_providers`` is off, a cloud
          default is downgraded fail-closed to a local Ollama provider. If the
          tenant has no local provider at all the KI feature is unavailable
          (:class:`AiDisabledError`), never silently a cloud call.
        * **User consent** — when a cloud provider is actually used the caller
          must hold the ``ai_cloud_processing`` consent, otherwise a 403
          (:class:`~app.common.exceptions.ConsentRequiredError`) is raised.

        Defaults to a local Ollama profile when no provider is configured, so a
        fresh tenant never accidentally counts as cloud processing.
        """
        provider = self._providers.get_default(ctx.tenant_key, provider_key)
        if provider is None:
            return ("", "ollama", False)

        uses_cloud = provider.provider_type != "ollama" or provider.requires_consent
        if uses_cloud and not allow_cloud:
            # Tenant admin has not enabled cloud processing → fail closed to a
            # local provider instead of leaking tenant data to a cloud LLM.
            local = self._local_provider(ctx.tenant_key)
            if local is None:
                raise AiDisabledError()
            provider = local
            uses_cloud = False

        if uses_cloud:
            self._consent.require_consent(ctx.user_key, AI_CLOUD_PROCESSING)

        return (provider.key or "", provider.provider_type, uses_cloud)

    def _platform_provider(self) -> tuple[str, bool]:
        """``(provider_type, uses_cloud)`` of the platform's system default provider.

        The label of an answer whose model the Knowledge Service picks itself —
        the same rule the glossary cache classifies by (REQ-035 §6, #2110):
        system rows only, ``ollama`` without ``requires_consent`` is local, and
        no system provider at all counts as local Ollama.
        """
        provider = self._providers.get_system_default()
        if provider is None:
            return ("ollama", False)
        return (provider.provider_type, bool(provider.provider_type != "ollama" or provider.requires_consent))

    def _charge(self, ctx: TenantContext) -> None:
        """Count one LLM call against the daily budgets, or refuse it (#2110).

        Called after every gate that can refuse for another reason (consent,
        context ownership, provider) and right before the call, so a request
        that would have been refused anyway does not use up the day.
        """
        self._budget.charge(tenant_key=ctx.tenant_key, user_key=ctx.user_key)

    def _local_provider(self, tenant_key: str):
        """Return the first local Ollama provider for a tenant, or ``None``."""
        for provider in self._providers.list_for_tenant(tenant_key):
            if provider.provider_type == "ollama" and not provider.requires_consent:
                return provider
        return None

    # ── Tips ───────────────────────────────────────────────────────────

    def get_tips(self, ctx: TenantContext, *, context_type: str, context_key: str) -> list[AiTipCard]:
        """Return the stored tip cards for a plant/run context — **read-only**.

        Requires ``ai_tenant_data_access``. An empty list is a legitimate answer:
        nothing has been generated for this context yet, or everything that was
        has expired or been dismissed.

        Generation used to happen right here, on a cache miss, which made
        ``GET /t/{slug}/ai/tips`` persist a tip card and an audit record while
        answering — entry 6 of the #1443 detector inventory, filed as #1461 — and
        made a read of a plant's detail page cost an LLM call. It lives in
        :meth:`refresh_tips` now, behind the ``POST`` that existed for it all
        along.
        """
        self._consent.require_consent(ctx.user_key, AI_TENANT_DATA_ACCESS)
        return self._tip_cache.find_valid(ctx.tenant_key, context_type, context_key)

    def refresh_tips(
        self,
        ctx: TenantContext,
        *,
        context_type: str,
        context_key: str,
        language: str = "de",
        allow_cloud: bool = False,
    ) -> list[AiTipCard]:
        """Generate and persist the tip cards for a context (§4.4) — the write path.

        Requires ``ai_tenant_data_access``. On a Knowledge-Service outage returns
        rule-based fallback tips (HTTP 200) and audits ``knowledge_service_error``.
        ``allow_cloud`` mirrors the tenant ``ai_allow_cloud_providers`` flag and
        gates cloud provider use (SEC-001).

        Always regenerates: this is what the caller asked for by choosing the
        ``POST``. The previous cache-first behaviour belonged to the read half,
        which is now :meth:`get_tips`.
        """
        self._consent.require_consent(ctx.user_key, AI_TENANT_DATA_ACCESS)
        # A tip card is stored under its context: only the known context types
        # (security review of #1872, S2) — an unknown one stored any key unchecked.
        if context_type not in get_args(ContextType):
            raise ValidationError(f"Unknown tip context type '{context_type}'.")
        self._require_owned_context(ctx.tenant_key, context_type, context_key)
        self._tip_cache.invalidate_context(ctx.tenant_key, context_type, context_key)

        question_context = self._resolve_context(ctx.tenant_key, context_type, context_key)
        question = self._tips.build_question(question_context, language)
        provider_key, provider_type, uses_cloud = self._resolve_provider(ctx, None, allow_cloud=allow_cloud)
        self._charge(ctx)
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
        self._budget.record_usage(tenant_key=ctx.tenant_key, usage=result.usage)
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
            usage=result.usage,
        )
        return [persisted]

    def get_daily_tip(self, ctx: TenantContext) -> AiTipCard | None:
        """Return today's stored daily tip, or ``None`` — **read-only**.

        ``None`` means nothing has been generated for today yet (or it was
        dismissed). Generation used to happen here on a miss, which made
        ``GET /t/{slug}/ai/daily-tip`` — a route the dashboard calls on every
        load — persist a tip card and an audit record and pay for an LLM call:
        entry 5 of the #1443 detector inventory, filed as #1461. It lives in
        :meth:`refresh_daily_tip` now.
        """
        self._consent.require_consent(ctx.user_key, AI_TENANT_DATA_ACCESS)
        today = datetime.now(UTC).date().isoformat()
        cached = self._tip_cache.find_valid(ctx.tenant_key, "daily", today)
        return cached[0] if cached else None

    def refresh_daily_tip(
        self, ctx: TenantContext, *, language: str = "de", allow_cloud: bool = False
    ) -> AiTipCard | None:
        """Generate and persist today's daily tip (§4.4) — the write path.

        Returns the stored card when there already is one for today, so a second
        request on the same day is idempotent rather than a second LLM call; the
        dashboard reaches this through ``POST …/ai/daily-tip/refresh`` (grower).

        A ``POST …/ai/tips/refresh?context_type=daily`` would not do: it builds a
        ``care``/``medium`` card valid for 24 hours, whereas the daily tip is an
        ``optimization``/``low`` card that expires at midnight. Reusing it would
        have changed what the daily tip *is*.
        """
        self._consent.require_consent(ctx.user_key, AI_TENANT_DATA_ACCESS)
        today = datetime.now(UTC).date().isoformat()
        cached = self._tip_cache.find_valid(ctx.tenant_key, "daily", today)
        if cached:
            return cached[0]

        question_context = self._resolve_context(ctx.tenant_key, "daily", today)
        question = self._tips.build_question(question_context, language)
        provider_key, provider_type, uses_cloud = self._resolve_provider(ctx, None, allow_cloud=allow_cloud)
        self._charge(ctx)
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
        self._budget.record_usage(tenant_key=ctx.tenant_key, usage=result.usage)
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
            usage=result.usage,
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
        allow_cloud: bool = False,
    ) -> AiResponse:
        """Generate a "why?" answer for a concrete recommendation (§4.5)."""
        self._consent.require_consent(ctx.user_key, AI_TENANT_DATA_ACCESS)
        self._require_owned_context(ctx.tenant_key, subject_type, subject_key)
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
        provider_key, provider_type, uses_cloud = self._resolve_provider(ctx, None, allow_cloud=allow_cloud)
        self._charge(ctx)
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

        self._budget.record_usage(tenant_key=ctx.tenant_key, usage=result.usage)
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
            usage=result.usage,
        )
        return self._to_response(
            result,
            language=language,
            uses_tenant_data=True,
            uses_cloud_provider=uses_cloud,
            confidence=question_context.confidence,
            provider_type=provider_type,
        )

    # ── Knowledge ask (tenant-scoped) ───────────────────────────────────

    def ask_knowledge(
        self,
        ctx: TenantContext,
        *,
        question: str,
        top_k: int = 5,
        doc_language: str | None = None,
        prompt_language: str | None = None,
        context: QuestionContext | None = None,
        allow_cloud: bool = False,
    ) -> KnowledgeAnswer:
        """Answer a free-form question through the Knowledge Service (#2175).

        The tenant-scoped successor of the former ``POST /api/v1/knowledge/ask``,
        which reached the LLM with no toggle, no consent and no budget. The
        caller's free-text question leaves the installation, so it needs its own
        consent ``ai_knowledge_question``; when ``context`` carries any plant
        value, those values leave too and ``ai_tenant_data_access`` is required
        in addition — tenant data never leaves under the question-only consent.
        Then the provider gate (``ai_cloud_processing`` when a cloud provider is
        used) and one charge against the daily AI budget — all before the
        Knowledge Service is called. The router adds the rank and the stage 1/2
        toggle.

        Unlike the tip and "why?" paths there is no rule-based answer to fall
        back on, so an unreachable Knowledge Service is a ``502`` here, audited
        as ``knowledge_service_error``.

        The answer carries the platform's cloud label (:meth:`_platform_provider`),
        as the glossary does: the Knowledge Service answers with its own model.
        """
        self._consent.require_consent(ctx.user_key, AI_KNOWLEDGE_QUESTION)
        # Decided on what would actually be sent: ``to_ks_payload`` drops unset
        # fields, so ``QuestionContext()`` carries no plant value and needs no
        # second consent — any value that would reach the KS does.
        carries_plant_values = context is not None and bool(context.to_ks_payload())
        if carries_plant_values:
            self._consent.require_consent(ctx.user_key, AI_TENANT_DATA_ACCESS)
        else:
            context = None
        _provider_key, provider_type, uses_cloud = self._resolve_provider(ctx, None, allow_cloud=allow_cloud)
        self._charge(ctx)
        started = time.monotonic()
        try:
            result = _run_sync(
                self._ks.ask(
                    question,
                    top_k=top_k,
                    context=context,
                    doc_language=doc_language,
                    prompt_language=prompt_language,
                )
            )
        except KnowledgeServiceUnavailableError:
            self._audit.record(
                tenant_key=ctx.tenant_key,
                user_key=ctx.user_key,
                endpoint="knowledge.ask",
                question=question,
                answer_length=0,
                provider_type=provider_type,
                language=prompt_language or "de",
                uses_tenant_data=context is not None,
                uses_cloud_provider=uses_cloud,
                latency_ms=int((time.monotonic() - started) * 1000),
                status="knowledge_service_error",
                error_class="knowledge_service_unavailable",
            )
            # ``from None``: the adapter's cause may be an httpx error that still
            # holds the request and its service-token header (SEC-004).
            raise ExternalSourceError("knowledge-service", "unavailable") from None

        self._budget.record_usage(tenant_key=ctx.tenant_key, usage=result.usage)
        self._audit.record(
            tenant_key=ctx.tenant_key,
            user_key=ctx.user_key,
            endpoint="knowledge.ask",
            question=question,
            answer_length=len(result.answer),
            model_name=result.model_name,
            provider_type=provider_type,
            kb_version=result.kb_version,
            language=prompt_language or "de",
            uses_tenant_data=context is not None,
            uses_cloud_provider=uses_cloud,
            latency_ms=int((time.monotonic() - started) * 1000),
            status="ok",
            usage=result.usage,
        )
        platform_provider_type, platform_uses_cloud = self._platform_provider()
        return KnowledgeAnswer(
            result=result,
            provider_type=platform_provider_type,
            uses_cloud_provider=platform_uses_cloud,
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
            usage=result.usage,
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

    def list_conversations(
        self, ctx: TenantContext, *, offset: int | None = None, limit: int | None = None
    ) -> list[AiConversation]:
        """The caller's conversations; ``offset``/``limit`` read one window (MT-035, #2131)."""
        return self._conversations.list_for_user(ctx.tenant_key, ctx.user_key, offset=offset, limit=limit)

    def get_conversation(self, ctx: TenantContext, key: str) -> AiConversation | None:
        conv = self._conversations.get_by_key(key)
        # SEC-002: a conversation is private to its owner. Scoping on tenant_key
        # alone lets any tenant member read/inject into a peer's chat (IDOR);
        # enforce ownership too, mirroring ``list_for_user`` semantics.
        if conv is None or conv.tenant_key != ctx.tenant_key or conv.user_key != ctx.user_key:
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
        self._require_owned_context(ctx.tenant_key, context_type, context_key)
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
        """DSGVO Art. 17 — hard-delete a caller-owned conversation (§7.5)."""
        conv = self._conversations.get_by_key(key)
        # SEC-002: only the owner may delete — tenant scoping alone is an IDOR.
        if conv is None or conv.tenant_key != ctx.tenant_key or conv.user_key != ctx.user_key:
            return False
        return self._conversations.delete(key)

    def stream_chat(
        self,
        ctx: TenantContext,
        *,
        conversation_key: str,
        message: str,
        language: str = "de",
        allow_cloud: bool = False,
    ) -> AsyncIterator[str]:
        """Admit a chat message, then return the SSE frames of its answer (§5.4).

        Every gate runs **here, eagerly**, before a single frame exists: the
        consent, the provider gate and the AI budget (#2110). The caller hands
        the returned iterator to a ``StreamingResponse``, whose ``200`` is on the
        wire before the first frame is produced — a refusal raised inside the
        stream used to arrive as a broken connection instead of a 403/429 the
        client can show.

        The Knowledge Service answers in one shot; the stream sends the answer
        word-by-word so the client renders progressively. A trailing ``event:
        done`` frame carries the metadata for the ``<AIResponse>`` envelope.
        """
        self._consent.require_consent(ctx.user_key, AI_TENANT_DATA_ACCESS)
        conv = self.get_conversation(ctx, conversation_key)
        if conv is None:
            return _frames(_sse_event("error", '{"detail":"conversation_not_found"}'))

        question_context = self._resolve_context(ctx.tenant_key, conv.context_type, conv.context_key or "")
        provider_key, provider_type, uses_cloud = self._resolve_provider(
            ctx, conv.provider_key or None, allow_cloud=allow_cloud
        )
        self._charge(ctx)
        return self._stream_answer(
            ctx,
            conv,
            message=message,
            language=language,
            question_context=question_context,
            provider_key=provider_key,
            provider_type=provider_type,
            uses_cloud=uses_cloud,
        )

    async def _stream_answer(
        self,
        ctx: TenantContext,
        conv: AiConversation,
        *,
        message: str,
        language: str,
        question_context: QuestionContext,
        provider_key: str,
        provider_type: str,
        uses_cloud: bool,
    ) -> AsyncIterator[str]:
        """The admitted half of :meth:`stream_chat`: one LLM call, streamed."""
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
        self._budget.record_usage(tenant_key=ctx.tenant_key, usage=result.usage)
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
            usage=result.usage,
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


async def _frames(*frames: str) -> AsyncIterator[str]:
    """A stream of fixed frames (an answer that needs no LLM call)."""
    for frame in frames:
        yield frame


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
