"""v0097 (#2325, #2346, REQ-053 M5): cron rules converted, unconvertible rules parked, on a fake volume.

The fake dispatches the scan and the batched ``UPDATE`` on their text. The real AQL is
measured in ``tests/integration/test_v0096_v0097_req053_m5_m6.py``.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions import v0097_recurrence_cron_to_rrule as module
from app.migrations.versions.v0097_recurrence_cron_to_rrule import migration


class _FakeAql:
    def __init__(self, db: _FakeDb) -> None:
        self.db = db
        self.updates: list[list[dict[str, str]]] = []
        self.parks: list[list[dict[str, str]]] = []

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None, **_: Any) -> Any:
        bind_vars = bind_vars or {}
        assert bind_vars["@collection"] == col.TASKS
        if "UPDATE u._key" in query and "recurrence_rule_unconvertible" not in query:
            self.updates.append(list(bind_vars["updates"]))
            for update in bind_vars["updates"]:
                self.db.docs[update["_key"]]["recurrence_rule"] = update["rule"]
            return iter(())
        if "recurrence_rule_unconvertible: u.rule" in query:
            self.parks.append(list(bind_vars["updates"]))
            for update in bind_vars["updates"]:
                doc = self.db.docs[update["_key"]]
                if doc.get("recurrence_rule") == update["rule"]:
                    doc["recurrence_rule"] = None
                    doc["recurrence_rule_unconvertible"] = update["rule"]
            return iter(())
        if "t.recurrence_rule != null" in query:
            with_rule = [d for d in self.db.docs.values() if d.get("recurrence_rule")]
            return iter(
                {"_key": d["_key"], "tenant_key": d.get("tenant_key"), "rule": d["recurrence_rule"]} for d in with_rule
            )
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


#: Free text, ``@daily`` and a six-field cron are not five-field crons; ``*/15`` is, but has no RRULE.
_UNCONVERTIBLE = {
    "free_text": ("weekly", "not_a_five_field_cron"),
    "at_daily": ("@daily", "not_a_five_field_cron"),
    "six_field": ("0 0 8 * * 1", "not_a_five_field_cron"),
    "quarter_hourly": ("*/15 * * * *", "cron_without_lossless_rrule"),
}


def _expected_parked() -> list[dict[str, str]]:
    return [
        {"_key": key, "tenant_key": "tenant-a", "rule": rule, "reason": reason}
        for key, (rule, reason) in _UNCONVERTIBLE.items()
    ]


def _volume(*, with_refusal: bool = False) -> _FakeDb:
    docs = [
        {"_key": "monday", "recurrence_rule": "0 8 * * 1"},  # GP-ACC-038
        {"_key": "daily", "recurrence_rule": "0 9 * * *"},
        {"_key": "rrule", "recurrence_rule": "FREQ=WEEKLY;BYDAY=MO"},
        {"_key": "none", "recurrence_rule": None},
        {"_key": "empty", "recurrence_rule": ""},
        {"_key": "one_off", "name": "no rule at all"},
    ]
    if with_refusal:
        docs.extend(
            {"_key": key, "tenant_key": "tenant-a", "recurrence_rule": rule}
            for key, (rule, _) in _UNCONVERTIBLE.items()
        )
    return _FakeDb(docs)


class TestConversion:
    def test_cron_rules_become_rrules_and_rrules_are_untouched(self) -> None:
        db = _volume()

        report = migration.up(db)

        assert report.changed == 2 and report.scanned == 3 and report.precondition_unmet is False
        assert db.docs["monday"]["recurrence_rule"] == "FREQ=WEEKLY;BYDAY=MO;BYHOUR=8;BYMINUTE=0"
        assert db.docs["daily"]["recurrence_rule"] == "FREQ=DAILY;BYHOUR=9;BYMINUTE=0"
        assert db.docs["rrule"]["recurrence_rule"] == "FREQ=WEEKLY;BYDAY=MO"
        assert report.details["already_rrule"] == 1
        assert report.details["convertible"] == {
            "count": 2,
            "listed": [
                {"_key": "monday", "from": "0 8 * * 1", "rule": "FREQ=WEEKLY;BYDAY=MO;BYHOUR=8;BYMINUTE=0"},
                {"_key": "daily", "from": "0 9 * * *", "rule": "FREQ=DAILY;BYHOUR=9;BYMINUTE=0"},
            ],
        }
        assert report.details["parked"] == {"count": 0, "listed": []}

    def test_second_run_changes_nothing(self) -> None:
        db = _volume()
        migration.up(db)
        before = db.snapshot()

        report = migration.up(db)

        assert report.changed == 0 and report.noop is True and report.details["already_rrule"] == 3
        assert db.snapshot() == before and len(db.aql.updates) == 1

    def test_dry_run_lists_and_writes_nothing(self) -> None:
        db = _volume(with_refusal=True)
        before = db.snapshot()

        report = migration.up(db, dry_run=True)

        assert report.dry_run is True and report.changed == 0 and report.precondition_unmet is False
        assert report.details["convertible"]["count"] == 2
        assert report.details["parked"] == {"count": 4, "listed": _expected_parked()}
        assert db.snapshot() == before and db.aql.updates == [] and db.aql.parks == []

    def test_mixed_volume_converts_parks_and_records(self) -> None:
        """RRULE, convertible cron, free text, ``@daily``, six-field cron: nothing halts the chain."""
        db = _volume(with_refusal=True)

        report = migration.up(db)

        assert report.precondition_unmet is False and report.dry_run is False
        assert report.scanned == 7 and report.changed == 2 + 4 and report.details["already_rrule"] == 1
        assert db.docs["monday"]["recurrence_rule"] == "FREQ=WEEKLY;BYDAY=MO;BYHOUR=8;BYMINUTE=0"
        assert db.docs["rrule"]["recurrence_rule"] == "FREQ=WEEKLY;BYDAY=MO"
        for key, (rule, _reason) in _UNCONVERTIBLE.items():
            assert db.docs[key]["recurrence_rule"] is None
            assert db.docs[key]["recurrence_rule_unconvertible"] == rule  # original value, unchanged
            assert db.docs[key]["tenant_key"] == "tenant-a"

    def test_report_lists_every_parked_rule_in_full(self) -> None:
        """The P-1 dry-run report: task key, tenant key, original value and reason, never capped."""
        db = _volume(with_refusal=True)

        report = migration.up(db)

        assert report.details["parked"] == {"count": 4, "listed": _expected_parked()}
        assert report.to_dict()["details"]["parked"]["listed"][0].keys() == {"_key", "tenant_key", "rule", "reason"}

    def test_parked_rules_are_never_capped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(module, "_LISTED_CONVERSIONS", 1)
        db = _FakeDb([{"_key": f"t{i}", "tenant_key": "x", "recurrence_rule": "weekly"} for i in range(5)])

        report = migration.up(db, dry_run=True)

        assert report.details["parked"]["count"] == 5 and len(report.details["parked"]["listed"]) == 5

    def test_second_run_after_parking_changes_nothing(self) -> None:
        """Idempotent: a parked task has ``recurrence_rule == null`` and is not touched again."""
        db = _volume(with_refusal=True)
        migration.up(db)
        before = db.snapshot()
        updates, parks = len(db.aql.updates), len(db.aql.parks)

        report = migration.up(db)

        assert report.changed == 0 and report.noop is True and report.precondition_unmet is False
        assert report.details["parked"] == {"count": 0, "listed": []}
        assert db.snapshot() == before and (len(db.aql.updates), len(db.aql.parks)) == (updates, parks)

    def test_a_rule_edited_since_the_scan_is_not_parked(self) -> None:
        """The park statement only touches a task whose rule is still the scanned value."""
        db = _FakeDb([{"_key": "raced", "tenant_key": "x", "recurrence_rule": "weekly"}])
        db.docs["raced"]["recurrence_rule"] = "FREQ=DAILY"

        db.aql.execute(
            module._PARK, bind_vars={"@collection": col.TASKS, "updates": [{"_key": "raced", "rule": "weekly"}]}
        )

        assert db.docs["raced"] == {"_key": "raced", "tenant_key": "x", "recurrence_rule": "FREQ=DAILY"}

    def test_updates_are_batched(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(module, "_BATCH_SIZE", 4)
        db = _FakeDb([{"_key": f"t{i}", "recurrence_rule": "0 9 * * *"} for i in range(10)])

        migration.up(db)

        assert [len(chunk) for chunk in db.aql.updates] == [4, 4, 2]

    def test_the_conversion_list_is_capped_but_counted(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(module, "_LISTED_CONVERSIONS", 3)
        db = _FakeDb([{"_key": f"t{i}", "recurrence_rule": "0 9 * * *"} for i in range(5)])

        report = migration.up(db, dry_run=True)

        assert report.details["convertible"]["count"] == 5
        assert len(report.details["convertible"]["listed"]) == 3

    def test_a_volume_without_the_collection_is_a_noop(self) -> None:
        report = migration.up(_FakeDb(present=False))

        assert report.changed == 0 and report.scanned == 0

    def test_down_is_refused(self) -> None:
        with pytest.raises(IrreversibleMigrationError):
            migration.down(_FakeDb())
