"""#2027 follow-up — v0078 clears ``is_system`` on tenant rows and leaves every global row alone.

Runs on a database built by today's ``ensure_collections``, with the rows a volume can
carry: a global seed (``tenant_key == ""``), a legacy global row without the field, a
tenant's row flagged ``is_system`` and a tenant's plain row.
"""

from __future__ import annotations

import pytest

from app.data_access.arango import collections as col
from app.migrations.versions.v0078_clear_system_flag_on_tenant_catalogue_rows import COLLECTIONS, migration
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the migration rewrites rows on a real server"),
]

_DB_NAME = run_database_name("v0078_clear_system_flag")
TENANT = "t-grower"


@pytest.fixture
def db():
    system, database = create_database(_DB_NAME)
    for collection in COLLECTIONS:
        database.collection(collection).insert_many(
            [
                {"_key": "seed", "tenant_key": "", "name": "Topping", "is_system": True},
                {"_key": "legacy-global", "name": "Pruning", "is_system": True},
                {"_key": "tenant-flagged", "tenant_key": TENANT, "name": "My routine", "is_system": True},
                {"_key": "tenant-plain", "tenant_key": TENANT, "name": "My other routine", "is_system": False},
            ]
        )
    yield database
    system.delete_database(_DB_NAME)


def _flags(db, collection: str) -> dict[str, bool]:
    return {doc["_key"]: doc.get("is_system") for doc in db.collection(collection).all()}


def test_the_flag_goes_from_tenant_rows_only_and_a_rerun_is_a_noop(db):
    dry = migration.up(db, dry_run=True)
    assert (dry.scanned, dry.changed) == (2, 0)
    assert _flags(db, col.WORKFLOW_TEMPLATES)["tenant-flagged"] is True

    report = migration.up(db)

    assert report.changed == 2
    assert report.details == {col.ACTIVITIES: 1, col.WORKFLOW_TEMPLATES: 1}
    for collection in COLLECTIONS:
        assert _flags(db, collection) == {
            "seed": True,
            "legacy-global": True,
            "tenant-flagged": False,
            "tenant-plain": False,
        }
        assert db.collection(collection).get("tenant-flagged")["tenant_key"] == TENANT
    assert migration.up(db).changed == 0
