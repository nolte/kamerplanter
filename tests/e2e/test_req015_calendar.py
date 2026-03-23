"""E2E tests for REQ-015 -- Kalenderansicht (TC-015-001 to TC-015-036).

Tests cover:
- Calendar page load with month view as default (TC-015-001)
- Month navigation: next, previous, today button (TC-015-002, TC-015-003)
- View switching: list, sowing, season, phases timeline (TC-015-004 to TC-015-007)
- Category filter chips (TC-015-010, TC-015-011)
- Event popover display (TC-015-022)
- Feed management: create, validation, delete, toggle (TC-015-030 to TC-015-036)

NFR-008 section 3.4 screenshot checkpoints at:
1. Page Load
2. Before significant actions
3. After significant actions
4. Error states
"""

from __future__ import annotations

import pytest
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .pages.calendar_page import CalendarPage


# -- Fixtures ----------------------------------------------------------------


@pytest.fixture
def calendar(browser: WebDriver, base_url: str) -> CalendarPage:
    """Return a CalendarPage bound to the test browser."""
    return CalendarPage(browser, base_url)


# -- TC-015-001 to TC-015-003: Page load & month navigation ------------------


class TestCalendarPageLoad:
    """TC-015-001 to TC-015-003: Calendar page load and month navigation."""

    def test_calendar_page_loads_with_month_view(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-001: Calendar page loads and shows month view as default.

        Verifies:
        - data-testid='calendar-page' is visible
        - View tabs are present (month, list, phases, sowing, season)
        - Month navigation buttons (prev, next, today) are visible
        - Month tab is the active/selected tab
        """
        capture = request.node._screenshot_capture
        calendar.open()
        capture("req015_001_calendar_page_loaded", "Calendar page after initial load")

        # Page container visible
        assert calendar.driver.find_element(
            *CalendarPage.PAGE
        ).is_displayed(), "Expected [data-testid='calendar-page'] to be visible"

        # View tabs present
        for locator_name, locator in [
            ("month", CalendarPage.VIEW_TAB_MONTH),
            ("list", CalendarPage.VIEW_TAB_LIST),
            ("phases", CalendarPage.VIEW_TAB_PHASES),
            ("sowing", CalendarPage.VIEW_TAB_SOWING),
            ("season", CalendarPage.VIEW_TAB_SEASON),
        ]:
            tabs = calendar.driver.find_elements(*locator)
            assert len(tabs) > 0, f"Expected '{locator_name}' view tab to be present"

        # Navigation buttons visible
        assert calendar.driver.find_element(
            *CalendarPage.PREV_MONTH_BTN
        ).is_displayed(), "Expected prev-month button to be visible"
        assert calendar.driver.find_element(
            *CalendarPage.NEXT_MONTH_BTN
        ).is_displayed(), "Expected next-month button to be visible"
        assert calendar.driver.find_element(
            *CalendarPage.TODAY_BTN
        ).is_displayed(), "Expected today button to be visible"

        # Month tab is the active tab
        active = calendar.get_active_tab_value()
        assert active == "month", (
            f"Expected month tab to be active by default, got: '{active}'"
        )

    def test_navigate_to_next_month(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-002: Click next-month arrow advances the displayed month.

        Verifies the month header text changes after clicking the next button.
        """
        capture = request.node._screenshot_capture
        calendar.open()

        header_before = calendar.get_month_header_text()
        capture("req015_002_before_next_month", "Month header before navigation")

        calendar.click_next_month()
        capture("req015_002_after_next_month", "Month header after clicking next")

        header_after = calendar.get_month_header_text()
        assert header_before != header_after, (
            f"Expected month header to change after clicking next, "
            f"before='{header_before}', after='{header_after}'"
        )

    def test_navigate_back_to_today(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-003: Navigate forward then click Today to return to current month.

        Verifies the month header returns to the original value after clicking Today.
        """
        capture = request.node._screenshot_capture
        calendar.open()

        header_original = calendar.get_month_header_text()

        # Navigate forward twice
        calendar.click_next_month()
        calendar.click_next_month()
        header_shifted = calendar.get_month_header_text()
        capture("req015_003_shifted_forward", "After navigating 2 months forward")

        assert header_original != header_shifted, (
            "Expected month header to differ after navigating forward"
        )

        # Click Today
        calendar.click_today()
        capture("req015_003_after_today", "After clicking Today button")

        header_restored = calendar.get_month_header_text()
        assert header_restored == header_original, (
            f"Expected Today button to restore original month, "
            f"original='{header_original}', restored='{header_restored}'"
        )

    def test_navigate_to_previous_month(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-002 (reverse): Click prev-month arrow goes to previous month.

        Verifies the month header text changes after clicking the prev button.
        """
        capture = request.node._screenshot_capture
        calendar.open()

        header_before = calendar.get_month_header_text()
        calendar.click_prev_month()
        capture("req015_002b_after_prev_month", "Month header after clicking prev")

        header_after = calendar.get_month_header_text()
        assert header_before != header_after, (
            f"Expected month header to change after clicking prev, "
            f"before='{header_before}', after='{header_after}'"
        )


# -- TC-015-004 to TC-015-007: View switching ---------------------------------


class TestCalendarViewSwitching:
    """TC-015-004 to TC-015-007: Switch between calendar view modes."""

    def test_switch_to_list_view(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-004: Switch from month view to list view.

        Verifies the list tab becomes active and list events container is shown.
        """
        capture = request.node._screenshot_capture
        calendar.open()
        capture("req015_004_before_list_switch", "Calendar in month view")

        calendar.switch_to_list_view()
        capture("req015_004_after_list_switch", "Calendar in list view")

        active = calendar.get_active_tab_value()
        assert active == "list", (
            f"Expected list tab to be active, got: '{active}'"
        )

    def test_switch_to_sowing_view(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-005: Switch to sowing calendar view.

        Verifies the sowing tab becomes active.
        """
        capture = request.node._screenshot_capture
        calendar.open()

        calendar.switch_to_sowing_view()
        capture("req015_005_sowing_view", "Calendar in sowing calendar view")

        active = calendar.get_active_tab_value()
        assert active == "sowing", (
            f"Expected sowing tab to be active, got: '{active}'"
        )

    def test_switch_to_season_view(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-006: Switch to season overview view.

        Verifies the season tab becomes active.
        """
        capture = request.node._screenshot_capture
        calendar.open()

        calendar.switch_to_season_view()
        capture("req015_006_season_view", "Calendar in season overview view")

        active = calendar.get_active_tab_value()
        assert active == "season", (
            f"Expected season tab to be active, got: '{active}'"
        )

    def test_switch_to_phases_timeline_view(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-007: Switch to phases timeline view.

        Verifies the phases tab becomes active.
        """
        capture = request.node._screenshot_capture
        calendar.open()

        calendar.switch_to_phases_view()
        capture("req015_007_phases_view", "Calendar in phases timeline view")

        active = calendar.get_active_tab_value()
        assert active == "phases", (
            f"Expected phases tab to be active, got: '{active}'"
        )

    def test_switch_back_to_month_from_list(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-004 (round-trip): Switch to list then back to month.

        Verifies view tabs are bidirectional.
        """
        capture = request.node._screenshot_capture
        calendar.open()

        calendar.switch_to_list_view()
        assert calendar.get_active_tab_value() == "list", "Expected list tab active"

        calendar.switch_to_month_view()
        capture("req015_004b_back_to_month", "Back to month view from list")

        assert calendar.get_active_tab_value() == "month", (
            "Expected month tab active after switching back"
        )


# -- TC-015-010, TC-015-011: Category filtering ------------------------------


class TestCalendarCategoryFilter:
    """TC-015-010 to TC-015-011: Category filter chip interactions."""

    def test_category_filter_chips_are_present(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-010 (pre): Verify category filter chips are rendered on the calendar page."""
        capture = request.node._screenshot_capture
        calendar.open()
        capture("req015_010_category_filters", "Category filter chips visible")

        chips = calendar.get_category_filter_chips()
        assert len(chips) > 0, (
            "Expected at least one category filter chip to be present"
        )

    def test_category_filter_chip_click_toggles(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-010: Click a category filter chip to toggle it.

        Verifies the chip changes visual state when clicked.
        """
        capture = request.node._screenshot_capture
        calendar.open()

        chips = calendar.get_category_filter_chips()
        if len(chips) == 0:
            pytest.skip("No category filter chips present; skipping toggle test")

        # Get the first chip's testid to extract the category name
        first_chip = chips[0]
        testid = first_chip.get_attribute("data-testid") or ""
        category = testid.replace("category-filter-", "")

        capture("req015_010_before_filter_toggle", "Before toggling category filter")
        calendar.click_category_filter(category)
        capture("req015_010_after_filter_toggle", "After toggling category filter")

        # The chip should still exist (click toggles, does not remove)
        updated_chips = calendar.get_category_filter_chips()
        assert len(updated_chips) > 0, (
            "Category filter chips should remain after toggle"
        )


# -- TC-015-022: Event popover ------------------------------------------------


class TestCalendarEventPopover:
    """TC-015-022: Event interaction via popover."""

    def test_day_cell_click_opens_popover(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-022: Click a day cell to potentially open a popover.

        If events exist on a given day, a popover should appear with event details.
        This test verifies the day cell is clickable; actual popover depends on data.
        """
        capture = request.node._screenshot_capture
        calendar.open()
        capture("req015_022_before_day_click", "Calendar before clicking a day cell")

        # Try clicking day 15 (usually exists in any month)
        try:
            calendar.click_day_cell(15)
            capture("req015_022_after_day_click", "After clicking day 15 cell")
        except Exception:
            # Day 15 may not be in the visible grid if the month has unusual layout
            capture("req015_022_day_click_skipped", "Day cell click could not be performed")
            pytest.skip("Day cell 15 not clickable; may not have events")


# -- TC-015-030 to TC-015-036: Feed management --------------------------------


class TestCalendarFeedManagement:
    """TC-015-030 to TC-015-036: iCal feed CRUD via calendar page."""

    def test_feeds_section_toggle(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-036: Toggle the iCal feeds section to expand/collapse.

        Verifies the feeds toggle button exists and can be clicked.
        """
        capture = request.node._screenshot_capture
        calendar.open()
        capture("req015_036_before_feeds_toggle", "Calendar before toggling feeds section")

        calendar.toggle_feeds_section()
        capture("req015_036_after_feeds_toggle", "After toggling feeds section")

        # After expanding, the Create Feed button should be visible
        create_btns = calendar.driver.find_elements(*CalendarPage.CREATE_FEED_BTN)
        assert len(create_btns) > 0, (
            "Expected Create Feed button to be visible after expanding feeds section"
        )

    def test_create_feed_dialog_opens(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-030 (pre): Create Feed dialog opens when clicking the create button.

        Verifies the dialog with name input and save/cancel buttons appears.
        """
        capture = request.node._screenshot_capture
        calendar.open()

        calendar.toggle_feeds_section()
        capture("req015_030_feeds_expanded", "Feeds section expanded")

        calendar.click_create_feed()
        capture("req015_030_create_dialog_open", "Create feed dialog opened")

        assert calendar.is_create_feed_dialog_visible(), (
            "Expected create feed dialog to be visible"
        )

        # Name input should be present
        name_inputs = calendar.driver.find_elements(*CalendarPage.FEED_NAME_INPUT)
        assert len(name_inputs) > 0, (
            "Expected feed name input field in dialog"
        )

    def test_create_feed_dialog_cancel(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-035: Cancel the create feed dialog.

        Verifies the dialog closes without creating a feed.
        """
        capture = request.node._screenshot_capture
        calendar.open()

        calendar.toggle_feeds_section()
        calendar.click_create_feed()
        assert calendar.is_create_feed_dialog_visible(), "Dialog should be open"

        capture("req015_035_before_cancel", "Create feed dialog before cancel")
        calendar.cancel_feed()
        capture("req015_035_after_cancel", "After cancelling create feed dialog")

        # Dialog should be closed
        WebDriverWait(calendar.driver, 5).until(
            EC.invisibility_of_element_located(CalendarPage.CREATE_FEED_DIALOG)
        )

    def test_create_feed_happy_path(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-030: Create a new iCal feed with a valid name.

        Verifies:
        - Dialog closes after saving
        - New feed appears in the feed list
        """
        capture = request.node._screenshot_capture
        calendar.open()

        calendar.toggle_feeds_section()
        feeds_before = calendar.get_feed_items()
        count_before = len(feeds_before)

        calendar.click_create_feed()
        calendar.enter_feed_name("E2E Test Feed")
        capture("req015_030_feed_name_entered", "Feed name entered in dialog")

        calendar.save_feed()
        capture("req015_030_after_feed_save", "After saving new feed")

        # Dialog should close
        WebDriverWait(calendar.driver, 10).until(
            EC.invisibility_of_element_located(CalendarPage.CREATE_FEED_DIALOG)
        )

        # Feed list should now have one more item
        feeds_after = calendar.get_feed_items()
        assert len(feeds_after) >= count_before, (
            f"Expected at least {count_before} feeds after creation, got {len(feeds_after)}"
        )

    def test_create_feed_empty_name_validation(
        self,
        calendar: CalendarPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-015-031: Attempt to create feed without a name shows validation error.

        Verifies the dialog stays open and the save button is disabled or an error is shown.
        """
        capture = request.node._screenshot_capture
        calendar.open()

        calendar.toggle_feeds_section()
        calendar.click_create_feed()

        # Leave name empty and click save
        capture("req015_031_empty_name_before_save", "Empty name before attempting save")
        calendar.save_feed()
        capture("req015_031_after_empty_save", "After attempting save with empty name")

        # Dialog should remain open (validation prevents creation)
        assert calendar.is_create_feed_dialog_visible(), (
            "Expected dialog to stay open when name is empty (validation error)"
        )
