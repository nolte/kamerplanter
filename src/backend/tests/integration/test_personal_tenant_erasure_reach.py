"""#1788 — an account erasure takes the subject's personal tenant with it.

Before #1788 the account erasure kept the subject's personal tenant: the
``tenants`` rule of ``ErasureEngine.ANONYMIZE_COLLECTIONS`` replaced the owner and
renamed it, and no path ever ran the tenant-erasure inventory (#1769) on it. Its
sites, plants, diary, tasks, tanks … stayed under a tenant nobody could reach
any more — the erased person's own data, kept without purpose.

Only a real server can say whether the rows are gone, so this reads them back.
Three tenants, all seeded from :attr:`TenantErasureEngine.INVENTORY` (never a
list written here), through both account-erasure entries (the platform-admin
``DELETE /admin/platform/users/{key}`` and the daily beat after the self-service
grace):

* the subject's **personal tenant, the subject its only active member** — every
  ``delete`` row gone, the tenant document gone, the retention rows kept under
  the subject's tombstone hash; the tenant-erasure record ``completed`` with
  origin ``account_erasure``; the erasure request ``completed`` and naming it;
* the subject's **personal tenant with a second active member** — kept (the
  spec does not say who takes it over; #1788 holds it and says why), every row
  of it still there, the request naming the reason;
* an **organisation tenant** the subject owns — untouched by the tenant
  inventory (it is the group's, not the subject's).

Locally it needs a database::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_personal_tenant_erasure_reach.py -v
"""

from __future__ import annotations

import asyncio
import inspect
from datetime import timedelta
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from arango import ArangoClient

from app.api.v1.admin.platform import router as admin_router
from app.data_access.arango import collections as col
from app.data_access.arango.erasure_executor import ArangoErasureExecutor
from app.data_access.arango.erasure_repository import ArangoErasureRepository
from app.data_access.arango.membership_repository import ArangoMembershipRepository
from app.data_access.arango.pest_image_repository import ArangoPestImageRepository
from app.data_access.arango.user_repository import ArangoUserRepository
from app.data_access.vectordb.noop_reference_index_store import NoopReferenceIndexStore
from app.data_access.vectordb.pest_prototype_stores import NoopPestPrototypeStore
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
from app.domain.services.privacy_service import PrivacyService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name
from tests.support.privacy_doubles import admin_erasure_route_args, step_up
from tests.support.tenant_erasure_wiring import tenant_erasure_service

TEST_DATABASE = run_database_name("personal_tenant_erasure_reach")
#: NFR-011 §4 wants >= 32 characters. Synthetic, test-only.
SALT = "personal-tenant-salt-not-a-secret-0123456789"
ADMIN = "platform-admin"
COMPANION = "companion-user"
#: A member whose own erasure is pending: its account is deactivated (#1788 review GDPR-01).
DEPARTING = "departing-user"

pytestmark = pytest.mark.usefixtures("arango_db")


def _key(collection: str, tenant: str) -> str:
    return f"{tenant}-{collection}".replace("_", "-")


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


def _user(database, key: str, *, active: bool = True) -> None:
    database.collection(col.USERS).insert(
        {
            "_key": key,
            "email": f"{key}@example.com",
            "display_name": f"Display name of {key}",
            "password_hash": "not-a-hash",
            "email_verified": True,
            "is_active": active,
            "account_type": "human",
            "created_at": "2026-09-01T00:00:00+00:00",
        }
    )


def _seed_tenant(database, tenant: str, *, owner: str, tenant_type: str, members: list[str]) -> dict[str, str]:
    """One row per inventory entry for *tenant*, owned by *owner*; returns ``collection -> _id``.

    The inventory's ``memberships`` row is the owner's; every further *member*
    gets an active membership of its own. The retention rows carry the owner's
    account key and a free-text name, as a harvest the owner recorded would.
    """
    ids: dict[str, str] = {}
    database.collection(col.TENANTS).insert(
        {
            "_key": tenant,
            "name": f"Garden of {owner}",
            "slug": tenant,
            "tenant_type": tenant_type,
            "owner_user_key": owner,
            "is_active": True,
            "created_at": "2026-09-01T00:00:00+00:00",
        }
    )
    for entry in TenantErasureEngine.INVENTORY:
        if not database.has_collection(entry.collection):
            database.create_collection(entry.collection)
        doc: dict[str, Any] = {"_key": _key(entry.collection, tenant), "marker": f"{entry.collection}-{tenant}"}
        if entry.parents:
            parent = entry.parents[0]
            doc[parent.field] = ids[parent.collection].split("/", 1)[1]
            doc.update(parent.where)
        else:
            doc[entry.tenant_field] = tenant
        if entry.collection == col.MEMBERSHIPS:
            doc.update({"user_key": owner, "role": "lead", "is_active": True})
        for rule in _pseudonymizations(entry.collection):
            doc[rule.user_field] = owner
            doc.update(dict.fromkeys(rule.clear_fields, f"Display name of {owner}"))
        for field in _unique_fields(database, entry.collection):
            doc.setdefault(field, f"{doc['_key']}-{field}")
        ids[entry.collection] = database.collection(entry.collection).insert(doc)["_id"]
    for member in members:
        ids[f"membership:{member}"] = database.collection(col.MEMBERSHIPS).insert(
            {"user_key": member, "tenant_key": tenant, "role": "grower", "is_active": True}
        )["_id"]
    return ids


