"""The served API majors are discoverable, and derived rather than declared (#1124).

The Android client is a separate release train against a **self-hosted** backend,
so app and server drift in both directions and the client must negotiate the
highest major both sides support. It has been probing
`GET/HEAD /api/v{n}/openapi.json` downward from the highest major it knows — a
workaround that also cannot tell "this major is not served" apart from "the server
was briefly unreachable".

`GET /api/health` now carries `supported_majors`. That endpoint, and not a new
one, because it is the only thing a client can reach *before* it has chosen a
major — putting the negotiation input behind a versioned path would be circular —
and because it is unauthenticated, which negotiation needs: the base URL is picked
before there is a token.

**The load-bearing property is that the list is derived from the router table.**
A maintained constant would answer the question and then go stale the first time a
major is added or retired — replacing a probe that is at least *true* with a
declaration that might not be. `test_a_newly_mounted_major_appears_by_itself` is
the test that holds that; without it this file would pass just as well against a
hardcoded `[1]`.
"""

from __future__ import annotations

from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from app.main import app, supported_api_majors


def test_health_reports_the_served_majors() -> None:
    response = TestClient(app).get("/api/health")

    assert response.status_code == 200, response.text
    assert response.json()["supported_majors"] == [1]


def test_the_field_is_reachable_without_authentication() -> None:
    """Negotiation happens before there is a token, so a 401 here would defeat it."""
    response = TestClient(app).get("/api/health")

    assert response.status_code == 200
    assert "supported_majors" in response.json()


def test_a_newly_mounted_major_appears_by_itself() -> None:
    """The whole point: mounting a v2 router is enough, no list to remember.

    Without this, every other assertion in this file is satisfied by a hardcoded
    `[1]` — and a hardcoded list is exactly the failure this replaces, since it
    would keep claiming `[1]` on the day v2 ships.
    """
    application = FastAPI()
    for prefix in ("/api/v1", "/api/v2"):
        router = APIRouter(prefix=prefix)
        router.add_api_route("/things", lambda: {}, methods=["GET"])
        application.include_router(router)

    assert supported_api_majors(application) == [1, 2]


def test_an_empty_router_is_not_a_served_major() -> None:
    """Mounting a prefix that serves nothing must not advertise a major.

    This started as a mistake in the fixture above — a bare
    `APIRouter(prefix="/api/v1")` with no routes — and the answer the code gave
    was the right one. Kept as its own case because the distinction is real: a
    client that negotiates onto a major with no endpoints is worse off than one
    that never saw it.
    """
    application = FastAPI()
    application.include_router(APIRouter(prefix="/api/v1"))

    assert supported_api_majors(application) == []


def test_a_retired_major_disappears_by_itself() -> None:
    """The other direction, which a "just append to the list" habit gets wrong."""
    application = FastAPI()
    only_v2 = APIRouter(prefix="/api/v2")
    only_v2.add_api_route("/things", lambda: {}, methods=["GET"])
    application.include_router(only_v2)

    assert supported_api_majors(application) == [2]


def test_the_order_is_ascending_and_deduplicated() -> None:
    """Many routes share a major; the client wants a set, and wants the last entry
    to be the highest so "take the newest we both support" is a single read."""
    application = FastAPI()
    for prefix in ("/api/v3", "/api/v1", "/api/v3", "/api/v10"):
        router = APIRouter(prefix=prefix)
        router.add_api_route(f"/thing-{prefix.replace('/', '-')}", lambda: {}, methods=["GET"])
        application.include_router(router)

    assert supported_api_majors(application) == [1, 3, 10]


def test_unversioned_and_lookalike_paths_are_not_counted() -> None:
    """`/api/health` itself, and anything that merely starts with `v`, must not
    invent a major. A false entry is worse than a missing one: the client would
    negotiate onto a base URL that serves nothing."""
    application = FastAPI()
    application.add_api_route("/api/health", lambda: {}, methods=["GET"])
    application.add_api_route("/api/vegetables", lambda: {}, methods=["GET"])
    application.add_api_route("/apiv9/things", lambda: {}, methods=["GET"])

    assert supported_api_majors(application) == []
