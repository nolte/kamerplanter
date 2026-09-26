"""#1781 — ``email_digest`` is a keyed pseudonym, not a dictionary-reversible hash.

The digest stands in for an address on log lines. Unkeyed (plain sha256 over the
normalised address), anyone holding the log stream could confirm a guessed
address by hashing it — e-mail addresses are a small, enumerable space. Keyed
with the tombstone salt under its own purpose label, the digest correlates the
lines of one address and names nobody. Measured on #1781: the digest is read by
log calls only; no stored value or lookup depends on it.
"""

from __future__ import annotations

import hashlib

import pytest

from app.common.decoys import email_digest
from app.config.settings import settings

_SALT = "s" * 40


@pytest.fixture
def salted(monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setattr(settings, "log_pseudonym_salt", _SALT)
    return _SALT


def test_email_digest_is_stable_per_salt(salted: str) -> None:
    assert email_digest("a@example.org") == email_digest("  A@Example.org ")


def test_email_digest_changes_with_the_salt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "log_pseudonym_salt", "a" * 32)
    first = email_digest("a@example.org")
    monkeypatch.setattr(settings, "log_pseudonym_salt", "b" * 32)
    assert email_digest("a@example.org") != first


def test_email_digest_is_not_the_dictionary_reversible_hash(salted: str) -> None:
    unkeyed = hashlib.sha256(b"a@example.org").hexdigest()[:16]
    digest = email_digest("a@example.org")
    assert digest != unkeyed
    assert len(digest) == 16


@pytest.mark.parametrize("salt", ["", "short"])
def test_email_digest_without_a_usable_salt_is_a_constant(monkeypatch: pytest.MonkeyPatch, salt: str) -> None:
    monkeypatch.setattr(settings, "log_pseudonym_salt", salt)
    assert email_digest("a@example.org") == email_digest("b@example.org") == "unavailable"
