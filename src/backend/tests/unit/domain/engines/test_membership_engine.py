"""REQ-049 two-axis permission logic.

The point of the split is that the two axes are *independent*. Most of these
cases exist to hold that independence in place: someone with only ``TECHNICAL``
cannot touch the member list, and a viewer with ``MANAGEMENT`` can.
"""

from app.common.enums import AdminScope, TenantRole
from app.domain.engines.membership_engine import MembershipEngine

_NONE: list[AdminScope] = []


class TestCanManageMembers:
    def test_management_scope_grants_it(self):
        assert MembershipEngine.can_manage_members([AdminScope.MANAGEMENT]) is True

    def test_technical_scope_alone_does_not_grant_it(self):
        # The separation that keeps the sensor maintainer out of the member list.
        assert MembershipEngine.can_manage_members([AdminScope.TECHNICAL]) is False

    def test_no_scope_does_not_grant_it(self):
        assert MembershipEngine.can_manage_members(_NONE) is False


class TestCanConfigureIntegrations:
    def test_technical_scope_grants_it(self):
        assert MembershipEngine.can_configure_integrations([AdminScope.TECHNICAL]) is True

    def test_management_scope_alone_does_not_grant_it(self):
        assert MembershipEngine.can_configure_integrations([AdminScope.MANAGEMENT]) is False

    def test_no_scope_does_not_grant_it(self):
        assert MembershipEngine.can_configure_integrations(_NONE) is False


class TestCanAssignRole:
    def test_management_can_assign_every_role(self):
        # No rank ceiling on the target on purpose: a tenant whose only lead
        # left must be able to regain one.
        for role in (TenantRole.VIEWER, TenantRole.GROWER, TenantRole.LEAD):
            assert MembershipEngine.can_assign_role([AdminScope.MANAGEMENT], role) is True

    def test_without_management_nobody_can_assign(self):
        assert MembershipEngine.can_assign_role(_NONE, TenantRole.VIEWER) is False
        assert MembershipEngine.can_assign_role([AdminScope.TECHNICAL], TenantRole.VIEWER) is False


class TestCanEditResource:
    def test_lead_can_edit(self):
        assert MembershipEngine.can_edit_resource(TenantRole.LEAD) is True

    def test_grower_can_edit(self):
        assert MembershipEngine.can_edit_resource(TenantRole.GROWER) is True

    def test_viewer_cannot_edit(self):
        assert MembershipEngine.can_edit_resource(TenantRole.VIEWER) is False


class TestCanDeleteResource:
    def test_lead_can_delete(self):
        assert MembershipEngine.can_delete_resource(TenantRole.LEAD) is True

    def test_grower_cannot_delete(self):
        # The deliberate behaviour change of REQ-049: the grower/lead boundary
        # runs along irreversibility. REQ-024 §1a.1 always said so; the
        # implementation is what had drifted.
        assert MembershipEngine.can_delete_resource(TenantRole.GROWER) is False

    def test_viewer_cannot_delete(self):
        assert MembershipEngine.can_delete_resource(TenantRole.VIEWER) is False


class TestCanViewResource:
    def test_every_domain_role_can_view(self):
        for role in (TenantRole.VIEWER, TenantRole.GROWER, TenantRole.LEAD):
            assert MembershipEngine.can_view_resource(role) is True


class TestValidateNotLastManager:
    def test_safe_when_another_manager_remains(self):
        assert MembershipEngine.validate_not_last_manager(2, True) is True

    def test_unsafe_when_target_is_the_last_manager(self):
        # Removing them would strand the tenant: nobody left could invite
        # anyone, not even the people still in it.
        assert MembershipEngine.validate_not_last_manager(1, True) is False

    def test_safe_when_the_target_holds_no_management(self):
        assert MembershipEngine.validate_not_last_manager(1, False) is True

    def test_safe_when_there_are_no_managers_and_the_target_is_not_one(self):
        assert MembershipEngine.validate_not_last_manager(0, False) is True
