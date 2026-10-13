"""The path-credential masking covers Apprise-native URLs, dotted chains and more token shapes (#1927, NFR-011 L-6).

#1879 masked the three named HTTP shapes and any ``/``-anchored segment of at least 32
token characters that mixes case with digits or is hex. Left readable: an Apprise-native
URL as a user configures it (``slack://<a>/<b>/<c>``, ``pover://<user>@<app>``,
``gotify://host/<token>``), the part of a dotted token chain after its first ``.`` (the
attachment token is ``<body>.<signature>``; a JWT has three parts), and three token
alphabets (base36 lower case, base32 upper case plus digits, mixed case without digits).

**What reaches a sink — measured, not assumed.** The real ``apprise`` package (installed
ephemerally; it is not a dependency of the backend) abbreviates every URL it logs itself
(``Loaded Slack URL: slack://T...h/B...h/a...x//``, ``Could not load Slack URL:
slack://T...A/T...B/``); no ``app/`` log call names a user's Apprise URL. At ``DEBUG``,
however, Apprise logs the request payload, and ``Pushover Payload: {'token': '<app
token>', 'user': '<user key>'}`` is not a URL at all: the ``apprise`` logger is therefore
held at WARNING like the other request-logging libraries. The native-URL and chain masks
below are defence in depth for a URL that reaches a text through an exception.

The probe values are assembled at run time (secret scanner).
"""

from __future__ import annotations

import logging

import pytest

from app.common.log_privacy import loggable_error, loggable_text, loggable_url_text, mask_path_credentials
from app.config.logging import harden_library_loggers
from tests.unit.guards.test_log_redaction_has_no_residual_gaps import _late_handler
from tests.unit.guards.test_logs_carry_no_secrets_runtime import (  # noqa: F401  (fixture, used via usefixtures)
    _configure,
    isolated_logging,
)

_A = "".join(("Tok", "enAAAAAAAAAAAAAAAAAAA", "1"))
_B = "".join(("Tok", "enBBBBBBBBBBBBBBBBBBB", "2"))
_C = "".join(("Tok", "enCCCCCCCCCCCCCCCCCCC", "3"))
_USER = "u" * 30
_APP = "a" * 30
_SHORT_TOKEN = "k" * 15
_BODY = "eyJvcCI6ImRvd25sb2FkIiwia2V5IjoiYWJjMTIzIiwiZXhwIjoxNzkwMDAwMDAwfQ"
_SIG = "x9Yz" * 10 + "abc"
_BASE36 = "k3j2h4g5f6d7s8a9q1w2e3r4t5y6u7i8o9p0"
_BASE32 = "ABCDEFGHIJKLMNOP2345672ABCDEFGHIJ"
_MIXED_NO_DIGIT = "AbCdEfGhIjKlMnOpQrStUvWxYzAbCdEfGh"

NATIVE_URLS = {
    "slack": (f"slack://{_A}/{_B}/{_C}", (_A, _B, _C)),
    "pover": (f"pover://{_USER}@{_APP}", (_USER, _APP)),
    "pushover": (f"pushover://{_USER}@{_APP}/device", (_USER, _APP)),
    "tgram": (f"tgram://123456789:{_A}/-1001234", (_A,)),
    "telegram": (f"telegram://123456789:{_A}", (_A,)),
    "discord": (f"discord://{'1879' * 4}/{_A}", (_A, "1879" * 4)),
    "gotify": (f"gotify://gotify.example.org/{_SHORT_TOKEN}", (_SHORT_TOKEN,)),
    "gotifys": (f"gotifys://gotify.example.org:8443/{_SHORT_TOKEN}?priority=high", (_SHORT_TOKEN,)),
    "ntfy": ("ntfy://ntfy.example.org/a-private-topic-name", ("a-private-topic-name",)),
    "matrixs": ("matrixs://matrix.example.org/#room-secret:matrix.example.org", ("room-secret",)),
}
CHAINS = {
    "attachment token": (f"/api/v1/attachments/token/{_BODY}.{_SIG}", (_BODY, _SIG)),
    "jwt": (f"/cb/{_BODY}.{_BODY[:40]}.{_SIG}", (_BODY[:40], _SIG)),
}
SHAPES = {
    "base36 lower case": (f"/hook/{_BASE36}/deliver", _BASE36),
    "base32 upper case": (f"/hook/{_BASE32}/deliver", _BASE32),
    "mixed case without digits": (f"/hook/{_MIXED_NO_DIGIT}/deliver", _MIXED_NO_DIGIT),
}
SINKS = [loggable_error, loggable_text, loggable_url_text, mask_path_credentials]


