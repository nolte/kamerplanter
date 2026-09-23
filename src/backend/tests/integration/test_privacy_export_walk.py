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

import json

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


# ── End-to-end: the bundle a real data subject actually receives ──────
#
# Everything above measures the walk. This measures the *delivery*, because a
# walk that returns rows and a user who receives a file are two different
# claims and #1645 is exactly the gap between them. Nothing here is doubled:
# a real ArangoDB, the real repository, the real engine, the real filesystem
# storage adapter, and the bytes are read back through the same
# `prepare_export_download` gate the HTTP endpoint uses.


def _service_under_test(database, storage_root):
    """A PrivacyService whose export path is entirely real.

    Only the collaborators the export path never touches are doubled, and each
    of those would raise rather than quietly return a plausible value if the
    export started depending on it.
    """
    from unittest.mock import MagicMock

    from app.data_access.arango.data_export_repository import ArangoDataExportRepository
    from app.data_access.storage.local_fs_adapter import LocalFsStorageAdapter
    from app.domain.engines.consent_engine import ConsentEngine
    from app.domain.engines.erasure_engine import ErasureEngine
    from app.domain.services.privacy_service import PrivacyService

    export_repo = ArangoDataExportRepository(database)
    storage = LocalFsStorageAdapter(
        root=str(storage_root),
        public_base_url="https://storage.test",
        signing_secret="x" * 48,
        max_object_size_bytes=64 * 1024 * 1024,
    )
    service = PrivacyService(
        export_repo=export_repo,
        consent_repo=MagicMock(),
        restriction_repo=MagicMock(),
        erasure_repo=MagicMock(),
        email_change_repo=MagicMock(),
        user_repo=MagicMock(),
        refresh_token_repo=MagicMock(),
        data_export_engine=DataExportEngine(),
        erasure_engine=ErasureEngine(),
        consent_engine=ConsentEngine(),
        password_engine=MagicMock(),
        token_engine=MagicMock(),
        email_service=MagicMock(),
        frontend_url="https://app.test",
        storage_adapter=storage,
        personal_data_repo=ArangoPersonalDataRepository(database),
    )
    return service, export_repo


@pytest.mark.asyncio
async def test_the_data_subject_receives_a_bundle_carrying_their_records(db, tmp_path):
    """The acceptance for #1645: content reaching the user, not a status field.

    The assertion deliberately does **not** read `status`. It reads the bytes
    that come back out of `prepare_export_download`, and requires a marker from
    every declared manifest source to be in them — so an export that completed
    with an empty bundle fails here, which is the whole point.
    """
    from app.domain.models.privacy import DataExportRequest

    service, export_repo = _service_under_test(db, tmp_path / "objects")
    created = export_repo.create(DataExportRequest(user_key=SUBJECT, status="pending"))

    await service.process_data_export(created.key)

    # The same gate the HTTP endpoint goes through: ownership, status, expiry,
    # download counter. If it refuses, no bytes exist to assert on.
    export, stream = await service.open_export_bundle(SUBJECT, created.key)
    payload = b"".join([chunk async for chunk in stream]).decode("utf-8")
    bundle = json.loads(payload)

    delivered = {value for section in bundle["sections"] for row in section["records"] for value in row.values()}
    missing = [
        source.collection
        for source in DataExportEngine.USER_DATA_MANIFEST
        if _marker(source.collection, SUBJECT) not in delivered
    ]
    assert not missing, f"the delivered bundle carries no record for: {missing}"

    # Nothing of the other user's, in the file that is handed out.
    leaked = [
        source.collection
        for source in DataExportEngine.USER_DATA_MANIFEST
        if _marker(source.collection, OTHER) in delivered
    ]
    assert not leaked, f"the delivered bundle leaks another user's records for: {leaked}"

    # The file on disk is the file the record points at, and it is not empty.
    stored = (tmp_path / "objects" / export.file_path).read_bytes()
    assert stored.decode("utf-8") == payload
    assert export.file_size_bytes == len(stored) > 0


@pytest.mark.asyncio
async def test_an_expired_export_stops_pointing_at_a_deleted_object(db, tmp_path):
    """NFR-011 R-05 against the real repository's write semantics.

    `ArangoDataExportRepository` is in **merge** mode, so a `file_path` set to
    `None` on a full model never reaches the payload and the record keeps
    pointing at a bundle that has just been deleted. A unit test with a mock
    cannot see that; this reads the stored document back.
    """
    from datetime import UTC, datetime, timedelta

    from app.domain.models.privacy import DataExportRequest

    service, export_repo = _service_under_test(db, tmp_path / "objects")
    created = export_repo.create(DataExportRequest(user_key=SUBJECT, status="pending"))
    built = await service.process_data_export(created.key)
    on_disk = tmp_path / "objects" / built.file_path
    assert on_disk.exists(), "precondition: the run produced a bundle to expire"

    past = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    export_repo.update_fields(created.key, {"expires_at": past})

    await service.expire_data_exports(datetime.now(UTC))

    stored = export_repo.get_or_raise(created.key)
    assert stored.status == "expired"
    assert stored.file_path is None, "the record still points at a bundle that no longer exists"
    assert stored.file_size_bytes is None
    assert not on_disk.exists(), "the Art. 15 disclosure is still in object storage"
