"""#1769 — tenant deletion reaches every collection of the declared inventory.

Before #1769 ``TenantService.delete_tenant`` removed storage, the derived indexes,
memberships, invitations, assignments and the tenant document; every other
collection kept the tenant's rows under a ``tenant_key`` that pointed at nothing.
Only a real server can say whether each AQL write reaches the rows, so this reads
them back.

**The seeded collections are derived from the inventory**, never listed here:
every entry of :attr:`TenantErasureEngine.INVENTORY` gets one row of tenant A and
one of tenant B — stamped with ``tenant_key`` when the entry has no parent,
reached **only** through its first parent otherwise (no ``tenant_key`` on the
row, the ``locations``/``slots`` shape of #1397). Retention rows carry a member's
account key and a free-text name. What is asserted, through both HTTP entry
points (``DELETE /t/{slug}`` and ``DELETE /admin/platform/tenants/{key}``):

* every A row of a ``delete`` entry is gone, and every edge touching one;
* every A row of an ``anonymize`` entry survives with the member's key replaced
  by the member's tombstone hash and the free-text name emptied; ``retain`` rows
  survive untouched;
* the tenant document is gone and the persisted record says ``completed``, with
  every ``delete`` entry having matched at least one row (reach, not a status);
* every B row and B edge is byte-for-byte unchanged (``_rev``), and so are the
  global catalogue seeds, including a legacy seed carrying A's key (v0004 stamp);
* a row stamped with the tenant in a collection nobody declared keeps the
  deletion open (``TENANT_ERASURE_INCOMPLETE``) and is named in the record.

Locally it needs a database::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_tenant_erasure_reach.py -v
"""

from __future__ import annotations

import inspect
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from arango import ArangoClient

from app.api.v1.admin.platform import router as admin_router
from app.api.v1.tenants import router as tenant_router
from app.common.exceptions import KamerplanterError
from app.data_access.arango.attachment_repository import ArangoAttachmentRepository
from app.data_access.arango.invitation_repository import ArangoInvitationRepository
from app.data_access.arango.location_assignment_repository import ArangoLocationAssignmentRepository
from app.data_access.arango.membership_repository import ArangoMembershipRepository
from app.data_access.arango.pest_image_repository import ArangoPestImageRepository
from app.data_access.arango.tenant_repository import ArangoTenantRepository
from app.data_access.vectordb.noop_reference_index_store import NoopReferenceIndexStore
from app.data_access.vectordb.pest_prototype_stores import NoopPestPrototypeStore
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
from app.domain.services.tenant_service import TenantService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("tenant_erasure_reach")
#: NFR-011 §4 wants >= 32 characters. Synthetic, test-only.
SALT = "tenant-reach-salt-not-a-secret-0123456789"
MEMBER = "member-u1"
ENTRY_POINTS = {"t-route": "tenant_management", "t-admin": "platform_admin"}
OTHER = "t-other"

pytestmark = pytest.mark.usefixtures("arango_db")


def _key(collection: str, tenant: str) -> str:
    return f"{tenant}-{collection}".replace("_", "-")


def _ensure(database, name: str, *, edge: bool = False) -> None:
    if not database.has_collection(name):
        database.create_collection(name, edge=edge)


def _unique_fields(database, collection: str) -> set[str]:
    return {
        field
        for index in database.collection(collection).indexes()
        if index.get("unique") and index["type"] == "persistent"
        for field in index["fields"]
        if "[" not in field and "." not in field
    }


def _pseudonymizations(collection: str):
    return [r for r in TenantErasureEngine().build_plan("probe").pseudonymizations if r.collection == collection]


