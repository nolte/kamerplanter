"""A limited ``async`` route does not run its limit check on the event loop (#2048).

slowapi runs the limit check **synchronously** inside the wrapper of an
``async def`` route. With the Valkey-backed storage of #2045 every check of such
a route is a network round trip on the event loop — up to the 0.5 s socket
timeout when the storage hangs — and every other request of the process waits
behind it. Measured before the fix through the real app (``httpx`` against the
ASGI app, the shared limiter's storage answering in 0.3 s): three concurrent
``POST /public/ai/ask`` held five requests to the unrelated async route
``GET /public/ai/health``, due 20 ms later, for 0.935 s each — 0.007 s alone.

The fix: the shared limiter (``app.common.rate_limit.OffLoopLimiter``) runs the
check of an ``async`` route through ``run_in_threadpool``, where every ``def``
route already runs it. ``GET /api/health`` counts in process memory only and
never reaches the shared storage.

The three async limited routes are driven here through the real application —
``/public/ai/*`` through the light-mode mount (:func:`light_app`), because the
production app the suite imports is full mode, where that router does not
exist (REQ-031 §5.3); the class — every async limited route, whichever limiter it uses — is held by
``tests/unit/guards/test_async_limited_routes_check_off_the_loop.py``.
"""

from __future__ import annotations

import asyncio
import threading
import time
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import FastAPI

from app.api.v1.auth.router import limiter
from app.common.auth import get_current_tenant, get_current_user
from app.common.dependencies import get_ai_assistant_service, get_notification_service, get_privacy_service
from app.common.enums import TenantRole
from app.config.settings import settings
from app.domain.models.privacy import DataExportRequest
from app.domain.models.tenant_context import TenantContext

#: How long the doubled shared storage takes to answer one limit check.
_STORAGE_DELAY_S = 1.0

#: An unrelated request that waits behind a blocked loop takes at least
#: :data:`_STORAGE_DELAY_S`; one that does not answers in milliseconds. Half the
#: delay keeps an order of magnitude away from both.
_UNBLOCKED_BOUND_S = _STORAGE_DELAY_S / 2


class _StorageCalls:
    """Records the thread every shared-storage ``incr`` ran on."""

    def __init__(self) -> None:
        self.threads: list[int] = []


@pytest.fixture
def storage_calls(monkeypatch: pytest.MonkeyPatch) -> _StorageCalls:
    calls = _StorageCalls()
    original: Callable[..., int] = limiter._storage.incr

    def _incr(*args: Any, **kwargs: Any) -> int:
        calls.threads.append(threading.get_ident())
        time.sleep(_STORAGE_DELAY_S)  # a socket round trip blocks its thread exactly like this
        return original(*args, **kwargs)

    monkeypatch.setattr(limiter._storage, "incr", _incr)
    return calls


@pytest.fixture
def app_under_test(monkeypatch: pytest.MonkeyPatch) -> Iterator[Any]:
    with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
        from app.main import app

    monkeypatch.setattr(settings, "ai_features_enabled", True)

    ai = MagicMock()
    ai.ask_public = AsyncMock(
        return_value=MagicMock(
            answer_text="a",
            sources=[],
            language="de",
            language_mismatch_warning=False,
            uses_tenant_data=False,
            uses_cloud_provider=False,
            confidence="high",
            model_name="m",
            provider_type="local",
            kb_version="1",
            generated_at=datetime.now(UTC),
        )
    )
    ai.health_check = AsyncMock(return_value=True)

    notifications = MagicMock()
    notifications.send_test = AsyncMock(return_value={"status": "delivered", "success": True, "error": None})

    async def _bytes():  # noqa: ANN202 - async generator
        yield b"{}"

    async def _open(user_key: str, export_key: str):  # noqa: ANN202 - tuple of model and stream
        return DataExportRequest(key=export_key, user_key=user_key, status="completed"), _bytes()

    privacy = MagicMock()
    privacy.open_export_bundle = AsyncMock(side_effect=_open)

    user = MagicMock()
    user.key = "u-1"
    user.api_key_tenant_scope = None

    app.dependency_overrides[get_ai_assistant_service] = lambda: ai
    app.dependency_overrides[get_notification_service] = lambda: notifications
    app.dependency_overrides[get_privacy_service] = lambda: privacy
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_current_tenant] = lambda: TenantContext(
        tenant_key="tenant-a", tenant_slug="garden", user_key="u-1", role=TenantRole.GROWER
    )
    # tests/api/conftest.py restores the overrides and resets the limiters.
    yield app


