"""#1812 — the Celery worker refuses to start without the log pseudonym salt, like the API.

``LOG_PSEUDONYM_SALT`` keys every ``sub_…`` subject reference and ``email_sha256``
digest the worker writes (retention, erasure, notification tasks). Without it
each one is a constant, and the lines of different accounts become
indistinguishable. The API refuses to start with ``DEBUG`` off and a salt
shorter than 32 characters (``app.main.insecure_default_secrets``); the worker
never imports ``app.main`` and needs its own ``celeryd_init`` receiver.

The tests send the **real** signal (see ``test_worker_salt_fail_fast.py`` for
why a swallowed exception type or an unconnected receiver fails here).

Traces to issue #1812 (no TC-ID: process start-up is not a user-facing case).
"""

from __future__ import annotations

import base64

import pytest
from celery.signals import celeryd_init

import app.tasks  # noqa: F401  importing the package is what connects the receivers
from app.config.settings import settings


@pytest.fixture(autouse=True)
def _sibling_gates_satisfied(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the other receivers inert: no DSN, a valid Fernet key, a valid tombstone salt."""
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    monkeypatch.setattr(settings, "fernet_key", base64.urlsafe_b64encode(bytes(range(32))).decode())
    monkeypatch.setattr(settings, "erasure_tombstone_salt", "t" * 32)


@pytest.mark.parametrize("salt", ["", "x" * 31])
def test_worker_start_without_a_log_salt_exits_when_not_debug(monkeypatch: pytest.MonkeyPatch, salt: str) -> None:
    monkeypatch.setattr(settings, "debug", False)
    monkeypatch.setattr(settings, "log_pseudonym_salt", salt)

    with pytest.raises(SystemExit) as excinfo:
        celeryd_init.send(sender="worker@test", conf=None, instance=None)

    assert "LOG_PSEUDONYM_SALT" in str(excinfo.value)
    assert salt not in str(excinfo.value) or not salt


def test_worker_start_with_a_valid_log_salt_proceeds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "debug", False)
    monkeypatch.setattr(settings, "log_pseudonym_salt", "x" * 32)

    responses = celeryd_init.send(sender="worker@test", conf=None, instance=None)

    assert not [r for _receiver, r in responses if isinstance(r, BaseException)], responses


def test_worker_start_in_debug_proceeds_without_a_log_salt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "debug", True)
    monkeypatch.setattr(settings, "log_pseudonym_salt", "")

    responses = celeryd_init.send(sender="worker@test", conf=None, instance=None)

    assert not [r for _receiver, r in responses if isinstance(r, BaseException)], responses
