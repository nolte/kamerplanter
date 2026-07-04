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
    mock_deps.get_notification_preference_repo = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_user_repo = MagicMock()  # type: ignore[attr-defined]

    # Inject mock module
    monkeypatch.setitem(sys.modules, "app.common.dependencies", mock_deps)

    # Also need to handle the enums import
    # (enums should be importable normally, so we don't mock it)

    yield mock_deps


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
        mock_engine.escalate_overdue = AsyncMock(return_value={"escalated": 1})
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
    @staticmethod
    def _prefs(user_key: str, config: dict):
        from app.domain.models.notification import (
            ChannelPreference,
            NotificationPreferences,
        )

        return NotificationPreferences(
            user_key=user_key,
            channels={"email": ChannelPreference(enabled=True, config=config)},
        )

    def test_no_candidates_sends_nothing(self, _mock_dependencies):
        pref_repo = MagicMock()
        pref_repo.list_users_with_digest_enabled.return_value = []
        _mock_dependencies.get_notification_preference_repo.return_value = pref_repo

        mock_service = MagicMock()
        _mock_dependencies.get_notification_service.return_value = mock_service
        _mock_dependencies.get_user_repo.return_value = MagicMock()

        from app.tasks.notification_tasks import send_email_digests

        result = send_email_digests()

        assert result["status"] == "complete"
        assert result["candidates"] == 0
        assert result["digests_sent"] == 0
        mock_service.send_email_digest.assert_not_called()

    def test_sends_one_digest_per_user(self, _mock_dependencies):
        pref_repo = MagicMock()
        pref_repo.list_users_with_digest_enabled.return_value = [
            self._prefs("user_1", {"email": "a@x", "digest": True}),
            self._prefs("user_2", {"email": "b@x", "digest": True}),
        ]
        _mock_dependencies.get_notification_preference_repo.return_value = pref_repo

        mock_service = MagicMock()
        _mock_dependencies.get_notification_service.return_value = mock_service
        _mock_dependencies.get_user_repo.return_value = MagicMock()

        with patch("asyncio.run") as mock_asyncio_run:
            mock_asyncio_run.return_value = {"status": "sent", "count": 3}

            from app.tasks.notification_tasks import send_email_digests

            result = send_email_digests()

        assert result["digests_sent"] == 2
        assert result["digests_empty"] == 0
        assert result["digests_failed"] == 0
        # Two coroutines created — one per user with the resolved address.
        assert mock_service.send_email_digest.call_count == 2
        called_addresses = {c.args[1] for c in mock_service.send_email_digest.call_args_list}
        assert called_addresses == {"a@x", "b@x"}
        # since-window is roughly now - 24h
        since_arg = mock_service.send_email_digest.call_args_list[0].args[2]
        delta = datetime.now(UTC) - since_arg
        assert abs(delta.total_seconds() - 24 * 3600) < 120

    def test_address_fallback_to_user_email(self, _mock_dependencies):
        from types import SimpleNamespace

        pref_repo = MagicMock()
        pref_repo.list_users_with_digest_enabled.return_value = [
            self._prefs("user_1", {"digest": True}),  # no email in config
        ]
        _mock_dependencies.get_notification_preference_repo.return_value = pref_repo

        user_repo = MagicMock()
        user_repo.get_by_key.return_value = SimpleNamespace(email="fallback@x")
        _mock_dependencies.get_user_repo.return_value = user_repo

        mock_service = MagicMock()
        _mock_dependencies.get_notification_service.return_value = mock_service

        with patch("asyncio.run") as mock_asyncio_run:
            mock_asyncio_run.return_value = {"status": "sent", "count": 1}

            from app.tasks.notification_tasks import send_email_digests

            result = send_email_digests()

        assert result["digests_sent"] == 1
        user_repo.get_by_key.assert_called_once_with("user_1")
        assert mock_service.send_email_digest.call_args.args[1] == "fallback@x"

    def test_missing_address_counts_failed(self, _mock_dependencies):
        pref_repo = MagicMock()
        pref_repo.list_users_with_digest_enabled.return_value = [
            self._prefs("user_1", {"digest": True}),
        ]
        _mock_dependencies.get_notification_preference_repo.return_value = pref_repo

        user_repo = MagicMock()
        user_repo.get_by_key.return_value = None
        _mock_dependencies.get_user_repo.return_value = user_repo

        mock_service = MagicMock()
        _mock_dependencies.get_notification_service.return_value = mock_service

        from app.tasks.notification_tasks import send_email_digests

        result = send_email_digests()

        assert result["digests_failed"] == 1
        assert result["digests_sent"] == 0
        mock_service.send_email_digest.assert_not_called()

    def test_per_user_failure_does_not_abort(self, _mock_dependencies):
        pref_repo = MagicMock()
        pref_repo.list_users_with_digest_enabled.return_value = [
            self._prefs("user_1", {"email": "a@x", "digest": True}),
            self._prefs("user_2", {"email": "b@x", "digest": True}),
        ]
        _mock_dependencies.get_notification_preference_repo.return_value = pref_repo
        _mock_dependencies.get_user_repo.return_value = MagicMock()

        mock_service = MagicMock()
        _mock_dependencies.get_notification_service.return_value = mock_service

        with patch("asyncio.run") as mock_asyncio_run:
            mock_asyncio_run.side_effect = [
                RuntimeError("boom"),
                {"status": "sent", "count": 2},
            ]

            from app.tasks.notification_tasks import send_email_digests

            result = send_email_digests()

        assert result["digests_sent"] == 1
        assert result["digests_failed"] == 1

    def test_empty_window_counts_empty(self, _mock_dependencies):
        pref_repo = MagicMock()
        pref_repo.list_users_with_digest_enabled.return_value = [
            self._prefs("user_1", {"email": "a@x", "digest": True}),
        ]
        _mock_dependencies.get_notification_preference_repo.return_value = pref_repo
        _mock_dependencies.get_user_repo.return_value = MagicMock()

        mock_service = MagicMock()
        _mock_dependencies.get_notification_service.return_value = mock_service

        with patch("asyncio.run") as mock_asyncio_run:
            mock_asyncio_run.return_value = {"status": "empty", "count": 0}

            from app.tasks.notification_tasks import send_email_digests

            result = send_email_digests()

        assert result["digests_empty"] == 1
        assert result["digests_sent"] == 0

    def test_has_retry_config(self):
        from app.tasks.notification_tasks import send_email_digests

        assert send_email_digests.max_retries == 3
        assert ConnectionError in send_email_digests.autoretry_for
        assert TimeoutError in send_email_digests.autoretry_for
