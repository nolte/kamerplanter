"""Apprise URLs are secrets (#2113): sealed at rest, masked in the API, counted in the export.

An Apprise URL carries its credential in the URL itself — the Telegram bot token
in ``tgram://<token>/<chat>``, the Gotify app token, the webhook path. Until #2113
``channels.apprise.config.urls`` was stored as typed and returned by the
preferences API as stored. Now:

* **at rest** the list is Fernet ciphertext under ``config.urls_encrypted``
  (:func:`seal_config`, applied by ``ArangoNotificationPreferenceRepository`` on
  every write); the plaintext ``urls`` key exists only in memory, decrypted on
  read for the channel that sends (:func:`open_config`);
* **in the API** every URL is answered by a placeholder — its scheme and its
  1-based position, ``tgram://****#1`` (:func:`masked_urls`). A client that sends a
  placeholder back unchanged keeps the stored URL it stands for
  (:func:`resolve_masked_urls`); a new line is a new URL; a placeholder that names
  no stored URL is refused (422) instead of being stored as if it were a URL;
* **in the Art. 15 bundle** the list is replaced by its length,
  ``urls_configured`` (:func:`export_config`).

Pure functions; the encryption engine is passed in. Nothing here logs a URL.
"""

from __future__ import annotations

import re
from typing import Any

import structlog

from app.common.exceptions import ValidationError
from app.domain.engines.encryption_engine import EncryptionEngine, SecretKeyMismatchError
from app.domain.models.notification import ChannelPreference

logger = structlog.get_logger()

APPRISE_CHANNEL = "apprise"
#: The in-memory / API key of the URL list (``notification-channels.json`` contract).
URLS = "urls"
#: The stored key: Fernet ciphertext, one token per URL.
URLS_ENCRYPTED = "urls_encrypted"
#: The export key: how many URLs are configured.
URLS_CONFIGURED = "urls_configured"

_SCHEME = re.compile(r"[A-Za-z][A-Za-z0-9+.-]{0,31}")
_MASKED_URL = re.compile(r"^(?:(?P<scheme>[A-Za-z][A-Za-z0-9+.-]{0,31})://)?\*{4}#(?P<position>[0-9]{1,3})$")


def mask_url(url: object, position: int) -> str:
    """The placeholder the API shows for the stored URL at 1-based *position*."""
    scheme = url.split("://", 1)[0] if isinstance(url, str) and "://" in url else ""
    if scheme and _SCHEME.fullmatch(scheme):
        return f"{scheme}://****#{position}"
    return f"****#{position}"


def masked_urls(urls: object) -> list[str]:
    """Placeholders for a stored URL list (an unreadable shape masks to nothing)."""
    if not isinstance(urls, list):
        return []
    return [mask_url(url, index) for index, url in enumerate(urls, start=1)]


def masked_channels(channels: dict[str, ChannelPreference]) -> dict[str, ChannelPreference]:
    """A copy of *channels* whose Apprise URLs are placeholders — what the API may answer with."""
    masked = {key: pref.model_copy(deep=True) for key, pref in channels.items()}
    apprise = masked.get(APPRISE_CHANNEL)
    if apprise is not None:
        apprise.config.pop(URLS_ENCRYPTED, None)
        if URLS in apprise.config:
            apprise.config[URLS] = masked_urls(apprise.config[URLS])
    return masked


def resolve_masked_urls(submitted: object, stored: list[str]) -> object:
    """Replace every placeholder in *submitted* by the stored URL it stands for.

    A non-list is returned unchanged (the allow-list validation refuses it).

    Raises:
        ValidationError: a placeholder whose position names no stored URL, or a
            URL of another scheme — value-free, like the allow-list's refusals.
    """
    if not isinstance(submitted, list):
        return submitted
    resolved: list[object] = []
    for index, value in enumerate(submitted):
        match = _MASKED_URL.match(value) if isinstance(value, str) else None
        if match is None:
            resolved.append(value)
            continue
        position = int(match["position"])
        if not 1 <= position <= len(stored) or mask_url(stored[position - 1], position) != value:
            raise ValidationError(
                "A masked Apprise URL does not match a stored URL; enter the URL again.",
                details=[
                    {
                        "field": f"channels.apprise.config.urls[{index}]",
                        "reason": "Masked placeholder without a stored URL.",
                        "code": "APPRISE_URL_MASK_UNKNOWN",
                    }
                ],
            )
        resolved.append(stored[position - 1])
    return resolved


def seal_config(config: dict[str, Any], encryption: EncryptionEngine) -> dict[str, Any]:
    """The stored form of an Apprise channel config: ``urls`` → ``urls_encrypted``.

    A ``urls_encrypted`` the caller supplied is dropped — the ciphertext is derived
    from ``urls`` only, so it cannot carry a value that skipped validation.
    """
    sealed = {key: value for key, value in config.items() if key not in (URLS, URLS_ENCRYPTED)}
    urls = config.get(URLS)
    if isinstance(urls, list):
        sealed[URLS_ENCRYPTED] = [encryption.encrypt(url) for url in urls if isinstance(url, str)]
    return sealed


def open_config(config: dict[str, Any], encryption: EncryptionEngine) -> dict[str, Any]:
    """The in-memory form of a stored Apprise channel config: ``urls_encrypted`` → ``urls``.

    A row stored before #2113 carries plaintext ``urls`` and no ciphertext; it is
    returned as stored (v0083, or its next save, seals it). A token the configured key
    cannot open is left out and counted in the log, never shown.
    """
    if URLS_ENCRYPTED not in config:
        return dict(config)
    opened = {key: value for key, value in config.items() if key not in (URLS, URLS_ENCRYPTED)}
    urls: list[str] = []
    unreadable = 0
    tokens = config[URLS_ENCRYPTED] if isinstance(config[URLS_ENCRYPTED], list) else []
    for token in tokens:
        if not isinstance(token, str):
            unreadable += 1
            continue
        try:
            urls.append(encryption.decrypt(token))
        except SecretKeyMismatchError:
            unreadable += 1
    if unreadable:
        logger.error("apprise_urls_unreadable", unreadable_count=unreadable)
    opened[URLS] = urls
    return opened


def export_config(config: dict[str, Any]) -> dict[str, Any]:
    """The Art. 15 form of a stored Apprise channel config: the URLs as a count only."""
    if URLS not in config and URLS_ENCRYPTED not in config:
        return dict(config)
    exported = {key: value for key, value in config.items() if key not in (URLS, URLS_ENCRYPTED)}
    stored = config.get(URLS_ENCRYPTED, config.get(URLS))
    exported[URLS_CONFIGURED] = len(stored) if isinstance(stored, list) else 0
    return exported
