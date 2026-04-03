"""Question classification and prompt construction -- Single Source of Truth.

Consolidates the prompt logic that was previously split between
the KnowledgeService (production) and eval_rag.py (test tooling).
"""

import re
from enum import StrEnum

from app.vectordb.repository import VectorChunk


class QuestionType(StrEnum):
    """Classification of user questions for prompt selection."""

    DIAGNOSIS = "diagnosis"
    HOWTO = "howto"
    FACTUAL = "factual"


_HOWTO_PATTERNS = re.compile(
    r"(?i)(reihenfolge|wie\s+(mische|mach|starte|bereite|soll\s+ich|trockne|keime|berechne|stelle|ueberw[ei]nter|pflege)|"
    r"schritt|anleitung|wann\s+(starte|beginne|soll|kann\s+ich|ernte|pflanze)|"
    r"how\s+(do|should|to)|step|procedure|order|"
    r"welche.*reihenfolge|in\s+welcher|wie\s+oft|wie\s+viel|wie\s+lange|"
    r"muss\s+ich|brauche\s+ich|kann\s+ich.*verwenden|soll\s+ich.*duengen|"
    r"soll\s+ich.*giessen|wie\s+funktioniert|"
    r"wie\s+stelle\s+ich|wie\s+beuge|tipps)",
)

_DIAGNOSIS_PATTERNS = re.compile(
    r"(?i)(gelb|braun|welk|fleck|symptom|mangel|schae?dling|krank|"
    r"trueb|runoff|drift|fliegen|streifen|krusten|klebrig|"
    r"yellow|brown|wilt|spot|deficien|pest|disease|"
    r"haengt.*schlaff|kuemmer|Gespinst|Schimmel|faul|"
    r"stirbt|verfaerb|vergilb|was.*fehlt|was.*stimmt.*nicht|was.*ist.*das)",
)

_EXTRACTION_SUFFIX: dict[str, str] = {
    "de": (
        "Nenne mindestens 3-4 konkrete Punkte aus dem Kontext. "
        "Zitiere konkrete Schritte, Werte und Reihenfolgen. Nutze NUR den Kontext. Erfinde nichts.\n\n"
        "Beispiel fuer eine gute Antwort:\n"
        "Frage: Wie giesse ich meine Zimmerpflanze richtig?\n"
        "Antwort: 1. Fingerprobe: Erst giessen wenn die oberen 2-3 cm Substrat trocken sind. "
        "2. Gruendlich durchgiessen bis Wasser aus den Abzugsloechern laeuft. "
        "3. Ueberschuessiges Wasser im Untersetzer nach 30 Minuten weggiessen. "
        "4. Nicht nach Zeitplan giessen — der Bedarf haengt von Licht, Temperatur und Jahreszeit ab."
    ),
    "en": (
        "State at least 3-4 concrete points from the context. "
        "Quote specific steps, values, and sequences. "
        "Use ONLY the provided context. Do not make up facts."
    ),
}

