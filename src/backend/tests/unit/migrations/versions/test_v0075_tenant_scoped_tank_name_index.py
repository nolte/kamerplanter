"""v0075 — the tank name index becomes ``(tenant_key, name)`` (#2029).

A double of the index list only: it records creations and drops the way the server
reports them. The real-server counterpart, with the legacy index created exactly as
the shipped code did (``hash`` and ``persistent``), is
``tests/integration/test_v0075_tenant_scoped_tank_name_index.py``.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.migrations.versions.v0075_tenant_scoped_tank_name_index import migration


def _row(index_id: str, index_type: str, fields: list[str], *, unique: bool = True) -> dict[str, Any]:
    return {"id": index_id, "type": index_type, "fields": list(fields), "unique": unique, "sparse": False}


class _Tanks:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.created = 0

    def indexes(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self.rows]

    def add_persistent_index(self, *, fields: list[str], unique: bool) -> dict[str, Any]:
        self.created += 1
        row = _row(f"tanks/new{self.created}", "persistent", fields, unique=unique)
        self.rows.append(row)
        return row

    def delete_index(self, index_id: str, ignore_missing: bool = False) -> bool:  # noqa: ARG002
        self.rows = [row for row in self.rows if row["id"] != index_id]
        return True


class _Db:
    def __init__(self, rows: list[dict[str, Any]] | None) -> None:
        self.tanks = _Tanks(rows or [])
        self.present = rows is not None

    def has_collection(self, name: str) -> bool:
        return self.present and name == col.TANKS

    def collection(self, name: str) -> _Tanks:
        assert name == col.TANKS, f"the migration touched {name}"
        return self.tanks


@pytest.mark.parametrize("legacy_type", ["hash", "persistent"])
def test_creates_the_compound_first_then_drops_the_legacy_index(legacy_type: str) -> None:
    db = _Db([_row("tanks/1", legacy_type, ["name"])])

    report = migration.up(db)  # type: ignore[arg-type]

    assert [(r["type"], r["fields"]) for r in db.tanks.rows] == [("persistent", ["tenant_key", "name"])]
    assert report.changed == 2
    assert report.precondition_unmet is False
    assert report.details["legacy_index_types"] == [legacy_type]
    assert migration.up(db).changed == 0  # type: ignore[arg-type]


def test_a_present_compound_is_not_created_again() -> None:
    db = _Db([_row("tanks/1", "hash", ["name"]), _row("tanks/2", "persistent", ["tenant_key", "name"])])

    report = migration.up(db)  # type: ignore[arg-type]

    assert db.tanks.created == 0
    assert report.changed == 1
    assert [r["id"] for r in db.tanks.rows] == ["tanks/2"]


def test_a_non_unique_compound_is_no_replacement() -> None:
    """The actuator-style non-unique ``(tenant_key, name)`` shape must not count."""
    db = _Db(
        [_row("tanks/1", "persistent", ["name"]), _row("tanks/2", "persistent", ["tenant_key", "name"], unique=False)]
    )

    report = migration.up(db)  # type: ignore[arg-type]

    assert db.tanks.created == 1
    assert report.details["replacement_indexes"] == 1
    assert sorted(r["id"] for r in db.tanks.rows) == ["tanks/2", "tanks/new1"]


def test_a_dry_run_writes_nothing() -> None:
    db = _Db([_row("tanks/1", "hash", ["name"])])

    report = migration.up(db, dry_run=True)  # type: ignore[arg-type]

    assert report.changed == 0
    assert report.precondition_unmet is False
    assert report.details["compound_to_create"] is True
    assert report.details["legacy_indexes"] == 1
    assert db.tanks.created == 0
    assert [r["id"] for r in db.tanks.rows] == ["tanks/1"]


def test_a_non_unique_name_index_is_left_alone() -> None:
    db = _Db([_row("tanks/1", "persistent", ["name"], unique=False)])

    report = migration.up(db)  # type: ignore[arg-type]

    assert report.details["legacy_indexes"] == 0
    assert sorted(r["id"] for r in db.tanks.rows) == ["tanks/1", "tanks/new1"]


def test_a_missing_collection_is_a_no_op() -> None:
    report = migration.up(_Db(None))  # type: ignore[arg-type]

    assert report.changed == 0
    assert report.precondition_unmet is False
