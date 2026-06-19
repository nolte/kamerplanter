"""NFR-013 AC-08 — readiness reflects object-storage health.

The health router resolves ``get_connection`` / ``get_object_storage`` at call
time from its own module namespace, so the tests patch those module attributes
rather than using FastAPI dependency overrides.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.api.v1.health.router as health_module
from app.api.v1.health.router import router as health_router


class _FakeStorage:
    def __init__(self, ready: bool) -> None:
        self._ready = ready

    async def health_check(self) -> dict:
        return {"backend": "local-fs", "ready": self._ready}


def _conn(connected: bool):
    conn = MagicMock()
    conn.is_connected.return_value = connected
    return conn


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(health_router)
    return TestClient(app)


def test_ready_when_db_and_storage_ok(monkeypatch):
    monkeypatch.setattr(health_module, "get_connection", lambda: _conn(True))
    monkeypatch.setattr(health_module, "get_object_storage", lambda: _FakeStorage(True))
    resp = _client().get("/health/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"
    assert body["object_storage"] is True


def test_not_ready_when_storage_down(monkeypatch):
    monkeypatch.setattr(health_module, "get_connection", lambda: _conn(True))
    monkeypatch.setattr(health_module, "get_object_storage", lambda: _FakeStorage(False))
    resp = _client().get("/health/ready")
    assert resp.status_code == 503
    body = resp.json()
    assert body["status"] == "not_ready"
    assert body["object_storage"] is False
    assert body["database"] is True


def test_not_ready_when_storage_raises(monkeypatch):
    def _boom():
        raise RuntimeError("storage unreachable")

    monkeypatch.setattr(health_module, "get_connection", lambda: _conn(True))
    monkeypatch.setattr(health_module, "get_object_storage", _boom)
    resp = _client().get("/health/ready")
    assert resp.status_code == 503
    assert resp.json()["object_storage"] is False
