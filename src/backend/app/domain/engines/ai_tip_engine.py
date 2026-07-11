"""REQ-031 §4.4 — ``TipEngine`` (tip-card question + rule-based fallback).

The RAG retrieval itself lives in the Knowledge Service; this engine only builds
the tip question and — crucially — provides the **backend-side rule-based
fallback** (W-011) so a Knowledge-Service outage degrades to a still-useful tip
instead of a 5xx. Fallback rules use master values only (no PII).
"""

from __future__ import annotations

from app.domain.interfaces.knowledge_service import QuestionContext
from app.domain.models.ai_assistant import AiTipCard, SourceReference


class TipEngine:
    """Builds tip questions and rule-based fallback tips."""

    def build_question(self, context: QuestionContext, language: str) -> str:
        """Compose a compact "generate care tips" question from the context."""
        species = context.species or ("a houseplant" if language == "en" else "einer Zimmerpflanze")
        phase = context.phase
        if language == "en":
            question = f"Give 2-4 concise, actionable care tips for {species}"
            if phase:
                question += f" in the {phase} phase"
            question += "."
        else:
            question = f"Gib 2-4 kompakte, umsetzbare Pflegehinweise fuer {species}"
            if phase:
                question += f" in der Phase {phase}"
            question += "."
        return question

    def rule_based_fallback(
        self,
        *,
        tenant_key: str,
        context_type: str,
        context_key: str,
        context: QuestionContext,
        language: str,
    ) -> list[AiTipCard]:
        """Return deterministic fallback tips when the KS is unavailable (W-011).

        These carry no ``sources`` and are flagged as backend-generated so the UI
        can present them without the "AI answered" implication being misleading —
        they are rule-based, not LLM output.
        """
        tips: list[AiTipCard] = []

        def _card(title: str, body: str, priority: str, tip_type: str) -> AiTipCard:
            return AiTipCard(
                tenant_key=tenant_key,
                context_type=context_type,  # type: ignore[arg-type]
                context_key=context_key,
                tip_type=tip_type,  # type: ignore[arg-type]
                priority=priority,  # type: ignore[arg-type]
                title=title,
                body=body,
                sources=[],
                language=language,  # type: ignore[arg-type]
                uses_tenant_data=bool(context.species),
                model_name="rule-based-fallback",
                provider_key="fallback",
            )

        en = language == "en"
        # EC out of a common target band → warning tip.
        if context.ec is not None and (context.ec < 0.8 or context.ec > 2.4):
            tips.append(
                _card(
                    "Check nutrient concentration" if en else "Naehrstoffkonzentration pruefen",
                    (
                        f"The measured EC ({context.ec}) is outside the usual range. "
                        "Adjust the nutrient solution and re-measure."
                        if en
                        else f"Der gemessene EC-Wert ({context.ec}) liegt ausserhalb des ueblichen Bereichs. "
                        "Passe die Naehrloesung an und miss erneut."
                    ),
                    "high",
                    "warning",
                )
            )
        # pH out of band → warning tip.
        if context.ph is not None and (context.ph < 5.5 or context.ph > 6.8):
            tips.append(
                _card(
                    "Correct the pH value" if en else "pH-Wert korrigieren",
                    (
                        f"A pH of {context.ph} can block nutrient uptake. Aim for 5.8-6.5."
                        if en
                        else f"Ein pH von {context.ph} kann die Naehrstoffaufnahme blockieren. Ziel: 5,8-6,5."
                    ),
                    "high",
                    "warning",
                )
            )
        # Always provide at least one generic care tip.
        if not tips:
            tips.append(
                _card(
                    "Keep an eye on your plant" if en else "Behalte deine Pflanze im Blick",
                    (
                        "The knowledge assistant is temporarily unavailable. Check soil "
                        "moisture, light and leaf colour, and revisit in a moment for AI tips."
                        if en
                        else "Der Wissensassistent ist gerade nicht erreichbar. Pruefe Substratfeuchte, "
                        "Licht und Blattfarbe und schau gleich noch einmal fuer KI-Tipps vorbei."
                    ),
                    "low",
                    "care",
                )
            )
        return tips

    @staticmethod
    def to_sources(chunks: list) -> list[SourceReference]:
        """Map KS ``KnowledgeChunk`` results to persisted ``SourceReference``s."""
        return [
            SourceReference(
                source_key=chunk.source_key,
                source_type=chunk.source_type,
                title=chunk.title,
                score=chunk.score,
                language=chunk.language,
            )
            for chunk in chunks
        ]
