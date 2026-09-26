from app.common.exceptions import UnauthorizedError
from app.domain.engines.token_engine import TokenEngine
from app.domain.interfaces.auth_provider import IAuthProvider
from app.domain.interfaces.user_repository import IUserRepository
from app.domain.models.auth import TokenPayload
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService

_API_KEY_PREFIX = "kp_"


def is_api_key_authorization(authorization: str | None) -> bool:
    """Whether *authorization* (the raw header value) carries an API key, not a session token.

    The one place outside :meth:`FullAuthProvider.resolve_user` that tells the two
    apart, for an action that must refuse a key even when it belongs to a human
    account (#1791 review SEC-001): an API key is a long-lived M2M credential
    that cannot re-authenticate, whoever owns it.
    """
    return bool(authorization) and authorization.startswith(f"Bearer {_API_KEY_PREFIX}")


class FullAuthProvider(IAuthProvider):
    def __init__(
        self,
        token_engine: TokenEngine,
        user_repo: IUserRepository,
        auth_service: AuthService,
    ) -> None:
        self._token_engine = token_engine
        self._user_repo = user_repo
        self._auth_service = auth_service

    def resolve_user(self, authorization: str | None, *, client_ip: str | None) -> User:
        if not authorization or not authorization.startswith("Bearer "):
            raise UnauthorizedError("Missing or invalid authorization header.")

        token = authorization[7:]

        if token.startswith(_API_KEY_PREFIX):
            user = self._auth_service.authenticate_api_key(token, client_ip=client_ip)
            if user is None:
                raise UnauthorizedError("Invalid or revoked API key.")
            return user

        try:
            payload: TokenPayload = self._token_engine.decode_access_token(token)
        except ValueError as e:
            raise UnauthorizedError(str(e)) from e

        user = self._user_repo.get_by_key(payload.sub)
        if user is None or not user.is_active:
            raise UnauthorizedError("User not found or inactive.")

        return user

    def resolve_user_optional(self, authorization: str | None, *, client_ip: str | None) -> User | None:
        if not authorization or not authorization.startswith("Bearer "):
            return None

        token = authorization[7:]

        if token.startswith(_API_KEY_PREFIX):
            return self._auth_service.authenticate_api_key(token, client_ip=client_ip)

        try:
            payload: TokenPayload = self._token_engine.decode_access_token(token)
        except ValueError:
            return None

        user = self._user_repo.get_by_key(payload.sub)
        if user is None or not user.is_active:
            return None
        return user

    def is_authentication_required(self) -> bool:
        return True
