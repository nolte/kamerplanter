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

The seeded shape is what production writes (#1662 SCR-002): a user-reference
field gets the owner's key only where a production write path is measured to
store one there. Since #1669 the three retained categories carry a server-set
account key (``harvested_by_key`` / ``inspected_by_key`` / ``applied_by_key``)
beside their free-text name, and the walk keys on that. Rows written before
#1669 carry ``null`` in the key field (v0056) and only a name — they are seeded
too, in the subject's own tenant, and must **not** be delivered, even when the
name is the subject's key: guessing an owner from free text is the backfill
#1669 forbids, and the bundle states the gap instead.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.personal_data_repository import ArangoPersonalDataRepository
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.erasure_engine import ErasureEngine
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("privacy_export")

SUBJECT = "subject-user"
OTHER = "other-user"
#: What production really stores in a free-text attribution field
#: (``harvester``, ``inspector``, ``applied_by``): a name, not a key. The
#: OpenAPI example for ``inspector`` is literally ``"Maren"``.
FREE_TEXT_ATTRIBUTION = "Maren"
#: The free-text display field beside each #1669 key field. Read off the Art. 17
#: rules rather than written down twice: the rule that pseudonymises the key is
#: the one that clears the name, so the two cannot drift apart here.
_DISPLAY_TEXT_FIELD: dict[str, str] = {
    rule.collection: rule.clear_fields[0] for rule in ErasureEngine.ANONYMIZE_COLLECTIONS if rule.clear_fields
}
#: The subject's tenants, and one they are not a member of.
TENANTS = ("t-a", "t-b")
FOREIGN_TENANT = "t-foreign"

_APP = Path(__file__).resolve().parents[2] / "app"

pytestmark = pytest.mark.usefixtures("arango_db")


def _marker(collection: str, owner: str) -> str:
    """A value unique per (collection, owner) so a mix-up is visible, not silent."""
    return f"marker-{collection}-{owner}"


def _document(source, owner: str, *, tenant: str = TENANTS[0]) -> dict:
    """A document of *source* owned by *owner*, carrying a recognisable marker.

    Every declared field is filled: a ``KEEP`` over a field the document lacks
    yields ``null``, which the caller cannot distinguish from a field the user
    genuinely left empty.

    **The user-reference field gets what production writes there** (#1662
    SCR-002). The first version of this fixture set ``doc[filter_field] =
    owner`` for every source, i.e. ``harvester = "subject-user"`` — a shape no
    production writer produces, since ``harvester`` is free text typed by the
    user. The walk was green here and empty in every real database. Now:

    * a source whose filter field is measured to carry a user key (see
      :func:`_assert_filter_field_is_written_as_a_user_key`) gets the owner's key;
    * a source with a declared ``disclosure_gap`` gets the free text production
      stores, so the seeded row is exactly as unattributable as a real one;
    * a source with an ``attribution_gap`` (#1669) additionally gets the free-text
      display name every real row carries beside the key.
    """
    doc = {field: _marker(source.collection, owner) for field in source.fields}
    if source.filter_field and source.filter_field != "_key":
        doc[source.filter_field] = FREE_TEXT_ATTRIBUTION if source.disclosure_gap else owner
    if source.attribution_gap:
        doc[_DISPLAY_TEXT_FIELD[source.collection]] = FREE_TEXT_ATTRIBUTION
    if source.tenant_scoped:
        doc["tenant_key"] = tenant
    return doc


def _legacy_documents(source, *, tenant: str = TENANTS[0]) -> list[dict]:
    """Rows of *source* written before #1669, in the subject's own tenant.

    Three shapes, all carrying a marker in a declared field so a walk that
    matched them would deliver it:

    * the free text names a stranger, the key is the explicit ``null`` v0056 stamps;
    * the free text is **literally the subject's key** — the row the forbidden
      backfill would have attributed — key ``null``;
    * the attribute is absent altogether (a row v0056 has not reached yet).
    """
    display = _DISPLAY_TEXT_FIELD[source.collection]
    base = {field: _marker("legacy", SUBJECT) for field in source.fields}
    base["tenant_key"] = tenant
    stamped_stranger = {**base, display: FREE_TEXT_ATTRIBUTION, source.filter_field: None}
    stamped_named = {**base, display: SUBJECT, source.filter_field: None}
    unstamped = {**base, display: SUBJECT}
    return [stamped_stranger, stamped_named, unstamped]


def _user_key_writers(field: str) -> list[str]:
    """Production sites that assign *field* from something that is a user key.

    Read off the AST of ``app/``: a keyword argument or attribute assignment
    named *field* whose value is a bare name or attribute ending in ``user_key``
    / ``account_key`` / ``.key``. Deliberately narrow — ``args.inspector.strip()
    or f"mcp:{ctx.principal.account_key}"`` mentions ``account_key`` and is
    **not** a user key (it is a prefixed string that never equals one), and a
    scan that accepted it would certify exactly the defect this guard exists for.
    """

    def _is_user_key_expr(node: ast.AST) -> bool:
        if isinstance(node, ast.Name):
            return node.id.endswith(("user_key", "account_key"))
        if isinstance(node, ast.Attribute):
            return node.attr in {"user_key", "account_key", "key"} or node.attr.endswith("user_key")
        return False

    hits: list[str] = []
    for path in _APP.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for kw in node.keywords:
                    if kw.arg == field and _is_user_key_expr(kw.value):
                        hits.append(f"{path.relative_to(_APP.parent)}:{kw.lineno}")
            elif isinstance(node, ast.Assign) and _is_user_key_expr(node.value):
                for target in node.targets:
                    if isinstance(target, ast.Attribute) and target.attr == field:
                        hits.append(f"{path.relative_to(_APP.parent)}:{node.lineno}")
    return hits


def _assert_filter_field_is_written_as_a_user_key(source) -> None:
    """Refuse to seed a user key into a field production never writes one into.

    The mirror of :func:`_assert_edge_can_connect_the_user` for filter sources.
    A fixture that puts ``owner`` into ``harvester`` invents a document no
    writer produces; the walk then finds it here and nothing in a real database,
    and the test certifies an Art. 15 category that is in fact never disclosed.
    A source that declares a ``disclosure_gap`` is exempt — it is seeded with the
    free text production stores and asserted *not* to be disclosed.
    """
    if not source.filter_field or source.filter_field == "_key" or source.disclosure_gap:
        return
    writers = _user_key_writers(source.filter_field)
    assert writers, (
        f"manifest source '{source.collection}' is keyed on '{source.filter_field}', but no production "
        "write path assigns a user key to that field. Seeding one here would certify a disclosure the "
        "real system cannot make; declare a disclosure_gap on the source or add the writer."
    )


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
        _assert_filter_field_is_written_as_a_user_key(source)
        for owner in (SUBJECT, OTHER):
            inserted = target.insert(_document(source, owner))
            if source.edge_collection:
                _assert_edge_can_connect_the_user(source)
                if not database.has_collection(source.edge_collection):
                    database.create_collection(source.edge_collection, edge=True)
                database.collection(source.edge_collection).insert(
                    {"_from": f"{col.USERS}/{owner}", "_to": inserted["_id"]}
                )
        if source.tenant_scoped and not source.disclosure_gap:
            # A row naming the subject's key in a tenant they do not belong to:
            # the shape a writer elsewhere could produce to plant data into the
            # subject's disclosure (#1662 SCR-001). It must never be delivered.
            # The marker sits in a *declared* field, so it would be delivered
            # if the tenant filter were missing.
            planted = _document(source, SUBJECT, tenant=FOREIGN_TENANT)
            planted[source.fields[0]] = _marker("planted", SUBJECT)
            target.insert(planted)
        if source.attribution_gap:
            # Pre-#1669 rows in the subject's *own* tenant (see
            # ``_legacy_documents``): unattributable by design, never delivered.
            target.insert_many(_legacy_documents(source))

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


DISCLOSED = [source for source in DataExportEngine.USER_DATA_MANIFEST if not source.disclosure_gap]
#: The #1669 sources: disclosed by key, with pre-attribution rows stated as a gap.
ATTRIBUTED = [source for source in DISCLOSED if source.attribution_gap]


@pytest.mark.parametrize("source", DISCLOSED, ids=[source.collection for source in DISCLOSED])
def test_every_declared_source_returns_the_subjects_document(db, source):
    """One case per manifest entry, so a broken source names itself."""
    repo = ArangoPersonalDataRepository(db)

    rows = repo.collect_for_user(source, SUBJECT, TENANTS)

    assert rows, f"source '{source.collection}' returned nothing for a subject that has a document there"
    values = {value for row in rows for value in row.values()}
    assert _marker(source.collection, SUBJECT) in values


@pytest.mark.parametrize("source", DISCLOSED, ids=[source.collection for source in DISCLOSED])
def test_no_declared_source_leaks_another_users_document(db, source):
    """The mirror case: a query matching everything is as wrong as one matching nothing."""
    repo = ArangoPersonalDataRepository(db)

    rows = repo.collect_for_user(source, SUBJECT, TENANTS)

    values = {value for row in rows for value in row.values()}
    assert _marker(source.collection, OTHER) not in values


TENANT_SCOPED = [source for source in DISCLOSED if source.tenant_scoped]


@pytest.mark.parametrize("source", TENANT_SCOPED, ids=[source.collection for source in TENANT_SCOPED])
def test_a_row_planted_in_a_foreign_tenant_is_not_delivered(db, source):
    """#1662 SCR-001, the injection direction.

    The user-reference field is written by whoever edits the document. A row
    that names the subject's key inside a tenant the subject is not a member of
    must not reach their disclosure, however it got there.
    """
    repo = ArangoPersonalDataRepository(db)

    rows = repo.collect_for_user(source, SUBJECT, TENANTS)

    values = {value for row in rows for value in row.values()}
    assert _marker("planted", SUBJECT) not in values
    assert _marker(source.collection, SUBJECT) in values, "precondition: the subject's own row is still delivered"


@pytest.mark.parametrize("source", ATTRIBUTED, ids=[source.collection for source in ATTRIBUTED])
def test_a_legacy_row_is_not_delivered_even_when_its_free_text_names_the_subject(db, source):
    """#1669 — the rows the forbidden backfill would have attributed.

    Three pre-attribution shapes sit in the subject's own tenant (see
    ``_legacy_documents``); one of them carries the subject's key as the typed-in
    name. None reaches the disclosure: the walk keys on the account field and
    nothing reads the free text.
    """
    assert ATTRIBUTED, "guard against a vacuous parametrisation"
    repo = ArangoPersonalDataRepository(db)

    rows = repo.collect_for_user(source, SUBJECT, TENANTS)

    values = {value for row in rows for value in row.values()}
    assert _marker("legacy", SUBJECT) not in values
    assert _marker(source.collection, SUBJECT) in values, "precondition: the subject's keyed row is delivered"


def test_an_undisclosable_source_is_refused_not_answered_with_nothing(db):
    """An empty list from such a source would read as "no data" — the #1645 silence.

    Since #1669 no production source carries a ``disclosure_gap`` any more, so
    the floor is exercised with a constructed one rather than skipped for lack
    of a parameter.
    """
    from app.domain.models.privacy import DataSourceDefinition

    gapped = DataSourceDefinition(
        collection="harvest_batches", filter_field="harvester", label="x", fields=["notes"], disclosure_gap="why"
    )
    repo = ArangoPersonalDataRepository(db)

    with pytest.raises(ValueError, match="cannot be disclosed"):
        repo.collect_for_user(gapped, SUBJECT, TENANTS)


@pytest.mark.parametrize("source", ATTRIBUTED, ids=[source.collection for source in ATTRIBUTED])
def test_the_guard_accepts_the_key_field_because_a_production_writer_assigns_it(source):
    """#1669's acceptance, spelled out: the guard names the writers it found.

    Before #1669 this went red for all three (``harvested_by_key`` etc. had no
    writer). It is green because every create path — REST, MCP, the two
    inspection bridges — assigns the field from the caller's key; remove one
    of those assignments and the source it feeds goes red here again.
    """
    _assert_filter_field_is_written_as_a_user_key(source)
    assert _user_key_writers(source.filter_field), "the guard passed without a writer — it has become vacuous"


def test_the_guard_refuses_a_fixture_that_invents_a_user_key():
    """The SCR-002 guard itself, against the shape that fooled the first fixture.

    Hands the guard ``harvest_batches`` keyed on the free-text ``harvester``,
    ungated — the declaration the first version of #1662 shipped — and expects
    the refusal. Still the right shape after #1669: the key lives in
    ``harvested_by_key``, and ``harvester`` remains a typed-in name that no
    writer fills from an account. Were this to go green, some path would have
    started writing keys into the display field, which is a defect, not a
    reason to key on it.
    """
    from app.domain.models.privacy import DataSourceDefinition

    ungated = DataSourceDefinition(collection="harvest_batches", filter_field="harvester", label="x", fields=["notes"])

    with pytest.raises(AssertionError, match="no production write path assigns a user key"):
        _assert_filter_field_is_written_as_a_user_key(ungated)


def test_the_declared_fields_are_the_fields_delivered(db):
    """``KEEP`` must not widen the disclosure beyond what the manifest declares."""
    source = _profile_source()
    repo = ArangoPersonalDataRepository(db)

    rows = repo.collect_for_user(source, SUBJECT, TENANTS)

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
    from app.data_access.arango.data_export_repository import ArangoDataExportRepository
    from app.data_access.storage.local_fs_adapter import LocalFsStorageAdapter
    from app.domain.engines.consent_engine import ConsentEngine
    from app.domain.engines.erasure_engine import ErasureEngine
    from app.domain.services.privacy_service import PrivacyService

    export_repo = ArangoDataExportRepository(database)
    membership_repo = MagicMock()
    membership_repo.list_by_user.return_value = [MagicMock(tenant_key=t) for t in TENANTS]
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
        membership_repo=membership_repo,
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
    missing = [source.collection for source in DISCLOSED if _marker(source.collection, SUBJECT) not in delivered]
    assert not missing, f"the delivered bundle carries no record for: {missing}"

    # The three retained categories (#1669): the subject's keyed row is in the
    # file (asserted above via ``missing``), the section says that rows written
    # before attribution cannot be, and the legacy rows seeded in the subject's
    # own tenant — one of them naming the subject in free text — are not there.
    sections = {section["collection"]: section for section in bundle["sections"]}
    assert ATTRIBUTED, "guard against a vacuous loop"
    for source in ATTRIBUTED:
        assert sections[source.collection]["disclosed"] is True
        assert sections[source.collection]["not_disclosed_reason"] is None
        assert sections[source.collection]["attribution_gap"] == source.attribution_gap
        assert sections[source.collection]["record_count"] == 1
    assert _marker("legacy", SUBJECT) not in delivered

    # The injection direction, end to end: a row naming the subject in a foreign
    # tenant is in the database and not in the file.
    assert _marker("planted", SUBJECT) not in delivered

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
