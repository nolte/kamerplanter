"""The routers ``app/api/v1/router.py`` mounts only when ``KAMERPLANTER_MODE=light``.

The app the suite imports is built at import time under the default
``kamerplanter_mode="full"``, so a route-walking guard over ``app.main.app`` or
``api_router`` never sees a light-only route. Since the 2026-10-09 decision on
PR #2208 ``/public/ai/*`` is such a route (REQ-031 §5.3): a guard that holds it
— rate limit off the event loop, write-route authorisation, per-user limits —
must walk these as well, or the light-mode surface drops out of the class
unnoticed.

Read from ``LIGHT_ONLY_ROUTERS``, the tuple the mount itself iterates, so the
list here cannot drift from the mount. That the tuple is complete — the light
app mounts nothing else the full app lacks — is pinned by
``tests/api/test_ai_public_routes_light_mode_only.py::test_the_light_only_routes_are_exactly_these``,
which diffs both apps in fresh interpreters.
"""

from __future__ import annotations

from typing import Any


def light_only_routers() -> list[tuple[str, Any]]:
    """``(cumulative prefix, router)`` of every router mounted in light mode only."""
    from app.api.v1.router import LIGHT_ONLY_ROUTERS, api_router

    return [(api_router.prefix, router) for router in LIGHT_ONLY_ROUTERS]
