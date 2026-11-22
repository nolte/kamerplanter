"""#2857 — v0113 measured on a real ArangoDB: the scan with its species join and the guarded update.

Asserted: a catalogue species' ``day_neutral`` without a seed source becomes ``unspecified``, a sourced one stays,
hemp's default becomes the ``short_day`` its source states, a tenant's own species with a sourced name only gets
``unspecified`` (never the catalogue value), a lifecycle whose species is gone gets ``unspecified``, ``short_day`` and
``long_day`` are never touched, the dry run writes nothing, a second run writes nothing, and the migrated documents load
into ``LifecycleConfig``.

Locally it needs a database::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_v0113_photoperiod_unspecified.py -v
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.common.enums import PhotoperiodType
from app.data_access.arango import collections as col
from app.data_access.arango.collections import ensure_collections
from app.domain.models.lifecycle import LifecycleConfig
from app.migrations.versions.v0113_photoperiod_unspecified import migration
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the migration's species join and guarded UPDATE are AQL over a real server"),
]

_DB_NAME = run_database_name("v0113_photoperiod_unspecified")


@pytest.fixture
def db():  # type: ignore[no-untyped-def]
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    database = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    ensure_collections(database)
    _seed(database)
    yield database
    system.delete_database(_DB_NAME)


def _insert(collection, docs: list[dict]) -> None:  # type: ignore[no-untyped-def]
    refused = [r for r in collection.insert_many(docs) if isinstance(r, Exception)]
    assert not refused, refused


def _seed(db) -> None:  # type: ignore[no-untyped-def]
    _insert(
        db.collection(col.SPECIES),
        [
            {
                "_key": "sp_hemp",
                "scientific_name": "Cannabis sativa",
                "tenant_key": "",
                "scientific_name_normalized": "cannabis sativa",
            },
            {
                "_key": "sp_basil",
                "scientific_name": "Ocimum basilicum",
                "tenant_key": "",
                "scientific_name_normalized": "ocimum basilicum",
            },
            {
                "_key": "sp_unsourced",
                "scientific_name": "Imaginaria nullius",
                "tenant_key": "",
                "scientific_name_normalized": "imaginaria nullius",
            },
            {
                "_key": "sp_no_stamp",
                "scientific_name": "Imaginaria secunda",
                "scientific_name_normalized": "imaginaria secunda",
            },
            {
                # ``scientific_name`` is unique across the catalogue and the tenants, so the tenant's species
                # carries a sourced name no catalogue row here holds.
                "_key": "sp_tenant_dahlia",
                "scientific_name": "Dahlia pinnata",
                "tenant_key": "t_a",
                "scientific_name_normalized": "dahlia pinnata",
            },
            {
                "_key": "sp_lettuce",
                "scientific_name": "Lactuca sativa",
                "tenant_key": "",
                "scientific_name_normalized": "lactuca sativa",
            },
        ],
    )
    _insert(
        db.collection(col.LIFECYCLE_CONFIGS),
        [
            {"_key": "lc_hemp", "species_key": "sp_hemp", "cycle_type": "annual", "photoperiod_type": "day_neutral"},
            {"_key": "lc_basil", "species_key": "sp_basil", "cycle_type": "annual", "photoperiod_type": "day_neutral"},
            {"_key": "lc_unsourced", "species_key": "sp_unsourced", "photoperiod_type": "day_neutral"},
            {"_key": "lc_no_stamp", "species_key": "sp_no_stamp", "photoperiod_type": "day_neutral"},
            {"_key": "lc_tenant_dahlia", "species_key": "sp_tenant_dahlia", "photoperiod_type": "day_neutral"},
            {"_key": "lc_orphan", "species_key": "sp_gone", "photoperiod_type": "day_neutral"},
            {"_key": "lc_no_species", "photoperiod_type": "day_neutral"},
            {"_key": "lc_lettuce", "species_key": "sp_lettuce", "photoperiod_type": "long_day"},
            {"_key": "lc_short", "species_key": "sp_unsourced", "photoperiod_type": "short_day"},
        ],
    )


def _types(db) -> dict[str, str]:  # type: ignore[no-untyped-def]
    return {doc["_key"]: doc["photoperiod_type"] for doc in db.collection(col.LIFECYCLE_CONFIGS).all()}


EXPECTED = {
    "lc_hemp": "short_day",
    "lc_basil": "day_neutral",
    "lc_unsourced": "unspecified",
    "lc_no_stamp": "unspecified",
    "lc_tenant_dahlia": "unspecified",
    "lc_orphan": "unspecified",
    "lc_no_species": "unspecified",
    "lc_lettuce": "long_day",
    "lc_short": "short_day",
}


def test_up_converts_the_defaults_and_corrects_hemp(db) -> None:  # type: ignore[no-untyped-def]
    report = migration.up(db)

    assert _types(db) == EXPECTED
    assert (report.scanned, report.changed) == (7, 6)
    assert report.details["corrected_to"] == {"short_day": 1}
    assert report.details["buckets"]["unspecified_tenant_species"]["listed"] == ["lc_tenant_dahlia"]
    assert report.details["buckets"]["unspecified_species_missing"]["count"] == 2


def test_the_migrated_documents_load(db) -> None:  # type: ignore[no-untyped-def]
    migration.up(db)

    loaded = {
        doc["_key"]: LifecycleConfig(**doc).photoperiod_type for doc in db.collection(col.LIFECYCLE_CONFIGS).all()
    }

    assert loaded["lc_unsourced"] is PhotoperiodType.UNSPECIFIED
    assert loaded["lc_hemp"] is PhotoperiodType.SHORT_DAY


def test_the_dry_run_writes_nothing(db) -> None:  # type: ignore[no-untyped-def]
    before = _types(db)

    report = migration.up(db, dry_run=True)

    assert _types(db) == before
    assert (report.scanned, report.changed, report.details["will_write"]) == (7, 0, 6)


def test_a_second_run_writes_nothing(db) -> None:  # type: ignore[no-untyped-def]
    migration.up(db)

    again = migration.up(db)

    assert _types(db) == EXPECTED
    assert (again.scanned, again.changed) == (1, 0)
    assert again.details["buckets"] == {"kept_sourced": {"count": 1, "listed": ["lc_basil"]}}
