"""`BasePage.expand_all_fields` returns only once the form really shows every field (#1897).

## What #1897 saw

`E2E smoke` failed four times on 2026-09-26 with the species create dialog
open, its "Alle Felder anzeigen" toggle **not** expanded and the scientific-name
field (expertise level ``intermediate``, the light-mode default is
``beginner``) therefore absent; the test then timed out 15 s later in
``fill_scientific_name`` — far from the step that went wrong. The helper that
should have expanded the form looked for the toggle once, clicked it natively
if present, slept 0.3 s and returned without checking anything.

## What is pinned here

* a collapsed form is expanded with one coordinate-free click and the helper
  waits for ``aria-expanded="true"``;
* an already expanded form is left alone — the toggle flips a global override,
  so a second click collapses it (the double-toggle spelling of the defect);
* a click that does not take effect fails **in the helper**, naming the
  toggle's state;
* a form whose level already shows every field renders no toggle, and the
  helper returns without clicking — read only after the form settled.

The fake below is minimal on purpose: a toggle node with an ``aria-expanded``
attribute that a ``.click()`` script flips (or, for the failure case, does not).
"""

from __future__ import annotations

import pytest
from selenium.webdriver.common.by import By

from tests.e2e.pages.base_page import BasePage

FORM = (By.CSS_SELECTOR, "[data-testid='species-create-dialog']")
SETTLED = (
    By.CSS_SELECTOR,
    "[data-testid='species-create-dialog'] [data-testid='form-submit-button']",
)
TOGGLE_CSS = "[data-testid='species-create-dialog'] [data-testid='show-all-fields-toggle']"


class _Node:
    def __init__(self, driver: _Driver, css: str) -> None:
        self._driver = driver
        self.css = css

    def is_displayed(self) -> bool:
        return True

    def is_enabled(self) -> bool:
        return True

    def get_attribute(self, name: str) -> str | None:
        return self._driver.expanded if name == "aria-expanded" else None

    @property
    def text(self) -> str:
        return (
            "Weniger Felder anzeigen" if self._driver.expanded == "true" else "Alle Felder anzeigen"
        )


class _Driver:
    """A dialog with a submit button and (optionally) a toggle whose click may or may not work."""

    def __init__(
        self,
        *,
        toggle: bool = True,
        expanded: str = "false",
        click_works: bool = True,
        vanish_on_click: bool = False,
    ) -> None:
        self.vanish_on_click = vanish_on_click
        self.toggle = toggle
        self.expanded = expanded
        self.click_works = click_works
        self.clicks = 0

    def find_element(self, by: str, value: str) -> _Node:
        found = self.find_elements(by, value)
        if not found:
            from selenium.common.exceptions import NoSuchElementException

            raise NoSuchElementException(value)
        return found[0]

    def find_elements(self, _by: str, value: str) -> list[_Node]:
        if value == SETTLED[1]:
            return [_Node(self, value)]
        if value == TOGGLE_CSS and self.toggle:
            return [_Node(self, value)]
        return []

    def execute_script(self, script: str, *args: object) -> None:
        if ".click()" in script:
            self.clicks += 1
            if self.vanish_on_click:
                self.toggle = False
            elif self.click_works:
                self.expanded = "false" if self.expanded == "true" else "true"


def _page(driver: _Driver) -> BasePage:
    page = BasePage(driver, "http://app.invalid")  # type: ignore[arg-type]
    settled_waits: list[tuple[str, str]] = []

    def _visible(locator: tuple[str, str], timeout: int = 0) -> _Node:
        # The settled wait itself is `resolve_element`'s (held by test_element_proxy.py);
        # here it only has to happen, and before the toggle is looked for.
        settled_waits.append(locator)
        return driver.find_element(*locator)

    page.wait_for_element_visible = _visible  # type: ignore[method-assign]
    driver.settled_waits = settled_waits  # type: ignore[attr-defined]
    return page


def test_a_collapsed_form_is_expanded_with_one_click_and_the_helper_waits_for_it() -> None:
    driver = _Driver(expanded="false")

    _page(driver).expand_all_fields(FORM, settled=SETTLED, timeout=1)

    assert (driver.clicks, driver.expanded) == (1, "true")


def test_an_expanded_form_is_left_alone_rather_than_collapsed() -> None:
    driver = _Driver(expanded="true")

    _page(driver).expand_all_fields(FORM, settled=SETTLED, timeout=1)

    assert (driver.clicks, driver.expanded) == (0, "true")


def test_a_click_that_does_not_take_effect_fails_in_the_helper_naming_the_state() -> None:
    driver = _Driver(expanded="false", click_works=False)

    with pytest.raises(AssertionError, match="aria-expanded='false'"):
        _page(driver).expand_all_fields(FORM, settled=SETTLED, timeout=1)


def test_a_form_without_a_toggle_needs_no_click() -> None:
    driver = _Driver(toggle=False)

    _page(driver).expand_all_fields(FORM, settled=SETTLED, timeout=1)

    assert driver.clicks == 0
    assert driver.settled_waits == [SETTLED], "absence may only be read once the form settled"


def test_a_toggle_that_disappears_after_the_click_counts_as_expanded() -> None:
    """The dialog renders the toggle only below ``expert``; a level arriving late removes it — all fields show."""
    driver = _Driver(expanded="false", vanish_on_click=True)

    _page(driver).expand_all_fields(FORM, settled=SETTLED, timeout=1)

    assert driver.clicks == 1
