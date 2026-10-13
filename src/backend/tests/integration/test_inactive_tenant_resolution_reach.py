"""#2105 / REQ-024 AK-56 — a deactivated tenant resolves for nobody, on any surface that names it.

``PATCH /admin/platform/tenants/{key}`` with ``is_active=false`` (step-up protected, #2009)
used to remove the tenant only from ``GET /tenants`` (``list_my_tenants``). The resolver
every tenant-scoped request passes — :func:`app.common.auth._membership_for_slug` — read
``membership.is_active`` but never ``tenant.is_active``, so every member who knew the slug
kept reading and writing through the ``/t/{slug}/`` path and the ``X-Active-Tenant`` header.
The header-less personal fallback did not read it either.

Driven end to end against a **real** ArangoDB: the tenant is deactivated through the real
platform-admin route with the admin's real step-up, then the member's requests go through
the real routers (``/tenants/{slug}`` for the path surface, ``/botanical-families`` for the
header surface and the personal fallback) and the real MCP transport with a real API key
and the real :class:`McpAuthenticator`. Every assertion has its positive control — the
same request answered before the deactivation and again after the reactivation — so a
refusal observed here is the deactivation taking effect, not a request that never worked.

Runs in CI against the service container; locally it needs a database of its own
(``docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12``).
"""

from __future__ import annotations

import hashlib
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from arango import ArangoClient
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.admin.platform import router as admin_mod
from app.api.v1.botanical_families.router import router as families_router
from app.api.v1.mcp import deps as mcp_deps
from app.api.v1.mcp.router import router as mcp_router
from app.api.v1.tenants.router import router as tenants_router
from app.common.auth import get_current_user, require_platform_admin
from app.common.dependencies import get_family_repo, get_mcp_authenticator, get_tenant_service, get_user_service
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError
from app.config.settings import settings
from app.data_access.arango import collections as col
from app.data_access.arango.api_key_repository import ArangoApiKeyRepository
from app.data_access.arango.botanical_family_repository import ArangoBotanicalFamilyRepository
from app.data_access.arango.membership_repository import ArangoMembershipRepository
from app.data_access.arango.tenant_repository import ArangoTenantRepository
from app.data_access.arango.user_repository import ArangoUserRepository
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.models.auth import ApiKey
from app.domain.models.membership import Membership
from app.domain.models.user import User
from app.domain.services.tenant_service import TenantService
from app.mcp_server.audit import MCPAuditLogger
from app.mcp_server.auth import McpAuthenticator
from app.mcp_server.dispatcher import ToolDispatcher
from app.mcp_server.idempotency import IdempotencyStore
from app.mcp_server.registry import load_tools
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("inactive_tenant_resolution")
ORG = "t-club"
ORG_SLUG = "green-club"
PERSONAL = "t-personal"
PERSONAL_SLUG = "member-garden"
FAMILY = "fam-solanaceae"
MEMBER_KEY = "u-member-2105"
# Assembled at runtime: a literal shaped like a credential trips the secret scanner (#1838).
PASSWORD = " ".join(["correct", "horse", "battery", "staple"])
RAW_API_KEY = "kp_" + "-".join(["inactive", "tenant", "reach", "2105"])
ADMIN = User.model_validate(
    {
        "_key": "admin-2105",
        "email": "admin-2105@example.com",
        "display_name": "Admin",
        "password_hash": PasswordEngine().hash_password(PASSWORD),
    }
)
MEMBER = User.model_validate({"_key": MEMBER_KEY, "email": "member-2105@example.com", "display_name": "Member"})

pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    from app.data_access.arango.collections import ensure_collections

    ensure_collections(db)
    yield db
    system.delete_database(TEST_DATABASE)


def _tenant_doc(key: str, slug: str, tenant_type: str) -> dict[str, Any]:
    return {
        "_key": key,
        "name": slug.replace("-", " ").title(),
        "slug": slug,
        "tenant_type": tenant_type,
        "owner_user_key": MEMBER_KEY,
        "is_active": True,
        "is_platform": False,
        "max_members": 50,
        "settings": {},
    }


