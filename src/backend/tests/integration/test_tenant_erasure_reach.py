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
* every A row of an ``pseudonymize`` entry survives with the member's key replaced
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
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from arango import ArangoClient

from app.api.v1.admin.platform import router as admin_router
from app.api.v1.tenants import router as tenant_router
from app.api.v1.tenants.schemas import TenantDeleteRequest
from app.common.exceptions import ForbiddenError, KamerplanterError
from app.data_access.arango.attachment_repository import ArangoAttachmentRepository
from app.data_access.arango.invitation_repository import ArangoInvitationRepository
from app.data_access.arango.location_assignment_repository import ArangoLocationAssignmentRepository
from app.data_access.arango.membership_repository import ArangoMembershipRepository
from app.data_access.arango.pest_image_repository import ArangoPestImageRepository
from app.data_access.arango.tenant_repository import ArangoTenantRepository
from app.data_access.timescale.null_observation_repository import NullObservationRepository
from app.data_access.vectordb.noop_reference_index_store import NoopReferenceIndexStore
from app.data_access.vectordb.pest_prototype_stores import NoopPestPrototypeStore
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
from app.domain.models.user import User
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
            doc[entry.tenant_field] = tenant
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
        "observation_repo": NullObservationRepository(),
    }
    accepted = inspect.signature(TenantService).parameters
    return TenantService(**{name: value for name, value in kwargs.items() if name in accepted})


#: The requester of every deletion here (#1791): a federated account (no
#: password — the slug echo is its step-up) whose right is proven from a real
#: membership row, the way the service reads it.
#: The requester signs in with a local password, so the step-up is the slug echo plus
#: that password — a step-up these reach tests pass, not the one they test (#1815
#: made a federated requester need a mailed code; the hourly code budget would then
#: bound how many tenants one module may delete). Assembled at runtime (#1838).
REQUESTER_PASSWORD = "-".join(["reach", "requester", "passphrase"])
REQUESTER = User.model_validate(
    {
        "_key": "requester-1",
        "email": "requester@example.org",
        "display_name": "R",
        "password_hash": PasswordEngine().hash_password(REQUESTER_PASSWORD),
    }
)


def _grant(database, tenant: str) -> None:
    """The membership that lets :data:`REQUESTER` delete *tenant*: lead + management, or platform lead."""
    database.collection("memberships").insert(
        {
            "_key": f"grant-{tenant}",
            "user_key": REQUESTER.key,
            "tenant_key": tenant,
            "role": "lead",
            "admin_scopes": [] if tenant == "platform" else ["management"],
            "is_active": True,
        },
        overwrite=True,
    )


def _delete_through(database, entry_point: str, tenant: str) -> None:
    service = _service(database)
    body = TenantDeleteRequest(confirm_slug=tenant, password=REQUESTER_PASSWORD)
    if entry_point == "tenant_management":
        _grant(database, tenant)
        tenant_router.delete_tenant(
            body=body,
            ctx=SimpleNamespace(tenant_key=tenant),
            user=REQUESTER,
            via_api_key=False,
            client_ip="203.0.113.1",
            service=service,
        )
    else:
        _grant(database, "platform")
        admin_router.delete_tenant(
            tenant, body=body, user=REQUESTER, via_api_key=False, client_ip="203.0.113.1", tenant_service=service
        )


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
    for collection in _entries("pseudonymize"):
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


def test_a_foreign_child_of_the_tenants_parent_is_left_alone(database, erased):
    """#1769 review SEC-004 — a row stamped with another tenant is never ours, whatever it points at."""
    tenant = "t-foreign-parent"
    ids = _seed_tenant(database, tenant)
    site_key = ids["sites"].split("/", 1)[1]
    foreign = database.collection("locations").insert({"site_key": site_key, "tenant_key": OTHER})["_id"]

    _delete_through(database, "platform_admin", tenant)

    assert _read(database, ids["locations"]) is None
    assert _read(database, foreign) is not None


def test_a_retry_reaches_a_child_whose_parent_the_first_attempt_deleted(database, erased):
    """#1769 review SEC-001 — the parent keys of an attempt are persisted and fed into the retry."""
    from app.data_access.arango.tenant_erasure_repository import ArangoTenantErasureRepository

    tenant = "t-late-child"
    ids = _seed_tenant(database, tenant)
    site_key = ids["sites"].split("/", 1)[1]
    service = _service(database)
    # First attempt completes; then a location is written under the (now gone)
    # site, as a request racing the commit would, and the record reopened.
    _grant(database, "platform")
    service.delete_tenant(
        tenant,
        requester=REQUESTER,
        authenticated_with_api_key=False,
        confirmation=TenantDeleteRequest(confirm_slug=tenant, password=REQUESTER_PASSWORD).to_confirmation(),
        origin="platform_admin",
        client_ip="203.0.113.1",
    )
    late = database.collection("locations").insert({"site_key": site_key})["_id"]
    records = ArangoTenantErasureRepository(database)
    key = TenantErasureEngine.record_key(tenant)
    assert site_key in records.get(key).parent_keys["sites"]
    records.update_fields(key, {"status": "partially_completed", "next_attempt_at": None})

    result = service.resume_tenant_erasures(datetime.now(UTC))

    assert result["completed"] == 1
    assert _read(database, late) is None


def test_a_granted_species_and_a_system_seed_outlive_the_tenant(database, erased):
    """#1769 code review — rows another tenant depends on, or a system seed v0004 stamped, are not the tenant's."""
    tenant = "t-sharing"
    ids = _seed_tenant(database, tenant)
    shared = database.collection("species").insert({"tenant_key": tenant, "scientific_name": "Sharea granta"})["_id"]
    database.collection("tenant_has_access").insert({"_from": f"tenants/{OTHER}", "_to": shared})
    seed = database.collection("workflow_templates").insert({"tenant_key": tenant, "is_system": True})["_id"]

    _delete_through(database, "platform_admin", tenant)

    assert _read(database, shared) is not None
    assert _read(database, seed) is not None
    assert _read(database, ids["species"]) is None
    assert _read(database, ids["workflow_templates"]) is None
    record = database.collection("tenant_erasure_records").get(TenantErasureEngine.record_key(tenant))
    assert record["status"] == "completed"


def test_a_management_scope_viewer_erases_nothing(database, erased):
    """#1791 — the right is proven from the stored membership: ``management`` without ``lead`` is refused.

    The membership row is the real shape the tenant route reads; the refusal
    comes before any record is written or any row is touched.
    """
    from app.data_access.arango.tenant_erasure_repository import ArangoTenantErasureRepository

    tenant = "t-secretary"
    _seed_tenant(database, tenant)
    database.collection("memberships").insert(
        {"user_key": REQUESTER.key, "tenant_key": tenant, "role": "viewer", "admin_scopes": ["management"]}
    )

    with pytest.raises(ForbiddenError):
        tenant_router.delete_tenant(
            body=TenantDeleteRequest(confirm_slug=tenant, password=REQUESTER_PASSWORD),
            ctx=SimpleNamespace(tenant_key=tenant),
            user=REQUESTER,
            via_api_key=False,
            client_ip="203.0.113.1",
            service=_service(database),
        )

    assert database.collection("tenants").has(tenant)
    assert database.collection("sites").has(_key("sites", tenant))
    assert ArangoTenantErasureRepository(database).get(TenantErasureEngine.record_key(tenant)) is None
