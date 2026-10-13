"""#1815 — which configured providers can re-authenticate a person freshly.

A fresh re-authentication is an OpenID Connect sign-in with ``prompt=login`` and
``max_age=0`` whose ID token carries ``auth_time``. GitHub is plain OAuth2 (no ID
token at all); Apple sends no ``auth_time``. Google and a generic OIDC provider
requesting the ``openid`` scope can.
"""

from __future__ import annotations

import pytest

from app.domain.engines.oauth_engine import supports_fresh_reauth
from app.domain.models.oidc_config import OidcProviderConfig


def _config(provider_type: str, scopes: list[str] | None = None, token_url: str | None = None) -> OidcProviderConfig:
    return OidcProviderConfig(
        slug="p",
        display_name="P",
        provider_type=provider_type,
        issuer_url="https://idp.example",
        client_id="cid",
        scopes=scopes or ["openid", "email", "profile"],
        token_url=token_url
        if token_url is not None
        else ("https://idp.example/token" if provider_type == "oidc" else None),
        enabled=True,
    )


@pytest.mark.parametrize(
    ("provider_type", "scopes", "expected"),
    [
        ("google", None, True),
        ("oidc", None, True),
        ("github", ["read:user", "user:email"], False),
        ("github", None, False),
        ("apple", None, False),
        ("oidc", ["email profile"], False),
        ("GitHub", None, False),
    ],
)
def test_supports_fresh_reauth(provider_type: str, scopes: list[str] | None, expected: bool) -> None:
    assert supports_fresh_reauth(_config(provider_type, scopes)) is expected


def test_a_disabled_provider_cannot_re_authenticate() -> None:
    config = _config("google").model_copy(update={"enabled": False})

    assert supports_fresh_reauth(config) is False


def test_the_fresh_login_url_asks_for_a_new_sign_in() -> None:
    from urllib.parse import parse_qs, urlsplit

    from app.domain.engines.oauth_engine import OAuthEngine

    redirect = OAuthEngine().build_authorization_url(_config("google"), "https://api.test/cb", fresh_login=True)
    query = parse_qs(urlsplit(redirect.authorization_url).query)

    assert query["prompt"] == ["login"]
    assert query["max_age"] == ["0"]


def test_the_login_url_does_not() -> None:
    from urllib.parse import parse_qs, urlsplit

    from app.domain.engines.oauth_engine import OAuthEngine

    redirect = OAuthEngine().build_authorization_url(_config("google"), "https://api.test/cb")
    query = parse_qs(urlsplit(redirect.authorization_url).query)

    assert "prompt" not in query and "max_age" not in query


# ── review SEC-003: the ID token is trusted only because it came over TLS ──


@pytest.mark.parametrize(
    ("token_url", "expected"),
    [
        ("https://idp.example/token", True),
        ("http://idp.example/token", False),
        ("HTTP://idp.example/token", False),
    ],
)
def test_only_a_tls_token_endpoint_re_authenticates(token_url: str, expected: bool) -> None:
    assert supports_fresh_reauth(_config("oidc", token_url=token_url)) is expected


def test_a_discovered_plain_http_token_endpoint_does_not() -> None:
    config = _config("oidc").model_copy(
        update={"token_url": None, "discovery_document": {"token_endpoint": "http://idp.example/token"}}
    )

    assert supports_fresh_reauth(config) is False


def test_an_unresolvable_token_endpoint_does_not() -> None:
    config = _config("oidc").model_copy(update={"token_url": None, "discovery_document": None})

    assert supports_fresh_reauth(config) is False


# ── review SEC-004: NaN and Infinity never reach a time comparison ──


@pytest.mark.parametrize("literal", ["NaN", "Infinity", "-Infinity"])
def test_an_id_token_with_a_non_finite_number_does_not_decode(literal: str) -> None:
    import base64

    from app.domain.engines.oauth_engine import OAuthEngine

    payload = base64.urlsafe_b64encode(f'{{"sub": "s", "auth_time": {literal}}}'.encode()).rstrip(b"=").decode()

    with pytest.raises(ValueError):
        OAuthEngine.id_token_claims({"id_token": f"h.{payload}.s"})


# ── review SEC-006: the authorization URL is properly encoded ──


def test_the_authorization_url_encodes_its_parameters() -> None:
    from urllib.parse import parse_qs, urlsplit

    from app.domain.engines.oauth_engine import OAuthEngine

    redirect_uri = "https://api.test/api/v1/auth/oauth/p/callback?x=1&y=2"
    redirect = OAuthEngine().build_authorization_url(_config("google"), redirect_uri)
    url = urlsplit(redirect.authorization_url)
    query = parse_qs(url.query)

    assert query["redirect_uri"] == [redirect_uri]
    assert query["scope"] == ["openid email profile"]
    assert query["state"] == [redirect.state]
    assert query["nonce"] == [redirect.nonce]
    assert set(query) == {
        "client_id",
        "redirect_uri",
        "response_type",
        "scope",
        "state",
        "nonce",
        "code_challenge",
        "code_challenge_method",
    }
    assert "&y=2" not in url.query  # the redirect URI's own query does not leak into ours
