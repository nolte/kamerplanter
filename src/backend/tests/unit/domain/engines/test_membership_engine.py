from app.common.enums import TenantRole
from app.domain.engines.membership_engine import MembershipEngine


class TestCanManageMembers:
    def test_admin_can_manage(self):
        assert MembershipEngine.can_manage_members(TenantRole.ADMIN) is True

    def test_grower_cannot_manage(self):
        assert MembershipEngine.can_manage_members(TenantRole.GROWER) is False

    def test_viewer_cannot_manage(self):
        assert MembershipEngine.can_manage_members(TenantRole.VIEWER) is False


class TestCanAssignRole:
    def test_admin_can_assign_viewer(self):
        assert MembershipEngine.can_assign_role(TenantRole.ADMIN, TenantRole.VIEWER) is True

    def test_admin_can_assign_grower(self):
        assert MembershipEngine.can_assign_role(TenantRole.ADMIN, TenantRole.GROWER) is True

    def test_admin_can_assign_admin(self):
        assert MembershipEngine.can_assign_role(TenantRole.ADMIN, TenantRole.ADMIN) is True

    def test_grower_cannot_assign(self):
        assert MembershipEngine.can_assign_role(TenantRole.GROWER, TenantRole.VIEWER) is False

    def test_viewer_cannot_assign(self):
        assert MembershipEngine.can_assign_role(TenantRole.VIEWER, TenantRole.VIEWER) is False


class TestCanEditResource:
    def test_admin_can_edit(self):
        assert MembershipEngine.can_edit_resource(TenantRole.ADMIN) is True

    def test_grower_can_edit(self):
        assert MembershipEngine.can_edit_resource(TenantRole.GROWER) is True

    def test_viewer_cannot_edit(self):
        assert MembershipEngine.can_edit_resource(TenantRole.VIEWER) is False


class TestCanViewResource:
    def test_admin_can_view(self):
        assert MembershipEngine.can_view_resource(TenantRole.ADMIN) is True

    def test_grower_can_view(self):
        assert MembershipEngine.can_view_resource(TenantRole.GROWER) is True

    def test_viewer_can_view(self):
        assert MembershipEngine.can_view_resource(TenantRole.VIEWER) is True


class TestValidateNotLastAdmin:
    def test_safe_when_multiple_admins(self):
        assert MembershipEngine.validate_not_last_admin(2, True) is True

    def test_unsafe_when_last_admin(self):
        assert MembershipEngine.validate_not_last_admin(1, True) is False

    def test_safe_when_target_not_admin(self):
        assert MembershipEngine.validate_not_last_admin(1, False) is True

    def test_safe_when_zero_admins_non_admin_target(self):
        assert MembershipEngine.validate_not_last_admin(0, False) is True
