"""Unit tests for the RerankerEngine."""

import json

import httpx
import pytest

from app.reranker import RerankerEngine
from app.vectordb.repository import VectorChunk


def _make_chunk(key: str, title: str, content: str, score: float = 0.5) -> VectorChunk:
    return VectorChunk(
        source_key=key,
        source_type="care_rule",
        title=title,
        content=content,
        score=score,
        metadata={},
        language="de",
    )


class TestRerankerDisabled:
    """Tests for when reranker is not configured."""

    def test_not_available_when_url_is_none(self):
        engine = RerankerEngine(None)
        assert engine.available is False

    def test_rerank_returns_truncated_chunks_when_disabled(self):
        engine = RerankerEngine(None)
        chunks = [_make_chunk(f"k{i}", f"Title {i}", f"Content {i}") for i in range(10)]
        result = engine.rerank("query", chunks, top_k=3)
        assert len(result) == 3
        assert result[0].source_key == "k0"

    def test_rerank_returns_empty_list_for_empty_input(self):
        engine = RerankerEngine(None)
        assert engine.rerank("query", [], top_k=5) == []


class TestRerankerEnabled:
    """Tests for when reranker service is available."""

    def test_available_when_url_is_set(self):
        engine = RerankerEngine("http://reranker:8081")
        assert engine.available is True

    def test_rerank_calls_service_and_reorders(self, monkeypatch):
        """Mock the HTTP call and verify chunks are reordered by reranker score."""
        chunks = [
            _make_chunk("low", "Low relevance", "Not very relevant", score=0.9),
            _make_chunk("high", "High relevance", "Very relevant", score=0.3),
            _make_chunk("mid", "Mid relevance", "Somewhat relevant", score=0.6),
        ]

        mock_response = {
            "results": [
                {"index": 1, "score": 0.95, "text": "High relevance\nVery relevant"},
                {"index": 2, "score": 0.72, "text": "Mid relevance\nSomewhat relevant"},
            ],
            "model": "bge-reranker-v2-m3",
        }

        captured_body = {}

        def fake_post(url, *, json=None, timeout=None):
            captured_body.update(json or {})
            resp = httpx.Response(200, json=mock_response, request=httpx.Request("POST", url))
            return resp

        monkeypatch.setattr(httpx, "post", fake_post)

        engine = RerankerEngine("http://reranker:8081")
        result = engine.rerank("test query", chunks, top_k=2)

        assert captured_body["query"] == "test query"
        assert len(captured_body["documents"]) == 3
        assert captured_body["top_k"] == 2

        assert len(result) == 2
        assert result[0].source_key == "high"
        assert result[0].score == pytest.approx(0.95)
        assert result[1].source_key == "mid"
        assert result[1].score == pytest.approx(0.72)

    def test_rerank_falls_back_on_http_error(self):
        """On HTTP error, return original chunks truncated to top_k."""
        chunks = [_make_chunk(f"k{i}", f"Title {i}", f"Content {i}") for i in range(10)]

        def mock_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, json={"error": "internal"})

        engine = RerankerEngine("http://reranker:8081")

        # The real httpx.post will fail to connect — that's the fallback we're testing
        result = engine.rerank("query", chunks, top_k=3)
        # Should fall back to truncated original list
        assert len(result) == 3
        assert result[0].source_key == "k0"
