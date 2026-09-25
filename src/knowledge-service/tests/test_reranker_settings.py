"""#1751: reranker budget defaults and their wiring from Settings into the running service."""

import asyncio

from app import main
from app.config import RERANK_SCORED_CHARS_BUDGET, Settings


class TestRerankerSettingsDefaults:
    def test_initial_k_defaults_to_15(self, monkeypatch):
        monkeypatch.delenv("RERANKER_INITIAL_K", raising=False)
        assert Settings().reranker_initial_k == 15

    def test_max_document_chars_defaults_to_500(self, monkeypatch):
        monkeypatch.delenv("RERANKER_MAX_DOCUMENT_CHARS", raising=False)
        assert Settings().reranker_max_document_chars == 500

    def test_the_defaults_fit_the_measured_budget(self, monkeypatch):
        monkeypatch.delenv("RERANKER_INITIAL_K", raising=False)
        monkeypatch.delenv("RERANKER_MAX_DOCUMENT_CHARS", raising=False)
        settings = Settings()
        assert settings.reranker_initial_k * settings.reranker_max_document_chars <= RERANK_SCORED_CHARS_BUDGET

    def test_max_document_chars_is_read_from_the_environment(self, monkeypatch):
        monkeypatch.setenv("RERANKER_MAX_DOCUMENT_CHARS", "640")
        assert Settings().reranker_max_document_chars == 640


class _FakeVectorDbConnection:
    def __init__(self, config) -> None:
        self.config = config

    def connect(self) -> object:
        return object()

    def close(self) -> None:
        pass


class TestLifespanWiring:
    """Drives the real lifespan with the database and LLM replaced by stand-ins."""

    def test_lifespan_builds_the_reranker_from_settings(self, monkeypatch):
        monkeypatch.setattr(main, "VectorDbConnection", _FakeVectorDbConnection)
        monkeypatch.setattr(main, "run_migrations", lambda pool, directory: None)
        monkeypatch.setattr(main, "create_llm_adapter", lambda settings: object())
        monkeypatch.setattr(main.settings, "debug", True)
        monkeypatch.setattr(main.settings, "reranker_url", "http://reranker:8081")
        monkeypatch.setattr(main.settings, "reranker_initial_k", 7)
        monkeypatch.setattr(main.settings, "reranker_max_document_chars", 123, raising=False)
        monkeypatch.setattr(main, "_service", None)
        monkeypatch.setattr(main, "_ingestor", None)
        monkeypatch.setattr(main, "_vec_conn", None)

        seen: dict = {}

        async def run() -> None:
            async with main.lifespan(main.app):
                service = main._service
                assert service is not None
                seen["initial_k"] = service._reranker_initial_k
                seen["reranker"] = service._reranker

        asyncio.run(run())

        assert seen["initial_k"] == 7
        assert seen["reranker"].available is True
        assert seen["reranker"]._max_document_chars == 123