@pytest.fixture
def db(database):
    for name in (
        col.TENANTS,
        col.USERS,
        col.MEMBERSHIPS,
        col.HAS_MEMBERSHIP,
        col.MEMBERSHIP_IN,
        col.API_KEYS,
        col.BOTANICAL_FAMILIES,
        col.SPECIES,
    ):
        database.collection(name).truncate()
    database.collection(col.USERS).insert(
        {"_key": MEMBER_KEY, "email": "member-2105@example.com", "display_name": "Member", "is_active": True}
    )
    database.collection(col.TENANTS).insert(_tenant_doc(ORG, ORG_SLUG, "organization"))
    database.collection(col.TENANTS).insert(_tenant_doc(PERSONAL, PERSONAL_SLUG, "personal"))
    memberships = ArangoMembershipRepository(database)
    for tenant_key in (ORG, PERSONAL):
        memberships.create(Membership(user_key=MEMBER_KEY, tenant_key=tenant_key, role=TenantRole.LEAD, is_active=True))
    # One own species per tenant, so the per-family count tells which tenant a request resolved to.
    database.collection(col.BOTANICAL_FAMILIES).insert({"_key": FAMILY, "name": "Solanaceae"})
    for tenant_key in (ORG, PERSONAL):
        database.collection(col.SPECIES).insert(
            {
                "_key": f"sp-{tenant_key}",
                "scientific_name": f"Own {tenant_key}",
                "family_key": FAMILY,
                "tenant_key": tenant_key,
            }
        )
    ArangoApiKeyRepository(database).create(
        ApiKey(
            user_key=MEMBER_KEY,
            label="mcp",
            key_hash=hashlib.sha256(RAW_API_KEY.encode()).hexdigest(),
            key_prefix=RAW_API_KEY[:8],
        )
    )
    return database


class _NullAuditRepo:
    def record(self, entry: object) -> str:
        return "audit"


class _NullIdempotencyRepo:
    def get(self, *args: object) -> None:
        return None

    def store(self, record: object, *, ttl_hours: int = 24) -> object:
        return record


