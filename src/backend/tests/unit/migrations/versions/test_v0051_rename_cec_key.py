"""v0051 moves the stored substrate CEC to the key the model reads (#1468).

What this tier can decide: the classification (which document is renamed, which is
reported, which is already correct), that ``dry_run`` writes nothing, that a
re-run is a no-op, and that the write is issued with the two keyword arguments the
rename depends on.

What it deliberately does **not** decide: whether ``keep_none=False`` makes the
server *delete* the old attribute. A double asserting that would only restate my
belief about ArangoDB; ``tests/integration/test_v0051_rename_cec_key.py`` measures
it against a real ``arangodb:3.12`` with ``HAS``.

The AQL double answers this migration's own query and refuses one it does not
recognise — including one that has grown a tenant filter. A double that returned
``[]`` for an unknown query would make every assertion here pass vacuously,
starting with the idempotence one, which is supposed to observe an empty write
list.
"""

from __future__ import annotations

import re
from typing import Any

import pytest

from app.migrations.versions.v0051_rename_cec_key import (
    NEW_KEY,
    OLD_KEY,
    RenameCecKeyMigration,
)

_SUBSTRATES = "substrates"
_ABSENT = object()


class _Collection:
    def __init__(self, docs: dict[str, dict[str, Any]]) -> None:
        self.docs = docs
        self.updates: list[tuple[dict[str, Any], bool, bool]] = []

    def update(self, patch: dict[str, Any], keep_none: bool = True, merge: bool = True) -> None:
        """Model ArangoDB's PATCH, including the ``keepNull`` semantics this rename rests on.

        The parameter names are python-arango's (``keep_none``, not AQL's
        ``keepNull`` — ``keep_null`` raises ``TypeError`` on the real driver), so a
        migration calling the wrong one fails here too and not only live.
        """
        self.updates.append((dict(patch), keep_none, merge))
        doc = self.docs[patch["_key"]]
        for name, value in patch.items():
            if name == "_key":
                continue
            if value is None and not keep_none:
                doc.pop(name, None)
                continue
            if merge and isinstance(value, dict) and isinstance(doc.get(name), dict):
                doc[name] = {**doc[name], **value}
            else:
                doc[name] = value


