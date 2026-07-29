"""Member management runs on REQ-049 axis 2, and INV-1 protects the last manager (#780).

Two properties are asserted here because both fail silently otherwise:

* member management is gated on the ``MANAGEMENT`` scope, never on the domain
  rank — a lead without it is not an administrator;
* a tenant never loses its last ``MANAGEMENT`` holder (INV-1, AK-06). Losing it
  would strand the tenant: nobody left could invite anyone, not even the people
  still in it.
"""

from unittest.mock import MagicMock

import pytest

from app.common.enums import AdminScope, TenantRole
from app.common.exceptions import ForbiddenError, ValidationError
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.models.membership import Membership
from app.domain.services.tenant_service import TenantService

_MANAGER = [AdminScope.MANAGEMENT]
_NONE: list[AdminScope] = []


def _membership(scopes: list[AdminScope], role: TenantRole = TenantRole.LEAD) -> Membership:
    return Membership(_key="m1", user_key="u1", tenant_key="t1", role=role, admin_scopes=scopes)


def _service(membership: Membership, manager_count: int) -> tuple[TenantService, MagicMock]:
    membership_repo = MagicMock()
    membership_repo.get_by_key.return_value = membership
    membership_repo.get_by_user_and_tenant.return_value = membership
    membership_repo.count_managers.return_value = manager_count
    membership_repo.delete.return_value = True
    membership_repo.update.return_value = membership

    service = TenantService(
        tenant_repo=MagicMock(),
        membership_repo=membership_repo,
        invitation_repo=MagicMock(),
        tenant_engine=MagicMock(),
        membership_engine=MembershipEngine(),
        invitation_engine=MagicMock(),
        assignment_repo=MagicMock(),
    )
    return service, membership_repo


class TestManagementScopeGatesMemberManagement:
    def test_lead_without_the_scope_cannot_remove_a_member(self):
        service, _ = _service(_membership(_MANAGER), manager_count=2)

        with pytest.raises(ForbiddenError, match="management"):
            service.remove_member("t1", "m1", actor_scopes=_NONE)

    def test_scope_holder_can_remove_a_member(self):
        service, repo = _service(_membership(_NONE, role=TenantRole.GROWER), manager_count=1)

        assert service.remove_member("t1", "m1", actor_scopes=_MANAGER) is True
        repo.delete.assert_called_once_with("m1")

    def test_technical_scope_does_not_substitute(self):
        service, _ = _service(_membership(_NONE), manager_count=2)

        with pytest.raises(ForbiddenError, match="management"):
            service.remove_member("t1", "m1", actor_scopes=[AdminScope.TECHNICAL])


class TestLastManagerGuard:
    def test_removing_the_last_manager_is_rejected(self):
        service, repo = _service(_membership(_MANAGER), manager_count=1)

        with pytest.raises(ValidationError, match="management"):
            service.remove_member("t1", "m1", actor_scopes=_MANAGER)
        repo.delete.assert_not_called()

    def test_removing_a_manager_while_another_remains_is_allowed(self):
        service, repo = _service(_membership(_MANAGER), manager_count=2)

        assert service.remove_member("t1", "m1", actor_scopes=_MANAGER) is True
        repo.delete.assert_called_once_with("m1")

    def test_the_last_manager_cannot_leave(self):
        service, repo = _service(_membership(_MANAGER), manager_count=1)

        with pytest.raises(ValidationError, match="management"):
            service.leave_tenant("t1", "u1")
        repo.delete.assert_not_called()

    def test_a_member_without_the_scope_may_always_leave(self):
        # The guard counts managers, not members — a grower leaving strands
        # nobody, however few people remain.
        service, repo = _service(_membership(_NONE, role=TenantRole.GROWER), manager_count=1)

        assert service.leave_tenant("t1", "u1") is True
        repo.delete.assert_called_once()

    def test_dropping_the_scope_from_the_last_manager_is_rejected(self):
        # Demotion is the same hole as removal; guarding only removal would
        # leave the tenant strandable by an edit.
        service, repo = _service(_membership(_MANAGER), manager_count=1)

        with pytest.raises(ValidationError, match="management"):
            service.change_member_scopes("t1", "m1", new_scopes=_NONE, actor_scopes=_MANAGER)
        repo.update.assert_not_called()

    def test_the_domain_role_may_still_be_demoted_freely(self):
        # Axis 1 carries no administrative rights, so lowering it can never
        # strand a tenant — the guard must not block it.
        service, repo = _service(_membership(_MANAGER), manager_count=1)

        service.change_member_role("t1", "m1", new_role=TenantRole.VIEWER, actor_scopes=_MANAGER)

        repo.update.assert_called_once_with("m1", {"role": TenantRole.VIEWER})
