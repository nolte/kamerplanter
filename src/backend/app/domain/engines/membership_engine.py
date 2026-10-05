"""Pure permission logic for the REQ-049 two-axis role model.

Axis 1 (:class:`TenantRole`) is ranked and decides what a member may do with
domain data. Axis 2 (:class:`AdminScope`) is additive and decides what they may
administer. Everything here is a pure function of those two values, so the rules
can be asserted directly without a request or a database.
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal

from app.common.enums import AdminScope, TenantRole

if TYPE_CHECKING:
    from app.domain.models.membership import Membership

#: What an account erasure does to one organisation the account is a member of (#2134, MT-038).
type DepartureOutcome = Literal["unaffected", "management_passes_to_lead", "orphaned"]

#: Sorts a membership without a recorded start after every recorded one.
_UNKNOWN_START = datetime.max.replace(tzinfo=UTC)

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
    def role_grant_refusal(
        *,
        target_role: TenantRole,
        current_role: TenantRole | None,
        is_own_membership: bool,
        tenant_is_platform: bool,
        actor_role: TenantRole | None,
    ) -> str | None:
        """Why handing ``target_role`` out is refused, or ``None`` when it may proceed (#2078).

        :meth:`can_assign_role` answers *whether the actor administers members*; this answers
        *whether this particular grant may stand*. Two rules, both about a role being worth more
        than the right to hand it out:

        * **Nobody raises their own role.** A step-up proves who is asking, not that they may be
          given the role; the secretary REQ-049 §2.4 describes (``management``, role viewer)
          appoints others, not herself - a self-appointed lead would hold both axes, and a lead
          holding ``management`` is exactly who may delete the tenant (REQ-024 §1a.2). Lowering
          one's own role is allowed. ``current_role`` is ``None`` for a grant that has no
          membership yet (an invitation): the rule then does not apply.
        * **``lead`` in the platform tenant is the platform role** (REQ-049 §2.5; ``is_platform_admin``
          reads it), so it is handed out only by someone who holds it - the same standard the
          platform-admin routes apply. Every other tenant keeps the REQ-049 §2.4 reading: no rank
          ceiling on what ``management`` may grant, or a tenant whose only lead left could never
          regain one.

        ``actor_role`` is the actor's role in the tenant from the *stored, active* membership
        (``None`` when there is none), never the request's claim.
        """
        if (
            is_own_membership
            and current_role is not None
            and ROLE_HIERARCHY.get(target_role, 0) > ROLE_HIERARCHY.get(current_role, 0)
        ):
            return "A member cannot raise their own role"
        if tenant_is_platform and target_role == TenantRole.LEAD and actor_role != TenantRole.LEAD:
            return "Only a platform admin can grant the lead role in the platform tenant"
        return None

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
    def can_delete_tenant(role: TenantRole, admin_scopes: list[AdminScope]) -> bool:
        """Deleting the whole tenant takes **both** axes: the lead role *and* ``management`` (#1791).

        REQ-024 §1a.2 / REQ-049 §4.2. Since #1769 a tenant deletion erases every
        tenant-scoped collection irreversibly, so it sits on the irreversibility
        boundary of axis 1 (:meth:`can_delete_resource`, REQ-049 §2.3) *and* is an
        administrative act of axis 2. The two conditions are intersected, not
        united: a viewer holding ``management`` — the club secretary REQ-049 §2.4
        describes — keeps the member list but cannot erase the garden, and a lead
        without ``management`` cannot either. Ownership (``owner_user_key``) is
        provenance, not a right, and plays no part.
        """
        return MembershipEngine.can_delete_resource(role) and AdminScope.MANAGEMENT in admin_scopes

    @staticmethod
    def can_manage_service_accounts(role: TenantRole, admin_scopes: list[AdminScope]) -> bool:
        """Creating, re-keying or removing a tenant's service account takes the lead role *and* ``technical`` (#2137).

        REQ-023 §5b / MT-041. A service account is an integration (axis 2, ``technical`` —
        :meth:`can_configure_integrations`) **and** a member that acts with its own role in the tenant,
        whose credential outlives every session: handing one out sits on the lead boundary of axis 1
        as well. Intersected like :meth:`can_delete_tenant`: a lead without ``technical`` and a technician
        who is not a lead are both refused.
        """
        return role == TenantRole.LEAD and AdminScope.TECHNICAL in admin_scopes

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

    @staticmethod
    def departure_settlement(
        leaving: Membership, others: list[Membership]
    ) -> tuple[DepartureOutcome, Membership | None]:
        """What the erasure of *leaving*'s account does to its organisation (#2134, MT-038, INV-1).

        *others* are the remaining **active** memberships of active accounts in the
        same tenant. The account erasure removes *leaving* without the INV-1 guard
        that ``remove_member`` / ``leave_tenant`` apply — a person who exercises
        Art. 17 cannot be told to hand over first — so the tenant is settled here
        instead (operator decision 2026-10-04):

        * nobody else → ``orphaned``;
        * *leaving* held ``management`` and nobody else does → the longest-serving
          remaining ``lead`` (earliest ``joined_at``; an unrecorded start sorts last,
          the membership key breaks a tie) receives it: ``management_passes_to_lead``;
          without a remaining ``lead`` → ``orphaned``;
        * otherwise → ``unaffected``.

        Returns the outcome and, for a handover, the membership that receives
        ``management``.
        """
        if not others:
            return "orphaned", None
        if not leaving.has_management or any(member.has_management for member in others):
            return "unaffected", None
        leads = [member for member in others if member.role == TenantRole.LEAD]
        if not leads:
            return "orphaned", None
        heir = min(leads, key=lambda m: (_started(m), m.key or "", m.user_key))
        return "management_passes_to_lead", heir


def _started(membership: Membership) -> datetime:
    """The membership's start as an aware instant; an unrecorded one sorts after every recorded one."""
    joined = membership.joined_at
    if joined is None:
        return _UNKNOWN_START
    return joined if joined.tzinfo is not None else joined.replace(tzinfo=UTC)