def _read(database, doc_id: str) -> dict[str, Any] | None:
    collection, key = doc_id.split("/", 1)
    return database.collection(collection).get(key)


def _privacy_service(database) -> PrivacyService:
    """The privacy service ``get_privacy_service`` builds, over the test database."""
    password_engine = MagicMock()
    password_engine.verify_password.return_value = True
    kwargs: dict[str, Any] = {
        "export_repo": MagicMock(),
        "consent_repo": MagicMock(),
        "restriction_repo": MagicMock(),
        "erasure_repo": ArangoErasureRepository(database),
        "email_change_repo": MagicMock(),
        "user_repo": ArangoUserRepository(database),
        "refresh_token_repo": MagicMock(),
        "data_export_engine": MagicMock(),
        "erasure_engine": ErasureEngine(),
        "consent_engine": MagicMock(),
        "password_engine": password_engine,
        "token_engine": MagicMock(),
        "email_service": MagicMock(),
        "frontend_url": "http://localhost",
        "membership_repo": ArangoMembershipRepository(database),
        "pest_image_repo": ArangoPestImageRepository(database),
        "pest_prototype_store": NoopPestPrototypeStore(),
        "reference_index_store": NoopReferenceIndexStore(),
        "erasure_executor": ArangoErasureExecutor(database),
        "tenant_service": tenant_erasure_service(database, SALT),
        "tombstone_salt": SALT,
    }
    # The same module ran red against the code before #1788, which had no
    # tenant service to hand in; the assertions, not a TypeError, said so.
    accepted = inspect.signature(PrivacyService).parameters
    return PrivacyService(**{name: value for name, value in kwargs.items() if name in accepted})


def _admin_delete(database, subject: str) -> None:
    admin_router.delete_user(
        subject,
        **admin_erasure_route_args(_privacy_service(database), admin_key=ADMIN, target_email=f"{subject}@example.com"),
    )


def _scheduled_erasure(database, subject: str) -> None:
    request = _privacy_service(database).request_erasure(subject, **step_up(f"{subject}@example.com", "confirm"))
    assert request.hard_delete_scheduled_at is not None
    beat_clock = request.hard_delete_scheduled_at + timedelta(days=1)
    asyncio.run(_privacy_service(database).execute_scheduled_erasures(beat_clock))


ENTRY_POINTS = {"admin": _admin_delete, "scheduled": _scheduled_erasure}


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
    """Per entry point: one subject with a sole-member personal tenant, a shared one and an organisation."""
    for key in (ADMIN, COMPANION):
        _user(database, key)
    _user(database, DEPARTING, active=False)
    runs: dict[str, SimpleNamespace] = {}
    for name, erase in ENTRY_POINTS.items():
        subject = f"subject-{name}"
        _user(database, subject)
        own = _seed_tenant(database, f"p-{name}", owner=subject, tenant_type="personal", members=[])
        shared = _seed_tenant(database, f"s-{name}", owner=subject, tenant_type="personal", members=[COMPANION])
        organisation = _seed_tenant(database, f"o-{name}", owner=subject, tenant_type="organization", members=[])
        leaving = _seed_tenant(database, f"d-{name}", owner=subject, tenant_type="personal", members=[DEPARTING])
        before = {
            "shared": {doc_id: _read(database, doc_id) for doc_id in shared.values()},
            "organisation": {doc_id: _read(database, doc_id) for doc_id in organisation.values()},
        }
        erase(database, subject)
        runs[name] = SimpleNamespace(
            subject=subject, own=own, shared=shared, organisation=organisation, leaving=leaving, before=before
        )
    return runs


def _entries(action: str) -> list[str]:
    return [entry.collection for entry in TenantErasureEngine.INVENTORY if entry.action == action]


def _stamped(database, tenant: str) -> dict[str, int]:
    """Rows carrying *tenant* in ``tenant_key`` anywhere, per collection."""
    kept = set(_entries("pseudonymize")) | set(_entries("retain"))
    found: dict[str, int] = {}
    for info in database.collections():
        name = info["name"]
        if name.startswith("_") or name in kept:
            continue
        count = next(
            iter(
                database.aql.execute(
                    "FOR d IN @@c FILTER d.tenant_key == @t COLLECT WITH COUNT INTO n RETURN n",
                    bind_vars={"@c": name, "t": tenant},
                )
            )
        )
        if count:
            found[name] = count
    return found


