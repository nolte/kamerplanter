import base64
import json

import pytest

from app.common.enums import AuthProviderType
from app.domain.engines.oauth_engine import OAuthEngine
from app.domain.models.oidc_config import OidcProviderConfig


def _make_config(**overrides) -> OidcProviderConfig:
    defaults = {
        "slug": "test-provider",
        "display_name": "Test Provider",
        "provider_type": "oidc",
        "issuer_url": "https://auth.example.com",
        "client_id": "test-client-id",
        "client_secret_encrypted": "test-secret",
        "scopes": ["openid", "email", "profile"],
    }
    defaults.update(overrides)
    return OidcProviderConfig(**defaults)


def _make_id_token(claims: dict) -> str:
    """Build a minimal JWT-shaped id_token (header.payload.signature)."""
    header = base64.urlsafe_b64encode(json.dumps({"alg": "RS256"}).encode()).rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    signature = base64.urlsafe_b64encode(b"fake-sig").rstrip(b"=").decode()
    return f"{header}.{payload}.{signature}"


class TestBuildAuthorizationUrl:
    engine = OAuthEngine()

    def test_contains_pkce_params(self):
        config = _make_config(
            provider_type="google",
            authorization_url="https://accounts.google.com/o/oauth2/v2/auth",
        )
        result = self.engine.build_authorization_url(config, "https://app.example.com/callback")
        assert "code_challenge=" in result.authorization_url
        assert "code_challenge_method=S256" in result.authorization_url
        assert result.code_verifier
        assert result.state
        assert result.nonce

    def test_state_is_unique(self):
        config = _make_config(provider_type="google")
        r1 = self.engine.build_authorization_url(config, "https://app.example.com/cb")
        r2 = self.engine.build_authorization_url(config, "https://app.example.com/cb")
        assert r1.state != r2.state

    def test_apple_form_post(self):
        config = _make_config(provider_type="apple")
        result = self.engine.build_authorization_url(config, "https://app.example.com/cb")
        assert "response_mode=form_post" in result.authorization_url

    def test_custom_authorization_url(self):
        config = _make_config(authorization_url="https://custom.idp.com/authorize")
        result = self.engine.build_authorization_url(config, "https://app.example.com/cb")
        assert result.authorization_url.startswith("https://custom.idp.com/authorize?")

    def test_discovery_fallback(self):
        config = _make_config(
            provider_type="custom",
            discovery_document={"authorization_endpoint": "https://disc.example.com/auth"},
        )
        result = self.engine.build_authorization_url(config, "https://app.example.com/cb")
        assert result.authorization_url.startswith("https://disc.example.com/auth?")

    def test_no_url_raises(self):
        config = _make_config(provider_type="unknown")
        with pytest.raises(ValueError, match="Cannot resolve authorization URL"):
            self.engine.build_authorization_url(config, "https://app.example.com/cb")


class TestValidateState:
    def test_matching_state(self):
        assert OAuthEngine.validate_state("abc123", "abc123") is True

    def test_mismatched_state(self):
        assert OAuthEngine.validate_state("abc123", "xyz789") is False

    def test_empty_strings(self):
        assert OAuthEngine.validate_state("", "") is True


class TestShouldAutoLink:
    engine = OAuthEngine()

    def test_both_verified(self):
        assert self.engine.should_auto_link(True, True) is True

    def test_existing_not_verified(self):
        assert self.engine.should_auto_link(False, True) is False

    def test_oauth_not_verified(self):
        assert self.engine.should_auto_link(True, False) is False

    def test_neither_verified(self):
        assert self.engine.should_auto_link(False, False) is False


class TestExtractFromIdToken:
    engine = OAuthEngine()

    def test_google_id_token(self):
        id_token = _make_id_token(
            {
                "sub": "google-uid-123",
                "email": "user@gmail.com",
                "name": "Test User",
                "picture": "https://lh3.googleusercontent.com/photo.jpg",
            }
        )
        _make_config(provider_type="google", userinfo_url=None)
        # Force id_token path by not providing userinfo_url
        result = self.engine._extract_from_id_token(
            {"id_token": id_token},
            "google",
        )
        assert result.email == "user@gmail.com"
        assert result.provider_user_id == "google-uid-123"
        assert result.display_name == "Test User"
        assert result.provider == AuthProviderType.GOOGLE

    def test_apple_id_token(self):
        id_token = _make_id_token(
            {
                "sub": "apple-uid-456",
                "email": "user@privaterelay.appleid.com",
            }
        )
        result = self.engine._extract_from_id_token(
            {"id_token": id_token},
            "apple",
        )
        assert result.email == "user@privaterelay.appleid.com"
        assert result.provider == AuthProviderType.APPLE

    def test_missing_id_token_raises(self):
        with pytest.raises(ValueError, match="No id_token"):
            self.engine._extract_from_id_token({}, "google")

    def test_malformed_id_token_raises(self):
        with pytest.raises(ValueError, match="Malformed id_token"):
            self.engine._extract_from_id_token({"id_token": "not.valid"}, "google")


class TestProviderTypeMapping:
    def test_google(self):
        assert OAuthEngine._to_provider_type("google") == AuthProviderType.GOOGLE

    def test_github(self):
        assert OAuthEngine._to_provider_type("github") == AuthProviderType.GITHUB

    def test_apple(self):
        assert OAuthEngine._to_provider_type("apple") == AuthProviderType.APPLE

    def test_unknown_defaults_to_oidc(self):
        assert OAuthEngine._to_provider_type("keycloak") == AuthProviderType.OIDC


class TestResolveUrls:
    engine = OAuthEngine()

    def test_known_google_token_url(self):
        config = _make_config(provider_type="google")
        assert self.engine._resolve_token_url(config) == "https://oauth2.googleapis.com/token"

    def test_known_github_token_url(self):
        config = _make_config(provider_type="github")
        assert self.engine._resolve_token_url(config) == "https://github.com/login/oauth/access_token"

    def test_custom_token_url_override(self):
        config = _make_config(token_url="https://custom.example.com/token")
        assert self.engine._resolve_token_url(config) == "https://custom.example.com/token"

    def test_no_token_url_raises(self):
        config = _make_config(provider_type="unknown")
        with pytest.raises(ValueError, match="Cannot resolve token URL"):
            self.engine._resolve_token_url(config)

    def test_userinfo_url_none_for_unknown(self):
        config = _make_config(provider_type="unknown")
        assert self.engine._resolve_userinfo_url(config) is None
