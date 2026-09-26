"""Unit tests for the tenant-maintenance Celery task (REQ-024).

The task module imports ``get_invitation_repo`` at module level, so the mock
``app.common.dependencies`` module is installed before import. Tests assert
the result dict and that the repo cleanup is delegated to.
"""

import sys
from datetime import UTC, datetime, timedelta
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def _task_module(monkeypatch):
    """Import the task module once, then patch its module-level getters.

    The task module captures ``get_invitation_repo`` at import time, so the
    binding is overridden directly on the module rather than relying on
    re-import (which is unreliable across a shared pytest session).
    """
    mock_deps = ModuleType("app.common.dependencies")
    mock_deps.get_invitation_repo = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_tenant_service = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_retention_service = MagicMock()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "app.common.dependencies", mock_deps)

    import app.tasks.tenant_tasks as module

    monkeypatch.setattr(module, "get_invitation_repo", mock_deps.get_invitation_repo)
    monkeypatch.setattr(module, "get_tenant_service", mock_deps.get_tenant_service)
    monkeypatch.setattr(module, "get_retention_service", mock_deps.get_retention_service)

    deps = SimpleNamespace(
        get_invitation_repo=mock_deps.get_invitation_repo,
        get_tenant_service=mock_deps.get_tenant_service,
        get_retention_service=mock_deps.get_retention_service,
    )
    yield module, deps


class TestCleanupExpiredInvitations:
    def _repo(self, deps, *, cleanup: int = 0, purged: int = 0) -> MagicMock:
        repo = MagicMock()
        repo.cleanup_expired.return_value = cleanup
        repo.delete_expired_before.return_value = purged
        deps.get_invitation_repo.return_value = repo
        retention = MagicMock()
        retention.invitation_purge_cutoff.return_value = datetime(2026, 8, 27, tzinfo=UTC)
        deps.get_retention_service.return_value = retention
        return repo

    def test_returns_count_from_repo(self, _task_module):
        module, deps = _task_module
        repo = self._repo(deps, cleanup=5)

        result = module.cleanup_expired_invitations()

        assert result == {"expired_count": 5, "purged_count": 0}
        (now_arg,) = repo.cleanup_expired.call_args.kwargs.values()
        assert now_arg.tzinfo is not None

    def test_zero_when_nothing_expired(self, _task_module):
        module, deps = _task_module
        self._repo(deps, cleanup=0)

        result = module.cleanup_expired_invitations()

        assert result == {"expired_count": 0, "purged_count": 0}

    def test_hard_deletes_invitations_expired_past_the_r12_period(self, _task_module):
        """NFR-011 R-12 (#1800): an ``expired`` invitation is hard-deleted 30 days after ``expires_at``.

        Until #1800 nothing hard-deleted one; the invitee address (and the rest
        of the document) stayed forever after the status flip.
        """
        module, deps = _task_module
        repo = self._repo(deps, cleanup=0, purged=3)

        result = module.cleanup_expired_invitations()

        assert result == {"expired_count": 0, "purged_count": 3}
        retention = deps.get_retention_service.return_value
        (now_arg,) = retention.invitation_purge_cutoff.call_args.args
        assert now_arg.tzinfo is not None
        (cutoff_arg,) = repo.delete_expired_before.call_args.args
        assert cutoff_arg == retention.invitation_purge_cutoff.return_value.isoformat()

    def test_cleanup_and_purge_use_the_same_instant(self, _task_module):
        """The status flip and the purge cutoff are both derived from one ``now`` (no drift between them)."""
        module, deps = _task_module
        repo = self._repo(deps)
        captured: dict[str, datetime] = {}

        def _cutoff(now: datetime) -> datetime:
            captured["cutoff_now"] = now
            return now - timedelta(days=30)

        deps.get_retention_service.return_value.invitation_purge_cutoff.side_effect = _cutoff

        module.cleanup_expired_invitations()

        (cleanup_now,) = repo.cleanup_expired.call_args.kwargs.values()
        assert captured["cutoff_now"] == cleanup_now


class TestResumeTenantErasures:
    """#1769 — the beat hands the run to the service with an aware UTC clock and returns its counts."""

    def test_delegates_to_the_service(self, _task_module):
        module, deps = _task_module
        service = MagicMock()
        service.resume_tenant_erasures.return_value = {"candidates": 1, "completed": 1}
        deps.get_tenant_service.return_value = service

        result = module.resume_tenant_erasures()

        assert result == {"candidates": 1, "completed": 1}
        (now,) = service.resume_tenant_erasures.call_args.args
        assert now.tzinfo is not None
