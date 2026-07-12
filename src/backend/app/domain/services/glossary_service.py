"""REQ-035 §4.1 — ``GlossaryService`` (cache-first term explanations).

Central service behind the glossary endpoints. It resolves a term slug (with
language-sensitive alias resolution), serves a cached RAG answer when one is
still valid, and otherwise asks the Knowledge-Service microservice with a
strictly ``context=null`` prompt (no PII, §6). When the knowledge base has no
sufficiently relevant chunk (``max_score < 0.4``) it degrades to the editorial
fallback text and marks the answer ``is_fallback=true`` (§4.1 step 6).

The service consumes the REQ-031 foundation rather than rebuilding it: the async
:class:`~app.domain.interfaces.knowledge_service.IKnowledgeService` adapter (with
its circuit breaker), the :class:`~app.domain.services.ai_audit_logger.AiAuditLogger`,
and — for the tenant cloud-processing gate — the REQ-031 ``ConsentGuard`` and
provider repository. The Knowledge-Service LLM layer itself
(``app/llm/{ollama,anthropic,openai_compatible}.py``) is never touched here; it
is reached only through the adapter's ``/ask`` call.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import structlog

from app.common.exceptions import NotFoundError, ValidationError
from app.data_access.external.knowledge_service_adapter import KnowledgeServiceUnavailableError
from app.domain.guards.consent_guard import AI_CLOUD_PROCESSING, ConsentGuard
from app.domain.interfaces.knowledge_service import IKnowledgeService
from app.domain.models.glossary_term import (
    GlossaryRelatedTerm,
    GlossarySource,
    GlossaryTerm,
    GlossaryTermAnswer,
    GlossaryTermCacheEntry,
    GlossaryTermSummary,
)
from app.domain.services.ai_audit_logger import AiAuditLogger

logger = structlog.get_logger(__name__)

#: Glossary answers are quasi-static and cached for 7 days (§1, §2.2).
_CACHE_TTL = timedelta(days=7)
#: Below this RAG score the answer is considered a non-hit → editorial fallback.
_MIN_SCORE = 0.4
#: Retrieval breadth for the RAG call (§4.1 step 5).
_TOP_K = 5
#: Allowed slug characters — a controlled whitelist blocks prompt-injection and
#: XSS via the path segment (§9 scenario 9).
_SLUG_MAX_LEN = 80

_VALID_LEVELS: frozenset[str] = frozenset({"beginner", "intermediate", "expert"})
_VALID_LANGUAGES: frozenset[str] = frozenset({"de", "en"})


class GlossaryService:
    """Cache-first glossary term explanations backed by the Knowledge Service."""

    def __init__(
        self,
        *,
        term_repo,
        cache_repo,
        knowledge_adapter: IKnowledgeService,
        audit_logger: AiAuditLogger,
        consent_guard: ConsentGuard | None = None,
        provider_repo=None,
        redis_client=None,
    ) -> None:
        self._terms = term_repo
        self._cache = cache_repo
        self._ks = knowledge_adapter
        self._audit = audit_logger
        self._consent = consent_guard
        self._providers = provider_repo
        self._redis = redis_client

    # ── Public API ─────────────────────────────────────────────────────

    def list_terms(self, *, category: str | None = None, language: str = "de") -> list[GlossaryTermSummary]:
        """Return active terms (slug + localised label + category), §3.1 ``/terms``."""
        terms = self._terms.list_active(category=category)
        return [
            GlossaryTermSummary(slug=term.slug, label=term.label_for(language), category=term.category)
            for term in terms
        ]

    async def get_term(
        self,
        slug: str,
        *,
        language: str = "de",
        expertise_level: str = "beginner",
        tenant_key: str | None = None,
        user_key: str | None = None,
        allow_cloud: bool = False,
    ) -> GlossaryTermAnswer:
        """Explain one term (cache-first, RAG fallback), §4.1.

        ``tenant_key``/``user_key``/``allow_cloud`` are only supplied on the
        tenant-scoped path; the public light-mode path calls this without them and
        never triggers the cloud-processing consent gate. ``context`` is always
        ``null`` at the Knowledge Service (no PII, §6).
        """
        language = self._normalise_language(language)
        expertise_level = self._normalise_level(expertise_level)
        canonical = self._resolve_or_404(slug, language)
        term = self._terms.get_by_slug(canonical)
        if term is None:  # pragma: no cover - resolve guarantees existence
            raise NotFoundError("GlossaryTerm", slug)

        uses_cloud = self._enforce_cloud_gate(tenant_key=tenant_key, user_key=user_key, allow_cloud=allow_cloud)

        cached = self._load_cache(canonical, language, expertise_level)
        if cached is not None:
            self._audit_ok(term, language, expertise_level, cached, uses_cloud=uses_cloud)
            return self._to_answer(term, cached, language, expertise_level, uses_cloud=uses_cloud)

        entry = await self._generate(term, language, expertise_level)
        self._store_cache(entry)
        self._audit_ok(term, language, expertise_level, entry, uses_cloud=uses_cloud)
        return self._to_answer(term, entry, language, expertise_level, uses_cloud=uses_cloud)

    def invalidate_cache(self, slug: str | None = None) -> int:
        """Invalidate the whole glossary cache, or one term's cache (§3.3, §4.3)."""
        removed = self._cache.invalidate_slug(slug) if slug else self._cache.invalidate_all()
        self._redis_invalidate(slug)
        logger.info("glossary_cache_invalidated", slug=slug, removed=removed)
        return removed

    # ── Slug / input normalisation ─────────────────────────────────────

    def _resolve_or_404(self, slug: str, language: str) -> str:
        """Validate the slug shape then resolve it (or alias) to a canonical slug."""
        candidate = (slug or "").strip().lower()
        if not candidate or len(candidate) > _SLUG_MAX_LEN or not self._is_safe_slug(candidate):
            # §9 scenario 9 — reject malformed slugs before any KS call.
            raise ValidationError(
                "Invalid glossary term slug.",
                details=[{"field": "slug", "reason": "Slug contains illegal characters.", "code": "INVALID_SLUG"}],
            )
        canonical = self._terms.resolve_slug(candidate, language)
        if canonical is None:
            raise NotFoundError("GlossaryTerm", slug)
        return canonical

    @staticmethod
    def _is_safe_slug(value: str) -> bool:
        """True when ``value`` is a lowercase ``[a-z0-9-]`` slug (whitelist)."""
        return all(ch.isalnum() and ch.isascii() or ch == "-" for ch in value)

    @staticmethod
    def _normalise_language(language: str) -> str:
        if language not in _VALID_LANGUAGES:
            raise ValidationError(
                "Unsupported language.",
                details=[{"field": "language", "reason": "Must be 'de' or 'en'.", "code": "INVALID_LANGUAGE"}],
            )
        return language

    @staticmethod
    def _normalise_level(level: str) -> str:
        if level not in _VALID_LEVELS:
            # §9 scenario 9 — an out-of-enum expertise value is rejected, no KS call.
            raise ValidationError(
                "Unsupported expertise level.",
                details=[
                    {
                        "field": "expertise",
                        "reason": "Must be beginner, intermediate or expert.",
                        "code": "INVALID_EXPERTISE",
                    }
                ],
            )
        return level

    # ── Cloud-processing consent gate (§6) ─────────────────────────────

    def _enforce_cloud_gate(self, *, tenant_key: str | None, user_key: str | None, allow_cloud: bool) -> bool:
        """Return whether the answer is produced by a cloud provider.

        The public light-mode path (``tenant_key is None``) is always local — no
        cloud, no consent. On the tenant path, when the tenant both allows cloud
        providers *and* has a cloud provider as its effective default, the caller
        must hold the REQ-031 ``ai_cloud_processing`` consent before the RAG call
        runs (mirrors REQ-031 SEC-001). No PII is ever sent regardless (§6).
        """
        if tenant_key is None or self._providers is None or not allow_cloud:
            return False
        provider = self._providers.get_default(tenant_key, None)
        if provider is None:
            return False
        uses_cloud = provider.provider_type != "ollama" or provider.requires_consent
        if uses_cloud and self._consent is not None and user_key:
            self._consent.require_consent(user_key, AI_CLOUD_PROCESSING)
        return uses_cloud

    # ── RAG generation ─────────────────────────────────────────────────

    async def _generate(self, term: GlossaryTerm, language: str, expertise_level: str) -> GlossaryTermCacheEntry:
        """Ask the Knowledge Service and build a cache entry (fallback on miss)."""
        question = self._build_question(term, expertise_level)
        now = datetime.now(UTC)
        try:
            result = await self._ks.ask(
                question,
                top_k=_TOP_K,
                context=None,  # §4.1 step 5 — strictly no tenant/plant context.
                doc_language="all",
                prompt_language=language,
            )
        except KnowledgeServiceUnavailableError:
            self._audit.record(
                tenant_key="glossary",
                user_key=None,
                endpoint="glossary",
                question=question,
                answer_length=0,
                context_type="term",
                context_key=term.slug,
                language=language,
                uses_tenant_data=False,
                status="knowledge_service_error",
                error_class="knowledge_service_unavailable",
            )
            return self._fallback_entry(term, language, expertise_level, now)

        max_score = max((chunk.score for chunk in result.sources), default=0.0)
        if not result.sources or max_score < _MIN_SCORE:
            return self._fallback_entry(term, language, expertise_level, now)

        return GlossaryTermCacheEntry(
            term_slug=term.slug,
            language=language,  # type: ignore[arg-type]
            expertise_level=expertise_level,  # type: ignore[arg-type]
            answer_text=result.answer,
            sources=[
                GlossarySource(
                    source_key=chunk.source_key,
                    source_type=chunk.source_type,
                    title=chunk.title,
                    score=chunk.score,
                    language=chunk.language,
                )
                for chunk in result.sources
            ],
            model_name=result.model_name,
            provider_type=result.provider_type or "ollama",
            kb_version=result.kb_version,
            is_fallback=False,
            generated_at=now,
            valid_until=now + _CACHE_TTL,
        )

    def _fallback_entry(
        self, term: GlossaryTerm, language: str, expertise_level: str, now: datetime
    ) -> GlossaryTermCacheEntry:
        """Build an editorial fallback cache entry (``is_fallback=true``, §4.1)."""
        return GlossaryTermCacheEntry(
            term_slug=term.slug,
            language=language,  # type: ignore[arg-type]
            expertise_level=expertise_level,  # type: ignore[arg-type]
            answer_text=term.fallback_for(language),
            sources=[],
            model_name="",
            provider_type="",
            kb_version=None,
            is_fallback=True,
            generated_at=now,
            valid_until=now + _CACHE_TTL,
        )

    @staticmethod
    def _build_question(term: GlossaryTerm, expertise_level: str) -> str:
        """Template the curated ``rag_query_template`` (whitelist inputs, §6).

        Only the curated German label and the validated expertise level are
        substituted; no free user input reaches the prompt, so the glossary
        endpoint cannot be used for prompt injection (§9 scenario 9).
        """
        template = term.rag_query_template or (
            "Erklaere den Begriff '{label_de}' fuer einen {expertise_level} Pflanzenfreund. "
            "Gib eine kurze Definition und einen praxisnahen Hinweis."
        )
        return template.replace("{label_de}", term.label_for("de")).replace("{expertise_level}", expertise_level)

    # ── Cache (ArangoDB persist + optional Redis hot cache) ─────────────

    def _load_cache(self, slug: str, language: str, expertise_level: str) -> GlossaryTermCacheEntry | None:
        """Redis-hot first, then ArangoDB-persist (§4.1 step 3)."""
        hot = self._redis_get(slug, language, expertise_level)
        if hot is not None:
            return hot
        return self._cache.find_valid(slug, language, expertise_level)

    def _store_cache(self, entry: GlossaryTermCacheEntry) -> None:
        """Persist to ArangoDB (7d) and mirror into the Redis hot cache (§4.1 step 8)."""
        persisted = self._cache.upsert(entry)
        self._redis_set(persisted)

    def _redis_key(self, slug: str, language: str, expertise_level: str) -> str:
        return f"glossary:term:{slug}:{language}:{expertise_level}"

    def _redis_get(self, slug: str, language: str, expertise_level: str) -> GlossaryTermCacheEntry | None:
        if self._redis is None:
            return None
        try:
            raw = self._redis.get(self._redis_key(slug, language, expertise_level))
        except Exception:  # noqa: BLE001 — a Redis outage must not break the request.
            logger.debug("glossary_redis_get_failed", slug=slug)
            return None
        if not raw:
            return None
        try:
            return GlossaryTermCacheEntry(**json.loads(raw))
        except Exception:  # noqa: BLE001 — corrupt cache value is treated as a miss.
            return None

    def _redis_set(self, entry: GlossaryTermCacheEntry) -> None:
        if self._redis is None:
            return
        try:
            self._redis.set(
                self._redis_key(entry.term_slug, entry.language, entry.expertise_level),
                entry.model_dump_json(),
                ex=int(_CACHE_TTL.total_seconds()),
            )
        except Exception:  # noqa: BLE001 — best-effort hot cache.
            logger.debug("glossary_redis_set_failed", slug=entry.term_slug)

    def _redis_invalidate(self, slug: str | None) -> None:
        if self._redis is None:
            return
        try:
            pattern = f"glossary:term:{slug}:*" if slug else "glossary:term:*"
            keys = list(self._redis.scan_iter(match=pattern))
            if keys:
                self._redis.delete(*keys)
        except Exception:  # noqa: BLE001 — best-effort invalidation.
            logger.debug("glossary_redis_invalidate_failed", slug=slug)

    # ── Response assembly + audit ──────────────────────────────────────

    def _to_answer(
        self,
        term: GlossaryTerm,
        entry: GlossaryTermCacheEntry,
        language: str,
        expertise_level: str,
        *,
        uses_cloud: bool,
    ) -> GlossaryTermAnswer:
        return GlossaryTermAnswer(
            slug=term.slug,
            label=term.label_for(language),
            long_label=term.long_label_for(language),
            category=term.category,
            answer_text=entry.answer_text,
            expertise_level=expertise_level,  # type: ignore[arg-type]
            language=language,  # type: ignore[arg-type]
            language_mismatch_warning=entry.language_mismatch_warning,
            sources=entry.sources,
            related_terms=self._related_terms(term, language),
            is_fallback=entry.is_fallback,
            model_name=entry.model_name,
            provider_type=entry.provider_type,
            uses_tenant_data=False,
            uses_cloud_provider=uses_cloud,
            kb_version=entry.kb_version,
            generated_at=entry.generated_at,
        )

    def _related_terms(self, term: GlossaryTerm, language: str) -> list[GlossaryRelatedTerm]:
        """Resolve related-term slugs to clickable chips (skips missing terms)."""
        related: list[GlossaryRelatedTerm] = []
        for related_slug in term.related_term_slugs:
            neighbour = self._terms.get_by_slug(related_slug)
            if neighbour is not None and neighbour.is_active:
                related.append(GlossaryRelatedTerm(slug=neighbour.slug, label=neighbour.label_for(language)))
        return related

    def _audit_ok(
        self,
        term: GlossaryTerm,
        language: str,
        expertise_level: str,
        entry: GlossaryTermCacheEntry,
        *,
        uses_cloud: bool,
    ) -> None:
        """Write a PII-free audit record for a served answer (§4.1 step 9, §6)."""
        self._audit.record(
            tenant_key="glossary",
            user_key=None,
            endpoint="glossary",
            question=f"term:{term.slug}:{expertise_level}",
            answer_length=len(entry.answer_text),
            context_type="term",
            context_key=term.slug,
            model_name=entry.model_name,
            provider_type=entry.provider_type,
            kb_version=entry.kb_version,
            language=language,
            uses_tenant_data=False,
            uses_cloud_provider=uses_cloud,
            status="ok",
        )
