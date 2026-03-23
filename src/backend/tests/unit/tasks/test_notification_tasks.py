"""Unit tests for notification Celery tasks (REQ-030).

Mocks the dependency module before importing the task functions
to avoid triggering the ArangoDB import chain.
"""

import sys
from datetime import UTC, datetime
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _mock_dependencies(monkeypatch):
    """Mock app.common.dependencies to avoid ArangoDB import chain.

    This fixture installs a mock module that provides the dependency
    functions needed by notification_tasks. It runs before each test.
    """
    # Create a mock dependencies module
    mock_deps = ModuleType("app.common.dependencies")
    mock_deps.get_task_repo = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_notification_service = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_tenant_repo = MagicMock()  # type: ignore[attr-defined]

    # Inject mock module
    monkeypatch.setitem(sys.modules, "app.common.dependencies", mock_deps)

    # Also need to handle the enums import
    # (enums should be importable normally, so we don't mock it)

    yield mock_deps

    # Cleanup: remove cached notification_tasks so it re-imports fresh
    if "app.tasks.notification_tasks" in sys.modules:
        del sys.modules["app.tasks.notification_tasks"]


class TestDispatchDueCareNotifications:
    def test_no_due_tasks(self, _mock_dependencies):
        mock_repo = MagicMock()
        mock_repo.get_all.return_value = ([], 0)
        _mock_dependencies.get_task_repo.return_value = mock_repo
        _mock_dependencies.get_notification_service.return_value = MagicMock()

        from app.tasks.notification_tasks import dispatch_due_care_notifications

        result = dispatch_due_care_notifications()

        assert result["status"] == "empty"
        assert result["tasks_found"] == 0

    def test_dispatches_due_tasks(self, _mock_dependencies):
        today = datetime.now(UTC)
        mock_repo = MagicMock()
        mock_repo.get_all.return_value = (
            [
                {
                    "category": "care_reminder",
                    "status": "pending",
                    "due_date": today.isoformat(),
                    "priority": "medium",
                    "name": "Monstera \u2014 watering",
                    "plant_key": "p1",
                    "assigned_to": "user_1",
                    "tenant_key": "tenant_1",
                },
            ],
            1,
        )
        _mock_dependencies.get_task_repo.return_value = mock_repo

        mock_service = MagicMock()
        _mock_dependencies.get_notification_service.return_value = mock_service

        with patch("asyncio.run") as mock_asyncio_run:
            mock_asyncio_run.return_value = {
                "users_notified": 1,
                "total_sent": 1,
            }

            from app.tasks.notification_tasks import (
                dispatch_due_care_notifications,
            )

            result = dispatch_due_care_notifications()

        assert result["status"] == "complete"
        assert result["tasks_found"] == 1

    def test_skips_non_care_tasks(self, _mock_dependencies):
        today = datetime.now(UTC)
        mock_repo = MagicMock()
        mock_repo.get_all.return_value = (
            [
                {
                    "category": "manual",
                    "status": "pending",
                    "due_date": today.isoformat(),
                    "name": "Some manual task",
                    "tenant_key": "tenant_1",
                },
            ],
            1,
        )
        _mock_dependencies.get_task_repo.return_value = mock_repo
        _mock_dependencies.get_notification_service.return_value = MagicMock()

        from app.tasks.notification_tasks import dispatch_due_care_notifications

        result = dispatch_due_care_notifications()

        assert result["status"] == "empty"

    def test_skips_completed_tasks(self, _mock_dependencies):
        today = datetime.now(UTC)
        mock_repo = MagicMock()
        mock_repo.get_all.return_value = (
            [
                {
                    "category": "care_reminder",
                    "status": "completed",
                    "due_date": today.isoformat(),
                    "name": "Monstera \u2014 watering",
                    "tenant_key": "tenant_1",
                },
            ],
            1,
        )
        _mock_dependencies.get_task_repo.return_value = mock_repo
        _mock_dependencies.get_notification_service.return_value = MagicMock()

        from app.tasks.notification_tasks import dispatch_due_care_notifications

        result = dispatch_due_care_notifications()

        assert result["status"] == "empty"


