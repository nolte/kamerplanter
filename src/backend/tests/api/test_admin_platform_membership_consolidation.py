"""#1019 — the platform-admin membership operations converge on one service method.

Before this change the *tenant* perspective (``/admin/platform/tenants/{tk}/members``)
and the *user* perspective (``/admin/platform/users/{uk}/memberships``) each
hand-wrote the same add / change-role / remove with their own edge inserts, so a
fix landing in one copy missed the other and neither suite noticed. Both now route
through ``TenantService.admin_add_membership`` / ``admin_change_membership_role`` /
``admin_remove_membership``.

**The equivalence tests are the point.** For each operation, the two perspectives
are driven against isolated in-memory backends and the resulting stored
``Membership`` (and its graph edges) are asserted **identical** — the property the
duplication made unprovable. Real domain models flow through real
``TenantService`` / ``UserService`` over hand-written in-memory repositories, so a
persisted value observed here is a real model, not a ``MagicMock`` that never
became one (the #996 trap).
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from app.api.v1.admin.platform import router as mod
from app.common.auth import require_platform_admin
from app.common.dependencies import get_tenant_service, get_user_service
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler, validation_error_handler
from app.common.exceptions import KamerplanterError, NotFoundError
from app.domain.models.membership import MemberInfo, Membership, UserMembershipInfo
from app.domain.models.tenant import Tenant
from app.domain.models.user import User
from app.domain.services.tenant_service import TenantService
from app.domain.services.user_service import UserService

# ── In-memory repository doubles (real models, real service logic) ────────────


class InMemoryTenantRepo:
    def __init__(self, tenants: dict[str, Tenant]) -> None:
        self._store = tenants

    def get_by_key(self, key: str) -> Tenant | None:
        return self._store.get(key)

    def list_all(self) -> list[Tenant]:
        return sorted(self._store.values(), key=lambda t: t.created_at or "", reverse=True)

    def count(self, *, active_only: bool = False) -> int:
        values = self._store.values()
        return sum(1 for t in values if t.is_active) if active_only else len(list(values))


class InMemoryUserRepo:
    def __init__(self, users: dict[str, User]) -> None:
        self._store = users
        self.deleted: list[str] = []

    def get_by_key(self, key: str) -> User | None:
        return self._store.get(key)

    def get_or_raise(self, key: str) -> User:
        user = self._store.get(key)
        if user is None:
            raise NotFoundError("User", key)
        return user

    def list_all(self) -> list[User]:
        return sorted(self._store.values(), key=lambda u: u.created_at or "", reverse=True)

    def count(self, *, active_only: bool = False) -> int:
        values = self._store.values()
        return sum(1 for u in values if u.is_active) if active_only else len(list(values))

    def delete(self, key: str) -> bool:
        if key in self._store:
            self.deleted.append(key)
            del self._store[key]
            return True
        return False


class InMemoryMembershipRepo:
    """Stores real ``Membership`` models and mirrors the Arango repo's edge work."""

    def __init__(self, tenants: dict[str, Tenant], users: dict[str, User]) -> None:
        self._store: dict[str, Membership] = {}
        self._tenants = tenants
        self._users = users
        self._seq = 0
        # Observable side effects, mirroring ArangoMembershipRepository.
        self.edges: list[tuple[str, str, str]] = []
        self.location_assignments_cleaned: list[str] = []

    def get_by_key(self, key: str) -> Membership | None:
        return self._store.get(key)

    def get_by_user_and_tenant(self, user_key: str, tenant_key: str) -> Membership | None:
        for m in self._store.values():
            if m.user_key == user_key and m.tenant_key == tenant_key:
                return m
        return None

    def create(self, membership: Membership) -> Membership:
        self._seq += 1
        key = f"m-{self._seq}"
        created = membership.model_copy(update={"key": key})
        self._store[key] = created
        self.edges.append(("has_membership", f"users/{created.user_key}", f"memberships/{key}"))
        self.edges.append(("membership_in", f"memberships/{key}", f"tenants/{created.tenant_key}"))
        return created

    def update_fields(self, key: str, fields: dict[str, Any]) -> Membership | None:
        existing = self._store.get(key)
        if existing is None:
            return None
        updated = existing.model_copy(update=fields)
        self._store[key] = updated
        return updated

    def delete(self, key: str) -> bool:
        if key not in self._store:
            return False
        # Mirror ArangoMembershipRepository.delete: drop edges AND the membership's
        # location assignments (the raw-AQL router copy orphaned the latter).
        self.location_assignments_cleaned.append(key)
        self.edges = [e for e in self.edges if f"memberships/{key}" not in (e[1], e[2])]
        del self._store[key]
        return True

    def list_by_tenant(self, tenant_key: str) -> list[MemberInfo]:
        infos = []
        for m in self._store.values():
            if m.tenant_key != tenant_key:
                continue
            user = self._users.get(m.user_key)
            infos.append(
                MemberInfo(
                    key=m.key or "",
                    user_key=m.user_key,
                    display_name=user.display_name if user else "",
                    email=user.email if user else "",
                    role=m.role,
                    admin_scopes=m.admin_scopes,
                    is_active=m.is_active,
                    joined_at=m.joined_at,
                )
            )
        return infos

    def list_by_user_with_tenant(self, user_key: str) -> list[UserMembershipInfo]:
        infos = []
        for m in self._store.values():
            if m.user_key != user_key:
                continue
            tenant = self._tenants.get(m.tenant_key)
            if tenant is None:
                continue
            infos.append(
                UserMembershipInfo(
                    membership_key=m.key or "",
                    tenant_key=m.tenant_key,
                    tenant_name=tenant.name,
                    tenant_slug=tenant.slug,
                    role=m.role,
                    is_active=m.is_active,
                    joined_at=m.joined_at,
                )
            )
        return infos

    def count(self) -> int:
        return len(self._store)

    def delete_all_for_user(self, user_key: str) -> int:
        keys = [k for k, m in self._store.items() if m.user_key == user_key]
        for k in keys:
            self.delete(k)
        return len(keys)


