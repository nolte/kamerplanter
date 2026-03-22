"""Tests for request-ID middleware (NFR-007 tracing)."""

import uuid

import pytest
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient

from app.common.middleware import request_id_middleware


@pytest.fixture
def _app() -> FastAPI:
    """Minimal FastAPI app with request-ID middleware."""
    app = FastAPI()

    @app.middleware("http")
    async def _mid(request: Request, call_next):  # type: ignore[type-arg]
        return await request_id_middleware(request, call_next)

    @app.get("/ping")
    async def ping() -> dict[str, str]:
        return {"status": "ok"}

    return app


@pytest.fixture
async def client(_app: FastAPI) -> AsyncClient:
    transport = ASGITransport(app=_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_generates_request_id_when_absent(client: AsyncClient) -> None:
    """A new UUID4 is generated when no X-Request-ID header is sent."""
    resp = await client.get("/ping")
    assert resp.status_code == 200
    request_id = resp.headers.get("X-Request-ID")
    assert request_id is not None
    # Must be a valid UUID4
    parsed = uuid.UUID(request_id, version=4)
    assert str(parsed) == request_id


@pytest.mark.asyncio
async def test_reuses_valid_client_request_id(client: AsyncClient) -> None:
    """A valid UUID4 from the client is passed through."""
    client_id = str(uuid.uuid4())
    resp = await client.get("/ping", headers={"X-Request-ID": client_id})
    assert resp.status_code == 200
    assert resp.headers["X-Request-ID"] == client_id


@pytest.mark.asyncio
async def test_rejects_invalid_request_id(client: AsyncClient) -> None:
    """An invalid X-Request-ID is replaced with a server-generated UUID4."""
    resp = await client.get("/ping", headers={"X-Request-ID": "not-a-uuid"})
    assert resp.status_code == 200
    request_id = resp.headers["X-Request-ID"]
    assert request_id != "not-a-uuid"
    # Must be a valid UUID4
    uuid.UUID(request_id, version=4)


@pytest.mark.asyncio
async def test_rejects_empty_request_id(client: AsyncClient) -> None:
    """An empty X-Request-ID is treated as absent."""
    resp = await client.get("/ping", headers={"X-Request-ID": ""})
    assert resp.status_code == 200
    request_id = resp.headers["X-Request-ID"]
    assert request_id != ""
    uuid.UUID(request_id, version=4)


@pytest.mark.asyncio
async def test_each_request_gets_unique_id(client: AsyncClient) -> None:
    """Consecutive requests without client ID get distinct IDs."""
    resp1 = await client.get("/ping")
    resp2 = await client.get("/ping")
    assert resp1.headers["X-Request-ID"] != resp2.headers["X-Request-ID"]
