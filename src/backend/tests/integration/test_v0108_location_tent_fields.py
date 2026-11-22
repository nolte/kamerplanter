"""#2832 (REQ-053 WP 10.11, W-016) - v0108 measured on a real ArangoDB.

The AQL of the scan (``HAS`` on the two new names) and of the removal (``keepNull: false`` removes the attribute)
is only proven by a server. A location written by the production writer without the fields is never touched (nothing
is materialised); a refused value is removed and the location then reads through the production ``Location`` model;
a readable value stays; a second run changes no document (``_rev`` stays); a dry run writes nothing.
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.collections import ensure_collections
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.domain.models.site import Location
from app.migrations.versions.v0108_location_tent_fields import migration
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the migration's scan and UPDATE are AQL over a real server"),
]

_DB_NAME = run_database_name("v0108_location_tent_fields")


@pytest.fixture
def db():  # type: ignore[no-untyped-def]
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    database = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    ensure_collections(database)
    yield database
    system.delete_database(_DB_NAME)


def _location(db, name: str, **raw) -> str:  # type: ignore[no-untyped-def]
    created = ArangoSiteRepository(db).create_location(Location(name=name, site_key="", area_m2=1.0))
    assert created.key is not None
    if raw:
        db.collection(col.LOCATIONS).update({"_key": created.key, **raw})
    return created.key


def _revs(db) -> dict[str, str]:  # type: ignore[no-untyped-def]
    return {doc["_key"]: doc["_rev"] for doc in db.collection(col.LOCATIONS).all()}


def test_refused_values_are_removed_and_the_rest_is_untouched(db) -> None:  # type: ignore[no-untyped-def]
    plain = _location(db, "plain")
    bad = _location(db, "bad", adjacency_factor=-2, lighting={"lamp_height_cm": 50, "canopy_distance_cm": 90})
    good = _location(db, "good", adjacency_factor=2.0, lighting={"lamp_height_cm": 180})
    plain_doc = db.collection(col.LOCATIONS).get(plain)

    dry = migration.up(db, dry_run=True)

    assert (dry.scanned, dry.changed) == (2, 0)
    assert dry.details == {"will_clear_adjacency_factor": 1, "will_clear_lighting": 1}
    assert db.collection(col.LOCATIONS).get(bad)["adjacency_factor"] == -2

    report = migration.up(db)

    assert report.changed == 2
    stored_bad = db.collection(col.LOCATIONS).get(bad)
    assert "adjacency_factor" not in stored_bad and "lighting" not in stored_bad
    Location.model_validate(stored_bad)
    stored_good = db.collection(col.LOCATIONS).get(good)
    assert (stored_good["adjacency_factor"], stored_good["lighting"]) == (2.0, {"lamp_height_cm": 180})
    assert db.collection(col.LOCATIONS).get(plain) == plain_doc
    assert "adjacency_factor" not in plain_doc and "lighting" not in plain_doc

    revs = _revs(db)
    again = migration.up(db)

    assert again.changed == 0
    assert _revs(db) == revs
