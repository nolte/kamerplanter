"""Tests for v0033_diary_analysis_state_index (REQ-050 §5, #921).

The migration adds the persistent ``(tenant_key, analysis_state,
analysis_requested_at)`` index to ``plant_diary_entries`` on existing volumes. It
is structural only — it must never touch a document, because REQ-050 states
outright that existing entries need no data migration (AK-26).

The field *order* carries the whole value of the index, so the presence check is
tested against a same-fields-different-order index too: mistaking that for the
target would leave the work queue scanning while the migration reports success.
"""

from __future__ import annotations

import pytest

from app.data_access.arango import collections as col
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions.v0033_diary_analysis_state_index import (
    _TARGET_FIELDS,
    _has_analysis_state_index,
    migration,
)

_TARGET_INDEX = {
    "type": "persistent",
    "fields": ["tenant_key", "analysis_state", "analysis_requested_at"],
    "unique": False,
}
_WRONG_ORDER_INDEX = {
    "type": "persistent",
    "fields": ["analysis_state", "tenant_key", "analysis_requested_at"],
    "unique": False,
}
_PREFIX_ONLY_INDEX = {"type": "persistent", "fields": ["tenant_key"], "unique": False}
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

    def update(self, *args, **kwargs):  # pragma: no cover - guard, never called
        raise AssertionError("v0033 is structural: it must not write a document")


class _FakeAql:
    def execute(self, *args, **kwargs):  # pragma: no cover - guard, never called
        raise AssertionError("v0033 is structural: it must not query documents")


class _FakeDb:
    def __init__(self, collection: _FakeCollection, *, has_collection: bool = True) -> None:
        self._collection = collection
        self._has_collection = has_collection
        self.aql = _FakeAql()

    def has_collection(self, name: str) -> bool:
        assert name == col.PLANT_DIARY_ENTRIES
        return self._has_collection

    def collection(self, name: str) -> _FakeCollection:
        assert name == col.PLANT_DIARY_ENTRIES
        return self._collection


class TestHasAnalysisStateIndex:
    def test_none_is_false(self):
        assert _has_analysis_state_index(None) is False

    def test_empty_list_is_false(self):
        assert _has_analysis_state_index([]) is False

    def test_matching_index_is_true(self):
        assert _has_analysis_state_index([_PRIMARY_INDEX, _TARGET_INDEX]) is True

    def test_same_fields_in_another_order_is_false(self):
        # A tenant-scoped read cannot use an index whose leading attribute is
        # `analysis_state`; treating it as the target would leave the queue
        # scanning while the migration claims to be done.
        assert _has_analysis_state_index([_WRONG_ORDER_INDEX]) is False

    def test_prefix_only_index_is_false(self):
        # `tenant_key` alone already exists on the collection since REQ-013.
        assert _has_analysis_state_index([_PREFIX_ONLY_INDEX]) is False

    def test_wrong_type_is_false(self):
        assert _has_analysis_state_index([{"type": "hash", "fields": _TARGET_FIELDS}]) is False


class TestUp:
    def test_creates_index_when_absent(self):
        collection = _FakeCollection([_PRIMARY_INDEX, _PREFIX_ONLY_INDEX])

        report = migration.up(_FakeDb(collection))

        assert report.changed == 1
        assert report.scanned == 1
        assert collection.added == [{"type": "persistent", "fields": _TARGET_FIELDS, "unique": False}]
        assert report.details["created"] is True

    def test_index_present_after_up(self):
        collection = _FakeCollection([_PRIMARY_INDEX])

        migration.up(_FakeDb(collection))

        assert _has_analysis_state_index(collection.indexes()) is True

    def test_replaces_nothing_but_adds_the_target_when_order_is_wrong(self):
        collection = _FakeCollection([_PRIMARY_INDEX, _WRONG_ORDER_INDEX])

        report = migration.up(_FakeDb(collection))

        assert report.changed == 1
        assert _has_analysis_state_index(collection.indexes()) is True

    def test_noop_when_already_present(self):
        collection = _FakeCollection([_PRIMARY_INDEX, _TARGET_INDEX])

        report = migration.up(_FakeDb(collection))

        assert report.changed == 0
        assert report.noop is True
        assert collection.added == []

    def test_rerun_is_a_noop(self):
        collection = _FakeCollection([_PRIMARY_INDEX])
        db = _FakeDb(collection)

        migration.up(db)
        report = migration.up(db)

        assert report.changed == 0
        assert report.noop is True
        assert len(collection.added) == 1

    def test_dry_run_writes_nothing(self):
        collection = _FakeCollection([_PRIMARY_INDEX])

        report = migration.up(_FakeDb(collection), dry_run=True)

        assert report.dry_run is True
        assert report.changed == 0
        assert report.details["will_create"] is True
        assert collection.added == []
        assert _has_analysis_state_index(collection.indexes()) is False

    def test_absent_collection_is_a_noop(self):
        collection = _FakeCollection([])

        report = migration.up(_FakeDb(collection, has_collection=False))

        assert report.changed == 0
        assert report.details["collection_absent"] is True
        assert collection.added == []

    def test_migration_metadata(self):
        assert migration.version == "0033"
        assert migration.name == "diary_analysis_state_index"
        assert migration.reversible is False

    def test_down_refuses(self):
        with pytest.raises(IrreversibleMigrationError):
            migration.down(_FakeDb(_FakeCollection([])))
