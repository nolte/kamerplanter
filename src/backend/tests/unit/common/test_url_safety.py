"""Unit tests for the SSRF-hardening push-endpoint validator (SEC-001)."""

from unittest.mock import patch

import pytest

from app.common.exceptions import ValidationError
from app.common.url_safety import (
    is_safe_push_endpoint,
    validate_push_endpoint,
)


def _fake_getaddrinfo(ip: str):
    """Build a getaddrinfo replacement that always resolves to ``ip``."""

    def _resolver(host, *_args, **_kwargs):  # noqa: ANN001, ANN002, ANN003
        return [(None, None, None, "", (ip, 0))]

    return _resolver


class TestValidatePushEndpoint:
    def test_accepts_normal_https_fcm_endpoint(self) -> None:
        with patch("app.common.url_safety.socket.getaddrinfo", _fake_getaddrinfo("216.239.36.55")):
            result = validate_push_endpoint("https://fcm.googleapis.com/fcm/send/abc123")
        assert result == "https://fcm.googleapis.com/fcm/send/abc123"

    def test_rejects_http_scheme(self) -> None:
        with pytest.raises(ValidationError) as exc:
            validate_push_endpoint("http://fcm.googleapis.com/fcm/send/abc")
        assert exc.value.status_code == 422

    def test_rejects_file_scheme(self) -> None:
        with pytest.raises(ValidationError):
            validate_push_endpoint("file:///etc/passwd")

    def test_rejects_empty_endpoint(self) -> None:
        with pytest.raises(ValidationError):
            validate_push_endpoint("")

    def test_rejects_oversized_endpoint(self) -> None:
        with pytest.raises(ValidationError):
            validate_push_endpoint("https://example.com/" + "a" * 3000)

    @pytest.mark.parametrize(
        "endpoint",
        [
            "https://127.0.0.1/x",  # loopback
            "https://169.254.169.254/x",  # cloud metadata (link-local)
            "https://10.0.0.5/x",  # RFC1918 private
            "https://192.168.1.10/x",  # RFC1918 private
            "https://[::1]/x",  # IPv6 loopback
        ],
    )
    def test_rejects_internal_ip_literals(self, endpoint: str) -> None:
        # IP literals resolve to themselves — no real DNS needed.
        with pytest.raises(ValidationError) as exc:
            validate_push_endpoint(endpoint)
        assert exc.value.error_code == "VALIDATION_ERROR"

    def test_rejects_host_resolving_to_private_address(self) -> None:
        with (
            patch("app.common.url_safety.socket.getaddrinfo", _fake_getaddrinfo("10.1.2.3")),
            pytest.raises(ValidationError),
        ):
            validate_push_endpoint("https://sneaky.example.com/push")

    def test_rejects_host_resolving_to_metadata_address(self) -> None:
        with (
            patch("app.common.url_safety.socket.getaddrinfo", _fake_getaddrinfo("169.254.169.254")),
            pytest.raises(ValidationError),
        ):
            validate_push_endpoint("https://rebind.example.com/push")

    def test_rejects_unresolvable_host(self) -> None:
        def _boom(*_args, **_kwargs):  # noqa: ANN002, ANN003
            raise OSError("no such host")

        with (
            patch("app.common.url_safety.socket.getaddrinfo", _boom),
            pytest.raises(ValidationError),
        ):
            validate_push_endpoint("https://does-not-exist.invalid/push")


class TestAllowlist:
    def test_allowlist_accepts_matching_suffix(self) -> None:
        with (
            patch("app.common.url_safety.settings.pwa_push_endpoint_allowed_hosts", "googleapis.com"),
            patch("app.common.url_safety.socket.getaddrinfo", _fake_getaddrinfo("216.239.36.55")),
        ):
            assert validate_push_endpoint("https://fcm.googleapis.com/send/x") == "https://fcm.googleapis.com/send/x"

    def test_allowlist_rejects_non_matching_host(self) -> None:
        with (
            patch("app.common.url_safety.settings.pwa_push_endpoint_allowed_hosts", "googleapis.com"),
            pytest.raises(ValidationError),
        ):
            validate_push_endpoint("https://evil.example.com/send/x")


class TestIsSafePushEndpoint:
    def test_predicate_true_for_public_host(self) -> None:
        with patch("app.common.url_safety.socket.getaddrinfo", _fake_getaddrinfo("216.239.36.55")):
            assert is_safe_push_endpoint("https://fcm.googleapis.com/fcm/send/abc") is True

    def test_predicate_false_for_internal_ip(self) -> None:
        assert is_safe_push_endpoint("https://169.254.169.254/x") is False

    def test_predicate_false_for_http(self) -> None:
        assert is_safe_push_endpoint("http://example.com/x") is False

    def test_predicate_never_raises_on_garbage(self) -> None:
        assert is_safe_push_endpoint("not a url") is False