class _Aql:
    def __init__(self, substrates: _Collection) -> None:
        self._substrates = substrates

    def execute(self, query: str, bind_vars: dict | None = None, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: ARG002
        normalised = re.sub(r"\s+", " ", query).strip()
        if _SUBSTRATES not in normalised:
            raise AssertionError(f"unexpected query, this double cannot answer it: {normalised!r}")
        if "tenant_key ==" in normalised or "tenant_key ||" in normalised:
            raise AssertionError(
                "the migration has grown a tenant filter. A key that moved moved for every owner: "
                "a mix a tenant stored before #1174 reads as None for them exactly like a seed record."
            )
        assert bind_vars == {"old": OLD_KEY, "new": NEW_KEY}, f"unexpected bind vars: {bind_vars!r}"

        rows = []
        for key, doc in self._substrates.docs.items():
            rows.append(
                {
                    "_key": key,
                    "type": doc.get("type"),
                    "name_de": doc.get("name_de"),
                    "brand": doc.get("brand"),
                    "tenant_key": doc.get("tenant_key"),
                    "has_old": OLD_KEY in doc,
                    "has_new": NEW_KEY in doc,
                    "old_value": doc.get(OLD_KEY),
                    "new_value": doc.get(NEW_KEY),
                }
            )
        return rows


class _Db:
    def __init__(self, docs: dict[str, dict[str, Any]]) -> None:
        self._col = _Collection(docs)
        self.aql = _Aql(self._col)

    def has_collection(self, name: str) -> bool:
        return name == _SUBSTRATES

    def collection(self, name: str) -> _Collection:
        assert name == _SUBSTRATES
        return self._col

    # ── what the assertions read ──────────────────────────────────────────────

    def docs(self, key: str) -> dict[str, Any]:
        """The stored document, as the double holds it after any writes."""
        return self._col.docs[key]

    @property
    def updates(self) -> list[tuple[dict[str, Any], bool, bool]]:
        """``(patch, keep_none, merge)`` per write the migration issued."""
        return self._col.updates


def _doc(name_de: str, *, tenant: str = "", old: Any = _ABSENT, new: Any = _ABSENT) -> dict[str, Any]:
    doc: dict[str, Any] = {"type": "soil", "name_de": name_de, "tenant_key": tenant}
    if old is not _ABSENT:
        doc[OLD_KEY] = old
    if new is not _ABSENT:
        doc[NEW_KEY] = new
    return doc


@pytest.fixture
def migration() -> RenameCecKeyMigration:
    return RenameCecKeyMigration()


@pytest.fixture
def db() -> _Db:
    """One document per category, plus a tenant-owned mix carrying the old key."""
    return _Db(
        {
            "seeded": _doc("Universalerde", old=15.0),
            "tenant_mix": _doc("Mein Mix", tenant="mein-garten", old=6.0),
            "conflict": _doc("Beides", old=99.0, new=12.0),
            "current": _doc("Schon korrekt", new=8.5),
            "no_cec": _doc("Hydrokultur (kein Substrat)"),
        }
    )


class TestTheRename:
    def test_the_value_moves_to_the_new_key(self, migration, db):
        migration.up(db)

        assert db.docs("seeded")[NEW_KEY] == 15.0

    def test_the_old_key_is_dropped(self, migration, db):
        migration.up(db)

        assert OLD_KEY not in db.docs("seeded")

    def test_a_tenant_owned_mix_is_renamed_too(self, migration, db):
        migration.up(db)

        assert db.docs("tenant_mix")[NEW_KEY] == 6.0
        assert OLD_KEY not in db.docs("tenant_mix")

    def test_the_write_carries_the_two_keywords_the_rename_depends_on(self, migration, db):
        """``keep_none=False`` is what removes the attribute; ``merge=False`` is
        the flag v0047 settled against a live server. Both are asserted here so a
        later edit cannot drop one and stay green in this tier."""
        migration.up(db)

        assert [(keep_none, merge) for _patch, keep_none, merge in db.updates] == [(False, False)] * 2

    def test_only_the_two_cec_attributes_are_written(self, migration, db):
        migration.up(db)

        for patch, _keep_none, _merge in db.updates:
            assert set(patch) == {"_key", OLD_KEY, NEW_KEY}
            assert patch[OLD_KEY] is None


class TestTheConflictCase:
    def test_a_document_with_both_keys_is_not_written(self, migration, db):
        migration.up(db)

        assert [patch["_key"] for patch, _k, _m in db.updates] == ["seeded", "tenant_mix"]

    def test_the_new_key_keeps_its_value(self, migration, db):
        """``cm3`` wins by not being touched: it is what the model reads today, and
        nothing here can tell a leftover from a number somebody meant."""
        migration.up(db)

        assert db.docs("conflict")[NEW_KEY] == 12.0
        assert db.docs("conflict")[OLD_KEY] == 99.0

    def test_it_is_reported_with_both_values(self, migration, db):
        report = migration.up(db)

        assert report.details["both_keys_present_total"] == 1
        row = report.details["both_keys_present"][0]
        assert "Beides" in row
        assert "99.0" in row
        assert "12.0" in row


class TestTheReport:
    def test_every_scanned_document_lands_in_exactly_one_category(self, migration, db):
        report = migration.up(db)

        totals = {
            category: report.details[f"{category}_total"]
            for category in ("renamed", "both_keys_present", "already_correct", "no_cec_stored")
        }
        assert totals == {"renamed": 2, "both_keys_present": 1, "already_correct": 1, "no_cec_stored": 1}
        assert sum(totals.values()) == report.scanned == 5
        assert report.changed == 2

    def test_a_record_is_named_by_owner_so_an_operator_can_find_it(self, migration, db):
        report = migration.up(db)

        rows = report.details["renamed"]
        assert any("base catalogue" in row and "Universalerde" in row for row in rows)
        assert any("tenant=mein-garten" in row and "Mein Mix" in row for row in rows)

    def test_the_itemised_lists_are_capped_while_the_totals_stay_exact(self, migration):
        """600 renamable documents: the list caps at 500, the counter says 600."""
        big = _Db({f"s{i}": _doc(f"Substrat {i}", old=float(i)) for i in range(600)})

        report = migration.up(big)

        assert report.details["renamed_total"] == 600
        assert len(report.details["renamed"]) == 500
        assert report.changed == 600


class TestDryRun:
    def test_it_writes_nothing(self, migration, db):
        migration.up(db, dry_run=True)

        assert db.updates == []
        assert db.docs("seeded")[OLD_KEY] == 15.0

    def test_it_reports_the_plan_the_real_run_would_execute(self, migration, db):
        dry = migration.up(db, dry_run=True)
        wet = migration.up(db)

        assert dry.details["renamed"] == wet.details["renamed"]
        assert dry.scanned == wet.scanned
        assert dry.changed == 0
        assert wet.changed == 2


class TestIdempotence:
    def test_a_second_run_writes_nothing(self, migration, db):
        migration.up(db)

        second = migration.up(db)

        assert second.changed == 0
        assert second.noop is True
        assert len(db.updates) == 2

    def test_the_converted_records_report_as_already_correct(self, migration, db):
        migration.up(db)

        second = migration.up(db)

        assert second.details["renamed_total"] == 0
        assert second.details["already_correct_total"] == 3


class TestAnUnbootstrappedDatabase:
    def test_a_missing_collection_is_a_no_op(self, migration):
        class _Empty:
            def has_collection(self, name: str) -> bool:  # noqa: ARG002
                return False

        report = migration.up(_Empty())

        assert report.scanned == 0
        assert report.changed == 0