def _seed_tenant(database, tenant: str) -> dict[str, str]:
    """One row per inventory entry for *tenant*; returns ``collection -> _id``."""
    ids: dict[str, str] = {}
    database.collection("tenants").insert(
        {
            "_key": tenant,
            "name": f"Garden {tenant}",
            "slug": tenant,
            "tenant_type": "organization",
            "owner_user_key": MEMBER,
            "is_active": True,
        }
    )
    for entry in TenantErasureEngine.INVENTORY:
        _ensure(database, entry.collection)
        doc: dict[str, Any] = {"_key": _key(entry.collection, tenant), "marker": f"{entry.collection}-{tenant}"}
        if entry.parents:
            parent = entry.parents[0]
            doc[parent.field] = ids[parent.collection].split("/", 1)[1]
            doc.update(parent.where)
        else:
            doc["tenant_key"] = tenant
        for rule in _pseudonymizations(entry.collection):
            doc[rule.user_field] = MEMBER
            doc.update(dict.fromkeys(rule.clear_fields, "Display name of the member"))
        # A unique index over a field the row does not carry would see two
        # tenants' ``null`` collide; give every such field a per-row value.
        for field in _unique_fields(database, entry.collection):
            doc.setdefault(field, f"{doc['_key']}-{field}")
        ids[entry.collection] = database.collection(entry.collection).insert(doc)["_id"]

    edges = {
        # membership plumbing, a place hierarchy, a retained record pointing at a
        # deleted plant, and an account-owned edge onto a tenant catalogue row
        "has_membership": ("users/" + MEMBER, ids["memberships"]),
        "membership_in": (ids["memberships"], f"tenants/{tenant}"),
        "contains": (ids["sites"], ids["locations"]),
        "applied_to_plant": (ids["treatment_applications"], ids["plant_instances"]),
        "user_favorites": ("users/" + MEMBER, ids["species"]),
    }
    for name, (source, target) in edges.items():
        _ensure(database, name, edge=True)
        ids[f"edge:{name}"] = database.collection(name).insert(
            {"_key": _key(name, tenant), "_from": source, "_to": target}
        )["_id"]
    return ids


def _seed_globals(database, stamped_tenant: str) -> dict[str, str]:
    _ensure(database, "pests")
    _ensure(database, "species")
    return {
        "global species": database.collection("species").insert({"_key": "global-species", "tenant_key": ""})["_id"],
        # A seed the v0004 backfill stamped with a tenant key — not the tenant's.
        "legacy pest": database.collection("pests").insert({"_key": "legacy-pest", "tenant_key": stamped_tenant})[
            "_id"
        ],
    }


def _read(database, doc_id: str) -> dict[str, Any] | None:
    collection, key = doc_id.split("/", 1)
    return database.collection(collection).get(key)


def _service(database) -> TenantService:
    """The service ``get_tenant_service`` builds, over the test database."""
    from app.data_access.arango.tenant_erasure_executor import ArangoTenantErasureExecutor
    from app.data_access.arango.tenant_erasure_repository import ArangoTenantErasureRepository

    kwargs: dict[str, Any] = {
        "tenant_repo": ArangoTenantRepository(database),
        "membership_repo": ArangoMembershipRepository(database),
        "invitation_repo": ArangoInvitationRepository(database),
        "assignment_repo": ArangoLocationAssignmentRepository(database),
        "tenant_engine": MagicMock(),
        "membership_engine": MagicMock(),
        "invitation_engine": MagicMock(),
        "storage_adapter": None,
        "attachment_repo": ArangoAttachmentRepository(database),
        "reference_index_store": NoopReferenceIndexStore(),
        "pest_image_repo": ArangoPestImageRepository(database),
        "pest_prototype_store": NoopPestPrototypeStore(),
        "tenant_erasure_executor": ArangoTenantErasureExecutor(database),
        "tenant_erasure_repo": ArangoTenantErasureRepository(database),
        "tombstone_salt": SALT,
    }
    accepted = inspect.signature(TenantService).parameters
    return TenantService(**{name: value for name, value in kwargs.items() if name in accepted})