def _tenant(key: str, name: str, slug: str, *, is_active: bool = True, is_platform: bool = False) -> Tenant:
    return Tenant(
        _key=key,
        name=name,
        slug=slug,
        tenant_type="organization",
        owner_user_key="u-owner",
        is_active=is_active,
        is_platform=is_platform,
        max_members=50,
        created_at=f"2026-01-0{key[-1]}T00:00:00+00:00",
    )


def _user(key: str, name: str, email: str, *, is_active: bool = True) -> User:
    return User(
        _key=key,
        email=email,
        display_name=name,
        password_hash="hash",
        email_verified=True,
        is_active=is_active,
        account_type="user",
        created_at=f"2026-02-0{key[-1]}T00:00:00+00:00",
    )


class Backend:
    """A self-contained in-memory backend + wired services + mounted router."""

    def __init__(self) -> None:
        self.tenants: dict[str, Tenant] = {
            "t-1": _tenant("t-1", "Community Garden", "community-garden"),
            "t-2": _tenant("t-2", "Rooftop Farm", "rooftop-farm"),
        }
        self.users: dict[str, User] = {
            "u-1": _user("u-1", "Alice Grower", "alice@example.com"),
            "u-2": _user("u-2", "Bob Keeper", "bob@example.com", is_active=False),
        }
        self.membership_repo = InMemoryMembershipRepo(self.tenants, self.users)
        self.tenant_repo = InMemoryTenantRepo(self.tenants)
        self.user_repo = InMemoryUserRepo(self.users)

        self.tenant_service = TenantService(
            tenant_repo=self.tenant_repo,  # type: ignore[arg-type]
            membership_repo=self.membership_repo,  # type: ignore[arg-type]
            invitation_repo=MagicMock(),
            assignment_repo=MagicMock(),
            tenant_engine=MagicMock(),
            membership_engine=MagicMock(),
            invitation_engine=MagicMock(),
        )
        self.user_service = UserService(
            self.user_repo,  # type: ignore[arg-type]
            MagicMock(),
            self.membership_repo,  # type: ignore[arg-type]
        )

        app = FastAPI()
        app.include_router(mod.router, prefix="/api/v1")
        app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
        app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
        app.dependency_overrides[require_platform_admin] = lambda: SimpleNamespace(key="admin-1")
        app.dependency_overrides[get_tenant_service] = lambda: self.tenant_service
        app.dependency_overrides[get_user_service] = lambda: self.user_service
        self.client = TestClient(app)


@pytest.fixture
def backend() -> Backend:
    return Backend()


def _sole_membership(backend: Backend) -> Membership:
    memberships = list(backend.membership_repo._store.values())
    assert len(memberships) == 1
    return memberships[0]


