"""v0082 (#2111): the security-audit collection and its indexes, idempotent, a dry run writes nothing."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.data_access.arango import collections as col
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions.v0082_security_audit_log_collection import migration

_INDEXES = [
    {"type": "persistent", "fields": ["tenant_key", "created_at"]},
    {"type": "persistent", "fields": ["target_user_key"]},
    {"type": "persistent", "fields": ["actor_user_key"]},
    {"type": "persistent", "fields": ["created_at"]},
]


def _db(*, present: bool, indexes: list[dict] | None = None) -> MagicMock:
    db = MagicMock()
    db.has_collection.return_value = present
    db.collection.return_value.indexes.return_value = indexes or []
    return db


def test_a_fresh_volume_gets_the_collection_and_four_indexes() -> None:
    db = _db(present=False)

    report = migration.up(db)

    db.create_collection.assert_called_once_with(col.SECURITY_AUDIT_LOG)
    assert db.collection.return_value.add_persistent_index.call_count == 4
    assert (report.changed, report.dry_run) == (5, False)


def test_a_dry_run_counts_and_writes_nothing() -> None:
    db = _db(present=False)

    report = migration.up(db, dry_run=True)

    db.create_collection.assert_not_called()
    db.collection.return_value.add_persistent_index.assert_not_called()
    assert (report.changed, report.dry_run) == (0, True)
    assert report.details["document_collections"] == [col.SECURITY_AUDIT_LOG]


def test_an_already_applied_volume_is_a_noop() -> None:
    db = _db(present=True, indexes=_INDEXES)

    report = migration.up(db)

    db.create_collection.assert_not_called()
    db.collection.return_value.add_persistent_index.assert_not_called()
    assert report.changed == 0


def test_a_missing_index_is_added_alone() -> None:
    db = _db(present=True, indexes=_INDEXES[:3])

    report = migration.up(db)

    db.collection.return_value.add_persistent_index.assert_called_once_with(fields=["created_at"], unique=False)
    assert report.changed == 1


def test_the_migration_is_irreversible_and_ordered_after_v0081() -> None:
    assert migration.version == "0082"
    with pytest.raises(IrreversibleMigrationError):
        migration.down(MagicMock())
