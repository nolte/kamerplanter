"""Unit tests for KnowledgeService."""

from unittest.mock import MagicMock

import pytest

from app.data_access.vectordb.vector_chunk_repository import VectorChunk
from app.domain.interfaces.llm_adapter import LlmResponse
from app.domain.services.knowledge_service import _SYSTEM_PROMPTS, KnowledgeService


def _make_chunk(title: str = "Test Guide", score: float = 0.9) -> VectorChunk:
    return VectorChunk(
        source_key=f"knowledge_guide:{title.lower().replace(' ', '_')}",
        source_type="knowledge_guide",
        title=title,
        content=f"Content of {title}.",
        metadata={"category": "test"},
        score=score,
    )


@pytest.fixture
def mock_embedding():
    engine = MagicMock()
    engine.embed.return_value = [0.1] * 768
    return engine


@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def mock_llm():
    return MagicMock()


@pytest.fixture
def service(mock_embedding, mock_repo, mock_llm):
    return KnowledgeService(
        embedding_engine=mock_embedding,
        chunk_repo=mock_repo,
        llm_adapter=mock_llm,
        max_tokens=512,
        temperature=0.2,
    )


class TestSearch:
    def test_search_returns_chunks(self, service, mock_embedding, mock_repo):
        chunks = [_make_chunk("VPD Guide"), _make_chunk("EC Guide", score=0.8)]
        mock_repo.hybrid_search.return_value = chunks

        result = service.search("What is VPD?", top_k=3)

        assert len(result) == 2
        assert result[0].title == "VPD Guide"
        mock_embedding.embed.assert_called_once_with("What is VPD?", prefix="query: ")
        mock_repo.hybrid_search.assert_called_once()

    def test_search_empty(self, service, mock_repo):
        mock_repo.hybrid_search.return_value = []

        result = service.search("nonexistent topic")

        assert result == []


class TestAsk:
    def test_ask_returns_answer(self, service, mock_repo, mock_llm):
        chunks = [_make_chunk("VPD Guide")]
        mock_repo.hybrid_search.return_value = chunks
        mock_llm.generate.return_value = LlmResponse(
            content="VPD is the vapor pressure deficit.",
            model="claude-sonnet-4-20250514",
            usage={"prompt_tokens": 200, "completion_tokens": 30},
        )

        answer = service.ask("What is VPD?", top_k=3)

        assert answer.answer == "VPD is the vapor pressure deficit."
        assert answer.model == "claude-sonnet-4-20250514"
        assert len(answer.sources) == 1
        assert answer.sources[0].title == "VPD Guide"
        assert answer.usage["prompt_tokens"] == 200

        # Verify the LLM was called with system prompt and context
        call_args = mock_llm.generate.call_args
        assert "VPD Guide" in call_args[0][1]  # user_message contains context title
        assert call_args[1]["max_tokens"] == 512
        assert call_args[1]["temperature"] == 0.2

    def test_ask_no_context_returns_no_knowledge(self, service, mock_repo, mock_llm):
        mock_repo.hybrid_search.return_value = []

        answer = service.ask("Something completely unknown")

        assert "No relevant knowledge" in answer.answer
        assert answer.model == "none"
        assert answer.sources == []
        mock_llm.generate.assert_not_called()

    def test_ask_multiple_sources(self, service, mock_repo, mock_llm):
        chunks = [
            _make_chunk("Guide A", score=0.95),
            _make_chunk("Guide B", score=0.85),
            _make_chunk("Guide C", score=0.75),
        ]
        mock_repo.hybrid_search.return_value = chunks
        mock_llm.generate.return_value = LlmResponse(
            content="Combined answer.",
            model="llama3",
            usage={"prompt_tokens": 500, "completion_tokens": 50},
        )

        answer = service.ask("Complex question", top_k=3)

        assert len(answer.sources) == 3


class TestLanguageParams:
    def test_search_with_doc_language_passes_to_repo(self, service, mock_repo):
        mock_repo.hybrid_search.return_value = []

        service.search("test", doc_language="en")

        call_kwargs = mock_repo.hybrid_search.call_args
        assert call_kwargs[1]["language"] == "en"

    def test_search_default_doc_language(self, service, mock_repo):
        mock_repo.hybrid_search.return_value = []

        service.search("test")

        call_kwargs = mock_repo.hybrid_search.call_args
        assert call_kwargs[1]["language"] == "de"

    def test_ask_with_prompt_language_de_uses_german_prompt(
        self,
        service,
        mock_repo,
        mock_llm,
    ):
        mock_repo.hybrid_search.return_value = [_make_chunk()]
        mock_llm.generate.return_value = LlmResponse(
            content="Antwort",
            model="test",
            usage={},
        )

        service.ask("Was ist VPD?", prompt_language="de")

        system_prompt = mock_llm.generate.call_args[0][0]
        assert system_prompt == _SYSTEM_PROMPTS["de"]
        assert "Antworte auf Deutsch" in system_prompt

    def test_ask_with_prompt_language_en_uses_english_prompt(
        self,
        service,
        mock_repo,
        mock_llm,
    ):
        mock_repo.hybrid_search.return_value = [_make_chunk()]
        mock_llm.generate.return_value = LlmResponse(
            content="Answer",
            model="test",
            usage={},
        )

        service.ask("What is VPD?", prompt_language="en")

        system_prompt = mock_llm.generate.call_args[0][0]
        assert system_prompt == _SYSTEM_PROMPTS["en"]
        assert "SAME LANGUAGE" in system_prompt

    def test_ask_defaults_from_constructor(self, mock_embedding, mock_repo, mock_llm):
        mock_repo.hybrid_search.return_value = [_make_chunk()]
        mock_llm.generate.return_value = LlmResponse(
            content="Answer",
            model="test",
            usage={},
        )

        svc = KnowledgeService(
            embedding_engine=mock_embedding,
            chunk_repo=mock_repo,
            llm_adapter=mock_llm,
            default_doc_language="en",
            default_prompt_language="en",
        )
        svc.ask("test question")

        # Doc language default should be "en"
        assert mock_repo.hybrid_search.call_args[1]["language"] == "en"
        # Prompt language default should be "en"
        system_prompt = mock_llm.generate.call_args[0][0]
        assert system_prompt == _SYSTEM_PROMPTS["en"]

    def test_ask_doc_language_override(self, service, mock_repo, mock_llm):
        mock_repo.hybrid_search.return_value = [_make_chunk()]
        mock_llm.generate.return_value = LlmResponse(
            content="Answer",
            model="test",
            usage={},
        )

        service.ask("test", doc_language="all")

        assert mock_repo.hybrid_search.call_args[1]["language"] == "all"


class TestBuildContext:
    def test_context_format(self):
        chunks = [_make_chunk("First"), _make_chunk("Second")]
        context = KnowledgeService._build_context(chunks)

        assert "[1] First" in context
        assert "[2] Second" in context
        assert "---" in context

    def test_empty_context(self):
        context = KnowledgeService._build_context([])
        assert context == ""
