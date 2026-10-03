"""#2064 — an index an older image re-creates is retired again by the next boot.

On a real ArangoDB 3.12: every migration runs, then the index calls of the image
before each retirement re-create the legacy indexes (``persistent`` and, as a pre-June
image did, ``hash``), then the boot path runs again
(``ensure_collections`` + ``run_pending_migrations``). Before #2064 the second boot ran
no migration and left every legacy index in place.
"""

from __future__ import annotations

import pytest
from arango.exceptions import DocumentInsertError, IndexCreateError

from app.data_access.arango import collections as col
from app.migrations.framework.runner import run_pending_migrations
from app.migrations.support import retired_indexes
from app.migrations.support.legacy_indexes import indexes_on
from app.migrations.support.retired_indexes import RETIRED_INDEXES
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the boot drops re-created indexes on a real server"),
]

_DB_NAME = run_database_name("retired_index_catalogue")


@pytest.fixture
def db(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(retired_indexes, "_last", None)
    system, database = create_database(_DB_NAME)
    run_pending_migrations(database)
    yield database
    system.delete_database(_DB_NAME)


def _boot(database) -> None:
    """What ``app.main.lifespan`` does before the seeds."""
    col.ensure_collections(database)
    run_pending_migrations(database)


def _older_image_creates(database, *, index_type: str) -> None:
    """The legacy index calls of the images before each retirement."""
    for entry in RETIRED_INDEXES:
        database.collection(entry.collection).add_index(
            {
                "type": index_type,
                "fields": list(entry.legacy.fields),
                "unique": entry.legacy.unique,
                "sparse": entry.legacy.sparse,
            }
        )


@pytest.mark.parametrize("index_type", ["persistent", "hash"])
def test_every_catalogued_index_an_older_image_recreates_is_retired_by_the_next_boot(db, index_type: str) -> None:
    _older_image_creates(db, index_type=index_type)
    recreated = [
        e.label for e in RETIRED_INDEXES if any(e.legacy.matches(i) for i in db.collection(e.collection).indexes())
    ]
    assert len(recreated) == len(RETIRED_INDEXES)

    _boot(db)

    for entry in RETIRED_INDEXES:
        rows = db.collection(entry.collection).indexes()
        assert not [i for i in rows if entry.legacy.matches(i)], entry.label
        assert [i for i in rows if entry.replacement.matches(i)], entry.label
    assert retired_indexes.last_enforcement().re_retired == tuple(e.label for e in RETIRED_INDEXES)


def test_the_retired_tank_constraint_is_gone_again_for_a_second_tenant(db) -> None:
    """The defect #2029 closed, back after the older image, closed again after the boot."""
    tanks = db.collection(col.TANKS)
    tanks.add_persistent_index(fields=["name"], unique=True)
    tanks.insert({"name": "Tank 1", "tenant_key": "tenant-a"})
    with pytest.raises(DocumentInsertError):
        tanks.insert({"name": "Tank 1", "tenant_key": "tenant-b"})

    _boot(db)

    tanks.insert({"name": "Tank 1", "tenant_key": "tenant-b"})
    with pytest.raises(DocumentInsertError):
        tanks.insert({"name": "Tank 1", "tenant_key": "tenant-b"})


def test_with_cross_tenant_duplicates_the_older_image_cannot_recreate_it(db) -> None:
    """The other branch of #2064: the old pod's ensure_collections fails, nothing to retire."""
    tanks = db.collection(col.TANKS)
    tanks.insert({"name": "Tank 1", "tenant_key": "tenant-a"})
    tanks.insert({"name": "Tank 1", "tenant_key": "tenant-b"})

    with pytest.raises(IndexCreateError) as raised:
        tanks.add_persistent_index(fields=["name"], unique=True)

    assert raised.value.error_code == 1210
    assert indexes_on(tanks, ["name"]) == []


def test_without_the_replacement_the_boot_refuses_and_reports_it(db, monkeypatch: pytest.MonkeyPatch) -> None:
    tanks = db.collection(col.TANKS)
    for idx in indexes_on(tanks, col.TANK_NAME_INDEX_FIELDS):
        tanks.delete_index(idx["id"])
    tanks.add_persistent_index(fields=["name"], unique=True)

    run_pending_migrations(db)  # without ensure_collections, which would create the replacement

    assert [i["unique"] for i in indexes_on(tanks, ["name"])] == [True]
    assert retired_indexes.last_enforcement().refused == ("tanks(name)",)
