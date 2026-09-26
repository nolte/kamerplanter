"""#1781 — the Celery worker refuses to start without the tombstone salt, like the API.

The API refuses to start with ``DEBUG`` off and an ``ERASURE_TOMBSTONE_SALT``
shorter than 32 characters (``app.main.insecure_default_secrets``). The worker
never imports ``app.main``: without a check of its own it started, and every log
line naming a data subject carried ``subject=anon_unavailable`` — silently
uncorrelatable — while the scheduled erasure refused to run.

The check is a ``celeryd_init`` receiver. Celery's ``Signal.send`` catches
``Exception`` raised by a receiver and only logs it; ``SystemExit`` is not an
``Exception`` and propagates. The tests send the **real** signal, so a receiver
that raised a swallowed exception type — or was never connected — fails here.

Traces to issue #1781 (no TC-ID: process start-up is not a user-facing case).
"""

from __future__ import annotations

import base64

import pytest
from celery.signals import celeryd_init

import app.tasks  # noqa: F401  importing the package is what connects the receivers
from app.config.settings import settings


@pytest.fixture(autouse=True)
def _no_error_tracking(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the sibling receivers inert: no DSN, no SDK initialisation, a valid Fernet key (#1859)."""
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    monkeypatch.setattr(settings, "fernet_key", base64.urlsafe_b64encode(bytes(range(32))).decode())


@pytest.mark.parametrize("salt", ["", "x" * 31])
def test_worker_start_without_a_salt_exits_when_not_debug(monkeypatch: pytest.MonkeyPatch, salt: str) -> None:
    monkeypatch.setattr(settings, "debug", False)
    monkeypatch.setattr(settings, "erasure_tombstone_salt", salt)

    with pytest.raises(SystemExit) as excinfo:
        celeryd_init.send(sender="worker@test", conf=None, instance=None)

    assert "ERASURE_TOMBSTONE_SALT" in str(excinfo.value)


def test_worker_start_with_a_valid_salt_proceeds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "debug", False)
    monkeypatch.setattr(settings, "erasure_tombstone_salt", "x" * 32)

    responses = celeryd_init.send(sender="worker@test", conf=None, instance=None)

    assert not [r for _receiver, r in responses if isinstance(r, BaseException)], responses


def test_worker_start_in_debug_proceeds_without_a_salt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "debug", True)
    monkeypatch.setattr(settings, "erasure_tombstone_salt", "")

    responses = celeryd_init.send(sender="worker@test", conf=None, instance=None)

    assert not [r for _receiver, r in responses if isinstance(r, BaseException)], responses
