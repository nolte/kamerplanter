"""REQ-031 §5.3 / REQ-027 — ``/public/ai/*`` exists only in light mode and is not anonymous.

The security review of PR #2208 measured ``POST /api/v1/public/ai/ask`` mounted
in both modes with no principal at all: in full mode an anonymous caller got an
LLM answer past the consent, the garden's KI switch and the daily budget that
``POST /t/{slug}/ai/knowledge/ask`` enforces (§5.1). Decided 2026-10-09: the
router is mounted only when ``KAMERPLANTER_MODE=light`` and every route depends
on ``get_current_user`` — which in light mode resolves the system user without a
login, so the light frontend keeps working unchanged.

The mount decision runs at import time of ``app/api/v1/router.py``, so it is
driven here in a fresh interpreter per mode; the in-process production app the
suite imports is full mode and is asked directly as well.
"""

from __future__ import annotations

import functools
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.auth.router import limiter
from app.api.v1.ki_assistent.public_router import router as public_router
from app.common.dependencies import get_ai_assistant_service, get_auth_provider
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError
from app.config.settings import settings
from app.domain.engines.light_auth_provider import LightAuthProvider
from app.domain.models.user import User
from tests.api.test_expensive_routes_per_user_limit import _TokenAuth
from tests.support.light_mode_routes import light_only_routers

BACKEND = Path(__file__).resolve().parents[2]
ASK = "/api/v1/public/ai/ask"
HEALTH = "/api/v1/public/ai/health"

#: Prints every ``"<METHOD> <path>"`` the assembled app mounts under the env's mode.
_ALL_ROUTES = """
import json
from app.main import app

def walk(routes, prefix=""):
    for route in routes:
        if hasattr(route, "original_router"):
            yield from walk(route.original_router.routes, prefix + route.include_context.prefix)
        elif hasattr(route, "path_format"):
            for method in sorted(getattr(route, "methods", None) or ["*"]):
                yield f"{method} {prefix}{route.path_format}"

print(json.dumps(sorted(set(walk(app.router.routes)))))
"""


