"""A malformed ``APP_BASE_URL`` warns at start and the iCal URL still works (#2226 re-review I3).

Measured before the change: any string was accepted silently. A value without a
scheme (``garden.example``) parses with an empty scheme and host, so the iCal
subscription URL came out as a relative path that no calendar app can subscribe
to, and its ``https`` upgrade never applied.

The start is deliberately *not* refused: a link-shape problem must not take the
backend down (the precedent is the start crash over an unresolvable ``HA_URL``).
Instead the start logs a structured warning naming the variable - never the
value - and the iCal URL builder supplies the missing scheme itself.
"""

from __future__ import annotations

import pytest
from structlog.testing import capture_logs

from app.api.v1.calendar.tenant_router import feed_subscription_url, public_base_url
from app.config.settings import Settings, report_app_base_url_shape

MALFORMED = [
    "garden.example.org",
    "garden.example.org:8443",
    "//garden.example.org",
    "ftp://garden.example.org",
    "",
]


class TestTheStartWarnsButDoesNotFail:
    @pytest.mark.parametrize("value", MALFORMED)
    def test_a_malformed_value_is_accepted_by_the_settings(self, value: str) -> None:
        assert Settings(app_base_url=value).app_base_url == value

    @pytest.mark.parametrize("value", MALFORMED)
    def test_a_malformed_value_logs_a_warning_without_the_value(self, value: str) -> None:
        with capture_logs() as logs:
            assert report_app_base_url_shape(value) is False

        (event,) = [e for e in logs if e["event"] == "app_base_url_not_absolute_http"]
        assert event["log_level"] == "warning"
        assert event["variable"] == "APP_BASE_URL"
        if value:
            assert all(value not in str(field) for field in event.values())

    @pytest.mark.parametrize(
        "value", ["http://localhost:5173", "https://garden.example.org", "https://example.org/garden/", "HTTPS://G.Ex"]
    )
    def test_a_well_formed_value_logs_nothing(self, value: str) -> None:
        with capture_logs() as logs:
            assert report_app_base_url_shape(value) is True

        assert [e for e in logs if e["event"] == "app_base_url_not_absolute_http"] == []

    def test_the_development_default_is_well_formed(self) -> None:
        assert report_app_base_url_shape(Settings().app_base_url) is True


class TestTheFeedUrlGetsAScheme:
    @pytest.mark.parametrize(
        ("configured", "expected"),
        [
            ("garden.example.org", "https://garden.example.org"),
            ("garden.example.org:8443/", "https://garden.example.org:8443"),
            ("//garden.example.org/garden", "https://garden.example.org/garden"),
            ("ftp://garden.example.org", "https://garden.example.org"),
            ("localhost:5173", "http://localhost:5173"),
            ("127.0.0.1:8000", "http://127.0.0.1:8000"),
            ("[::1]:8000", "http://[::1]:8000"),
        ],
    )
    def test_a_missing_scheme_is_supplied(self, configured: str, expected: str) -> None:
        assert public_base_url(configured) == expected

    @pytest.mark.parametrize(
        ("configured", "expected"),
        [
            ("http://garden.example.org/", "https://garden.example.org"),
            ("https://garden.example.org", "https://garden.example.org"),
            ("http://localhost:5173", "http://localhost:5173"),
            ("https://localhost:5173", "https://localhost:5173"),
        ],
    )
    def test_a_named_scheme_keeps_its_rules(self, configured: str, expected: str) -> None:
        assert public_base_url(configured) == expected

    def test_the_issued_url_is_absolute(self) -> None:
        url = feed_subscription_url("garden.example.org", "feed-1", "tok")

        assert url == "https://garden.example.org/api/v1/calendar/feeds/feed-1/feed.ics?token=tok"