_TYPED_PROMPTS: dict[str, dict[str, str]] = {
    "diagnosis": {
        "de": (
            "Du bist ein Pflanzenberater. Antworte auf Deutsch, fachlich korrekt und ausfuehrlich. "
            "Nenne: 1) Diagnose (Naehrstoff/Schaedling), 2) ob mobil/immobil und welche Blaetter betroffen, "
            "3) Ursachen (pH, EC pruefen), 4) Massnahmen. "
            "Nenne NUR die wahrscheinlichste Diagnose, nicht was es NICHT ist. "
            "Nenne ALLE relevanten Punkte, Empfehlungen und konkreten Massnahmen aus dem Kontext — ueberspringe nichts. "
        ),
        "en": (
            "You are a plant care advisor. Answer concisely and technically correct. "
            "State: 1) Diagnosis (nutrient/pest), 2) whether mobile/immobile and which leaves affected, "
            "3) Causes (check pH, EC), 4) Remedies. "
            "State ONLY the most likely diagnosis, not what it is NOT. "
            "Answer in the SAME LANGUAGE as the user's question. "
        ),
    },
    "howto": {
        "de": (
            "Du bist ein Pflanzenberater. Antworte auf Deutsch, praktisch und ausfuehrlich. "
            "Gib eine konkrete Schritt-fuer-Schritt-Anleitung. "
            "Nenne exakte Werte (Mengen, Temperaturen, Zeiten, Reihenfolgen) aus dem Kontext. "
            "Nummeriere die Schritte. Nenne ALLE relevanten Schritte und Hinweise aus dem Kontext — ueberspringe nichts. "
            "WICHTIG: Verwende KEINE Diagnose-Struktur. Antworte NICHT mit '1) Diagnose', "
            "'2) Mobil/Immobil'. Gib stattdessen eine praktische Anleitung. "
        ),
        "en": (
            "You are a plant care advisor. Answer concisely and practically. "
            "Provide a concrete step-by-step guide. "
            "State exact values (amounts, temperatures, times, sequences) from the context. "
            "Number the steps. "
            "IMPORTANT: Do NOT use a diagnosis structure. Do NOT answer with '1) Diagnosis', "
            "'2) Mobile/Immobile'. Instead, provide a practical guide. "
            "Answer in the SAME LANGUAGE as the user's question. "
        ),
    },
    "factual": {
        "de": (
            "Du bist ein Pflanzenberater. Antworte auf Deutsch, fachlich korrekt und ausfuehrlich. "
            "Beantworte die Frage direkt mit konkreten Fakten, Werten und Empfehlungen aus dem Kontext. "
            "Erklaere kurz warum. Nenne ALLE relevanten Punkte und Empfehlungen aus dem Kontext — ueberspringe nichts. "
            "WICHTIG: Verwende KEINE Diagnose-Struktur. Antworte NICHT mit '1) Diagnose', "
            "'2) Mobil/Immobil', '3) Ursachen', '4) Massnahmen'. "
            "Beantworte die Frage stattdessen direkt und erklaerend. "
        ),
        "en": (
            "You are a plant care advisor. Answer concisely and technically correct. "
            "Answer the question directly with concrete facts, values, and recommendations from the context. "
            "Briefly explain why. "
            "IMPORTANT: Do NOT use a diagnosis structure. Do NOT answer with '1) Diagnosis', "
            "'2) Mobile/Immobile', '3) Causes', '4) Remedies'. "
            "Instead, answer the question directly and explanatorily. "
            "Answer in the SAME LANGUAGE as the user's question. "
        ),
    },
}


class PromptEngine:
    """Classifies questions and builds optimized system prompts.

    Single Source of Truth for question classification and prompt construction.
    Used by both the production KnowledgeService and the eval benchmark runner.
    """

    def classify(self, question_text: str, explicit_type: str | None = None) -> QuestionType:
        """Determine question type: diagnosis, howto, or factual.

        Uses explicit type if provided, otherwise auto-detects from
        question text with keyword heuristics.
        """
        if explicit_type and explicit_type in QuestionType.__members__.values():
            return QuestionType(explicit_type)

        if _HOWTO_PATTERNS.search(question_text):
            return QuestionType.HOWTO
        if _DIAGNOSIS_PATTERNS.search(question_text):
            return QuestionType.DIAGNOSIS
        return QuestionType.FACTUAL

    def build_system_prompt(self, question_type: QuestionType, language: str = "de") -> str:
        """Build type-specific system prompt with extraction suffix."""
        base = _TYPED_PROMPTS.get(question_type, _TYPED_PROMPTS["factual"])
        prompt = base.get(language, base["de"])
        suffix = _EXTRACTION_SUFFIX.get(language, _EXTRACTION_SUFFIX["de"])
        return prompt + suffix

    def build_user_message(
        self,
        question: str,
        chunks: list[VectorChunk],
        situation: dict | None = None,
    ) -> str:
        """Build user message with context chunks and optional situation.

        Args:
            question: The user's question.
            chunks: Retrieved context chunks.
            situation: Optional dict with keys like species, phase, substrate, ec, ph.
        """
        chunk_texts = "\n\n---\n\n".join(f"[{i}] {c.title}\n{c.content}" for i, c in enumerate(chunks, start=1))

        parts = [f"Kontext aus Wissensdatenbank:\n{chunk_texts}"]

        if situation:
            situation_parts = []
            for key in ("species", "phase", "substrate", "ec", "ph"):
                val = situation.get(key)
                if val is not None:
                    situation_parts.append(f"{key}: {val}")
            if situation_parts:
                parts.append(f"Situation: {', '.join(situation_parts)}")

        parts.append(f"Frage: {question}")
        return "\n\n".join(parts)
