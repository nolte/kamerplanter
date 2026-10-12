"""Tests for v0092_task_tenant_status_index (#1534).

The migration adds the persistent, non-unique ``(tenant_key, status)`` index to
``tasks`` on a volume that predates it; ``ensure_collections`` bootstraps the same
index on every boot. Two statements are pinned here:

* the migration and the bootstrap agree on the shape — a bootstrapped volume is a
  no-op for the migration, and the migration builds exactly what the bootstrap builds
  (fields in order, non-unique, non-sparse, in the background);
* the presence check is on the exact field *sequence*: ``(status, tenant_key)`` cannot
  serve a tenant-scoped read, and the existing single-field ``status`` index must not
  be mistaken for the target nor removed.

Whether the optimizer then actually picks the index for the queue query is a
question only a server answers: ``tests/integration/test_task_queue_tenant_status_index.py``.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions.v0092_task_tenant_status_index import TARGET_FIELDS, migration
from tests.unit.guards.test_tenant_unique_indexes_are_scoped import _RecordingDb

_PRIMARY = {"type": "primary", "fields": ["_key"], "unique": True}
_STATUS = {"type": "persistent", "fields": ["status"], "unique": False}
_PLANT_KEY = {"type": "persistent", "fields": ["plant_key"], "unique": False}
_TARGET = {"type": "persistent", "fields": ["tenant_key", "status"], "unique": False}
_WRONG_ORDER = {"type": "persistent", "fields": ["status", "tenant_key"], "unique": False}
_WITH_DUE_DATE = {"type": "persistent", "fields": ["tenant_key", "status", "due_date"], "unique": False}


class _FakeTasks:
    def __init__(self, indexes: list[dict[str, Any]]) -> None:
        self._indexes = [dict(i) for i in indexes]
        self.created: list[dict[str, Any]] = []

    def indexes(self) -> list[dict[str, Any]]:
        return [dict(i) for i in self._indexes]

    def add_persistent_index(self, **kwargs: Any) -> dict[str, Any]:
        self.created.append(kwargs)
        row = {"type": "persistent", "fields": list(kwargs["fields"]), "unique": kwargs.get("unique", False)}
        self._indexes.append(row)
        return row

    def update(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - guard, never called
        raise AssertionError("v0092 is structural: it must not write a document")


class _FakeAql:
    def execute(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - guard, never called
        raise AssertionError("v0092 is structural: it must not query documents")


class _FakeDb:
    def __init__(self, tasks: _FakeTasks, *, has_tasks: bool = True) -> None:
        self._tasks = tasks
        self._has_tasks = has_tasks
        self.aql = _FakeAql()

    def has_collection(self, name: str) -> bool:
        assert name == col.TASKS
        return self._has_tasks

    def collection(self, name: str) -> _FakeTasks:
        assert name == col.TASKS
        return self._tasks


class TestBootstrapSync:
    def test_the_frozen_fields_equal_the_bootstrap_constant(self) -> None:
        assert list(TARGET_FIELDS) == col.TASK_TENANT_STATUS_INDEX_FIELDS == ["tenant_key", "status"]

    def test_the_bootstrap_builds_the_index_next_to_the_single_field_status_index(self) -> None:
        db = _RecordingDb()
        col.ensure_collections(db)  # type: ignore[arg-type]

        rows = [(row["fields"], row["unique"], row["sparse"]) for row in db.collections[col.TASKS].rows]

        assert (["tenant_key", "status"], False, False) in rows
        assert (["status"], False, False) in rows  # kept for reads on status alone
        assert not any(fields == ["tenant_key", "status", "due_date"] for fields, _, _ in rows)

    def test_a_bootstrapped_volume_is_a_noop(self) -> None:
        db = _RecordingDb()
        col.ensure_collections(db)  # type: ignore[arg-type]
        before = len(db.collections[col.TASKS].rows)

        report = migration.up(db)  # type: ignore[arg-type]

        assert (report.changed, report.details["already_present"]) == (0, True)
        assert len(db.collections[col.TASKS].rows) == before


class TestUp:
    def test_creates_the_index_on_a_volume_that_predates_it(self) -> None:
        tasks = _FakeTasks([_PRIMARY, _PLANT_KEY, _STATUS])

        report = migration.up(_FakeDb(tasks))  # type: ignore[arg-type]

        assert tasks.created == [{"fields": ["tenant_key", "status"], "unique": False, "in_background": True}]
        assert (report.scanned, report.changed, report.details["created"]) == (1, 1, True)

    def test_a_second_run_changes_nothing(self) -> None:
        tasks = _FakeTasks([_PRIMARY, _STATUS])
        migration.up(_FakeDb(tasks))  # type: ignore[arg-type]

        report = migration.up(_FakeDb(tasks))  # type: ignore[arg-type]

        assert report.changed == 0
        assert len(tasks.created) == 1

    @pytest.mark.parametrize("index_type", ["persistent", "hash"])
    def test_an_existing_index_of_either_reported_type_is_a_noop(self, index_type: str) -> None:
        # A pre-June volume reports bootstrap indexes as ``hash`` (#2034).
        tasks = _FakeTasks([_PRIMARY, {**_TARGET, "type": index_type}])

        report = migration.up(_FakeDb(tasks))  # type: ignore[arg-type]

        assert (report.changed, tasks.created) == (0, [])

    @pytest.mark.parametrize("other", [_WRONG_ORDER, _WITH_DUE_DATE, _STATUS], ids=["reversed", "three", "status"])
    def test_another_shape_is_not_mistaken_for_the_target(self, other: dict[str, Any]) -> None:
        tasks = _FakeTasks([_PRIMARY, other])

        report = migration.up(_FakeDb(tasks))  # type: ignore[arg-type]

        assert report.changed == 1
        assert [c["fields"] for c in tasks.created] == [["tenant_key", "status"]]
        assert other in tasks.indexes()  # nothing is dropped

    def test_dry_run_creates_nothing(self) -> None:
        tasks = _FakeTasks([_PRIMARY, _STATUS])

        report = migration.up(_FakeDb(tasks), dry_run=True)  # type: ignore[arg-type]

        assert (report.dry_run, report.changed, report.details["will_create"]) == (True, 0, True)
        assert tasks.created == []

    def test_missing_collection_is_a_noop(self) -> None:
        tasks = _FakeTasks([])

        report = migration.up(_FakeDb(tasks, has_tasks=False))  # type: ignore[arg-type]

        assert (report.scanned, report.changed, report.details["collection_absent"]) == (0, 0, True)
        assert tasks.created == []


def test_down_is_irreversible() -> None:
    assert migration.reversible is False
    with pytest.raises(IrreversibleMigrationError):
        migration.down(_FakeDb(_FakeTasks([])))  # type: ignore[arg-type]