def _comparable(m: Membership) -> dict[str, Any]:
    """The membership's identity fields, ignoring generated key / timestamps."""
    return {
        "user_key": m.user_key,
        "tenant_key": m.tenant_key,
        "role": m.role,
        "is_active": m.is_active,
        "admin_scopes": m.admin_scopes,
    }


# ── Equivalence: the two perspectives produce the same result ─────────────────


class TestAddMembershipEquivalence:
    def test_tenant_and_user_perspective_create_the_same_membership(self):
        """POST via the tenant view and via the user view, in isolated backends,
        must persist an identical membership and identical graph edges."""
        tenant_view = Backend()
        resp_t = tenant_view.client.post(
            "/api/v1/admin/platform/tenants/t-1/members",
            json={"user_key": "u-1", "role": "grower"},
        )
        assert resp_t.status_code == 201

        user_view = Backend()
        resp_u = user_view.client.post(
            "/api/v1/admin/platform/users/u-1/memberships",
            json={"tenant_key": "t-1", "role": "grower"},
        )
        assert resp_u.status_code == 201

        m_tenant = _sole_membership(tenant_view)
        m_user = _sole_membership(user_view)

        # Same persisted membership …
        assert _comparable(m_tenant) == _comparable(m_user)
        assert _comparable(m_tenant) == {
            "user_key": "u-1",
            "tenant_key": "t-1",
            "role": TenantRole.GROWER,
            "is_active": True,
            "admin_scopes": [],
        }
        # … and the same two graph edges (identity kinds/endpoints).
        assert tenant_view.membership_repo.edges == user_view.membership_repo.edges
        assert tenant_view.membership_repo.edges == [
            ("has_membership", "users/u-1", "memberships/m-1"),
            ("membership_in", "memberships/m-1", "tenants/t-1"),
        ]

    def test_both_perspectives_reject_a_duplicate_membership_with_409(self):
        for path, payload in (
            ("/api/v1/admin/platform/tenants/t-1/members", {"user_key": "u-1", "role": "viewer"}),
            ("/api/v1/admin/platform/users/u-1/memberships", {"tenant_key": "t-1", "role": "viewer"}),
        ):
            backend = Backend()
            assert backend.client.post(path, json=payload).status_code == 201
            # Second identical add is a duplicate.
            assert backend.client.post(path, json=payload).status_code == 409


class TestChangeRoleEquivalence:
    def test_tenant_and_user_perspective_change_the_role_identically(self):
        tenant_view = Backend()
        tenant_view.membership_repo.create(Membership(user_key="u-1", tenant_key="t-1", role=TenantRole.VIEWER))
        resp_t = tenant_view.client.patch(
            "/api/v1/admin/platform/tenants/t-1/members/m-1/role",
            json={"role": "lead"},
        )
        assert resp_t.status_code == 200

        user_view = Backend()
        user_view.membership_repo.create(Membership(user_key="u-1", tenant_key="t-1", role=TenantRole.VIEWER))
        resp_u = user_view.client.patch(
            "/api/v1/admin/platform/users/u-1/memberships/m-1/role",
            json={"role": "lead"},
        )
        assert resp_u.status_code == 200

        assert _comparable(_sole_membership(tenant_view)) == _comparable(_sole_membership(user_view))
        assert _sole_membership(tenant_view).role == TenantRole.LEAD
        # Both responses carry the new role, in their own shape.
        assert resp_t.json()["role"] == "lead"
        assert resp_u.json()["role"] == "lead"


class TestRemoveMembershipEquivalence:
    def test_tenant_and_user_perspective_remove_identically_and_clean_assignments(self):
        tenant_view = Backend()
        tenant_view.membership_repo.create(Membership(user_key="u-1", tenant_key="t-1", role=TenantRole.GROWER))
        assert tenant_view.client.delete("/api/v1/admin/platform/tenants/t-1/members/m-1").status_code == 204

        user_view = Backend()
        user_view.membership_repo.create(Membership(user_key="u-1", tenant_key="t-1", role=TenantRole.GROWER))
        assert user_view.client.delete("/api/v1/admin/platform/users/u-1/memberships/m-1").status_code == 204

        # Both removed the membership …
        assert tenant_view.membership_repo._store == {}
        assert user_view.membership_repo._store == {}
        # … and both cleaned the membership's location assignments — the behaviour
        # the raw-AQL router copies skipped (it removed only the two edges).
        assert tenant_view.membership_repo.location_assignments_cleaned == ["m-1"]
        assert user_view.membership_repo.location_assignments_cleaned == ["m-1"]
        assert tenant_view.membership_repo.edges == []
        assert user_view.membership_repo.edges == []


