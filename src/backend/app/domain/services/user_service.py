import structlog

from app.common.exceptions import NotFoundError
from app.common.types import UserKey
from app.domain.interfaces.membership_repository import IMembershipRepository
from app.domain.interfaces.refresh_token_repository import IRefreshTokenRepository
from app.domain.interfaces.user_repository import IUserRepository
from app.domain.models.user import User, UserProfile, UserProfileUpdate

logger = structlog.get_logger()


class UserService:
    def __init__(
        self,
        user_repo: IUserRepository,
        refresh_token_repo: IRefreshTokenRepository,
        membership_repo: IMembershipRepository | None = None,
    ) -> None:
        self._user_repo = user_repo
        self._refresh_token_repo = refresh_token_repo
        # Optional so the profile-only call sites (and their tests) need no
        # membership repository. Required for the platform-admin account
        # hard-delete (#1019): the cascade removes the user's memberships before
        # the user document.
        self._membership_repo = membership_repo

    def get_profile(self, user_key: UserKey) -> UserProfile:
        user = self._user_repo.get_or_raise(user_key)
        return self._to_profile(user)

    def update_profile(self, user_key: UserKey, update: UserProfileUpdate) -> UserProfile:
        user = self._user_repo.get_or_raise(user_key)

        if update.display_name is not None:
            user.display_name = update.display_name
        if update.avatar_url is not None:
            user.avatar_url = update.avatar_url
        if update.locale is not None:
            user.locale = update.locale

        updated = self._user_repo.update(user_key, user)
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

    def delete_account_permanently(self, user_key: UserKey) -> None:
        """Hard-delete a user account and everything it owns (#1019).

        The platform-admin ``DELETE /admin/platform/users/{key}`` cascade, moved
        out of the router (which hand-wrote eight raw-AQL ``REMOVE``s past the
        service layer, NFR-001). Order matters:

        1. the user's **memberships** (+ their graph edges) are removed via
           :meth:`IMembershipRepository.delete_all_for_user`;
        2. the user document and its remaining single-user artefacts
           (auth-provider docs + edges, refresh tokens, session edges, API keys,
           preferences, onboarding state) are removed by
           :meth:`IUserRepository.delete`.

        **SEC-003 caller contract:** the REQ-025 Phase 0 / 0.5 object-storage and
        reference-index erasure must have run *before* this call — that walk
        resolves the user's tenants through the very memberships step 1 deletes.
        The router sequences the two; this method assumes storage is already
        detached.
        """
        if self._membership_repo is None:  # pragma: no cover - guarded by wiring
            raise RuntimeError(
                "UserService.delete_account_permanently requires a membership_repo; "
                "construct the service with one (see app.common.dependencies)."
            )
        self._user_repo.get_or_raise(user_key)
        self._membership_repo.delete_all_for_user(user_key)
        self._user_repo.delete(user_key)
        logger.info("account_hard_deleted", user_key=user_key)

    def delete_account(self, user_key: UserKey) -> None:
        user = self._user_repo.get_or_raise(user_key)

        # Revoke all sessions
        self._refresh_token_repo.revoke_all_for_user(user_key)

        # Soft-delete: deactivate
        user.is_active = False
        user.email = f"deleted_{user_key}@deleted.local"
        user.display_name = "Deleted User"
        user.password_hash = None
        user.avatar_url = None
        self._user_repo.update(user_key, user)
        logger.info("account_deleted", user_key=user_key)

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
