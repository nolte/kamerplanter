"""Unit tests for the RerankerEngine."""

import httpx
import pytest
from structlog.testing import capture_logs

from app import reranker as reranker_module
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

    def test_rerank_falls_back_when_the_service_is_busy(self, monkeypatch):
        """A 503 busy/timeout from the reranker (its bounded lock wait / deadline) degrades to no reranking."""
        chunks = [_make_chunk(f"k{i}", f"Title {i}", f"Content {i}") for i in range(10)]

        def busy_post(url, **kwargs):
            return httpx.Response(
                503,
                json={"status": "busy"},
                headers={"Retry-After": "20"},
                request=httpx.Request("POST", url),
            )

        monkeypatch.setattr(httpx, "post", busy_post)

        result = RerankerEngine("http://reranker:8081").rerank("query", chunks, top_k=3)

        assert [chunk.source_key for chunk in result] == ["k0", "k1", "k2"]


# --------------------------------------------------------------------------
# Fallback observability (#1751): every degradation names its reason
# --------------------------------------------------------------------------

_URL = "http://reranker:8081"
_TOP_K = 3
_CHUNK_COUNT = 6


def _chunks() -> list[VectorChunk]:
    return [_make_chunk(f"k{i}", f"Title {i}", f"Content {i}") for i in range(_CHUNK_COUNT)]


def _returning(response_factory):
    """A fake ``httpx.post`` that returns the response; the code under test calls ``raise_for_status``."""

    def fake_post(url, **kwargs):
        return response_factory(httpx.Request("POST", url))

    return fake_post


def _raising(exc_factory):
    """A fake ``httpx.post`` that raises what the real client raises before any response exists."""

    def fake_post(url, **kwargs):
        raise exc_factory(httpx.Request("POST", url))

    return fake_post


def _fallback_events(logs: list[dict]) -> list[dict]:
    return [entry for entry in logs if entry["event"] == "reranker_fallback"]


def _assert_single_fallback(logs: list[dict], *, reason: str, status_code: int | None) -> dict:
    events = _fallback_events(logs)
    assert len(events) == 1, events
    event = events[0]
    assert event["log_level"] == "warning"
    assert event["reason"] == reason
    assert event["reason"] in reranker_module.RERANKER_FALLBACK_REASONS
    assert event["status_code"] == status_code
    assert event["documents"] == _CHUNK_COUNT
    assert isinstance(event["elapsed_s"], float)
    assert event["elapsed_s"] >= 0.0
    assert event["elapsed_s"] == round(event["elapsed_s"], 2)
    assert isinstance(event["error"], str)
    assert event["error"]
    return event


_FALLBACK_CASES = [
    pytest.param(
        _returning(lambda req: httpx.Response(503, json={"status": "timeout"}, request=req)),
        "deadline",
        503,
        id="deadline",
    ),
    pytest.param(
        _returning(
            lambda req: httpx.Response(503, json={"status": "busy"}, headers={"Retry-After": "10"}, request=req)
        ),
        "busy",
        503,
        id="busy",
    ),
    pytest.param(
        _returning(lambda req: httpx.Response(503, json={"status": "loading"}, request=req)),
        "loading",
        503,
        id="loading",
    ),
    pytest.param(
        _returning(lambda req: httpx.Response(500, json={"error": "internal"}, request=req)),
        "http_status",
        500,
        id="http_status-500",
    ),
    pytest.param(
        _returning(lambda req: httpx.Response(422, json={"detail": "bad"}, request=req)),
        "http_status",
        422,
        id="http_status-422",
    ),
    pytest.param(
        _returning(lambda req: httpx.Response(503, json={"status": "maintenance"}, request=req)),
        "http_status",
        503,
        id="http_status-503-unknown-status",
    ),
    pytest.param(
        _returning(lambda req: httpx.Response(503, text="<html>Service Unavailable</html>", request=req)),
        "http_status",
        503,
        id="http_status-503-unparsable-body",
    ),
    pytest.param(
        _returning(lambda req: httpx.Response(503, json=["timeout"], request=req)),
        "http_status",
        503,
        id="http_status-503-non-object-body",
    ),
    pytest.param(
        _raising(lambda req: httpx.ReadTimeout("timed out", request=req)),
        "client_timeout",
        None,
        id="client_timeout-read",
    ),
    pytest.param(
        _raising(lambda req: httpx.ConnectTimeout("connect timed out", request=req)),
        "client_timeout",
        None,
        id="client_timeout-connect",
    ),
    pytest.param(
        _raising(lambda req: httpx.ConnectError("connection refused", request=req)),
        "transport",
        None,
        id="transport-connect-error",
    ),
    pytest.param(
        _raising(lambda req: httpx.RemoteProtocolError("peer closed connection", request=req)),
        "transport",
        None,
        id="transport-protocol-error",
    ),
    pytest.param(
        _returning(lambda req: httpx.Response(200, text="not json", request=req)),
        "malformed_response",
        200,
        id="malformed-not-json",
    ),
    pytest.param(
        _returning(lambda req: httpx.Response(200, json={"model": "bge"}, request=req)),
        "malformed_response",
        200,
        id="malformed-no-results",
    ),
    pytest.param(
        _returning(lambda req: httpx.Response(200, json={"results": "k1"}, request=req)),
        "malformed_response",
        200,
        id="malformed-results-not-a-list",
    ),
    pytest.param(
        _returning(lambda req: httpx.Response(200, json={"results": [{"score": 0.9}]}, request=req)),
        "malformed_response",
        200,
        id="malformed-entry-without-index",
    ),
    pytest.param(
        _returning(
            lambda req: httpx.Response(200, json={"results": [{"index": _CHUNK_COUNT, "score": 0.9}]}, request=req)
        ),
        "malformed_response",
        200,
        id="malformed-index-out-of-range",
    ),
    pytest.param(
        _returning(lambda req: httpx.Response(200, json={"results": [{"index": -1, "score": 0.9}]}, request=req)),
        "malformed_response",
        200,
        id="malformed-negative-index",
    ),
    pytest.param(
        _returning(lambda req: httpx.Response(200, json={"results": [{"index": 1}]}, request=req)),
        "malformed_response",
        200,
        id="malformed-entry-without-score",
    ),
    pytest.param(
        _returning(lambda req: httpx.Response(200, json=[{"index": 1, "score": 0.9}], request=req)),
        "malformed_response",
        200,
        id="malformed-body-not-an-object",
    ),
]


