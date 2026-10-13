"""An exception that never becomes a log record is printed redacted (#1880).

#1796/#1877 redact exception texts where a ``logging`` record is created or
handled. Three interpreter hooks render an exception without one and printed it
raw to stderr — measured before the fix, in a real subprocess configured the way
the API and the worker configure themselves:

* ``sys.excepthook`` — an exception escaping the process entry;
* ``threading.excepthook`` — an uncaught exception in a thread;
* ``sys.unraisablehook`` — an exception raised in a finaliser.

Each printed ``app.common.exceptions.NotFoundError: User with key '<key>' not
found.`` — the account key — and a connection error's URL with its query string.
The probe values come in through the environment, so the traceback's *source
lines* (which are code, never runtime values) cannot contain them.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading

import pytest

from app.config import logging as logging_config
from tests.unit.guards.test_privacy_logs_carry_no_plaintext_subject import BACKEND_ROOT

# Assembled at run time: a literal shaped like a credential is reported by the
# repository's secret scanner (BACKEND.md §16.3).
SUBJECT_KEY = "-".join(("acct", "1880", "subject"))
API_KEY = "-".join(("SECRET", "KEY", "1880"))

_SETUP = {
    "api": "import app.main\n",
    "worker": (
        "from celery.app.log import Logging\n"
        "from app.tasks import celery_app\n"
        "Logging._setup = False\n"
        "celery_app.log.setup(loglevel='INFO')\n"
    ),
    "cli": "from app.config.logging import setup_logging\nsetup_logging()\n",
}
_RAISE = (
    "import os, threading\n"
    "from app.common.exceptions import NotFoundError\n"
    "def lookup():\n"
    "    try:\n"
    "        raise ConnectionError('GET https://api.example.org/v1?appid=' + os.environ['PROBE_API_KEY'])\n"
    "    except ConnectionError as cause:\n"
    "        raise NotFoundError('User', os.environ['PROBE_SUBJECT']) from cause\n"
)
_SINKS = {
    "main": "lookup()\n",
    "thread": "t = threading.Thread(target=lookup, name='probe-thread'); t.start(); t.join()\n",
    "finaliser": ("class Probe:\n    def __del__(self):\n        lookup()\np = Probe(); del p\n"),
}


def _run(setup: str, sink: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-W", "ignore", "-c", _SETUP[setup] + _RAISE + _SINKS[sink]],
        cwd=BACKEND_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": str(BACKEND_ROOT),
            "PROBE_SUBJECT": SUBJECT_KEY,
            "PROBE_API_KEY": API_KEY,
            "SENTRY_DSN": "",
        },
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )


@pytest.mark.parametrize("sink", sorted(_SINKS))
@pytest.mark.parametrize("setup", sorted(_SETUP))
def test_an_uncaught_exception_is_printed_without_its_text(setup: str, sink: str) -> None:
    result = _run(setup, sink)
    output = result.stderr + result.stdout

    # The traceback is still there — frames, class, error code — for the operator.
    assert "NotFoundError: [ENTITY_NOT_FOUND]" in result.stderr, output
    assert "in lookup" in result.stderr, output
    assert "ConnectionError: GET https://api.example.org/v1?<redacted>" in result.stderr, output
    assert SUBJECT_KEY not in output, output
    assert API_KEY not in output, output
    assert (result.returncode != 0) is (sink == "main"), output
    if sink == "thread":
        assert "Exception in thread probe-thread" in result.stderr, output


def test_an_error_trackers_hook_still_runs_but_cannot_print() -> None:
    """A hook installed before ours (the Sentry SDK in the worker) captures; its raw print is discarded."""
    probe = (
        "import sys, os\n"
        "seen = []\n"
        "def tracker(exc_type, exc, tb):\n"
        "    seen.append(exc_type.__name__)\n"
        "    sys.__excepthook__(exc_type, exc, tb)\n"
        "sys.excepthook = tracker\n"
        "from app.config.logging import setup_logging\n"
        "setup_logging()\n"
        "import atexit\n"
        "atexit.register(lambda: print('tracker saw', seen))\n"
    )
    result = subprocess.run(
        [sys.executable, "-W", "ignore", "-c", probe + _RAISE + "lookup()\n"],
        cwd=BACKEND_ROOT,
        env={**os.environ, "PYTHONPATH": str(BACKEND_ROOT), "PROBE_SUBJECT": SUBJECT_KEY, "PROBE_API_KEY": API_KEY},
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )

    assert "tracker saw ['NotFoundError']" in result.stdout, result.stdout + result.stderr
    assert "NotFoundError: [ENTITY_NOT_FOUND]" in result.stderr, result.stderr
    assert SUBJECT_KEY not in result.stderr + result.stdout, result.stderr


def test_installing_twice_wraps_once() -> None:
    saved = sys.excepthook, threading.excepthook, sys.unraisablehook
    try:
        logging_config.install_uncaught_exception_redaction()
        first = sys.excepthook, threading.excepthook, sys.unraisablehook
        logging_config.install_uncaught_exception_redaction()

        assert (sys.excepthook, threading.excepthook, sys.unraisablehook) == first
        assert all(getattr(hook, "_kp_redacting", False) for hook in first)
    finally:
        sys.excepthook, threading.excepthook, sys.unraisablehook = saved
