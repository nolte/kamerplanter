"""Tests for v0059_backfill_instantiated_task_tenant_key (#1708).

Same shape as the v0056–v0058 suites: a fake answering the queries the migration
issues and recording every write. Pins which rows are candidates, that the owner
is read off the execution's entity (a location through its site), that an
unresolvable owner is counted and left alone rather than guessed, and that a
re-run is a no-op. The real ``== null`` semantics for an absent attribute are
measured against a server in
``tests/integration/test_v0059_backfill_instantiated_task_tenant_key.py``.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions.v0059_backfill_instantiated_task_tenant_key import migration

TENANT_A = "tenant-a"
TENANT_B = "tenant-b"


class _Aql:
    def __init__(self, docs: dict[str, list[dict[str, Any]]]) -> None:
        self._docs = docs

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        rows = self._docs.get((bind_vars or {})["@collection"], [])
        if "LENGTH" in query:
            return iter([len(rows)])
        return iter(
            [
                {
                    "key": doc["_key"],
                    "execution_key": doc.get("workflow_execution_key"),
                    "entity_type": doc.get("entity_type"),
                    "entity_key": doc.get("entity_key"),
                }
                for doc in rows
                if not doc.get("tenant_key") and doc.get("workflow_execution_key")
            ]
        )


class _Collection:
    def __init__(self, name: str, docs: list[dict[str, Any]], writes: list[tuple[str, dict[str, Any]]]) -> None:
        self._name = name
        self._docs = docs
        self._writes = writes

    def get(self, key: str) -> dict[str, Any] | None:
        return next((doc for doc in self._docs if doc["_key"] == key), None)

    def update(self, document: dict[str, Any], **_kwargs: Any) -> None:
        self._writes.append((self._name, document))
        for doc in self._docs:
            if doc["_key"] == document["_key"]:
                doc.update(document)


class _Db:
    def __init__(self, docs: dict[str, list[dict[str, Any]]]) -> None:
        self._docs = docs
        self.aql = _Aql(docs)
        self.writes: list[tuple[str, dict[str, Any]]] = []

    def has_collection(self, name: str) -> bool:
        return name in self._docs

    def collection(self, name: str) -> _Collection:
        return _Collection(name, self._docs[name], self.writes)


def _db() -> _Db:
    return _Db(
        {
            col.SITES: [{"_key": "site-b", "tenant_key": TENANT_B}],
            col.LOCATIONS: [{"_key": "loc-b", "tenant_key": "", "site_key": "site-b"}],
            col.PLANT_INSTANCES: [{"_key": "plant-a", "tenant_key": TENANT_A}],
            col.TANKS: [{"_key": "tank-a", "tenant_key": TENANT_A}],
            col.PLANTING_RUNS: [{"_key": "run-b", "tenant_key": TENANT_B}],
            col.WORKFLOW_EXECUTIONS: [
                {"_key": "we-plant", "entity_type": "plant_instance", "entity_key": "plant-a"},
                {"_key": "we-loc", "entity_type": "location", "entity_key": "loc-b"},
                {"_key": "we-tank", "entity_type": "tank", "entity_key": "tank-a"},
                {"_key": "we-gone", "entity_type": "plant_instance", "entity_key": "plant-deleted"},
                {"_key": "we-generic", "entity_type": "generic", "entity_key": "thing"},
            ],
            col.TASKS: [
                {"_key": "t-plant", "tenant_key": "", "workflow_execution_key": "we-plant"},
                {"_key": "t-loc", "tenant_key": "", "workflow_execution_key": "we-loc"},
                {"_key": "t-tank", "workflow_execution_key": "we-tank"},
                # Execution record gone: the task's own binding is the source.
                {
                    "_key": "t-run",
                    "tenant_key": "",
                    "workflow_execution_key": "we-deleted",
                    "entity_type": "planting_run",
                    "entity_key": "run-b",
                },
                {"_key": "t-gone", "tenant_key": "", "workflow_execution_key": "we-gone"},
                {"_key": "t-generic", "tenant_key": "", "workflow_execution_key": "we-generic"},
                {"_key": "t-stamped", "tenant_key": TENANT_B, "workflow_execution_key": "we-plant"},
                {"_key": "t-manual", "tenant_key": "", "entity_type": "plant_instance", "entity_key": "plant-a"},
            ],
        }
    )


def test_the_version_follows_v0058() -> None:
    assert migration.version == "0059"
    assert migration.reversible is False


def test_the_owner_is_read_off_the_executions_entity() -> None:
    db = _db()

    report = migration.up(db)

    stamped = {doc["_key"]: doc["tenant_key"] for _name, doc in db.writes}
    assert stamped == {"t-plant": TENANT_A, "t-loc": TENANT_B, "t-tank": TENANT_A, "t-run": TENANT_B}
    assert all(name == col.TASKS for name, _doc in db.writes)
    assert all(set(doc) == {"_key", "tenant_key"} for _name, doc in db.writes)
    assert report.scanned == 8
    assert report.changed == 4
    assert report.details == {"candidates": 6, "stamped": 4, "unresolved": 2}


def test_an_unresolvable_owner_is_counted_not_guessed() -> None:
    db = _db()

    migration.up(db)

    written = {doc["_key"] for _name, doc in db.writes}
    assert "t-gone" not in written
    assert "t-generic" not in written


def test_stamped_and_non_execution_tasks_are_not_candidates() -> None:
    db = _db()

    migration.up(db)

    written = {doc["_key"] for _name, doc in db.writes}
    assert "t-stamped" not in written
    assert "t-manual" not in written


def test_a_second_run_is_a_no_op() -> None:
    db = _db()
    migration.up(db)
    db.writes.clear()

    report = migration.up(db)

    assert db.writes == []
    assert report.changed == 0
    assert report.details == {"candidates": 2, "stamped": 0, "unresolved": 2}


def test_dry_run_reports_the_plan_and_writes_nothing() -> None:
    db = _db()

    report = migration.up(db, dry_run=True)

    assert db.writes == []
    assert report.changed == 0
    assert report.details == {"candidates": 6, "stamped": 4, "unresolved": 2}


def test_a_missing_tasks_collection_is_skipped() -> None:
    report = migration.up(_Db({}))

    assert report.scanned == 0
    assert report.changed == 0


def test_down_is_irreversible() -> None:
    with pytest.raises(IrreversibleMigrationError):
        migration.down(_db())
