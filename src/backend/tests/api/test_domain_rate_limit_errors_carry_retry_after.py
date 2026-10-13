"""#2110 — a 429 raised as a domain ``RateLimitError`` carries ``Retry-After``.

#2109 documented that every 429 carries the header, and wired it for slowapi's
refusals only. A ``RateLimitError`` (identification and contribution day caps,
the API-key limiter, and since #2110 the AI budget) reached the client through
``app_error_handler``, which put the wait into the message text and nowhere
else — measured with this test against the unchanged handler.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.common.error_handlers import app_error_handler
from app.common.exceptions import AiBudgetExceededError, KamerplanterError, NotFoundError, RateLimitError


def _client() -> TestClient:
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]

    @app.get("/day-cap")
    def _day_cap() -> None:
        raise RateLimitError("identify", retry_after=123)

    @app.get("/ai-budget")
    def _ai_budget() -> None:
        raise AiBudgetExceededError("tenant_calls", 4567)

    @app.get("/missing")
    def _missing() -> None:
        raise NotFoundError("PlantInstance", "p-1")

    return TestClient(app)


def test_a_domain_429_carries_retry_after() -> None:
    resp = _client().get("/day-cap")
    assert resp.status_code == 429
    assert resp.headers["Retry-After"] == "123"


def test_the_ai_budget_429_carries_the_wait_until_the_day_ends() -> None:
    resp = _client().get("/ai-budget")
    assert resp.status_code == 429
    assert resp.headers["Retry-After"] == "4567"
    assert resp.json()["error_code"] == "AI_BUDGET_EXCEEDED"


def test_other_errors_carry_no_retry_after() -> None:
    resp = _client().get("/missing")
    assert resp.status_code == 404
    assert "Retry-After" not in resp.headers
