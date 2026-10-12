"""#1855 SEC-006 — in full mode the light-mode system account never authenticates, whatever is stored.

The start seals the account (deactivated, keys revoked); these resolvers refuse it on their own,
for the window before a start sealed it, a restored backup or a replica that still serves an older
state: an *active* stored ``system-user`` with a *valid* key or token is still refused.
"""

from __future__ import annotations

import hashlib
from unittest.mock import MagicMock

import pytest

from app.common.exceptions import UnauthorizedError
from app.domain.engines.full_auth_provider import FullAuthProvider
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.auth import ApiKey, TokenPayload
from app.domain.models.mode_switch import SYSTEM_USER_KEY, system_account_refused
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService
from app.mcp_server.auth import McpAuthenticator

RAW_KEY = "kp_" + "x" * 40


def _system_user() -> User:
    return User.model_validate(
        {"_key": SYSTEM_USER_KEY, "email": "system@kamerplanter.example", "display_name": "Gaertner", "is_active": True}
    )


def _provider() -> FullAuthProvider:
    tokens = MagicMock()
    tokens.decode_access_token.return_value = TokenPayload(sub=SYSTEM_USER_KEY, exp=0, iat=0, jti="j")
    users = MagicMock()
    users.get_by_key.return_value = _system_user()
    auth = MagicMock()
    auth.authenticate_api_key.return_value = _system_user()
    return FullAuthProvider(tokens, users, auth)


def test_the_predicate() -> None:
    assert system_account_refused(SYSTEM_USER_KEY, mode="full") is True
    assert system_account_refused(SYSTEM_USER_KEY, mode="light") is False
    assert system_account_refused("anna", mode="full") is False


@pytest.mark.parametrize("credential", ["Bearer access-token", f"Bearer {RAW_KEY}"])
def test_the_full_auth_provider_refuses_the_system_account(credential: str) -> None:
    provider = _provider()

    with pytest.raises(UnauthorizedError):
        provider.resolve_user(credential, client_ip=None)
    assert provider.resolve_user_optional(credential, client_ip=None) is None


def test_the_mcp_authenticator_refuses_the_system_account(monkeypatch) -> None:
    from app.config.settings import settings

    monkeypatch.setattr(settings, "kamerplanter_mode", "full")
    keys = MagicMock()
    keys.get_by_hash.return_value = ApiKey(
        _key="k1",
        user_key=SYSTEM_USER_KEY,
        label="mcp",
        key_hash=hashlib.sha256(RAW_KEY.encode()).hexdigest(),
        key_prefix=RAW_KEY[:8],
    )
    users = MagicMock()
    users.get_by_key.return_value = _system_user()

    with pytest.raises(UnauthorizedError):
        McpAuthenticator(keys, users, MagicMock()).authenticate(RAW_KEY)


@pytest.mark.parametrize(("light_mode", "admitted"), [(False, False), (True, True)])
def test_the_auth_service_refuses_the_system_accounts_key_in_full_mode_only(light_mode: bool, admitted: bool) -> None:
    """The key check itself, not only the provider around it: an active stored ``system-user`` with a
    live key is ``None`` in full mode and still the principal in light mode (the HA/MCP keys there)."""
    keys = MagicMock()
    keys.get_by_hash.return_value = ApiKey(
        _key="k1",
        user_key=SYSTEM_USER_KEY,
        label="ha",
        key_hash=hashlib.sha256(RAW_KEY.encode()).hexdigest(),
        key_prefix=RAW_KEY[:8],
    )
    users = MagicMock()
    users.get_by_key.return_value = _system_user()
    service = AuthService(
        user_repo=users,
        auth_provider_repo=MagicMock(),
        refresh_token_repo=MagicMock(),
        password_engine=PasswordEngine(),
        token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
        throttle_engine=LoginThrottleEngine(),
        email_service=MagicMock(),
        frontend_url="http://localhost:5173",
        api_key_repo=keys,
        light_mode=light_mode,
    )

    principal = service.authenticate_api_key(RAW_KEY, client_ip=None)

    assert (principal is not None) is admitted
    if principal is not None:
        assert principal.key == SYSTEM_USER_KEY