class TestRerankerFallbackReason:
    """Each degradation logs exactly one ``reranker_fallback`` with a countable ``reason``."""

    @pytest.mark.parametrize(("fake_post", "reason", "status_code"), _FALLBACK_CASES)
    def test_fallback_names_its_reason_and_keeps_the_original_order(self, monkeypatch, fake_post, reason, status_code):
        chunks = _chunks()
        monkeypatch.setattr(httpx, "post", fake_post)

        with capture_logs() as logs:
            result = RerankerEngine(_URL).rerank("query", chunks, top_k=_TOP_K)

        _assert_single_fallback(logs, reason=reason, status_code=status_code)
        assert result == chunks[:_TOP_K]
        assert [chunk.source_key for chunk in result] == ["k0", "k1", "k2"]
        assert not [entry for entry in logs if entry["event"] == "reranker_complete"]

    def test_every_reason_of_the_closed_set_is_reachable(self):
        """The constant is the single source of truth; the parametrized cases cover all of it."""
        covered = {case.values[1] for case in _FALLBACK_CASES}
        assert covered == set(reranker_module.RERANKER_FALLBACK_REASONS)
        assert set(reranker_module.RERANKER_FALLBACK_REASONS) == {
            "deadline",
            "busy",
            "loading",
            "http_status",
            "client_timeout",
            "transport",
            "malformed_response",
        }


class TestRerankerCompleteLog:
    def test_complete_log_carries_elapsed_seconds(self, monkeypatch):
        chunks = _chunks()
        body = {"results": [{"index": 2, "score": 0.9}, {"index": 0, "score": 0.4}]}
        monkeypatch.setattr(httpx, "post", _returning(lambda req: httpx.Response(200, json=body, request=req)))

        with capture_logs() as logs:
            result = RerankerEngine(_URL).rerank("query", chunks, top_k=2)

        assert [chunk.source_key for chunk in result] == ["k2", "k0"]
        assert not _fallback_events(logs)
        complete = [entry for entry in logs if entry["event"] == "reranker_complete"]
        assert len(complete) == 1
        assert isinstance(complete[0]["elapsed_s"], float)
        assert complete[0]["elapsed_s"] >= 0.0
        assert complete[0]["elapsed_s"] == round(complete[0]["elapsed_s"], 2)


class TestRerankerDocumentTruncation:
    """#1751: each document is cut client-side so the sidecar finishes inside its deadline."""

    def test_documents_sent_are_cut_to_max_document_chars(self, monkeypatch):
        chunks = [
            _make_chunk("long", "Title", "x" * 5000),
            _make_chunk("short", "Short", "tiny"),
        ]
        captured: dict = {}

        def fake_post(url, *, json=None, timeout=None):
            captured.update(json or {})
            return httpx.Response(
                200,
                json={"results": [{"index": 0, "score": 0.9}, {"index": 1, "score": 0.1}]},
                request=httpx.Request("POST", url),
            )

        monkeypatch.setattr(httpx, "post", fake_post)

        engine = RerankerEngine("http://reranker:8081", max_document_chars=100)
        result = engine.rerank("query", chunks, top_k=2)

        assert captured["documents"] == [("Title\n" + "x" * 5000)[:100], "Short\ntiny"]
        assert len(captured["documents"][0]) == 100
        # Truncation only changes what is scored: the answer keeps the full chunk.
        assert result[0].source_key == "long"
        assert result[0].content == "x" * 5000
        assert result[1].content == "tiny"

    def test_the_fallback_keeps_the_full_content(self, monkeypatch):
        chunks = [_make_chunk("long", "Title", "y" * 2000)]

        def fake_post(url, *, json=None, timeout=None):
            return httpx.Response(503, json={"status": "timeout"}, request=httpx.Request("POST", url))

        monkeypatch.setattr(httpx, "post", fake_post)

        result = RerankerEngine("http://reranker:8081", max_document_chars=50).rerank("q", chunks, top_k=1)

        assert result[0].content == "y" * 2000

    def test_the_default_cut_is_500_characters(self, monkeypatch):
        captured: dict = {}

        def fake_post(url, *, json=None, timeout=None):
            captured.update(json or {})
            return httpx.Response(200, json={"results": []}, request=httpx.Request("POST", url))

        monkeypatch.setattr(httpx, "post", fake_post)

        RerankerEngine("http://reranker:8081").rerank("q", [_make_chunk("k", "T", "z" * 3000)], top_k=1)

        assert len(captured["documents"][0]) == 500

    @pytest.mark.parametrize("value", [0, -1])
    def test_a_non_positive_cut_is_refused(self, value):
        with pytest.raises(ValueError, match="max_document_chars"):
            RerankerEngine("http://reranker:8081", max_document_chars=value)
