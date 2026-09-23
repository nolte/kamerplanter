"""#1645 Art. 15 — the export walk against a real ArangoDB.

The unit tier can pin that the service asks the repository for every declared
manifest source. It cannot say whether an AQL query written against a
``DataSourceDefinition`` actually returns rows: an edge traversed in the wrong
direction, a ``KEEP`` over a field the document does not carry, or a filter on
``_key`` returns **an empty list**, and an empty list is indistinguishable from
"this data subject has no data here". That is the exact failure mode the Art. 15
scaffold had, so it must be measured against a server.

Every source of ``DataExportEngine.USER_DATA_MANIFEST`` gets one seeded document
belonging to the subject plus one belonging to a second user, so a query that
matched everything fails as loudly as one that matched nothing.

No real personal data: every value here is synthetic and ``.invalid``-domained.

Runs in CI against a service container; locally it needs a database of its own
(a missing one is a failure in CI, a loud skip locally — ``conftest.py``)::

    docker run -d -p 8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_privacy_export_walk.py -v
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.personal_data_repository import ArangoPersonalDataRepository
from app.domain.engines.data_export_engine import DataExportEngine
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME

TEST_DATABASE = "kamerplanter_privacy_export_test"

SUBJECT = "subject-user"
OTHER = "other-user"

pytestmark = pytest.mark.usefixtures("arango_db")


def _marker(collection: str, owner: str) -> str:
    """A value unique per (collection, owner) so a mix-up is visible, not silent."""
    return f"marker-{collection}-{owner}"


def _document(source, owner: str) -> dict:
    """A document of *source* owned by *owner*, carrying a recognisable marker.

    Every declared field is filled: a ``KEEP`` over a field the document lacks
    yields ``null``, which the caller cannot distinguish from a field the user
    genuinely left empty.
    """
    doc = {field: _marker(source.collection, owner) for field in source.fields}
    if source.filter_field and source.filter_field != "_key":
        doc[source.filter_field] = owner
    return doc


@pytest.fixture(scope="module")
def db():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    database = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)

    database.create_collection(col.USERS)
    users = database.collection(col.USERS)
    for owner in (SUBJECT, OTHER):
        doc = {"_key": owner}
        doc.update(_document(_profile_source(), owner))
        users.insert(doc)

    for source in DataExportEngine.USER_DATA_MANIFEST:
        if source.collection == col.USERS:
            continue
        if not database.has_collection(source.collection):
            database.create_collection(source.collection)
        target = database.collection(source.collection)
        for owner in (SUBJECT, OTHER):
            inserted = target.insert(_document(source, owner))
            if source.edge_collection:
                _assert_edge_can_connect_the_user(source)
                if not database.has_collection(source.edge_collection):
                    database.create_collection(source.edge_collection, edge=True)
                database.collection(source.edge_collection).insert(
                    {"_from": f"{col.USERS}/{owner}", "_to": inserted["_id"]}
                )

    yield database
    system.delete_database(TEST_DATABASE)


def _assert_edge_can_connect_the_user(source) -> None:
    """Refuse to seed an edge the real named graph does not allow.

    Without this the fixture would happily insert ``users/x -> memberships/y``
    into ``membership_in``, a shape the graph definition forbids and production
    therefore never writes. The walk would then find the row here and nothing in
    a real database — a green test certifying an Art. 15 category that is in
    fact never disclosed. (Measured: ``membership_in`` runs
    ``memberships -> tenants`` and never touches ``users``.)
    """
    definition = next(
        (d for d in col.GRAPH_EDGE_DEFINITIONS if d["edge_collection"] == source.edge_collection),
        None,
    )
    assert definition is not None, (
        f"manifest source '{source.collection}' declares edge '{source.edge_collection}', "
        "which the named graph does not define"
    )
    assert (
        col.USERS in definition["from_vertex_collections"] and source.collection in definition["to_vertex_collections"]
    ), (
        f"manifest source '{source.collection}' declares edge '{source.edge_collection}', but that edge runs "
        f"{definition['from_vertex_collections']} -> {definition['to_vertex_collections']}: it cannot reach the "
        "user, so the Art. 15 export discloses nothing for this category."
    )


def _profile_source():
    for source in DataExportEngine.USER_DATA_MANIFEST:
        if source.collection == col.USERS:
            return source
    raise AssertionError("the manifest no longer declares the user profile")


@pytest.mark.parametrize(
    "source",
    DataExportEngine.USER_DATA_MANIFEST,
    ids=[source.collection for source in DataExportEngine.USER_DATA_MANIFEST],
)
def test_every_declared_source_returns_the_subjects_document(db, source):
    """One case per manifest entry, so a broken source names itself."""
    repo = ArangoPersonalDataRepository(db)

    rows = repo.collect_for_user(source, SUBJECT)

    assert rows, f"source '{source.collection}' returned nothing for a subject that has a document there"
    values = {value for row in rows for value in row.values()}
    assert _marker(source.collection, SUBJECT) in values


@pytest.mark.parametrize(
    "source",
    DataExportEngine.USER_DATA_MANIFEST,
    ids=[source.collection for source in DataExportEngine.USER_DATA_MANIFEST],
)
def test_no_declared_source_leaks_another_users_document(db, source):
    """The mirror case: a query matching everything is as wrong as one matching nothing."""
    repo = ArangoPersonalDataRepository(db)

    rows = repo.collect_for_user(source, SUBJECT)

    values = {value for row in rows for value in row.values()}
    assert _marker(source.collection, OTHER) not in values


def test_the_declared_fields_are_the_fields_delivered(db):
    """``KEEP`` must not widen the disclosure beyond what the manifest declares."""
    source = _profile_source()
    repo = ArangoPersonalDataRepository(db)

    rows = repo.collect_for_user(source, SUBJECT)

    assert set(rows[0]) <= set(source.fields)
