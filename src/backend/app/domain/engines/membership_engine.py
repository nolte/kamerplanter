"""Pure permission logic for the REQ-049 two-axis role model.

Axis 1 (:class:`TenantRole`) is ranked and decides what a member may do with
domain data. Axis 2 (:class:`AdminScope`) is additive and decides what they may
administer. Everything here is a pure function of those two values, so the rules
can be asserted directly without a request or a database.
"""

from app.common.enums import AdminScope, TenantRole

# Role hierarchy: lead > grower > viewer (REQ-049 §2.3).
ROLE_HIERARCHY: dict[TenantRole, int] = {
    TenantRole.VIEWER: 0,
    TenantRole.GROWER: 1,
    TenantRole.LEAD: 2,
}


class MembershipEngine:
    """Pure logic for membership and permission operations."""

    @staticmethod
    def can_manage_members(admin_scopes: list[AdminScope]) -> bool:
        """Member management is axis 2, not a rank.

        Deliberately blind to the domain role: the club secretary who keeps the
        member list and never touches a plant holds ``MANAGEMENT`` with the
        domain role viewer (REQ-049 §2.4).
        """
        return AdminScope.MANAGEMENT in admin_scopes

    @staticmethod
    def can_configure_integrations(admin_scopes: list[AdminScope]) -> bool:
        """The tenant's own integrations, sensors, import and enrichment sources."""
        return AdminScope.TECHNICAL in admin_scopes

    @staticmethod
    def can_assign_role(assigner_scopes: list[AdminScope], target_role: TenantRole) -> bool:
        """Whether a member may hand out ``target_role``.

        Assigning a role *is* member management, so it hangs off axis 2. There
        is deliberately no rank ceiling on the target: someone entrusted with
        the member list can appoint a lead — otherwise a tenant whose only lead
        left could never regain one.
        """
        return AdminScope.MANAGEMENT in assigner_scopes and target_role in ROLE_HIERARCHY

    @staticmethod
    def can_edit_resource(role: TenantRole) -> bool:
        """Growers and leads may create and change domain records."""
        return role in (TenantRole.LEAD, TenantRole.GROWER)

    @staticmethod
    def can_delete_resource(role: TenantRole) -> bool:
        """Only a lead may destroy domain records.

        The boundary runs along irreversibility (REQ-049 §2.3): a grower
        corrects a mistake by overwriting a value; erasing history is a
        different kind of act. REQ-024 §1a.1 always said so ("❌D" throughout) —
        the implementation is what had drifted.
        """
        return role == TenantRole.LEAD

    @staticmethod
    def can_view_resource(role: TenantRole) -> bool:
        """Every domain role may read."""
        return role in ROLE_HIERARCHY

    @staticmethod
    def validate_not_last_manager(manager_count: int, target_has_management: bool) -> bool:
        """INV-1: a tenant always keeps at least one active ``MANAGEMENT`` membership.

        Returns ``True`` when the removal or demotion is safe. Removing the last
        member who can invite anyone would strand the tenant — nobody left could
        restore access, not even the people still in it.

        Args:
            manager_count: Active memberships in the tenant holding
                ``MANAGEMENT``, the target included.
            target_has_management: Whether the membership about to be removed or
                demoted is one of them.
        """
        if not target_has_management:
            return True
        return manager_count > 1
