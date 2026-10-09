"""Who may obtain a step-up factor for which target (#1884, operator decision D2).

A step-up code or re-authentication token for an act on something other than the
requester's own account (:data:`~app.domain.services.step_up_service.TARGETED_ACTIONS`)
is bound to that target. Binding alone would still mint a factor for any string the
client names; so the target is also checked **when the factor is issued**: it must
exist and be the requester's to act on. The act re-checks both when it runs — this
is the earlier of two gates, never the only one.

Authorization is decided first and existence second, so a requester who may not act
on a kind of target learns nothing about which targets of that kind exist (403 before
404). Every rule mirrors the act it guards:

* ``admin_account_update`` / ``admin_account_erasure`` — a platform admin by the
  stored membership (an active ``lead`` membership in the ``platform`` tenant, the
  predicate ``PrivacyService._require_platform_admin_membership`` applies); the
  target account exists; an erasure never targets the requester (that is the
  self-service path);
* ``tenant_deletion`` — the requester holds the lead role and the management scope
  in the tenant (``MembershipEngine.can_delete_tenant``) or is a platform admin; the
  tenant exists and is not the platform tenant, or an erasure of it is still open
  (a deletion an earlier attempt left partial is resumed by the same act);
* ``tenant_erasure_cancel`` (#2123) — the rule of ``tenant_deletion``: whoever may request a
  tenant's deletion may obtain the factor that cancels a scheduled one;
* ``provider_unlink`` — the link is one of the requester's own;
* ``oidc_provider_change`` (#1883) — a platform admin; the configuration exists, or,
  for ``new:<slug>``, no configuration uses that slug yet;
* ``admin_tenant_update`` (#2009) — a platform admin; the tenant exists and is not the
  platform tenant (which cannot be deactivated, #1021);
* ``admin_membership_removal`` (#2009) — a platform admin; the membership exists;
* ``admin_membership_role_change`` (#2032) — a platform admin; the membership exists;
* ``admin_membership_add`` (#2106) — a platform admin; the target is ``<tenant_key>|<user_key>`` and
  both exist (the membership itself does not yet);
* ``service_account_change`` (#2137) — the requester holds the ``lead`` role **and** the ``technical``
  scope in the tenant (:meth:`MembershipEngine.can_manage_service_accounts`, the rule the service-account
  routes apply). The target is the tenant's key (a creation) or ``<tenant_key>|<service_account_key>``
  (a rotation or removal); for the pair, the account is a service account with an active membership in
  that tenant. Authorization on the tenant first, so a requester who may not manage the tenant's service
  accounts learns nothing about which exist;
* ``tenant_member_removal`` / ``tenant_member_role_change`` (#2032) — the requester holds
  the ``management`` scope in the tenant the membership belongs to
  (``MembershipEngine.can_manage_members``, the predicate the routes' scope gate
  applies). An unknown membership and one of another tenant are one answer (403): the
  tenant is read off the membership, so deciding "not yours" before "unknown" is the
  only order that is no membership-existence oracle.
"""

from __future__ import annotations

from app.common.enums import TenantRole
from app.common.exceptions import DuplicateError, ForbiddenError, NotFoundError, ValidationError
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
from app.domain.interfaces.auth_provider_repository import IAuthProviderRepository
from app.domain.interfaces.membership_repository import IMembershipRepository
from app.domain.interfaces.oidc_config_repository import IOidcConfigRepository
from app.domain.interfaces.tenant_erasure_repository import ITenantErasureRepository
from app.domain.interfaces.tenant_repository import ITenantRepository
from app.domain.interfaces.user_repository import IUserRepository
from app.domain.models.oidc_config import is_valid_oidc_slug
from app.domain.models.user import User
from app.domain.services.step_up_service import NEW_OIDC_PROVIDER_TARGET_PREFIX, TARGETED_ACTIONS

_PLATFORM_TENANT_KEY = "platform"


def oidc_provider_target(config_key: str | None, *, slug: str | None = None) -> str:
    """The step-up target of an OIDC provider configuration change (#1883).

    The configuration's key for an update or a deletion; ``new:<slug>`` for a
    creation, which has no key yet.
    """
    if config_key:
        return config_key
    if not slug:
        raise ValueError("an OIDC provider target needs the configuration's key or the new slug")
    return f"{NEW_OIDC_PROVIDER_TARGET_PREFIX}{slug}"


