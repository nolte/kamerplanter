"""Truthful handling of a Selenium session that died under a test (#1903).

CI run 36231650530 lost one session six seconds after creation: the grid node
could no longer reach that session's chromedriver (``Connection error ...
localhost:<port>``), while the hub, the node and the other three sessions kept
working. The test body failed, and then every teardown step that touched the
dead session (``driver.quit()``, the failure screenshot) raised again, burying
the one fact that matters under three more stack traces.

What this module does and does not do:

* It classifies an exception as "the session is gone" from the *transport*
  evidence only (a connection-level error, or the W3C ``invalid session id``
  family). An assertion failure, a timeout or any other WebDriver error is NOT
  classified that way and keeps propagating.
* The teardown helpers swallow nothing silently: the dead-session fact is
  returned to the caller, which records it on the test item
  (``user_properties`` -> junit XML) and emits a warning. They never retry, and
  they never touch the original test failure.
* It does not claim to know why the session died. Resource evidence is
  collected by ``scripts/run-e2e.sh`` (``diagnostics/``).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from selenium.common.exceptions import (
    InvalidSessionIdException,
    WebDriverException,
)

# Substrings the Grid / chromedriver put into the message when the *transport*
# to the browser is broken. Deliberately narrow: "timeout" is absent, because a
# slow page is not a dead session.
_GONE_MARKERS = (
    "connection error",
    "invalid session id",
    "chrome not reachable",
    "session deleted because of page crash",
    "disconnected: not connected to devtools",
    "connection refused",
)

SESSION_LOST_PROPERTY = "selenium_session_lost"


def is_session_gone(exc: BaseException) -> bool:
    """Whether ``exc`` shows that the browser session itself is unreachable."""
    if isinstance(exc, InvalidSessionIdException):
        return True
    if not isinstance(exc, WebDriverException):
        return False
    message = (exc.msg or str(exc)).lower()
    return any(marker in message for marker in _GONE_MARKERS)


def _describe(exc: BaseException) -> str:
    first_line = (getattr(exc, "msg", None) or str(exc)).strip().splitlines()[0]
    return f"{type(exc).__name__}: {first_line}"[:300]


def quit_driver(driver: Any) -> str | None:
    """Quit ``driver``; return a note when the session was already gone.

    Any other failure of ``quit()`` is re-raised unchanged.
    """
    try:
        driver.quit()
    except WebDriverException as exc:
        if is_session_gone(exc):
            return f"driver.quit() found the session already gone ({_describe(exc)})"
        raise
    return None


def run_if_session_alive(action: Callable[[], Any], what: str) -> str | None:
    """Run a best-effort post-failure ``action``; return a note if the session is gone.

    For artefacts taken *after* a test failed (screenshots): when the session is
    gone there is nothing to capture, and the note says so instead of adding a
    second traceback. Any other error still propagates.
    """
    try:
        action()
    except WebDriverException as exc:
        if is_session_gone(exc):
            return f"{what} skipped, the session was already gone ({_describe(exc)})"
        raise
    return None
