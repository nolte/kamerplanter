"""What a log line may carry about a person (#1781).

A log stream has no retention rule of its own (NFR-011): whatever it receives
outlives the account it names, the erasure that removed the account and the
erasure record proving it (R-06). A log call therefore never hands the logger a
data subject's account key, e-mail address, full IP address or an unredacted
exception text — it hands it the value of one of these helpers:

* :func:`log_subject` — the salted subject reference instead of an account key;
* :func:`loggable_error` — an exception text with the subject's key, export
  bundle keys, e-mail addresses and URL query strings masked;
* :func:`loggable_ip` — an IP truncated the NFR-011 R-03 way, i.e. no more than
  the database keeps long-term;
* ``app.common.decoys.email_digest`` — the keyed pseudonym of an address.

``tests/unit/guards/test_privacy_logs_carry_no_plaintext_subject.py`` enforces
the rule over every module under ``app/``. The salt is read from ``settings`` at
call time, so tests can monkeypatch it.
"""

from __future__ import annotations

import ipaddress
import re

from app.common.decoys import email_digest
from app.config.settings import settings
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.engines.storage.export_bundle_key import mask_export_bundle_keys

#: An e-mail address inside free text (an ``SMTPRecipientsRefused`` names the
#: refused address, a ``NotFoundError`` may name the looked-up one).
_EMAIL = re.compile(r"[A-Za-z0-9.!#$%&*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
#: A URL's query string inside free text. httpx errors embed the full request
#: URL; the weather adapters' carries the site coordinates, OpenWeatherMap's and
#: Perenual's an API key. The query ends at whitespace or a quote.
_URL_QUERY = re.compile(r"(https?://[^\s'\"?#]+)\?[^\s'\"]*")


def log_subject(user_key: str | None) -> str | None:
    """The reference a log line carries instead of *user_key*; ``None`` for no key.

    ``ErasureEngine.log_subject`` keyed with the configured tombstone salt; a
    missing or short salt yields ``anon_unavailable``, never the plaintext key.
    """
    if not user_key:
        return None
    return ErasureEngine.log_subject(user_key, settings.erasure_tombstone_salt)


def loggable_error(error: BaseException | str, *, user_key: str | None = None) -> str:
    """*error*'s text as it may reach a log line.

    The text stays — an operator needs it — with, in this order: *user_key*
    replaced by :func:`log_subject`, the account segment of every embedded
    export-bundle key masked, every e-mail address replaced by
    ``<email:{email_digest(address)}>``, and every URL query string replaced by
    ``<redacted>``.
    """
    text = error if isinstance(error, str) else str(error)
    if user_key:
        text = ErasureEngine.redact_subject(text, user_key, settings.erasure_tombstone_salt)
    text = mask_export_bundle_keys(text)
    text = _EMAIL.sub(lambda match: f"<email:{email_digest(match.group(0))}>", text)
    return _URL_QUERY.sub(r"\1?<redacted>", text)


def loggable_ip(ip: str | None) -> str | None:
    """*ip* truncated the NFR-011 R-03 way: IPv4 last octet 0, IPv6 its /48 network.

    The same truncation ``anonymize_old_ips`` applies to the stored refresh-token
    IP after 7 days, so a log line never holds more than the database keeps
    long-term. An unparsable value yields ``0.0.0.0``; ``None`` stays ``None``.
    """
    if ip is None:
        return None
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return "0.0.0.0"
    if isinstance(addr, ipaddress.IPv4Address):
        return str(ipaddress.IPv4Network(f"{addr}/24", strict=False).network_address)
    return str(ipaddress.IPv6Network(f"{addr}/48", strict=False).network_address)
