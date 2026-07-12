"""REQ-033 — smoke tests for the v0017 MCP migration + Celery cleanup tasks.

The injected ``StandardDatabase`` is doubled with MagicMock (owned I/O
boundary); the migration is verified for idempotency (fresh vs. already-applied)
and the retention tasks for delegation to the repositories.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.data_access.arango import collections as col
from app.migrations.versions.v0017_mcp_collections import migration


def _fresh_db() -> MagicMock:
    db = MagicMock()
    db.has_collection.return_value = False
    db.collection.return_value.indexes.return_value = []
    return db


def _applied_db() -> MagicMock:
    db = MagicMock()
    db.has_collection.return_value = True
    db.collection.return_value.indexes.return_value = [
        {"type": "persistent", "fields": ["service_account_key"]},
        {"type": "persistent", "fields": ["tenant_key", "created_at"]},
        {"type": "persistent", "fields": ["created_at"]},
        {"type": "persistent", "fields": ["service_account_key", "tenant_key", "tool_name", "idempotency_key"]},
        {"type": "persistent", "fields": ["expires_at"]},
    ]
    return db


def test_migration_metadata() -> None:
    assert migration.version == "0017"
    assert migration.name == "mcp_collections"
    assert migration.reversible is False


def test_dry_run_reports_pending_without_writing() -> None:
    db = _fresh_db()
    report = migration.up(db, dry_run=True)
    assert report.dry_run is True
    assert report.changed == 0
    db.create_collection.assert_not_called()


def test_up_creates_collections_and_indexes() -> None:
    db = _fresh_db()
    report = migration.up(db)
    created = {call.args[0] for call in db.create_collection.call_args_list}
    assert col.MCP_AUDIT_LOG in created
    assert col.MCP_IDEMPOTENCY_RECORD in created
    assert report.changed > 0


def test_up_is_idempotent_when_already_applied() -> None:
    db = _applied_db()
    report = migration.up(db)
    assert report.changed == 0
    db.create_collection.assert_not_called()


def test_audit_cleanup_task_delegates_to_repo() -> None:
    with (
        patch("app.tasks.mcp_tasks.ArangoConnection") as conn,
        patch("app.tasks.mcp_tasks.ArangoMcpAuditRepository") as repo_cls,
    ):
        conn.return_value.db = MagicMock()
        repo_cls.return_value.delete_expired.return_value = 5
        from app.tasks.mcp_tasks import cleanup_expired_audit_log

        assert cleanup_expired_audit_log() == 5


def test_idempotency_cleanup_task_delegates_to_repo() -> None:
    with (
        patch("app.tasks.mcp_tasks.ArangoConnection") as conn,
        patch("app.tasks.mcp_tasks.ArangoMcpIdempotencyRepository") as repo_cls,
    ):
        conn.return_value.db = MagicMock()
        repo_cls.return_value.delete_expired.return_value = 3
        from app.tasks.mcp_tasks import cleanup_expired_idempotency

        assert cleanup_expired_idempotency() == 3
