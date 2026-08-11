"""CORS preflight admits ``X-Active-Tenant`` (#1091 A-6, ADR-009).

**Why this file exists at all.** ``X-Active-Tenant`` is not one of the four
CORS-safelisted request headers (``Accept``, ``Accept-Language``,
``Content-Language``, ``Content-Type``), so a browser sends a **preflight**
``OPTIONS`` before the catalogue request — even though that request is a plain
``GET``. Whether the header ever reaches the resolver in a deployed browser is
therefore decided by the CORS configuration, not by the resolver: the most
carefully tested tenant resolution in the world resolves nothing if the header
never leaves the browser.

**Why no production change accompanies it.** ``app.main`` configures
``CORSMiddleware(..., allow_headers=["*"])``; under the wildcard Starlette
mirrors the requested headers back on the preflight, so the header is admitted
today. The original work item assumed the config had to be widened; that
assumption was refuted (analysis refutation R-2). What was missing is not
configuration but a **guard that keeps the current behaviour true**.

**The failure mode the guard names.** Someone narrows ``allow_headers`` from
``["*"]`` to an explicit list — a wholly reasonable hardening move — and omits
``x-active-tenant``. From that moment:

* the preflight is refused, so the browser never issues the real request. The
  backend sees nothing: no 4xx, no log line, no metric — the regression is
  invisible on the server side, where anyone would look for it;
* nothing in dev reproduces it. The Vite dev server proxies ``/api`` on the same
  origin, so dev traffic is not cross-origin and is never preflighted at all;
  ``curl``, the E2E API clients and every backend test likewise ignore CORS. The
  breakage exists only in a deployed browser;
* the user-visible symptom does not point at CORS. Depending on how the client
  handles the blocked request, the catalogue either fails with a generic network
  error or degrades to whatever it renders without the header — which is the
  personal-tenant scope. Every member of an organisation tenant quietly sees the
  personal catalogue instead of the organisation's, and no error anywhere says
  why.

That combination — server-side silence, dev-side invisibility, a symptom that
misdirects — is what earns a test for a line of configuration nobody plans to
touch.

**What is pinned is behaviour, not the wildcard.** The assertion accepts either
shape a correct configuration can produce: the header echoed verbatim (what the
wildcard does today) or an explicit allow-list containing it. A future switch to
an explicit list that *includes* ``x-active-tenant`` must keep this test green.
The literal token ``*`` is accepted too, but only for a non-credentialed
preflight response: per the Fetch standard the wildcard in
``Access-Control-Allow-Headers`` is ignored when the request's credentials mode
is ``include``, and this app sets ``allow_credentials=True``.

Datastore-free by construction: a preflight is answered by the middleware and
never reaches a route, so no repository, service or connection is involved.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Response
from starlette.middleware.cors import CORSMiddleware

from app.common.auth import ACTIVE_TENANT_HEADER
from app.config.settings import settings

#: A global, tenant-aware catalogue route — one of the consumers of the header
#: (ADR-009). The preflight is answered by the middleware before routing, so the
#: path only has to be one the frontend really calls cross-origin.
CATALOGUE_ROUTE = "/api/v1/species"

#: An origin no deployment configures. Used by the control test to show the
#: middleware is actually deciding rather than waving everything through.
UNCONFIGURED_ORIGIN = "https://evil.example.invalid"


@pytest.fixture(scope="module")
def production_app() -> FastAPI:
    """The real ``app.main:app``, assembled exactly as production assembles it.

    Deliberately *not* a locally built ``FastAPI()`` with a hand-written
    ``add_middleware(CORSMiddleware, ...)``: such a test pins its own fixture and
    would stay green through any change to ``app.main``, which is the one file
    whose change this guard has to catch. The startup hooks are patched only so
    that importing the module cannot open a connection; the middleware stack is
    untouched.
    """
    with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
        from app.main import app

    return app


@pytest.fixture(scope="module")
def client(production_app: FastAPI) -> TestClient:
    """A client on the production app. ``TestClient`` runs the full middleware stack."""
    return TestClient(production_app)


@pytest.fixture(scope="module")
def configured_origin() -> str:
    """A browser origin drawn from the app's own configuration, never hard-coded.

    Hard-coding ``http://localhost:5173`` here would make the test pass on a
    deployment whose ``cors_origins`` no longer contains the frontend at all.
    """
    assert settings.cors_origins, "cors_origins is empty — no browser origin could ever be admitted"
    return settings.cors_origins[0]


def _preflight(client: TestClient, origin: str, requested_headers: str) -> Response:
    """Issue the preflight a browser would issue before a cross-origin catalogue GET."""
    return client.options(
        CATALOGUE_ROUTE,
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": requested_headers,
        },
    )


def _admits_header(allow_headers: str | None, credentialed: bool, wanted: str) -> bool:
    """Decide whether an ``Access-Control-Allow-Headers`` value admits ``wanted``.

    Mirrors what a browser does, so the test survives a change of *shape* in the
    response while still catching a change of *meaning*:

    * an explicit token list admits the header if it contains it (matching is
      case-insensitive — header names are case-insensitive and Starlette
      lowercases its allow-list);
    * the wildcard ``*`` admits it only for a non-credentialed response. The
      Fetch standard treats ``*`` literally — as a header *named* ``*`` — when
      the request's credentials mode is ``include``, which is exactly the mode
      this app invites by sending ``Access-Control-Allow-Credentials: true``.
    """
    if allow_headers is None:
        return False

    tokens = {token.strip().lower() for token in allow_headers.split(",")}
    if wanted.lower() in tokens:
        return True

    return "*" in tokens and not credentialed


def test_preflight_admits_active_tenant_header(client: TestClient, configured_origin: str) -> None:
    """A browser preflight requesting ``X-Active-Tenant`` is granted.

    Guards the single configuration line every org member's catalogue scope hangs
    on. See the module docstring for the failure mode.
    """
    response = _preflight(client, configured_origin, ACTIVE_TENANT_HEADER)

    assert response.status_code == 200, (
        f"Preflight for {ACTIVE_TENANT_HEADER} was refused ({response.status_code}: {response.text!r}). "
        "A browser would block the catalogue request outright; the backend would never see it."
    )
    assert response.headers.get("access-control-allow-origin") == configured_origin, (
        f"Preflight did not allow the configured origin {configured_origin!r} — "
        "the browser blocks the request regardless of the allowed headers."
    )

    allow_headers = response.headers.get("access-control-allow-headers")
    credentialed = response.headers.get("access-control-allow-credentials", "").lower() == "true"
    assert _admits_header(allow_headers, credentialed, ACTIVE_TENANT_HEADER), (
        f"Access-Control-Allow-Headers={allow_headers!r} does not admit {ACTIVE_TENANT_HEADER} "
        f"(credentialed response: {credentialed}). Add it to allow_headers in app/main.py — "
        "without it the browser drops the request and every org member falls back to personal scope."
    )


def test_preflight_admits_active_tenant_header_beside_the_others_a_browser_sends(
    client: TestClient, configured_origin: str
) -> None:
    """The real preflight carries several headers at once, not one in isolation.

    An authenticated catalogue read sends ``Authorization`` and
    ``Content-Type`` alongside ``X-Active-Tenant``; browsers list them in one
    comma-separated ``Access-Control-Request-Headers``, lower-cased. An
    allow-list that admitted the header only when requested alone would still
    break the app, so the guard asserts the combination that actually occurs.
    """
    requested = f"authorization,content-type,{ACTIVE_TENANT_HEADER.lower()}"

    response = _preflight(client, configured_origin, requested)

    assert response.status_code == 200, (
        f"Preflight for {requested!r} was refused ({response.status_code}: {response.text!r})."
    )
    allow_headers = response.headers.get("access-control-allow-headers")
    credentialed = response.headers.get("access-control-allow-credentials", "").lower() == "true"
    assert _admits_header(allow_headers, credentialed, ACTIVE_TENANT_HEADER), (
        f"Access-Control-Allow-Headers={allow_headers!r} admits {ACTIVE_TENANT_HEADER} alone but not "
        "in the header set a browser really sends."
    )


def test_preflight_discriminates_between_configured_and_foreign_origins(
    client: TestClient, configured_origin: str
) -> None:
    """Control: a real CORS policy runs, and it is not waving everything through.

    Without a control, the tests above could not distinguish "CORS admits the
    header" from "CORS is not in the stack at all, so nothing is checked". Both
    directions are asserted together on purpose: a foreign origin alone is *also*
    refused by an app with no CORS middleware (the bare ``OPTIONS`` 405s), so
    that half passes vacuously and only the configured half detects removal.
    """
    granted = _preflight(client, configured_origin, ACTIVE_TENANT_HEADER)
    refused = _preflight(client, UNCONFIGURED_ORIGIN, ACTIVE_TENANT_HEADER)

    assert granted.headers.get("access-control-allow-origin") == configured_origin, (
        f"Configured origin {configured_origin!r} was not echoed back — "
        "no CORS policy appears to be running on this app at all."
    )
    assert refused.headers.get("access-control-allow-origin") != UNCONFIGURED_ORIGIN, (
        f"Unconfigured origin {UNCONFIGURED_ORIGIN} was allowed — CORS is not restricting origins, "
        "so the admission asserted above says nothing about the configured policy."
    )


@pytest.mark.parametrize(
    ("allow_headers", "credentialed", "expected"),
    [
        ("x-active-tenant", True, True),
        ("X-Active-Tenant", True, True),
        ("authorization, content-type, x-active-tenant", True, True),
        ("authorization, content-type", True, False),
        (None, True, False),
        ("*", False, True),
        ("*", True, False),
    ],
)
def test_admits_header_follows_the_browser_rule(allow_headers: str | None, credentialed: bool, expected: bool) -> None:
    """The admission rule itself, including the branch Starlette cannot produce.

    ``allow_headers=["*"]`` makes Starlette mirror the requested headers rather
    than answer with a literal ``*``, so no configuration of the current stack
    reaches the wildcard branch above — it exists for a future middleware or
    reverse proxy that answers with ``*``. Untested, it would be an unverified
    claim inside a guard; here the Fetch rule it encodes is pinned directly:
    ``*`` is a wildcard only while the response is not credentialed.
    """
    assert _admits_header(allow_headers, credentialed, ACTIVE_TENANT_HEADER) is expected


def test_app_wires_cors_middleware_from_settings(production_app: FastAPI) -> None:
    """The app under test is the one whose CORS config production runs.

    Structural companion to the behavioural tests: it names the two ways this
    guard could quietly stop guarding anything — the middleware disappearing from
    the stack, or its origins being pinned to a literal instead of read from
    ``settings`` (which would decouple the fixture origin above from what the
    deployment really allows).
    """
    cors_layers = [layer for layer in production_app.user_middleware if layer.cls is CORSMiddleware]

    assert len(cors_layers) == 1, (
        f"Expected exactly one CORSMiddleware in the production stack, found {len(cors_layers)}."
    )
    assert cors_layers[0].kwargs["allow_origins"] == settings.cors_origins, (
        "CORSMiddleware no longer takes its origins from settings.cors_origins — "
        "the origin this test preflights with is then unrelated to what a deployment allows."
    )
