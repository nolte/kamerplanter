"""#2064 — the boot retires a catalogued legacy index an older image re-created.

The real-server counterpart, with the older image's own index calls, is
``tests/integration/test_retired_index_catalogue.py``.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.data_access.arango.collections import SCHEMA_MIGRATIONS
from app.migrations.framework import tracking
from app.migrations.framework.runner import MigrationRunner
from app.migrations.support import retired_indexes as module
from app.migrations.support.legacy_indexes import IndexShape
from app.migrations.support.retired_indexes import RetiredIndex, enforce_retired_indexes, last_enforcement
from tests.unit.migrations.framework.conftest import FakeDatabase, RecordingMigration

_ENTRY = RetiredIndex(
    collection="tanks",
    legacy=IndexShape(fields=("name",), unique=True),
    replacement=IndexShape(fields=("tenant_key", "name"), unique=True),
    retired_by=("0002",),
)
_LEGACY_HASH = {"id": "tanks/1", "type": "hash", "fields": ["name"], "unique": True, "sparse": False}
_REPLACEMENT = {
    "id": "tanks/2",
    "type": "persistent",
    "fields": ["tenant_key", "name"],
    "unique": True,
    "sparse": False,
}


class _IndexedCollection:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = [dict(row) for row in rows]

    def indexes(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self.rows]

    def delete_index(self, index_id: str, ignore_missing: bool = False) -> bool:  # noqa: ARG002
        self.rows = [row for row in self.rows if row["id"] != index_id]
        return True


class _Db(FakeDatabase):
    """The framework fake plus one collection that answers ``indexes()``."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        super().__init__()
        self.tanks = _IndexedCollection(rows)

    def collection(self, name: str) -> Any:
        return self.tanks if name == "tanks" else super().collection(name)

    def has_collection(self, name: str) -> bool:
        return name == "tanks" or super().has_collection(name)


