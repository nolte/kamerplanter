"""Verification of `tests/e2e/_session_health.py` (#1903).

CI run 36231650530 lost one chromedriver six seconds into a session; the test
body failed and then `driver.quit()` and the failure screenshot each raised a
further traceback on the dead session. The helpers must (a) report a dead
session as a fact instead of raising, (b) keep raising everything that is not
transport evidence of a dead session, and (c) never retry.
"""

from __future__ import annotations

import pytest
from selenium.common.exceptions import (
    InvalidSessionIdException,
    TimeoutException,
    WebDriverException,
)

from tests.e2e._session_health import is_session_gone, quit_driver, run_if_session_alive

CONNECTION_ERROR = WebDriverException(
    "Connection error (DELETE http://localhost:5820/session/e5a3f71281b99eeb491d374cc8da7448)"
)


class _Driver:
    def __init__(self, exc: BaseException | None) -> None:
        self._exc = exc
        self.quit_calls = 0

    def quit(self) -> None:
        self.quit_calls += 1
        if self._exc is not None:
            raise self._exc


@pytest.mark.parametrize(
    "exc",
    [
        CONNECTION_ERROR,
        InvalidSessionIdException("invalid session id"),
        WebDriverException("chrome not reachable"),
    ],
)
def test_transport_evidence_is_classified_as_session_gone(exc: BaseException) -> None:
    assert is_session_gone(exc)


@pytest.mark.parametrize(
    "exc",
    [
        TimeoutException("Message: timeout waiting for element"),
        WebDriverException("unknown error: element click intercepted"),
        AssertionError("Connection error in the app under test"),
        ValueError("boom"),
    ],
)
def test_other_errors_are_not_session_gone(exc: BaseException) -> None:
    assert not is_session_gone(exc)


def test_quit_on_healthy_session_reports_nothing() -> None:
    driver = _Driver(None)
    assert quit_driver(driver) is None
    assert driver.quit_calls == 1


def test_quit_on_dead_session_reports_the_fact_and_does_not_retry() -> None:
    driver = _Driver(CONNECTION_ERROR)
    note = quit_driver(driver)
    assert note is not None and "already gone" in note and "localhost:5820" in note
    assert driver.quit_calls == 1


def test_quit_failing_for_another_reason_still_raises() -> None:
    with pytest.raises(WebDriverException, match="unknown error"):
        quit_driver(_Driver(WebDriverException("unknown error: disk full")))


def test_failure_screenshot_on_dead_session_is_a_note_not_a_second_traceback() -> None:
    def action() -> None:
        raise CONNECTION_ERROR

    note = run_if_session_alive(action, "failure screenshot")
    assert note is not None and note.startswith("failure screenshot skipped")


def test_screenshot_failing_for_another_reason_still_raises() -> None:
    def action() -> None:
        raise OSError("disk full")

    with pytest.raises(OSError):
        run_if_session_alive(action, "failure screenshot")
