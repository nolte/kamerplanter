"""REQ-036 §4.3 — ``DiagnosisAnalysisEngine``.

Turns the selected symptoms plus PII-free plant context into a knowledge-base
question that constrains the LLM to emit a JSON ``diagnoses`` array, calls the
Knowledge-Service through the async REQ-031 adapter, and validates the answer
into :class:`~app.domain.models.diagnosis.LlmDiagnosis` objects.

Robustness (spec risk note: "JSON-Output-Parsing des LLM ist fragil"):

* a permissive JSON extractor tolerates Markdown code fences and leading prose;
* a **two-attempt** strategy re-asks once with a stricter prompt on the first
  parse/validation failure; a second failure raises
  :class:`DiagnosisInvalidOutputError`, which the service maps to
  ``status="error"`` / ``error_class="diagnosis.invalid_llm_output"`` (never a
  5xx).

The engine never touches the IPM stammdaten or the audit log — that enrichment
and bookkeeping lives in :class:`~app.domain.services.diagnose_service.DiagnoseService`.
"""

from __future__ import annotations

import json
import re

import structlog
from pydantic import ValidationError

from app.domain.interfaces.knowledge_service import AskResult, IKnowledgeService, QuestionContext
from app.domain.models.diagnosis import LlmDiagnosis, SymptomCatalogEntry

logger = structlog.get_logger(__name__)

#: How many candidate diagnoses the client surfaces (top-3, §8 DoD).
MAX_CANDIDATES = 3

#: Knowledge-Service retrieval depth for a diagnosis query (§4.3).
_ASK_TOP_K = 8

_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


class DiagnosisInvalidOutputError(RuntimeError):
    """The LLM answer could not be parsed into structured diagnoses (twice)."""


def _symptom_label(entry: SymptomCatalogEntry, language: str) -> str:
    return entry.label_en if language == "en" else entry.label_de


def _extract_json(text: str) -> dict:
    """Best-effort extraction of the first JSON object from an LLM answer.

    Handles bare JSON, ```json fenced blocks and answers with leading prose. A
    :class:`ValueError` is raised when nothing JSON-shaped is present.
    """
    stripped = text.strip()
    # Strip a Markdown code fence if present.
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.lstrip().lower().startswith("json"):
            stripped = stripped.lstrip()[4:]
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass
    match = _JSON_OBJECT_RE.search(text)
    if match is None:
        raise ValueError("no JSON object found in LLM answer")
    return json.loads(match.group(0))


def _parse_candidates(answer: str) -> list[LlmDiagnosis]:
    """Parse + validate the ``diagnoses`` array, sorted by confidence desc.

    Raises :class:`ValueError`/:class:`ValidationError` on malformed output so the
    caller can decide whether to retry.
    """
    payload = _extract_json(answer)
    raw = payload.get("diagnoses")
    if not isinstance(raw, list) or not raw:
        raise ValueError("LLM answer has no 'diagnoses' array")
    candidates = [LlmDiagnosis.model_validate(item) for item in raw if isinstance(item, dict)]
    if not candidates:
        raise ValueError("no valid diagnosis objects in 'diagnoses' array")
    candidates.sort(key=lambda c: c.confidence, reverse=True)
    return candidates[:MAX_CANDIDATES]


