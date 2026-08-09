"""Tests for v0036_cutover_species_tenant_key (F-3/#808 acceptance-4).

The cutover defaults every existing species to ``tenant_key == ""`` (global) —
including ``origin: tenant`` rows, which are deliberately **left un-owned** (R6:
their creator was never recorded, and a default-tenant stamp would be the #324
regression). Idempotency keys on the attribute being *absent*, because ``""`` is a
legitimate final value here.
"""

from __future__ import annotations

from typing import Any

from app.data_access.arango import collections as col
from app.migrations.versions.v0036_cutover_species_tenant_key import migration


class _FakeAql:
    def __init__(self, db: _FakeDb) -> None:
        self._db = db

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        bind_vars = bind_vars or {}
        if "UPDATE" in query:
            docs = self._db.data[bind_vars["@collection"]]
            for row in bind_vars["rows"]:
                docs[row["key"]]["tenant_key"] = ""
            return iter([])
        # The attribute-absence scan: FILTER doc.tenant_key == null
        collection = bind_vars["@collection"]
        docs = self._db.data.get(collection, {})
        return iter({"key": key, "origin": doc.get("origin")} for key, doc in docs.items() if "tenant_key" not in doc)


class _FakeDb:
    def __init__(self, data: dict[str, dict[str, dict]]) -> None:
        self.data = data
        self.aql = _FakeAql(self)

    def has_collection(self, name: str) -> bool:
        return name in self.data


def _sample() -> _FakeDb:
    return _FakeDb(
        {
            col.SPECIES: {
                # Pre-cutover system seed — no tenant_key attribute yet.
                "sp-system": {"origin": "system", "scientific_name": "Rosa canina"},
                # Pre-cutover user-created — no tenant_key attribute yet.
                "sp-tenant": {"origin": "tenant", "scientific_name": "Ocimum basilicum"},
                # Enriched seed — no tenant_key attribute yet.
                "sp-enrichment": {"origin": "enrichment", "scientific_name": "Mentha spicata"},
                # Already carries the attribute (a fresh-schema insert) — must be skipped.
                "sp-already-global": {"origin": "system", "tenant_key": ""},
            }
        }
    )


def test_all_existing_species_default_to_global():
    db = _sample()

    migration.up(db)

    species = db.data[col.SPECIES]
    assert species["sp-system"]["tenant_key"] == ""
    assert species["sp-tenant"]["tenant_key"] == ""
    assert species["sp-enrichment"]["tenant_key"] == ""


def test_origin_tenant_is_left_global_never_owner_stamped():
    # R6: a legacy origin:tenant species stays part of the shared catalogue — it is
    # defaulted to "" (global), never bound to any tenant.
    db = _sample()

    migration.up(db)

    assert db.data[col.SPECIES]["sp-tenant"]["tenant_key"] == ""


def test_report_counts_split_by_origin():
    db = _sample()

    report = migration.up(db)

    # 3 attribute-less rows are stamped; the already-present row is skipped.
    assert report.changed == 3
    assert report.scanned == 3
    assert report.details["defaulted_global"] == 3
    assert report.details["origin_tenant_left_global"] == 1
    assert report.details["origin_other_left_global"] == 2


def test_already_stamped_row_is_left_untouched():
    db = _sample()

    migration.up(db)

    assert db.data[col.SPECIES]["sp-already-global"]["tenant_key"] == ""


def test_rerun_is_a_noop():
    db = _sample()
    migration.up(db)

    report = migration.up(db)

    assert report.changed == 0
    assert report.noop is True


def test_dry_run_writes_nothing_but_plans_the_full_cutover():
    db = _sample()

    report = migration.up(db, dry_run=True)

    assert report.dry_run is True
    assert report.changed == 0
    assert report.details["to_update"] == 3
    # Nothing written: the attribute is still absent on every candidate row.
    assert "tenant_key" not in db.data[col.SPECIES]["sp-system"]
    assert "tenant_key" not in db.data[col.SPECIES]["sp-tenant"]


def test_empty_database_is_a_noop():
    db = _FakeDb({})

    report = migration.up(db)

    assert report.changed == 0
    assert report.scanned == 0


def test_migration_metadata():
    assert migration.version == "0036"
    assert migration.name == "cutover_species_tenant_key"
    assert migration.reversible is False
