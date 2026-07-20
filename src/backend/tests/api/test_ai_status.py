"""Issue #685 — API tests for the public KI-Assistent availability probe.

The ``GET /ai/status`` endpoint mirrors ``settings.ai_features_enabled`` and,
unlike the rest of the KI API, must answer 200 in both flag states so the
frontend can gate the nav entry instead of hitting the guard's 404.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.ki_assistent.status_router import router as status_router
from app.config.settings import settings


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(status_router, prefix="/api/v1")
    return TestClient(app)


def test_status_reports_unavailable_when_flag_off(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ai_features_enabled", False)

    resp = _client().get("/api/v1/ai/status")

    assert resp.status_code == 200
    assert resp.json() == {"available": False}


def test_status_reports_available_when_flag_on(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ai_features_enabled", True)

    resp = _client().get("/api/v1/ai/status")

    assert resp.status_code == 200
    assert resp.json() == {"available": True}
