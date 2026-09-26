"""Unit tests for NFR-011 retention Celery tasks (REQ-025).

Mocks ``app.common.dependencies`` and doubles the async PrivacyService methods
with ``AsyncMock``. The ``run_async_task`` bridge runs the real task coroutine on
a loop-isolated worker thread (no real database is touched). Tests assert the
result dict and error propagation.
"""

import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

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
        service = MagicMock()
        service.process_data_export = AsyncMock(return_value=SimpleNamespace(status="completed", file_size_bytes=1024))
        _mock_dependencies.get_privacy_service.return_value = service

        from app.tasks.retention_tasks import process_data_export

        result = process_data_export("export_1")

        assert result == {"export_key": "export_1", "status": "completed"}
        # A first, direct call is attempt 1 of 6: not final, not a retry (#1666).
        service.process_data_export.assert_awaited_once_with("export_1", final_attempt=False, is_retry=False)

    def test_handles_none_result(self, _mock_dependencies):
        service = MagicMock()
        service.process_data_export = AsyncMock(return_value=None)
        _mock_dependencies.get_privacy_service.return_value = service

        from app.tasks.retention_tasks import process_data_export

        result = process_data_export("export_1")

        assert result == {"export_key": "export_1", "status": "unknown"}

    def test_reraises_on_failure(self, _mock_dependencies):
        service = MagicMock()
        service.process_data_export = AsyncMock(side_effect=RuntimeError("boom"))
        _mock_dependencies.get_privacy_service.return_value = service

        from app.tasks.retention_tasks import process_data_export

        with pytest.raises(RuntimeError, match="boom"):
            process_data_export("export_1")


class TestExecuteScheduledErasures:
    def test_returns_processed_count(self, _mock_dependencies):
        service = MagicMock()
        service.execute_scheduled_erasures = AsyncMock(return_value=3)
        _mock_dependencies.get_privacy_service.return_value = service

        from app.tasks.retention_tasks import execute_scheduled_erasures

        result = execute_scheduled_erasures()

        assert result == {"processed": 3}

    def test_reraises_on_failure(self, _mock_dependencies):
        service = MagicMock()
        service.execute_scheduled_erasures = AsyncMock(side_effect=RuntimeError("db down"))
        _mock_dependencies.get_privacy_service.return_value = service

        from app.tasks.retention_tasks import execute_scheduled_erasures

        with pytest.raises(RuntimeError):
            execute_scheduled_erasures()


class TestExpireEmailChangeRequests:
    def test_returns_expired_count(self, _mock_dependencies):
        service = MagicMock()
        service.expire_email_change_requests = AsyncMock(return_value=2)
        _mock_dependencies.get_privacy_service.return_value = service

        from app.tasks.retention_tasks import expire_email_change_requests

        result = expire_email_change_requests()

        assert result == {"expired": 2}


class TestPurgeExpiredConsentRecords:
    """NFR-011 R-04 (#1800): the beat task delegates to the service, no AQL of its own (NFR-001)."""

    def test_returns_purged_count(self, _mock_dependencies):
        service = MagicMock()
        service.purge_expired_consent_records = AsyncMock(return_value=4)
        _mock_dependencies.get_privacy_service.return_value = service

        from app.tasks.retention_tasks import purge_expired_consent_records

        result = purge_expired_consent_records()

        assert result == {"purged": 4}

    def test_the_task_is_registered_on_the_daily_beat(self):
        from app.tasks import celery_app

        entries = [
            e for e in celery_app.conf.beat_schedule.values() if e["task"] == "retention.purge_expired_consent_records"
        ]
        assert len(entries) == 1


class TestAnonymizeConsentIps:
    """NFR-011 R-04a (#1800): the R-03 analogue for consent-record IPs."""

    def test_returns_anonymized_count(self, _mock_dependencies):
        service = MagicMock()
        service.anonymize_consent_ips = AsyncMock(return_value=3)
        _mock_dependencies.get_privacy_service.return_value = service

        from app.tasks.retention_tasks import anonymize_consent_ips

        result = anonymize_consent_ips()

        assert result == {"anonymized": 3}

    def test_the_task_is_registered_on_the_daily_beat(self):
        from app.tasks import celery_app

        entries = [e for e in celery_app.conf.beat_schedule.values() if e["task"] == "retention.anonymize_consent_ips"]
        assert len(entries) == 1

    def test_the_task_does_not_double_log_the_service_s_own_event(self, _mock_dependencies):
        """#1800 /code-review — the service already logs the completion event; the task must not repeat it."""
        import structlog.testing

        service = MagicMock()
        service.anonymize_consent_ips = AsyncMock(return_value=2)
        _mock_dependencies.get_privacy_service.return_value = service

        from app.tasks.retention_tasks import anonymize_consent_ips

        with structlog.testing.capture_logs() as logs:
            anonymize_consent_ips()

        completed = [e for e in logs if e["event"] == "retention.anonymize_consent_ips.completed"]
        assert completed == [], "the task must not log this event itself — the service (mocked here) already does"


class TestExpireDataExports:
    def test_returns_expired_count(self, _mock_dependencies):
        service = MagicMock()
        service.expire_data_exports = AsyncMock(return_value=1)
        _mock_dependencies.get_privacy_service.return_value = service

        from app.tasks.retention_tasks import expire_data_exports

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
            "purge_expired_erasure_records",
            "purge_expired_consent_records",
            "anonymize_consent_ips",
        ],
    )
    def test_beat_tasks_retry_on_transient_transport_errors(self, task_name):
        import app.tasks.retention_tasks as mod

        task = getattr(mod, task_name)
        assert task.max_retries == 3
        assert ConnectionError in task.autoretry_for
        assert TimeoutError in task.autoretry_for
        assert task.default_retry_delay == 300
