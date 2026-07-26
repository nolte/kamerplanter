"""Unit tests for `BasePage.navigate_via_sidebar`'s no-longer-silent fallback.

The defect these pin (#778 A3): the helper decided between clicking the nav link
and navigating by URL on ``items[0].is_displayed()``. That answer is ``False``
both for a nav item the app legitimately hides *and* for one merely clipped by
the drawer's ``overflow: auto`` scroll box, so the suite stopped exercising
sidebar navigation for every item below the fold -- and the test still passed.
"""

from __future__ import annotations

import warnings

import pytest
from selenium.common.exceptions import TimeoutException

from tests.e2e.pages.base_page import BasePage, SidebarNavigationFallback

from .fake_driver import FakeDriver

SIDEBAR = "[data-testid='sidebar']"
PAPER = "[data-testid='sidebar'] .MuiDrawer-paper"
NAV_SITES = "[data-testid='nav-/standorte/sites']"
PATH = "/standorte/sites"


class RecordingPage(BasePage):
    """Records whether the URL fallback was taken instead of a link click."""

    def __init__(self, driver: FakeDriver) -> None:
        super().__init__(driver, "http://app.invalid")  # type: ignore[arg-type]
        self.navigated_to: list[str] = []

    def navigate(self, path: str) -> None:
        self.navigated_to.append(path)
        self.driver.current_url = f"{self.base_url}{path}"  # type: ignore[attr-defined]


def page_with(*present: str, hidden: tuple[str, ...] = ()) -> RecordingPage:
    driver = FakeDriver(
        set(present),
        hidden=hidden,
        nav_targets={NAV_SITES: f"http://app.invalid{PATH}"},
    )
    return RecordingPage(driver)


class TestNavigateViaSidebar:
    def test_clicks_an_item_inside_an_open_drawer(self) -> None:
        page = page_with(SIDEBAR, PAPER, NAV_SITES)
        with warnings.catch_warnings():
            warnings.simplefilter("error", SidebarNavigationFallback)
            assert page.navigate_via_sidebar(PATH, timeout=2) is True
        assert page.navigated_to == []
        assert page.driver.clicked == [NAV_SITES]  # type: ignore[attr-defined]

    def test_the_click_path_waits_for_the_url_to_change(self) -> None:
        """A click that never routed must not be reported as a navigation.

        Without the nav target the URL stays put, so the post-click
        ``url_contains`` wait is the thing that has to fail -- the helper must not
        return ``True`` on the strength of having dispatched a click.
        """
        driver = FakeDriver({SIDEBAR, PAPER, NAV_SITES})
        page = RecordingPage(driver)
        with pytest.raises(TimeoutException):
            page.navigate_via_sidebar(PATH, timeout=1)

    def test_a_genuinely_hidden_item_warns_instead_of_staying_silent(self) -> None:
        page = page_with(SIDEBAR, PAPER, NAV_SITES, hidden=(NAV_SITES,))
        with pytest.warns(SidebarNavigationFallback, match="nav-/standorte/sites"):
            assert page.navigate_via_sidebar(PATH, timeout=2) is False
        assert page.navigated_to == [PATH]

    def test_strict_mode_fails_instead_of_falling_back(self) -> None:
        page = page_with(SIDEBAR, PAPER, NAV_SITES, hidden=(NAV_SITES,))
        with pytest.raises(AssertionError, match="exercised the router rather than the drawer"):
            page.navigate_via_sidebar(PATH, timeout=2, strict=True)
        assert page.navigated_to == []

    def test_a_missing_nav_item_warns_and_falls_back(self) -> None:
        page = page_with(SIDEBAR, PAPER)
        with pytest.warns(SidebarNavigationFallback):
            assert page.navigate_via_sidebar(PATH, timeout=2) is False
        assert page.navigated_to == [PATH]

    def test_no_sidebar_mounted_is_not_an_error(self) -> None:
        """The login route renders outside `MainLayout`; that is the caller's assertion."""
        page = page_with()
        with pytest.warns(SidebarNavigationFallback):
            assert page.navigate_via_sidebar(PATH, timeout=2) is False
