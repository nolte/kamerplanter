"""Tests for v0057_stamp_quality_assessor_user_key (#1663).

Same shape as the v0056 suite: a fake answering the two queries the migration
issues, recording every write. Pins that only rows *without* the attribute are
stamped, that the stamp is an explicit ``null`` that survives the write
(``keep_none=True``), and that nothing is derived from the free-text
``assessed_by``. The real ``!HAS`` / ``keepNull`` semantics are measured against
a server in ``tests/integration/test_v0057_stamp_quality_assessor_user_key.py``.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions.v0057_stamp_quality_assessor_user_key import (
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
            col.QUALITY_ASSESSMENTS: [
                # Pre-#1663: only the free text. Must be stamped.
                {"_key": "qa-legacy", "assessed_by": "Maren"},
                # The trap: the free text *is* an existing user key. Stamped
                # ``null`` like any other legacy row — never copied.
                {"_key": "qa-name-is-a-key", "assessed_by": "user-42"},
                # Written by a #1663 path already. Must not be touched.
                {"_key": "qa-keyed", "assessed_by": "Maren", "assessed_by_key": "user-42"},
                # Already stamped by an earlier run. Must not be touched.
                {"_key": "qa-stamped", "assessed_by": "", "assessed_by_key": None},
            ],
        }
    )


def test_the_field_is_the_issue_1663_field() -> None:
    assert dict(ATTRIBUTION_KEY_FIELDS) == {"quality_assessments": "assessed_by_key"}


def test_the_version_follows_v0056() -> None:
    assert migration.version == "0057"
    assert migration.reversible is False


def test_only_rows_without_the_attribute_are_stamped_and_the_stamp_is_null() -> None:
    db = _db()

    report = migration.up(db)

    assert {doc["_key"] for _name, doc, _kw in db.writes} == {"qa-legacy", "qa-name-is-a-key"}
    for name, doc, kwargs in db.writes:
        assert name == col.QUALITY_ASSESSMENTS
        # An explicit null in the key field and nothing else in the write.
        assert doc == {"_key": doc["_key"], "assessed_by_key": None}
        assert kwargs.get("keep_none") is True
    assert report.changed == 2
    assert report.scanned == 4
    assert report.details == {"stamped": {"quality_assessments.assessed_by_key": 2}}


def test_a_free_text_that_equals_a_user_key_is_not_copied_into_the_key_field() -> None:
    db = _db()

    migration.up(db)

    write = next(doc for _name, doc, _kw in db.writes if doc["_key"] == "qa-name-is-a-key")
    assert write["assessed_by_key"] is None
    assert "assessed_by" not in write


def test_dry_run_reports_the_plan_and_writes_nothing() -> None:
    db = _db()

    report = migration.up(db, dry_run=True)

    assert db.writes == []
    assert report.dry_run is True
    assert report.changed == 0
    assert report.details["stamped"]["quality_assessments.assessed_by_key"] == 2


def test_a_missing_collection_is_skipped_not_created() -> None:
    db = _Db({})

    report = migration.up(db)

    assert db.writes == []
    assert report.changed == 0
    assert report.scanned == 0


def test_down_is_irreversible() -> None:
    with pytest.raises(IrreversibleMigrationError):
        migration.down(_db())