def _request(database, subject: str) -> dict[str, Any]:
    tombstone = ErasureEngine.compute_tombstone_hash(subject, SALT)
    (doc,) = list(
        database.aql.execute(
            "FOR r IN @@c FILTER r.user_key == @u RETURN r",
            bind_vars={"@c": col.ERASURE_REQUESTS, "u": tombstone},
        )
    )
    return doc


@pytest.mark.parametrize("entry_point", list(ENTRY_POINTS))
def test_no_row_of_the_sole_member_personal_tenant_survives(database, erased, entry_point):
    run = erased[entry_point]
    tenant = f"p-{entry_point}"
    survivors = [run.own[c] for c in _entries("delete") if _read(database, run.own[c]) is not None]
    assert survivors == []
    assert _read(database, f"{col.TENANTS}/{tenant}") is None
    assert _stamped(database, tenant) == {}


@pytest.mark.parametrize("entry_point", list(ENTRY_POINTS))
def test_its_retention_rows_stay_under_the_subjects_tombstone(database, erased, entry_point):
    run = erased[entry_point]
    tombstone = ErasureEngine.compute_tombstone_hash(run.subject, SALT)
    for collection in _entries("pseudonymize"):
        row = _read(database, run.own[collection])
        assert row is not None, collection
        for rule in _pseudonymizations(collection):
            assert row[rule.user_field] == tombstone, collection
            assert all(row[name] == "" for name in rule.clear_fields), collection


@pytest.mark.parametrize("entry_point", list(ENTRY_POINTS))
def test_the_tenant_erasure_record_and_the_erasure_request_prove_it(database, erased, entry_point):
    run = erased[entry_point]
    tenant = f"p-{entry_point}"
    record = database.collection("tenant_erasure_records").get(TenantErasureEngine.record_key(tenant))
    assert record is not None
    assert (record["status"], record["origin"], record["unreached"]) == ("completed", "account_erasure", [])
    assert record["step_up"] == "account_erasure_no_interactive_step_up"
    assert record["requested_by_subject"] == ErasureEngine.log_subject(run.subject, SALT)
    assert record["slug_digest"] and run.subject not in str(record.values())

    request = _request(database, run.subject)
    assert request["status"] == "completed"
    outcomes = {item["tenant_key"]: item for item in request["personal_tenants"]}
    assert outcomes[tenant]["outcome"] == "erased"
    assert outcomes[tenant]["tenant_erasure_record_key"] == TenantErasureEngine.record_key(tenant)
    assert outcomes[f"s-{entry_point}"]["outcome"] == "retained_other_members"
    assert outcomes[f"s-{entry_point}"]["reason"]
    assert f"o-{entry_point}" not in outcomes


@pytest.mark.parametrize("entry_point", list(ENTRY_POINTS))
def test_a_personal_tenant_with_another_member_is_kept_whole(database, erased, entry_point):
    run = erased[entry_point]
    tenant = f"s-{entry_point}"
    gone = [doc_id for doc_id in run.before["shared"] if _read(database, doc_id) is None]
    # The account plan removes the subject's own membership (and its edges); the
    # tenant's domain rows, the companion's membership and the tenant stay.
    assert gone == [run.shared[col.MEMBERSHIPS]]
    assert _read(database, run.shared[f"membership:{COMPANION}"])["is_active"] is True
    kept = _read(database, f"{col.TENANTS}/{tenant}")
    assert kept is not None and kept["owner_user_key"] != run.subject
    assert database.collection("tenant_erasure_records").get(TenantErasureEngine.record_key(tenant)) is None


@pytest.mark.parametrize("entry_point", list(ENTRY_POINTS))
def test_an_organisation_the_subject_owns_is_not_run_through_the_tenant_inventory(database, erased, entry_point):
    run = erased[entry_point]
    tenant = f"o-{entry_point}"
    assert _read(database, f"{col.TENANTS}/{tenant}") is not None
    assert database.collection("tenant_erasure_records").get(TenantErasureEngine.record_key(tenant)) is None
    domain_rows = [run.organisation[c] for c in _entries("delete") if c not in (col.MEMBERSHIPS,) and c != col.TENANTS]
    assert [doc_id for doc_id in domain_rows if _read(database, doc_id) is None] == []


@pytest.mark.parametrize("entry_point", list(ENTRY_POINTS))
def test_a_member_whose_own_account_is_closing_does_not_keep_the_tenant(database, erased, entry_point):
    """#1788 review GDPR-01 — a deactivated account is leaving; counting it would orphan the tenant for good."""
    run = erased[entry_point]
    tenant = f"d-{entry_point}"
    assert _read(database, f"{col.TENANTS}/{tenant}") is None
    assert [c for c in _entries("delete") if _read(database, run.leaving[c]) is not None] == []
    outcomes = {item["tenant_key"]: item["outcome"] for item in _request(database, run.subject)["personal_tenants"]}
    assert outcomes[tenant] == "erased"
