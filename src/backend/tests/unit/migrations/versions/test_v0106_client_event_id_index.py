"""Tests for v0106_client_event_id_index (REQ-053 WP 9.3, #2743).

Pinned here: the migration and the bootstrap agree on the shape (unique **and sparse**, ``tenant_key`` first; a
bootstrapped volume is a no-op), a volume that predates WP 9.3 gets all three indexes once, the dry run creates
nothing, and a volume that holds a duplicate id is reported as blocked without failing the run. That the index
really refuses a second object under one id is ``tests/integration/test_client_event_idempotency.py``.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.domain.models.care_event import MAX_AGE_DAYS
from app.domain.models.client_event import CLIENT_EVENT_TOMBSTONE_DAYS
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions.v0106_client_event_id_index import (
    INDEXES,
    TOMBSTONE_FIELDS,
    TOMBSTONE_TTL_FIELDS,
    TOMBSTONE_TTL_SECONDS,
    TOMBSTONES,
    migration,
)
from app.observability.garden_plan_metrics import CLIENT_EVENT_INDEX_BLOCKED
from tests.unit.guards.test_tenant_unique_indexes_are_scoped import _RecordingDb

_COLLECTIONS = (col.CARE_EVENTS, col.TASKS, col.ATTACHMENTS, col.CARE_CONFIRMATIONS)


class _Aql:
    def __init__(self, duplicates: int) -> None:
        self.duplicates = duplicates
        self.queries: list[tuple[str, dict[str, Any]]] = []

    def execute(self, query: str, **kwargs: Any) -> Any:
        self.queries.append((query, kwargs.get("bind_vars", {})))
        return iter([self.duplicates])


class _Db(_RecordingDb):
    """A volume that predates WP 9.3: the four collections exist, no client-event index and no tombstones do."""

    def __init__(self, *, duplicates: int = 0) -> None:
        super().__init__()
        self.aql = _Aql(duplicates)
        for name in _COLLECTIONS:
            self.collection(name)


def _tombstone_rows(db: _RecordingDb) -> list[tuple[str, list[str], bool, bool]]:
    return [(row["type"], row["fields"], row["unique"], row["sparse"]) for row in db.collections[TOMBSTONES].rows]


def _client_rows(db: _RecordingDb, name: str) -> list[tuple[list[str], bool, bool]]:
    fields = dict(INDEXES)[name]
    return [
        (row["fields"], row["unique"], row["sparse"])
        for row in db.collections[name].rows
        if row["fields"] == list(fields)
    ]


class TestBootstrapSync:
    def test_the_frozen_fields_equal_the_bootstrap_constants(self) -> None:
        frozen = dict(INDEXES)
        assert list(frozen[col.CARE_EVENTS]) == col.CARE_EVENT_CLIENT_EVENT_INDEX_FIELDS
        assert list(frozen[col.TASKS]) == col.TASK_COMPLETION_CLIENT_EVENT_INDEX_FIELDS
        assert list(frozen[col.ATTACHMENTS]) == col.ATTACHMENT_CLIENT_EVENT_INDEX_FIELDS
        assert list(frozen[col.CARE_CONFIRMATIONS]) == col.CARE_CONFIRMATION_COMPLETION_INDEX_FIELDS
        assert TOMBSTONES == col.CLIENT_EVENT_TOMBSTONES
        assert list(TOMBSTONE_FIELDS) == col.CLIENT_EVENT_TOMBSTONE_INDEX_FIELDS
        assert list(TOMBSTONE_TTL_FIELDS) == col.CLIENT_EVENT_TOMBSTONE_TTL_FIELDS
        assert TOMBSTONE_TTL_SECONDS == col.CLIENT_EVENT_TOMBSTONE_TTL_SECONDS == CLIENT_EVENT_TOMBSTONE_DAYS * 86400
        # Each index is scoped: the tenant, or for a confirmation the plant (its parent chain).
        assert all({"tenant_key", "plant_key"} & set(fields) for _, fields in INDEXES)

    def test_the_tombstones_outlive_every_buffered_write(self) -> None:
        assert CLIENT_EVENT_TOMBSTONE_DAYS > MAX_AGE_DAYS

    def test_the_bootstrap_builds_all_unique_and_sparse_and_the_tombstones(self) -> None:
        db = _RecordingDb()
        col.ensure_collections(db)  # type: ignore[arg-type]

        for name in _COLLECTIONS:
            assert _client_rows(db, name) == [(list(dict(INDEXES)[name]), True, True)], name
        assert _tombstone_rows(db) == [
            ("persistent", list(TOMBSTONE_FIELDS), True, False),
            ("ttl", list(TOMBSTONE_TTL_FIELDS), False, False),
        ]

    def test_a_bootstrapped_volume_is_a_noop(self) -> None:
        db = _RecordingDb()
        col.ensure_collections(db)  # type: ignore[arg-type]
        db.aql = _Aql(0)  # type: ignore[attr-defined]

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.changed == 0
        assert db.aql.queries == []  # type: ignore[attr-defined]  # a present index needs no duplicate scan


class TestUp:
    def test_creates_the_three_indexes_once(self) -> None:
        db = _Db()

        first = migration.up(db)  # type: ignore[arg-type]
        second = migration.up(db)  # type: ignore[arg-type]

        assert (first.changed, second.changed) == (5, 0)
        assert sorted(first.details["created"]) == sorted([*_COLLECTIONS, TOMBSTONES])
        for name in _COLLECTIONS:
            assert _client_rows(db, name) == [(list(dict(INDEXES)[name]), True, True)], name
        assert [row[0] for row in _tombstone_rows(db)] == ["persistent", "ttl"]
        ttl = next(row for row in db.collections[TOMBSTONES].rows if row["type"] == "ttl")
        assert ttl["fields"] == ["deleted_at"]

    def test_the_duplicate_scan_binds_the_attribute_name(self) -> None:
        db = _Db()

        migration.up(db, dry_run=True)  # type: ignore[arg-type]

        bound = {(binds["@collection"], binds["id_field"]) for _, binds in db.aql.queries}
        assert bound == {
            (col.CARE_EVENTS, "client_event_id"),
            (col.TASKS, "completion_client_event_id"),
            (col.ATTACHMENTS, "client_event_id"),
            (col.CARE_CONFIRMATIONS, "completion_client_event_id"),
        }
        assert all("client_event_id" not in query for query, _ in db.aql.queries)  # never spliced into the text

    def test_the_dry_run_reports_and_creates_nothing(self) -> None:
        db = _Db(duplicates=2)

        report = migration.up(db, dry_run=True)  # type: ignore[arg-type]

        assert (report.dry_run, report.changed) == (True, 0)
        assert sorted(report.details["will_create"]) == sorted([*_COLLECTIONS, TOMBSTONES])
        assert report.details["duplicate_ids"] == dict.fromkeys(_COLLECTIONS, 2)
        assert all(db.collections[name].rows == [] for name in _COLLECTIONS)
        assert TOMBSTONES not in db.collections

    def test_a_non_sparse_unique_index_does_not_count(self) -> None:
        # A unique index without sparse would make every row without an id collide: it is not the target shape.
        db = _Db()
        db.collection(col.TASKS).add_persistent_index(fields=list(dict(INDEXES)[col.TASKS]), unique=True)

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.details["index_present"][col.TASKS] is False
        assert (list(dict(INDEXES)[col.TASKS]), True, True) in _client_rows(db, col.TASKS)

    def test_a_duplicate_id_blocks_that_index_without_failing_the_run(self) -> None:
        from arango.exceptions import IndexCreateError

        db = _Db(duplicates=1)

        def refuse(**_: Any) -> None:
            error = IndexCreateError.__new__(IndexCreateError)
            error.error_code = 1210  # what ArangoDB answers a unique index over duplicate values with
            raise error

        db.collection(col.ATTACHMENTS).add_persistent_index = refuse  # type: ignore[method-assign]

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.changed == 4  # three client-event indexes and the tombstone collection
        assert report.details["blocked"] == [col.ATTACHMENTS]
        assert db.collections[col.ATTACHMENTS].rows == []
        # The operator's alert: the gauge is up for the blocked collection, down for the others.
        assert CLIENT_EVENT_INDEX_BLOCKED.labels(collection=col.ATTACHMENTS)._value.get() == 1
        assert CLIENT_EVENT_INDEX_BLOCKED.labels(collection=col.TASKS)._value.get() == 0

    def test_an_absent_collection_is_skipped(self) -> None:
        db = _RecordingDb()
        db.aql = _Aql(0)  # type: ignore[attr-defined]

        report = migration.up(db)  # type: ignore[arg-type]

        assert sorted(report.details["collections_absent"]) == sorted(_COLLECTIONS)
        assert report.details["created"] == [TOMBSTONES]  # the tombstone collection is the migration's own


def test_down_is_irreversible() -> None:
    with pytest.raises(IrreversibleMigrationError):
        migration.down(_Db())  # type: ignore[arg-type]
