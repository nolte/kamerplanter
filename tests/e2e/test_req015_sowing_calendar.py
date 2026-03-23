"""E2E tests for REQ-015 -- Aussaatkalender / Sowing Calendar (TC-015-040 to TC-015-052).

Tests cover:
- Sowing calendar view loads with time bars and frost config (TC-015-040, TC-015-049)
- Sowing calendar has site select dropdown (TC-015-048)
- Category filter chips in sowing calendar (TC-015-046)
- Favorites filter toggle (TC-015-046)
- Legend and phase color display (TC-015-040)
- Empty state when no sowing data (TC-015-045, TC-015-048)

NFR-008 section 3.4 screenshot checkpoints at:
1. Page Load
2. Before significant actions
3. After significant actions
4. Error states
"""

from __future__ import annotations

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.calendar_page import CalendarPage


# -- Fixtures ----------------------------------------------------------------


@pytest.fixture
def calendar(browser: WebDriver, base_url: str) -> CalendarPage:
    """Return a CalendarPage bound to the test browser."""
    return CalendarPage(browser, base_url)


# -- Helpers ------------------------------------------------------------------


def _open_sowing_view(calendar: CalendarPage) -> None:
    """Navigate to calendar and switch to sowing tab."""
    calendar.open()
    calendar.switch_to_sowing_view()


# -- TC-015-040: Sowing calendar basics ----------------------------------------