@functools.cache
def _all_routes(mode: str) -> frozenset[str]:
    """The app's routes as a fresh interpreter under ``KAMERPLANTER_MODE=<mode>`` builds it."""
    env = {**os.environ, "KAMERPLANTER_MODE": mode}
    result = subprocess.run(  # noqa: S603 - fixed interpreter and fixed script
        [sys.executable, "-c", _ALL_ROUTES],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert result.returncode == 0, result.stderr[-2000:]
    return frozenset(json.loads(result.stdout.strip().splitlines()[-1]))


def _public_ai(mode: str) -> set[str]:
    return {route for route in _all_routes(mode) if "/public/ai/" in route}


def test_light_mode_mounts_the_public_ai_routes() -> None:
    """The control: the probe sees the routes where they are meant to be."""
    assert _public_ai("light") == {f"POST {ASK}", f"GET {HEALTH}"}


def test_full_mode_does_not_mount_the_public_ai_routes() -> None:
    assert _public_ai("full") == set()
    assert "POST /api/v1/t/{tenant_slug}/ai/knowledge/ask" in _all_routes("full")


def test_the_light_only_routes_are_exactly_these() -> None:
    """Pins ``tests/support/light_mode_routes.py`` to the real mount decision.

    The route-walking guards walk the full-mode app plus that list; a router
    mounted in light mode only and missing from it would drop out of every guard.
    """
    walked: set[str] = set()
    for prefix, router in light_only_routers():
        for route in router.routes:
            walked |= {f"{method} {prefix}{route.path_format}" for method in route.methods}

    assert _all_routes("light") - _all_routes("full") == walked == {f"POST {ASK}", f"GET {HEALTH}"}


def test_the_full_mode_production_app_answers_404(monkeypatch: pytest.MonkeyPatch) -> None:
    """With the KI operator flag on: the 404 is the missing route, not stage 1."""
    with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
        from app.main import app

    assert settings.kamerplanter_mode == "full", "precondition: the suite's app is full mode"
    monkeypatch.setattr(settings, "ai_features_enabled", True)
    service = MagicMock()
    app.dependency_overrides[get_ai_assistant_service] = lambda: service
    # tests/api/conftest.py restores the overrides.
    client = TestClient(app)

    assert client.post(ASK, json={"question": "Was ist VPD?"}).status_code == 404
    assert client.get(HEALTH).status_code == 404
    service.ask_public.assert_not_called()
    assert ASK not in app.openapi()["paths"]


# ── the router as light mode mounts it ──────────────────────────────


def _answer() -> SimpleNamespace:
    return SimpleNamespace(
        answer_text="VPD is the vapour pressure deficit.",
        sources=[],
        language="de",
        language_mismatch_warning=False,
        uses_tenant_data=False,
        uses_cloud_provider=False,
        confidence="high",
        model_name="gemma3:12b",
        provider_type="ollama",
        kb_version=None,
        generated_at=None,
    )


@pytest.fixture
def service() -> MagicMock:
    double = MagicMock()
    double.ask_public = AsyncMock(return_value=_answer())
    double.health_check = AsyncMock(return_value=True)
    return double


def _light_app(service: MagicMock, auth_provider: object) -> TestClient:
    app = FastAPI()
    app.state.limiter = limiter
    app.include_router(public_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[get_ai_assistant_service] = lambda: service
    app.dependency_overrides[get_auth_provider] = lambda: auth_provider
    return TestClient(app)


@pytest.fixture(autouse=True)
def _flag_on(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ai_features_enabled", True)


def test_light_mode_answers_through_the_system_user_without_a_login(service: MagicMock) -> None:
    """The real ``LightAuthProvider`` resolves the system user — no header needed."""
    users = MagicMock()
    users.get_by_key.return_value = User(
        _key="system-user", email="system@kamerplanter.example", display_name="Gaertner"
    )
    client = _light_app(service, LightAuthProvider(users))

    resp = client.post(ASK, json={"question": "What is VPD?"})

    assert resp.status_code == 200, resp.text
    assert resp.json()["uses_tenant_data"] is False
    assert resp.json()["answer_text"].startswith("VPD")
    service.ask_public.assert_awaited_once_with("What is VPD?", language="de")
    users.get_by_key.assert_called_with("system-user")
    assert client.get(HEALTH).json() == {"healthy": True}


def test_the_routes_refuse_a_caller_without_a_principal(service: MagicMock) -> None:
    """Not anonymous: under a provider that requires a login, no token is a 401
    before the LLM — the router itself carries ``get_current_user``."""
    client = _light_app(service, _TokenAuth())

    ask = client.post(ASK, json={"question": "What is VPD?"})
    health = client.get(HEALTH)

    assert ask.status_code == 401, ask.text
    assert ask.json()["error_code"] == "UNAUTHORIZED"
    assert health.status_code == 401
    service.ask_public.assert_not_called()
    service.health_check.assert_not_called()


def test_a_signed_in_caller_is_answered(service: MagicMock) -> None:
    client = _light_app(service, _TokenAuth())

    resp = client.post(ASK, json={"question": "What is VPD?"}, headers={"Authorization": "Bearer token-anna"})

    assert resp.status_code == 200, resp.text
    service.ask_public.assert_awaited_once()


def test_the_operator_flag_off_still_answers_404(service: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    """Stage 1 stays: with ``AI_FEATURES_ENABLED=false`` the routes look absent."""
    monkeypatch.setattr(settings, "ai_features_enabled", False)
    client = _light_app(service, _TokenAuth())

    resp = client.post(ASK, json={"question": "What is VPD?"}, headers={"Authorization": "Bearer token-anna"})

    assert resp.status_code == 404
    service.ask_public.assert_not_called()


def test_the_ip_rate_limit_stays() -> None:
    """The address limit ``AI_PUBLIC_RATE_LIMIT_PER_MIN`` is still on the ask route."""
    names = set(limiter._route_limits) | set(limiter._dynamic_route_limits)
    assert "app.api.v1.ki_assistent.public_router.public_ask" in names