@pytest.mark.parametrize("scheme", sorted(NATIVE_URLS))
@pytest.mark.parametrize("sink", SINKS)
def test_an_apprise_native_url_is_masked_after_the_scheme(scheme: str, sink) -> None:  # type: ignore[no-untyped-def]
    url, secrets = NATIVE_URLS[scheme]

    masked = sink(f"Could not load URL: {url} (retrying)")

    for secret in secrets:
        assert secret not in masked, masked
    assert f"{scheme}://" in masked, masked
    assert masked.endswith("(retrying)"), masked


def test_a_host_first_scheme_keeps_the_host_an_operator_needs() -> None:
    masked = loggable_text(f"failed: {NATIVE_URLS['gotify'][0]}")

    assert "gotify.example.org" in masked, masked


@pytest.mark.parametrize("name", sorted(CHAINS))
@pytest.mark.parametrize("sink", SINKS)
def test_a_dotted_token_chain_is_masked_whole(name: str, sink) -> None:  # type: ignore[no-untyped-def]
    text, secrets = CHAINS[name]

    masked = sink(f"GET {text} failed")

    for secret in secrets:
        assert secret not in masked, masked
    assert masked.endswith("failed"), masked


@pytest.mark.parametrize("name", sorted(SHAPES))
@pytest.mark.parametrize("sink", SINKS)
def test_other_token_alphabets_are_masked(name: str, sink) -> None:  # type: ignore[no-untyped-def]
    text, secret = SHAPES[name]

    masked = sink(f"POST {text}")

    assert secret not in masked, masked
    assert masked.startswith("POST /hook/"), masked
    assert masked.endswith("/deliver"), masked


@pytest.mark.parametrize(
    "text",
    [
        "/data/migrations/v0056_backfill_user_key_on_three_models.py",
        "/docs/internationalization-and-localization-settings-reference/",
        "/static/" + "abcdefghijklmnopqrstuvwxyz" * 2,
        "/api/v1/t/{tenant_slug}/attachments/{attachment_key}/download-original-variant",
        "https://example.org/blog/2026/10/why-we-masked-every-token-shaped-segment",
        "see slack:// for the scheme",
        "gotify:// alone",
        "version 3.14.0.1 of the library",
        "/report/summary.v2.final.pdf",
    ],
)
@pytest.mark.parametrize("sink", SINKS)
def test_ordinary_text_is_left_alone(text: str, sink) -> None:  # type: ignore[no-untyped-def]
    assert sink(text) == text


@pytest.mark.parametrize("sink", SINKS)
def test_masking_is_idempotent(sink) -> None:  # type: ignore[no-untyped-def]
    text = "  ".join(url for url, _ in NATIVE_URLS.values()) + f" /t/{_BODY}.{_SIG} /hook/{_BASE36}"
    once = sink(text)
    assert sink(once) == once


@pytest.mark.usefixtures("isolated_logging")
@pytest.mark.parametrize("process", ["api", "worker"])
def test_the_real_log_path_masks_a_native_url_in_an_exception(process: str) -> None:
    """A library logger, a text that names a user's URL: the record factory and the handler redact it."""
    _configure(process)
    late = _late_handler("somelib")
    url, secrets = NATIVE_URLS["slack"]

    try:
        raise ValueError(f"bad target {url}")
    except ValueError as exc:
        logging.getLogger("somelib").error("send failed for %s: %s", url, exc, exc_info=True)

    text = late.stream.getvalue()
    assert "send failed" in text, text
    for secret in secrets:
        assert secret not in text, text


@pytest.mark.usefixtures("isolated_logging")
def test_the_apprise_logger_is_held_at_warning() -> None:
    """Apprise logs the request payload (``token``, ``user``) at DEBUG; the logger stays above that."""
    logging.getLogger("apprise").setLevel(logging.NOTSET)

    harden_library_loggers()

    assert logging.getLogger("apprise").level >= logging.WARNING


def test_every_scheme_the_channel_delivers_to_is_masked() -> None:
    """The class is the allow-list in ``url_safety``, not the schemes this file lists."""
    from app.common.url_safety import APPRISE_ALLOWED_SCHEMES

    for scheme in sorted(APPRISE_ALLOWED_SCHEMES):
        masked = loggable_text(f"x {scheme}://{_A}/{_B}/{_C} y")
        # A server-first scheme keeps its authority (the host), whatever it looks like.
        assert _B not in masked and _C not in masked, (scheme, masked)
        assert f"{scheme}://" in masked, (scheme, masked)
