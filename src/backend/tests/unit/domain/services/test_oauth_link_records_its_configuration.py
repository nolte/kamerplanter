"""#1815 review SEC-001 — a provider link records the configuration and issuer it was made with.

A link stored only its *type*. With two generic OIDC configurations both links read
``oidc``, so a step-up re-authentication could be sent to — and accept a ``sub``
from — the other identity provider. The link now carries ``oidc_config_slug`` and,
where the provider issued an ID token, its ``iss``; the step-up matches a link only
to its own configuration.

Driven through ``complete_oauth`` (the linking entry) with doubled repositories and
the real engine; only the token endpoint and the user-info extraction are doubled.
"""

from __future__ import annotations

import base64
import json
from unittest.mock import MagicMock

from app.common.enums import AuthProviderType
from app.domain.engines.oauth_engine import OAuthEngine
from app.domain.models.auth import OAuthUserInfo
from app.domain.models.oidc_config import OidcProviderConfig
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService

ISSUER = "https://idp-b.example"


def _jwt(claims: dict) -> str:
    part = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    return f"h.{part}.s"


def _service(token_response: dict, config: OidcProviderConfig) -> tuple[AuthService, MagicMock]:
    existing = User(_key="u1", email="owner@example.org", display_name="Owner", email_verified=True)
    user_repo = MagicMock()
    user_repo.get_by_email.return_value = existing
    auth_provider_repo = MagicMock()
    auth_provider_repo.get_by_provider.return_value = None
    auth_provider_repo.create.side_effect = lambda row: row

    engine = MagicMock(wraps=OAuthEngine())
    engine.exchange_code_for_tokens.return_value = token_response
    engine.extract_user_info.return_value = OAuthUserInfo(
        provider=AuthProviderType.OIDC,
        provider_user_id="sub-b",
        email="owner@example.org",
        display_name="Owner",
        email_verified=True,
    )
    state_store = MagicMock()
    state_store.get_and_delete.return_value = {"provider_slug": config.slug, "code_verifier": "v", "nonce": "n"}
    config_repo = MagicMock()
    config_repo.get_by_slug.return_value = config
    token_engine = MagicMock()
    token_engine.create_refresh_token.return_value = ("raw-refresh", "refresh-hash")

    service = AuthService(
        user_repo=user_repo,
        auth_provider_repo=auth_provider_repo,
        refresh_token_repo=MagicMock(),
        password_engine=MagicMock(),
        token_engine=token_engine,
        throttle_engine=MagicMock(),
        email_service=MagicMock(),
        frontend_url="https://app.example",
        oauth_engine=engine,
        oauth_state_store=state_store,
        oidc_config_repo=config_repo,
    )
    return service, auth_provider_repo


def _config(slug: str = "corp-b") -> OidcProviderConfig:
    return OidcProviderConfig(
        slug=slug,
        display_name="Corp B",
        provider_type="oidc",
        issuer_url=ISSUER,
        client_id="cid",
        client_secret_encrypted="secret",
        enabled=True,
    )


def test_a_new_link_records_its_configuration_and_issuer() -> None:
    service, providers = _service({"access_token": "a", "id_token": _jwt({"iss": ISSUER, "sub": "sub-b"})}, _config())

    service.complete_oauth("corp-b", "code", "state")

    (row,) = [c.args[0] for c in providers.create.call_args_list]
    assert row.oidc_config_slug == "corp-b"
    assert row.issuer == ISSUER


def test_a_link_without_an_id_token_records_the_configuration_only() -> None:
    """GitHub is plain OAuth2: there is no issuer to record, but the configuration is known."""
    service, providers = _service({"access_token": "a"}, _config("github-corp"))

    service.complete_oauth("github-corp", "code", "state")

    (row,) = [c.args[0] for c in providers.create.call_args_list]
    assert row.oidc_config_slug == "github-corp"
    assert row.issuer is None
