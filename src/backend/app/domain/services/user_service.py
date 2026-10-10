from datetime import UTC, datetime

import structlog

from app.common.enums import SecurityAuditAction, SecurityAuditVia, TenantRole
from app.common.exceptions import NotFoundError, ValidationError
from app.common.types import UserKey
from app.domain.interfaces.membership_repository import IMembershipRepository
from app.domain.interfaces.refresh_token_repository import IRefreshTokenRepository
from app.domain.interfaces.user_repository import IUserRepository
from app.domain.models.user import User, UserProfile, UserProfileUpdate
from app.domain.services.security_audit_service import SecurityAuditService
from app.domain.services.step_up_service import StepUpVerifier, default_step_up_verifier

logger = structlog.get_logger()

#: Fields whose change by an administrator is a step-up act (#1857, #1992): raising them
#: widens what the account is trusted with, lowering them can lead to the account's erasure
#: (``email_verified`` -> the unverified-account cleanup) or lock its owner out
#: (``is_active``).
_TRUST_FIELDS = ("email_verified", "is_active")

#: The security-audit action of each trust field moving to ``True`` / ``False`` (MT-014, #2111).
_TRUST_AUDIT_ACTIONS: dict[str, tuple[SecurityAuditAction, SecurityAuditAction]] = {
    "is_active": (SecurityAuditAction.ACCOUNT_REACTIVATED, SecurityAuditAction.ACCOUNT_DEACTIVATED),
    "email_verified": (SecurityAuditAction.ACCOUNT_EMAIL_VERIFIED, SecurityAuditAction.ACCOUNT_EMAIL_UNVERIFIED),
}

#: The technical tenant whose ``lead`` membership is the platform role (REQ-049 §2.5) —
#: the same lookup ``app.common.auth.is_platform_admin`` makes.
_PLATFORM_TENANT_KEY = "platform"


