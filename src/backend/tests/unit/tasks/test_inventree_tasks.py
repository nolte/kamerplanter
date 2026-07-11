"""REQ-016 — unit tests for the InvenTree sync Celery tasks.

The scheduler-driven sync/push must build the :class:`InvenTreeService` with the
shared Valkey/Redis client injected, so the adapter's persistent per-connection
outbound rate-limit window (IT-005) is honoured on the Celery path too — not just
on the HTTP path. Without it the cap would silently degrade to a best-effort
in-memory window that resets on every task run.

Dependency getters are imported lazily inside the task body, so installing a mock
``app.common.dependencies`` module before the task runs is sufficient; no real
database, broker or Redis is touched.
"""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def _mock_deps(monkeypatch):
    mock_deps = ModuleType("app.common.dependencies")
    mock_deps._get_redis_client = MagicMock(name="_get_redis_client")  # type: ignore[attr-defined]
    mock_deps.get_encryption_engine = MagicMock(name="get_encryption_engine")  # type: ignore[attr-defined]
    mock_deps.get_inventree_repo = MagicMock(name="get_inventree_repo")  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "app.common.dependencies", mock_deps)
    return mock_deps


def test_run_per_connection_injects_shared_redis_client(monkeypatch, _mock_deps):
    """The Celery path builds the service with a non-None shared redis_client."""
    import app.domain.services.inventree_service as svc_mod
    from app.tasks import inventree_tasks

    sentinel_redis = object()
    _mock_deps._get_redis_client.return_value = sentinel_redis

    captured: dict = {}

    class CapturingService:
        def __init__(self, repo, encryption, adapter_factory=None, redis_client=None):
            captured["redis_client"] = redis_client

    monkeypatch.setattr(svc_mod, "InvenTreeService", CapturingService)
    # No active connections → the run builds the service, then returns at once.
    monkeypatch.setattr(inventree_tasks, "_active_connections", lambda: iter(()))

    result = inventree_tasks._run_per_connection("sync")

    assert result == {"connections": 0, "ok": 0, "errors": 0}
    # The shared client from the same factory as the HTTP path must be injected.
    assert captured["redis_client"] is sentinel_redis
    _mock_deps._get_redis_client.assert_called_once()
