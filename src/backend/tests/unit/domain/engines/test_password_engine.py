import pytest

from app.domain.engines.password_engine import PasswordEngine


@pytest.fixture
def engine():
    return PasswordEngine()


class TestHashPassword:
    def test_hash_returns_bcrypt_string(self, engine):
        result = engine.hash_password("test-password-123")
        assert result.startswith("$2b$")

    def test_hash_is_different_each_time(self, engine):
        h1 = engine.hash_password("same-password-123")
        h2 = engine.hash_password("same-password-123")
        assert h1 != h2


class TestVerifyPassword:
    def test_correct_password(self, engine):
        hashed = engine.hash_password("my-secure-password")
        assert engine.verify_password("my-secure-password", hashed) is True

    def test_wrong_password(self, engine):
        hashed = engine.hash_password("my-secure-password")
        assert engine.verify_password("wrong-password-12", hashed) is False


class TestValidatePasswordPolicy:
    def test_valid_password(self, engine):
        errors = engine.validate_password_policy("a-good-password-10")
        assert errors == []

    def test_too_short(self, engine):
        errors = engine.validate_password_policy("short")
        assert len(errors) == 1
        assert "at least 10" in errors[0]

    def test_exactly_10_chars(self, engine):
        errors = engine.validate_password_policy("1234567890")
        assert errors == []

    def test_too_long(self, engine):
        errors = engine.validate_password_policy("a" * 129)
        assert len(errors) == 1
        assert "128" in errors[0]

    def test_exactly_128_chars(self, engine):
        errors = engine.validate_password_policy("a" * 128)
        assert errors == []

    def test_empty_password(self, engine):
        errors = engine.validate_password_policy("")
        assert len(errors) == 1

    def test_no_complexity_rules(self, engine):
        """NIST 800-63B: no complexity rules, just length."""
        errors = engine.validate_password_policy("aaaaaaaaaa")
        assert errors == []

    def test_unicode_password(self, engine):
        errors = engine.validate_password_policy("überpasswort!")
        assert errors == []
