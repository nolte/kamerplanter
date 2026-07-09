"""Tests for v0009_notification_group_key_index.

The migration adds the persistent ``(group_key, tenant_key)`` index to the
``notifications`` collection on existing volumes (Issue #409, F2). It is
idempotent — when the index already exists (bootstrapped fresh DB or a prior run)
``up`` creates nothing — and honours ``dry_run`` by never writing.
"""

from __future__ import annotations

from app.data_access.arango import collections as col
from app.migrations.versions.v0009_notification_group_key_index import (
    _TARGET_FIELDS,
    _has_group_key_index,
    migration,
)

_GROUP_KEY_INDEX = {"type": "persistent", "fields": ["group_key", "tenant_key"], "unique": False}
_OTHER_INDEX = {"type": "persistent", "fields": ["created_at"], "unique": False}
_PRIMARY_INDEX = {"type": "primary", "fields": ["_key"], "unique": True}


class _FakeCollection:
    def __init__(self, indexes: list[dict]) -> None:
        self._indexes = list(indexes)
        self.added: list[dict] = []

    def indexes(self) -> list[dict]:
        return list(self._indexes)

    def add_persistent_index(self, *, fields: list[str], unique: bool = False) -> dict:
        record = {"type": "persistent", "fields": fields, "unique": unique}
        self.added.append(record)
        self._indexes.append(record)
        return record


class _FakeDb:
    def __init__(self, collection: _FakeCollection) -> None:
        self._collection = collection

    def collection(self, name: str) -> _FakeCollection:
        assert name == col.NOTIFICATIONS
        return self._collection


class TestHasGroupKeyIndex:
    def test_none_is_false(self):
        assert _has_group_key_index(None) is False

    def test_empty_list_is_false(self):
        assert _has_group_key_index([]) is False

    def test_wrong_fields_is_false(self):
        assert _has_group_key_index([_OTHER_INDEX, _PRIMARY_INDEX]) is False

    def test_wrong_type_is_false(self):
        assert _has_group_key_index([{"type": "hash", "fields": ["group_key", "tenant_key"]}]) is False

    def test_matching_index_is_true(self):
        assert _has_group_key_index([_PRIMARY_INDEX, _GROUP_KEY_INDEX]) is True


class TestUp:
    def test_creates_index_when_absent(self):
        collection = _FakeCollection([_PRIMARY_INDEX, _OTHER_INDEX])
        report = migration.up(_FakeDb(collection))

        assert report.changed == 1
        assert report.scanned == 1
        assert collection.added == [{"type": "persistent", "fields": _TARGET_FIELDS, "unique": False}]
        assert report.details["created"] is True

    def test_index_present_after_up(self):
        collection = _FakeCollection([_PRIMARY_INDEX])
        migration.up(_FakeDb(collection))
        assert _has_group_key_index(collection.indexes()) is True

    def test_noop_when_already_present(self):
        collection = _FakeCollection([_PRIMARY_INDEX, _GROUP_KEY_INDEX])
        report = migration.up(_FakeDb(collection))

        assert report.changed == 0
        assert report.noop is True
        assert collection.added == []

    def test_rerun_is_a_noop(self):
        collection = _FakeCollection([_PRIMARY_INDEX])
        migration.up(_FakeDb(collection))
        report = migration.up(_FakeDb(collection))

        assert report.changed == 0
        assert report.noop is True

    def test_dry_run_writes_nothing(self):
        collection = _FakeCollection([_PRIMARY_INDEX])
        report = migration.up(_FakeDb(collection), dry_run=True)

        assert report.dry_run is True
        assert report.changed == 0
        assert collection.added == []
        assert _has_group_key_index(collection.indexes()) is False

    def test_migration_metadata(self):
        assert migration.version == "0009"
        assert migration.name == "notification_group_key_index"
        assert migration.reversible is False
