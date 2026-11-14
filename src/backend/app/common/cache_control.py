"""MT-044 and its one named exception — the ``Cache-Control`` of a versioned API answer (REQ-053 §32.6 Pkt. 13).

Every ``/api/v1/`` answer is :data:`API_DEFAULT_CACHE_CONTROL` (``no-store``) unless its route chose otherwise: the
security-headers middleware fills it in where a route left the header absent (``app/main.py``). Downloads decide
their own policy (``app/api/v1/attachments/response_headers.py``).

**The offline-read exception** (operator decision of 2026-11-14 on #2759, question 13): the three tenant-scoped
reads the service worker keeps for the garden plan offline - :data:`OFFLINE_READ_ROUTES` - answer
:data:`OFFLINE_READ_CACHE_CONTROL` instead. ``private`` keeps them out of every shared cache, ``no-cache`` makes
each reuse ask the server first, so online a logout or a lost membership takes effect on the next read. The worker
keeps them only in the namespace ``kp:{user_key}:{tenant_key}``, which a logout and a tenant switch delete
(UI-NFR-012 R-056, GP-UX-024).

A route opts in by calling :func:`allow_offline_read_cache` on its ``Response``; the sweep
``tests/api/test_api_responses_are_not_stored.py`` pins that exactly the routes of :data:`OFFLINE_READ_ROUTES` do,
and the frontend guard ``src/test/guards/swCacheAllowlist.test.ts`` that the worker's allowlist names the same
three paths.
"""

from __future__ import annotations

from typing import Final

from starlette.responses import Response

#: MT-044: tenant-private JSON is never kept by a shared proxy or the browser cache.
API_DEFAULT_CACHE_CONTROL: Final = "no-store"

#: The named exception of MT-044 for the offline reads of the garden plan (REQ-053 §32.6 Pkt. 13).
OFFLINE_READ_CACHE_CONTROL: Final = "private, no-cache"

#: ``(method, path template)`` of every route that answers :data:`OFFLINE_READ_CACHE_CONTROL` - the service
#: worker's allowlist (REQ-053 §32.6 Pkt. 12): the site list, a site's plan, a bed's summary. Nothing else.
OFFLINE_READ_ROUTES: Final[frozenset[tuple[str, str]]] = frozenset(
    {
        ("GET", "/api/v1/t/{tenant_slug}/sites"),
        ("GET", "/api/v1/t/{tenant_slug}/sites/{key}/plan"),
        ("GET", "/api/v1/t/{tenant_slug}/locations/{key}/summary"),
    }
)


def allow_offline_read_cache(response: Response) -> None:
    """Mark the answer as one the service worker may keep in the user's and tenant's namespace (§32.6 Pkt. 13).

    Only for a route of :data:`OFFLINE_READ_ROUTES`; the middleware then leaves the header as it is.
    """
    response.headers["Cache-Control"] = OFFLINE_READ_CACHE_CONTROL


__all__ = [
    "API_DEFAULT_CACHE_CONTROL",
    "OFFLINE_READ_CACHE_CONTROL",
    "OFFLINE_READ_ROUTES",
    "allow_offline_read_cache",
]
