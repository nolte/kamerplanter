import time

import pytest
from authlib.jose import JsonWebToken

from app.domain.engines.token_engine import TokenEngine


@pytest.fixture
def engine():
    return TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256")


class TestCreateAccessToken:
    def test_returns_token_pair(self, engine):
        pair = engine.create_access_token("user123")
        assert pair.access_token
        assert pair.token_type == "bearer"
        assert pair.expires_in == 15 * 60  # default 15 min

    def test_custom_expiry(self, engine):
        pair = engine.create_access_token("user123", expire_minutes=30)
        assert pair.expires_in == 30 * 60

    def test_tenant_roles_in_token(self, engine):
        pair = engine.create_access_token(
            "user123",
            tenant_roles={"garden-1": "admin", "garden-2": "viewer"},
        )
        payload = engine.decode_access_token(pair.access_token)
        assert payload.tenant_roles == {"garden-1": "admin", "garden-2": "viewer"}

    def test_is_platform_admin_in_token(self, engine):
        pair = engine.create_access_token("user123", is_platform_admin=True)
        payload = engine.decode_access_token(pair.access_token)
        assert payload.is_platform_admin is True

    def test_is_platform_admin_defaults_false(self, engine):
        pair = engine.create_access_token("user123")
        payload = engine.decode_access_token(pair.access_token)
        assert payload.is_platform_admin is False

    def test_no_pii_in_payload(self, engine):
        """SEC-M-001: JWT must not contain email or display_name."""
        pair = engine.create_access_token("user123")
        payload = engine.decode_access_token(pair.access_token)
        # Verify PII fields are absent from the model
        assert not hasattr(payload, "email")
        assert not hasattr(payload, "display_name")

    def test_type_field_is_access(self, engine):
        pair = engine.create_access_token("user123")
        payload = engine.decode_access_token(pair.access_token)
        assert payload.type == "access"


class TestDecodeAccessToken:
    def test_decode_valid_token(self, engine):
        pair = engine.create_access_token("user123")
        payload = engine.decode_access_token(pair.access_token)
        assert payload.sub == "user123"
        assert payload.jti  # UUID present
        assert payload.type == "access"

    def test_decode_expired_token(self, engine):
        pair = engine.create_access_token("user123", expire_minutes=0)
        time.sleep(1)
        with pytest.raises(ValueError, match="expired"):
            engine.decode_access_token(pair.access_token)

    def test_decode_invalid_token(self, engine):
        with pytest.raises(ValueError, match="Invalid"):
            engine.decode_access_token("not-a-valid-token")

    def test_decode_wrong_secret(self):
        engine1 = TokenEngine("secret-one-is-good-enough-32ch!", "HS256")
        engine2 = TokenEngine("secret-two-is-also-different-32!", "HS256")
        pair = engine1.create_access_token("user123")
        with pytest.raises(ValueError):
            engine2.decode_access_token(pair.access_token)

    def test_decode_rejects_alg_none(self, engine):
        """SEC-B1: a token with ``alg=none`` must be rejected (alg-confusion)."""
        now = int(time.time())
        claims = {
            "sub": "user123",
            "tenant_roles": {},
            "is_platform_admin": False,
            "exp": now + 900,
            "iat": now,
            "jti": "attacker-supplied-jti",
            "type": "access",
        }
        # Mint an unsigned ``alg=none`` token with a permissive encoder.
        forged = JsonWebToken(["none"]).encode({"alg": "none"}, claims, key="")
        with pytest.raises(ValueError, match="Invalid"):
            engine.decode_access_token(forged)

    def test_decode_rejects_foreign_algorithm(self, engine):
        """SEC-B1: a token signed with a different alg (HS512) is rejected."""
        secret = "test-secret-key-for-unit-tests-32chars!"
        now = int(time.time())
        claims = {
            "sub": "user123",
            "exp": now + 900,
            "iat": now,
            "jti": "x",
            "type": "access",
        }
        forged = JsonWebToken(["HS512"]).encode({"alg": "HS512"}, claims, secret)
        with pytest.raises(ValueError, match="Invalid"):
            engine.decode_access_token(forged)

    def test_decode_rejects_refresh_type(self, engine):
        """SEC-B2: a validly-signed non-``access`` token must be rejected."""
        secret = "test-secret-key-for-unit-tests-32chars!"
        now = int(time.time())
        claims = {
            "sub": "user123",
            "tenant_roles": {},
            "is_platform_admin": False,
            "exp": now + 900,
            "iat": now,
            "jti": "refresh-jti",
            "type": "refresh",
        }
        forged = JsonWebToken(["HS256"]).encode({"alg": "HS256"}, claims, secret)
        with pytest.raises(ValueError, match="Invalid token type"):
            engine.decode_access_token(forged)

    def test_decode_rejects_missing_type(self, engine):
        """SEC-B2: a token without a ``type`` claim must be rejected."""
        secret = "test-secret-key-for-unit-tests-32chars!"
        now = int(time.time())
        claims = {"sub": "user123", "exp": now + 900, "iat": now, "jti": "no-type"}
        forged = JsonWebToken(["HS256"]).encode({"alg": "HS256"}, claims, secret)
        with pytest.raises(ValueError, match="Invalid token type"):
            engine.decode_access_token(forged)

    def test_decode_rejects_tampered_signature(self, engine):
        """A token whose payload is altered fails signature verification."""
        pair = engine.create_access_token("user123")
        header, payload, signature = pair.access_token.split(".")
        tampered_payload = payload[:-1] + ("A" if payload[-1] != "A" else "B")
        tampered = f"{header}.{tampered_payload}.{signature}"
        with pytest.raises(ValueError, match="Invalid"):
            engine.decode_access_token(tampered)


class TestCreateRefreshToken:
    def test_returns_tuple(self, engine):
        raw, hashed = engine.create_refresh_token()
        assert raw
        assert hashed
        assert raw != hashed

    def test_unique_tokens(self, engine):
        raw1, _ = engine.create_refresh_token()
        raw2, _ = engine.create_refresh_token()
        assert raw1 != raw2


class TestHashToken:
    def test_deterministic(self):
        h1 = TokenEngine.hash_token("test-token")
        h2 = TokenEngine.hash_token("test-token")
        assert h1 == h2

    def test_different_inputs(self):
        h1 = TokenEngine.hash_token("token-a")
        h2 = TokenEngine.hash_token("token-b")
        assert h1 != h2
