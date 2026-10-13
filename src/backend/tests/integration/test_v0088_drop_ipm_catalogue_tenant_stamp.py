"""MT-052 (#2144) — v0088 removes the v0004 stamp from pests, diseases and treatments, on a real ArangoDB.

The volume is stamped by the real ``backfill_tenant_key`` (the v0004 body), so the
test measures the shape a legacy volume holds rather than an invented one: every
IPM row that had no ``tenant_key`` carries the default tenant's key afterwards.
Rows of the tenant-owned collections v0004 stamped as well (sites) keep theirs.
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.migrations.backfill_tenant_key import backfill_tenant_key
from app.migrations.versions.v0088_drop_ipm_catalogue_tenant_stamp import migration
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("v0088_ipm_tenant_stamp")

pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    col.ensure_collections(db)
    db.collection(col.TENANTS).insert(
        {"_key": "t-default", "slug": "home", "name": "Home", "created_at": "2026-01-01T00:00:00+00:00"}
    )
    db.collection(col.MEMBERSHIPS).insert({"user_key": "u1", "tenant_key": "t-default", "role": "admin"})
    db.collection(col.PESTS).insert({"_key": "aphid", "scientific_name": "Aphidoidea", "common_name": "Aphid"})
    db.collection(col.PESTS).insert(
        {"_key": "mite", "scientific_name": "Tetranychus urticae", "common_name": "Mite", "tenant_key": ""}
    )
    db.collection(col.DISEASES).insert({"_key": "mildew", "scientific_name": "Erysiphales", "common_name": "Mildew"})
    db.collection(col.TREATMENTS).insert({"_key": "neem", "name": "Neem oil"})
    db.collection(col.TREATMENTS).insert({"_key": "clean", "name": "Soap"})
    db.collection(col.SITES).insert({"_key": "s1", "name": "Garden"})
    # The v0004 body, as it ran on legacy volumes.
    backfill_tenant_key(db)
    db.collection(col.TREATMENTS).update({"_key": "clean", "tenant_key": None}, keep_none=False)
    yield db
    system.delete_database(TEST_DATABASE)


def test_v0004_did_stamp_the_ipm_catalogues(database) -> None:
    """The measurement the migration rests on: hits are possible, not hypothetical."""
    assert database.collection(col.PESTS).get("aphid")["tenant_key"] == "t-default"
    assert database.collection(col.DISEASES).get("mildew")["tenant_key"] == "t-default"
    assert database.collection(col.TREATMENTS).get("neem")["tenant_key"] == "t-default"


def test_v0088_removes_the_stamp_only_and_is_idempotent(database) -> None:
    pests, diseases, treatments = (database.collection(name) for name in (col.PESTS, col.DISEASES, col.TREATMENTS))

    dry = migration.up(database, dry_run=True)
    assert dry.changed == 0
    assert dry.details["pests_with_tenant_key"] == 2
    assert dry.details["pests_stamped"] == 2  # v0004 stamped the empty one too
    assert dry.details["treatments_with_tenant_key"] == 1
    assert pests.get("aphid")["tenant_key"] == "t-default"

    first = migration.up(database)
    second = migration.up(database)

    assert first.changed == first.scanned == 4
    assert (second.scanned, second.changed) == (0, 0)
    for collection, key in ((pests, "aphid"), (pests, "mite"), (diseases, "mildew"), (treatments, "neem")):
        assert "tenant_key" not in collection.get(key)
    assert pests.get("aphid")["scientific_name"] == "Aphidoidea"
    assert treatments.get("clean")["name"] == "Soap"
    assert database.collection(col.SITES).get("s1")["tenant_key"] == "t-default"