def _delete_through(database, entry_point: str, tenant: str) -> None:
    service = _service(database)
    if entry_point == "tenant_management":
        tenant_router.delete_tenant(ctx=SimpleNamespace(tenant_key=tenant), service=service)
    else:
        admin_router.delete_tenant(tenant, _user=None, tenant_service=service)


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    database = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    from app.data_access.arango.collections import ensure_collections

    ensure_collections(database)
    yield database
    system.delete_database(TEST_DATABASE)


@pytest.fixture(scope="module")
def erased(database):
    seeded = {tenant: _seed_tenant(database, tenant) for tenant in (*ENTRY_POINTS, OTHER)}
    globals_ = _seed_globals(database, stamped_tenant="t-route")
    before = {doc_id: _read(database, doc_id) for doc_id in [*seeded[OTHER].values(), *globals_.values()]}
    for tenant, entry_point in ENTRY_POINTS.items():
        _delete_through(database, entry_point, tenant)
    return SimpleNamespace(seeded=seeded, before=before)


def _entries(action: str) -> list[str]:
    return [entry.collection for entry in TenantErasureEngine.INVENTORY if entry.action == action]


@pytest.mark.parametrize("tenant", list(ENTRY_POINTS))
def test_every_row_of_a_delete_entry_and_its_edges_are_gone(database, erased, tenant):
    ids = erased.seeded[tenant]
    survivors = [ids[c] for c in _entries("delete") if _read(database, ids[c]) is not None]
    assert survivors == []
    edges = [doc_id for name, doc_id in ids.items() if name.startswith("edge:")]
    assert [doc_id for doc_id in edges if _read(database, doc_id) is not None] == []
    assert _read(database, f"tenants/{tenant}") is None


@pytest.mark.parametrize("tenant", list(ENTRY_POINTS))
def test_retention_rows_survive_pseudonymised(database, erased, tenant):
    ids = erased.seeded[tenant]
    tombstone = ErasureEngine.compute_tombstone_hash(MEMBER, SALT)
    for collection in _entries("anonymize"):
        row = _read(database, ids[collection])
        assert row is not None, collection
        for rule in _pseudonymizations(collection):
            assert row[rule.user_field] == tombstone, collection
            assert all(row[name] == "" for name in rule.clear_fields), collection
    for collection in _entries("retain"):
        assert _read(database, ids[collection]) is not None, collection


@pytest.mark.parametrize(("tenant", "origin"), list(ENTRY_POINTS.items()))
def test_the_record_proves_what_was_reached(database, erased, tenant, origin):
    record = database.collection("tenant_erasure_records").get(TenantErasureEngine.record_key(tenant))
    assert record is not None
    assert record["status"] == "completed"
    assert record["origin"] == origin
    assert record["unreached"] == []
    reached = {o["collection"]: o["affected"] for o in record["outcomes"] if o["action"] == "delete"}
    assert [c for c in _entries("delete") if reached.get(c, 0) < 1] == []
    assert "name" not in record and "slug" not in record and "owner_user_key" not in record


def test_the_other_tenant_and_the_global_catalogue_are_untouched(database, erased):
    changed = [doc_id for doc_id, before in erased.before.items() if _read(database, doc_id) != before]
    assert changed == []


def test_an_undeclared_collection_keeps_the_deletion_open(database, erased):
    tenant = "t-undeclared"
    _seed_tenant(database, tenant)
    _ensure(database, "legacy_orphans")
    database.collection("legacy_orphans").insert({"_key": "orphan", "tenant_key": tenant})

    with pytest.raises(KamerplanterError) as raised:
        _delete_through(database, "platform_admin", tenant)

    assert raised.value.error_code == "TENANT_ERASURE_INCOMPLETE"
    record = database.collection("tenant_erasure_records").get(TenantErasureEngine.record_key(tenant))
    assert record["status"] == "partially_completed"
    assert record["unreached"] == ["undeclared:legacy_orphans"]
    assert record["attempt_count"] == 1
    assert record["next_attempt_at"] is not None
