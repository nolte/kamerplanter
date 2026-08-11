"""REQ-027 / #1118 — device pairing exists in **full** mode only.

The mirror image of ``test_api_key_router_mounting.py``, and it is the mirror on
purpose. API keys are the one part of the auth surface a light-mode instance
needs, so they hang on ``api_keys_router``; device pairing is the opposite case
and must hang on ``auth_router``.

Why that matters more here than anywhere else on this router: redemption is
**unauthenticated** and mints a token pair for the account a code was issued to.
A light-mode instance has no accounts — every request there resolves to the
system user without authenticating (``LightAuthProvider``) — so a pairing route
mounted there would be a public endpoint handing out sessions for the single
privileged identity that deployment has. Moving one decorator from ``router`` to
``api_keys_router`` is all it would take, and nothing else in the suite would
notice; that is exactly the kind of silent regression this module pins.

The mode-dependent includes are built at **import** time, so the router module is
re-imported under each mode rather than merely inspected. No database or Valkey
is required: routing decides both answers here.
"""

from __future__ import annotations

import importlib

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# The v1 router carries its own "/api/v1" prefix.
_DEVICE_PAIRING_PATHS = {"/api/v1/auth/device-pairing", "/api/v1/auth/device-pairing/redeem"}


def _v1_router(mode: str):  # noqa: ANN201 - fastapi.APIRouter
    """Import the v1 router under ``mode`` and return it."""

    from app.config import settings as settings_module

    original = settings_module.settings.kamerplanter_mode
    settings_module.settings.kamerplanter_mode = mode
    try:
        router_module = importlib.import_module("app.api.v1.router")
        importlib.reload(router_module)
        return router_module.api_router
    finally:
        settings_module.settings.kamerplanter_mode = original
        importlib.reload(importlib.import_module("app.api.v1.router"))


def _mounted_paths(mode: str) -> set[str]:
    app = FastAPI()
    app.include_router(_v1_router(mode))
    return set(app.openapi()["paths"])


def test_device_pairing_routes_are_mounted_in_full_mode():
    assert _mounted_paths("full") >= _DEVICE_PAIRING_PATHS


def test_device_pairing_routes_are_absent_in_light_mode():
    paths = _mounted_paths("light")
    leaked = paths & _DEVICE_PAIRING_PATHS
    assert not leaked, f"device-pairing routes reachable in light mode: {leaked}"


@pytest.mark.parametrize("path", sorted(_DEVICE_PAIRING_PATHS))
def test_a_light_mode_instance_answers_404_on_both_routes(path: str):
    """The property as a caller observes it, not merely as the path table shows it.

    A route can disappear from ``openapi()`` and still be reachable (a second
    mount elsewhere, an ``include_in_schema=False``), so the answer is asserted
    on the wire. 404 — the route does not exist — and never 401/403, which would
    tell a probe that the feature is there but shut.
    """
    app = FastAPI()
    app.include_router(_v1_router("light"))
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post(path, json={"code": "whatever"})

    assert response.status_code == 404


def test_the_pairing_routes_hang_on_the_full_mode_router_and_not_the_other():
    """Names the cause, where the two tests above only observe the effect.

    ``api_keys_router`` is mounted in *both* modes; ``router`` only in full. So
    the mode gating is a property of which of the two objects carries the
    decorator, and reading it here says which edit broke it — the light-mode 404
    above would just go red without saying why. It also catches a pair added to
    *both* routers, which is invisible in full mode (the endpoints work either
    way) and is exactly what would expose them in light mode.
    """
    from app.api.v1.auth import router as auth_module

    # Router-local paths: the "/api/v1" prefix is added when the v1 router is
    # mounted into the app, not here.
    pairing = {"/auth/device-pairing", "/auth/device-pairing/redeem"}
    full_mode_only = {getattr(r, "path", None) for r in auth_module.router.routes}
    both_modes = {getattr(r, "path", None) for r in auth_module.api_keys_router.routes}

    assert pairing <= full_mode_only
    assert not (pairing & both_modes), "device pairing must not ride on the light-mode API-key router"