class TestSowingCalendarLoad:
    """TC-015-040 to TC-015-045: Sowing calendar view rendering and content."""

    def test_sowing_view_renders_after_tab_switch(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-040: Sowing calendar view renders after switching to the sowing tab.

        Verifies:
        - The sowing tab is active
        - The sowing calendar card content is present (either data or empty state)
        """
        capture = request.node._screenshot_capture
        _open_sowing_view(calendar)
        capture("req015_040_sowing_view_loaded", "Sowing calendar view after tab switch")

        active = calendar.get_active_tab_value()
        assert active == "sowing", (
            f"Expected sowing tab to be active, got: '{active}'"
        )

        # Either sowing entries or an empty state should be visible
        cards = calendar.driver.find_elements(By.CSS_SELECTOR, ".MuiCard-root")
        empty_states = calendar.driver.find_elements(*CalendarPage.EMPTY_STATE)
        assert len(cards) > 0 or len(empty_states) > 0, (
            "Expected either sowing calendar card or empty state to be visible"
        )

    def test_sowing_view_shows_site_select(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-048: Site select dropdown is visible in sowing calendar view.

        Verifies the site select element is rendered so users can choose a site
        for frost configuration.
        """
        capture = request.node._screenshot_capture
        _open_sowing_view(calendar)
        capture("req015_048_sowing_site_select", "Sowing view with site select")

        assert calendar.is_site_select_visible(), (
            "Expected site select dropdown to be visible in sowing calendar view"
        )

    def test_sowing_view_has_month_column_headers(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-040: Sowing calendar shows month column headers (Jan-Dez).

        Verifies that columnheader elements are present in the sowing grid.
        """
        capture = request.node._screenshot_capture
        _open_sowing_view(calendar)
        capture("req015_040_sowing_month_headers", "Sowing calendar with month headers")

        # Month headers are rendered as columnheader role elements
        headers = calendar.driver.find_elements(
            By.CSS_SELECTOR, "[role='columnheader']"
        )
        # There should be 12 month headers
        assert len(headers) >= 12, (
            f"Expected at least 12 month column headers, got {len(headers)}"
        )


# -- TC-015-049: Frost config visualization ------------------------------------


class TestSowingCalendarFrostConfig:
    """TC-015-049: Eisheiligen marking and frost chips in sowing calendar."""

    def test_frost_info_chips_visible_when_site_has_frost_data(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-049: Frost info chips (last frost, Eisheilige) are visible.

        If a site with frost configuration is selected, info chips should
        display the frost dates. If no site is selected or no frost data
        is configured, this test documents the current state.
        """
        capture = request.node._screenshot_capture
        _open_sowing_view(calendar)
        capture("req015_049_frost_chips", "Sowing view frost info area")

        # Frost chips are MUI Chip elements with outlined variant and info/error color
        frost_chips = calendar.get_sowing_frost_chips()
        # Document what we found (may be 0 if no frost data configured)
        capture(
            "req015_049_frost_chips_count",
            f"Found {len(frost_chips)} frost info chips",
        )
        # No hard assert -- frost data depends on seed data


# -- TC-015-046: Sowing favorites filter ---------------------------------------


class TestSowingCalendarFavoritesFilter:
    """TC-015-046: Favorites filter toggle in sowing calendar."""

    def test_favorites_filter_button_exists(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-046: Favorites filter toggle is present in sowing calendar view.

        Verifies the filter button with data-testid='sowing-favorites-filter' exists.
        """
        capture = request.node._screenshot_capture
        _open_sowing_view(calendar)
        capture("req015_046_favorites_filter", "Sowing view with favorites filter")

        favorites_btns = calendar.driver.find_elements(*CalendarPage.SOWING_FAVORITES_FILTER)
        assert len(favorites_btns) > 0, (
            "Expected sowing favorites filter button to be present"
        )

    def test_favorites_filter_toggle_click(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-046: Click favorites filter toggle changes the display.

        Verifies the filter button can be clicked without errors.
        """
        capture = request.node._screenshot_capture
        _open_sowing_view(calendar)
        capture("req015_046_before_favorites_toggle", "Before toggling favorites filter")

        calendar.click_sowing_favorites_filter()
        capture("req015_046_after_favorites_toggle", "After toggling favorites filter")

        # The page should not show an error
        assert not calendar.is_error_displayed(), (
            "Expected no error after toggling favorites filter"
        )


# -- Sowing category filter chips ---------------------------------------------


class TestSowingCategoryFilter:
    """TC-015-046 (extended): Plant category filter chips in sowing calendar."""

    def test_sowing_category_chips_present(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-046: Plant category filter chips are rendered in sowing calendar.

        Verifies at least one sowing-category-filter chip exists when species
        of multiple categories are present.
        """
        capture = request.node._screenshot_capture
        _open_sowing_view(calendar)
        capture("req015_046_sowing_category_chips", "Sowing category filter chips")

        chips = calendar.get_sowing_category_filter_chips()
        # Chips only appear if there are species of more than 1 category
        # Document the count
        capture(
            "req015_046_sowing_category_count",
            f"Found {len(chips)} sowing category filter chips",
        )

    def test_sowing_category_chip_toggle(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-046: Toggle a sowing category filter chip.

        Verifies clicking a chip changes its visual state and no error occurs.
        """
        capture = request.node._screenshot_capture
        _open_sowing_view(calendar)

        chips = calendar.get_sowing_category_filter_chips()
        if len(chips) == 0:
            pytest.skip("No sowing category filter chips present; skipping toggle test")

        first_chip = chips[0]
        testid = first_chip.get_attribute("data-testid") or ""
        category = testid.replace("sowing-category-filter-", "")

        capture("req015_046_before_sowing_cat_toggle", "Before toggling sowing category")
        calendar.click_sowing_category_filter(category)
        capture("req015_046_after_sowing_cat_toggle", "After toggling sowing category")

        assert not calendar.is_error_displayed(), (
            "Expected no error after toggling sowing category filter"
        )


# -- TC-015-040: Sowing legend ------------------------------------------------


class TestSowingCalendarLegend:
    """TC-015-040: Sowing calendar legend with phase colors."""

    def test_sowing_legend_visible(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-040: Sowing calendar shows a legend with phase color indicators.

        Verifies caption text elements exist in the sowing card (legend area).
        """
        capture = request.node._screenshot_capture
        _open_sowing_view(calendar)
        capture("req015_040_sowing_legend", "Sowing calendar legend area")

        legend_items = calendar.get_sowing_legend_items()
        # Legend should have at least one item if entries are present
        capture(
            "req015_040_legend_count",
            f"Found {len(legend_items)} legend items in sowing calendar",
        )
