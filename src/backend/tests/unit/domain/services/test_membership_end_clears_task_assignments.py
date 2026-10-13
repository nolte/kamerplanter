"""#2114 (MT-017, REQ-024 AK-62): a membership that ends takes the member's task assignments in that tenant with it.

``remove_member`` / ``leave_tenant`` / ``admin_remove_membership`` deleted the membership and the location
assignments but not ``tasks.assigned_to_user_key``: the ex-member stayed the assignee of the tenant's tasks and
the care-reminder beat went on notifying them (plant names, due dates) by push and mail. Every way a membership
ends now clears the assignee of that tenant's tasks - and only that tenant's - through
``ITaskRepository.clear_assignee``. The real repository (tenant filter, other tenants untouched) is measured on a
real ArangoDB in ``tests/integration/test_membership_end_task_assignments_reach.py``.
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
_STEP_UP_ONLY = {"client_ip": None, **STEP_UP_PASSED}


def _world(*, deleted: bool = True) -> tuple[TenantService, MagicMock]:
    stored = Membership(_key="m1", user_key="ex-member", tenant_key="t1", role=TenantRole.GROWER, is_active=True)
    memberships = MagicMock()
    memberships.get_by_key.return_value = stored
    memberships.get_by_user_and_tenant.return_value = stored
    memberships.count_managers.return_value = 2
    memberships.delete.return_value = deleted
    tenants = MagicMock()
    tenants.get_by_key.return_value = Tenant(_key="t1", name="Garden", slug="garden", owner_user_key="o")
    tasks = MagicMock()
    tasks.clear_assignee.return_value = 3
    service = TenantService(
        tenant_repo=tenants,
        membership_repo=memberships,
        invitation_repo=MagicMock(),
        assignment_repo=MagicMock(),
        tenant_engine=TenantEngine(),
        membership_engine=MembershipEngine(),
        invitation_engine=InvitationEngine(),
        step_up_verifier=PassedStepUpVerifier(),  # type: ignore[arg-type]
        task_repo=tasks,
    )
    return service, tasks


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
def test_every_way_a_membership_ends_clears_the_assignee_of_that_tenants_tasks(end) -> None:
    service, tasks = _world()

    end(service)

    tasks.clear_assignee.assert_called_once_with(tenant_key="t1", user_key="ex-member")


@pytest.mark.parametrize("end", [_remove_as_tenant_admin, _remove_as_platform_admin, _leave])
def test_nothing_is_cleared_when_the_membership_was_not_removed(end) -> None:
    service, tasks = _world(deleted=False)

    end(service)

    tasks.clear_assignee.assert_not_called()


def test_a_failing_clear_does_not_undo_the_removal_and_is_reported_without_the_keys() -> None:
    """The membership is gone; the notifier's own membership check (#2114) is the second barrier."""
    service, tasks = _world()
    tasks.clear_assignee.side_effect = RuntimeError("tasks store down for ex-member / t1")

    with capture_logs() as logs:
        removed = _leave(service)

    assert removed is True
    (line,) = [entry for entry in logs if entry["event"] == "task_assignments_not_cleared"]
    assert line["log_level"] == "warning"
    assert "ex-member" not in repr(line)
    assert line["error_type"] == "RuntimeError"


def test_a_service_without_a_task_store_still_removes() -> None:
    service, _ = _world()
    service._task_repo = None  # type: ignore[attr-defined]

    assert _leave(service) is True
