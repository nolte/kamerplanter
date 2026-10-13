"""#2078 / REQ-024 AK-58 — the tenant-scoped role and invitation routes refuse an escalation.

The real ``/tenants/{slug}`` router, the real ``TenantService`` and the real step-up verifier,
over the in-memory doubles of ``test_admin_tenant_step_up.py``. The real-database measurement is
``tests/integration/test_member_role_escalation_reach.py``; this one runs in the unit lane.

The defect: a ``management`` holder in the ``platform`` tenant who was not its ``lead`` promoted
themselves to ``lead`` with their *own* password as the step-up (#2032) — and ``lead`` there is the
platform role. A refusal is a 403 *before* the step-up is asked for, and nothing is written.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from app.common.enums import AdminScope, TenantRole
from app.domain.models.membership import Membership
from tests.unit.api.test_admin_tenant_step_up import (
    PASSWORD,
    _full_rate_limit_budget,  # noqa: F401 - autouse fixture
)
from tests.unit.api.test_tenant_role_membership_step_up import (
    GROWER_MEMBERSHIP,
    SECRETARY_MEMBERSHIP,
    _TenantWorld,
)

PLATFORM_SECRETARY = "m-platform-secretary"
PLATFORM_VIEWER = "m-platform-viewer"


def _world() -> _TenantWorld:
    """The garden's secretary also sits in the platform tenant — holding ``management``, not ``lead``."""
    world = _TenantWorld()
    world.memberships.rows[PLATFORM_SECRETARY] = Membership(
        _key=PLATFORM_SECRETARY,
        user_key=world.actor_key,
        tenant_key="platform",
        role=TenantRole.GROWER,
        admin_scopes=[AdminScope.MANAGEMENT],
    )
    world.memberships.rows[PLATFORM_VIEWER] = Membership(
        _key=PLATFORM_VIEWER, user_key="u-platform-viewer", tenant_key="platform", role=TenantRole.VIEWER
    )
    return world


def _set_role(world: _TenantWorld, slug: str, membership: str, role: str) -> Any:
    return world.send(
        "PATCH", f"/api/v1/tenants/{slug}/members/{membership}/role", {"role": role, "current_password": PASSWORD}
    )


def test_a_platform_member_with_management_cannot_make_themselves_lead() -> None:
    world = _world()

    resp = _set_role(world, "platform", PLATFORM_SECRETARY, "lead")

    assert resp.status_code == 403, resp.text
    assert world.memberships.rows[PLATFORM_SECRETARY].role == TenantRole.GROWER
    assert world.memberships.writes == []


def test_the_refusal_comes_before_the_step_up_is_asked_for() -> None:
    world = _world()

    resp = world.send("PATCH", f"/api/v1/tenants/platform/members/{PLATFORM_SECRETARY}/role", {"role": "lead"})

    assert resp.status_code == 403, resp.text


def test_a_platform_member_who_is_not_lead_cannot_hand_out_lead() -> None:
    world = _world()

    resp = _set_role(world, "platform", PLATFORM_VIEWER, "lead")

    assert resp.status_code == 403, resp.text
    assert world.memberships.rows[PLATFORM_VIEWER].role == TenantRole.VIEWER


def test_a_member_of_an_ordinary_tenant_cannot_raise_their_own_role() -> None:
    world = _world()

    resp = _set_role(world, "t-garden", SECRETARY_MEMBERSHIP, "grower")

    assert resp.status_code == 403, resp.text
    assert world.memberships.rows[SECRETARY_MEMBERSHIP].role == TenantRole.VIEWER
    assert world.memberships.writes == []


def test_the_secretary_of_an_ordinary_tenant_still_appoints_a_lead() -> None:
    """REQ-049 §2.4: no rank ceiling outside the platform tenant."""
    world = _world()

    resp = _set_role(world, "t-garden", GROWER_MEMBERSHIP, "lead")

    assert resp.status_code == 200, resp.text
    assert world.memberships.rows[GROWER_MEMBERSHIP].role == TenantRole.LEAD


def test_a_platform_member_with_management_still_hands_out_roles_below_lead() -> None:
    world = _world()

    resp = _set_role(world, "platform", PLATFORM_VIEWER, "grower")

    assert resp.status_code == 200, resp.text
    assert world.memberships.rows[PLATFORM_VIEWER].role == TenantRole.GROWER


@pytest.mark.parametrize("path", ["invitations/email", "invitations/link"])
def test_a_platform_member_who_is_not_lead_cannot_invite_a_lead(path: str) -> None:
    world = _world()
    invitations = MagicMock()
    world.tenant_service._invitation_repo = invitations
    body: dict[str, Any] = {"role": "lead"}
    if path.endswith("email"):
        body["email"] = "new@example.org"

    resp = world.send("POST", f"/api/v1/tenants/platform/{path}", body)

    assert resp.status_code == 403, resp.text
    invitations.create.assert_not_called()
