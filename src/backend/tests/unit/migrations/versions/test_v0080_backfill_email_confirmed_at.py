"""v0080 (#1948): a dry run only counts, the write stamps, a missing collection is skipped.

A double of the AQL layer only; which accounts the predicate selects and that a
re-run is a no-op are measured on a real server in
``tests/integration/test_v0080_backfill_email_confirmed_at.py``.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions.v0080_backfill_email_confirmed_at import migration


class _Db:
    def __init__(self, count: int, present: bool = True) -> None:
        self.count = count
        self.present = present
        self.queries: list[tuple[str, dict[str, Any]]] = []
        self.aql = self

    def has_collection(self, name: str) -> bool:
        return self.present and name == col.USERS

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None, **_: Any) -> Any:
        self.queries.append((query, bind_vars or {}))
        return iter([self.count])


def test_a_dry_run_counts_and_writes_nothing() -> None:
    db = _Db(4)

    report = migration.up(db, dry_run=True)  # type: ignore[arg-type]

    assert (report.scanned, report.changed, report.dry_run) == (4, 0, True)
    assert report.details == {"grandfathered_accounts": 4}
    assert all("UPDATE" not in query for query, _ in db.queries)


def test_the_write_stamps_verified_accounts_only() -> None:
    db = _Db(4)

    report = migration.up(db)  # type: ignore[arg-type]

    assert (report.scanned, report.changed) == (4, 4)
    ((query, binds),) = db.queries
    assert "doc.email_verified == true" in query
    assert "UPDATE doc WITH {email_confirmed_at: @stamp}" in query
    assert binds["@collection"] == col.USERS
    assert isinstance(binds["stamp"], str)


def test_a_missing_collection_is_a_noop() -> None:
    db = _Db(0, present=False)

    report = migration.up(db)  # type: ignore[arg-type]

    assert (report.scanned, report.changed) == (0, 0)
    assert db.queries == []


def test_down_is_refused() -> None:
    with pytest.raises(IrreversibleMigrationError):
        migration.down(_Db(0))  # type: ignore[arg-type]
