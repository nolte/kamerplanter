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


def test_a_refused_index_retirement_is_reported_without_failing_readiness(monkeypatch):
    """#2064: a too-strict constraint is an operator's case, not a reason to leave rotation."""
    from app.migrations.support import retired_indexes

    refused = retired_indexes.RetiredIndexEnforcement(
        enforced=("tanks(name)", "activities(name)"), re_retired=(), refused=("tanks(name)",)
    )
    monkeypatch.setattr(retired_indexes, "_last", refused)
    monkeypatch.setattr(health_module, "get_connection", lambda: _conn(True))
    monkeypatch.setattr(health_module, "get_object_storage", lambda: _FakeStorage(True))

    resp = _client().get("/health/ready")

    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"
    assert resp.json()["retired_indexes_refused"] == 1
    assert "tanks" not in resp.text


def test_no_enforcement_yet_reports_zero(monkeypatch):
    from app.migrations.support import retired_indexes

    monkeypatch.setattr(retired_indexes, "_last", None)
    monkeypatch.setattr(health_module, "get_connection", lambda: _conn(True))
    monkeypatch.setattr(health_module, "get_object_storage", lambda: _FakeStorage(True))

    assert _client().get("/health/ready").json()["retired_indexes_refused"] == 0