@pytest.fixture
def light_app(app_under_test: Any) -> FastAPI:
    """The ``/public/ai/*`` router as ``app/api/v1/router.py`` mounts it in light mode.

    Same router object, same shared limiter, same dependency overrides as the
    production app — only the mode-dependent mount is reproduced here.
    """
    from app.api.v1.ki_assistent.public_router import router as ai_public_router

    light = FastAPI()
    light.state.limiter = limiter
    light.include_router(ai_public_router, prefix="/api/v1")
    light.dependency_overrides = app_under_test.dependency_overrides
    return light


#: ``(app fixture, method, path, json body)`` of the three async limited routes.
_ASYNC_LIMITED = [
    pytest.param("light_app", "post", "/api/v1/public/ai/ask", {"question": "Was ist VPD?"}, id="public_ask"),
    pytest.param("app_under_test", "get", "/api/v1/privacy/export/exp-1/download", None, id="download_export"),
    pytest.param(
        "app_under_test",
        "post",
        "/api/v1/t/garden/notifications/test",
        {"channel_key": "email"},
        id="send_test_notification",
    ),
]


async def _call(client: httpx.AsyncClient, method: str, path: str, body: dict[str, str] | None) -> int:
    kwargs: dict[str, Any] = {"json": body} if body is not None else {}
    response = await client.request(method.upper(), path, **kwargs)
    return response.status_code


@pytest.mark.parametrize(("app_fixture", "method", "path", "body"), _ASYNC_LIMITED)
def test_the_limit_check_runs_off_the_event_loop(
    request: pytest.FixtureRequest,
    storage_calls: _StorageCalls,
    app_fixture: str,
    method: str,
    path: str,
    body: dict[str, str] | None,
) -> None:
    target = request.getfixturevalue(app_fixture)

    async def scenario() -> tuple[int, int]:
        loop_thread = threading.get_ident()
        transport = httpx.ASGITransport(app=target)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            assert await _call(client, method, path, body) == 200
        return loop_thread, len(storage_calls.threads)

    loop_thread, checks = asyncio.run(scenario())

    assert checks >= 1, "precondition: the route reached the shared storage"
    assert loop_thread not in storage_calls.threads, "the limit check ran on the event loop's thread"


def test_an_unrelated_async_route_is_not_held_by_a_slow_limit_check(
    light_app: FastAPI, storage_calls: _StorageCalls
) -> None:
    async def scenario() -> list[float]:
        transport = httpx.ASGITransport(app=light_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:

            async def unrelated() -> list[float]:
                due = time.perf_counter() + 0.02
                await asyncio.sleep(0.02)

                async def one() -> float:
                    await client.get("/api/v1/public/ai/health")
                    # From when it was due: a blocked loop also delays the wake-up.
                    return time.perf_counter() - due

                return list(await asyncio.gather(*(one() for _ in range(5))))

            limited, latencies = await asyncio.gather(
                _call(client, "post", "/api/v1/public/ai/ask", {"question": "Was ist VPD?"}), unrelated()
            )
            assert limited == 200
            return latencies

    latencies = asyncio.run(scenario())

    assert storage_calls.threads, "precondition: the limited request reached the slow storage"
    assert max(latencies) < _UNBLOCKED_BOUND_S, f"unrelated requests waited {max(latencies):.3f}s behind the check"


def test_the_public_health_route_never_reaches_the_shared_storage(
    app_under_test: Any, storage_calls: _StorageCalls
) -> None:
    """Decided in #2048: ``/api/health`` is limited from process memory only.

    During a Valkey outage every health probe paid the socket timeout of the
    shared storage (measured 0.34 s per call against a storage answering in
    0.3 s); the endpoint exists for clients that negotiate before anything else.
    """

    async def scenario() -> int:
        transport = httpx.ASGITransport(app=app_under_test)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get("/api/health")
            return response.status_code

    assert asyncio.run(scenario()) == 200
    assert storage_calls.threads == [], "GET /api/health reached the shared limiter storage"
