"""REQ-035 — smoke tests for the v0016 glossary migration + Celery cleanup task.

The injected ``StandardDatabase`` is doubled with MagicMock (owned I/O boundary);
the migration is verified for idempotency (fresh vs. already-applied) and the
cleanup task for delegation to the cache repository.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.data_access.arango import collections as col
from app.migrations.versions.v0016_glossary_terms_collection import migration


def _fresh_db() -> MagicMock:
    """A DB where neither glossary collection nor any index exists yet."""
    db = MagicMock()
    db.has_collection.return_value = False
    db.collection.return_value.indexes.return_value = []
    return db


def _applied_db() -> MagicMock:
    """A DB where both collections and all indexes already exist (no-op re-run)."""
    db = MagicMock()
    db.has_collection.return_value = True
    db.collection.return_value.indexes.return_value = [
        {"type": "persistent", "fields": ["slug"]},
        {"type": "persistent", "fields": ["category"]},
        {"type": "persistent", "fields": ["is_active"]},
        {"type": "persistent", "fields": ["term_slug", "language", "expertise_level", "kb_version"]},
        {"type": "persistent", "fields": ["valid_until"]},
    ]
    return db


def test_migration_metadata() -> None:
    assert migration.version == "0016"
    assert migration.name == "glossary_terms_collection"
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
    assert col.GLOSSARY_TERMS in created
    assert col.GLOSSARY_TERM_CACHE in created
    assert report.changed > 0


def test_up_is_idempotent_when_already_applied() -> None:
    db = _applied_db()
    report = migration.up(db)
    assert report.changed == 0
    db.create_collection.assert_not_called()


def test_cleanup_task_delegates_to_repo() -> None:
    with (
        patch("app.tasks.glossary_tasks.ArangoConnection") as conn,
        patch("app.tasks.glossary_tasks.ArangoGlossaryTermCacheRepository") as repo_cls,
    ):
        conn.return_value.db = MagicMock()
        repo_cls.return_value.delete_expired.return_value = 9
        from app.tasks.glossary_tasks import cleanup_expired_cache

        assert cleanup_expired_cache() == 9


def test_reingest_invalidation_task_delegates_to_repo() -> None:
    with (
        patch("app.tasks.glossary_tasks.ArangoConnection") as conn,
        patch("app.tasks.glossary_tasks.ArangoGlossaryTermCacheRepository") as repo_cls,
    ):
        conn.return_value.db = MagicMock()
        repo_cls.return_value.invalidate_all.return_value = 30
        from app.tasks.glossary_tasks import invalidate_after_reingest

        assert invalidate_after_reingest() == 30
