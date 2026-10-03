"""#2052 — no rate-limited route buckets on a value the caller writes into the path.

The defect: slowapi's default ``key_style="url"`` put the **request path** into
every bucket key, so on ``/public/glossary/term/{slug}``,
``/privacy/export/{export_key}/download`` and ``/t/{tenant_slug}/notifications/test``
each value the caller chose was a fresh budget — and a fresh key in the shared
Valkey. The fix builds the one shared limiter with ``key_style="endpoint"``
(``app.common.rate_limit.LIMITER_KEY_STYLE``).

The class is not those three routes. It is **every route of the assembled app
that carries a ``@limiter.limit``**, today's and tomorrow's: a later limiter
setting, a second ``Limiter`` with the default style, or a custom ``key_func``
that reads ``request.url`` would re-open it on a route nobody looked at. This
guard therefore measures the key slowapi actually computes, for every limited
leaf route reached through the nested ``_IncludedRouter.original_router``
wrappers (``include_router`` does not flatten), from two requests that differ
only in the path — the template's parameters filled with two different values,
or, for a route without parameters, a trailing ``/`` — and requires one key.

Non-vacuity: the walk must reach the three routes the defect was measured on,
and the comparison must tell two keys apart when it is handed a limiter in the
old style.
"""

from __future__ import annotations

import gc
import re
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.routing import APIRoute
from slowapi import Limiter
from starlette.requests import Request

_PATH_PARAMETER = re.compile(r"\{[^}]+\}")

#: The routes #2052 was measured on; the walk must reach all of them.
_MEASURED_ROUTES = frozenset(
    {
        "app.api.v1.glossar.public_router.public_get_term",
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


def _name(route: APIRoute) -> str:
    return f"{route.endpoint.__module__}.{route.endpoint.__name__}"


def _limited_routes(limiter: Limiter) -> list[tuple[str, APIRoute]]:
    from app.main import app

    names = set(limiter._route_limits) | set(limiter._dynamic_route_limits)
    return [(path, route) for path, route in _leaf_routes(app.router.routes) if _name(route) in names]


def _app_limiters() -> list[Limiter]:
    """Every ``Limiter`` alive after the app is assembled that limits one of its routes.

    Found on the heap rather than imported by name, so a limiter added in a
    module this guard never heard of — ``/api/health`` has its own since #2048 —
    is measured too.
    """
    from app.main import app

    names = {_name(route) for _, route in _leaf_routes(app.router.routes)}
    found = [obj for obj in gc.get_objects() if isinstance(obj, Limiter)]
    return [each for each in found if names & (set(each._route_limits) | set(each._dynamic_route_limits))]


def _variants(path: str) -> tuple[str, str]:
    if _PATH_PARAMETER.search(path):
        return _PATH_PARAMETER.sub("value-a", path), _PATH_PARAMETER.sub("value-b", path)
    return path, path + "/"


def _bucket(limiter: Limiter, route: APIRoute, path: str) -> tuple[str, ...]:
    """The key arguments slowapi hit the storage with for one request to *path*."""
    method = sorted(route.methods or {"GET"})[0]
    request = Request(
        {
            "type": "http",
            "method": method,
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "headers": [],
            "client": ("203.0.113.9", 40000),
            "server": ("testserver", 80),
            "scheme": "http",
        }
    )
    limiter._check_request_limit(request, route.endpoint, False)
    _limit, args = request.state.view_rate_limit
    return tuple(args)


@pytest.fixture
def shared_limiter() -> Iterator[Limiter]:
    from app.api.v1.auth.router import limiter

    limiters = _app_limiters()
    for each in limiters:
        each.reset()
    yield limiter
    for each in limiters:
        each.reset()


def test_every_limited_route_counts_one_bucket_whatever_the_path_says(shared_limiter: Limiter) -> None:
    limited = [(limiter, path, route) for limiter in _app_limiters() for path, route in _limited_routes(limiter)]
    reached = {_name(route) for _, _, route in limited}
    assert reached >= _MEASURED_ROUTES, f"the walk missed {sorted(_MEASURED_ROUTES - reached)}"
    assert "app.main.root_health" in reached, "the walk missed the limiter of /api/health"
    assert len(limited) >= 15, len(limited)

    split = []
    for limiter, path, route in limited:
        first, second = _variants(path)
        if _bucket(limiter, route, first) != _bucket(limiter, route, second):
            split.append(f"{sorted(route.methods or [])} {path} ({_name(route)})")

    assert not split, "these limited routes open a fresh bucket per path value:\n" + "\n".join(split)


def test_the_comparison_tells_a_path_keyed_limiter_apart(shared_limiter: Limiter) -> None:
    """Self-test: the same comparison on an old-style limiter reports a split."""
    from app.api.v1.auth.router import _rate_limit_key

    path_keyed = Limiter(key_func=_rate_limit_key, storage_uri="memory://", key_style="url")
    path_keyed._route_limits = shared_limiter._route_limits
    term = next(
        (path, route)
        for path, route in _limited_routes(shared_limiter)
        if _name(route) == "app.api.v1.glossar.public_router.public_get_term"
    )
    first, second = _variants(term[0])

    assert _bucket(path_keyed, term[1], first) != _bucket(path_keyed, term[1], second)
