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
