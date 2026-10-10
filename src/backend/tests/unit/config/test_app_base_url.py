"""``APP_BASE_URL`` must be an absolute ``http(s)://host`` URL (#2226 re-review I3).

Measured before the change: any string was accepted. A value without a scheme
(``garden.example``) parses with an empty scheme and host, so the iCal
subscription URL, the OAuth callback and the QR codes all came out as relative
paths and the iCal URL lost its ``https`` upgrade - nothing failed, every link
was simply broken. The start now fails and names the variable, never its value.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config.settings import Settings, SettingsError, load_settings


@pytest.mark.parametrize(
    "value",
    [
        "http://localhost:5173",
        "https://garden.example.org",
        "https://example.org/garden/",
        "http://127.0.0.1:8000",
        "http://[::1]:8000",
        "HTTPS://Garden.Example",
    ],
)
def test_an_absolute_http_url_is_accepted(value: str) -> None:
    assert Settings(app_base_url=value).app_base_url == value


def test_the_development_default_is_accepted() -> None:
    assert Settings().app_base_url == "http://localhost:5173"


@pytest.mark.parametrize(
    "value",
    [
        "garden.example.org",
        "garden.example.org:8443",
        "//garden.example.org",
        "ftp://garden.example.org",
        "webcal://garden.example.org",
        "https://",
        "",
    ],
)
def test_a_url_without_http_scheme_or_host_is_refused(value: str) -> None:
    with pytest.raises(ValidationError, match="APP_BASE_URL must be an absolute http"):
        Settings(app_base_url=value)


def test_the_start_names_the_variable_but_not_its_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_BASE_URL", "secret-host.internal")

    with pytest.raises(SettingsError) as raised:
        load_settings()

    assert "APP_BASE_URL" in str(raised.value)
    assert "secret-host.internal" not in str(raised.value)