class DiagnosisAnalysisEngine:
    """Builds the diagnosis question and validates the LLM's structured answer."""

    def __init__(self, knowledge_adapter: IKnowledgeService) -> None:
        self._ks = knowledge_adapter

    def build_question(
        self,
        symptoms: list[SymptomCatalogEntry],
        *,
        language: str = "de",
        has_extra_notes: bool = False,
        has_photo: bool = False,
        strict: bool = False,
    ) -> str:
        """Assemble the RAG question that constrains the answer to JSON.

        Only symptom *labels* and the (already PII-free) context enter here. The
        user's free-text ``extra_notes`` are NEVER inlined — at most the neutral
        hint that the user added notes is appended (§8 scenario).
        """
        symptom_lines = "\n".join(f"- {_symptom_label(s, language)}" for s in symptoms)
        if language == "en":
            preamble = (
                "You are a horticultural plant-health diagnosis assistant. Based on the "
                "observed symptoms below, determine the three most likely causes."
            )
            schema = (
                'Respond with ONLY a JSON object of the form: {"diagnoses": [{"name": str, '
                '"scientific_name": str|null, "category": str, "confidence": number 0..1, '
                '"explanation": str, "recommended_actions": [str]}]}. Return at most three '
                "diagnoses ordered by descending confidence. Do not add any text outside the JSON."
            )
            symptom_header = "Observed symptoms:"
            notes_hint = "The user added free-text notes (not shown for privacy)."
            photo_hint = "The user attached a photo for reference."
        else:
            preamble = (
                "Du bist ein Assistent fuer die Pflanzengesundheits-Diagnose. Bestimme anhand der "
                "unten genannten Symptome die drei wahrscheinlichsten Ursachen."
            )
            schema = (
                'Antworte AUSSCHLIESSLICH mit einem JSON-Objekt der Form: {"diagnoses": [{"name": str, '
                '"scientific_name": str|null, "category": str, "confidence": Zahl 0..1, '
                '"explanation": str, "recommended_actions": [str]}]}. Gib hoechstens drei Diagnosen '
                "absteigend nach Konfidenz zurueck. Fuege keinen Text ausserhalb des JSON hinzu."
            )
            symptom_header = "Beobachtete Symptome:"
            notes_hint = "Der Nutzer hat Freitext-Anmerkungen gemacht (aus Datenschutzgruenden nicht gezeigt)."
            photo_hint = "Der Nutzer hat ein Foto als Referenz angehaengt."

        parts = [preamble, "", symptom_header, symptom_lines]
        if has_extra_notes:
            parts.append(notes_hint)
        if has_photo:
            parts.append(photo_hint)
        if strict:
            reminder = (
                "IMPORTANT: your previous answer was not valid JSON. Return valid JSON only."
                if language == "en"
                else (
                    "WICHTIG: Deine vorherige Antwort war kein gueltiges JSON. "
                    "Gib ausschliesslich gueltiges JSON zurueck."
                )
            )
            parts.append(reminder)
        parts.append("")
        parts.append(schema)
        return "\n".join(parts)

    async def analyze(
        self,
        symptoms: list[SymptomCatalogEntry],
        *,
        context: QuestionContext | None = None,
        language: str = "de",
        has_extra_notes: bool = False,
        has_photo: bool = False,
    ) -> tuple[list[LlmDiagnosis], AskResult]:
        """Query the KS and return ``(top_candidates, raw_ask_result)``.

        Propagates :class:`~app.data_access.external.knowledge_service_adapter.
        KnowledgeServiceUnavailableError` unchanged (the service degrades on it).
        Raises :class:`DiagnosisInvalidOutputError` only after two failed parses.
        """
        question = self.build_question(
            symptoms, language=language, has_extra_notes=has_extra_notes, has_photo=has_photo
        )
        result = await self._ks.ask(
            question,
            top_k=_ASK_TOP_K,
            context=context,
            doc_language="all",
            prompt_language=language,
        )
        try:
            return (_parse_candidates(result.answer), result)
        except (ValueError, ValidationError, json.JSONDecodeError) as exc:
            # First-attempt parse/validation failure → fall through to the
            # stricter retry below (§4.3 two-attempt strategy).
            logger.debug("diagnosis.first_attempt_parse_failed", error=str(exc))

        # Second, stricter attempt (§4.3 two-attempt strategy).
        strict_question = self.build_question(
            symptoms,
            language=language,
            has_extra_notes=has_extra_notes,
            has_photo=has_photo,
            strict=True,
        )
        retry = await self._ks.ask(
            strict_question,
            top_k=_ASK_TOP_K,
            context=context,
            doc_language="all",
            prompt_language=language,
        )
        try:
            return (_parse_candidates(retry.answer), retry)
        except (ValueError, ValidationError, json.JSONDecodeError) as exc:
            raise DiagnosisInvalidOutputError("LLM produced no valid diagnosis JSON") from exc
