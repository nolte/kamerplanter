"""Unit tests for NFR-011 retention Celery tasks (REQ-025).

Mocks ``app.common.dependencies`` and ``asyncio.run`` so the async PrivacyService
is exercised through a synchronous double. No real database or event loop is
touched. Tests assert the result dict and error propagation.
"""

import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _mock_dependencies(monkeypatch):
    mock_deps = ModuleType("app.common.dependencies")
    mock_deps.get_privacy_service = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_data_export_repo = MagicMock()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "app.common.dependencies", mock_deps)

    yield mock_deps


class TestProcessDataExport:
    def test_returns_status_from_result(self, _mock_dependencies):
        _mock_dependencies.get_privacy_service.return_value = MagicMock()

        from app.tasks.retention_tasks import process_data_export

        with patch("asyncio.run") as run:
            run.return_value = SimpleNamespace(status="completed", file_size_bytes=1024)
            result = process_data_export("export_1")

        assert result == {"export_key": "export_1", "status": "completed"}

    def test_handles_none_result(self, _mock_dependencies):
        _mock_dependencies.get_privacy_service.return_value = MagicMock()

        from app.tasks.retention_tasks import process_data_export

        with patch("asyncio.run") as run:
            run.return_value = None
            result = process_data_export("export_1")

        assert result == {"export_key": "export_1", "status": "unknown"}

    def test_reraises_on_failure(self, _mock_dependencies):
        _mock_dependencies.get_privacy_service.return_value = MagicMock()

        from app.tasks.retention_tasks import process_data_export

        with patch("asyncio.run") as run:
            run.side_effect = RuntimeError("boom")
            with pytest.raises(RuntimeError, match="boom"):
                process_data_export("export_1")


class TestExecuteScheduledErasures:
    def test_returns_processed_count(self, _mock_dependencies):
        _mock_dependencies.get_privacy_service.return_value = MagicMock()

        from app.tasks.retention_tasks import execute_scheduled_erasures

        with patch("asyncio.run") as run:
            run.return_value = 3
            result = execute_scheduled_erasures()

        assert result == {"processed": 3}

    def test_reraises_on_failure(self, _mock_dependencies):
        _mock_dependencies.get_privacy_service.return_value = MagicMock()

        from app.tasks.retention_tasks import execute_scheduled_erasures

        with patch("asyncio.run") as run:
            run.side_effect = RuntimeError("db down")
            with pytest.raises(RuntimeError):
                execute_scheduled_erasures()


class TestExpireEmailChangeRequests:
    def test_returns_expired_count(self, _mock_dependencies):
        _mock_dependencies.get_privacy_service.return_value = MagicMock()

        from app.tasks.retention_tasks import expire_email_change_requests

        with patch("asyncio.run") as run:
            run.return_value = 2
            result = expire_email_change_requests()

        assert result == {"expired": 2}


class TestExpireDataExports:
    def test_returns_expired_count(self, _mock_dependencies):
        _mock_dependencies.get_privacy_service.return_value = MagicMock()

        from app.tasks.retention_tasks import expire_data_exports

        with patch("asyncio.run") as run:
            run.return_value = 1
            result = expire_data_exports()

        assert result == {"expired": 1}


class TestRedispatchStalePendingExports:
    def test_redispatches_each_stale_export(self, _mock_dependencies):
        repo = MagicMock()
        repo.list_stale_pending.return_value = [
            SimpleNamespace(key="export_1"),
            SimpleNamespace(key="export_2"),
        ]
        _mock_dependencies.get_data_export_repo.return_value = repo

        from app.tasks.retention_tasks import redispatch_stale_pending_exports

        with patch("app.tasks.retention_tasks.process_data_export.delay") as delay:
            result = redispatch_stale_pending_exports()

        assert result == {"redispatched": 2}
        assert delay.call_count == 2
        delay.assert_any_call("export_1")
        delay.assert_any_call("export_2")

    def test_empty_returns_zero(self, _mock_dependencies):
        repo = MagicMock()
        repo.list_stale_pending.return_value = []
        _mock_dependencies.get_data_export_repo.return_value = repo

        from app.tasks.retention_tasks import redispatch_stale_pending_exports

        with patch("app.tasks.retention_tasks.process_data_export.delay") as delay:
            result = redispatch_stale_pending_exports()

        assert result == {"redispatched": 0}
        delay.assert_not_called()

    def test_skips_exports_without_key(self, _mock_dependencies):
        repo = MagicMock()
        repo.list_stale_pending.return_value = [
            SimpleNamespace(key=None),
            SimpleNamespace(key="export_2"),
        ]
        _mock_dependencies.get_data_export_repo.return_value = repo

        from app.tasks.retention_tasks import redispatch_stale_pending_exports

        with patch("app.tasks.retention_tasks.process_data_export.delay") as delay:
            result = redispatch_stale_pending_exports()

        assert result == {"redispatched": 2}  # count is the query result length
        delay.assert_called_once_with("export_2")


class TestRetryHardening:
    """INF-L3 — every retention task must carry retry configuration."""

    def test_process_data_export_has_retry_config(self):
        from app.tasks.retention_tasks import process_data_export

        assert process_data_export.max_retries == 5
        assert Exception in process_data_export.autoretry_for
        assert process_data_export.retry_backoff is True
        assert process_data_export.retry_backoff_max == 600

    @pytest.mark.parametrize(
        "task_name",
        [
            "execute_scheduled_erasures",
            "expire_email_change_requests",
            "expire_data_exports",
            "redispatch_stale_pending_exports",
        ],
    )
    def test_beat_tasks_retry_on_transient_transport_errors(self, task_name):
        import app.tasks.retention_tasks as mod

        task = getattr(mod, task_name)
        assert task.max_retries == 3
        assert ConnectionError in task.autoretry_for
        assert TimeoutError in task.autoretry_for
        assert task.default_retry_delay == 300
