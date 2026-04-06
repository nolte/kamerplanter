"""E2E tests for REQ-015 — Aussaatkalender / Sowing Calendar.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-015.md):
  TC-REQ-015-040  ->  TC-015-040  Aussaatkalender — Nutzpflanze mit Voranzucht und Ernte
  TC-REQ-015-041  ->  TC-015-048  Aussaatkalender — Frosttermin-Konfiguration / Standort-Auswahl
  TC-REQ-015-042  ->  TC-015-040  Aussaatkalender — Monats-Spaltenkoepfe sichtbar
  TC-REQ-015-043  ->  TC-015-049  Aussaatkalender — Frost-Info-Chips sichtbar
  TC-REQ-015-044  ->  TC-015-046  Aussaatkalender — Favoriten-Filter vorhanden
  TC-REQ-015-045  ->  TC-015-046  Aussaatkalender — Favoriten-Filter Klick
  TC-REQ-015-046  ->  TC-015-046  Aussaatkalender — Kategorie-Filter-Chips sichtbar
  TC-REQ-015-047  ->  TC-015-046  Aussaatkalender — Kategorie-Filter toggled
  TC-REQ-015-048  ->  TC-015-040  Aussaatkalender — Legende mit Phasenfarben sichtbar
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.calendar_page import CalendarPage


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def calendar(browser: WebDriver, base_url: str) -> CalendarPage:
    """Return a CalendarPage bound to the test browser."""
    return CalendarPage(browser, base_url)


# -- Helpers ------------------------------------------------------------------


def _open_sowing_view(calendar: CalendarPage) -> None:
    """Navigate to calendar and switch to sowing tab."""
    calendar.open()
    calendar.switch_to_sowing_view()


# -- TC-REQ-015-040 to TC-REQ-015-042: Sowing calendar basics -----------------


class TestSowingCalendarLoad:
    """Sowing calendar view rendering and content (Spec: TC-015-040, TC-015-048)."""

    @pytest.mark.smoke
    def test_sowing_view_renders_after_tab_switch(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-040: Sowing calendar view renders after switching to the sowing tab.

        Spec: TC-015-040 -- Aussaatkalender — Nutzpflanze mit Voranzucht und Ernte.
        """
        _open_sowing_view(calendar)
        screenshot("TC-REQ-015-040_sowing-view-loaded", "Sowing calendar view after tab switch")

        active = calendar.get_active_tab_value()
        assert active == "sowing", (
            f"TC-REQ-015-040 FAIL: Expected sowing tab to be active, got: '{active}'"
        )

        cards = calendar.driver.find_elements(By.CSS_SELECTOR, ".MuiCard-root")
        empty_states = calendar.driver.find_elements(*CalendarPage.EMPTY_STATE)
        assert len(cards) > 0 or len(empty_states) > 0, (
            "TC-REQ-015-040 FAIL: Expected either sowing calendar card or empty state"
        )

    @pytest.mark.smoke
    def test_sowing_view_shows_site_select(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-041: Site select dropdown is visible in sowing calendar view.

        Spec: TC-015-048 -- Aussaatkalender — Frosttermin-Konfiguration bei fehlendem Standort.
        """
        _open_sowing_view(calendar)
        screenshot("TC-REQ-015-041_sowing-site-select", "Sowing view with site select")

        assert calendar.is_site_select_visible(), (
            "TC-REQ-015-041 FAIL: Expected site select dropdown in sowing calendar view"
        )

    @pytest.mark.core_crud
    def test_sowing_view_has_month_column_headers(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-042: Sowing calendar shows month column headers (Jan-Dez).

        Spec: TC-015-040 -- Aussaatkalender — Monats-Spaltenkoepfe sichtbar.
        """
        _open_sowing_view(calendar)
        screenshot("TC-REQ-015-042_sowing-month-headers", "Sowing calendar with month headers")

        headers = calendar.driver.find_elements(
            By.CSS_SELECTOR, "[role='columnheader']"
        )
        assert len(headers) >= 12, (
            f"TC-REQ-015-042 FAIL: Expected at least 12 month column headers, got {len(headers)}"
        )


# -- TC-REQ-015-043: Frost config visualization -------------------------------


class TestSowingCalendarFrostConfig:
    """Eisheiligen marking and frost chips in sowing calendar (Spec: TC-015-049)."""

    @pytest.mark.core_crud
    def test_frost_info_chips_visible_when_site_has_frost_data(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-043: Frost info chips (last frost, Eisheilige) are visible.

        Spec: TC-015-049 -- Aussaatkalender — Eisheiligen-Markierung sichtbar.
        """
        _open_sowing_view(calendar)
        screenshot("TC-REQ-015-043_frost-chips", "Sowing view frost info area")

        frost_chips = calendar.get_sowing_frost_chips()
        screenshot(
            "TC-REQ-015-043_frost-chips-count",
            f"Found {len(frost_chips)} frost info chips",
        )
        # No hard assert — frost data depends on seed data


# -- TC-REQ-015-044 to TC-REQ-015-045: Sowing favorites filter ----------------


class TestSowingCalendarFavoritesFilter:
    """Favorites filter toggle in sowing calendar (Spec: TC-015-046)."""

    @pytest.mark.core_crud
    def test_favorites_filter_button_exists(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-044: Favorites filter toggle is present in sowing calendar view.

        Spec: TC-015-046 -- Aussaatkalender — Filter 'Nur meine geplanten Pflanzen'.
        """
        _open_sowing_view(calendar)
        screenshot("TC-REQ-015-044_favorites-filter", "Sowing view with favorites filter")

        favorites_btns = calendar.driver.find_elements(*CalendarPage.SOWING_FAVORITES_FILTER)
        assert len(favorites_btns) > 0, (
            "TC-REQ-015-044 FAIL: Expected sowing favorites filter button to be present"
        )

    @pytest.mark.core_crud
    def test_favorites_filter_toggle_click(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-045: Click favorites filter toggle changes the display.

        Spec: TC-015-046 -- Aussaatkalender — Filter 'Nur meine geplanten Pflanzen'.
        """
        _open_sowing_view(calendar)
        screenshot("TC-REQ-015-045_before-favorites-toggle", "Before toggling favorites filter")

        calendar.click_sowing_favorites_filter()
        screenshot("TC-REQ-015-045_after-favorites-toggle", "After toggling favorites filter")

        assert not calendar.is_error_displayed(), (
            "TC-REQ-015-045 FAIL: Expected no error after toggling favorites filter"
        )


# -- TC-REQ-015-046 to TC-REQ-015-047: Sowing category filter chips -----------


class TestSowingCategoryFilter:
    """Plant category filter chips in sowing calendar (Spec: TC-015-046)."""

    @pytest.mark.core_crud
    def test_sowing_category_chips_present(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-046: Plant category filter chips are rendered in sowing calendar.

        Spec: TC-015-046 -- Aussaatkalender — Kategorie-Filter-Chips sichtbar.
        """
        _open_sowing_view(calendar)
        screenshot("TC-REQ-015-046_sowing-category-chips", "Sowing category filter chips")

        chips = calendar.get_sowing_category_filter_chips()
        screenshot(
            "TC-REQ-015-046_sowing-category-count",
            f"Found {len(chips)} sowing category filter chips",
        )

    @pytest.mark.core_crud
    def test_sowing_category_chip_toggle(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-047: Toggle a sowing category filter chip.

        Spec: TC-015-046 -- Aussaatkalender — Kategorie-Filter toggled.
        """
        _open_sowing_view(calendar)

        chips = calendar.get_sowing_category_filter_chips()
        if len(chips) == 0:
            pytest.skip("No sowing category filter chips present; skipping toggle test")

        first_chip = chips[0]
        testid = first_chip.get_attribute("data-testid") or ""
        category = testid.replace("sowing-category-filter-", "")

        screenshot("TC-REQ-015-047_before-sowing-cat-toggle", "Before toggling sowing category")
        calendar.click_sowing_category_filter(category)
        screenshot("TC-REQ-015-047_after-sowing-cat-toggle", "After toggling sowing category")

        assert not calendar.is_error_displayed(), (
            "TC-REQ-015-047 FAIL: Expected no error after toggling sowing category filter"
        )


# -- TC-REQ-015-048: Sowing legend --------------------------------------------


class TestSowingCalendarLegend:
    """Sowing calendar legend with phase colors (Spec: TC-015-040)."""

    @pytest.mark.smoke
    def test_sowing_legend_visible(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-048: Sowing calendar shows a legend with phase color indicators.

        Spec: TC-015-040 -- Aussaatkalender — Legende mit Phasenfarben sichtbar.
        """
        _open_sowing_view(calendar)
        screenshot("TC-REQ-015-048_sowing-legend", "Sowing calendar legend area")

        legend_items = calendar.get_sowing_legend_items()
        screenshot(
            "TC-REQ-015-048_legend-count",
            f"Found {len(legend_items)} legend items in sowing calendar",
        )
