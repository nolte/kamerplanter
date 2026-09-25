import structlog

from app.common.exceptions import NotFoundError
from app.common.types import UserKey
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.interfaces.refresh_token_repository import IRefreshTokenRepository
from app.domain.interfaces.user_repository import IUserRepository
from app.domain.models.user import User, UserProfile, UserProfileUpdate, tombstone_email

logger = structlog.get_logger()


class UserService:
    def __init__(
        self,
        user_repo: IUserRepository,
        refresh_token_repo: IRefreshTokenRepository,
        tombstone_salt: str = "",
    ) -> None:
        self._user_repo = user_repo
        self._refresh_token_repo = refresh_token_repo
        # #1773 — salt of the subject reference ``account_deleted`` logs instead
        # of the account key (see ``ErasureEngine.log_subject``).
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

    def admin_update_user(self, user_key: UserKey, data: dict) -> User:
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
        """
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

    def delete_account(self, user_key: UserKey) -> None:
        self._user_repo.get_or_raise(user_key)

        # Revoke all sessions
        self._refresh_token_repo.revoke_all_for_user(user_key)

        # A *narrow* write, not a full-model one (#1525 SCR-003). Since
        # `ArangoUserRepository` became full-replace, a full model read before the
        # session revocation and written after it does not merely lose a concurrent
        # change — it **removes** the attribute, because the stale model carries
        # `None` for a `password_reset_token` a parallel request set in between.
        # `update_fields` re-reads the stored user inside the call, so the window
        # shrinks to that call. It does not vanish: see
        # `ArangoUserRepository.update_fields`, which is itself read-modify-write.
        self._user_repo.update_fields(
            user_key,
            {
                "is_active": False,
                "email": tombstone_email(user_key),
                "display_name": "Deleted User",
                "password_hash": None,
                "avatar_url": None,
            },
        )
        logger.info("account_deleted", subject=self._log_subject(user_key))

    def _log_subject(self, user_key: str) -> str:
        """The salted reference a log line names the account by (#1773, NFR-011)."""
        return ErasureEngine.log_subject(user_key, self._tombstone_salt)

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
