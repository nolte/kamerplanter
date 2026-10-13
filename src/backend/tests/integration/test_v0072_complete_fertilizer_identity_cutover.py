"""Review follow-up to #2030 — v0072 finishes the fertilizer identity cutover v0069 started.

Measured on ArangoDB 3.12: an index created as ``hash`` is still reported as
``type: "hash"``, so v0069 (``type == "persistent"`` only) left a volume's collection-wide
``(product_name, brand)`` constraint in force; and an absent ``tenant_key`` and ``""``
are two values to the compound index, so two "global" rows of one pair were accepted.
"""

from __future__ import annotations

import pytest
from arango.exceptions import DocumentInsertError

from app.data_access.arango import collections as col
from app.data_access.arango.collections import LEGACY_GLOBAL_FERTILIZER_INDEX_FIELDS
from app.migrations.versions.v0069_tenant_scoped_fertilizer_identity_index import migration as v0069
from app.migrations.versions.v0072_complete_fertilizer_identity_cutover import migration
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the migration changes indexes and rows on a real server"),
]

_DB_NAME = run_database_name("v0072_fertilizer_identity_cutover")
_ROW = {"product_name": "CalMag", "brand": "Canna", "fertilizer_type": "supplement"}


@pytest.fixture
def db():
    system, database = create_database(_DB_NAME)
    yield database
    system.delete_database(_DB_NAME)


def _legacy_on_fields(db) -> list[dict]:
    return [
        idx
        for idx in db.collection(col.FERTILIZERS).indexes()
        if idx["fields"] == LEGACY_GLOBAL_FERTILIZER_INDEX_FIELDS
    ]


def test_a_hash_typed_legacy_index_survives_v0069_and_is_dropped_here(db) -> None:
    fertilizers = db.collection(col.FERTILIZERS)
    fertilizers.add_index({"type": "hash", "fields": LEGACY_GLOBAL_FERTILIZER_INDEX_FIELDS, "unique": True})
    fertilizers.insert({**_ROW, "tenant_key": ""})
    v0069.up(db)
    assert [idx["type"] for idx in _legacy_on_fields(db)] == ["hash"], "the gap v0069 left"

    report = migration.up(db)

    assert _legacy_on_fields(db) == []
    assert report.details["legacy_indexes_dropped"] == 1
    fertilizers.insert({**_ROW, "tenant_key": "t-grower"})  # refused while the hash index stood


def test_a_non_unique_index_on_the_same_fields_is_kept(db) -> None:
    db.collection(col.FERTILIZERS).add_persistent_index(fields=LEGACY_GLOBAL_FERTILIZER_INDEX_FIELDS, unique=False)

    migration.up(db)

    assert [idx["unique"] for idx in _legacy_on_fields(db)] == [False]


def test_an_absent_tenant_key_becomes_global_so_a_second_global_row_is_refused(db) -> None:
    fertilizers = db.collection(col.FERTILIZERS)
    legacy = fertilizers.insert(dict(_ROW))["_key"]  # no tenant_key attribute at all

    report = migration.up(db)

    assert fertilizers.get(legacy)["tenant_key"] == ""
    assert report.details["absent_tenant_key_stamped"] == 1
    with pytest.raises(DocumentInsertError):
        fertilizers.insert({**_ROW, "tenant_key": ""})


def test_an_absent_row_with_a_global_twin_is_counted_not_stamped(db) -> None:
    fertilizers = db.collection(col.FERTILIZERS)
    legacy = fertilizers.insert(dict(_ROW))["_key"]
    fertilizers.insert({**_ROW, "tenant_key": ""})  # accepted: the gap itself

    report = migration.up(db)

    assert "tenant_key" not in fertilizers.get(legacy)
    assert report.details["absent_tenant_key_left_beside_global_twin"] == 1


def test_a_dry_run_writes_nothing_and_a_second_run_changes_nothing(db) -> None:
    fertilizers = db.collection(col.FERTILIZERS)
    fertilizers.add_index({"type": "hash", "fields": LEGACY_GLOBAL_FERTILIZER_INDEX_FIELDS, "unique": True})
    legacy = fertilizers.insert(dict(_ROW))["_key"]

    dry = migration.up(db, dry_run=True)
    assert dry.changed == 0
    assert dry.details["to_update"] == 2
    assert "tenant_key" not in fertilizers.get(legacy)
    assert len(_legacy_on_fields(db)) == 1

    assert migration.up(db).changed == 2
    assert migration.up(db).changed == 0
