"""v0078 (#2027 follow-up): a dry run only counts, the write covers both catalogues, a missing collection is skipped.

A double of the AQL layer only; which rows the predicate selects and that a re-run
is a no-op are measured on a real server in
``tests/integration/test_v0078_clear_system_flag_on_tenant_catalogue_rows.py``.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions.v0078_clear_system_flag_on_tenant_catalogue_rows import COLLECTIONS, migration


class _Db:
    def __init__(self, counts: dict[str, int], present: tuple[str, ...] = COLLECTIONS) -> None:
        self.counts = counts
        self.present = present
        self.queries: list[tuple[str, dict[str, Any]]] = []
        self.aql = self

    def has_collection(self, name: str) -> bool:
        return name in self.present

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None, **_: Any) -> Any:
        binds = bind_vars or {}
        self.queries.append((query, binds))
        return iter([self.counts.get(binds["@collection"], 0)])


def test_the_two_catalogues_are_activities_and_workflow_templates() -> None:
    assert COLLECTIONS == (col.ACTIVITIES, col.WORKFLOW_TEMPLATES)


def test_a_dry_run_counts_and_writes_nothing() -> None:
    db = _Db({col.ACTIVITIES: 1, col.WORKFLOW_TEMPLATES: 2})

    report = migration.up(db, dry_run=True)  # type: ignore[arg-type]

    assert (report.scanned, report.changed, report.dry_run) == (3, 0, True)
    assert report.details == {col.ACTIVITIES: 1, col.WORKFLOW_TEMPLATES: 2}
    assert all("UPDATE" not in query for query, _ in db.queries)


def test_the_write_clears_the_flag_in_both_catalogues() -> None:
    db = _Db({col.ACTIVITIES: 1, col.WORKFLOW_TEMPLATES: 2})

    report = migration.up(db)  # type: ignore[arg-type]

    assert (report.scanned, report.changed) == (3, 3)
    assert [binds["@collection"] for _, binds in db.queries] == list(COLLECTIONS)
    assert all("UPDATE doc WITH {is_system: false}" in query for query, _ in db.queries)
    assert all("doc.tenant_key != ''" in query for query, _ in db.queries)


def test_a_missing_collection_is_skipped() -> None:
    db = _Db({col.WORKFLOW_TEMPLATES: 1}, present=(col.WORKFLOW_TEMPLATES,))

    report = migration.up(db)  # type: ignore[arg-type]

    assert report.changed == 1
    assert [binds["@collection"] for _, binds in db.queries] == [col.WORKFLOW_TEMPLATES]


def test_down_is_refused() -> None:
    with pytest.raises(IrreversibleMigrationError):
        migration.down(_Db({}))  # type: ignore[arg-type]
