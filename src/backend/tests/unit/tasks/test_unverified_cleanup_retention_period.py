"""#1772 — the unverified-account cleanup waits the period NFR-011 R-02 declares.

NFR-011 R-02 (and its §4 ``UNVERIFIED_ACCOUNT_DAYS = 7``) and REQ-023 AK-17
give an unconfirmed account **7 days** before it is erased. The task carried a
literal ``timedelta(hours=72)`` instead — three days, from a period no setting
named. The period now comes from ``settings.retention_unverified_account_days``
through :class:`RetentionService`, the one place the R-02 cutoff is computed.

The tests drive the real Celery task: the cutoff is read off the argument the
task hands to ``get_unverified_before``, not recomputed next to it.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from app.config.settings import Settings, settings
from app.tasks.auth_tasks import cleanup_unverified_accounts

#: Slack for the wall clock between the task's ``now`` and the test's.
_CLOCK_SLACK = timedelta(seconds=30)


def _cutoff_the_task_uses() -> datetime:
    repo = MagicMock()
    repo.get_unverified_before.return_value = []
    with patch("app.common.dependencies.get_user_repo", return_value=repo):
        cleanup_unverified_accounts.run()
    repo.get_unverified_before.assert_called_once()
    return datetime.fromisoformat(repo.get_unverified_before.call_args.args[0])


class TestTheCleanupCutoffFollowsTheSetting:
    def test_the_default_cutoff_is_seven_days_back(self):
        """NFR-011 R-02 / REQ-023 AK-17: an unverified account lives 7 days, not 72 hours."""
        cutoff = _cutoff_the_task_uses()

        expected = datetime.now(UTC) - timedelta(days=7)
        assert abs(cutoff - expected) < _CLOCK_SLACK

    def test_a_configured_period_moves_the_cutoff(self, monkeypatch):
        monkeypatch.setattr(settings, "retention_unverified_account_days", 10)

        cutoff = _cutoff_the_task_uses()

        expected = datetime.now(UTC) - timedelta(days=10)
        assert abs(cutoff - expected) < _CLOCK_SLACK


class TestTheR02Setting:
    def test_the_default_is_the_spec_period(self):
        """NFR-011 R-02 / §4 ``UNVERIFIED_ACCOUNT_DAYS = 7`` and REQ-023 AK-17 name 7 days."""
        assert Settings.model_fields["retention_unverified_account_days"].default == 7

    def test_zero_days_is_refused(self):
        # ``0`` would erase an account the moment it registered, before its
        # confirmation mail could arrive. The positive case first: without it a
        # field that does not exist at all is refused too, and the test is vacuous.
        assert Settings(retention_unverified_account_days=1).retention_unverified_account_days == 1
        with pytest.raises(ValidationError):
            Settings(retention_unverified_account_days=0)
