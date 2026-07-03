"""Startup security gate tests (AP-4, INF-S5).

Covers ``insecure_default_secrets`` — the fail-fast list evaluated in the
FastAPI lifespan that refuses to boot with default/missing secrets in
production. The check now includes ``fernet_key``, ``erasure_tombstone_salt``
and the internal M2M ``internal_service_token`` in addition to the original
three (jwt/arango/timescale).
"""

import pytest

from app import main
from app.config.settings import settings

_VALID_SALT = "x" * 32


@pytest.fixture
def secure_settings(monkeypatch):
    """Set every gated secret to a secure, non-default value."""
    monkeypatch.setattr(settings, "jwt_secret_key", "a-real-jwt-secret")
    monkeypatch.setattr(settings, "arangodb_password", "a-real-arango-password")
    monkeypatch.setattr(settings, "timescaledb_enabled", False)
    monkeypatch.setattr(settings, "fernet_key", "a-real-fernet-key")
    monkeypatch.setattr(settings, "erasure_tombstone_salt", _VALID_SALT)
    monkeypatch.setattr(settings, "knowledge_service_enabled", False)
    monkeypatch.setattr(settings, "inference_service_enabled", False)
    monkeypatch.setattr(settings, "internal_service_token", "")
    return settings


def test_secure_config_yields_empty_list(secure_settings):
    assert main.insecure_default_secrets() == []


def test_default_jwt_secret_flagged(secure_settings, monkeypatch):
    monkeypatch.setattr(settings, "jwt_secret_key", "change-me-in-production-use-openssl-rand-hex-32")
    assert "jwt_secret_key" in main.insecure_default_secrets()


def test_default_arango_password_flagged(secure_settings, monkeypatch):
    monkeypatch.setattr(settings, "arangodb_password", "rootpassword")
    assert "arangodb_password" in main.insecure_default_secrets()


def test_missing_fernet_key_flagged(secure_settings, monkeypatch):
    monkeypatch.setattr(settings, "fernet_key", "")
    assert "fernet_key" in main.insecure_default_secrets()


def test_short_tombstone_salt_flagged(secure_settings, monkeypatch):
    monkeypatch.setattr(settings, "erasure_tombstone_salt", "too-short")
    assert "erasure_tombstone_salt" in main.insecure_default_secrets()


def test_exactly_32_char_salt_is_accepted(secure_settings, monkeypatch):
    monkeypatch.setattr(settings, "erasure_tombstone_salt", "y" * 32)
    assert "erasure_tombstone_salt" not in main.insecure_default_secrets()


def test_service_token_required_when_knowledge_service_enabled(secure_settings, monkeypatch):
    monkeypatch.setattr(settings, "knowledge_service_enabled", True)
    monkeypatch.setattr(settings, "internal_service_token", "")
    assert "internal_service_token" in main.insecure_default_secrets()


def test_service_token_required_when_inference_service_enabled(secure_settings, monkeypatch):
    monkeypatch.setattr(settings, "inference_service_enabled", True)
    monkeypatch.setattr(settings, "internal_service_token", "")
    assert "internal_service_token" in main.insecure_default_secrets()


def test_service_token_not_required_when_services_disabled(secure_settings):
    # Both services disabled + empty token -> not flagged.
    assert "internal_service_token" not in main.insecure_default_secrets()


def test_service_token_satisfied_when_set(secure_settings, monkeypatch):
    monkeypatch.setattr(settings, "knowledge_service_enabled", True)
    monkeypatch.setattr(settings, "internal_service_token", "a-real-token")
    assert "internal_service_token" not in main.insecure_default_secrets()
