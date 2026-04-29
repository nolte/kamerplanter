"""REQ-023 v1.10 service account + ApiKey hardening tests."""

import pytest
from pydantic import ValidationError

from app.domain.models.auth import ApiKey
from app.domain.models.user import User


class TestUserAccountType:
    def test_default_account_type_is_user(self):
        u = User(email="alice@example.com", display_name="Alice")
        assert u.account_type == "user"

    def test_service_account_type_is_accepted(self):
        u = User(
            email="ha-integration@kamerplanter.example",
            display_name="Home Assistant",
            account_type="service",
            password_hash=None,  # service accounts have no password
        )
        assert u.account_type == "service"
        assert u.password_hash is None

    def test_unknown_account_type_is_rejected(self):
        with pytest.raises(ValidationError):
            User(email="x@example.com", display_name="X", account_type="bot")  # type: ignore[arg-type]


class TestApiKeyHardening:
    def _base_kwargs(self) -> dict:
        return {
            "user_key": "u-1",
            "label": "ha-integration",
            "key_hash": "h" * 64,
            "key_prefix": "kpkapi_a",
        }

    def test_ip_allowlist_defaults_to_none(self):
        ak = ApiKey(**self._base_kwargs())
        assert ak.ip_allowlist is None
        assert ak.rate_limit_per_minute is None

    def test_ip_allowlist_accepts_list_of_cidrs(self):
        ak = ApiKey(**self._base_kwargs(), ip_allowlist=["10.0.0.0/8", "192.168.1.42/32"])
        assert ak.ip_allowlist == ["10.0.0.0/8", "192.168.1.42/32"]

    def test_rate_limit_lower_bound(self):
        with pytest.raises(ValidationError):
            ApiKey(**self._base_kwargs(), rate_limit_per_minute=0)

    def test_rate_limit_upper_bound(self):
        with pytest.raises(ValidationError):
            ApiKey(**self._base_kwargs(), rate_limit_per_minute=10001)

    def test_rate_limit_in_band(self):
        ak = ApiKey(**self._base_kwargs(), rate_limit_per_minute=120)
        assert ak.rate_limit_per_minute == 120
