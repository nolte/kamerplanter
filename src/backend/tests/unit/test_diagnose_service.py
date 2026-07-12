"""REQ-036 §4.2 — unit tests for ``DiagnoseService`` orchestration.

Covers the top-3 result assembly, the REQ-010 IPM bridge (pest → detail URL +
treatments), the stage-3 consent gate, the SEC-001 cloud consent gate, and the
graceful ``status`` degradation on KS outage / invalid LLM output.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.common.enums import TenantRole, TreatmentType
from app.common.exceptions import ConsentRequiredError
from app.data_access.external.knowledge_service_adapter import KnowledgeServiceUnavailableError
from app.domain.engines.diagnosis_analysis_engine import DiagnosisInvalidOutputError
from app.domain.interfaces.knowledge_service import AskResult
from app.domain.models.ai_assistant import AiProviderConfig
from app.domain.models.diagnosis import LlmDiagnosis
from app.domain.models.ipm import Pest, Treatment
from app.domain.models.tenant_context import TenantContext
from app.domain.services.diagnose_service import DiagnoseService

pytestmark = pytest.mark.asyncio


def _ctx() -> TenantContext:
    return TenantContext(tenant_key="home", tenant_slug="home", user_key="anna", role=TenantRole.GROWER)


def _candidates() -> list[LlmDiagnosis]:
    return [
        LlmDiagnosis(
            name="Spider mites",
            scientific_name="Tetranychus urticae",
            category="pest_visible",
            confidence=0.85,
            explanation="Webbing present.",
            recommended_actions=["Increase humidity"],
        ),
        LlmDiagnosis(name="Heat stress", confidence=0.5, explanation="Too hot."),
    ]


def _service(*, analyze_result=None, analyze_exc=None, provider=None, consent_guard=None) -> DiagnoseService:
    engine = MagicMock()
    if analyze_exc is not None:
        engine.analyze = AsyncMock(side_effect=analyze_exc)
    else:
        result = analyze_result or (_candidates(), AskResult(answer="{...}", model_name="gemma3:12b"))
        engine.analyze = AsyncMock(return_value=result)

    guard = consent_guard or MagicMock()
    if consent_guard is None:
        guard.require_consent.return_value = None

    ipm_repo = MagicMock()
    ipm_repo.get_pest_by_scientific_name.return_value = Pest(
        _key="pest-1", scientific_name="Tetranychus urticae", common_name="Two-spotted spider mite"
    )
    ipm_repo.get_disease_by_scientific_name.return_value = None
    ipm_repo.get_treatments_for_pest.return_value = [
        Treatment(_key="t-1", name="Neem oil", treatment_type=TreatmentType.BIOLOGICAL, safety_interval_days=0),
        Treatment(_key="t-2", name="Pyrethrin", treatment_type=TreatmentType.CHEMICAL, safety_interval_days=3),
    ]

    provider_repo = MagicMock()
    provider_repo.get_default.return_value = provider

    return DiagnoseService(
        analysis_engine=engine,
        consent_guard=guard,
        audit_logger=MagicMock(),
        ipm_repo=ipm_repo,
        provider_repo=provider_repo,
    )


async def test_diagnose_returns_top_candidates_ipm_bridged() -> None:
    service = _service()

    result = await service.diagnose(_ctx(), symptom_slugs=["webbing_on_leaves"])

    assert result.status == "ok"
    assert result.uses_tenant_data is True
    assert len(result.candidates) == 2
    top = result.candidates[0]
    assert top.rank == 1
    assert top.matched_pest_key == "pest-1"
    assert top.matched_pest_detail_url == "/pflanzenschutz/pests/pest-1"
    assert {t.key for t in top.matched_treatments} == {"t-1", "t-2"}
    # Karenz flag derived from the chemical treatment's safety interval.
    karenz = {t.key: t.has_karenz for t in top.matched_treatments}
    assert karenz == {"t-1": False, "t-2": True}


async def test_diagnose_requires_tenant_data_consent() -> None:
    guard = MagicMock()
    guard.require_consent.side_effect = ConsentRequiredError("ai_tenant_data_access")
    service = _service(consent_guard=guard)

    with pytest.raises(ConsentRequiredError):
        await service.diagnose(_ctx(), symptom_slugs=["leaf_spots"])


async def test_diagnose_degrades_on_ks_outage() -> None:
    service = _service(analyze_exc=KnowledgeServiceUnavailableError("down"))

    result = await service.diagnose(_ctx(), symptom_slugs=["leaf_spots"])

    assert result.status == "knowledge_service_error"
    assert result.candidates == []


async def test_diagnose_reports_invalid_llm_output() -> None:
    service = _service(analyze_exc=DiagnosisInvalidOutputError("bad json"))

    result = await service.diagnose(_ctx(), symptom_slugs=["leaf_spots"])

    assert result.status == "error"
    assert result.error_class == "diagnosis.invalid_llm_output"


async def test_extra_notes_not_forwarded_as_plaintext() -> None:
    service = _service()

    await service.diagnose(_ctx(), symptom_slugs=["leaf_spots"], extra_notes="my plant named after my daughter Lena")

    # The engine only receives the has_extra_notes flag, never the raw text.
    kwargs = service._engine.analyze.await_args.kwargs
    assert kwargs["has_extra_notes"] is True
    assert "Lena" not in str(service._engine.analyze.await_args)


async def test_cloud_provider_without_consent_is_blocked() -> None:
    guard = MagicMock()

    def _require(user_key, purpose):
        if purpose == "ai_cloud_processing":
            raise ConsentRequiredError("ai_cloud_processing")

    guard.require_consent.side_effect = _require
    cloud = AiProviderConfig(
        _key="claude",
        tenant_key="home",
        provider_type="anthropic",
        display_name="Claude",
        model_name="claude-3-5",
        requires_consent=True,
        is_default=True,
    )
    service = _service(provider=cloud, consent_guard=guard)

    with pytest.raises(ConsentRequiredError):
        await service.diagnose(_ctx(), symptom_slugs=["leaf_spots"], allow_cloud=True)


async def test_plant_context_builds_species_anchor() -> None:
    from app.common.enums import DataOrigin
    from app.domain.models.species import Species

    service = _service()
    plant = MagicMock()
    plant.tenant_key = "home"
    plant.species_key = "sp-1"
    plant.current_phase_key = "phase-veg"
    plant_repo = MagicMock()
    plant_repo.get_by_key.return_value = plant
    plant_repo.resolve_phase_name.return_value = "vegetative"
    species_repo = MagicMock()
    species_repo.get_by_key.return_value = Species(
        _key="sp-1",
        scientific_name="Cannabis sativa",
        common_names=["Hanf"],
        origin=DataOrigin.SYSTEM,
    )
    service._plants = plant_repo
    service._species = species_repo

    await service.diagnose(_ctx(), symptom_slugs=["leaf_spots"], plant_instance_key="plant-1")

    ctx_arg = service._engine.analyze.await_args.kwargs["context"]
    assert ctx_arg is not None
    assert ctx_arg.species == "Cannabis sativa"
    assert ctx_arg.phase == "vegetative"


async def test_foreign_tenant_plant_is_not_leaked_into_context() -> None:
    service = _service()
    plant = MagicMock()
    plant.tenant_key = "other-tenant"
    plant_repo = MagicMock()
    plant_repo.get_by_key.return_value = plant
    service._plants = plant_repo

    await service.diagnose(_ctx(), symptom_slugs=["leaf_spots"], plant_instance_key="foreign-1")

    # SEC: a foreign-tenant plant must never enter the KS context.
    assert service._engine.analyze.await_args.kwargs["context"] is None


async def test_cloud_provider_downgraded_when_tenant_disallows() -> None:
    cloud = AiProviderConfig(
        _key="claude",
        tenant_key="home",
        provider_type="anthropic",
        display_name="Claude",
        model_name="claude-3-5",
        requires_consent=True,
        is_default=True,
    )
    service = _service(provider=cloud)

    result = await service.diagnose(_ctx(), symptom_slugs=["leaf_spots"], allow_cloud=False)

    # Fail-closed: cloud not used, so no cloud indicator.
    assert result.uses_cloud_provider is False
