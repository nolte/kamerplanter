"""REQ-036 §4.2 — ``DiagnoseService`` (structured KI diagnosis assistant).

The symptom-based counterpart to the REQ-038 CV image classifier: the caller
picks catalogue symptoms (plus optional PII-free plant context and free-text
notes), the Knowledge-Service reasons over the RAG base, and the service returns
the **top-3 candidate diagnoses** bridged to the REQ-010 IPM stammdaten
(pests / treatments) for deep-linking.

It reuses the whole REQ-031 foundation — the async ``IKnowledgeService`` adapter
(circuit-breaker), the ``AiContextBuilder`` (ADR-002 species fallback), the
``ConsentGuard`` (stage-3 consent) and the privacy-preserving ``AiAuditLogger``
(hash-only). The diagnosis flow is **stateless**: nothing is persisted beyond one
hashed audit entry, so no new ArangoDB collection / migration is required.
"""

from __future__ import annotations

import time

import structlog

from app.data_access.external.knowledge_service_adapter import KnowledgeServiceUnavailableError
from app.domain.engines.diagnosis_analysis_engine import (
    DiagnosisAnalysisEngine,
    DiagnosisInvalidOutputError,
)
from app.domain.guards.consent_guard import AI_CLOUD_PROCESSING, AI_TENANT_DATA_ACCESS, ConsentGuard
from app.domain.interfaces.ipm_repository import IIpmRepository
from app.domain.interfaces.knowledge_service import ConfidenceLevel, QuestionContext
from app.domain.models.ai_assistant import SourceReference
from app.domain.models.diagnosis import (
    DiagnosisCandidate,
    DiagnosisResult,
    LlmDiagnosis,
    MatchedTreatment,
)
from app.domain.models.tenant_context import TenantContext
from app.domain.services.ai_audit_logger import AiAuditLogger
from app.domain.services.ai_context_builder import AiContextBuilder
from app.domain.services.symptom_catalog import SymptomCatalog

logger = structlog.get_logger(__name__)

#: Deep-link templates into the existing IPM detail pages (REQ-010 frontend).
_PEST_DETAIL_URL = "/pflanzenschutz/pests/{key}"
_TREATMENT_DETAIL_URL = "/pflanzenschutz/treatments/{key}"


def _numeric_to_level(confidence: float) -> ConfidenceLevel:
    """Map an LLM 0..1 confidence onto the shared UI confidence badge levels."""
    if confidence >= 0.66:
        return ConfidenceLevel.HIGH
    if confidence >= 0.33:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


