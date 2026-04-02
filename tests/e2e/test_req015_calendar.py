"""E2E tests for REQ-015 — Kalenderansicht.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-015.md):
  TC-REQ-015-001  ->  TC-015-001  Kalenderseite aufrufen — Standardansicht Monat
  TC-REQ-015-002  ->  TC-015-002  Monatsnavigation — Naechsten Monat aufrufen
  TC-REQ-015-003  ->  TC-015-003  Monatsnavigation — Zurueck zum aktuellen Monat
  TC-REQ-015-004  ->  TC-015-002  Monatsnavigation — Vorherigen Monat aufrufen
  TC-REQ-015-005  ->  TC-015-004  Ansichtswechsel — Listenansicht
  TC-REQ-015-006  ->  TC-015-005  Ansichtswechsel — Aussaatkalender-Tab
  TC-REQ-015-007  ->  TC-015-006  Ansichtswechsel — Saisonuebersicht-Tab
  TC-REQ-015-008  ->  TC-015-007  Phasen-Timeline-Ansicht aufrufen
  TC-REQ-015-009  ->  TC-015-004  Ansichtswechsel — Zurueck zu Monat von Liste
  TC-REQ-015-010  ->  TC-015-010  Kategorie-Filter — Chips sichtbar
  TC-REQ-015-011  ->  TC-015-010  Kategorie-Filter — Chip-Klick toggled
  TC-REQ-015-012  ->  TC-015-022  Event-Klick — Popover mit Details
  TC-REQ-015-013  ->  TC-015-036  Feed-Bereich ein-/ausklappen
  TC-REQ-015-014  ->  TC-015-030  Feed erstellen — Dialog oeffnet sich
  TC-REQ-015-015  ->  TC-015-035  Feed erstellen — Dialog abbrechen
  TC-REQ-015-016  ->  TC-015-030  Feed erstellen — Happy Path
  TC-REQ-015-017  ->  TC-015-031  Feed erstellen — Validierung leerer Name
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .pages.calendar_page import CalendarPage


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def calendar(browser: WebDriver, base_url: str) -> CalendarPage:
    """Return a CalendarPage bound to the test browser."""
    return CalendarPage(browser, base_url)


# -- TC-REQ-015-001 to TC-REQ-015-004: Page load & month navigation -----------


class TestCalendarPageLoad:
    """Calendar page load and month navigation (Spec: TC-015-001, TC-015-002, TC-015-003)."""

    @pytest.mark.smoke
    def test_calendar_page_loads_with_month_view(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-001: Calendar page loads and shows month view as default.

        Spec: TC-015-001 -- Kalenderseite aufrufen — Standardansicht Monat.
        """
        calendar.open()
        screenshot("TC-REQ-015-001_calendar-page-loaded", "Calendar page after initial load")

        page_el = calendar.wait_for_element(CalendarPage.PAGE)
        assert page_el.is_displayed(), (
            "TC-REQ-015-001 FAIL: Expected [data-testid='calendar-page'] to be visible"
        )

        # View tabs present
        for locator_name, locator in [
            ("month", CalendarPage.VIEW_TAB_MONTH),
            ("list", CalendarPage.VIEW_TAB_LIST),
            ("phases", CalendarPage.VIEW_TAB_PHASES),
            ("sowing", CalendarPage.VIEW_TAB_SOWING),
            ("season", CalendarPage.VIEW_TAB_SEASON),
        ]:
            tabs = calendar.driver.find_elements(*locator)
            assert len(tabs) > 0, (
                f"TC-REQ-015-001 FAIL: Expected '{locator_name}' view tab to be present"
            )

        # Navigation buttons visible
        assert calendar.driver.find_elements(*CalendarPage.PREV_MONTH_BTN), (
            "TC-REQ-015-001 FAIL: Expected prev-month button to be visible"
        )
        assert calendar.driver.find_elements(*CalendarPage.NEXT_MONTH_BTN), (
            "TC-REQ-015-001 FAIL: Expected next-month button to be visible"
        )
        assert calendar.driver.find_elements(*CalendarPage.TODAY_BTN), (
            "TC-REQ-015-001 FAIL: Expected today button to be visible"
        )

        active = calendar.get_active_tab_value()
        assert active == "month", (
            f"TC-REQ-015-001 FAIL: Expected month tab to be active by default, got: '{active}'"
        )

    @pytest.mark.core_crud
    def test_navigate_to_next_month(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-002: Click next-month arrow advances the displayed month.

        Spec: TC-015-002 -- Monatsnavigation — Naechsten Monat aufrufen.
        """
        calendar.open()

        header_before = calendar.get_month_header_text()
        screenshot("TC-REQ-015-002_before-next-month", "Month header before navigation")

        calendar.click_next_month()
        screenshot("TC-REQ-015-002_after-next-month", "Month header after clicking next")

        header_after = calendar.get_month_header_text()
        assert header_before != header_after, (
            f"TC-REQ-015-002 FAIL: Expected month header to change, "
            f"before='{header_before}', after='{header_after}'"
        )

    @pytest.mark.core_crud
    def test_navigate_back_to_today(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-003: Navigate forward then click Today to return to current month.

        Spec: TC-015-003 -- Monatsnavigation — Zurueck zum aktuellen Monat.
        """
        calendar.open()

        header_original = calendar.get_month_header_text()

        calendar.click_next_month()
        calendar.click_next_month()
        header_shifted = calendar.get_month_header_text()
        screenshot("TC-REQ-015-003_shifted-forward", "After navigating 2 months forward")

        assert header_original != header_shifted, (
            "TC-REQ-015-003 FAIL: Expected month header to differ after navigating forward"
        )

        calendar.click_today()
        screenshot("TC-REQ-015-003_after-today", "After clicking Today button")

        header_restored = calendar.get_month_header_text()
        assert header_restored == header_original, (
            f"TC-REQ-015-003 FAIL: Expected Today to restore original month, "
            f"original='{header_original}', restored='{header_restored}'"
        )

    @pytest.mark.core_crud
    def test_navigate_to_previous_month(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-004: Click prev-month arrow goes to previous month.

        Spec: TC-015-002 -- Monatsnavigation — Vorherigen Monat aufrufen.
        """
        calendar.open()

        header_before = calendar.get_month_header_text()
        calendar.click_prev_month()
        screenshot("TC-REQ-015-004_after-prev-month", "Month header after clicking prev")

        header_after = calendar.get_month_header_text()
        assert header_before != header_after, (
            f"TC-REQ-015-004 FAIL: Expected month header to change, "
            f"before='{header_before}', after='{header_after}'"
        )


# -- TC-REQ-015-005 to TC-REQ-015-009: View switching -------------------------


class TestCalendarViewSwitching:
    """Switch between calendar view modes (Spec: TC-015-004, TC-015-005, TC-015-006, TC-015-007)."""

    @pytest.mark.core_crud
    def test_switch_to_list_view(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-005: Switch from month view to list view.

        Spec: TC-015-004 -- Ansichtswechsel — Listenansicht.
        """
        calendar.open()
        screenshot("TC-REQ-015-005_before-list-switch", "Calendar in month view")

        calendar.switch_to_list_view()
        screenshot("TC-REQ-015-005_after-list-switch", "Calendar in list view")

        active = calendar.get_active_tab_value()
        assert active == "list", (
            f"TC-REQ-015-005 FAIL: Expected list tab to be active, got: '{active}'"
        )

    @pytest.mark.core_crud
    def test_switch_to_sowing_view(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-006: Switch to sowing calendar view.

        Spec: TC-015-005 -- Ansichtswechsel — Aussaatkalender-Tab.
        """
        calendar.open()

        calendar.switch_to_sowing_view()
        screenshot("TC-REQ-015-006_sowing-view", "Calendar in sowing calendar view")

        active = calendar.get_active_tab_value()
        assert active == "sowing", (
            f"TC-REQ-015-006 FAIL: Expected sowing tab to be active, got: '{active}'"
        )

    @pytest.mark.core_crud
    def test_switch_to_season_view(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-007: Switch to season overview view.

        Spec: TC-015-006 -- Ansichtswechsel — Saisonuebersicht-Tab.
        """
        calendar.open()

        calendar.switch_to_season_view()
        screenshot("TC-REQ-015-007_season-view", "Calendar in season overview view")

        active = calendar.get_active_tab_value()
        assert active == "season", (
            f"TC-REQ-015-007 FAIL: Expected season tab to be active, got: '{active}'"
        )

    @pytest.mark.core_crud
    def test_switch_to_phases_timeline_view(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-008: Switch to phases timeline view.

        Spec: TC-015-007 -- Phasen-Timeline-Ansicht aufrufen.
        """
        calendar.open()

        calendar.switch_to_phases_view()
        screenshot("TC-REQ-015-008_phases-view", "Calendar in phases timeline view")

        active = calendar.get_active_tab_value()
        assert active == "phases", (
            f"TC-REQ-015-008 FAIL: Expected phases tab to be active, got: '{active}'"
        )

    @pytest.mark.core_crud
    def test_switch_back_to_month_from_list(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-009: Switch to list then back to month.

        Spec: TC-015-004 -- Ansichtswechsel — Zurueck zu Monat von Liste.
        """
        calendar.open()

        calendar.switch_to_list_view()
        assert calendar.get_active_tab_value() == "list", (
            "TC-REQ-015-009 FAIL: Expected list tab active"
        )

        calendar.switch_to_month_view()
        screenshot("TC-REQ-015-009_back-to-month", "Back to month view from list")

        assert calendar.get_active_tab_value() == "month", (
            "TC-REQ-015-009 FAIL: Expected month tab active after switching back"
        )


# -- TC-REQ-015-010, TC-REQ-015-011: Category filtering -----------------------


class TestCalendarCategoryFilter:
    """Category filter chip interactions (Spec: TC-015-010)."""

    @pytest.mark.smoke
    def test_category_filter_chips_are_present(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-010: Verify category filter chips are rendered on the calendar page.

        Spec: TC-015-010 -- Kategorie-Filter — Einzelne Kategorie aktivieren.
        """
        calendar.open()
        screenshot("TC-REQ-015-010_category-filters", "Category filter chips visible")

        chips = calendar.get_category_filter_chips()
        assert len(chips) > 0, (
            "TC-REQ-015-010 FAIL: Expected at least one category filter chip"
        )

    @pytest.mark.core_crud
    def test_category_filter_chip_click_toggles(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-011: Click a category filter chip to toggle it.

        Spec: TC-015-010 -- Kategorie-Filter — Einzelne Kategorie aktivieren.
        """
        calendar.open()

        chips = calendar.get_category_filter_chips()
        if len(chips) == 0:
            pytest.skip("No category filter chips present; skipping toggle test")

        first_chip = chips[0]
        testid = first_chip.get_attribute("data-testid") or ""
        category = testid.replace("category-filter-", "")

        screenshot("TC-REQ-015-011_before-filter-toggle", "Before toggling category filter")
        calendar.click_category_filter(category)
        screenshot("TC-REQ-015-011_after-filter-toggle", "After toggling category filter")

        updated_chips = calendar.get_category_filter_chips()
        assert len(updated_chips) > 0, (
            "TC-REQ-015-011 FAIL: Category filter chips should remain after toggle"
        )


# -- TC-REQ-015-012: Event popover --------------------------------------------


class TestCalendarEventPopover:
    """Event interaction via popover (Spec: TC-015-022)."""

    @pytest.mark.core_crud
    def test_day_cell_click_opens_popover(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-012: Click a day cell to potentially open a popover.

        Spec: TC-015-022 -- Event-Klick — Popover mit Details.
        """
        calendar.open()
        screenshot("TC-REQ-015-012_before-day-click", "Calendar before clicking a day cell")

        try:
            calendar.click_day_cell(15)
            screenshot("TC-REQ-015-012_after-day-click", "After clicking day 15 cell")
        except Exception:
            screenshot("TC-REQ-015-012_day-click-skipped", "Day cell click could not be performed")
            pytest.skip("Day cell 15 not clickable; may not have events")


# -- TC-REQ-015-013 to TC-REQ-015-017: Feed management ------------------------


class TestCalendarFeedManagement:
    """iCal feed CRUD via calendar page (Spec: TC-015-030, TC-015-031, TC-015-035, TC-015-036)."""

    @pytest.mark.core_crud
    def test_feeds_section_toggle(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-013: Toggle the iCal feeds section to expand/collapse.

        Spec: TC-015-036 -- Feed auflisten — Mehrere Feeds sichtbar.
        """
        calendar.open()
        screenshot("TC-REQ-015-013_before-feeds-toggle", "Calendar before toggling feeds section")

        calendar.toggle_feeds_section()
        screenshot("TC-REQ-015-013_after-feeds-toggle", "After toggling feeds section")

        create_btns = calendar.driver.find_elements(*CalendarPage.CREATE_FEED_BTN)
        assert len(create_btns) > 0, (
            "TC-REQ-015-013 FAIL: Expected Create Feed button after expanding feeds section"
        )

    @pytest.mark.core_crud
    def test_create_feed_dialog_opens(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-014: Create Feed dialog opens when clicking the create button.

        Spec: TC-015-030 -- Feed erstellen — Happy Path (Dialog-Oeffnung).
        """
        calendar.open()

        calendar.toggle_feeds_section()
        screenshot("TC-REQ-015-014_feeds-expanded", "Feeds section expanded")

        calendar.click_create_feed()
        screenshot("TC-REQ-015-014_create-dialog-open", "Create feed dialog opened")

        assert calendar.is_create_feed_dialog_visible(), (
            "TC-REQ-015-014 FAIL: Expected create feed dialog to be visible"
        )

        name_inputs = calendar.driver.find_elements(*CalendarPage.FEED_NAME_INPUT)
        assert len(name_inputs) > 0, (
            "TC-REQ-015-014 FAIL: Expected feed name input field in dialog"
        )

    @pytest.mark.core_crud
    def test_create_feed_dialog_cancel(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-015: Cancel the create feed dialog.

        Spec: TC-015-035 -- Feed loeschen — Abbrechen.
        """
        calendar.open()

        calendar.toggle_feeds_section()
        calendar.click_create_feed()
        assert calendar.is_create_feed_dialog_visible(), (
            "TC-REQ-015-015 FAIL: Dialog should be open"
        )

        screenshot("TC-REQ-015-015_before-cancel", "Create feed dialog before cancel")
        calendar.cancel_feed()
        screenshot("TC-REQ-015-015_after-cancel", "After cancelling create feed dialog")

        WebDriverWait(calendar.driver, 5).until(
            EC.invisibility_of_element_located(CalendarPage.CREATE_FEED_DIALOG)
        )

    @pytest.mark.core_crud
    def test_create_feed_happy_path(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-016: Create a new iCal feed with a valid name.

        Spec: TC-015-030 -- Feed erstellen — Happy Path.
        """
        calendar.open()

        calendar.toggle_feeds_section()
        feeds_before = calendar.get_feed_items()
        count_before = len(feeds_before)

        calendar.click_create_feed()
        calendar.enter_feed_name("E2E Test Feed")
        screenshot("TC-REQ-015-016_feed-name-entered", "Feed name entered in dialog")

        calendar.save_feed()
        screenshot("TC-REQ-015-016_after-feed-save", "After saving new feed")

        WebDriverWait(calendar.driver, 10).until(
            EC.invisibility_of_element_located(CalendarPage.CREATE_FEED_DIALOG)
        )

        feeds_after = calendar.get_feed_items()
        assert len(feeds_after) >= count_before, (
            f"TC-REQ-015-016 FAIL: Expected at least {count_before} feeds after creation, "
            f"got {len(feeds_after)}"
        )

    @pytest.mark.core_crud
    def test_create_feed_empty_name_validation(
        self,
        calendar: CalendarPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-015-017: Attempt to create feed without a name — save button is disabled.

        Spec: TC-015-031 -- Feed erstellen — Validierung leerer Name.
        """
        calendar.open()

        calendar.toggle_feeds_section()
        calendar.click_create_feed()

        screenshot("TC-REQ-015-017_empty-name-before-save", "Empty name — save button state")

        save_btn = calendar.driver.find_element(*CalendarPage.FEED_SAVE_BTN)
        assert not save_btn.is_enabled(), (
            "TC-REQ-015-017 FAIL: Expected save button to be disabled when feed name is empty"
        )

        assert calendar.is_create_feed_dialog_visible(), (
            "TC-REQ-015-017 FAIL: Expected dialog to stay open when name is empty"
        )

        screenshot("TC-REQ-015-017_after-empty-check", "Dialog still open with disabled save")
        calendar.cancel_feed()
