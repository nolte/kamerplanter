"""#2138 — the import's body ceiling names the route that serves the import, and only that one.

``RequestBodyLimitMiddleware`` matches a route ceiling on the exact method and path, before routing.
A path that drifted from the route (a renamed prefix, a moved router) would silently fall back to the
global ceiling — every archive above ``STORAGE_MAX_FILE_SIZE_MB`` refused again — and a second entry
would hand the import's ceiling to a route that has neither the platform-admin gate nor the step-up.

**Predicate** — in the assembled full-mode application, the middleware carries exactly one route
ceiling; its path is a ``POST`` route of the application (``include_router`` does not flatten, so the
walk follows ``original_router``) whose endpoint is the import handler; its size is
``TENANT_IMPORT_MAX_UPLOAD_MB`` + 1 MiB.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Any

from app.api.v1.tenant_exports.router import TENANT_IMPORT_PATH, admin_import_tenant
from app.common.body_limit import RequestBodyLimitMiddleware, RouteBodyCeiling, request_body_limit_bytes
from app.config.settings import settings


def _routes(routes: Iterable[Any], prefix: str = "", depth: int = 0) -> Iterator[tuple[str, set[str], Any]]:
    assert depth < 8, "router graph deeper than expected — a cycle?"
    for route in routes:
        original = getattr(route, "original_router", None)
        if original is not None:
            yield from _routes(original.routes, prefix + route.include_context.prefix, depth + 1)
        elif hasattr(route, "path"):
            yield prefix + route.path, set(getattr(route, "methods", None) or ()), getattr(route, "endpoint", None)


def _route_ceilings() -> list[RouteBodyCeiling]:
    from app.main import app

    entries = [m for m in app.user_middleware if m.cls is RequestBodyLimitMiddleware]
    assert len(entries) == 1, "the body-limit middleware is installed exactly once"
    return list(entries[0].kwargs.get("route_ceilings", ()))


def test_the_import_ceiling_is_the_only_route_ceiling_and_names_the_import_route() -> None:
    from app.main import app

    assert settings.kamerplanter_mode == "full"
    ceilings = _route_ceilings()

    assert [(c.method, c.path) for c in ceilings] == [("POST", TENANT_IMPORT_PATH)]
    assert ceilings[0].max_body_bytes == request_body_limit_bytes(settings.tenant_import_max_upload_mb)
    served = [
        endpoint for path, methods, endpoint in _routes(app.routes) if path == TENANT_IMPORT_PATH and "POST" in methods
    ]
    assert served == [admin_import_tenant]


def test_the_walk_finds_routes_at_all() -> None:
    """Self-check: a walk that found nothing would make the predicate above fail for the wrong reason."""
    from app.main import app

    assert sum(1 for _ in _routes(app.routes)) > 100