class DiagnoseService:
    """Orchestrates a stateless, structured, IPM-bridged plant diagnosis."""

    def __init__(
        self,
        *,
        analysis_engine: DiagnosisAnalysisEngine,
        consent_guard: ConsentGuard,
        audit_logger: AiAuditLogger,
        ipm_repo: IIpmRepository,
        context_builder: AiContextBuilder | None = None,
        symptom_catalog: SymptomCatalog | None = None,
        plant_repo=None,
        species_repo=None,
        provider_repo=None,
    ) -> None:
        self._engine = analysis_engine
        self._consent = consent_guard
        self._audit = audit_logger
        self._ipm = ipm_repo
        self._context_builder = context_builder or AiContextBuilder()
        self._catalog = symptom_catalog or SymptomCatalog()
        self._plants = plant_repo
        self._species = species_repo
        self._providers = provider_repo

    # ── Symptom catalogue ───────────────────────────────────────────────

    def list_symptoms(self, *, phase: str | None = None, category: str | None = None):
        """Return the curated symptom catalogue (optionally filtered)."""
        return self._catalog.list_symptoms(phase=phase, category=category)

    # ── Diagnosis ───────────────────────────────────────────────────────

    async def diagnose(
        self,
        ctx: TenantContext,
        *,
        symptom_slugs: list[str],
        extra_notes: str | None = None,
        plant_instance_key: str | None = None,
        photo_ref: str | None = None,
        language: str = "de",
        allow_cloud: bool = False,
    ) -> DiagnosisResult:
        """Run the multi-step diagnosis flow and return the top-3 candidates.

        Order per call (mirrors the REQ-031 orchestration): consent (stage 3) →
        cloud-provider gate → PII-free context → KS reasoning → IPM bridge →
        hashed audit. Knowledge-Service outages and invalid LLM output degrade to
        a structured ``status`` result — never a 5xx.
        """
        self._consent.require_consent(ctx.user_key, AI_TENANT_DATA_ACCESS)

        symptoms = self._catalog.resolve(symptom_slugs)
        provider_type, uses_cloud = self._resolve_cloud(ctx, allow_cloud)
        context, confidence = self._build_context(ctx, plant_instance_key)
        has_notes = bool(extra_notes and extra_notes.strip())

        # A stable, PII-free question fingerprint for the audit hash.
        audit_question = "diagnosis:" + ",".join(sorted(symptom_slugs))
        started = time.monotonic()

        try:
            candidates_raw, ask_result = await self._engine.analyze(
                symptoms,
                context=context,
                language=language,
                has_extra_notes=has_notes,
                has_photo=bool(photo_ref),
            )
        except KnowledgeServiceUnavailableError:
            self._audit.record(
                tenant_key=ctx.tenant_key,
                user_key=ctx.user_key,
                endpoint="diagnosis",
                question=audit_question,
                answer_length=0,
                provider_type=provider_type,
                uses_tenant_data=True,
                uses_cloud_provider=uses_cloud,
                latency_ms=int((time.monotonic() - started) * 1000),
                status="knowledge_service_error",
                error_class="knowledge_service_unavailable",
            )
            return DiagnosisResult(
                status="knowledge_service_error",
                error_class="knowledge_service_unavailable",
                language=language,
                uses_tenant_data=True,
                uses_cloud_provider=uses_cloud,
                confidence=ConfidenceLevel.NONE,
            )
        except DiagnosisInvalidOutputError:
            self._audit.record(
                tenant_key=ctx.tenant_key,
                user_key=ctx.user_key,
                endpoint="diagnosis",
                question=audit_question,
                answer_length=0,
                provider_type=provider_type,
                uses_tenant_data=True,
                uses_cloud_provider=uses_cloud,
                latency_ms=int((time.monotonic() - started) * 1000),
                status="provider_error",
                error_class="diagnosis.invalid_llm_output",
            )
            return DiagnosisResult(
                status="error",
                error_class="diagnosis.invalid_llm_output",
                language=language,
                uses_tenant_data=True,
                uses_cloud_provider=uses_cloud,
                confidence=ConfidenceLevel.NONE,
            )

        candidates = [self._enrich(candidate, rank=index + 1) for index, candidate in enumerate(candidates_raw)]
        self._audit.record(
            tenant_key=ctx.tenant_key,
            user_key=ctx.user_key,
            endpoint="diagnosis",
            question=audit_question,
            answer_length=len(ask_result.answer),
            model_name=ask_result.model_name,
            provider_type=provider_type,
            uses_tenant_data=True,
            uses_cloud_provider=uses_cloud,
            latency_ms=int((time.monotonic() - started) * 1000),
            status="ok",
        )
        return DiagnosisResult(
            candidates=candidates,
            answer_summary=candidates[0].explanation if candidates else "",
            sources=[
                SourceReference(
                    source_key=c.source_key,
                    source_type=c.source_type,
                    title=c.title,
                    score=c.score,
                    language=c.language,
                )
                for c in ask_result.sources
            ],
            language=language,
            uses_tenant_data=True,
            uses_cloud_provider=uses_cloud,
            confidence=confidence,
            model_name=ask_result.model_name,
            provider_type=provider_type,
            kb_version=ask_result.kb_version,
            status="ok",
        )

    # ── IPM bridge ──────────────────────────────────────────────────────

    def _enrich(self, candidate: LlmDiagnosis, *, rank: int) -> DiagnosisCandidate:
        """Bridge one raw diagnosis onto REQ-010 pests / diseases / treatments."""
        enriched = DiagnosisCandidate(
            rank=rank,
            name=candidate.name,
            scientific_name=candidate.scientific_name,
            category=candidate.category,
            confidence=candidate.confidence,
            confidence_level=_numeric_to_level(candidate.confidence),
            explanation=candidate.explanation,
            recommended_actions=candidate.recommended_actions,
        )
        scientific = candidate.scientific_name
        if not scientific:
            return enriched

        pest = self._ipm.get_pest_by_scientific_name(scientific)
        if pest is not None and pest.key:
            enriched.matched_pest_key = pest.key
            enriched.matched_pest_detail_url = _PEST_DETAIL_URL.format(key=pest.key)
            enriched.matched_treatments = self._treatments_for_pest(pest.key)
            return enriched

        disease = self._ipm.get_disease_by_scientific_name(scientific)
        if disease is not None and disease.key:
            enriched.matched_disease_key = disease.key
        return enriched

    def _treatments_for_pest(self, pest_key: str) -> list[MatchedTreatment]:
        treatments = self._ipm.get_treatments_for_pest(pest_key)
        return [
            MatchedTreatment(
                key=t.key or "",
                name=t.name,
                name_de=t.name_de,
                treatment_type=str(t.treatment_type),
                safety_interval_days=t.safety_interval_days,
                has_karenz=t.safety_interval_days > 0,
                detail_url=_TREATMENT_DETAIL_URL.format(key=t.key),
            )
            for t in treatments
            if t.key
        ]

    # ── Context + provider helpers ──────────────────────────────────────

    def _build_context(
        self, ctx: TenantContext, plant_instance_key: str | None
    ) -> tuple[QuestionContext | None, ConfidenceLevel]:
        """Build the PII-free KS context from an optional plant instance.

        Returns ``(context, overall_confidence)``. Without a plant the diagnosis is
        purely symptom-driven (no species anchor, ``confidence=medium``).
        """
        if not plant_instance_key or self._plants is None:
            return (None, ConfidenceLevel.MEDIUM)

        plant = self._plants.get_by_key(plant_instance_key)
        if plant is None or plant.tenant_key != ctx.tenant_key:
            # SEC: never leak a foreign-tenant plant into the KS context.
            return (None, ConfidenceLevel.MEDIUM)

        species = None
        if self._species is not None and plant.species_key:
            species = self._species.get_by_key(plant.species_key)

        phase_name: str | None = None
        if plant.current_phase_key and hasattr(self._plants, "resolve_phase_name"):
            phase_name = self._plants.resolve_phase_name(plant.current_phase_key)

        context = self._context_builder.build_base_context(species=species, phase=phase_name)
        return (context, context.confidence)

    def _resolve_cloud(self, ctx: TenantContext, allow_cloud: bool) -> tuple[str, bool]:
        """Resolve ``(provider_type, uses_cloud)`` and enforce the cloud consent.

        Mirrors ``AiAssistantService._resolve_provider`` (SEC-001): a cloud default
        is downgraded fail-closed when the tenant disallows cloud, and an actually
        used cloud provider requires the ``ai_cloud_processing`` consent.
        """
        if self._providers is None:
            return ("ollama", False)
        provider = self._providers.get_default(ctx.tenant_key, None)
        if provider is None:
            return ("ollama", False)

        uses_cloud = provider.provider_type != "ollama" or provider.requires_consent
        if uses_cloud and not allow_cloud:
            uses_cloud = False
            return ("ollama", False)
        if uses_cloud:
            self._consent.require_consent(ctx.user_key, AI_CLOUD_PROCESSING)
        return (provider.provider_type, uses_cloud)


__all__ = ["DiagnoseService"]
