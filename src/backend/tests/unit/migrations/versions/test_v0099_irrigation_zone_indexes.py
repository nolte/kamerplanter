"""Tests for v0099_irrigation_zone_indexes (REQ-053 WP 7.1, #2467).

Pinned here: the migration and the bootstrap agree on the shape (a bootstrapped volume is a no-op, the frozen
fields equal the bootstrap constants), the dry run creates nothing, and on a volume with two edges to one bed the
unique index is reported as blocked — never created, never repaired, and the run (the boot) does not fail. The
behaviour against a real server (the index really refuses a second zone, the duplicate count is the AQL's) is
``tests/integration/test_irrigation_zone_repository.py``.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions.v0099_irrigation_zone_indexes import (
    COVERS_TARGET_FIELDS,
    ZONE_SITE_FIELDS,
    migration,
)
from tests.unit.guards.test_tenant_unique_indexes_are_scoped import _RecordingDb


class _Aql:
    def __init__(self, duplicates: int) -> None:
        self.duplicates = duplicates
        self.queries: list[str] = []

    def execute(self, query: str, **_: Any) -> Any:
        self.queries.append(query)
        return iter([self.duplicates])


class _Db(_RecordingDb):
    """A volume that predates WP 7.1: both collections exist, neither index does."""

    def __init__(self, *, duplicates: int = 0) -> None:
        super().__init__()
        self.aql = _Aql(duplicates)
        self.collection(col.IRRIGATION_ZONES)
        self.collection(col.ZONE_COVERS)


def _rows(db: _RecordingDb, name: str) -> list[tuple[list[str], bool]]:
    return [(row["fields"], row["unique"]) for row in db.collections[name].rows]


class TestBootstrapSync:
    def test_the_frozen_fields_equal_the_bootstrap_constants(self) -> None:
        assert list(ZONE_SITE_FIELDS) == col.IRRIGATION_ZONE_SITE_INDEX_FIELDS == ["tenant_key", "site_key"]
        assert list(COVERS_TARGET_FIELDS) == col.ZONE_COVERS_TARGET_INDEX_FIELDS == ["_to"]

    def test_the_bootstrap_builds_both_indexes(self) -> None:
        db = _RecordingDb()
        col.ensure_collections(db)  # type: ignore[arg-type]

        assert (["tenant_key", "site_key"], False) in _rows(db, col.IRRIGATION_ZONES)
        assert (["_to"], True) in _rows(db, col.ZONE_COVERS)

    def test_a_bootstrapped_volume_is_a_noop(self) -> None:
        db = _RecordingDb()
        col.ensure_collections(db)  # type: ignore[arg-type]
        db.aql = _Aql(0)  # type: ignore[attr-defined]

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.changed == 0
        assert db.aql.queries == []  # type: ignore[attr-defined]  # an existing unique index needs no duplicate scan


class TestUp:
    def test_creates_both_indexes_once(self) -> None:
        db = _Db()

        first = migration.up(db)  # type: ignore[arg-type]
        second = migration.up(db)  # type: ignore[arg-type]

        assert (first.changed, second.changed) == (2, 0)
        assert _rows(db, col.IRRIGATION_ZONES) == [(["tenant_key", "site_key"], False)]
        assert _rows(db, col.ZONE_COVERS) == [(["_to"], True)]

    def test_the_dry_run_reports_and_creates_nothing(self) -> None:
        db = _Db(duplicates=3)

        report = migration.up(db, dry_run=True)  # type: ignore[arg-type]

        assert (report.dry_run, report.changed) == (True, 0)
        assert report.details["will_create"] == ["zone_site", "covers_target"]
        assert report.details["duplicate_targets"] == 3
        assert _rows(db, col.IRRIGATION_ZONES) == [] and _rows(db, col.ZONE_COVERS) == []

    def test_duplicate_coverage_blocks_the_unique_index_without_failing_the_run(self) -> None:
        from arango.exceptions import IndexCreateError

        db = _Db(duplicates=1)
        covers = db.collection(col.ZONE_COVERS)

        def refuse(**_: Any) -> None:
            error = IndexCreateError.__new__(IndexCreateError)
            error.error_code = 1210  # what ArangoDB answers a unique index over duplicate values with
            raise error

        covers.add_persistent_index = refuse  # type: ignore[method-assign]

        report = migration.up(db)  # type: ignore[arg-type]

        assert (report.changed, report.details["covers_target_blocked"]) == (1, True)  # the zone-site index only
        assert report.details["duplicate_targets"] == 1
        assert _rows(db, col.ZONE_COVERS) == []

    def test_a_non_unique_target_index_does_not_count(self) -> None:
        db = _Db()
        db.collection(col.ZONE_COVERS).add_persistent_index(fields=["_to"], unique=False)

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.details["covers_target_index_present"] is False
        assert (["_to"], True) in _rows(db, col.ZONE_COVERS)

    def test_absent_collections_are_skipped(self) -> None:
        db = _RecordingDb()
        db.aql = _Aql(0)  # type: ignore[attr-defined]

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.changed == 0
        assert report.details["collections_absent"] == sorted([col.IRRIGATION_ZONES, col.ZONE_COVERS])


def test_down_is_irreversible() -> None:
    with pytest.raises(IrreversibleMigrationError):
        migration.down(_Db())  # type: ignore[arg-type]
