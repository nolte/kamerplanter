"""#2226 review SEC-001: a membership that ends takes the member's iCal feeds in that tenant with it.

A feed is a standing read of the tenant's calendar by URL. ``remove_member`` /
``leave_tenant`` / ``admin_remove_membership`` / ``remove_service_account``
deleted the membership and left the member's feeds behind, so a removed member's
subscription went on rendering the tenant's calendar. Every way a membership ends
now deletes the member's feeds in that tenant - and only there - through
``ICalendarFeedRepository.delete_by_user``. The feed route checks the owner's
membership itself (``CalendarService.generate_ical_for_feed``); this delete is
the tidy-up behind that barrier.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from structlog.testing import capture_logs

from app.common.enums import AdminScope, TenantRole
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.models.membership import Membership
from app.domain.models.tenant import Tenant
from app.domain.services.tenant_service import TenantService
from tests.support.step_up import STEP_UP_PASSED, PassedStepUpVerifier

_ADMIN = MagicMock(key="admin-1")
_STEP_UP = {"requester": _ADMIN, "client_ip": None, **STEP_UP_PASSED}


def _world(*, deleted: bool = True) -> tuple[TenantService, MagicMock]:
    stored = Membership(_key="m1", user_key="ex-member", tenant_key="t1", role=TenantRole.GROWER, is_active=True)
    memberships = MagicMock()
    memberships.get_by_key.return_value = stored
    memberships.get_by_user_and_tenant.return_value = stored
    memberships.count_managers.return_value = 2
    memberships.delete.return_value = deleted
    tenants = MagicMock()
    tenants.get_by_key.return_value = Tenant(_key="t1", name="Garden", slug="garden", owner_user_key="o")
    feeds = MagicMock()
    feeds.delete_by_user.return_value = 2
    service = TenantService(
        tenant_repo=tenants,
        membership_repo=memberships,
        invitation_repo=MagicMock(),
        assignment_repo=MagicMock(),
        tenant_engine=TenantEngine(),
        membership_engine=MembershipEngine(),
        invitation_engine=InvitationEngine(),
        step_up_verifier=PassedStepUpVerifier(),  # type: ignore[arg-type]
        task_repo=MagicMock(),
        calendar_feed_repo=feeds,
    )
    return service, feeds


def _remove_as_tenant_admin(service: TenantService) -> object:
    return service.remove_member("t1", "m1", [AdminScope.MANAGEMENT], **_STEP_UP)


def _remove_as_platform_admin(service: TenantService) -> object:
    return service.admin_remove_membership("m1", tenant_key="t1", **_STEP_UP)


def _leave(service: TenantService) -> object:
    return service.leave_tenant("t1", "ex-member")


@pytest.mark.parametrize(
    "end",
    [
        pytest.param(_remove_as_tenant_admin, id="removed by the tenant's administrator"),
        pytest.param(_remove_as_platform_admin, id="removed by a platform admin"),
        pytest.param(_leave, id="leaving"),
    ],
)
def test_every_way_a_membership_ends_deletes_the_members_feeds_in_that_tenant(end) -> None:
    service, feeds = _world()

    end(service)

    feeds.delete_by_user.assert_called_once_with("ex-member", tenant_key="t1")


@pytest.mark.parametrize("end", [_remove_as_tenant_admin, _remove_as_platform_admin, _leave])
def test_nothing_is_deleted_when_the_membership_was_not_removed(end) -> None:
    service, feeds = _world(deleted=False)

    end(service)

    feeds.delete_by_user.assert_not_called()


def test_a_failing_delete_does_not_undo_the_removal_and_is_reported_without_the_keys() -> None:
    service, feeds = _world()
    feeds.delete_by_user.side_effect = RuntimeError("feed store down for ex-member / t1")

    with capture_logs() as logs:
        removed = _leave(service)

    assert removed is True
    (line,) = [entry for entry in logs if entry["event"] == "calendar_feeds_not_deleted"]
    assert line["log_level"] == "warning"
    assert "ex-member" not in repr(line)
    assert line["error_type"] == "RuntimeError"


def test_a_service_without_a_feed_store_still_removes() -> None:
    service, _ = _world()
    service._calendar_feed_repo = None  # type: ignore[attr-defined]

    assert _leave(service) is True
