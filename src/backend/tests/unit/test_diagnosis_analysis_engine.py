"""REQ-036 §4.3 — unit tests for the ``DiagnosisAnalysisEngine``.

Covers JSON extraction (bare / fenced / prose-prefixed), top-3 confidence sort,
the free-text privacy guarantee, and the two-attempt retry → error path.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.domain.engines.diagnosis_analysis_engine import (
    DiagnosisAnalysisEngine,
    DiagnosisInvalidOutputError,
)
from app.domain.interfaces.knowledge_service import AskResult
from app.domain.services.symptom_catalog import SymptomCatalog

pytestmark = pytest.mark.asyncio

_CATALOG = SymptomCatalog()
_SYMPTOMS = _CATALOG.resolve(["leaves_yellowing_lower", "leaf_spots"])


def _ask(answer: str) -> AsyncMock:
    return AsyncMock(return_value=AskResult(answer=answer, model_name="gemma3:12b"))


_FOUR_DIAGNOSES = (
    '{"diagnoses": ['
    '{"name": "Nitrogen deficiency", "scientific_name": null, "category": "environmental", '
    '"confidence": 0.9, "explanation": "Low N.", "recommended_actions": ["Feed nitrogen"]},'
    '{"name": "Overwatering", "scientific_name": null, "category": "environmental", '
    '"confidence": 0.4, "explanation": "Too wet.", "recommended_actions": []},'
    '{"name": "Leaf spot", "scientific_name": "Septoria", "category": "disease_visible", '
    '"confidence": 0.6, "explanation": "Fungal.", "recommended_actions": []},'
    '{"name": "Filler", "scientific_name": null, "category": "environmental", '
    '"confidence": 0.1, "explanation": "x", "recommended_actions": []}'
    "]}"
)


async def test_analyze_returns_top3_sorted_by_confidence() -> None:
    adapter = AsyncMock()
    adapter.ask = _ask(_FOUR_DIAGNOSES)
    engine = DiagnosisAnalysisEngine(adapter)

    candidates, _ = await engine.analyze(_SYMPTOMS, language="en")

    assert [c.confidence for c in candidates] == [0.9, 0.6, 0.4]
    assert len(candidates) == 3


async def test_analyze_extracts_json_from_markdown_fence() -> None:
    adapter = AsyncMock()
    fenced = "```json\n" + _FOUR_DIAGNOSES + "\n```"
    adapter.ask = _ask(fenced)
    engine = DiagnosisAnalysisEngine(adapter)

    candidates, _ = await engine.analyze(_SYMPTOMS)
    assert candidates[0].name == "Nitrogen deficiency"


async def test_analyze_extracts_json_after_prose() -> None:
    adapter = AsyncMock()
    adapter.ask = _ask("Sure, here is my analysis:\n" + _FOUR_DIAGNOSES)
    engine = DiagnosisAnalysisEngine(adapter)

    candidates, _ = await engine.analyze(_SYMPTOMS)
    assert len(candidates) == 3


async def test_analyze_retries_once_then_succeeds() -> None:
    adapter = AsyncMock()
    adapter.ask = AsyncMock(
        side_effect=[
            AskResult(answer="not json at all", model_name="m"),
            AskResult(answer=_FOUR_DIAGNOSES, model_name="m"),
        ]
    )
    engine = DiagnosisAnalysisEngine(adapter)

    candidates, _ = await engine.analyze(_SYMPTOMS)

    assert adapter.ask.await_count == 2
    assert len(candidates) == 3


async def test_analyze_raises_after_two_invalid_attempts() -> None:
    adapter = AsyncMock()
    adapter.ask = _ask("still not json")
    engine = DiagnosisAnalysisEngine(adapter)

    with pytest.raises(DiagnosisInvalidOutputError):
        await engine.analyze(_SYMPTOMS)
    assert adapter.ask.await_count == 2


async def test_build_question_never_inlines_extra_notes() -> None:
    engine = DiagnosisAnalysisEngine(AsyncMock())
    question = engine.build_question(_SYMPTOMS, language="de", has_extra_notes=True)
    # Only the neutral hint, never any user free text.
    assert "Anmerkungen gemacht" in question


async def test_analyze_forwards_top_k_and_language() -> None:
    adapter = AsyncMock()
    adapter.ask = _ask(_FOUR_DIAGNOSES)
    engine = DiagnosisAnalysisEngine(adapter)

    await engine.analyze(_SYMPTOMS, language="en")

    kwargs = adapter.ask.await_args.kwargs
    assert kwargs["top_k"] == 8
    assert kwargs["prompt_language"] == "en"
    assert kwargs["doc_language"] == "all"
