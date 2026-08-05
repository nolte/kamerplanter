from unittest.mock import MagicMock

import pytest

from app.api.v1.auth.csrf import set_csrf_cookie, verify_csrf
from app.common.exceptions import ForbiddenError


class TestSetCsrfCookie:
    def test_sets_cookie_and_returns_token(self):
        response = MagicMock()
        token = set_csrf_cookie(response)
        assert isinstance(token, str)
        assert len(token) > 20
        response.set_cookie.assert_called_once()
        call_kwargs = response.set_cookie.call_args
        assert call_kwargs.kwargs["key"] == "csrf_token"
        assert call_kwargs.kwargs["httponly"] is False  # Must be readable by JS
        assert call_kwargs.kwargs["secure"] is True
        assert call_kwargs.kwargs["samesite"] == "lax"

    def test_unique_tokens(self):
        r1, r2 = MagicMock(), MagicMock()
        t1 = set_csrf_cookie(r1)
        t2 = set_csrf_cookie(r2)
        assert t1 != t2


class TestVerifyCsrf:
    def _make_request(self, cookie_value: str | None, header_value: str | None) -> MagicMock:
        request = MagicMock()
        request.cookies = {}
        request.headers = {}
        if cookie_value is not None:
            request.cookies["csrf_token"] = cookie_value
        if header_value is not None:
            request.headers["x-csrf-token"] = header_value
        return request

    def test_matching_tokens(self):
        request = self._make_request("valid-token-abc", "valid-token-abc")
        verify_csrf(request)  # Should not raise

    def test_missing_cookie(self):
        request = self._make_request(None, "some-header-value")
        with pytest.raises(ForbiddenError, match="Missing CSRF token"):
            verify_csrf(request)

    def test_missing_header(self):
        request = self._make_request("some-cookie-value", None)
        with pytest.raises(ForbiddenError, match="Missing CSRF token"):
            verify_csrf(request)

    def test_both_missing(self):
        request = self._make_request(None, None)
        with pytest.raises(ForbiddenError, match="Missing CSRF token"):
            verify_csrf(request)

    def test_mismatched_tokens(self):
        request = self._make_request("token-A", "token-B")
        with pytest.raises(ForbiddenError, match="CSRF token mismatch"):
            verify_csrf(request)
