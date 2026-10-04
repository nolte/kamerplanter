"""``security_audit.purge_expired`` (NFR-011 R-38, #2111): scheduled, bound to the fixed 730 days, really constructible.

The sibling retention tasks of ``mcp_tasks`` / ``ai_tasks`` / ``glossary_tasks`` call ``ArangoConnection()`` with no
argument while its constructor requires the settings: measured, they raise ``TypeError`` the first time the beat
fires them, and their unit tests passed because those tests replace the class with a bare ``MagicMock``. This task
is tested against the class's own signature (``autospec``), so the same slip cannot pass here.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.config.settings import settings
from app.domain.services.security_audit_service import SECURITY_AUDIT_RETENTION_DAYS
from app.tasks import celery_app


def test_the_task_deletes_with_the_fixed_window_and_reports_the_held_rows() -> None:
    with (
        patch("app.tasks.security_audit_tasks.ArangoConnection", autospec=True) as connection,
        patch("app.tasks.security_audit_tasks.ArangoSecurityAuditRepository") as repo_cls,
    ):
        repo = MagicMock()
        repo.delete_expired.return_value = 4
        repo.count_undated.return_value = 0
        repo_cls.return_value = repo
        from app.tasks.security_audit_tasks import purge_expired_security_audit_log

        removed = purge_expired_security_audit_log()

    assert removed == 4
    connection.assert_called_once_with(settings)  # the constructor requires the settings
    repo.delete_expired.assert_called_once_with(retention_days=SECURITY_AUDIT_RETENTION_DAYS)
    assert SECURITY_AUDIT_RETENTION_DAYS == 730


def test_the_task_is_in_the_beat_schedule() -> None:
    entries = [e for e in celery_app.conf.beat_schedule.values() if e["task"] == "security_audit.purge_expired"]

    assert len(entries) == 1
