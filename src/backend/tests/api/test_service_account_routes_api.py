"""#2137 (MT-041) — ``/t/{slug}/service-accounts`` through real HTTP, and the minted key on the production chain.

The routes run the real router, the real ``get_current_tenant`` resolver and the real ``TenantService``
with its **real** step-up verifier (bcrypt, the shared throttle) over repository doubles. The second
half takes the raw key a creation returned and drives it through ``get_current_user`` →
``FullAuthProvider`` → ``AuthService.authenticate_api_key`` — nothing declares the principal — so what
answers there is the key the route wrote:

* it acts in its tenant, and only from inside its allowlist (401 outside);
* it is refused on another tenant (403, its ``tenant_scope``) and on an account-level route such as
  founding a tenant (403, ``require_account_principal``, #1851);
* it cannot mint another key or create a service account (403 — a key never passes a step-up).
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.v1.auth.router import api_keys_router
from app.api.v1.service_accounts.tenant_router import router as service_accounts_router
from app.api.v1.tenants.router import router as tenants_router
from app.common.auth import get_current_tenant, get_current_user
from app.common.dependencies import get_auth_provider, get_auth_service, get_tenant_service
from app.common.enums import AdminScope, TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError
from app.domain.engines.full_auth_provider import FullAuthProvider
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.auth import ApiKey
from app.domain.models.membership import Membership
from app.domain.models.tenant import Tenant
from app.domain.models.tenant_context import TenantContext
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService
from app.domain.services.tenant_service import TenantService

# Assembled at runtime: a credential-shaped literal is a secret-scanner hit (#1838).
PASSWORD = " ".join(["correct", "horse", "battery", "staple"])
PASSWORD_HASH = PasswordEngine().hash_password(PASSWORD)
SECRET = "test-secret-key-for-unit-tests-32chars!"
INSIDE = "192.168.1.20"
OUTSIDE = "203.0.113.7"


class _Users:
    def __init__(self, *users: User) -> None:
        self.rows = {u.key: u for u in users}

    def create(self, user: User) -> User:
        stored = user.model_copy(update={"key": f"sa-{uuid.uuid4().hex[:8]}"})
        self.rows[stored.key] = stored
        return stored

    def get_by_key(self, key: str) -> User | None:
        return self.rows.get(key)

    def get_or_raise(self, key: str) -> User:
        return self.rows[key]

    def delete(self, key: str) -> bool:
        return self.rows.pop(key, None) is not None

    def update_fields(self, key: str, fields: dict[str, Any]) -> User:
        self.rows[key] = self.rows[key].model_copy(update=fields)
        return self.rows[key]


class _Keys:
    def __init__(self) -> None:
        self.rows: list[ApiKey] = []

    def create(self, api_key: ApiKey) -> ApiKey:
        stored = api_key.model_copy(update={"key": f"ak-{len(self.rows) + 1}"})
        self.rows.append(stored)
        return stored

    def get_by_hash(self, key_hash: str) -> ApiKey | None:
        return next((k for k in self.rows if k.key_hash == key_hash and not k.revoked), None)

    def update_last_used(self, key: str) -> None:
        return None

    def list_by_user(self, user_key: str) -> list[ApiKey]:
        return [k for k in self.rows if k.user_key == user_key]

    def revoke(self, key: str) -> bool:
        self.rows = [k.model_copy(update={"revoked": True}) if k.key == key else k for k in self.rows]
        return True


class _World:
    """Two tenants; the lead of ``garden`` holds the given role and scopes there."""

    def __init__(self, *, role: TenantRole = TenantRole.LEAD, scopes: list[AdminScope] | None = None) -> None:
        self.lead = User.model_validate(
            {
                "_key": f"u-lead-{uuid.uuid4().hex[:8]}",
                "email": "lead@example.org",
                "display_name": "Lead",
                "password_hash": PASSWORD_HASH,
            }
        )
        self.users = _Users(self.lead)
        self.keys = _Keys()
        self.tenants = {
            "garden": Tenant(_key="t-garden", name="Garden", slug="garden", owner_user_key="x", max_members=50),
            "other": Tenant(_key="t-other", name="Other", slug="other", owner_user_key="x", max_members=50),
        }
        scopes = [AdminScope.MANAGEMENT, AdminScope.TECHNICAL] if scopes is None else scopes
        self.members: dict[tuple[str, str], Membership] = {
            (self.lead.key or "", "t-garden"): Membership(
                _key="m-lead", user_key=self.lead.key or "", tenant_key="t-garden", role=role, admin_scopes=scopes
            ),
            (self.lead.key or "", "t-other"): Membership(
                _key="m-lead-other", user_key=self.lead.key or "", tenant_key="t-other", role=TenantRole.LEAD
            ),
        }
        memberships = MagicMock()
        memberships.get_by_user_and_tenant.side_effect = lambda user_key, tenant_key: self.members.get(
            (user_key, tenant_key)
        )
        memberships.active_service_account_memberships.side_effect = lambda *, tenant_key: [
            m
            for (user_key, t), m in self.members.items()
            if t == tenant_key and (u := self.users.rows.get(user_key)) is not None and u.account_type == "service"
        ]
        memberships.count_active_members.return_value = 1
        memberships.create.side_effect = self._join
        memberships.delete.side_effect = lambda key: any(
            self.members.pop(k) is not None for k, m in list(self.members.items()) if m.key == key
        )
        memberships.list_by_user.side_effect = lambda user_key: [
            m for (u, _), m in self.members.items() if u == user_key
        ]
        tenant_repo = MagicMock()
        tenant_repo.get_by_slug.side_effect = lambda slug: self.tenants.get(slug)
        tenant_repo.get_by_key.side_effect = lambda key: next((t for t in self.tenants.values() if t.key == key), None)
        self.tenant_service = TenantService(
            tenant_repo=tenant_repo,
            membership_repo=memberships,
            invitation_repo=MagicMock(),
            assignment_repo=MagicMock(),
            tenant_engine=TenantEngine(),
            membership_engine=MembershipEngine(),
            invitation_engine=InvitationEngine(),
            security_audit=MagicMock(),
            task_repo=MagicMock(),
            user_repo=self.users,  # type: ignore[arg-type]
            api_key_repo=self.keys,  # type: ignore[arg-type]
        )
        self.auth = AuthService(
            user_repo=self.users,  # type: ignore[arg-type]
            auth_provider_repo=MagicMock(),
            refresh_token_repo=MagicMock(),
            password_engine=PasswordEngine(),
            token_engine=TokenEngine(SECRET, "HS256"),
            throttle_engine=LoginThrottleEngine(),
            email_service=MagicMock(),
            frontend_url="https://app.test",
            api_key_repo=self.keys,  # type: ignore[arg-type]
            tenant_service=self.tenant_service,
        )

    def _join(self, membership: Membership) -> Membership:
        stored = membership.model_copy(update={"key": f"m-{membership.user_key}"})
        self.members[(membership.user_key, membership.tenant_key)] = stored
        return stored

    def _app(self, *, as_lead: bool) -> FastAPI:
        app = FastAPI()
        app.include_router(service_accounts_router, prefix="/api/v1/t/{tenant_slug}")
        app.include_router(tenants_router, prefix="/api/v1")
        app.include_router(api_keys_router, prefix="/api/v1")
        probe = APIRouter()

        @probe.get("/t/{tenant_slug}/probe")
        def tenant_probe(ctx: TenantContext = Depends(get_current_tenant)) -> dict[str, str]:
            return {"tenant_key": ctx.tenant_key, "role": str(ctx.role)}

        app.include_router(probe, prefix="/api/v1")
        app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
        app.dependency_overrides[get_tenant_service] = lambda: self.tenant_service
        app.dependency_overrides[get_auth_service] = lambda: self.auth
        if as_lead:
            app.dependency_overrides[get_current_user] = lambda: self.users.rows[self.lead.key]
        else:
            app.dependency_overrides[get_auth_provider] = lambda: FullAuthProvider(
                TokenEngine(SECRET, "HS256"),
                self.users,  # type: ignore[arg-type]
                self.auth,
            )
        return app

    def as_lead(self, method: str, path: str, body: dict[str, Any] | None = None, *, bearer: str | None = None) -> Any:
        headers = {"X-Forwarded-For": "198.51.100.7"}
        if bearer:
            headers["Authorization"] = f"Bearer {bearer}"
        client = TestClient(self._app(as_lead=True), raise_server_exceptions=False)
        return client.request(method, path, json=body, headers=headers)

    def as_key(
        self, raw_key: str, method: str, path: str, *, ip: str = INSIDE, body: dict[str, Any] | None = None
    ) -> Any:
        client = TestClient(self._app(as_lead=False), raise_server_exceptions=False)
        return client.request(
            method, path, json=body, headers={"Authorization": f"Bearer {raw_key}", "X-Forwarded-For": ip}
        )

    def create(self, **body: Any) -> Any:
        payload = {"name": "Home Assistant", "ip_allowlist": ["192.168.1.0/24"], "current_password": PASSWORD, **body}
        return self.as_lead("POST", "/api/v1/t/garden/service-accounts", payload)


# ── the route's gates ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("role", "scopes"),
    [(TenantRole.LEAD, [AdminScope.MANAGEMENT]), (TenantRole.GROWER, [AdminScope.TECHNICAL])],
    ids=["lead-without-technical", "technical-without-lead"],
)
def test_the_route_wants_the_lead_role_and_the_technical_scope(role: TenantRole, scopes: list[AdminScope]) -> None:
    world = _World(role=role, scopes=scopes)

    response = world.create()

    assert response.status_code == 403, response.text
    assert world.keys.rows == []


def test_creation_without_the_password_is_refused() -> None:
    world = _World()

    response = world.create(current_password=None)

    assert response.status_code == 401, response.text
    assert world.keys.rows == []


def test_creation_from_an_api_key_request_is_refused_even_with_the_password() -> None:
    world = _World()

    response = world.as_lead(
        "POST",
        "/api/v1/t/garden/service-accounts",
        {"name": "Home Assistant", "current_password": PASSWORD},
        bearer="kp_" + "x" * 24,
    )

    assert response.status_code == 403, response.text
    assert world.keys.rows == []


def test_the_lead_creates_lists_rotates_and_removes() -> None:
    world = _World()

    created = world.create()
    assert created.status_code == 201, created.text
    account_key = created.json()["key"]
    assert created.json()["role"] == "grower"
    assert created.json()["api_key"]["tenant_scope"] == "t-garden"
    assert created.json()["api_key"]["ip_allowlist"] == ["192.168.1.0/24"]

    listed = world.as_lead("GET", "/api/v1/t/garden/service-accounts")
    assert listed.status_code == 200, listed.text
    assert [a["key"] for a in listed.json()] == [account_key]
    assert "raw_key" not in listed.json()[0]["api_keys"][0]

    rotated = world.as_lead(
        "POST",
        f"/api/v1/t/garden/service-accounts/{account_key}/rotate-key",
        {"overlap_minutes": 0, "current_password": PASSWORD},
    )
    assert rotated.status_code == 201, rotated.text
    assert rotated.json()["replaced_key_count"] == 1

    removed = world.as_lead(
        "DELETE", f"/api/v1/t/garden/service-accounts/{account_key}", {"current_password": PASSWORD}
    )
    assert removed.status_code == 200, removed.text
    assert all(k.revoked for k in world.keys.rows)
    assert world.users.rows[account_key].is_active is False
    assert world.as_lead("GET", "/api/v1/t/garden/service-accounts").json() == []


# ── the minted key on the production chain ──────────────────────────────────


def _minted(world: _World) -> str:
    created = world.create()
    assert created.status_code == 201, created.text
    return created.json()["api_key"]["raw_key"]


def test_the_key_acts_in_its_tenant_as_the_role_it_was_given() -> None:
    world = _World()
    raw_key = _minted(world)

    response = world.as_key(raw_key, "GET", "/api/v1/t/garden/probe")

    assert response.status_code == 200, response.text
    assert response.json() == {"tenant_key": "t-garden", "role": "grower"}


def test_the_key_is_refused_from_outside_its_allowlist() -> None:
    world = _World()
    raw_key = _minted(world)

    assert world.as_key(raw_key, "GET", "/api/v1/t/garden/probe", ip=OUTSIDE).status_code == 401


def test_the_key_is_refused_on_another_tenant() -> None:
    world = _World()
    raw_key = _minted(world)

    assert world.as_key(raw_key, "GET", "/api/v1/t/other/probe").status_code == 403


def test_the_key_founds_no_tenant() -> None:
    world = _World()
    raw_key = _minted(world)

    response = world.as_key(raw_key, "POST", "/api/v1/tenants", body={"name": "Machine Club"})

    assert response.status_code == 403, response.text


@pytest.mark.parametrize(
    ("path", "body"),
    [
        ("/api/v1/auth/api-keys", {"label": "another"}),
        ("/api/v1/t/garden/service-accounts", {"name": "Another"}),
    ],
    ids=["api-key", "service-account"],
)
def test_the_key_mints_nothing(path: str, body: dict[str, Any]) -> None:
    world = _World()
    raw_key = _minted(world)

    response = world.as_key(raw_key, "POST", path, body=body)

    assert response.status_code == 403, response.text
    assert len(world.keys.rows) == 1


def test_a_rotated_key_stops_and_its_successor_works() -> None:
    world = _World()
    created = world.create().json()
    old_key = created["api_key"]["raw_key"]

    rotated = world.as_lead(
        "POST",
        f"/api/v1/t/garden/service-accounts/{created['key']}/rotate-key",
        {"current_password": PASSWORD},
    ).json()

    assert world.as_key(old_key, "GET", "/api/v1/t/garden/probe").status_code == 401
    assert world.as_key(rotated["api_key"]["raw_key"], "GET", "/api/v1/t/garden/probe").status_code == 200
    # The successor kept the allowlist: still refused from outside.
    assert world.as_key(rotated["api_key"]["raw_key"], "GET", "/api/v1/t/garden/probe", ip=OUTSIDE).status_code == 401
