"""`FieldModePage.watch_undo_lifetime` installs its observer only once no "Rückgängig" button is mounted.

`tap_undo` returns when the dismissed snackbar is *invisible*; MUI keeps it mounted through
its exit transition. An observer installed in that window stamped the leaving button as
"shown" and its unmount as "hidden": TC-053-026 measured 259 ms instead of about 8 s.

Browser-free: the real page object over a driver whose button leaves the DOM only after a
few lookups, recording when the observer script arrives.
"""

from __future__ import annotations

import pytest
from selenium.webdriver.support.ui import WebDriverWait

from tests.e2e.pages.field_mode_page import FieldModePage

from .fake_driver import FakeElement

UNDO = FieldModePage.SNACKBAR_UNDO[1]


class LeavingSnackbarDriver:
    def __init__(self, mounted_for: int) -> None:
        self.mounted_for = mounted_for
        self.lookups = 0
        self.mounted_when_installed: bool | None = None

    def find_elements(self, _by: str, value: str) -> list[FakeElement]:
        assert value == UNDO, value
        self.lookups += 1
        return [FakeElement(UNDO, displayed=False)] if self.lookups <= self.mounted_for else []

    def execute_script(self, script: str, *_args: object) -> object:
        assert "__kpUndoLife" in script, script[:60]
        self.mounted_when_installed = self.lookups <= self.mounted_for
        return True


def page_for(driver: LeavingSnackbarDriver) -> FieldModePage:
    return FieldModePage(driver, "http://app.invalid")  # type: ignore[arg-type]


def test_the_observer_waits_until_the_leaving_snackbar_is_unmounted() -> None:
    driver = LeavingSnackbarDriver(mounted_for=3)

    page_for(driver).watch_undo_lifetime()

    assert driver.mounted_when_installed is False


def test_a_snackbar_that_never_leaves_fails_loudly() -> None:
    driver = LeavingSnackbarDriver(mounted_for=10**9)
    page = page_for(driver)
    page.poll = lambda timeout=None: WebDriverWait(driver, 0.3, poll_frequency=0.05)  # type: ignore[method-assign]

    with pytest.raises(AssertionError, match="still mounted"):
        page.watch_undo_lifetime()

    assert driver.mounted_when_installed is None
