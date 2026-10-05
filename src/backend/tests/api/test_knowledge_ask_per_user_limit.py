"""#2110 class sweep — ``POST /api/v1/knowledge/ask`` is an LLM call and carries a per-user limit.

The raw knowledge-service proxy is mounted whenever ``KNOWLEDGE_SERVICE_ENABLED``
is on and answers any authenticated account with an LLM call. The #2109 guard
cannot see it (the router is not mounted under the test defaults), so its
limit is measured here, through the production principal resolution.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi.errors import RateLimitExceeded

from app.api.v1.auth.router import limiter
from app.api.v1.knowledge.router import router as knowledge_router
from app.common.dependencies import get_auth_provider, get_knowledge_client
from app.config.settings import settings
from tests.api.test_expensive_routes_per_user_limit import _TokenAuth


def _client(client_double: MagicMock) -> TestClient:
    from app.main import app as production_app

    app = FastAPI()
    app.include_router(knowledge_router, prefix="/api/v1")
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, production_app.exception_handlers[RateLimitExceeded])
    app.dependency_overrides[get_auth_provider] = _TokenAuth
    app.dependency_overrides[get_knowledge_client] = lambda: client_double
    return TestClient(app)


def _ask(client: TestClient, token: str) -> int:
    return client.post(
        "/api/v1/knowledge/ask",
        json={"question": "What is VPD?"},
        headers={"Authorization": f"Bearer {token}"},
    ).status_code


def test_the_call_past_the_per_minute_budget_is_refused_per_account() -> None:
    knowledge = MagicMock()
    knowledge.ask.return_value = {"answer": "a", "model": "m", "usage": {}, "sources": []}
    client = _client(knowledge)
    budget = int(settings.rate_limit_inference.split("/")[0])

    assert [_ask(client, "token-anna") for _ in range(budget)] == [200] * budget
    assert _ask(client, "token-anna") == 429
    assert knowledge.ask.call_count == budget
    # Another account behind the same address keeps its own budget.
    assert _ask(client, "token-ben") == 200
