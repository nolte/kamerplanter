"""#2048 — no ``async`` route runs its rate-limit check on the event loop.

The defect: slowapi's ``async_wrapper`` calls the synchronous limit check
directly. Against the Valkey-backed storage of #2045 that check is a network
round trip on the event loop — a socket timeout while the storage hangs — and
every other request of the process waits behind it. Measured through the real
app: an unrelated async route went from 0.007 s to 0.935 s while three limited
async requests met a storage answering in 0.3 s. The fix is
``app.common.rate_limit.OffLoopLimiter``: it wraps every ``async`` limited route
in a wrapper that runs the check through ``run_in_threadpool`` and marks itself
with ``LIMIT_CHECK_OFF_LOOP_ATTRIBUTE``.

The class is **every limited route of the assembled app whose handler is a
coroutine function**, under whichever ``Limiter`` decorated it — a new async
route, or a limiter built as a plain ``slowapi.Limiter``, re-opens it. The walk
reaches leaf routes through the nested ``_IncludedRouter.original_router``
wrappers (``include_router`` does not flatten) and finds the limiters on the heap
rather than by import, so one added elsewhere is checked too. A ``def`` route is
out of the class: FastAPI runs it, check included, in the threadpool.

Non-vacuity: the walk must reach the three async routes the defect was measured
on, and the detector must flag a route decorated by a plain ``slowapi.Limiter``.
"""

from __future__ import annotations

import gc
import inspect
from collections.abc import Callable, Iterator
from typing import Any

from fastapi import Request
from fastapi.routing import APIRoute
from slowapi import Limiter

from app.common.rate_limit import LIMIT_CHECK_OFF_LOOP_ATTRIBUTE

#: The async limited routes #2048 was measured on; the walk must reach all of them.
_MEASURED_ROUTES = frozenset(
    {
        "app.api.v1.ki_assistent.public_router.public_ask",
        "app.api.v1.privacy.router.download_export",
        "app.api.v1.notifications.tenant_router.send_test_notification",
    }
)


def _leaf_routes(routes: list[Any], prefix: str = "") -> Iterator[tuple[str, APIRoute]]:
    for route in routes:
        if isinstance(route, APIRoute):
            yield prefix + route.path_format, route
        elif hasattr(route, "original_router"):
            yield from _leaf_routes(route.original_router.routes, prefix + route.include_context.prefix)


def _name(endpoint: Callable[..., Any]) -> str:
    return f"{endpoint.__module__}.{endpoint.__name__}"


def _handler(endpoint: Callable[..., Any]) -> Callable[..., Any]:
    """The function the route's author wrote, below every decorator wrapper."""
    return inspect.unwrap(endpoint)


def _checks_on_the_loop(endpoint: Callable[..., Any]) -> bool:
    return inspect.iscoroutinefunction(_handler(endpoint)) and not getattr(
        endpoint, LIMIT_CHECK_OFF_LOOP_ATTRIBUTE, False
    )


def _limited_names() -> set[str]:
    names: set[str] = set()
    for obj in gc.get_objects():
        if isinstance(obj, Limiter):
            names |= set(obj._route_limits) | set(obj._dynamic_route_limits)
    return names


def test_every_async_limited_route_checks_its_limit_off_the_loop() -> None:
    from app.main import app

    limited = _limited_names()
    async_limited = [
        (path, route)
        for path, route in _leaf_routes(app.router.routes)
        if _name(route.endpoint) in limited and inspect.iscoroutinefunction(_handler(route.endpoint))
    ]
    reached = {_name(route.endpoint) for _, route in async_limited}
    assert reached >= _MEASURED_ROUTES, f"the walk missed {sorted(_MEASURED_ROUTES - reached)}"

    on_loop = [
        f"{sorted(route.methods or [])} {path} ({_name(route.endpoint)})"
        for path, route in async_limited
        if _checks_on_the_loop(route.endpoint)
    ]

    assert not on_loop, "these async routes run the limit check on the event loop:\n" + "\n".join(on_loop)


def test_the_detector_flags_a_plain_slowapi_async_route() -> None:
    """Self-test: an async route under a plain ``slowapi.Limiter`` is reported."""
    plain = Limiter(key_func=lambda request: "client", storage_uri="memory://")

    @plain.limit("1/minute")
    async def plain_async_route(request: Request) -> dict[str, str]:
        return {}

    assert _checks_on_the_loop(plain_async_route)
