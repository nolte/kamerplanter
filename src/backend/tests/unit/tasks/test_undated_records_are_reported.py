"""#1806 GDPR-003 — the age-selector tasks report what they cannot judge.

``ai_audit_log``, ``mcp_audit_log`` and orphaned task photos are swept by age. A
record whose ``created_at`` is missing or unreadable is skipped (deleting it would
be a guess), and until now the run said nothing about it. The doubles here are
``spec``-bound to the real repositories: a counter the repository does not have
would raise instead of passing vacuously. What the SQL-level counters select is
measured against a real ArangoDB in ``tests/integration/test_undated_records_held_count.py``.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.data_access.arango.ai_repository import ArangoAiAuditRepository
from app.data_access.arango.attachment_repository import ArangoAttachmentRepository
from app.data_access.arango.mcp_repository import ArangoMcpAuditRepository


def test_the_ai_audit_task_logs_the_held_count():
    from app.tasks import ai_tasks

    repo = MagicMock(spec=ArangoAiAuditRepository)
    repo.delete_older_than.return_value = 4
    repo.count_undated.return_value = 2
    with (
        patch.object(ai_tasks, "get_db"),
        patch.object(ai_tasks, "ArangoAiAuditRepository", return_value=repo),
        patch.object(ai_tasks, "logger") as logger,
    ):
        removed = ai_tasks.cleanup_expired_audit_log()

    assert removed == 4
    assert logger.info.call_args.kwargs["held_undated"] == 2


def test_the_mcp_audit_task_logs_the_held_count():
    from app.tasks import mcp_tasks

    repo = MagicMock(spec=ArangoMcpAuditRepository)
    repo.delete_expired.return_value = 5
    repo.count_undated.return_value = 1
    with (
        patch.object(mcp_tasks, "get_db"),
        patch.object(mcp_tasks, "ArangoMcpAuditRepository", return_value=repo),
        patch.object(mcp_tasks, "logger") as logger,
    ):
        removed = mcp_tasks.cleanup_expired_audit_log()

    assert removed == 5
    assert logger.info.call_args.kwargs["held_undated"] == 1


async def test_the_orphan_sweep_reports_the_held_count():
    from app.tasks import storage_tasks

    repo = MagicMock(spec=ArangoAttachmentRepository)
    repo.find_orphaned_task_photos.return_value = []
    repo.count_undated_orphaned_task_photos.return_value = 6
    with (
        patch("app.common.dependencies.get_attachment_repo", return_value=repo),
        patch("app.common.dependencies.get_attachment_service", return_value=MagicMock()),
    ):
        result = await storage_tasks._cleanup_orphaned_task_photos(48, 500)

    assert result["held_undated"] == 6
    assert result["found"] == 0


class TestAFailingCountNeverFailsTheTask:
    """The held-count is a report; its failure must not abort the deletion work (code-review of #1945)."""

    def test_the_helper_returns_none_on_error(self):
        from app.common.held_count import held_undated_count

        def boom() -> int:
            raise ConnectionError("db down")

        assert held_undated_count(boom, task="t") is None
        assert held_undated_count(lambda: 4, task="t") == 4

    def test_the_unverified_cleanup_still_erases_when_the_count_fails(self):
        from types import SimpleNamespace
        from unittest.mock import AsyncMock

        from app.data_access.arango.user_repository import ArangoUserRepository
        from app.tasks.auth_tasks import cleanup_unverified_accounts

        repo = MagicMock(spec=ArangoUserRepository)
        repo.get_unverified_before.return_value = [SimpleNamespace(key="u1")]
        repo.count_unverified_undated.side_effect = ConnectionError("db down")
        service = MagicMock()
        service.erase_account_now = AsyncMock(return_value=SimpleNamespace(status="completed"))
        with (
            patch("app.common.dependencies.get_user_repo", return_value=repo),
            patch("app.common.dependencies.get_privacy_service", return_value=service),
        ):
            result = cleanup_unverified_accounts.run()

        assert result["removed"] == 1
        assert result["held_undated"] is None
