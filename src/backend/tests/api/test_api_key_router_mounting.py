"""REQ-033 §4.3 / REQ-027 — API-key routes must exist in *both* deployment modes.

MCP accepts no credential other than a ``kp_`` API key. A light-mode instance
mounts no auth router at all, so before this split the MCP interface could be
enabled there and then never used: the endpoint answered 401 forever and there
was no route to obtain a key from. These tests pin the mounting itself, which is
the part that silently regresses — the handlers are covered elsewhere.

The routers are read straight from the module rather than through a live app, so
no database or Valkey is required.
"""

from __future__ import annotations

import importlib

import pytest

# The v1 router carries its own "/api/v1" prefix.
_API_KEY_PATHS = {"/api/v1/auth/api-keys", "/api/v1/auth/api-keys/{key_id}"}


def _mounted_paths(mode: str) -> set[str]:
    """Import the v1 router under ``mode`` and return every path it exposes."""

    from app.config import settings as settings_module

    original = settings_module.settings.kamerplanter_mode
    settings_module.settings.kamerplanter_mode = mode
    try:
        # The router builds its mode-dependent includes at import time.
        router_module = importlib.import_module("app.api.v1.router")
        importlib.reload(router_module)
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router_module.api_router)
        return set(app.openapi()["paths"])
    finally:
        settings_module.settings.kamerplanter_mode = original
        importlib.reload(importlib.import_module("app.api.v1.router"))


@pytest.mark.parametrize("mode", ["light", "full"])
def test_api_key_routes_are_mounted_in_both_modes(mode: str):
    paths = _mounted_paths(mode)
    assert paths >= _API_KEY_PATHS, f"API-key routes missing in {mode} mode"


def test_light_mode_mounts_api_keys_but_not_the_rest_of_auth():
    paths = _mounted_paths("light")
    # The credential endpoints are there …
    assert paths >= _API_KEY_PATHS
    # … while everything that presupposes real accounts stays out.
    auth_paths = {p for p in paths if p.startswith("/api/v1/auth/")}
    assert auth_paths == _API_KEY_PATHS, f"unexpected auth routes in light mode: {auth_paths - _API_KEY_PATHS}"


def test_full_mode_keeps_the_complete_auth_surface_without_duplicating_keys():
    paths = _mounted_paths("full")
    assert "/api/v1/auth/login" in paths
    assert paths >= _API_KEY_PATHS
    # Mounting the key router separately must not double up the full-mode surface.
    assert len({p for p in paths if "api-keys" in p}) == len(_API_KEY_PATHS)
