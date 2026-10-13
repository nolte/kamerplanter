"""#2106 — a platform admin adding an account to a tenant passes the admin's own step-up and leaves an audit row.

``POST /admin/platform/tenants/{tenant_key}/members`` and ``POST /admin/platform/users/{user_key}/memberships``
put any account into any tenant — the ``platform`` tenant with the ``lead`` role (the platform-admin role)
included — on nothing but the admin session (or one of its API keys), without a log line, asymmetrically
to the role change and the removal, which passed the step-up since #2032 and #2009. The rule of #1992 — "a
change that gives or takes access to another account is a step-up act" — puts the add beside them
(act ``admin_membership_add``, bound to ``<tenant_key>|<user_key>``, #1884, REQ-024 AK-59).

Same harness as ``test_admin_tenant_step_up``: the real routers, the real ``TenantService`` and verifier with
the real target rules over in-memory repositories holding real models; what survives a refusal is read off
those stores. Every test uses a fresh admin key, so the process-wide throttle carries no state between tests.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from app.common.enums import TenantRole
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.interfaces.security_audit_repository import ISecurityAuditRepository
from app.domain.models.membership import Membership
from app.domain.models.security_audit import SecurityAuditEntry
from app.domain.models.user import User
from app.domain.services.security_audit_service import SecurityAuditService
from app.domain.services.tenant_service import TenantService
from tests.unit.api.test_admin_tenant_step_up import (  # noqa: F401 - the autouse rate-limit reset is a fixture
    API_KEY,
    GARDEN,
    MEMBER,
    OTHER_GARDEN,
    PASSWORD,
    WRONG_PASSWORD,
    _full_rate_limit_budget,
    _World,
)

NEWCOMER = "u-newcomer"
TENANT_ADD = "/api/v1/admin/platform/tenants/{tenant}/members"
USER_ADD = "/api/v1/admin/platform/users/{user}/memberships"


class _AuditRepo(ISecurityAuditRepository):
    def __init__(self) -> None:
        self.rows: list[SecurityAuditEntry] = []

    def record(self, entry: SecurityAuditEntry) -> str:
        self.rows.append(entry)
        return f"audit-{len(self.rows)}"

    def list_recent(self, *, tenant_key: str | None = None, limit: int = 100) -> list[SecurityAuditEntry]:
        return list(self.rows)

    def delete_expired(self, *, retention_days: int) -> int:
        return 0

    def count_undated(self) -> int:
        return 0


class _AddWorld(_World):
    """The step-up world, plus a newcomer account, a ``create`` on the membership store and an audit double."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.users.rows[NEWCOMER] = User.model_validate(
            {"_key": NEWCOMER, "email": "newcomer@example.org", "display_name": "Newcomer"}
        )
        self.audit = _AuditRepo()
        self.created: list[Membership] = []
        memberships = self.memberships

        def create(membership: Membership) -> Membership:
            stored = membership.model_copy(update={"key": f"m-{len(memberships.rows) + 1}"})
            memberships.rows[stored.key] = stored
            self.created.append(stored)
            return stored

        memberships.create = create  # type: ignore[attr-defined]
        self.tenant_service = TenantService(
            tenant_repo=self.tenants,  # type: ignore[arg-type]
            membership_repo=memberships,  # type: ignore[arg-type]
            invitation_repo=MagicMock(),
            assignment_repo=MagicMock(),
            tenant_engine=TenantEngine(),
            membership_engine=MembershipEngine(),
            invitation_engine=InvitationEngine(),
            step_up_verifier=self.verifier,
            security_audit=SecurityAuditService(self.audit),
        )

    def add(self, view: str, *, tenant: str = GARDEN, user: str = NEWCOMER, role: str = "grower", **extra: Any) -> Any:
        bearer = extra.pop("bearer", None)
        if view == "tenant":
            return self.send(
                "POST", TENANT_ADD.format(tenant=tenant), {"user_key": user, "role": role, **extra}, bearer=bearer
            )
        return self.send(
            "POST", USER_ADD.format(user=user), {"tenant_key": tenant, "role": role, **extra}, bearer=bearer
        )

    def is_member(self, user: str, tenant: str) -> bool:
        return self.memberships.get_by_user_and_tenant(user, tenant) is not None


VIEWS = [pytest.param("tenant", id="tenant view"), pytest.param("user", id="user view")]


@pytest.mark.parametrize("view", VIEWS)
@pytest.mark.parametrize(
    "step_up",
    [
        pytest.param({}, id="no password"),
        pytest.param({"current_password": WRONG_PASSWORD}, id="wrong password"),
        pytest.param({"step_up_code": "12345678"}, id="a code nobody issued"),
    ],
)
def test_nobody_is_added_without_the_admins_step_up(view: str, step_up: dict[str, Any]) -> None:
    world = _AddWorld()

    resp = world.add(view, **step_up)

    assert resp.status_code == 401, resp.text
    assert not world.is_member(NEWCOMER, GARDEN)
    assert world.created == [] and world.audit.rows == []


@pytest.mark.parametrize("view", VIEWS)
def test_an_account_is_added_with_the_admins_own_password_and_leaves_an_audit_row(view: str) -> None:
    world = _AddWorld()

    resp = world.add(view, current_password=PASSWORD)

    assert resp.status_code == 201, resp.text
    assert world.is_member(NEWCOMER, GARDEN)
    (stored,) = world.created
    assert stored.role == "grower"
    # The step-up field is the admin's, never written to the membership.
    assert "current_password" not in stored.model_dump()
    (row,) = world.audit.rows
    assert (row.action, row.via) == ("membership_added", "platform_admin")
    assert (row.actor_user_key, row.target_user_key, row.tenant_key, row.new_role) == (
        world.admin_key,
        NEWCOMER,
        GARDEN,
        "grower",
    )