class UserService:
    def __init__(
        self,
        user_repo: IUserRepository,
        step_up_verifier: StepUpVerifier | None = None,
        refresh_token_repo: IRefreshTokenRepository | None = None,
        membership_repo: IMembershipRepository | None = None,
        security_audit: SecurityAuditService | None = None,
    ) -> None:
        self._user_repo = user_repo
        # MT-014 (#2111) — the persistent audit of a platform admin's change of a trust flag.
        # ``None`` only in doubles; ``get_user_service`` wires it, and the class guard
        # ``test_account_and_tenant_mutations_write_the_security_audit`` holds that it does.
        self._security_audit = security_audit
        # MT-045.4 (#2144) — who still holds the platform role when an admin deactivates one.
        # ``None`` only in doubles; the production provider wires it (pinned by a unit test).
        self._membership_repo = membership_repo
        # #2116 — a deactivation ends every session, refresh and access tokens alike, so a
        # later reactivation does not bring the old ones back. ``None`` only in doubles.
        self._refresh_token_repo = refresh_token_repo
        # #1857 — the admin's own step-up before an update that raises trust.
        self._step_up_verifier = step_up_verifier or default_step_up_verifier()

    def get_profile(self, user_key: UserKey) -> UserProfile:
        user = self._user_repo.get_or_raise(user_key)
        return self._to_profile(user)

    def update_profile(self, user_key: UserKey, update: UserProfileUpdate) -> UserProfile:
        """Apply the three profile fields a user may edit themselves.

        A narrow write (#1525 SCR-003): only the supplied fields are named, so a
        concurrent change to anything else — a password reset requested from another
        device, a login stamping ``last_login_at`` — is not carried away by this
        request's stale snapshot. ``timezone`` is deliberately still not applied;
        :class:`UserProfileUpdate` carries it and this method never did, and quietly
        starting to write it here would be a behaviour change smuggled into a
        null-semantics fix.
        """
        self._user_repo.get_or_raise(user_key)

        fields = {
            name: value
            for name, value in (
                ("display_name", update.display_name),
                ("avatar_url", update.avatar_url),
                ("locale", update.locale),
            )
            if value is not None
        }
        if not fields:
            return self._to_profile(self._user_repo.get_or_raise(user_key))

        updated = self._user_repo.update_fields(user_key, fields)
        if updated is None:  # pragma: no cover - get_or_raise above already proved it exists
            raise NotFoundError("User", user_key)
        return self._to_profile(updated)

    def get_user(self, user_key: UserKey) -> User:
        """Load one full user, raising :class:`NotFoundError` when absent.

        Used by the platform-admin path (#1018), which needs the full ``User``
        (not the trimmed :class:`UserProfile`) to build its response.
        """
        return self._user_repo.get_or_raise(user_key)

    def admin_update_user(
        self,
        user_key: UserKey,
        data: dict,
        *,
        requester: User,
        current_password: str | None,
        step_up_code: str | None,
        step_up_token: str | None,
        authenticated_with_api_key: bool,
        client_ip: str | None,
    ) -> User:
        """Apply a partial platform-admin update to one user (#1018).

        ``data`` is a partial payload passed straight to
        :meth:`IUserRepository.update_fields`, so the **caller owns the
        allow-list**: build it from a closed request schema's ``model_dump()``
        (``AdminUserUpdate``), never from a raw request body. The single endpoint
        that reaches this — ``PATCH /admin/platform/users/{key}`` — does exactly
        that, and that closedness is what keeps ``email``, ``password_hash``,
        ``account_type`` and the token/lock fields out of the payload.

        Routed here by #1018, which ended a router that wrote to the users
        collection itself (``collection.update``) — Presentation straight onto
        Persistence (NFR-001), outside the repository's model re-validation
        (#982/#996), reserved-attribute strip and 1202 → ``NotFoundError``
        mapping.

        **Step-up when a trust field changes (#1857, #1992).** ``email_verified`` is
        the trust anchor of the OAuth auto-link (``OAuthEngine.should_auto_link``):
        a hijacked admin session that verified an attacker's pre-registered account
        under a victim's address had the victim's next federated sign-in linked
        into it. Lowering it is just as much an act on another account: an
        unverified account is what ``cleanup_unverified_accounts`` erases, and a
        deactivated one cannot sign in. The rule is "a change that can lead to
        erasure or lockout of another account is a step-up act", so *any* actual
        change of ``email_verified`` or ``is_active`` passes the admin's *own*
        step-up (``requester`` — their password, the fresh re-authentication or
        the mailed code; an API key is 403, 429 when locked). A display-name edit
        and a re-send of the current values need none, so the edit form stays one
        click.

        **A lowered ``email_verified`` is recorded** (``email_verified_lowered_at``)
        so the unverified-account cleanup can tell a demoted, established account
        from an abandoned registration and never erases it.

        **Every trust field that changed leaves a security-audit row (MT-014, #2111)**
        — who changed which flag of whose account, in which direction — written after
        the store and the session revocation succeeded; a failing audit write raises
        (the rule of ``TenantService._audit_membership``).
        """
        current = self._user_repo.get_or_raise(user_key)
        if data.get("is_active") is False and current.is_active:
            self._refuse_platform_lockout(user_key, requester)
        changes_trust = any(
            data.get(field) is not None and bool(data[field]) != bool(getattr(current, field))
            for field in _TRUST_FIELDS
        )
        if changes_trust:
            self._step_up_verifier.verify(
                requester,
                action="admin_account_update",
                # #1884 — a factor obtained to verify this account confirms this one only.
                target=user_key,
                echo_ok=None,
                password=current_password,
                code=step_up_code,
                reauth_token=step_up_token,
                authenticated_with_api_key=authenticated_with_api_key,
                client_ip=client_ip,
            )
        # Only a trust field that really changes is written (#1992 review SEC-003): a form that re-sends
        # the value it loaded must not undo a verification that happened in between, nor demote an
        # account without the step-up and the marker above.
        data = {
            k: v
            for k, v in data.items()
            if k not in _TRUST_FIELDS or (v is not None and bool(v) != bool(getattr(current, k)))
        }
        if data.get("email_verified") is False and current.email_verified:
            data = {**data, "email_verified_lowered_at": datetime.now(UTC)}
        user = self._user_repo.update_fields(user_key, data)
        if not user:
            raise NotFoundError("User", user_key)
        if data.get("is_active") is False and self._refresh_token_repo is not None:
            # The flag alone already refuses the account on every request; ending the sessions
            # is what keeps a reactivation from reviving the tokens issued before (#2116).
            self._refresh_token_repo.revoke_all_for_user(user_key)
        self._audit_account(user_key, data, requester=requester)
        return user

    def _audit_account(self, user_key: UserKey, written: dict, *, requester: User) -> None:
        """Write one security-audit row per trust field *written* changed (MT-014, #2111).

        *written* is the payload that reached the store, from which a re-sent unchanged value was already
        dropped - so a row is a change, never an echo. The row names the two accounts by key only.
        """
        if self._security_audit is None:
            return
        for field, (raised, lowered) in _TRUST_AUDIT_ACTIONS.items():
            if field not in written:
                continue
            self._security_audit.record_account_change(
                action=raised if written[field] else lowered,
                via=SecurityAuditVia.PLATFORM_ADMIN,
                actor_user_key=requester.key or "",
                target_user_key=user_key,
            )

    def _refuse_platform_lockout(self, user_key: UserKey, requester: User) -> None:
        """Refuse a deactivation that leaves nobody able to administer the platform (MT-045.4, #2144).

        Two cases, both before the step-up so a refusal never asks for a password:
        the requester deactivating their own account, and deactivating an account
        holding the platform role (an active ``lead`` membership in ``platform``)
        when no *other* active account holds it. Either one used to need a database
        edit to undo. A 422 like INV-1's last-manager refusal.

        Not atomic: two admins deactivating each other at the same instant can both
        pass. Each refusal still needs a step-up per act, which makes that a
        deliberate act of two people rather than an accident.
        """
        if user_key == requester.key:
            raise ValidationError("A platform administrator cannot deactivate their own account.")
        if self._membership_repo is None:
            return
        leads = [
            m.user_key
            for m in self._membership_repo.active_memberships_of(tenant_key=_PLATFORM_TENANT_KEY)
            if m.role == TenantRole.LEAD
        ]
        if user_key not in leads:
            return
        others = [key for key in leads if key != user_key and self._is_active_account(key)]
        if not others:
            raise ValidationError("The last platform administrator cannot be deactivated.")

    def _is_active_account(self, user_key: UserKey) -> bool:
        user = self._user_repo.get_by_key(user_key)
        return bool(user and user.is_active)

    def list_all_users(self, *, offset: int | None = None, limit: int | None = None) -> list[User]:
        """Every user, newest first — the platform-admin cross-tenant listing (#1019).

        The router enriches each user with its tenant memberships via
        ``TenantService.list_user_memberships``; this method only owns the user
        read, which the platform-admin panel used to hand-write as raw AQL.
        ``offset``/``limit`` read one window (MT-035, #2131).
        """
        return self._user_repo.list_all(offset=offset, limit=limit)

    def count_users(self, *, active_only: bool = False) -> int:
        """Number of users; ``active_only`` counts only ``is_active`` ones (#1019)."""
        return self._user_repo.count(active_only=active_only)

    @staticmethod
    def _to_profile(user: User) -> UserProfile:
        return UserProfile(
            key=user.key or "",
            email=user.email,
            display_name=user.display_name,
            email_verified=user.email_verified,
            is_active=user.is_active,
            avatar_url=user.avatar_url,
            locale=user.locale,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
        )
