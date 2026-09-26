"""#1859 — the Celery worker refuses to start without a usable FERNET_KEY, like the API.

The API refuses to start with ``DEBUG`` off and no ``FERNET_KEY``
(``app.main.insecure_default_secrets``). The worker never imports ``app.main``.
Without a check of its own it built ``EncryptionEngine("")``, whose plaintext
passthrough wrote encrypted-at-rest fields (OIDC client secrets, integration
tokens) in clear and handed ciphertext to integrations as their credential,
after one warning line.

The check is a ``celeryd_init`` receiver raising ``SystemExit``, the same
mechanism as #1781's salt gate. Celery's ``Signal.send`` only logs an
``Exception`` from a receiver, so the tests send the **real** signal: a receiver
that raised a swallowed type, or was never connected, fails here.

A malformed key is refused too. ``Fernet(key)`` raises on it, and the worker
would otherwise fail on the first task that touches a secret instead of at
start.

Traces to issue #1859 (no TC-ID: process start-up is not a user-facing case).
"""

from __future__ import annotations

import base64

import pytest
from celery.signals import celeryd_init

import app.tasks  # noqa: F401  importing the package is what connects the receivers
from app.config.settings import settings

# Assembled at runtime (BACKEND.md §16.3): a key-shaped literal is a scanner hit.
_VALID_KEY = base64.urlsafe_b64encode(bytes(range(32))).decode()


@pytest.fixture(autouse=True)
def _sane_start(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the sibling receivers inert: a valid salt, no DSN, no SDK initialisation."""
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    monkeypatch.setattr(settings, "erasure_tombstone_salt", "x" * 32)


def _errors(responses: list) -> list:
    return [r for _receiver, r in responses if isinstance(r, BaseException)]


@pytest.mark.parametrize("key", ["", "not-a-fernet-key", "x" * 44], ids=["empty", "short", "not-base64-32"])
def test_worker_start_without_a_usable_key_exits_when_not_debug(monkeypatch: pytest.MonkeyPatch, key: str) -> None:
    monkeypatch.setattr(settings, "debug", False)
    monkeypatch.setattr(settings, "fernet_key", key)

    with pytest.raises(SystemExit) as excinfo:
        celeryd_init.send(sender="worker@test", conf=None, instance=None)

    assert "FERNET_KEY" in str(excinfo.value)
    assert key not in str(excinfo.value) or not key  # the refusal never echoes the key


def test_worker_start_with_a_valid_key_proceeds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "debug", False)
    monkeypatch.setattr(settings, "fernet_key", _VALID_KEY)

    assert _errors(celeryd_init.send(sender="worker@test", conf=None, instance=None)) == []


def test_worker_start_in_debug_proceeds_without_a_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "debug", True)
    monkeypatch.setattr(settings, "fernet_key", "")

    assert _errors(celeryd_init.send(sender="worker@test", conf=None, instance=None)) == []