def _client(db, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(settings, "mcp_server_enabled", True)
    service = TenantService(
        tenant_repo=ArangoTenantRepository(db),
        membership_repo=ArangoMembershipRepository(db),
        invitation_repo=MagicMock(),
        assignment_repo=MagicMock(),
        tenant_engine=TenantEngine(),
        membership_engine=MembershipEngine(),
        invitation_engine=InvitationEngine(),
    )
    users = MagicMock()
    users.get_user.return_value = ADMIN
    # The catalogue tool reads through a species service; the tenant binding under test happens before it.
    species_service = SimpleNamespace(list_species=lambda offset, limit, tenant_key=None: ([], 0))
    dispatcher = ToolDispatcher(
        load_tools(),
        MCPAuditLogger(_NullAuditRepo()),
        IdempotencyStore(_NullIdempotencyRepo()),
        services={"species_service": species_service},
    )

    app = FastAPI()
    app.include_router(admin_mod.router, prefix="/api/v1")
    app.include_router(tenants_router, prefix="/api/v1")
    app.include_router(families_router, prefix="/api/v1")
    app.include_router(mcp_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[require_platform_admin] = lambda: ADMIN
    app.dependency_overrides[get_current_user] = lambda: MEMBER
    app.dependency_overrides[get_user_service] = lambda: users
    app.dependency_overrides[get_tenant_service] = lambda: service
    app.dependency_overrides[get_family_repo] = lambda: ArangoBotanicalFamilyRepository(db)
    # The real authenticator over the real key, user and membership collections.
    app.dependency_overrides[get_mcp_authenticator] = lambda: McpAuthenticator(
        ArangoApiKeyRepository(db), ArangoUserRepository(db), service
    )
    app.dependency_overrides[mcp_deps.get_dispatcher] = lambda: dispatcher
    return TestClient(app, raise_server_exceptions=False)


def _set_active(client: TestClient, tenant_key: str, *, active: bool) -> None:
    response = client.patch(
        f"/api/v1/admin/platform/tenants/{tenant_key}", json={"is_active": active, "current_password": PASSWORD}
    )
    assert response.status_code == 200, response.text
    assert response.json()["is_active"] is active


def _refusal(response: Any) -> tuple[int, dict[str, Any]]:
    """Everything a client sees of a refusal except what differs per request (id, time, echoed path)."""
    body = dict(response.json())
    for per_request in ("error_id", "timestamp", "path"):
        body.pop(per_request, None)
    return response.status_code, body


def _own_species_count(client: TestClient, headers: dict[str, str] | None = None) -> Any:
    return client.get(f"/api/v1/botanical-families/{FAMILY}", headers=headers or {})


def test_the_path_surface_refuses_a_deactivated_tenant_like_an_unknown_one(db, monkeypatch):
    client = _client(db, monkeypatch)
    assert client.get(f"/api/v1/tenants/{ORG_SLUG}").status_code == 200
    unknown = _refusal(client.get("/api/v1/tenants/no-such-club"))
    assert unknown[0] == 403

    _set_active(client, ORG, active=False)

    for path in (f"/api/v1/tenants/{ORG_SLUG}", f"/api/v1/tenants/{ORG_SLUG}/members"):
        assert _refusal(client.get(path)) == unknown, path

    # Reactivation restores access — the refusal was the flag, not a broken membership.
    _set_active(client, ORG, active=True)
    assert client.get(f"/api/v1/tenants/{ORG_SLUG}").status_code == 200


def test_the_header_surface_refuses_a_deactivated_tenant_like_an_unknown_one(db, monkeypatch):
    client = _client(db, monkeypatch)
    acting = {"X-Active-Tenant": ORG_SLUG}
    before = _own_species_count(client, acting)
    assert before.status_code == 200, before.text
    assert before.json()["species_count"] == 1
    unknown = _refusal(_own_species_count(client, {"X-Active-Tenant": "no-such-club"}))
    assert unknown[0] == 403

    _set_active(client, ORG, active=False)

    assert _refusal(_own_species_count(client, acting)) == unknown

    _set_active(client, ORG, active=True)
    assert _own_species_count(client, acting).json()["species_count"] == 1


def test_the_personal_fallback_narrows_to_global_when_the_personal_tenant_is_deactivated(db, monkeypatch):
    client = _client(db, monkeypatch)
    assert _own_species_count(client).json()["species_count"] == 1

    _set_active(client, PERSONAL, active=False)

    # Fail-open-to-narrow, never an error: the global catalogue without the tenant's own rows.
    after = _own_species_count(client)
    assert after.status_code == 200, after.text
    assert after.json()["species_count"] == 0

    _set_active(client, PERSONAL, active=True)
    assert _own_species_count(client).json()["species_count"] == 1


def _mcp(client: TestClient, tool: str, arguments: dict[str, Any]) -> Any:
    return client.post(f"/api/v1/mcp/tools/{tool}", json=arguments, headers={"X-API-Key": RAW_API_KEY})


def test_mcp_drops_a_deactivated_tenant_and_reports_it_not_found(db, monkeypatch):
    client = _client(db, monkeypatch)
    listed = _mcp(client, "list_tenants", {})
    assert listed.status_code == 200, listed.text
    assert {item["slug"] for item in listed.json()["data"]["items"]} == {ORG_SLUG, PERSONAL_SLUG}
    assert _mcp(client, "list_species", {"tenant": ORG_SLUG}).status_code == 200
    unknown = _refusal(_mcp(client, "list_species", {"tenant": "no-such-club"}))
    assert unknown[0] == 404

    _set_active(client, ORG, active=False)

    listed = _mcp(client, "list_tenants", {})
    assert {item["slug"] for item in listed.json()["data"]["items"]} == {PERSONAL_SLUG}
    refused = _refusal(_mcp(client, "list_species", {"tenant": ORG_SLUG}))
    assert refused[0] == unknown[0]
    assert refused[1]["error_code"] == unknown[1]["error_code"]

    _set_active(client, ORG, active=True)
    assert _mcp(client, "list_species", {"tenant": ORG_SLUG}).status_code == 200


def test_the_platform_admin_still_reaches_a_deactivated_tenant_to_administer_it(db, monkeypatch):
    client = _client(db, monkeypatch)
    _set_active(client, ORG, active=False)

    listing = client.get("/api/v1/admin/platform/tenants")
    assert listing.status_code == 200, listing.text
    assert {t["key"]: t["is_active"] for t in listing.json()}[ORG] is False
    members = client.get(f"/api/v1/admin/platform/tenants/{ORG}/members")
    assert members.status_code == 200, members.text
    assert [m["user_key"] for m in members.json()] == [MEMBER_KEY]
