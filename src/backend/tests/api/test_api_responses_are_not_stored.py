"""MT-044 (#2144): a ``/api/v1/**`` JSON answer carries ``Cache-Control: no-store``.

Tenant-private JSON (plants, tasks, members, the Art. 15 export) was sent without
any caching directive; only HSTS and the other security headers were set. A
shared proxy or the browser's back/forward and disk cache was then free to keep
a copy of a member's view after logout or a tenant switch.

The rule is a default, not an override: a route that decides its own caching
keeps it. The attachment downloads answer ``private, max-age=86400`` on purpose
(images re-used across pages), the pest reference images ``public`` and the SSE
stream ``no-cache`` — the middleware only fills in a header that is absent.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
    from app.main import app, security_headers_middleware


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_a_real_api_v1_route_answer_is_not_stored(client: TestClient) -> None:
    """A real ``/api/v1`` route through the real middleware stack (the liveness probe is datastore-free)."""
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"


def _request(path: str) -> Request:
    return Request({"type": "http", "method": "GET", "path": path, "headers": [], "query_string": b""})


async def _answer(path: str, response: Response) -> Response:
    async def call_next(_request: Request) -> Response:
        return response

    return await security_headers_middleware(_request(path), call_next)


async def test_an_api_v1_answer_without_a_directive_gets_no_store() -> None:
    answered = await _answer("/api/v1/t/a/tasks", JSONResponse({"x": 1}))
    assert answered.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    "directive",
    ["private, max-age=86400", "public, max-age=86400", "no-cache"],
    ids=["attachment", "pest-image", "sse"],
)
async def test_a_route_that_chose_its_own_directive_keeps_it(directive: str) -> None:
    answered = await _answer("/api/v1/t/a/attachments/x/download", Response(b"x", headers={"Cache-Control": directive}))
    assert answered.headers["cache-control"] == directive


@pytest.mark.parametrize("path", ["/api/health", "/metrics", "/docs"])
async def test_a_path_outside_api_v1_is_left_alone(path: str) -> None:
    answered = await _answer(path, JSONResponse({"x": 1}))
    assert "cache-control" not in answered.headers