@pytest.mark.parametrize("view", VIEWS)
def test_an_api_key_cannot_add_an_account_even_with_the_password(view: str) -> None:
    world = _AddWorld()

    resp = world.add(view, current_password=PASSWORD, bearer=API_KEY)

    assert resp.status_code == 403, resp.text
    assert not world.is_member(NEWCOMER, GARDEN)
    assert world.audit.rows == []


@pytest.mark.parametrize("view", VIEWS)
def test_the_platform_role_needs_the_step_up_too(view: str) -> None:
    world = _AddWorld()

    refused = world.add(view, tenant="platform", role="lead")
    assert refused.status_code == 401, refused.text
    assert not world.is_member(NEWCOMER, "platform")

    accepted = world.add(view, tenant="platform", role="lead", current_password=PASSWORD)
    assert accepted.status_code == 201, accepted.text
    assert world.is_member(NEWCOMER, "platform")
    (row,) = world.audit.rows
    assert (row.tenant_key, row.new_role) == ("platform", "lead")


@pytest.mark.parametrize("view", VIEWS)
def test_an_admin_does_not_add_themselves_to_the_platform_tenant(view: str) -> None:
    world = _AddWorld()

    resp = world.add(view, tenant="platform", user=world.admin_key, role="lead", current_password=PASSWORD)

    # The issue says 400; this API answers a refused request body-wise with its validation error (422).
    assert resp.status_code == 422, resp.text
    assert world.created == [] and world.audit.rows == []


def test_an_admin_adding_themselves_elsewhere_is_possible_with_the_step_up_and_audited() -> None:
    """The case #2106 names: not forbidden (support access), but never silent."""
    world = _AddWorld()

    refused = world.add("tenant", user=world.admin_key, role="lead")
    assert refused.status_code == 401, refused.text
    assert not world.is_member(world.admin_key, GARDEN)

    accepted = world.add("tenant", user=world.admin_key, role="lead", current_password=PASSWORD)
    assert accepted.status_code == 201, accepted.text
    (row,) = world.audit.rows
    assert row.actor_user_key == row.target_user_key == world.admin_key


@pytest.mark.parametrize("view", VIEWS)
def test_a_federated_admin_adds_with_a_code_bound_to_this_tenant_and_account(view: str) -> None:
    world = _AddWorld(password_hash=None)
    code = world.issue_code("admin_membership_add", f"{GARDEN}|{NEWCOMER}")

    # #1884 — the code obtained for this tenant and account does not add another account …
    world.users.rows["u-third"] = User.model_validate(
        {"_key": "u-third", "email": "third@example.org", "display_name": "Third"}
    )
    refused_other_user = world.add(view, user="u-third", role="viewer", step_up_code=code)
    assert refused_other_user.status_code == 401, refused_other_user.text
    assert not world.is_member("u-third", GARDEN)
    # … nor into another tenant …
    refused_other_tenant = world.add(view, tenant=OTHER_GARDEN, step_up_code=code)
    assert refused_other_tenant.status_code == 401, refused_other_tenant.text
    assert not world.is_member(NEWCOMER, OTHER_GARDEN)

    # … and is not spent by the mismatch: it still adds the pair it names.
    accepted = world.add(view, step_up_code=code)
    assert accepted.status_code == 201, accepted.text
    assert world.is_member(NEWCOMER, GARDEN)


def test_a_member_of_the_tenant_is_refused_before_a_step_up_is_asked_for() -> None:
    world = _AddWorld()

    resp = world.add("tenant", user=MEMBER, role="viewer")

    assert resp.status_code == 409, resp.text
    assert world.audit.rows == []


@pytest.mark.parametrize(
    ("tenant", "user", "status"),
    [
        pytest.param("t-missing", NEWCOMER, 404, id="unknown tenant"),
        pytest.param(GARDEN, "u-missing", 404, id="unknown account"),
    ],
)
def test_no_code_is_issued_for_a_pair_that_does_not_exist(tenant: str, user: str, status: int) -> None:
    world = _AddWorld(password_hash=None)

    resp = world.send(
        "POST", "/api/v1/users/me/step-up-code", {"action": "admin_membership_add", "target": f"{tenant}|{user}"}
    )

    assert resp.status_code == status, resp.text
    world.mail.send_step_up_code_email.assert_not_called()


def test_a_malformed_target_gets_no_code() -> None:
    world = _AddWorld(password_hash=None)

    for target in ("no-separator", f"{GARDEN}|", f"|{NEWCOMER}", f"{GARDEN}|{NEWCOMER}|extra", f"{GARDEN}/{NEWCOMER}"):
        resp = world.send("POST", "/api/v1/users/me/step-up-code", {"action": "admin_membership_add", "target": target})
        assert resp.status_code in (404, 422), (target, resp.text)
    world.mail.send_step_up_code_email.assert_not_called()


def test_the_service_refuses_the_platform_lead_role_to_anyone_who_does_not_hold_it() -> None:
    """The service's own check, behind the route's ``require_platform_admin`` (REQ-049 §2.5)."""
    world = _AddWorld()
    outsider = User.model_validate({"_key": "u-outsider", "email": "o@example.org", "display_name": "Outsider"})

    from app.common.exceptions import ForbiddenError

    with pytest.raises(ForbiddenError):
        world.tenant_service.admin_add_membership(
            "platform",
            NEWCOMER,
            TenantRole.LEAD,
            requester=outsider,
            current_password=None,
            step_up_code=None,
            step_up_token=None,
            authenticated_with_api_key=False,
            client_ip=None,
        )
    assert world.created == []
