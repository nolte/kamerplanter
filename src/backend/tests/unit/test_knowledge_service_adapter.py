"""REQ-031 §4.1 — unit tests for the async ``HttpKnowledgeServiceAdapter``.

Covers the happy path, the retry-on-5xx behaviour and the circuit breaker,
driving a real ``httpx.AsyncClient`` over an in-memory ``MockTransport`` (no
network, no live Knowledge Service).
"""

from __future__ import annotations

import httpx
import pytest

from app.data_access.external.knowledge_service_adapter import (
    HttpKnowledgeServiceAdapter,
    KnowledgeServiceUnavailableError,
    _CircuitBreaker,
)
from app.domain.interfaces.knowledge_service import QuestionContext


def _adapter(handler, *, max_retries: int = 2, breaker: _CircuitBreaker | None = None):
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://ks")
    return HttpKnowledgeServiceAdapter(
        base_url="http://ks",
        service_token="secret-token",
        max_retries=max_retries,
        breaker=breaker,
        client=client,
    )


async def test_ask_happy_path_maps_response() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(
            200,
            json={
                "answer": "VPD is the vapour pressure deficit.",
                "question_type": "factual",
                "model": "gemma3:12b",
                "usage": {"tokens": 10},
                "sources": [
                    {
                        "source_key": "umwelt/vpd",
                        "source_type": "rag",
                        "title": "VPD",
                        "content": "…",
                        "score": 0.9,
                        "language": "de",
                    }
                ],
            },
        )

    adapter = _adapter(handler)
    result = await adapter.ask("What is VPD?", context=QuestionContext(species="Cannabis sativa"))

    assert result.answer.startswith("VPD")
    assert result.model_name == "gemma3:12b"
    assert len(result.sources) == 1
    assert result.sources[0].source_key == "umwelt/vpd"
    # Bearer token forwarded (AP-4).
    assert calls[0].headers["Authorization"] == "Bearer secret-token"


async def test_ask_retries_on_5xx_then_trips_breaker() -> None:
    attempts = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["n"] += 1
        return httpx.Response(503, json={"detail": "unavailable"})

    breaker = _CircuitBreaker(threshold=3, window_s=60.0, cooldown_s=60.0)
    adapter = _adapter(handler, max_retries=2, breaker=breaker)

    with pytest.raises(KnowledgeServiceUnavailableError):
        await adapter.ask("Why?")

    # Initial call + 2 retries == 3 attempts.
    assert attempts["n"] == 3
    # Three failures inside the window trip the breaker.
    assert breaker.is_open() is True
    # A tripped breaker reports the service unhealthy without any HTTP call.
    assert await adapter.health_check() is False


async def test_open_breaker_short_circuits_without_calling() -> None:
    called = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        called["n"] += 1
        return httpx.Response(200, json={"ready": True})

    breaker = _CircuitBreaker(threshold=1, window_s=60.0, cooldown_s=60.0)
    breaker.record_failure()  # trip immediately
    adapter = _adapter(handler, breaker=breaker)

    with pytest.raises(KnowledgeServiceUnavailableError):
        await adapter.search("anything")
    assert called["n"] == 0


async def test_success_resets_failure_history() -> None:
    breaker = _CircuitBreaker(threshold=3, window_s=60.0, cooldown_s=60.0)
    breaker.record_failure()
    breaker.record_failure()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": []})

    adapter = _adapter(handler, breaker=breaker)
    await adapter.search("query")

    # A success clears the two prior failures so the breaker stays closed.
    assert breaker.is_open() is False


async def test_4xx_degrades_without_leaking_token(caplog) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json={"detail": "bad"})

    breaker = _CircuitBreaker(threshold=3, window_s=60.0, cooldown_s=60.0)
    adapter = _adapter(handler, breaker=breaker)

    # SEC-004: a 4xx must degrade to the token-free unavailable error, NOT to an
    # ``httpx.HTTPStatusError`` whose request still carries the bearer token.
    with pytest.raises(KnowledgeServiceUnavailableError) as excinfo:
        await adapter.ask("bad question")

    # The breaker stays closed (a caller error is not a service outage) …
    assert breaker.is_open() is False
    # … and neither the exception nor its cause chain leaks the bearer token.
    chain: list[BaseException] = []
    exc: BaseException | None = excinfo.value
    while exc is not None:
        chain.append(exc)
        exc = exc.__cause__ or exc.__context__
    rendered = " ".join(str(e) for e in chain)
    assert "secret-token" not in rendered
    assert "Authorization" not in rendered
    assert "422" in str(excinfo.value)
    assert "secret-token" not in caplog.text


async def test_4xx_on_search_degrades_to_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"detail": "bad query"})

    breaker = _CircuitBreaker(threshold=3, window_s=60.0, cooldown_s=60.0)
    adapter = _adapter(handler, breaker=breaker)

    with pytest.raises(KnowledgeServiceUnavailableError):
        await adapter.search("bad")
    assert breaker.is_open() is False


async def test_health_check_reads_ready_flag() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/health"
        return httpx.Response(200, json={"ready": True})

    adapter = _adapter(handler)
    assert await adapter.health_check() is True
