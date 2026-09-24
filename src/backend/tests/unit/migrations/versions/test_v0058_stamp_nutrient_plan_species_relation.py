"""Tests for v0058_stamp_nutrient_plan_species_relation (#1618).

Same shape as the v0056/v0057 suites: a fake answering the two queries the
migration issues, recording every write. Pins that only plans whose relation is
absent or ``null`` are stamped, that the stamp is an empty list and nothing
else — no species is derived from a plan's name or tags — and that a re-run is a
no-op. The real ``IS_ARRAY`` semantics are measured against a server in
``tests/integration/test_v0058_stamp_nutrient_plan_species_relation.py``.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions.v0058_stamp_nutrient_plan_species_relation import (
    SPECIES_RELATION_FIELD,
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
        # ``!IS_ARRAY(doc.@field)`` — absent or null, never an existing list.
        return iter([doc["_key"] for doc in rows if not isinstance(doc.get(field), list)])


class _Collection:
    def __init__(self, name: str, docs: list[dict[str, Any]], writes: list[tuple[str, dict[str, Any]]]) -> None:
        self._name = name
        self._docs = docs
        self._writes = writes

    def update(self, document: dict[str, Any], **_kwargs: Any) -> None:
        self._writes.append((self._name, document))
        # Apply the write so a second run sees the stamped state.
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
            col.NUTRIENT_PLANS: [
                # Pre-#1618: no attribute. Must be stamped.
                {"_key": "plan-legacy", "name": "Tomate — Plagron Terra", "tags": ["tomate"]},
                # A stored null. Must be stamped.
                {"_key": "plan-null", "name": "Null", "species_keys": None},
                # Already linked. Must not be touched.
                {"_key": "plan-linked", "name": "Linked", "species_keys": ["solanum-lycopersicum"]},
                # Saved empty on purpose. Must not be touched.
                {"_key": "plan-empty", "name": "Empty", "species_keys": []},
            ],
        }
    )


def test_the_field_is_the_issue_1618_relation() -> None:
    assert SPECIES_RELATION_FIELD == "species_keys"


def test_the_version_follows_v0057() -> None:
    assert migration.version == "0058"
    assert migration.reversible is False


def test_only_plans_without_a_list_are_stamped_and_the_stamp_is_empty() -> None:
    db = _db()

    report = migration.up(db)

    assert {doc["_key"] for _name, doc in db.writes} == {"plan-legacy", "plan-null"}
    for name, doc in db.writes:
        assert name == col.NUTRIENT_PLANS
        assert doc == {"_key": doc["_key"], "species_keys": []}
    assert report.changed == 2
    assert report.scanned == 4
    assert report.details == {"stamped": 2}


def test_no_species_is_derived_from_a_plans_name_or_tags() -> None:
    db = _db()

    migration.up(db)

    write = next(doc for _name, doc in db.writes if doc["_key"] == "plan-legacy")
    assert write["species_keys"] == []


def test_a_second_run_is_a_no_op() -> None:
    db = _db()
    migration.up(db)
    db.writes.clear()

    report = migration.up(db)

    assert db.writes == []
    assert report.changed == 0


def test_dry_run_reports_the_plan_and_writes_nothing() -> None:
    db = _db()

    report = migration.up(db, dry_run=True)

    assert db.writes == []
    assert report.dry_run is True
    assert report.changed == 0
    assert report.details == {"stamped": 2}


def test_a_missing_collection_is_skipped_not_created() -> None:
    db = _Db({})

    report = migration.up(db)

    assert db.writes == []
    assert report.changed == 0
    assert report.scanned == 0


def test_down_is_irreversible() -> None:
    with pytest.raises(IrreversibleMigrationError):
        migration.down(_db())
