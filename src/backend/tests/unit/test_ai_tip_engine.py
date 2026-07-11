"""REQ-031 §4.4 (W-011) — unit tests for ``TipEngine``.

Verifies the rule-based fallback (used when the Knowledge Service is down) and
the tip-question construction.
"""

from __future__ import annotations

from app.domain.engines.ai_tip_engine import TipEngine
from app.domain.interfaces.knowledge_service import QuestionContext


def test_build_question_uses_species_and_phase() -> None:
    engine = TipEngine()
    context = QuestionContext(species="Cannabis sativa", phase="flowering")

    question_de = engine.build_question(context, "de")
    question_en = engine.build_question(context, "en")

    assert "Cannabis sativa" in question_de
    assert "flowering" in question_de
    assert "Cannabis sativa" in question_en


def test_fallback_flags_ec_out_of_range() -> None:
    engine = TipEngine()
    context = QuestionContext(species="Cannabis sativa", ec=3.0)

    tips = engine.rule_based_fallback(
        tenant_key="home",
        context_type="planting_run",
        context_key="run-1",
        context=context,
        language="de",
    )

    assert any(t.tip_type == "warning" for t in tips)
    # Fallback tips carry no LLM sources and are marked rule-based.
    assert all(t.sources == [] for t in tips)
    assert all(t.model_name == "rule-based-fallback" for t in tips)


def test_fallback_always_returns_at_least_one_tip() -> None:
    engine = TipEngine()
    context = QuestionContext()

    tips = engine.rule_based_fallback(
        tenant_key="home",
        context_type="general",
        context_key="x",
        context=context,
        language="en",
    )

    assert len(tips) >= 1
    assert tips[0].language == "en"
