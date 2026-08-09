"""Tests for v0038_cutover_cultivar_tenant_key (#1090 package C-2).

The cutover defaults every existing cultivar to ``tenant_key == ""`` (global) —
including ``origin: tenant`` rows, which are deliberately **left un-owned**: their
creator was never recorded, and a default-tenant stamp would be the #324
regression. Idempotency keys on the attribute being *absent*, because ``""`` is a
legitimate final value here.

The fake database below deliberately models the ``FILTER doc.tenant_key == null``
semantics as "the attribute is missing from the document" — the distinction the
whole policy rests on. A cultivar already carrying ``tenant_key: "some-tenant"``
is in the fixture so the tests prove the migration never overwrites an *existing*
owner (the C-1 write path stamps one, and a re-run must not flatten it to global).
"""

from __future__ import annotations

from typing import Any

from app.data_access.arango import collections as col
from app.migrations.versions.v0038_cutover_cultivar_tenant_key import migration


class _FakeAql:
    def __init__(self, db: _FakeDb) -> None:
        self._db = db
        #: Every executed query, so the AQL text itself can be asserted on. The
        #: fake *implements* the null-filter semantics, so behavioural tests alone
        #: would stay green if the migration's FILTER silently became
        #: ``== ""`` — the queries are recorded to pin that separately.
        self.queries: list[str] = []

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        bind_vars = bind_vars or {}
        self.queries.append(query)
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
            col.CULTIVARS: {
                # Pre-cutover system seed — no tenant_key attribute yet.
                "cv-system": {"origin": "system", "name": "Green Zebra", "species_key": "solanum-lycopersicum"},
                # Pre-cutover user-created — no tenant_key attribute yet.
                "cv-tenant": {"origin": "tenant", "name": "Omas Tomate", "species_key": "solanum-lycopersicum"},
                # Enriched seed — no tenant_key attribute yet.
                "cv-enrichment": {"origin": "enrichment", "name": "Sungold", "species_key": "solanum-lycopersicum"},
                # Already carries the attribute (a fresh-schema insert) — must be skipped.
                "cv-already-global": {"origin": "system", "tenant_key": "", "name": "Black Cherry"},
                # Post-C-1 tenant-owned row — the owner must survive the cutover.
                "cv-owned": {"origin": "tenant", "tenant_key": "tenant-a", "name": "Hausmarke"},
            }
        }
    )


def test_all_existing_cultivars_default_to_global():
    db = _sample()

    migration.up(db)

    cultivars = db.data[col.CULTIVARS]
    assert cultivars["cv-system"]["tenant_key"] == ""
    assert cultivars["cv-tenant"]["tenant_key"] == ""
    assert cultivars["cv-enrichment"]["tenant_key"] == ""


def test_origin_tenant_is_left_global_never_owner_stamped():
    # A legacy origin:tenant cultivar stays part of the shared catalogue — it is
    # defaulted to "" (global), never bound to any tenant (#324).
    db = _sample()

    migration.up(db)

    assert db.data[col.CULTIVARS]["cv-tenant"]["tenant_key"] == ""


def test_report_counts_split_by_origin():
    db = _sample()

    report = migration.up(db)

    # 3 attribute-less rows are stamped; the two rows already carrying the
    # attribute (global and tenant-owned) are skipped.
    assert report.changed == 3
    assert report.scanned == 3
    assert report.details["defaulted_global"] == 3
    assert report.details["origin_tenant_left_global"] == 1
    assert report.details["origin_other_left_global"] == 2


def test_already_stamped_row_is_left_untouched():
    db = _sample()

    migration.up(db)

    assert db.data[col.CULTIVARS]["cv-already-global"]["tenant_key"] == ""


def test_existing_owner_is_never_flattened_to_global():
    # The cutover only *establishes* the attribute; a cultivar the C-1 write path
    # already stamped with an owner must keep it, or the migration would itself be
    # the ownership-loss bug it exists to avoid.
    db = _sample()

    migration.up(db)

    assert db.data[col.CULTIVARS]["cv-owned"]["tenant_key"] == "tenant-a"


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
    assert "tenant_key" not in db.data[col.CULTIVARS]["cv-system"]
    assert "tenant_key" not in db.data[col.CULTIVARS]["cv-tenant"]


def test_missing_collection_is_a_noop():
    # A volume without the cultivars collection must not raise — the scan probes
    # has_collection first.
    db = _FakeDb({})

    report = migration.up(db)

    assert report.changed == 0
    assert report.scanned == 0


def test_species_collection_is_not_touched():
    # v0036 owns the species cutover; v0038 must stay confined to cultivars, so a
    # species row lacking the attribute is left exactly as it is.
    db = _sample()
    db.data[col.SPECIES] = {"sp-legacy": {"origin": "tenant", "scientific_name": "Ocimum basilicum"}}

    migration.up(db)

    assert "tenant_key" not in db.data[col.SPECIES]["sp-legacy"]


def test_scan_filters_on_the_absent_attribute_not_on_empty_string():
    # The idempotency contract lives in the AQL, not in the fake: "" is a
    # legitimate final value, so a FILTER on `== ""` would re-stamp every global
    # row on each run (and, worse, re-own rows the policy left global). Pinned on
    # the query text because the fake DB implements the semantics itself.
    db = _sample()

    migration.up(db)

    scan = next(q for q in db.aql.queries if "UPDATE" not in q)
    assert "doc.tenant_key == null" in scan
    assert 'doc.tenant_key == ""' not in scan
    assert "doc.tenant_key == ''" not in scan


def test_update_stamps_the_empty_string_into_the_cultivars_collection():
    db = _sample()

    migration.up(db)

    update = next(q for q in db.aql.queries if "UPDATE" in q)
    assert "tenant_key: ''" in update
    # Collection comes from the bound @@collection, never interpolated (no AQL
    # injection surface) — assert the binding rather than the literal name.
    assert "@@collection" in update


def test_migration_metadata():
    assert migration.version == "0038"
    assert migration.name == "cutover_cultivar_tenant_key"
    assert migration.reversible is False