@pytest.fixture(autouse=True)
def _reset_last(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(module, "_last", None)


class TestEnforcement:
    def test_a_reappeared_legacy_index_is_retired_again(self) -> None:
        db = _Db([_LEGACY_HASH, _REPLACEMENT])

        outcome = enforce_retired_indexes(db, applied={"0001", "0002"}, catalogue=(_ENTRY,))  # type: ignore[arg-type]

        assert outcome.re_retired == ("tanks(name)",)
        assert [row["id"] for row in db.tanks.rows] == ["tanks/2"]
        assert last_enforcement() == outcome

    def test_without_the_replacement_nothing_is_dropped_and_the_refusal_is_reported(self) -> None:
        db = _Db([_LEGACY_HASH])

        outcome = enforce_retired_indexes(db, applied={"0002"}, catalogue=(_ENTRY,))  # type: ignore[arg-type]

        assert outcome.refused == ("tanks(name)",)
        assert outcome.re_retired == ()
        assert [row["id"] for row in db.tanks.rows] == ["tanks/1"]

    def test_an_entry_waits_for_every_retiring_migration(self) -> None:
        entry = RetiredIndex(
            collection=_ENTRY.collection, legacy=_ENTRY.legacy, replacement=_ENTRY.replacement, retired_by=("1", "2")
        )
        db = _Db([_LEGACY_HASH, _REPLACEMENT])

        outcome = enforce_retired_indexes(db, applied={"1"}, catalogue=(entry,))  # type: ignore[arg-type]

        assert outcome.enforced == ()
        assert len(db.tanks.rows) == 2

    def test_a_dry_run_drops_nothing_and_leaves_the_status(self) -> None:
        db = _Db([_LEGACY_HASH, _REPLACEMENT])

        outcome = enforce_retired_indexes(db, applied={"0002"}, catalogue=(_ENTRY,), dry_run=True)  # type: ignore[arg-type]

        assert outcome.re_retired == ("tanks(name)",)
        assert len(db.tanks.rows) == 2
        assert last_enforcement() is None

    def test_a_clean_volume_reports_nothing(self) -> None:
        outcome = enforce_retired_indexes(_Db([_REPLACEMENT]), applied={"0002"}, catalogue=(_ENTRY,))  # type: ignore[arg-type]
        assert (outcome.enforced, outcome.re_retired, outcome.refused) == (("tanks(name)",), (), ())

    def test_a_non_unique_replacement_is_refused_at_definition(self) -> None:
        with pytest.raises(ValueError, match="unique"):
            RetiredIndex(
                collection="x",
                legacy=IndexShape(fields=("a",), unique=True),
                replacement=IndexShape(fields=("a",), unique=False),
                retired_by=("1",),
            )


class TestTheRunnerEnforces:
    """Through ``upgrade`` — the path ``run_pending_migrations`` takes at every boot."""

    def test_on_a_boot_with_nothing_pending(self) -> None:
        db = _Db([_LEGACY_HASH, _REPLACEMENT])
        runner = MigrationRunner([RecordingMigration("0001"), RecordingMigration("0002")], retired_indexes=(_ENTRY,))
        runner.upgrade(db)  # type: ignore[arg-type]
        db.tanks.rows.append(dict(_LEGACY_HASH))  # the older image starts and re-creates it

        assert runner.upgrade(db) == []  # type: ignore[arg-type]

        assert [row["id"] for row in db.tanks.rows] == ["tanks/2"]

    def test_right_after_the_retiring_migration_was_recorded(self) -> None:
        db = _Db([_LEGACY_HASH, _REPLACEMENT])
        runner = MigrationRunner([RecordingMigration("0001"), RecordingMigration("0002")], retired_indexes=(_ENTRY,))

        runner.upgrade(db)  # type: ignore[arg-type]

        assert [row["id"] for row in db.tanks.rows] == ["tanks/2"]

    def test_not_while_the_retiring_migration_is_pending(self) -> None:
        db = _Db([_LEGACY_HASH, _REPLACEMENT])
        runner = MigrationRunner(
            [RecordingMigration("0001"), RecordingMigration("0002", precondition_unmet=True)],
            retired_indexes=(_ENTRY,),
        )

        runner.upgrade(db)  # type: ignore[arg-type]

        assert "0002" not in tracking.applied_versions(db)  # type: ignore[arg-type]
        assert len(db.tanks.rows) == 2

    def test_not_on_a_dry_run(self) -> None:
        db = _Db([_LEGACY_HASH, _REPLACEMENT])
        runner = MigrationRunner([RecordingMigration("0001"), RecordingMigration("0002")], retired_indexes=(_ENTRY,))
        runner.upgrade(db)  # type: ignore[arg-type]
        db.tanks.rows.append(dict(_LEGACY_HASH))

        runner.upgrade(db, dry_run=True)  # type: ignore[arg-type]

        assert len(db.tanks.rows) == 2

    def test_under_the_lock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The lock is held while the catalogue is enforced, and released after."""
        db = _Db([_LEGACY_HASH, _REPLACEMENT])
        held: list[bool] = []

        def spy(*args: Any, **kwargs: Any) -> Any:
            held.append(db.collection(SCHEMA_MIGRATIONS).get(tracking.LOCK_KEY) is not None)
            return module.RetiredIndexEnforcement(enforced=(), re_retired=(), refused=())

        from app.migrations.framework import runner as runner_module

        monkeypatch.setattr(runner_module, "enforce_retired_indexes", spy)
        MigrationRunner([RecordingMigration("0001")], retired_indexes=(_ENTRY,)).upgrade(db)  # type: ignore[arg-type]

        assert held == [True]
        assert db.collection(SCHEMA_MIGRATIONS).get(tracking.LOCK_KEY) is None

    def test_the_default_catalogue_is_the_shipped_one(self) -> None:
        assert MigrationRunner([RecordingMigration("0001")])._retired_indexes is module.RETIRED_INDEXES
