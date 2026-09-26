import structlog

from app.common.exceptions import NotFoundError
from app.common.types import UserKey
from app.domain.interfaces.refresh_token_repository import IRefreshTokenRepository
from app.domain.interfaces.user_repository import IUserRepository
from app.domain.models.user import User, UserProfile, UserProfileUpdate
from app.domain.services.step_up_service import StepUpVerifier, default_step_up_verifier

logger = structlog.get_logger()

#: Fields whose false -> true raises the account's trust (#1857).
_TRUST_FIELDS = ("email_verified", "is_active")


class UserService:
    def __init__(
        self,
        user_repo: IUserRepository,
        refresh_token_repo: IRefreshTokenRepository,
        tombstone_salt: str = "",
        step_up_verifier: StepUpVerifier | None = None,
    ) -> None:
        self._user_repo = user_repo
        self._refresh_token_repo = refresh_token_repo
        # #1857 — the admin's own step-up before an update that raises trust.
        self._step_up_verifier = step_up_verifier or default_step_up_verifier(tombstone_salt=tombstone_salt)
        # #1773 — kept for the DI signature; the only line that used it
        # (``account_deleted``) left with ``delete_account`` in #1813.
        self._tombstone_salt = tombstone_salt

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

        **Step-up when it raises trust (#1857).** ``email_verified`` is the trust
        anchor of the OAuth auto-link (``OAuthEngine.should_auto_link``): a
        hijacked admin session that verified an attacker's pre-registered account
        under a victim's address had the victim's next federated sign-in linked
        into it. Turning ``email_verified`` or ``is_active`` from false to true
        therefore passes the admin's *own* step-up (``requester`` — their password,
        the fresh re-authentication or the mailed code; an API key is 403, 429
        when locked). A display-name edit, a deactivation and a re-send of the
        current values need none, so the edit form stays one click.
        """
        current = self._user_repo.get_or_raise(user_key)
        raises_trust = any(data.get(field) is True and not getattr(current, field) for field in _TRUST_FIELDS)
        if raises_trust:
            self._step_up_verifier.verify(
                requester,
                action="admin_account_update",
                echo_ok=None,
                password=current_password,
                code=step_up_code,
                reauth_token=step_up_token,
                authenticated_with_api_key=authenticated_with_api_key,
                client_ip=client_ip,
            )
        user = self._user_repo.update_fields(user_key, data)
        if not user:
            raise NotFoundError("User", user_key)
        return user

    def list_all_users(self) -> list[User]:
        """Every user, newest first — the platform-admin cross-tenant listing (#1019).

        The router enriches each user with its tenant memberships via
        ``TenantService.list_user_memberships``; this method only owns the user
        read, which the platform-admin panel used to hand-write as raw AQL.
        """
        return self._user_repo.list_all()

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
