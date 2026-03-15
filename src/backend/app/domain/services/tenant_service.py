from datetime import UTC, datetime

import structlog

from app.common.enums import (
    InvitationStatus,
    InvitationType,
    TenantRole,
    TenantType,
)
from app.common.exceptions import (
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.interfaces.invitation_repository import IInvitationRepository
from app.domain.interfaces.location_assignment_repository import (
    ILocationAssignmentRepository,
)
from app.domain.interfaces.membership_repository import IMembershipRepository
from app.domain.interfaces.tenant_repository import ITenantRepository
from app.domain.models.invitation import Invitation, InvitationLink
from app.domain.models.location_assignment import LocationAssignment
from app.domain.models.membership import MemberInfo, Membership
from app.domain.models.tenant import Tenant, TenantWithRole

logger = structlog.get_logger()


class TenantService:
    def __init__(
        self,
        tenant_repo: ITenantRepository,
        membership_repo: IMembershipRepository,
        invitation_repo: IInvitationRepository,
        assignment_repo: ILocationAssignmentRepository,
        tenant_engine: TenantEngine,
        membership_engine: MembershipEngine,
        invitation_engine: InvitationEngine,
    ) -> None:
        self._tenant_repo = tenant_repo
        self._membership_repo = membership_repo
        self._invitation_repo = invitation_repo
        self._assignment_repo = assignment_repo
        self._tenant_engine = tenant_engine
        self._membership_engine = membership_engine
        self._invitation_engine = invitation_engine

    # --- Tenant CRUD ---

    def create_personal_tenant(self, user_key: str, display_name: str) -> Tenant:
        """Auto-create a personal tenant during registration."""
        slug = self._tenant_engine.generate_slug(display_name)
        slug = self._ensure_unique_slug(slug)

        tenant = Tenant(
            name=display_name,
            slug=slug,
            tenant_type=TenantType.PERSONAL,
            owner_user_key=user_key,
            max_members=1,
        )
        tenant = self._tenant_repo.create(tenant)

        membership = Membership(
            user_key=user_key,
            tenant_key=tenant.key,
            role=TenantRole.ADMIN,
            is_active=True,
            joined_at=datetime.now(UTC).isoformat(),
        )
        self._membership_repo.create(membership)

        logger.info("personal_tenant_created", user_key=user_key, tenant_key=tenant.key)
        return tenant

    def create_organization(
        self, user_key: str, name: str, description: str | None = None, max_members: int = 50
    ) -> Tenant:
        """Create an organization tenant."""
        errors = self._tenant_engine.validate_tenant_name(name)
        if errors:
            raise ValidationError(errors[0])

        org_count = self._tenant_repo.count_organizations_by_owner(user_key)
        if not self._tenant_engine.can_create_organization(org_count):
            raise ValidationError("Maximum number of organizations reached")

        slug = self._tenant_engine.generate_slug(name)
        slug = self._ensure_unique_slug(slug)

        tenant = Tenant(
            name=name,
            slug=slug,
            tenant_type=TenantType.ORGANIZATION,
            description=description,
            owner_user_key=user_key,
            max_members=max_members,
        )
        tenant = self._tenant_repo.create(tenant)

        membership = Membership(
            user_key=user_key,
            tenant_key=tenant.key,
            role=TenantRole.ADMIN,
            is_active=True,
            joined_at=datetime.now(UTC).isoformat(),
        )
        self._membership_repo.create(membership)

        logger.info("organization_created", user_key=user_key, tenant_key=tenant.key)
        return tenant

    def get_tenant(self, tenant_key: str) -> Tenant:
        tenant = self._tenant_repo.get_by_key(tenant_key)
        if not tenant:
            raise NotFoundError("tenants", tenant_key)
        return tenant

    def get_tenant_by_slug(self, slug: str) -> Tenant:
        tenant = self._tenant_repo.get_by_slug(slug)
        if not tenant:
            raise NotFoundError("tenants", slug)
        return tenant

    def update_tenant(self, tenant_key: str, data: dict) -> Tenant:
        if "name" in data:
            errors = self._tenant_engine.validate_tenant_name(data["name"])
            if errors:
                raise ValidationError(errors[0])
            data["slug"] = self._tenant_engine.generate_slug(data["name"])
            data["slug"] = self._ensure_unique_slug(data["slug"], exclude_key=tenant_key)

        tenant = self._tenant_repo.update(tenant_key, data)
        if not tenant:
            raise NotFoundError("tenants", tenant_key)
        return tenant

    def delete_tenant(self, tenant_key: str) -> bool:
        self._assignment_repo.delete_all_for_tenant(tenant_key)
        self._invitation_repo.delete_all_for_tenant(tenant_key)
        self._membership_repo.delete_all_for_tenant(tenant_key)
        deleted = self._tenant_repo.delete(tenant_key)
        if not deleted:
            raise NotFoundError("tenants", tenant_key)
        logger.info("tenant_deleted", tenant_key=tenant_key)
        return True

    def list_my_tenants(self, user_key: str) -> list[TenantWithRole]:
        memberships = self._membership_repo.list_by_user(user_key)
        result: list[TenantWithRole] = []
        for m in memberships:
            if not m.is_active:
                continue
            tenant = self._tenant_repo.get_by_key(m.tenant_key)
            if tenant and tenant.is_active:
                result.append(
                    TenantWithRole(
                        key=tenant.key,
                        name=tenant.name,
                        slug=tenant.slug,
                        tenant_type=tenant.tenant_type,
                        description=tenant.description,
                        role=m.role,
                        is_active=tenant.is_active,
                    )
                )
        return result

    # --- Member Management ---

    def list_members(self, tenant_key: str) -> list[MemberInfo]:
        return self._membership_repo.list_by_tenant(tenant_key)

    def change_member_role(
        self, tenant_key: str, membership_key: str, new_role: TenantRole, actor_role: TenantRole
    ) -> Membership:
        if not self._membership_engine.can_manage_members(actor_role):
            raise ForbiddenError("Only admins can manage members")

        if not self._membership_engine.can_assign_role(actor_role, new_role):
            raise ForbiddenError("Cannot assign a role higher than your own")

        membership = self._membership_repo.get_by_key(membership_key)
        if not membership or membership.tenant_key != tenant_key:
            raise NotFoundError("memberships", membership_key)

        # Protect last admin
        if membership.role == TenantRole.ADMIN and new_role != TenantRole.ADMIN:
            admin_count = self._membership_repo.count_admins(tenant_key)
            if not self._membership_engine.validate_not_last_admin(admin_count, True):
                raise ValidationError("Cannot demote the last admin")

        result = self._membership_repo.update(membership_key, {"role": new_role})
        if not result:
            raise NotFoundError("memberships", membership_key)
        return result

    def remove_member(self, tenant_key: str, membership_key: str, actor_role: TenantRole) -> bool:
        if not self._membership_engine.can_manage_members(actor_role):
            raise ForbiddenError("Only admins can remove members")

        membership = self._membership_repo.get_by_key(membership_key)
        if not membership or membership.tenant_key != tenant_key:
            raise NotFoundError("memberships", membership_key)

        if membership.role == TenantRole.ADMIN:
            admin_count = self._membership_repo.count_admins(tenant_key)
            if not self._membership_engine.validate_not_last_admin(admin_count, True):
                raise ValidationError("Cannot remove the last admin")

        return self._membership_repo.delete(membership_key)

    def leave_tenant(self, tenant_key: str, user_key: str) -> bool:
        membership = self._membership_repo.get_by_user_and_tenant(user_key, tenant_key)
        if not membership:
            raise NotFoundError("memberships", f"user={user_key}")

        if membership.role == TenantRole.ADMIN:
            admin_count = self._membership_repo.count_admins(tenant_key)
            if not self._membership_engine.validate_not_last_admin(admin_count, True):
                raise ValidationError("Cannot leave as the last admin. Transfer ownership first.")

        return self._membership_repo.delete(membership.key)

    # --- Invitations ---

    def create_email_invitation(
        self,
        tenant_key: str,
        invited_by_user_key: str,
        email: str,
        role: TenantRole = TenantRole.VIEWER,
    ) -> InvitationLink:
        raw_token, token_hash = self._invitation_engine.create_invitation_token()
        expires_at = self._invitation_engine.calculate_expiry(days=7)

        invitation = Invitation(
            tenant_key=tenant_key,
            invited_by_user_key=invited_by_user_key,
            invitation_type=InvitationType.EMAIL,
            email=email,
            role=role,
            token_hash=token_hash,
            expires_at=expires_at.isoformat(),
        )
        invitation = self._invitation_repo.create(invitation)

        logger.info("email_invitation_created", tenant_key=tenant_key, email=email)
        return InvitationLink(
            invitation_key=invitation.key,
            token=raw_token,
            expires_at=expires_at,
        )

    def create_link_invitation(
        self,
        tenant_key: str,
        invited_by_user_key: str,
        role: TenantRole = TenantRole.VIEWER,
    ) -> InvitationLink:
        raw_token, token_hash = self._invitation_engine.create_invitation_token()
        expires_at = self._invitation_engine.calculate_expiry(days=7)

        invitation = Invitation(
            tenant_key=tenant_key,
            invited_by_user_key=invited_by_user_key,
            invitation_type=InvitationType.LINK,
            role=role,
            token_hash=token_hash,
            expires_at=expires_at.isoformat(),
        )
        invitation = self._invitation_repo.create(invitation)

        logger.info("link_invitation_created", tenant_key=tenant_key)
        return InvitationLink(
            invitation_key=invitation.key,
            token=raw_token,
            expires_at=expires_at,
        )

    def list_invitations(self, tenant_key: str) -> list[Invitation]:
        return self._invitation_repo.list_by_tenant(tenant_key)

    def revoke_invitation(self, tenant_key: str, invitation_key: str) -> Invitation:
        invitation = self._invitation_repo.get_by_key(invitation_key)
        if not invitation or invitation.tenant_key != tenant_key:
            raise NotFoundError("invitations", invitation_key)

        result = self._invitation_repo.update(invitation_key, {"status": InvitationStatus.REVOKED})
        if not result:
            raise NotFoundError("invitations", invitation_key)
        return result

    def accept_invitation(self, token: str, user_key: str) -> Membership:
        token_hash = self._invitation_engine.hash_token(token)
        invitation = self._invitation_repo.get_by_token_hash(token_hash)
        if not invitation:
            raise NotFoundError("invitations", "token")

        is_expired = self._invitation_engine.is_expired(invitation.expires_at)
        is_pending = invitation.status == InvitationStatus.PENDING
        existing = self._membership_repo.get_by_user_and_tenant(user_key, invitation.tenant_key)

        can_accept, reason = self._invitation_engine.can_accept(
            is_expired=is_expired,
            is_pending=is_pending,
            is_already_member=existing is not None,
        )
        if not can_accept:
            raise ValidationError(reason)

        # Create membership
        membership = Membership(
            user_key=user_key,
            tenant_key=invitation.tenant_key,
            role=invitation.role,
            is_active=True,
            joined_at=datetime.now(UTC).isoformat(),
        )
        membership = self._membership_repo.create(membership)

        # Mark invitation as accepted
        self._invitation_repo.update(
            invitation.key,
            {
                "status": InvitationStatus.ACCEPTED,
                "accepted_by_user_key": user_key,
                "accepted_at": datetime.now(UTC).isoformat(),
            },
        )

        logger.info(
            "invitation_accepted",
            tenant_key=invitation.tenant_key,
            user_key=user_key,
        )
        return membership

    # --- Location Assignments ---

    def list_assignments(self, tenant_key: str) -> list[LocationAssignment]:
        return self._assignment_repo.list_by_tenant(tenant_key)

    def create_assignment(
        self,
        tenant_key: str,
        membership_key: str,
        location_key: str,
        can_edit: bool = True,
        notes: str | None = None,
    ) -> LocationAssignment:
        # Verify membership belongs to tenant
        membership = self._membership_repo.get_by_key(membership_key)
        if not membership or membership.tenant_key != tenant_key:
            raise NotFoundError("memberships", membership_key)

        # Check for duplicate
        existing = self._assignment_repo.get_by_membership_and_location(membership_key, location_key)
        if existing:
            raise ValidationError("Assignment already exists")

        assignment = LocationAssignment(
            membership_key=membership_key,
            location_key=location_key,
            tenant_key=tenant_key,
            can_edit=can_edit,
            notes=notes,
        )
        return self._assignment_repo.create(assignment)

    def update_assignment(self, tenant_key: str, assignment_key: str, data: dict) -> LocationAssignment:
        assignment = self._assignment_repo.get_by_key(assignment_key)
        if not assignment or assignment.tenant_key != tenant_key:
            raise NotFoundError("location_assignments", assignment_key)

        result = self._assignment_repo.update(assignment_key, data)
        if not result:
            raise NotFoundError("location_assignments", assignment_key)
        return result

    def delete_assignment(self, tenant_key: str, assignment_key: str) -> bool:
        assignment = self._assignment_repo.get_by_key(assignment_key)
        if not assignment or assignment.tenant_key != tenant_key:
            raise NotFoundError("location_assignments", assignment_key)
        return self._assignment_repo.delete(assignment_key)

    # --- Helpers ---

    def get_membership(self, user_key: str, tenant_key: str) -> Membership | None:
        return self._membership_repo.get_by_user_and_tenant(user_key, tenant_key)

    def _ensure_unique_slug(self, slug: str, exclude_key: str | None = None) -> str:
        """Append numeric suffix if slug already exists."""
        candidate = slug
        counter = 1
        while True:
            existing = self._tenant_repo.get_by_slug(candidate)
            if existing is None:
                return candidate
            if exclude_key and existing.key == exclude_key:
                return candidate
            counter += 1
            candidate = f"{slug}-{counter}"
