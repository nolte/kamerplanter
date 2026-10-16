"""v0095 (#2325, REQ-053 M3): ``suggested = false`` stamped on a fake volume — idempotent, a dry run writes nothing.

The fake dispatches the two AQL statements on their text (the key scan and the batched
``UPDATE``) and applies the filter ``t.suggested == null`` itself; the real AQL is
measured in ``tests/integration/test_v0094_v0095_req053_m2_m3.py``. The model side —
``Task`` reads a stored row without the attribute as ``suggested = False`` — is pinned
here too, because it is the reason the migration stamps nothing but the AQL-visible
default.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.common.enums import TaskCategory
from app.data_access.arango import collections as col
from app.domain.models.task import Task
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions import v0095_task_suggested_flag as module
from app.migrations.versions.v0095_task_suggested_flag import migration


class _FakeAql:
    def __init__(self, db: _FakeDb) -> None:
        self.db = db
        self.updates: list[list[str]] = []

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None, **_: Any) -> Any:
        bind_vars = bind_vars or {}
        assert bind_vars["@collection"] == col.TASKS
        if "UPDATE k WITH" in query:
            self.updates.append(list(bind_vars["keys"]))
            for key in bind_vars["keys"]:
                self.db.docs[key]["suggested"] = False
            return iter(())
        if "t.suggested == null" in query:
            return iter(d["_key"] for d in self.db.docs.values() if d.get("suggested") is None)
        raise AssertionError(f"unexpected query: {query}")


class _FakeDb:
    def __init__(self, docs: list[dict[str, Any]] | None = None, *, present: bool = True) -> None:
        self.docs: dict[str, dict[str, Any]] = {d["_key"]: dict(d) for d in docs or []}
        self.present = present
        self.aql = _FakeAql(self)

    def has_collection(self, name: str) -> bool:
        return self.present and name == col.TASKS

    def snapshot(self) -> dict[str, dict[str, Any]]:
        return {k: dict(d) for k, d in self.docs.items()}


def _volume() -> _FakeDb:
    return _FakeDb(
        [
            {"_key": "legacy", "name": "Mulchen", "category": "maintenance"},
            {"_key": "explicit_null", "name": "Gießen", "suggested": None},
            # A newer image already wrote these two; neither is touched.
            {"_key": "proposed", "name": "Fruchtfolge", "suggested": True, "suggestion_reason": "rotation"},
            {"_key": "accepted", "name": "Ernte", "suggested": False},
        ]
    )


class TestStamping:
    def test_rows_without_the_flag_get_false(self) -> None:
        db = _volume()

        report = migration.up(db)

        assert report.changed == 2 and report.scanned == 2 and report.details == {"tasks_without_flag": 2}
        assert db.docs["legacy"]["suggested"] is False
        assert db.docs["explicit_null"]["suggested"] is False
        assert db.docs["proposed"] == {
            "_key": "proposed",
            "name": "Fruchtfolge",
            "suggested": True,
            "suggestion_reason": "rotation",
        }
        assert "suggestion_reason" not in db.docs["legacy"], "the reason is left absent — null and missing agree"

    def test_second_run_changes_nothing(self) -> None:
        db = _volume()
        migration.up(db)
        before = db.snapshot()

        report = migration.up(db)

        assert report.changed == 0 and report.scanned == 0 and report.noop is True
        assert db.snapshot() == before
        assert len(db.aql.updates) == 1

    def test_dry_run_counts_and_writes_nothing(self) -> None:
        db = _volume()
        before = db.snapshot()

        report = migration.up(db, dry_run=True)

        assert report.dry_run is True and report.changed == 0 and report.scanned == 2
        assert report.details == {"tasks_without_flag": 2}
        assert db.snapshot() == before and db.aql.updates == []

    def test_updates_are_batched(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(module, "_BATCH_SIZE", 4)
        db = _FakeDb([{"_key": f"t{i}", "name": "x"} for i in range(10)])

        report = migration.up(db)

        assert [len(chunk) for chunk in db.aql.updates] == [4, 4, 2]
        assert report.changed == 10 and all(d["suggested"] is False for d in db.docs.values())

    def test_a_volume_without_the_collection_is_a_noop(self) -> None:
        report = migration.up(_FakeDb(present=False))

        assert report.changed == 0 and report.scanned == 0

    def test_down_is_refused(self) -> None:
        with pytest.raises(IrreversibleMigrationError):
            migration.down(_FakeDb())


class TestModelSide:
    """What M3 adds in code: the two fields read back with their defaults, the §12.1 values parse."""

    def test_a_stored_row_without_the_fields_reads_as_not_suggested(self) -> None:
        task = Task.model_validate({"_key": "legacy", "name": "Mulchen"})

        assert task.suggested is False and task.suggestion_reason is None
        assert task.model_dump()["suggested"] is False, "the default survives model_dump → persisted on next write"

    @pytest.mark.parametrize(
        "value",
        [
            "mulching",
            "weeding",
            "soil_loosening",
            "sowing",
            "pricking_out",
            "soil_amendment",
            "liming",
            "ph_adjustment",
            "ec_check",
            "flush",
            "thinning",
            "hilling",
            "tillage",
            "covering",
            "uncovering",
            "ventilating",
            "clearing",
            "soil_analysis",
            "rainfall",
            "pollinating",
        ],
    )
    def test_every_section_12_1_category_is_a_task_category(self, value: str) -> None:
        assert TaskCategory(value).value == value
        assert Task(name="x", category=value).category is TaskCategory(value)

    def test_no_existing_value_was_retired(self) -> None:
        before_m3 = {
            "training",
            "pruning",
            "ausgeizen",
            "transplant",
            "feeding",
            "ipm",
            "harvest",
            "observation",
            "maintenance",
            "care_reminder",
            "seasonal",
            "phenological",
            "watering",
            "pest_control",
            "monitoring",
            "cleaning",
        }
        assert before_m3 <= {c.value for c in TaskCategory}
        assert len(TaskCategory) == 36
