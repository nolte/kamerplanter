"""Unit tests for the tenant-maintenance Celery task (REQ-024).

The task module imports ``get_invitation_repo`` at module level, so the mock
``app.common.dependencies`` module is installed before import. Tests assert
the result dict and that the repo cleanup is delegated to.
"""

import sys
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
    monkeypatch.setitem(sys.modules, "app.common.dependencies", mock_deps)

    import app.tasks.tenant_tasks as module

    monkeypatch.setattr(module, "get_invitation_repo", mock_deps.get_invitation_repo)
    monkeypatch.setattr(module, "get_tenant_service", mock_deps.get_tenant_service)

    deps = SimpleNamespace(
        get_invitation_repo=mock_deps.get_invitation_repo,
        get_tenant_service=mock_deps.get_tenant_service,
    )
    yield module, deps


class TestCleanupExpiredInvitations:
    def test_returns_count_from_repo(self, _task_module):
        module, deps = _task_module
        repo = MagicMock()
        repo.cleanup_expired.return_value = 5
        deps.get_invitation_repo.return_value = repo

        result = module.cleanup_expired_invitations()

        assert result == {"expired_count": 5}
        repo.cleanup_expired.assert_called_once_with()

    def test_zero_when_nothing_expired(self, _task_module):
        module, deps = _task_module
        repo = MagicMock()
        repo.cleanup_expired.return_value = 0
        deps.get_invitation_repo.return_value = repo

        result = module.cleanup_expired_invitations()

        assert result == {"expired_count": 0}


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
