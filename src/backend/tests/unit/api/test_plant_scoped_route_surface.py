"""The plant-scoped global route surface, pinned so its client mirror can drift loudly.

Two routers resolve their tenant from the ``X-Active-Tenant`` header rather than
from a ``/t/{slug}`` path segment, and since #1402 C both carry
``require_owned_plant``, which refuses a request whose tenant does not resolve.
That refusal made a previously harmless situation load-bearing: a request sent
during the auth-bootstrap window, before ``loadMyTenants`` has produced a slug, no
longer falls back to personal scope — it 404s on the caller's **own** plant.

The frontend answers that by waiting out the window, for these paths only
(``TENANT_HEADER_REQUIRED`` in ``src/frontend/src/api/client.ts``). Waiting for
*every* global request would delay the genuinely global ones — the species
catalogue, ``/mode``, the auth surface — by the bootstrap timeout, and some of them
run before a tenant can exist. So the client holds a hand-maintained mirror of this
surface, in another language, with no compiler between the two.

**That mirror is what this file protects.** A route added to either router, or a
third router given the same dependency, would silently lose the wait and 404 during
the window — the failure being invisible precisely because it is transient. There is
no cross-language check that can be written here; what can be written is a witness
that fails the moment the backend side moves, naming the file that has to move with
it. The backend half of #1402 built a route sweep for exactly this drift class
(``test_write_route_gates.py``); this is the same idea pointed at the client.

Pinned by path template, not by count: a count would pass a rename, and a rename is
the case that breaks a regex mirror while leaving every backend test green.
"""

from __future__ import annotations

from typing import Any

from app.api.v1.care_reminders.router import router as care_router
from app.api.v1.phases.router import router as phases_router

#: Every path the two header-scoped routers mount, prefix included.
#:
#: Keep in step with ``TENANT_HEADER_REQUIRED`` in
#: ``src/frontend/src/api/client.ts``. The two regexes there are
#: ``^/plant-instances/[^/]+/phases(/|$)`` and ``^/care-reminders/plants/``; every
#: entry below has to be matched by one of them.
EXPECTED_PATHS: frozenset[str] = frozenset(
    {
        "/plant-instances/{plant_key}/phases/current",
        "/plant-instances/{plant_key}/phases/transition",
        "/plant-instances/{plant_key}/phases/history",
        "/plant-instances/{plant_key}/phases/history/{history_key}",
        "/care-reminders/plants/{plant_key}/profile",
        "/care-reminders/plants/{plant_key}/confirm",
        "/care-reminders/plants/{plant_key}/snooze",
        "/care-reminders/plants/{plant_key}/history",
        "/care-reminders/plants/{plant_key}/reset-profile",
    }
)

#: The client-side mirror, transcribed. Not imported — it lives in TypeScript — so
#: the transcription is checked against the real paths below rather than trusted.
_CLIENT_PREFIXES: tuple[str, ...] = ("/plant-instances/", "/care-reminders/plants/")


def _mounted_paths(router: Any) -> set[str]:
    # `route.path` on an APIRouter's own routes already carries the router prefix;
    # prepending `router.prefix` doubles it. Worth the comment because the first
    # version of this file did exactly that, and the resulting paths
    # (`/care-reminders/care-reminders/plants/...`) looked plausible enough in a
    # diff to be read past.
    return {route.path for route in router.routes if getattr(route, "path", None) is not None}


def _surface() -> set[str]:
    return _mounted_paths(phases_router) | _mounted_paths(care_router)


class TestThePlantScopedSurfaceIsPinned:
    def test_the_mounted_paths_are_the_expected_ones(self):
        """Both directions, so an addition and a removal each fail with their own line."""
        actual = _surface()

        added = sorted(actual - EXPECTED_PATHS)
        removed = sorted(EXPECTED_PATHS - actual)

        assert not added, (
            "new plant-scoped route(s) on a header-scoped router:\n  "
            + "\n  ".join(added)
            + "\n\nAdd them to EXPECTED_PATHS here AND check they are matched by "
            "TENANT_HEADER_REQUIRED in src/frontend/src/api/client.ts — a route the "
            "client does not match loses the auth-bootstrap wait and answers 404 on "
            "the caller's own plant during that window (#1402 C)."
        )
        assert not removed, (
            "plant-scoped route(s) gone from the routers:\n  "
            + "\n  ".join(removed)
            + "\n\nRemove them here, and drop the matching pattern in "
            "src/frontend/src/api/client.ts if nothing else needs it."
        )

    def test_every_path_is_covered_by_a_client_pattern(self):
        """The transcription above is checked, not assumed.

        A prefix list that matched nothing would make the pinning test pass while
        proving nothing about the client — the shape of guard this PR has already
        shipped once by mistake, with a pattern written against the frontend *route*
        rather than the API path.
        """
        uncovered = sorted(p for p in _surface() if not p.startswith(_CLIENT_PREFIXES))

        assert not uncovered, (
            "path(s) no client pattern covers:\n  "
            + "\n  ".join(uncovered)
            + "\n\nTENANT_HEADER_REQUIRED in src/frontend/src/api/client.ts has to gain "
            "a pattern for these."
        )

    def test_the_surface_is_not_empty(self):
        """A router import that silently yielded nothing would make both tests vacuous."""
        assert len(_surface()) == len(EXPECTED_PATHS) > 0
