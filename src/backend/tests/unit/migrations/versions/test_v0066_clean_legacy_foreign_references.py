"""v0066 (#1878): a dry run only reads, a clean store runs no write, a missing collection is skipped."""

from __future__ import annotations

from typing import Any

from app.migrations.support.legacy_foreign_references import CLASSES, COUNT_QUERIES, REQUIRED_COLLECTIONS
from app.migrations.versions.v0066_clean_legacy_foreign_references import migration


class _Db:
    def __init__(self, rows: list[dict[str, Any]], existing: bool = True) -> None:
        self.rows = rows
        self.existing = existing
        self.queries: list[str] = []
        self.aql = self

    def has_collection(self, name: str) -> bool:  # noqa: ARG002
        return self.existing

    def execute(self, query: str, bind_vars: dict | None = None, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: ARG002
        self.queries.append(query)
        return list(self.rows) if bind_vars is None else []


def test_every_class_declares_the_collections_it_reads_and_has_a_count_query() -> None:
    assert {c.name for c in CLASSES} == set(REQUIRED_COLLECTIONS) == set(COUNT_QUERIES)


def test_a_dry_run_only_reads() -> None:
    db = _Db([{"key": "k", "verdict": "drop"}])

    report = migration.up(db, dry_run=True)  # type: ignore[arg-type]

    assert report.changed == 0
    assert len(db.queries) == len(CLASSES)


def test_a_missing_collection_is_a_no_op() -> None:
    db = _Db([{"key": "k", "verdict": "drop"}], existing=False)

    report = migration.up(db)  # type: ignore[arg-type]

    assert (report.scanned, report.changed, db.queries) == (0, 0, [])
