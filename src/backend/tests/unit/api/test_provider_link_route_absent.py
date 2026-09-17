"""The manual provider-link route is gone and stays gone (#1416).

`POST /api/v1/users/me/providers/{provider_slug}/link` existed, worked, wrote
`auth_providers` rows — and no client ever called it. `api/endpoints/auth.ts`
exports `unlinkProvider` and nothing that links; `OAuthCallbackPage` completes a
sign-in and has no link mode. The operator decision on #1416 (2026-09-17) was
option 2 of the issue: remove the endpoint rather than build the client half.
Linking happens on the automatic path during sign-in only
(`AuthService.complete_oauth` → `OAuthEngine.should_auto_link`, #1403).

A deletion needs a test that fails when the deletion is reverted, otherwise the
removal is unobserved and the route comes back with the next copy-paste. Two
readings answer that, because either one alone can be quietly wrong:

* **The OpenAPI document** — the contract a client reads. It misses a route
  mounted with `include_in_schema=False`, which is exactly how a "temporarily
  hidden" route survives.
* **The mounted route surface** — what FastAPI actually serves. `include_router`
  does not flatten: it leaves `_IncludedRouter` wrappers, so a flat scan over
  `app.routes` finds only the docs routes and reads as correct while proving
  nothing (the mistake `scripts/check_frontend_calls_served.py` documents). The
  walk below follows `original_router`/`include_context.prefix`, like
  `test_write_route_gates.mounted_write_operations`.

Each absence assertion is paired with a control on the surviving sibling routes:
an absence test over a surface the reader never reaches is green for the wrong
reason.
"""

from __future__ import annotations

import inspect
from typing import Any

import pytest

PROVIDERS_PREFIX = "/api/v1/users/me/providers"
LIST_PATH = PROVIDERS_PREFIX
UNLINK_PATH = f"{PROVIDERS_PREFIX}/{{provider_key}}"


@pytest.fixture(scope="module")
def paths() -> dict[str, Any]:
    """The published OpenAPI paths of the assembled application."""
    from app.main import app

    return app.openapi()["paths"]


def _mounted_operations() -> list[tuple[str, str]]:
    """Every `(method, cumulative path)` the v1 router mounts."""
    from app.api.v1.router import api_router

    found: list[tuple[str, str]] = []

    def walk(router: Any, prefix: str = "") -> None:
        for route in getattr(router, "routes", []):
            included = getattr(route, "original_router", None)
            if included is not None:
                context = getattr(route, "include_context", None)
                walk(included, prefix + (getattr(context, "prefix", "") or ""))
                continue
            if getattr(route, "endpoint", None) is None:
                continue
            path = prefix + (getattr(route, "path", "") or "")
            for method in getattr(route, "methods", ()) or ():
                found.append((method, path))

    walk(api_router)
    return found


class TestTheOpenApiContract:
    """What a client can discover."""

    def test_no_provider_path_offers_a_link_operation(self, paths: dict[str, Any]) -> None:
        """Not keyed on the exact path: any POST below `/me/providers` is the defect."""
        offenders = [
            f"{method.upper()} {path}"
            for path, operations in paths.items()
            if path.startswith(PROVIDERS_PREFIX)
            for method in operations
            if method.lower() == "post"
        ]
        assert not offenders, "Provider-link write re-published:\n  " + "\n  ".join(offenders)

    def test_the_surviving_provider_routes_are_still_published(self, paths: dict[str, Any]) -> None:
        """The control: without these the assertion above holds over an empty set."""
        assert "get" in paths[LIST_PATH]
        assert "delete" in paths[UNLINK_PATH]


class TestTheMountedSurface:
    """What the application actually serves, schema flag or not."""

    def test_the_link_route_is_not_mounted(self) -> None:
        offenders = [
            f"{method} {path}" for method, path in _mounted_operations() if "/me/providers" in path and method == "POST"
        ]
        assert not offenders, "Provider-link route re-mounted:\n  " + "\n  ".join(offenders)

    def test_the_walk_reaches_the_users_router(self) -> None:
        """The control for the walk itself — a walk that never arrives finds no offender."""
        mounted = _mounted_operations()
        assert ("DELETE", UNLINK_PATH) in mounted
        assert ("GET", LIST_PATH) in mounted


class TestTheServiceMethod:
    """The route was `link_provider`'s only caller; the auto-link path does not use it."""

    def test_the_auth_service_no_longer_offers_link_provider(self) -> None:
        from app.domain.services.auth_service import AuthService

        assert not hasattr(AuthService, "link_provider")

    def test_unlink_and_the_auto_link_path_survive(self) -> None:
        """The control: removing the whole provider surface would pass the test above."""
        from app.domain.services.auth_service import AuthService

        assert callable(AuthService.unlink_provider)
        assert callable(AuthService._create_oauth_provider)
        assert "should_auto_link" in inspect.getsource(AuthService.complete_oauth)
