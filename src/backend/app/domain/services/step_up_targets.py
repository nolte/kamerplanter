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
* ``provider_unlink`` — the link is one of the requester's own;
* ``oidc_provider_change`` (#1883) — a platform admin; the configuration exists, or,
  for ``new:<slug>``, no configuration uses that slug yet.
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
        elif action == "tenant_deletion":
            self._authorize_tenant_deletion(user_key, target)
        elif action == "provider_unlink":
            if not any(link.key == target for link in self._providers.list_by_user(user_key)):
                raise NotFoundError("AuthProvider", target)
        elif action == "oidc_provider_change":
            self._require_platform_admin(user_key)
            self._authorize_oidc_provider(target)
        else:  # pragma: no cover - a new targeted act must be given its rule here
            raise ForbiddenError("This act cannot be confirmed here.")

    def _is_platform_admin(self, user_key: str) -> bool:
        membership = self._memberships.get_by_user_and_tenant(user_key, _PLATFORM_TENANT_KEY)
        return bool(membership and membership.is_active and membership.role == TenantRole.LEAD)

    def _require_platform_admin(self, user_key: str) -> None:
        if not self._is_platform_admin(user_key):
            raise ForbiddenError("Platform admin role required.")

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
