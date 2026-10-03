"""#2000 — v0069 retires the collection-wide fertilizer identity index for the per-tenant one.

A legacy volume carries ``fertilizers(product_name, brand)`` unique. With it, a tenant
cannot hold its own product under a global seed's name (and a second tenant cannot
hold a name the first one holds privately). After v0069 only ``(tenant_key,
product_name, brand)`` is unique: one global row per pair, one per tenant.
"""

from __future__ import annotations

import pytest
from arango.exceptions import DocumentInsertError

from app.data_access.arango import collections as col
from app.data_access.arango.collections import (
    FERTILIZER_IDENTITY_INDEX_FIELDS,
    LEGACY_GLOBAL_FERTILIZER_INDEX_FIELDS,
    has_unique_index,
)
from app.migrations.versions.v0069_tenant_scoped_fertilizer_identity_index import migration
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the migration changes indexes on a real server"),
]

_DB_NAME = run_database_name("v0069_fertilizer_identity_index")
_ROW = {"product_name": "CalMag", "brand": "Canna", "fertilizer_type": "supplement"}


@pytest.fixture
def db():
    system, database = create_database(_DB_NAME)
    yield database
    system.delete_database(_DB_NAME)


def _legacy(db) -> None:
    """The index shape of a volume from before #2000: the collection-wide pair beside the compound."""
    db.collection(col.FERTILIZERS).add_persistent_index(fields=LEGACY_GLOBAL_FERTILIZER_INDEX_FIELDS, unique=True)


def _indexes_on(db, fields: list[str]) -> list[dict]:
    return [idx for idx in db.collection(col.FERTILIZERS).indexes() if idx.get("fields") == fields]


def test_a_tenant_may_hold_a_global_seeds_identity_after_the_migration(db) -> None:
    _legacy(db)
    fertilizers = db.collection(col.FERTILIZERS)
    fertilizers.insert({**_ROW, "tenant_key": ""})
    with pytest.raises(DocumentInsertError):
        fertilizers.insert({**_ROW, "tenant_key": "t-grower"})  # the defect, on the legacy shape

    report = migration.up(db)

    assert report.changed == 1
    assert _indexes_on(db, LEGACY_GLOBAL_FERTILIZER_INDEX_FIELDS) == []
    fertilizers.insert({**_ROW, "tenant_key": "t-grower"})
    fertilizers.insert({**_ROW, "tenant_key": "t-other"})


def test_the_shared_catalogue_and_each_tenant_still_hold_one_row_per_pair(db) -> None:
    _legacy(db)
    migration.up(db)
    fertilizers = db.collection(col.FERTILIZERS)
    fertilizers.insert({**_ROW, "tenant_key": ""})
    fertilizers.insert({**_ROW, "tenant_key": "t-grower"})

    for tenant_key in ("", "t-grower"):
        with pytest.raises(DocumentInsertError):
            fertilizers.insert({**_ROW, "tenant_key": tenant_key})


def test_a_volume_without_the_compound_index_gets_it_before_the_legacy_one_goes(db) -> None:
    fertilizers = db.collection(col.FERTILIZERS)
    for idx in _indexes_on(db, FERTILIZER_IDENTITY_INDEX_FIELDS):
        fertilizers.delete_index(idx["id"])
    _legacy(db)

    report = migration.up(db)

    assert report.changed == 2
    assert has_unique_index(fertilizers, FERTILIZER_IDENTITY_INDEX_FIELDS)
    assert _indexes_on(db, LEGACY_GLOBAL_FERTILIZER_INDEX_FIELDS) == []


def test_a_second_run_and_a_dry_run_change_nothing(db) -> None:
    _legacy(db)

    dry = migration.up(db, dry_run=True)
    assert dry.changed == 0
    assert len(_indexes_on(db, LEGACY_GLOBAL_FERTILIZER_INDEX_FIELDS)) == 1

    migration.up(db)
    again = migration.up(db)
    assert again.changed == 0
    assert has_unique_index(db.collection(col.FERTILIZERS), FERTILIZER_IDENTITY_INDEX_FIELDS)
