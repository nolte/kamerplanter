"""#1535 — deleting a slot leaves no dangling ``has_slot`` edge, measured for real.

The defect was invisible to every double: ``delete_edges`` *was* called, with a
plausible-looking ``from_id=f"{col.LOCATIONS}/%"``, and the AQL it built is valid
and returns an empty cursor. Only a real server answers the question this file
asks — is the edge still there after the slot is gone? — which is why the
repository is driven against one here rather than only against the capturing
double in ``tests/unit/data_access/arango/test_slot_delete_edges_repo.py``.

Needs a real ArangoDB (see ``tests/integration/conftest.py``); a missing database
is a failure in CI and a loud skip locally.

Out of scope on purpose: the ``has_slot`` edges already orphaned by past deletions
stay where they are. Removing them is an irreversible data change with its own
operator sign-off (the group artefact's scope boundary), not a side effect of this
repair.
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.site_repository import ArangoSiteRepository
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME

TEST_DATABASE = "kp_test_slot_edge_cleanup"

pytestmark = pytest.mark.usefixtures("arango_db")

#: Document collections the repository touches, and the edge collections a slot
#: can carry. ``has_slot`` points *at* the slot; the other two start at it.
_DOCUMENT_COLLECTIONS = [col.SITES, col.LOCATIONS, col.SLOTS]
_EDGE_COLLECTIONS = [col.HAS_SLOT, col.ADJACENT_TO, col.FILLED_WITH]


@pytest.fixture
def db():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    database = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    for name in _DOCUMENT_COLLECTIONS:
        database.create_collection(name)
    for name in _EDGE_COLLECTIONS:
        database.create_collection(name, edge=True)
    yield database
    system.delete_database(TEST_DATABASE)


@pytest.fixture
def repo(db):
    return ArangoSiteRepository(db)


def _seed_location_with_slot(db) -> None:
    db.collection(col.LOCATIONS).insert({"_key": "loc-1", "name": "Tent A", "site_key": "site-1"})
    db.collection(col.SLOTS).insert({"_key": "slot-1", "name": "Slot 1", "location_key": "loc-1"})
    db.collection(col.HAS_SLOT).insert(
        {"_from": f"{col.LOCATIONS}/loc-1", "_to": f"{col.SLOTS}/slot-1"},
    )


def test_delete_slot_removes_the_edge_that_points_at_it(db, repo) -> None:
    _seed_location_with_slot(db)
    assert db.collection(col.HAS_SLOT).count() == 1

    assert repo.delete_slot("slot-1") is True

    assert db.collection(col.SLOTS).get("slot-1") is None
    assert db.collection(col.HAS_SLOT).count() == 0


def test_no_has_slot_edge_survives_its_target(db, repo) -> None:
    """The dangling-edge question in the shape a traversal would hit it.

    Asserting the *count* alone would still pass a repair that deleted the wrong
    edge; this one asks the store whether any ``has_slot`` edge now points at a
    document that no longer exists.
    """
    _seed_location_with_slot(db)
    db.collection(col.SLOTS).insert({"_key": "slot-2", "name": "Slot 2", "location_key": "loc-1"})
    db.collection(col.HAS_SLOT).insert({"_from": f"{col.LOCATIONS}/loc-1", "_to": f"{col.SLOTS}/slot-2"})

    repo.delete_slot("slot-1")

    dangling = list(
        db.aql.execute(
            f"FOR e IN {col.HAS_SLOT} FILTER DOCUMENT(e._to) == null RETURN e._to",
        )
    )
    assert dangling == []
    # The sibling slot's edge is untouched — the repair detaches one slot, not the
    # location's whole fan-out.
    surviving = list(db.aql.execute(f"FOR e IN {col.HAS_SLOT} RETURN e._to"))
    assert surviving == [f"{col.SLOTS}/slot-2"]
