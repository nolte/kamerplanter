"""#2249 — a malformed URL is refused by the SSRF validators, never dialed and never a 500.

``urlsplit`` raises a bare ``ValueError`` for an unclosed IPv6 bracket. Measured
against develop, every validator below let it escape: fail-closed (nothing was
dialed) but surfaced as an unhandled error instead of the validator's 422.
Numeric spellings of loopback (``0x7f.1``, ``2130706433``, ``127.1``) and IPv4
carried in IPv6 are pinned here too: they resolve to 127.0.0.1 and are refused.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from app.common.exceptions import ValidationError
from app.common.url_safety import (
    validate_ha_url,
    validate_inventree_url,
    validate_push_endpoint,
    validate_server_side_url,
    validate_storage_endpoint_url,
)

VALIDATORS: list[Callable[[str], str]] = [
    validate_server_side_url,
    validate_ha_url,
    validate_inventree_url,
    validate_push_endpoint,
    validate_storage_endpoint_url,
]
_IDS = [validator.__name__ for validator in VALIDATORS]


@pytest.mark.parametrize("validator", VALIDATORS, ids=_IDS)
@pytest.mark.parametrize("url", ["http://[::1", "https://[::1/api", "https://[fe80::1/x"])
def test_unclosed_ipv6_bracket_is_a_validation_error(validator: Callable[[str], str], url: str) -> None:
    with pytest.raises(ValidationError) as caught:
        validator(url)

    assert caught.value.details[0]["code"] in {"INVALID_URL", "INVALID_ENDPOINT"}


@pytest.mark.parametrize("validator", VALIDATORS, ids=_IDS)
@pytest.mark.parametrize("url", ["https://", "ftp://files.example/x", "javascript:alert(1)", ""])
def test_no_host_or_foreign_scheme_is_refused(validator: Callable[[str], str], url: str) -> None:
    with pytest.raises(ValidationError):
        validator(url)


@pytest.mark.parametrize("validator", VALIDATORS, ids=_IDS)
@pytest.mark.parametrize(
    "url",
    [
        "https://0x7f.1/",
        "https://2130706433/",
        "https://127.1/",
        "https://[::ffff:127.0.0.1]/",
        "https://[::1]/",
        "https://user:pw@127.0.0.1/",
    ],
)
def test_loopback_spellings_are_refused(validator: Callable[[str], str], url: str) -> None:
    with pytest.raises(ValidationError) as caught:
        validator(url)

    assert caught.value.details[0]["code"] in {
        "URL_PRIVATE_ADDRESS",
        "URL_METADATA_ADDRESS",
        "ENDPOINT_PRIVATE_ADDRESS",
    }
