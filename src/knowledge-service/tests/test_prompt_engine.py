"""Unit tests for the PromptEngine -- question classification and prompt building."""

from app.prompt_engine import PromptEngine, QuestionType
from app.vectordb.repository import VectorChunk


class TestClassify:
    """Tests for question type classification."""

    def test_diagnosis_gelbe_blaetter(self, prompt_engine: PromptEngine) -> None:
        result = prompt_engine.classify("Warum werden die unteren Blaetter gelb?")
        assert result == QuestionType.DIAGNOSIS

    def test_diagnosis_mangel(self, prompt_engine: PromptEngine) -> None:
        result = prompt_engine.classify("Meine Pflanze hat einen Mangel")
        assert result == QuestionType.DIAGNOSIS

    def test_diagnosis_english(self, prompt_engine: PromptEngine) -> None:
        result = prompt_engine.classify("Why are the leaves turning yellow?")
        assert result == QuestionType.DIAGNOSIS

    def test_howto_wie_mische(self, prompt_engine: PromptEngine) -> None:
        result = prompt_engine.classify("Wie mische ich CalMag richtig?")
        assert result == QuestionType.HOWTO

    def test_howto_reihenfolge(self, prompt_engine: PromptEngine) -> None:
        result = prompt_engine.classify("In welcher Reihenfolge mische ich Duenger?")
        assert result == QuestionType.HOWTO

    def test_howto_english(self, prompt_engine: PromptEngine) -> None:
        result = prompt_engine.classify("How do I start seeds indoors?")
        assert result == QuestionType.HOWTO

    def test_factual_default(self, prompt_engine: PromptEngine) -> None:
        result = prompt_engine.classify("Welcher EC-Wert ist optimal fuer Tomaten?")
        assert result == QuestionType.FACTUAL

    def test_explicit_override(self, prompt_engine: PromptEngine) -> None:
        result = prompt_engine.classify("Gelbe Blaetter", explicit_type="howto")
        assert result == QuestionType.HOWTO

    def test_explicit_invalid_falls_back(self, prompt_engine: PromptEngine) -> None:
        result = prompt_engine.classify("Welcher EC-Wert?", explicit_type="invalid_type")
        assert result == QuestionType.FACTUAL


class TestBuildSystemPrompt:
    """Tests for system prompt construction."""

    def test_diagnosis_de(self, prompt_engine: PromptEngine) -> None:
        prompt = prompt_engine.build_system_prompt(QuestionType.DIAGNOSIS, "de")
        assert "Diagnose" in prompt
        assert "Erfinde nichts" in prompt

    def test_howto_de(self, prompt_engine: PromptEngine) -> None:
        prompt = prompt_engine.build_system_prompt(QuestionType.HOWTO, "de")
        assert "Schritt-fuer-Schritt" in prompt
        assert "Nummeriere" in prompt

    def test_factual_en(self, prompt_engine: PromptEngine) -> None:
        prompt = prompt_engine.build_system_prompt(QuestionType.FACTUAL, "en")
        assert "concrete facts" in prompt
        assert "Do not make up facts" in prompt

    def test_unknown_language_falls_back_to_de(self, prompt_engine: PromptEngine) -> None:
        prompt = prompt_engine.build_system_prompt(QuestionType.DIAGNOSIS, "fr")
        assert "Diagnose" in prompt


class TestBuildUserMessage:
    """Tests for user message construction with context chunks."""

    def test_basic_message(self, prompt_engine: PromptEngine) -> None:
        chunks = [
            VectorChunk(
                source_key="test/chunk#1",
                source_type="care_rule",
                title="Test Chunk",
                content="Test content here.",
                metadata={},
            ),
        ]
        msg = prompt_engine.build_user_message("Was ist los?", chunks)
        assert "Kontext aus Wissensdatenbank:" in msg
        assert "[1] Test Chunk" in msg
        assert "Frage: Was ist los?" in msg

    def test_with_situation(self, prompt_engine: PromptEngine) -> None:
        chunks = [
            VectorChunk(
                source_key="test/chunk#1",
                source_type="care_rule",
                title="Test",
                content="Content.",
                metadata={},
            ),
        ]
        situation = {"species": "Cannabis sativa", "phase": "flowering", "ec": 1.8}
        msg = prompt_engine.build_user_message("Gelbe Blaetter?", chunks, situation)
        assert "Situation:" in msg
        assert "species: Cannabis sativa" in msg
        assert "phase: flowering" in msg
        assert "ec: 1.8" in msg

    def test_without_situation(self, prompt_engine: PromptEngine) -> None:
        chunks = [
            VectorChunk(
                source_key="test/chunk#1",
                source_type="care_rule",
                title="Test",
                content="Content.",
                metadata={},
            ),
        ]
        msg = prompt_engine.build_user_message("Frage?", chunks, None)
        assert "Situation:" not in msg
