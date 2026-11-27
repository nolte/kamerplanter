"""The helpers that clear a cover the way a user does, before a guarded click (#3157).

Since step 2 a guarded click on a covered control fails. Two covers in the
measuring nightly were transient and user-removable, so the page objects now
remove them the way a user would instead of clicking through:

* :meth:`BasePage.close_snackbars_over` closes the snackbars lying on the
  control's centre with their own close button and waits until each has left --
  and leaves a snackbar alone that covers nothing;
* :meth:`BasePage.close_header_overflow` closes the page header's ``⋮`` menu that
  the read-only header probes opened (a MUI ``Menu``, which ``close_mui_dropdown``
  does not see), so its invisible backdrop no longer lies on the next click.
"""

from __future__ import annotations

from typing import Any

import pytest
from selenium.common.exceptions import (
    NoAlertPresentException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.by import By

from tests.e2e.pages.base_page import BasePage

ROW = (By.CSS_SELECTOR, "[data-testid='care-done-1']")


class _Alertless:
    @property
    def alert(self) -> object:
        raise NoAlertPresentException("no such alert")

    @property
    def active_element(self) -> _Node:
        return _Node("<active-element>", self._driver)  # type: ignore[attr-defined]


class _Node:
    """A DOM node: clickable, and stale once its snackbar has left."""

    def __init__(self, name: str, driver: _Driver, *, wrapper: _Node | None = None) -> None:
        self.name = name
        self._driver = driver
        self._wrapper = wrapper
        self.gone = False

    # -- the wrapper side --
    def find_elements(self, by: str, value: str) -> list[_Node]:
        if value == "[data-testid='snackbar-close']" and self._driver.with_close_button:
            return [_Node(f"{self.name}/close", self._driver, wrapper=self)]
        return []

    def is_enabled(self) -> bool:
        if self.gone:
            raise StaleElementReferenceException(f"{self.name} left the DOM")
        return True

    # -- the button side --
    def click(self) -> None:
        self._driver.clicked.append(self.name)
        if self._wrapper is not None:
            self._wrapper.gone = True

    def send_keys(self, *keys: str) -> None:
        self._driver.keys.append((self.name, "".join(keys)))
        if self._driver.menu_open and self._driver.escape_closes:
            self._driver.menu_open = False


class _Driver:
    def __init__(
        self,
        covering: int = 0,
        *,
        with_close_button: bool = True,
        menu_open: bool = False,
        escape_closes: bool = True,
    ) -> None:
        #: Snackbars lying on the control, top-most first; each leaves when closed.
        self.snackbars = [_Node(f"snackbar-{i}", self) for i in range(covering)]
        self.with_close_button = with_close_button
        self.menu_open = menu_open
        self.escape_closes = escape_closes
        self.clicked: list[str] = []
        self.keys: list[tuple[str, str]] = []
        self.switch_to = _Alertless()
        self.switch_to._driver = self  # type: ignore[attr-defined]

    def execute_script(self, script: str, *args: object) -> Any:
        if script.startswith("/* snackbarOver */"):
            left = [s for s in self.snackbars if not s.gone]
            return left[0] if left else None
        raise AssertionError(f"unexpected script {script[:40]!r}")

    def find_elements(self, by: str, value: str) -> list[_Node]:
        if value == "[data-testid='page-header-overflow-menu']":
            return [_Node("menu-root", self)] if self.menu_open else []
        if value == "[role='menu']":
            return [_Node("menu", self)] if self.menu_open else []
        return []


def _page(driver: _Driver) -> BasePage:
    return BasePage(driver, "http://app.invalid")  # type: ignore[arg-type]


class TestCloseSnackbarsOver:
    def test_each_covering_snackbar_is_closed_with_its_own_button(self) -> None:
        driver = _Driver(covering=2)

        closed = _page(driver).close_snackbars_over(_Node("row", driver), "the row")  # type: ignore[arg-type]

        assert closed == 2
        assert driver.clicked == ["snackbar-0/close", "snackbar-1/close"]
        assert all(s.gone for s in driver.snackbars)

    def test_nothing_on_the_control_closes_nothing(self) -> None:
        driver = _Driver(covering=0)

        assert _page(driver).close_snackbars_over(_Node("row", driver), "the row") == 0  # type: ignore[arg-type]
        assert driver.clicked == []

    def test_a_snackbar_that_does_not_leave_fails_naming_the_step(self) -> None:
        driver = _Driver(covering=1, with_close_button=False)

        with pytest.raises(AssertionError, match="the row: a snackbar on the control"):
            _page(driver).close_snackbars_over(_Node("row", driver), "the row", timeout=0)  # type: ignore[arg-type]


class TestCloseHeaderOverflow:
    def test_an_open_menu_is_closed_with_escape_and_waited_for(self) -> None:
        driver = _Driver(menu_open=True)

        _page(driver).close_header_overflow()

        assert driver.keys == [("menu", "")]
        assert driver.menu_open is False

    def test_a_closed_menu_gets_no_key(self) -> None:
        driver = _Driver(menu_open=False)

        _page(driver).close_header_overflow()

        assert driver.keys == []

    def test_a_menu_that_stays_open_fails_loudly(self) -> None:
        driver = _Driver(menu_open=True, escape_closes=False)

        with pytest.raises(AssertionError, match="overflow menu did not close"):
            _page(driver).close_header_overflow(timeout=0)

    def test_the_read_only_probe_closes_the_menu_it_opened(self) -> None:
        """`is_header_action_enabled` used to call `close_mui_dropdown`, which cannot see a Menu."""
        driver = _Driver(menu_open=False)
        page = _page(driver)
        entry = _Node("remove-button-menu-item", driver)
        entry.get_attribute = lambda name: None  # type: ignore[attr-defined]

        def open_menu(testid: str, timeout: int = 0) -> _Node:
            driver.menu_open = True
            return entry

        page._header_action_element = open_menu  # type: ignore[method-assign]

        assert page.is_header_action_enabled("remove-button") is True
        assert driver.menu_open is False, "the probe must leave no menu (and no backdrop) behind"
