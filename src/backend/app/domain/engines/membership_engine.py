from app.common.enums import TenantRole

# Role hierarchy: admin > grower > viewer
ROLE_HIERARCHY: dict[TenantRole, int] = {
    TenantRole.VIEWER: 0,
    TenantRole.GROWER: 1,
    TenantRole.ADMIN: 2,
}


class MembershipEngine:
    """Pure logic for membership and permission operations."""

    @staticmethod
    def can_manage_members(role: TenantRole) -> bool:
        """Only admins can manage members."""
        return role == TenantRole.ADMIN

    @staticmethod
    def can_assign_role(
        assigner_role: TenantRole, target_role: TenantRole
    ) -> bool:
        """Assigner can only assign roles at or below their own level."""
        return (
            assigner_role == TenantRole.ADMIN
            and ROLE_HIERARCHY[assigner_role] >= ROLE_HIERARCHY[target_role]
        )

    @staticmethod
    def can_edit_resource(role: TenantRole) -> bool:
        """Admins and growers can edit resources."""
        return role in (TenantRole.ADMIN, TenantRole.GROWER)

    @staticmethod
    def can_view_resource(role: TenantRole) -> bool:
        """All roles can view resources."""
        return role in (TenantRole.ADMIN, TenantRole.GROWER, TenantRole.VIEWER)

    @staticmethod
    def validate_not_last_admin(
        admin_count: int, is_target_admin: bool
    ) -> bool:
        """Returns True if safe to remove/demote. False if would leave no admins."""
        if not is_target_admin:
            return True
        return admin_count > 1
