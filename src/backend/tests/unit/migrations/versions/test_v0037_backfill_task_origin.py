"""Tests for v0037_backfill_task_origin (#1082).

The migration stamps ``origin = 'user'`` on tasks that predate the FreeStyle
provenance field. Idempotency keys on the attribute being *absent* (``origin ==
null``), because ``'user'`` is a legitimate final value — a re-run must not
re-touch a row it already backfilled. Dry-run computes the plan and writes
nothing. Irreversible.
"""

from __future__ import annotations

from typing import Any

from app.data_access.arango import collections as col
from app.migrations.versions.v0037_backfill_task_origin import migration


class _FakeAql:
    def __init__(self, db: _FakeDb) -> None:
        self._db = db

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        bind_vars = bind_vars or {}
        if "UPDATE" in query:
            docs = self._db.data[bind_vars["@collection"]]
            for key in bind_vars["keys"]:
                docs[key]["origin"] = bind_vars["origin"]
            return iter([])
        # The attribute-absence scan: FILTER doc.origin == null.
        docs = self._db.data.get(bind_vars["@collection"], {})
        return iter({"key": key} for key, doc in docs.items() if "origin" not in doc)


class _FakeDb:
    def __init__(self, data: dict[str, dict[str, dict]]) -> None:
        self.data = data
        self.aql = _FakeAql(self)

    def has_collection(self, name: str) -> bool:
        return name in self.data


def _sample() -> _FakeDb:
    return _FakeDb(
        {
            col.TASKS: {
                # Predates the field → stamped user.
                "t-legacy-1": {"name": "Giessen"},
                "t-legacy-2": {"name": "Umtopfen"},
                # Already user-authored → skipped (attribute present).
                "t-user": {"name": "Manuell", "origin": "user"},
                # Already machine-marked → MUST NOT be flipped to user.
                "t-pipeline": {"name": "Analyse", "origin": "pipeline", "source": "goose/x"},
            }
        }
    )


def test_legacy_tasks_are_stamped_user():
    db = _sample()

    migration.up(db)

    assert db.data[col.TASKS]["t-legacy-1"]["origin"] == "user"
    assert db.data[col.TASKS]["t-legacy-2"]["origin"] == "user"


def test_machine_marked_task_is_left_untouched():
    db = _sample()

    migration.up(db)

    # The key correctness point: a row that already declares a machine origin is
    # skipped (attribute present), never rewritten to 'user'.
    assert db.data[col.TASKS]["t-pipeline"]["origin"] == "pipeline"
    assert db.data[col.TASKS]["t-user"]["origin"] == "user"


def test_report_counts_only_the_backfilled_rows():
    db = _sample()

    report = migration.up(db)

    assert report.changed == 2
    assert report.scanned == 2
    assert report.details["tasks"] == 2


def test_dry_run_writes_nothing():
    db = _sample()

    report = migration.up(db, dry_run=True)

    assert report.changed == 0
    assert "origin" not in db.data[col.TASKS]["t-legacy-1"]
    assert report.details["to_update"] == 2


def test_rerun_is_a_noop():
    db = _sample()

    migration.up(db)
    report = migration.up(db)

    assert report.changed == 0


def test_empty_database_is_safe():
    db = _FakeDb({})

    report = migration.up(db)

    assert report.changed == 0
