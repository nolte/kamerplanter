"""Unit tests for `BasePage.scroll_and_click`'s missed-click diagnosis (#3065).

The defect class: a native `WebElement.click()` hit-tests the element's centre
and only then sends the press. When the layout moves in between -- on the
desktop profiles a classic scrollbar appearing on the first scroll re-wrapped
the dialog content above the action row -- the press lands on the content
next to the button, nothing raises, and the caller's next wait reports the
*control* as unresponsive: "Cancel was clicked but the dialog neither closed
nor asked to discard its changes". These pin the two checks that tell a missed
click from a dead control, and that neither of them turns into a retry.
"""

from __future__ import annotations

import pytest
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.common.by import By

from tests.e2e.pages.base_page import BasePage

from .fake_driver import FakeDriver, FakeElement

CANCEL = "[data-testid='form-cancel-button']"


def page_and_element(driver: FakeDriver) -> tuple[BasePage, FakeElement]:
    page = BasePage(driver, "http://app.invalid")  # type: ignore[arg-type]
    return page, driver.find_element(By.CSS_SELECTOR, CANCEL)


class TestThePressProbe:
    def test_a_press_that_lands_on_the_element_passes(self) -> None:
        driver = FakeDriver({CANCEL})
        page, cancel = page_and_element(driver)

        page.scroll_and_click(cancel)

        assert driver.clicked == [CANCEL]

    def test_a_press_that_lands_elsewhere_is_reported_as_a_missed_click(self) -> None:
        """The regression guard: before #3065 this returned silently."""
        driver = FakeDriver({CANCEL}, press_lands_outside={CANCEL})
        page, cancel = page_and_element(driver)

        with pytest.raises(AssertionError, match="missed click") as caught:
            page.scroll_and_click(cancel)

        message = str(caught.value)
        assert CANCEL in message, "the report must name the element that was aimed at"
        assert "div.MuiDialogContent-root" in message, "…and what the press hit instead"

    def test_a_missed_click_is_not_repeated(self) -> None:
        """Diagnosis, not healing: one press went out, and no fallback follows it."""
        driver = FakeDriver({CANCEL}, press_lands_outside={CANCEL})
        page, cancel = page_and_element(driver)

        with pytest.raises(AssertionError):
            page.scroll_and_click(cancel)

        assert driver.clicked == [CANCEL]

    def test_no_verdict_means_no_assertion(self) -> None:
        """A probe that saw nothing (e.g. the click navigated away) must not fail the click."""
        driver = FakeDriver({CANCEL})
        page, cancel = page_and_element(driver)
        driver.execute_script = (  # type: ignore[method-assign]
            lambda script, *args: (
                None
                if script.startswith("/* readPressProbe */")
                else FakeDriver.execute_script(driver, script, *args)
            )
        )

        page.scroll_and_click(cancel)

        assert driver.clicked == [CANCEL]

    def test_the_probe_is_disarmed_when_the_driver_refuses_the_click(self) -> None:
        """An intercepted click sends no press; the JS fallback must still run, unjudged."""
        driver = FakeDriver({CANCEL}, press_lands_outside={CANCEL})
        page, cancel = page_and_element(driver)

        def intercepted() -> None:
            raise ElementClickInterceptedException("other element would receive the click")

        cancel.click = intercepted  # type: ignore[method-assign]

        page.scroll_and_click(cancel)

        assert driver.clicked == [CANCEL], "the JS fallback must have activated the element"
        assert driver._armed is None, "the probe must not outlive the click"


class TestTheSettledHitTest:
    def test_an_element_in_place_after_the_scroll_is_scrolled_to_once(self) -> None:
        driver = FakeDriver({CANCEL})
        page, cancel = page_and_element(driver)

        page.scroll_and_click(cancel)

        assert driver.scrolls == 1
        assert driver.settled_hit_checks == 1

    def test_an_element_the_scroll_moved_is_scrolled_to_once_more(self) -> None:
        driver = FakeDriver({CANCEL}, moves_after_scroll={CANCEL})
        page, cancel = page_and_element(driver)

        page.scroll_and_click(cancel)

        assert driver.scrolls == 2, "exactly one re-scroll, not a loop"
        assert driver.settled_hit_checks == 2
        assert driver.clicked == [CANCEL], "and still exactly one click"


class TestAnOpenPrompt:
    """A click that opens a native ``window.confirm`` must find it still open.

    The expertise-level downgrade on the account settings page asks through
    ``window.confirm`` (TC-REQ-021-004..006). Any script sent while it is open
    makes WebDriver dismiss it -- the app then reads "Cancel" -- and raise.
    """

    def test_no_script_reaches_the_driver_while_the_prompt_is_open(self) -> None:
        driver = FakeDriver({CANCEL}, opens_prompt_on_click={CANCEL})
        page, button = page_and_element(driver)

        page.scroll_and_click(button)

        assert driver.scripts_while_prompt == [], "a probe script dismissed the prompt"
        assert driver.prompt == "confirm", "the caller must find the prompt still open"
        assert driver.clicked == [CANCEL]

    def test_the_settle_and_arm_steps_leave_an_already_open_prompt_alone(self) -> None:
        driver = FakeDriver({CANCEL})
        page, button = page_and_element(driver)
        driver.prompt = "confirm"

        assert page._settled_hit(button) is None
        page._arm_press_probe(button)

        assert driver.scripts_while_prompt == []
        assert driver.prompt == "confirm"


class TestOpenSelectIn:
    """`open_select_in`'s mousedown fallback is for a press that hit the trigger only."""

    CONTAINER = "[data-testid='form-field-site_key']"
    TRIGGER = f"{CONTAINER} [role='combobox']"

    def test_a_press_that_missed_the_trigger_is_not_papered_over(self) -> None:
        driver = FakeDriver({self.TRIGGER}, press_lands_outside={self.TRIGGER})
        page = BasePage(driver, "http://app.invalid")  # type: ignore[arg-type]
        # The re-resolving element proxy needs a real driver; what is under test
        # is what happens after the click, not the locate step.
        page.wait_for_element_clickable = (  # type: ignore[method-assign]
            lambda locator, timeout=0: driver.find_element(*locator)
        )
        fallback: list[object] = []
        page.dispatch_menu_trigger_open = fallback.append  # type: ignore[method-assign]

        with pytest.raises(AssertionError, match="missed click"):
            page.open_select_in(self.CONTAINER, "site")

        assert fallback == [], "the mousedown fallback must not open a menu over a stray press"
        assert driver.clicked == [self.TRIGGER]
