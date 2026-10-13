"""Tests for v0056_stamp_attribution_user_keys (#1669).

The fake below answers the two queries the migration issues and records every
write, so the tests can pin the three properties the module docstring claims:
only rows *without* the attribute are stamped, the stamp is an explicit ``null``
that survives the write (``keep_none=True``), and nothing is derived from the
free-text name. The real ``!HAS`` / ``keepNull`` semantics are measured against a
server in ``tests/integration/test_v0056_stamp_attribution_user_keys.py``.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions.v0056_stamp_attribution_user_keys import (
    ATTRIBUTION_KEY_FIELDS,
    migration,
)


class _Aql:
    def __init__(self, docs: dict[str, list[dict[str, Any]]]) -> None:
        self._docs = docs

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        bind_vars = bind_vars or {}
        rows = self._docs.get(bind_vars["@collection"], [])
        if "LENGTH" in query:
            return iter([len(rows)])
        field = bind_vars["field"]
        # ``!HAS(doc, @field)`` — attribute absent, not attribute null.
        return iter([doc["_key"] for doc in rows if field not in doc])


class _Collection:
    def __init__(self, name: str, writes: list[tuple[str, dict[str, Any], dict[str, Any]]]) -> None:
        self._name = name
        self._writes = writes

    def update(self, document: dict[str, Any], **kwargs: Any) -> None:
        self._writes.append((self._name, document, kwargs))


class _Db:
    def __init__(self, docs: dict[str, list[dict[str, Any]]]) -> None:
        self._docs = docs
        self.aql = _Aql(docs)
        self.writes: list[tuple[str, dict[str, Any], dict[str, Any]]] = []

    def has_collection(self, name: str) -> bool:
        return name in self._docs

    def collection(self, name: str) -> _Collection:
        return _Collection(name, self.writes)


def _db() -> _Db:
    return _Db(
        {
            col.HARVEST_BATCHES: [
                # Pre-#1669: only the free text. Must be stamped.
                {"_key": "hb-legacy", "harvester": "Maren"},
                # The trap: the free text *is* an existing user key. Must be
                # stamped ``null`` like any other legacy row — never copied.
                {"_key": "hb-name-is-a-key", "harvester": "user-42"},
                # Written by a #1669 path already. Must not be touched.
                {"_key": "hb-keyed", "harvester": "Maren", "harvested_by_key": "user-42"},
                # Already stamped by an earlier run. Must not be touched.
                {"_key": "hb-stamped", "harvester": "Maren", "harvested_by_key": None},
            ],
            col.INSPECTIONS: [
                {"_key": "in-legacy", "inspector": "mcp:user-42"},
                {"_key": "in-keyed", "inspector": "mcp:user-42", "inspected_by_key": "user-42"},
            ],
            col.TREATMENT_APPLICATIONS: [
                {"_key": "ta-legacy", "applied_by": ""},
            ],
        }
    )


def test_the_three_fields_are_the_issue_1669_fields() -> None:
    assert dict(ATTRIBUTION_KEY_FIELDS) == {
        "harvest_batches": "harvested_by_key",
        "inspections": "inspected_by_key",
        "treatment_applications": "applied_by_key",
    }


def test_only_rows_without_the_attribute_are_stamped_and_the_stamp_is_null() -> None:
    db = _db()

    report = migration.up(db)

    stamped = {(name, doc["_key"]) for name, doc, _kw in db.writes}
    assert stamped == {
        (col.HARVEST_BATCHES, "hb-legacy"),
        (col.HARVEST_BATCHES, "hb-name-is-a-key"),
        (col.INSPECTIONS, "in-legacy"),
        (col.TREATMENT_APPLICATIONS, "ta-legacy"),
    }
    for name, doc, kwargs in db.writes:
        field = dict(ATTRIBUTION_KEY_FIELDS)[name]
        # An explicit null in the key field, and *nothing else* in the write:
        # no owner guessed from the free text, no free text touched.
        assert doc == {"_key": doc["_key"], field: None}
        # Without ``keep_none=True`` python-arango would drop the attribute and
        # the scan would rediscover the row on every run.
        assert kwargs.get("keep_none") is True
    assert report.changed == 4
    assert report.scanned == 7
    assert report.details == {
        "stamped": {
            "harvest_batches.harvested_by_key": 2,
            "inspections.inspected_by_key": 1,
            "treatment_applications.applied_by_key": 1,
        }
    }


def test_a_free_text_that_equals_a_user_key_is_not_copied_into_the_key_field() -> None:
    """The backfill the issue forbids, as its own case so the refusal is named."""
    db = _db()

    migration.up(db)

    write = next(doc for name, doc, _kw in db.writes if doc["_key"] == "hb-name-is-a-key")
    assert write["harvested_by_key"] is None
    assert "harvester" not in write


def test_dry_run_reports_the_plan_and_writes_nothing() -> None:
    db = _db()

    report = migration.up(db, dry_run=True)

    assert db.writes == []
    assert report.dry_run is True
    assert report.changed == 0
    assert report.scanned == 7
    assert report.details["stamped"]["harvest_batches.harvested_by_key"] == 2


def test_a_missing_collection_is_skipped_not_created() -> None:
    db = _Db({col.INSPECTIONS: [{"_key": "in-legacy"}]})

    report = migration.up(db)

    assert [name for name, _doc, _kw in db.writes] == [col.INSPECTIONS]
    assert report.changed == 1


def test_down_is_irreversible() -> None:
    with pytest.raises(IrreversibleMigrationError):
        migration.down(_db())
