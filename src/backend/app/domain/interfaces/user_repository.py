from abc import ABC, abstractmethod

from app.common.types import UserKey
from app.domain.models.user import User


class IUserRepository(ABC):
    @abstractmethod
    def get_by_key(self, key: UserKey) -> User | None: ...

    @abstractmethod
    def get_or_raise(self, key: UserKey) -> User: ...

    @abstractmethod
    def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    def get_by_email_verification_token(self, token: str) -> User | None:
        """The user carrying this email-verification token, or ``None`` (#1556).

        A lookup, not a check: expiry is a domain decision and stays in
        ``AuthService.verify_email``. Existed only as hand-written AQL inside the
        service until #1556, which is why ``IUserRepository`` was not the seam it
        claimed to be — a test substituting this interface could not drive the
        verification path at all without also faking an AQL cursor.

        Not indexed on the token attribute, so this is a collection scan (a
        property of user count, not of the caller).
        """

    @abstractmethod
    def get_by_password_reset_token(self, token: str) -> User | None:
        """The user carrying this password-reset token, or ``None`` (#1556).

        The reset-path twin of :meth:`get_by_email_verification_token`; expiry and
        the service-account refusal stay in ``AuthService.reset_password``.
        """

    @abstractmethod
    def create(self, user: User) -> User: ...

    @abstractmethod
    def update(self, key: UserKey, user: User) -> User: ...

    @abstractmethod
    def update_fields(self, key: UserKey, fields: dict) -> User | None:
        """Apply a partial field update to one user (#1018, mirrors #968 §2).

        Named ``update_fields`` rather than ``update`` because that is what it
        is: ``fields`` is a partial payload, not a full model. Callers MUST build
        ``fields`` from named fields or a validated schema's ``model_dump()``,
        never from a raw request body — the payload is applied key-by-key and
        ``model_copy(update=...)`` does not validate, so the re-validation of the
        merged model (#968) is what catches an ill-typed declared field.

        Returns ``None`` when no user carries ``key``.
        """

    @abstractmethod
    def delete(self, key: UserKey) -> bool:
        """Delete a user and the artefacts the account solely owns.

        Runs the ``account_cascade`` slice of the declared erasure plan: the
        user's auth-provider docs + edges, refresh tokens, session edges, API
        keys + edges, preferences and onboarding state, then the user document.
        Memberships and the anonymisation rules are *not* applied here — a full
        account deletion goes through ``PrivacyService.erase_account``, which
        runs the whole plan (#1664).
        """

    @abstractmethod
    def list_all(self) -> list[User]:
        """Every user, newest first (platform-admin listing, #1019)."""

    @abstractmethod
    def count(self, *, active_only: bool = False) -> int:
        """Number of user documents; ``active_only`` counts ``is_active`` ones (#1019)."""

    @abstractmethod
    def get_unverified_before(self, cutoff_iso: str) -> list[User]: ...
