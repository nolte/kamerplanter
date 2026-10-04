"""v0080 (#1963): a dry run only reads, report-only classes never write, a missing collection is skipped."""

from __future__ import annotations

from typing import Any

from app.migrations.support.legacy_foreign_fields import CLASSES, COUNT_QUERIES, REQUIRED_COLLECTIONS
from app.migrations.versions.v0080_null_foreign_reference_fields import migration


class _Db:
    def __init__(self, verdict_by_query: dict[str, str], existing: bool = True) -> None:
        self.verdict_by_query = verdict_by_query
        self.existing = existing
        self.reads: list[str] = []
        self.writes: list[str] = []
        self.aql = self

    def has_collection(self, name: str) -> bool:  # noqa: ARG002
        return self.existing

    def execute(self, query: str, bind_vars: dict | None = None, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: ARG002
        if bind_vars is not None:
            self.writes.append(query)
            return []
        self.reads.append(query)
        return [{"key": "k", "verdict": self.verdict_by_query[query], "kept": []}]


def _verdicts() -> dict[str, str]:
    return {c.rows_query: (c.repair_verdict or "left_required_field") for c in CLASSES}


def test_every_class_declares_the_collections_it_reads_and_has_a_count_query() -> None:
    assert {c.name for c in CLASSES} == set(REQUIRED_COLLECTIONS) == set(COUNT_QUERIES)


def test_a_dry_run_only_reads() -> None:
    db = _Db(_verdicts())

    report = migration.up(db, dry_run=True)  # type: ignore[arg-type]

    assert (report.changed, db.writes) == (0, [])
    assert len(db.reads) == len(CLASSES)


def test_only_the_repairable_classes_write_and_the_report_only_ones_are_counted() -> None:
    db = _Db(_verdicts())

    report = migration.up(db)  # type: ignore[arg-type]

    assert report.changed == sum(1 for c in CLASSES if c.repair_verdict is not None) == len(db.writes) == 2
    assert report.details["location_assignment_location_foreign__left"] == 1
    assert report.details["planting_run_entry_species_unreadable__left"] == 1


def test_a_missing_collection_is_a_no_op() -> None:
    db = _Db(_verdicts(), existing=False)

    report = migration.up(db)  # type: ignore[arg-type]

    assert (report.scanned, report.changed, db.reads, db.writes) == (0, 0, [], [])