class TestEscalateOverdueNotifications:
    def test_processes_tenants(self, _mock_dependencies):
        mock_tenant_repo = MagicMock()
        mock_tenant_repo.get_all.return_value = (
            [{"_key": "tenant_1"}, {"_key": "tenant_2"}],
            2,
        )
        _mock_dependencies.get_tenant_repo.return_value = mock_tenant_repo

        mock_service = MagicMock()
        mock_engine = MagicMock()
        mock_engine.escalate_overdue = AsyncMock(
            return_value={"escalated": 1}
        )
        mock_service._engine = mock_engine
        _mock_dependencies.get_notification_service.return_value = mock_service

        with patch("asyncio.run") as mock_asyncio_run:
            mock_asyncio_run.return_value = {"escalated": 1}

            from app.tasks.notification_tasks import (
                escalate_overdue_notifications,
            )

            result = escalate_overdue_notifications()

        assert result["status"] == "complete"
        assert result["tenants_processed"] == 2

    def test_no_tenants(self, _mock_dependencies):
        mock_tenant_repo = MagicMock()
        mock_tenant_repo.get_all.return_value = ([], 0)
        _mock_dependencies.get_tenant_repo.return_value = mock_tenant_repo
        _mock_dependencies.get_notification_service.return_value = MagicMock()

        from app.tasks.notification_tasks import escalate_overdue_notifications

        result = escalate_overdue_notifications()

        assert result["status"] == "complete"
        assert result["total_escalated"] == 0

    def test_handles_tenant_failure(self, _mock_dependencies):
        mock_tenant_repo = MagicMock()
        mock_tenant_repo.get_all.return_value = (
            [{"_key": "tenant_1"}],
            1,
        )
        _mock_dependencies.get_tenant_repo.return_value = mock_tenant_repo

        mock_service = MagicMock()
        _mock_dependencies.get_notification_service.return_value = mock_service

        with patch("asyncio.run") as mock_asyncio_run:
            mock_asyncio_run.side_effect = RuntimeError("connection failed")

            from app.tasks.notification_tasks import (
                escalate_overdue_notifications,
            )

            result = escalate_overdue_notifications()

        # Should not crash, graceful degradation
        assert result["status"] == "complete"
        assert result["total_escalated"] == 0


class TestSendDailySummary:
    def test_no_tasks(self, _mock_dependencies):
        mock_repo = MagicMock()
        mock_repo.get_all.return_value = ([], 0)
        _mock_dependencies.get_task_repo.return_value = mock_repo
        _mock_dependencies.get_notification_service.return_value = MagicMock()

        from app.tasks.notification_tasks import send_daily_summary

        result = send_daily_summary()

        assert result["status"] == "complete"
        assert result["summaries_sent"] == 0

    def test_sends_summary_when_enabled(self, _mock_dependencies):
        from app.domain.models.notification import (
            DailySummaryPreference,
            NotificationPreferences,
        )

        today = datetime.now(UTC)
        mock_repo = MagicMock()
        mock_repo.get_all.return_value = (
            [
                {
                    "category": "care_reminder",
                    "status": "pending",
                    "due_date": today.isoformat(),
                    "name": "Monstera \u2014 watering",
                    "assigned_to": "user_1",
                    "tenant_key": "tenant_1",
                },
            ],
            1,
        )
        _mock_dependencies.get_task_repo.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.get_preferences.return_value = NotificationPreferences(
            user_key="user_1",
            daily_summary=DailySummaryPreference(enabled=True),
        )
        _mock_dependencies.get_notification_service.return_value = mock_service

        with patch("asyncio.run") as mock_asyncio_run:
            mock_asyncio_run.return_value = {"status": "delivered"}

            from app.tasks.notification_tasks import send_daily_summary

            result = send_daily_summary()

        assert result["status"] == "complete"
        assert result["summaries_sent"] == 1

    def test_skips_when_disabled(self, _mock_dependencies):
        from app.domain.models.notification import (
            DailySummaryPreference,
            NotificationPreferences,
        )

        today = datetime.now(UTC)
        mock_repo = MagicMock()
        mock_repo.get_all.return_value = (
            [
                {
                    "category": "care_reminder",
                    "status": "pending",
                    "due_date": today.isoformat(),
                    "name": "Monstera \u2014 watering",
                    "assigned_to": "user_1",
                    "tenant_key": "tenant_1",
                },
            ],
            1,
        )
        _mock_dependencies.get_task_repo.return_value = mock_repo

        mock_service = MagicMock()
        mock_service.get_preferences.return_value = NotificationPreferences(
            user_key="user_1",
            daily_summary=DailySummaryPreference(enabled=False),
        )
        _mock_dependencies.get_notification_service.return_value = mock_service

        from app.tasks.notification_tasks import send_daily_summary

        result = send_daily_summary()

        assert result["summaries_sent"] == 0


class TestSendEmailDigests:
    def test_placeholder_returns_zero(self):
        from app.tasks.notification_tasks import send_email_digests

        result = send_email_digests()

        assert result["status"] == "complete"
        assert result["digests_sent"] == 0