# ── Ownership constraint: a membership addressed under the wrong parent 404s ───


class TestOwnershipConstraint:
    def test_tenant_perspective_404s_a_membership_of_a_different_tenant(self, backend):
        backend.membership_repo.create(Membership(user_key="u-1", tenant_key="t-1", role=TenantRole.VIEWER))
        # Address m-1 under t-2, which it does not belong to.
        resp = backend.client.patch(
            "/api/v1/admin/platform/tenants/t-2/members/m-1/role",
            json={"role": "lead"},
        )
        assert resp.status_code == 404

    def test_user_perspective_404s_a_membership_of_a_different_user(self, backend):
        backend.membership_repo.create(Membership(user_key="u-1", tenant_key="t-1", role=TenantRole.VIEWER))
        resp = backend.client.delete("/api/v1/admin/platform/users/u-2/memberships/m-1")
        assert resp.status_code == 404


# ── Reads routed through the service layer ────────────────────────────────────


class TestReadsRouteThroughServices:
    def test_stats_counts_come_from_the_service_layer(self, backend):
        backend.membership_repo.create(Membership(user_key="u-1", tenant_key="t-1", role=TenantRole.GROWER))
        resp = backend.client.get("/api/v1/admin/platform/stats")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total_users"] == 2
        assert body["active_users"] == 1  # u-2 is inactive
        assert body["total_tenants"] == 2
        assert body["active_tenants"] == 2
        assert body["total_memberships"] == 1

    def test_list_all_tenants_carries_active_member_counts(self, backend):
        backend.membership_repo.create(Membership(user_key="u-1", tenant_key="t-1", role=TenantRole.GROWER))
        resp = backend.client.get("/api/v1/admin/platform/tenants")

        assert resp.status_code == 200
        by_key = {t["key"]: t for t in resp.json()}
        assert by_key["t-1"]["member_count"] == 1
        assert by_key["t-2"]["member_count"] == 0

    def test_list_user_memberships_joins_tenant_name_and_slug(self, backend):
        backend.membership_repo.create(Membership(user_key="u-1", tenant_key="t-1", role=TenantRole.GROWER))
        resp = backend.client.get("/api/v1/admin/platform/users/u-1/memberships")

        assert resp.status_code == 200
        rows = resp.json()
        assert len(rows) == 1
        assert rows[0]["tenant_name"] == "Community Garden"
        assert rows[0]["tenant_slug"] == "community-garden"
        assert rows[0]["membership_key"] == "m-1"

    def test_list_all_users_enriches_active_memberships(self, backend):
        backend.membership_repo.create(Membership(user_key="u-1", tenant_key="t-1", role=TenantRole.GROWER))
        resp = backend.client.get("/api/v1/admin/platform/users")

        assert resp.status_code == 200
        by_key = {u["key"]: u for u in resp.json()}
        assert by_key["u-1"]["tenant_count"] == 1
        assert by_key["u-1"]["roles"][0]["tenant_slug"] == "community-garden"
        assert by_key["u-2"]["tenant_count"] == 0

    def test_list_tenant_members_reports_the_member(self, backend):
        backend.membership_repo.create(Membership(user_key="u-1", tenant_key="t-1", role=TenantRole.GROWER))
        resp = backend.client.get("/api/v1/admin/platform/tenants/t-1/members")

        assert resp.status_code == 200
        rows = resp.json()
        assert len(rows) == 1
        assert rows[0]["email"] == "alice@example.com"
        assert rows[0]["membership_key"] == "m-1"


# ── delete_user cascade removes memberships before the user (SEC-003 order) ────


class TestDeleteUserCascade:
    def test_permanent_delete_removes_memberships_then_the_user(self, backend):
        backend.membership_repo.create(Membership(user_key="u-1", tenant_key="t-1", role=TenantRole.GROWER))
        backend.membership_repo.create(Membership(user_key="u-1", tenant_key="t-2", role=TenantRole.VIEWER))

        backend.user_service.delete_account_permanently("u-1")

        assert backend.membership_repo._store == {}
        assert backend.user_repo.deleted == ["u-1"]
