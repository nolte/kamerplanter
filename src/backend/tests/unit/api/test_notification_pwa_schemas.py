"""Schema-level input-validation tests for Web Push (PWA) requests (SEC-004)."""

import pytest
from pydantic import ValidationError as PydanticValidationError

from app.api.v1.notifications.schemas import (
    PwaSubscribeRequest,
    PwaUnsubscribeRequest,
)

_VALID_ENDPOINT = "https://fcm.googleapis.com/fcm/send/abc123"


class TestPwaSubscribeRequestSchema:
    def test_accepts_valid_payload(self) -> None:
        req = PwaSubscribeRequest(
            endpoint=_VALID_ENDPOINT,
            p256dh="BNcRdreALRFXTkOOUHK1EtK2wtaz5Ry4YfYCA_0QTpQtUbVlUls0VJXg7A8u-Ts1XbjhazAkj7I99e8QcYP7DkM",
            auth="tBHItJI5svbpez7KI4CCXg",
            user_agent="Firefox/140",
        )
        assert req.endpoint == _VALID_ENDPOINT

    def test_rejects_non_https_endpoint(self) -> None:
        with pytest.raises(PydanticValidationError):
            PwaSubscribeRequest(endpoint="http://fcm.googleapis.com/x", p256dh="abc", auth="def")

    def test_rejects_oversized_endpoint(self) -> None:
        with pytest.raises(PydanticValidationError):
            PwaSubscribeRequest(
                endpoint="https://fcm.googleapis.com/" + "a" * 3000,
                p256dh="abc",
                auth="def",
            )

    def test_rejects_oversized_p256dh(self) -> None:
        with pytest.raises(PydanticValidationError):
            PwaSubscribeRequest(endpoint=_VALID_ENDPOINT, p256dh="A" * 300, auth="def")

    def test_rejects_oversized_auth(self) -> None:
        with pytest.raises(PydanticValidationError):
            PwaSubscribeRequest(endpoint=_VALID_ENDPOINT, p256dh="abc", auth="A" * 300)

    @pytest.mark.parametrize("bad_value", ["has spaces", "has/slash", "has+plus", "has=mid=eq"])
    def test_rejects_non_base64url_p256dh(self, bad_value: str) -> None:
        with pytest.raises(PydanticValidationError):
            PwaSubscribeRequest(endpoint=_VALID_ENDPOINT, p256dh=bad_value, auth="def")

    @pytest.mark.parametrize("bad_value", ["has spaces", "has/slash", "has+plus"])
    def test_rejects_non_base64url_auth(self, bad_value: str) -> None:
        with pytest.raises(PydanticValidationError):
            PwaSubscribeRequest(endpoint=_VALID_ENDPOINT, p256dh="abc", auth=bad_value)

    def test_accepts_base64url_with_padding(self) -> None:
        req = PwaSubscribeRequest(endpoint=_VALID_ENDPOINT, p256dh="abc_-DEF==", auth="xyz-_123=")
        assert req.p256dh == "abc_-DEF=="


class TestPwaUnsubscribeRequestSchema:
    def test_accepts_valid_endpoint(self) -> None:
        req = PwaUnsubscribeRequest(endpoint=_VALID_ENDPOINT)
        assert req.endpoint == _VALID_ENDPOINT

    def test_rejects_non_https_endpoint(self) -> None:
        with pytest.raises(PydanticValidationError):
            PwaUnsubscribeRequest(endpoint="http://fcm.googleapis.com/x")

    def test_rejects_oversized_endpoint(self) -> None:
        with pytest.raises(PydanticValidationError):
            PwaUnsubscribeRequest(endpoint="https://fcm.googleapis.com/" + "a" * 3000)