class StepUpTargetAuthorizer:
    """The :class:`~app.domain.services.step_up_service.StepUpTargetPolicy` of the running application."""

    def __init__(
        self,
        *,
        user_repo: IUserRepository,
        membership_repo: IMembershipRepository,
        tenant_repo: ITenantRepository,
        tenant_erasure_repo: ITenantErasureRepository | None,
        auth_provider_repo: IAuthProviderRepository,
        oidc_config_repo: IOidcConfigRepository,
    ) -> None:
        self._users = user_repo
        self._memberships = membership_repo
        self._tenants = tenant_repo
        self._tenant_erasures = tenant_erasure_repo
        self._providers = auth_provider_repo
        self._oidc_configs = oidc_config_repo

    def authorize(self, requester: User, *, action: str, target: str) -> None:
        """Refuse (403/404/409/422) a factor for *action* on *target* the requester could not use."""
        if action not in TARGETED_ACTIONS:  # pragma: no cover - the verifier asks for targeted acts only
            raise ValueError(f"step-up act {action!r} has no target to authorize")
        user_key = requester.key or ""
        if action in ("admin_account_update", "admin_account_erasure"):
            self._require_platform_admin(user_key)
            if action == "admin_account_erasure" and target == user_key:
                raise ForbiddenError("You cannot delete your own account from the admin panel.")
            if self._users.get_by_key(target) is None:
                raise NotFoundError("User", target)
        elif action in ("tenant_deletion", "tenant_erasure_cancel"):
            # #2123 — cancelling a scheduled deletion is open to whoever may request one.
            self._authorize_tenant_deletion(user_key, target)
        elif action == "provider_unlink":
            if not any(link.key == target for link in self._providers.list_by_user(user_key)):
                raise NotFoundError("AuthProvider", target)
        elif action == "oidc_provider_change":
            self._require_platform_admin(user_key)
            self._authorize_oidc_provider(target)
        elif action == "admin_tenant_update":
            self._require_platform_admin(user_key)
            tenant = self._tenants.get_by_key(target)
            if tenant is None:
                raise NotFoundError("Tenant", target)
            if tenant.is_platform:
                raise ForbiddenError("The platform tenant cannot be deactivated.")
        elif action in ("admin_membership_removal", "admin_membership_role_change"):
            self._require_platform_admin(user_key)
            if self._memberships.get_by_key(target) is None:
                raise NotFoundError("Membership", target)
        elif action == "admin_membership_add":
            self._require_platform_admin(user_key)
            tenant_key, _, account_key = target.partition("|")
            if not tenant_key or not account_key or "|" in account_key:
                raise ValidationError("An admin_membership_add target is <tenant_key>|<user_key>.")
            if self._tenants.get_by_key(tenant_key) is None:
                raise NotFoundError("Tenant", tenant_key)
            if self._users.get_by_key(account_key) is None:
                raise NotFoundError("User", account_key)
        elif action in ("tenant_member_removal", "tenant_member_role_change"):
            self._authorize_tenant_member_act(user_key, target)
        elif action == "service_account_change":
            self._authorize_service_account_act(user_key, target)
        else:  # pragma: no cover - a new targeted act must be given its rule here
            raise ForbiddenError("This act cannot be confirmed here.")

    def _is_platform_admin(self, user_key: str) -> bool:
        membership = self._memberships.get_by_user_and_tenant(user_key, _PLATFORM_TENANT_KEY)
        return bool(membership and membership.is_active and membership.role == TenantRole.LEAD)

    def _require_platform_admin(self, user_key: str) -> None:
        if not self._is_platform_admin(user_key):
            raise ForbiddenError("Platform admin role required.")

    def _authorize_service_account_act(self, user_key: str, target: str) -> None:
        tenant_key, separator, account_key = target.partition("|")
        if not tenant_key or (separator and (not account_key or "|" in account_key)):
            raise ValidationError(
                "A service_account_change target is <tenant_key> or <tenant_key>|<service_account_key>."
            )
        actor = self._memberships.get_by_user_and_tenant(user_key, tenant_key)
        if not (
            actor and actor.is_active and MembershipEngine.can_manage_service_accounts(actor.role, actor.admin_scopes)
        ):
            raise ForbiddenError("Managing service accounts requires the lead role and the technical scope.")
        if not separator:
            return
        account = self._users.get_by_key(account_key)
        membership = self._memberships.get_by_user_and_tenant(account_key, tenant_key)
        if account is None or account.account_type != "service" or membership is None or not membership.is_active:
            raise NotFoundError("User", account_key)

    def _authorize_tenant_member_act(self, user_key: str, membership_key: str) -> None:
        membership = self._memberships.get_by_key(membership_key)
        actor = self._memberships.get_by_user_and_tenant(user_key, membership.tenant_key) if membership else None
        if not (actor and actor.is_active and MembershipEngine.can_manage_members(actor.admin_scopes)):
            raise ForbiddenError("Managing members requires the management scope in the membership's tenant.")

    def _authorize_tenant_deletion(self, user_key: str, tenant_key: str) -> None:
        membership = self._memberships.get_by_user_and_tenant(user_key, tenant_key)
        may_delete = bool(
            membership
            and membership.is_active
            and MembershipEngine.can_delete_tenant(membership.role, membership.admin_scopes)
        )
        if not (may_delete or self._is_platform_admin(user_key)):
            raise ForbiddenError("Deleting a tenant requires the lead role and the management scope.")
        tenant = self._tenants.get_by_key(tenant_key)
        if tenant is not None:
            if tenant.is_platform:
                raise ForbiddenError("The platform tenant cannot be deleted.")
            return
        record = (
            self._tenant_erasures.get(TenantErasureEngine.record_key(tenant_key))
            if self._tenant_erasures is not None
            else None
        )
        if record is None or record.status == "completed":
            raise NotFoundError("Tenant", tenant_key)

    def _authorize_oidc_provider(self, target: str) -> None:
        if target.startswith(NEW_OIDC_PROVIDER_TARGET_PREFIX):
            slug = target.removeprefix(NEW_OIDC_PROVIDER_TARGET_PREFIX)
            if not is_valid_oidc_slug(slug):
                raise ValidationError("The new provider's slug is not valid.")
            if self._oidc_configs.get_by_slug(slug) is not None:
                raise DuplicateError("OidcProviderConfig", "slug", slug)
            return
        if self._oidc_configs.get_by_key(target) is None:
            raise NotFoundError("OidcProviderConfig", target)
