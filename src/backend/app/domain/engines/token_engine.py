import hashlib
import secrets
import time
import uuid

from authlib.jose import jwt as authlib_jwt
from authlib.jose.errors import DecodeError, ExpiredTokenError

from app.domain.models.auth import TokenPair, TokenPayload


class TokenEngine:
    """Pure logic for JWT access tokens and refresh token generation."""

    def __init__(self, secret_key: str, algorithm: str = "HS256") -> None:
        self._secret_key = secret_key
        self._algorithm = algorithm

    def create_access_token(
        self,
        user_key: str,
        expire_minutes: int = 15,
        tenant_roles: dict[str, str] | None = None,
        is_platform_admin: bool = False,
    ) -> TokenPair:
        now = int(time.time())
        payload = {
            "sub": user_key,
            "tenant_roles": tenant_roles or {},
            "is_platform_admin": is_platform_admin,
            "exp": now + (expire_minutes * 60),
            "iat": now,
            "jti": str(uuid.uuid4()),
            "type": "access",
        }
        header = {"alg": self._algorithm}
        token = authlib_jwt.encode(header, payload, self._secret_key)
        return TokenPair(
            access_token=token.decode("utf-8") if isinstance(token, bytes) else str(token),
            expires_in=expire_minutes * 60,
        )

    def decode_access_token(self, token: str) -> TokenPayload:
        """Decode and validate a JWT access token. Raises on invalid/expired."""
        try:
            claims = authlib_jwt.decode(token, self._secret_key)
            claims.validate()
        except ExpiredTokenError as e:
            raise ValueError("Token has expired.") from e
        except (DecodeError, Exception) as e:
            raise ValueError("Invalid token.") from e

        return TokenPayload(
            sub=claims["sub"],
            tenant_roles=claims.get("tenant_roles", {}),
            is_platform_admin=claims.get("is_platform_admin", False),
            exp=claims["exp"],
            iat=claims["iat"],
            jti=claims["jti"],
            type=claims.get("type", "access"),
        )

    def create_refresh_token(self) -> tuple[str, str]:
        """Generate a random refresh token. Returns (raw_token, token_hash)."""
        raw = secrets.token_urlsafe(64)
        hashed = self.hash_token(raw)
        return raw, hashed

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()
