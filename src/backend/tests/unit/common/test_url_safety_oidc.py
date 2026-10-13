"""#1987 — ``validate_oidc_fetch_url``: the address classes a key endpoint may not name, whatever else is allowed."""

from __future__ import annotations

import ipaddress

import pytest

from app.common import url_safety
from app.common.exceptions import ValidationError
from app.common.url_safety import https_endpoint_problem, validate_oidc_fetch_url
from app.config.settings import settings


@pytest.fixture
def resolves_to(monkeypatch: pytest.MonkeyPatch):
    def install(*addresses: str) -> None:
        monkeypatch.setattr(
            url_safety, "_resolved_addresses", lambda host: [ipaddress.ip_address(a) for a in addresses]
        )

    return install


#: Addresses no opt-in may reach: metadata services in every spelling the stdlib files under
#: "private" or "global", and IPv4 addresses carried inside IPv6.
ALWAYS_REFUSED = [
    "169.254.169.254",
    "100.100.100.200",
    "fd00:ec2::254",
    "::ffff:169.254.169.254",
    "64:ff9b::a9fe:a9fe",
    "2002:a9fe:a9fe::1",
    "224.0.0.1",
    "0.0.0.0",
]


@pytest.mark.parametrize("address", ALWAYS_REFUSED)
@pytest.mark.parametrize("opt_in", ["allow_private", "trusted_host", "debug"])
def test_a_metadata_address_is_refused_whatever_is_opted_into(
    resolves_to, monkeypatch: pytest.MonkeyPatch, address: str, opt_in: str
) -> None:
    resolves_to(address)
    monkeypatch.setattr(settings, "debug", opt_in == "debug")

    with pytest.raises(ValidationError) as caught:
        validate_oidc_fetch_url(
            "https://idp.example/keys",
            allow_private=opt_in == "allow_private",
            trusted_host="idp.example" if opt_in == "trusted_host" else None,
        )

    assert caught.value.details[0]["code"] == "URL_PRIVATE_ADDRESS"


@pytest.mark.parametrize("address", ["10.0.0.5", "192.168.1.10", "127.0.0.1", "100.64.0.1", "fd12::1", "::1"])
def test_a_private_address_needs_an_opt_in(resolves_to, address: str) -> None:
    resolves_to(address)

    with pytest.raises(ValidationError):
        validate_oidc_fetch_url("https://idp.example/keys")
    assert validate_oidc_fetch_url("https://idp.example/keys", allow_private=True)
    assert validate_oidc_fetch_url("https://idp.example/keys", trusted_host="IDP.example")
    with pytest.raises(ValidationError):
        validate_oidc_fetch_url("https://idp.example/keys", trusted_host="other.example")


def test_a_public_address_needs_none(resolves_to) -> None:
    resolves_to("93.184.216.34", "2606:2800:220:1::1")

    assert validate_oidc_fetch_url("https://idp.example/keys")


def test_one_blocked_address_among_public_ones_refuses(resolves_to) -> None:
    resolves_to("93.184.216.34", "169.254.169.254")

    with pytest.raises(ValidationError):
        validate_oidc_fetch_url("https://idp.example/keys")


def test_an_unresolvable_host_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(host: str) -> list:
        raise OSError("no such host")

    monkeypatch.setattr(url_safety, "_resolved_addresses", fail)

    with pytest.raises(ValidationError) as caught:
        validate_oidc_fetch_url("https://idp.example/keys")

    assert caught.value.details[0]["code"] == "URL_UNRESOLVABLE"


@pytest.mark.parametrize(
    "url",
    [
        "http://idp.example/keys",
        "https://user:pw@idp.example/keys",
        "https://@idp.example/keys",
        "https:///keys",
        "//idp.example/keys",
        "javascript:alert(1)",
        "",
        "https://idp.example:99999/keys",
        "https://" + "a" * 2100,
    ],
)
def test_the_scheme_rule_refuses_these(url: str) -> None:
    assert https_endpoint_problem(url) is not None
