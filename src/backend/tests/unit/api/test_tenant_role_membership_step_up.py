"""#2032 — changing a member's role and removing a member pass the acting admin's own step-up.

Four routes locked a member out of (or demoted them in) a tenant with nothing but the
session — or one of its API keys — after #2009 gated the other three platform-admin
lockout paths:

* ``PATCH /admin/platform/tenants/{tenant_key}/members/{membership_key}/role`` and
* ``PATCH /admin/platform/users/{user_key}/memberships/{membership_key}/role`` — a
  platform admin demotes a tenant's last ``lead`` (acts ``admin_membership_role_change``);
* ``DELETE /tenants/{slug}/members/{membership_key}`` and
* ``PATCH /tenants/{slug}/members/{membership_key}/role`` — a tenant's member
  administrator (the ``management`` scope) removes or demotes a member (acts
  ``tenant_member_removal`` / ``tenant_member_role_change``).

Operator decision on #2032 (REQ-024 AK-57): all four are step-up acts, bound to the
membership (#1884); ``DELETE /tenants/{slug}/assignments/{key}`` is not — it does not
lock a member out. A role *re-sent unchanged* needs none (the edit form re-sends what it
loaded) and writes nothing.

The requests run the real routers, the real ``TenantService`` and the real verifier with
the real target rules; the repositories are the in-memory doubles of
``test_admin_tenant_step_up.py`` holding real models. "Unchanged" is read off those stores.
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.admin.platform.router import router as admin_router
from app.api.v1.tenants.router import router as tenants_router
from app.api.v1.users.router import router as users_router
from app.common.auth import get_current_user
from app.common.dependencies import get_auth_service, get_tenant_service, get_user_service
from app.common.enums import AdminScope, TenantRole
from app.common.exceptions import KamerplanterError
from app.domain.engines.login_throttle_engine import MAX_ATTEMPTS
from app.domain.models.membership import Membership
from app.domain.models.user import User
from app.domain.services.user_service import UserService
from tests.unit.api.test_admin_tenant_step_up import (
    API_KEY,
    GARDEN,
    MEMBER,
    MEMBERSHIP,
    OTHER_GARDEN,
    OTHER_MEMBERSHIP,
    PASSWORD,
    PASSWORD_HASH,
    WRONG_PASSWORD,
    _error_handler,
    _full_rate_limit_budget,  # noqa: F401 - the autouse fixture of the shared harness
    _World,
)

GROWER_MEMBERSHIP = "m-grower"
GROWER = "u-grower"
SECRETARY_MEMBERSHIP = "m-secretary"


class _TenantWorld(_World):
    """The same garden, acted in by its **secretary**: a viewer holding ``management``, not a platform admin.

    The garden's last ``lead`` is still the member a demotion or removal would strip; the secretary
    is the only holder of ``management`` (INV-1), so the guard has something to protect.
    """

    def __init__(self, *, password_hash: str | None = PASSWORD_HASH) -> None:
        super().__init__(password_hash=None)
        self.actor_key = f"secretary-{uuid.uuid4().hex[:12]}"
        self.actor = User.model_validate(
            {
                "_key": self.actor_key,
                "email": f"{self.actor_key}@example.org",
                "display_name": "Secretary",
                "password_hash": password_hash,
            }
        )
        self.users.rows[self.actor_key] = self.actor
        self.users.rows[GROWER] = User.model_validate(
            {"_key": GROWER, "email": "grower@example.org", "display_name": "Grower"}
        )
        for membership in (
            Membership(
                _key=SECRETARY_MEMBERSHIP,
                user_key=self.actor_key,
                tenant_key=GARDEN,
                role=TenantRole.VIEWER,
                admin_scopes=[AdminScope.MANAGEMENT],
            ),
            Membership(_key=GROWER_MEMBERSHIP, user_key=GROWER, tenant_key=GARDEN, role=TenantRole.GROWER),
        ):
            self.memberships.rows[membership.key] = membership

    def client(self) -> TestClient:
        app = FastAPI()
        for router in (users_router, admin_router, tenants_router):
            app.include_router(router, prefix="/api/v1")
        app.add_exception_handler(KamerplanterError, _error_handler)
        app.dependency_overrides[get_current_user] = lambda: self.actor
        app.dependency_overrides[get_tenant_service] = lambda: self.tenant_service
        app.dependency_overrides[get_user_service] = lambda: UserService(self.users)  # type: ignore[arg-type]
        app.dependency_overrides[get_auth_service] = lambda: self.auth
        return TestClient(app, raise_server_exceptions=False)


# ── The three role routes and the one tenant removal route ───────────────────

ROLE_ROUTES = [
    pytest.param(
        "platform",
        "/api/v1/admin/platform/tenants/" + GARDEN + "/members/{key}/role",
        "admin_membership_role_change",
        id="platform tenant view",
    ),
    pytest.param(
        "platform",
        "/api/v1/admin/platform/users/" + MEMBER + "/memberships/{key}/role",
        "admin_membership_role_change",
        id="platform user view",
    ),
    pytest.param(
        "tenant", "/api/v1/tenants/" + GARDEN + "/members/{key}/role", "tenant_member_role_change", id="tenant scoped"
    ),
]
REMOVE_PATH = "/api/v1/tenants/" + GARDEN + "/members/{key}"


def _world(kind: str, *, password_hash: str | None = PASSWORD_HASH) -> _World:
    return _TenantWorld(password_hash=password_hash) if kind == "tenant" else _World(password_hash=password_hash)


def _sibling(kind: str, path: str) -> tuple[str, str]:
    """A second membership addressed under its own correct parent: (its key, the route to it)."""
    if kind == "tenant":
        return GROWER_MEMBERSHIP, path.format(key=GROWER_MEMBERSHIP)
    return OTHER_MEMBERSHIP, path.format(key=OTHER_MEMBERSHIP).replace(f"tenants/{GARDEN}", f"tenants/{OTHER_GARDEN}")


def _role_of(world: _World, key: str = MEMBERSHIP) -> TenantRole:
    return world.memberships.rows[key].role


# ── PATCH …/role: the demotion ───────────────────────────────────────────────


@pytest.mark.parametrize(("kind", "path", "action"), ROLE_ROUTES)
@pytest.mark.parametrize(
    "step_up",
    [
        pytest.param({}, id="no password"),
        pytest.param({"current_password": WRONG_PASSWORD}, id="wrong password"),
        pytest.param({"step_up_code": "12345678"}, id="a code instead of the password"),
    ],
)
def test_the_last_lead_is_not_demoted_without_the_actors_step_up(
    kind: str, path: str, action: str, step_up: dict[str, Any]
) -> None:
    world = _world(kind)

    resp = world.send("PATCH", path.format(key=MEMBERSHIP), {"role": "viewer", **step_up})

    assert resp.status_code == 401, resp.text
    assert _role_of(world) == TenantRole.LEAD
    assert world.memberships.writes == []


@pytest.mark.parametrize(("kind", "path", "action"), ROLE_ROUTES)
def test_a_role_is_changed_with_the_actors_own_password(kind: str, path: str, action: str) -> None:
    world = _world(kind)

    resp = world.send("PATCH", path.format(key=MEMBERSHIP), {"role": "viewer", "current_password": PASSWORD})

    assert resp.status_code == 200, resp.text
    assert _role_of(world) == TenantRole.VIEWER
    # The step-up field is the actor's, never written to the membership.
    assert world.memberships.writes == [(MEMBERSHIP, {"role": TenantRole.VIEWER})]


@pytest.mark.parametrize(("kind", "path", "action"), ROLE_ROUTES)
def test_promotion_passes_the_step_up_too(kind: str, path: str, action: str) -> None:
    """Any actual change: a promoted member can in turn lock others out."""
    world = _world(kind)
    target, target_path = _sibling(kind, path)

    refused = world.send("PATCH", target_path, {"role": "lead"})
    assert refused.status_code == 401, refused.text
    assert _role_of(world, target) != TenantRole.LEAD

    accepted = world.send("PATCH", target_path, {"role": "lead", "current_password": PASSWORD})
    assert accepted.status_code == 200, accepted.text
    assert _role_of(world, target) == TenantRole.LEAD


@pytest.mark.parametrize(("kind", "path", "action"), ROLE_ROUTES)
def test_an_api_key_cannot_change_a_role_even_with_the_password(kind: str, path: str, action: str) -> None:
    world = _world(kind)

    resp = world.send(
        "PATCH", path.format(key=MEMBERSHIP), {"role": "viewer", "current_password": PASSWORD}, bearer=API_KEY
    )

    assert resp.status_code == 403, resp.text
    assert _role_of(world) == TenantRole.LEAD


@pytest.mark.parametrize(("kind", "path", "action"), ROLE_ROUTES)
def test_re_sending_the_current_role_needs_no_step_up_and_writes_nothing(kind: str, path: str, action: str) -> None:
    world = _world(kind)

    resp = world.send("PATCH", path.format(key=MEMBERSHIP), {"role": "lead"})

    assert resp.status_code == 200, resp.text
    assert world.memberships.writes == []


@pytest.mark.parametrize(("kind", "path", "action"), ROLE_ROUTES)
def test_a_federated_actor_changes_a_role_with_a_code_bound_to_this_membership(
    kind: str, path: str, action: str
) -> None:
    world = _world(kind, password_hash=None)
    code = world.issue_code(action, MEMBERSHIP)
    _other_key, other_path = _sibling(kind, path)

    # #1884 — the code obtained for this membership changes no other one …
    refused = world.send("PATCH", other_path, {"role": "lead", "step_up_code": code})
    assert refused.status_code == 401, refused.text
    assert world.memberships.writes == []

    # … and is not spent by the mismatch: it still demotes the membership it names.
    accepted = world.send("PATCH", path.format(key=MEMBERSHIP), {"role": "viewer", "step_up_code": code})
    assert accepted.status_code == 200, accepted.text
    assert _role_of(world) == TenantRole.VIEWER


@pytest.mark.parametrize(("kind", "path", "action"), ROLE_ROUTES)
def test_a_code_obtained_for_a_removal_does_not_change_a_role(kind: str, path: str, action: str) -> None:
    """The act is part of the binding: one step-up, one act."""
    world = _world(kind, password_hash=None)
    removal = "tenant_member_removal" if kind == "tenant" else "admin_membership_removal"
    code = world.issue_code(removal, MEMBERSHIP)

    resp = world.send("PATCH", path.format(key=MEMBERSHIP), {"role": "viewer", "step_up_code": code})

    assert resp.status_code == 401, resp.text
    assert _role_of(world) == TenantRole.LEAD


@pytest.mark.parametrize(("kind", "path", "action"), ROLE_ROUTES)
def test_repeated_wrong_passwords_lock_the_role_change_even_for_the_right_one(
    kind: str, path: str, action: str
) -> None:
    world = _world(kind)
    for _ in range(MAX_ATTEMPTS):
        wrong = world.send("PATCH", path.format(key=MEMBERSHIP), {"role": "viewer", "current_password": WRONG_PASSWORD})
        assert wrong.status_code == 401

    resp = world.send("PATCH", path.format(key=MEMBERSHIP), {"role": "viewer", "current_password": PASSWORD})

    assert resp.status_code == 429, resp.text
    assert resp.json()["error_code"] == "STEP_UP_LOCKED"
    assert _role_of(world) == TenantRole.LEAD


@pytest.mark.parametrize(("kind", "path", "action"), ROLE_ROUTES)
def test_a_membership_of_another_parent_is_404_before_any_step_up(kind: str, path: str, action: str) -> None:
    world = _world(kind)
    # The membership exists, but under another tenant (or, in the user view, another user).
    foreign = path.format(key=MEMBERSHIP).replace(f"users/{MEMBER}", "users/u-other")
    if kind == "tenant":
        foreign = path.format(key=OTHER_MEMBERSHIP)
    elif "tenants/" in foreign:
        foreign = foreign.replace(f"tenants/{GARDEN}", f"tenants/{OTHER_GARDEN}")

    resp = world.send("PATCH", foreign, {"role": "viewer", "current_password": PASSWORD})

    assert resp.status_code == 404, resp.text
    assert world.memberships.writes == []


# ── DELETE /tenants/{slug}/members/{key}: the removal ────────────────────────


@pytest.mark.parametrize(
    "body",
    [
        pytest.param(None, id="no body"),
        pytest.param({}, id="empty body"),
        pytest.param({"current_password": WRONG_PASSWORD}, id="wrong password"),
    ],
)
def test_a_member_is_not_removed_by_a_tenant_admin_without_the_step_up(body: dict[str, Any] | None) -> None:
    world = _TenantWorld()

    resp = world.send("DELETE", REMOVE_PATH.format(key=MEMBERSHIP), body)

    assert resp.status_code == 401, resp.text
    assert world.lead_still_member()


def test_a_member_is_removed_by_a_tenant_admin_with_the_actors_own_password() -> None:
    world = _TenantWorld()

    resp = world.send("DELETE", REMOVE_PATH.format(key=MEMBERSHIP), {"current_password": PASSWORD})

    assert resp.status_code == 200, resp.text
    assert world.memberships.deleted == [MEMBERSHIP]


def test_an_api_key_cannot_remove_a_member_of_a_tenant_even_with_the_password() -> None:
    world = _TenantWorld()

    resp = world.send("DELETE", REMOVE_PATH.format(key=MEMBERSHIP), {"current_password": PASSWORD}, bearer=API_KEY)

    assert resp.status_code == 403, resp.text
    assert world.lead_still_member()


def test_a_federated_tenant_admin_removes_with_a_code_bound_to_this_membership() -> None:
    world = _TenantWorld(password_hash=None)
    code = world.issue_code("tenant_member_removal", MEMBERSHIP)

    refused = world.send("DELETE", REMOVE_PATH.format(key=GROWER_MEMBERSHIP), {"step_up_code": code})
    assert refused.status_code == 401, refused.text
    assert GROWER_MEMBERSHIP in world.memberships.rows

    accepted = world.send("DELETE", REMOVE_PATH.format(key=MEMBERSHIP), {"step_up_code": code})
    assert accepted.status_code == 200, accepted.text
    assert MEMBERSHIP not in world.memberships.rows


def test_a_role_change_code_does_not_remove_a_member() -> None:
    world = _TenantWorld(password_hash=None)
    code = world.issue_code("tenant_member_role_change", MEMBERSHIP)

    resp = world.send("DELETE", REMOVE_PATH.format(key=MEMBERSHIP), {"step_up_code": code})

    assert resp.status_code == 401, resp.text
    assert world.lead_still_member()


def test_the_last_manager_is_refused_before_a_step_up_is_asked_for() -> None:
    """INV-1 stays the first answer: the sole ``management`` holder cannot be removed, password or not."""
    world = _TenantWorld()

    resp = world.send("DELETE", REMOVE_PATH.format(key=SECRETARY_MEMBERSHIP), {"current_password": PASSWORD})

    assert resp.status_code == 422, resp.text
    assert SECRETARY_MEMBERSHIP in world.memberships.rows
    assert world.memberships.deleted == []


def test_repeated_wrong_passwords_lock_a_tenant_removal() -> None:
    world = _TenantWorld()
    for _ in range(MAX_ATTEMPTS):
        wrong = world.send("DELETE", REMOVE_PATH.format(key=MEMBERSHIP), {"current_password": WRONG_PASSWORD})
        assert wrong.status_code == 401

    resp = world.send("DELETE", REMOVE_PATH.format(key=MEMBERSHIP), {"current_password": PASSWORD})

    assert resp.status_code == 429, resp.text
    assert resp.json()["error_code"] == "STEP_UP_LOCKED"
    assert world.lead_still_member()


def test_a_membership_of_another_tenant_is_404_before_any_step_up() -> None:
    world = _TenantWorld()

    resp = world.send("DELETE", REMOVE_PATH.format(key=OTHER_MEMBERSHIP), {"current_password": PASSWORD})

    assert resp.status_code == 404, resp.text
    assert world.memberships.deleted == []


# ── who may obtain a factor, for which membership ───────────────────────────


@pytest.mark.parametrize("action", ["tenant_member_removal", "tenant_member_role_change"])
@pytest.mark.parametrize(
    "target", [pytest.param(OTHER_MEMBERSHIP, id="another tenant"), pytest.param("m-404", id="unknown")]
)
def test_no_code_is_issued_for_a_membership_the_requester_does_not_administer(action: str, target: str) -> None:
    """Unknown and foreign are one answer (403): the issuing step is no membership-existence oracle."""
    world = _TenantWorld(password_hash=None)

    resp = world.send("POST", "/api/v1/users/me/step-up-code", {"action": action, "target": target})

    assert resp.status_code == 403, resp.text
    world.mail.send_step_up_code_email.assert_not_called()


@pytest.mark.parametrize("action", ["tenant_member_removal", "tenant_member_role_change"])
def test_no_code_is_issued_to_a_member_without_the_management_scope(action: str) -> None:
    world = _TenantWorld(password_hash=None)
    world.memberships.rows[SECRETARY_MEMBERSHIP] = world.memberships.rows[SECRETARY_MEMBERSHIP].model_copy(
        update={"admin_scopes": [AdminScope.TECHNICAL]}
    )

    resp = world.send("POST", "/api/v1/users/me/step-up-code", {"action": action, "target": MEMBERSHIP})

    assert resp.status_code == 403, resp.text
    world.mail.send_step_up_code_email.assert_not_called()


def test_no_platform_code_is_issued_to_a_tenant_secretary() -> None:
    world = _TenantWorld(password_hash=None)

    resp = world.send(
        "POST", "/api/v1/users/me/step-up-code", {"action": "admin_membership_role_change", "target": MEMBERSHIP}
    )

    assert resp.status_code == 403, resp.text
    world.mail.send_step_up_code_email.assert_not_called()


def test_no_code_is_issued_for_a_role_change_of_a_membership_that_does_not_exist() -> None:
    world = _World(password_hash=None)

    resp = world.send(
        "POST", "/api/v1/users/me/step-up-code", {"action": "admin_membership_role_change", "target": "m-404"}
    )

    assert resp.status_code == 404, resp.text
    world.mail.send_step_up_code_email.assert_not_called()


# ── the decision: a location assignment is not a lockout ─────────────────────


def test_deleting_a_location_assignment_needs_no_step_up() -> None:
    """Operator decision on #2032: it does not lock a member out of the tenant."""
    world = _TenantWorld()
    assignment = type("A", (), {"tenant_key": GARDEN})()
    deleted: list[str] = []
    world.tenant_service._assignment_repo = type(  # noqa: SLF001
        "R", (), {"get_by_key": lambda _s, _k: assignment, "delete": lambda _s, k: deleted.append(k) or True}
    )()

    resp = world.send("DELETE", f"/api/v1/tenants/{GARDEN}/assignments/a-1")

    assert resp.status_code == 200, resp.text
    assert deleted == ["a-1"]


# ── documentation of the refusals ────────────────────────────────────────────


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("patch", "/api/v1/admin/platform/tenants/{tenant_key}/members/{membership_key}/role"),
        ("patch", "/api/v1/admin/platform/users/{user_key}/memberships/{membership_key}/role"),
        ("patch", "/api/v1/tenants/{tenant_slug}/members/{membership_key}/role"),
        ("delete", "/api/v1/tenants/{tenant_slug}/members/{membership_key}"),
    ],
)
def test_every_new_step_up_route_documents_its_refusals(method: str, path: str) -> None:
    app = FastAPI()
    for router in (admin_router, tenants_router):
        app.include_router(router, prefix="/api/v1")
    responses = app.openapi()["paths"][path][method]["responses"]

    assert {"401", "403", "429"} <= set(responses), sorted(responses)
