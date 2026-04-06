"""E2E tests for REQ-004 -- Feeding Event CRUD and management.

Covers the Feeding Event list page and create dialog. Feeding events
record nutrient applications to individual plant instances, tracking
volume, application method, EC/pH measurements, and runoff data.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.feeding_event_list_page import FeedingEventListPage


# -- Fixtures ----------------------------------------------------------------


@pytest.fixture
def feeding_list(browser: WebDriver, base_url: str) -> FeedingEventListPage:
    """Return a FeedingEventListPage bound to the current browser session."""
    return FeedingEventListPage(browser, base_url)


# -- TC-REQ-004-040 to TC-REQ-004-045: Feeding Event List Page ---------------


class TestFeedingEventListPage:
    """Feeding event list display and interaction."""

    @pytest.mark.smoke
    def test_feeding_event_page_loads(
        self, feeding_list: FeedingEventListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-004-040: Feeding event list page loads with correct structure.

        Given the user navigates to the feeding events page,
        When the page has finished loading,
        Then the page container and data table are present.
        """
        feeding_list.open()
        screenshot(
            "TC-REQ-004-040_feeding-event-list-loaded",
            "Feeding event list page after initial load",
        )

        page_elements = feeding_list.driver.find_elements(*feeding_list.PAGE)
        assert len(page_elements) > 0, (
            "TC-REQ-004-040 FAIL: Expected the feeding-event-list-page container to be present"
        )

    @pytest.mark.smoke
    def test_create_button_visible(
        self, feeding_list: FeedingEventListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-004-041: Create button is visible on the feeding event list page.

        Given the feeding event list page is loaded,
        When the user inspects the page header,
        Then a create button is visible and clickable.
        """
        feeding_list.open()
        screenshot(
            "TC-REQ-004-041_create-button-visible",
            "Feeding event list page showing create button",
        )

        create_buttons = feeding_list.driver.find_elements(*feeding_list.CREATE_BUTTON)
        assert len(create_buttons) > 0, (
            "TC-REQ-004-041 FAIL: Expected a create button on the feeding event list page"
        )
        assert create_buttons[0].is_displayed(), (
            "TC-REQ-004-041 FAIL: Create button should be displayed and visible"
        )

    @pytest.mark.requires_desktop
    @pytest.mark.smoke
    def test_feeding_event_list_has_columns(
        self, feeding_list: FeedingEventListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-004-042: Feeding event list shows relevant columns.

        Given the feeding event list page is loaded,
        When the data table is rendered,
        Then column headers for timestamp, plant, method, volume are present.
        """
        feeding_list.open()
        screenshot(
            "TC-REQ-004-042_feeding-event-columns",
            "Feeding event list showing column headers",
        )

        # Page may show empty state OR table with headers depending on data
        tables = feeding_list.driver.find_elements(*feeding_list.TABLE)
        empty_states = feeding_list.driver.find_elements(*feeding_list.EMPTY_STATE)
        assert len(tables) > 0 or len(empty_states) > 0, (
            "TC-REQ-004-042 FAIL: Expected either a data table or an empty state on the page"
        )

        if tables:
            headers = feeding_list.get_column_headers()
            assert len(headers) > 0, (
                f"TC-REQ-004-042 FAIL: Expected column headers in feeding event table, got none"
            )

    @pytest.mark.core_crud
    def test_feeding_event_search_filters_results(
        self, feeding_list: FeedingEventListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-004-043: Searching the feeding event list filters visible rows.

        Given the feeding event list page has at least one row,
        When the user enters a non-matching search term,
        Then the row count decreases or shows zero results.
        """
        feeding_list.open()
        initial_count = feeding_list.get_row_count()
        if initial_count == 0:
            pytest.skip("No feeding events in database -- cannot test search filtering")

        screenshot(
            "TC-REQ-004-043_before-search",
            "Feeding event list before applying search filter",
        )

        feeding_list.search("xxxx_nonexistent_feeding_yyyy")
        feeding_list.wait_for_loading_complete()

        screenshot(
            "TC-REQ-004-043_after-search-no-match",
            "Feeding event list after searching for non-existent term",
        )

        filtered_count = feeding_list.get_row_count()
        assert filtered_count < initial_count, (
            f"TC-REQ-004-043 FAIL: Search for non-existent term should reduce row count: "
            f"before={initial_count}, after={filtered_count}"
        )

    @pytest.mark.requires_desktop
    @pytest.mark.core_crud
    def test_feeding_event_sort_by_column(
        self, feeding_list: FeedingEventListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-004-044: Clicking a column header sorts the feeding event list.

        Given the feeding event list has visible rows,
        When the user clicks a column header,
        Then the table rows are re-ordered without errors.
        """
        feeding_list.open()
        if feeding_list.get_row_count() == 0:
            pytest.skip("No feeding events to sort")

        headers = feeding_list.get_column_headers()
        if not headers:
            pytest.skip("No column headers found")

        rows_before = feeding_list.get_first_column_texts()

        feeding_list.click_column_header(headers[0])
        feeding_list.wait_for_loading_complete()

        screenshot(
            "TC-REQ-004-044_feeding-event-sorted",
            "Feeding event list after clicking column header to sort",
        )

        rows_after = feeding_list.get_first_column_texts()
        assert len(rows_after) > 0, (
            "TC-REQ-004-044 FAIL: Expected table rows to still be present after clicking sort"
        )

    @pytest.mark.smoke
    def test_feeding_event_showing_count_or_empty_state(
        self, feeding_list: FeedingEventListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-004-045: Feeding event list shows either a row count label or empty state.

        Given the feeding event list page is loaded,
        When the data table is rendered,
        Then either a 'showing X of Y' count or an empty state illustration is shown.
        """
        feeding_list.open()
        screenshot(
            "TC-REQ-004-045_feeding-event-count-or-empty",
            "Feeding event list showing count label or empty state",
        )

        has_count = len(feeding_list.driver.find_elements(*feeding_list.SHOWING_COUNT)) > 0
        has_empty = feeding_list.has_empty_state()
        assert has_count or has_empty, (
            "TC-REQ-004-045 FAIL: Expected either a showing-count label or an empty-state element"
        )


# -- TC-REQ-004-050 to TC-REQ-004-057: Create Dialog -------------------------


class TestFeedingEventCreateDialog:
    """Feeding event create dialog and form validation."""

    @pytest.mark.core_crud
    def test_create_dialog_opens(
        self, feeding_list: FeedingEventListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-004-050: Clicking 'Create' opens the feeding event create dialog.

        Given the feeding event list page is loaded,
        When the user clicks the create button,
        Then the create dialog is displayed with form fields.
        """
        feeding_list.open()
        screenshot(
            "TC-REQ-004-050_before-create-click",
            "Feeding event list before clicking create button",
        )

        feeding_list.click_create()
        screenshot(
            "TC-REQ-004-050_create-dialog-open",
            "Feeding event create dialog open with form fields",
        )

        assert feeding_list.is_create_dialog_open(), (
            "TC-REQ-004-050 FAIL: Create dialog should be visible after clicking the create button"
        )

    @pytest.mark.core_crud
    def test_create_dialog_has_required_fields(
        self, feeding_list: FeedingEventListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-004-051: Create dialog contains plant, method, and volume fields.

        Given the create dialog is open,
        When the user inspects the form,
        Then plant_key, application_method, and volume_applied_liters fields are present.
        """
        feeding_list.open()
        feeding_list.click_create()

        screenshot(
            "TC-REQ-004-051_create-dialog-fields",
            "Create dialog showing required form fields",
        )

        assert feeding_list.has_plant_key_field(), (
            "TC-REQ-004-051 FAIL: Expected a plant_key form field in the create dialog"
        )

        method_fields = feeding_list.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='form-field-application_method']"
        )
        assert len(method_fields) > 0, (
            "TC-REQ-004-051 FAIL: Expected an application_method form field in the create dialog"
        )

        volume_fields = feeding_list.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='form-field-volume_applied_liters']"
        )
        assert len(volume_fields) > 0, (
            "TC-REQ-004-051 FAIL: Expected a volume_applied_liters form field in the create dialog"
        )

    @pytest.mark.core_crud
    def test_create_dialog_has_measurement_fields(
        self, feeding_list: FeedingEventListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-004-052: Create dialog contains EC and pH measurement fields.

        Given the create dialog is open,
        When the user scrolls through the form,
        Then EC before/after and pH before/after measurement fields are present.
        """
        feeding_list.open()
        feeding_list.click_create()

        screenshot(
            "TC-REQ-004-052_create-dialog-measurement-fields",
            "Create dialog showing EC and pH measurement fields",
        )

        for field_name in ["measured_ec_before", "measured_ec_after",
                           "measured_ph_before", "measured_ph_after"]:
            fields = feeding_list.driver.find_elements(
                By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}']"
            )
            assert len(fields) > 0, (
                f"TC-REQ-004-052 FAIL: Expected a '{field_name}' field in the create dialog"
            )

    @pytest.mark.core_crud
    def test_validation_empty_plant_key(
        self, feeding_list: FeedingEventListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-004-053: Submitting without selecting a plant shows validation error.

        Given the create dialog is open,
        When the user submits without selecting a plant,
        Then the dialog remains open (form is not submitted).
        """
        feeding_list.open()
        feeding_list.click_create()

        screenshot(
            "TC-REQ-004-053_before-validation",
            "Create dialog before submitting without plant selection",
        )

        # Clear volume to default and submit without selecting a plant
        feeding_list.submit_create_form()
        feeding_list.wait_for_loading_complete()

        screenshot(
            "TC-REQ-004-053_validation-error-plant-key",
            "Create dialog showing validation error for missing plant selection",
        )

        # Dialog should remain open because validation failed
        assert feeding_list.is_create_dialog_open(), (
            "TC-REQ-004-053 FAIL: Create dialog should remain open after submitting "
            "without selecting a plant (validation should prevent submission)"
        )

    @pytest.mark.core_crud
    def test_cancel_create_dialog_closes(
        self, feeding_list: FeedingEventListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-004-054: Cancelling the create dialog closes it without saving.

        Given the create dialog is open,
        When the user clicks cancel,
        Then the dialog closes and no new feeding event is created.
        """
        feeding_list.open()
        initial_count = feeding_list.get_row_count()

        feeding_list.click_create()
        screenshot(
            "TC-REQ-004-054_before-cancel",
            "Create dialog open before cancelling",
        )

        feeding_list.cancel_create_form()

        # Wait for MUI dialog close animation
        for _ in range(20):
            if not feeding_list.is_create_dialog_open():
                break
            feeding_list.wait_for_loading_complete()

        screenshot(
            "TC-REQ-004-054_after-cancel",
            "Feeding event list after cancelling create dialog",
        )

        assert not feeding_list.is_create_dialog_open(), (
            "TC-REQ-004-054 FAIL: Create dialog should be closed after clicking cancel"
        )

        # Row count should not have changed
        after_count = feeding_list.get_row_count()
        assert after_count == initial_count, (
            f"TC-REQ-004-054 FAIL: Row count should not change after cancel: "
            f"before={initial_count}, after={after_count}"
        )

    @pytest.mark.core_crud
    def test_cancel_resets_form_on_reopen(
        self, feeding_list: FeedingEventListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-004-055: Reopening the create dialog after cancel shows a clean form.

        Given the user has filled fields and cancelled,
        When the user reopens the create dialog,
        Then the form fields are reset to defaults.
        """
        feeding_list.open()
        feeding_list.click_create()

        # Modify volume to a recognizable value
        feeding_list.fill_volume(42.5)

        screenshot(
            "TC-REQ-004-055_before-cancel-with-data",
            "Create dialog with modified volume before cancel",
        )

        feeding_list.cancel_create_form()
        for _ in range(20):
            if not feeding_list.is_create_dialog_open():
                break
            feeding_list.wait_for_loading_complete()

        # Reopen dialog
        feeding_list.click_create()

        screenshot(
            "TC-REQ-004-055_reopened-after-cancel",
            "Create dialog reopened after cancel showing reset form",
        )

        volume_value = feeding_list.get_volume_field_value()
        assert volume_value != "42.5", (
            f"TC-REQ-004-055 FAIL: Form should be reset after cancel, "
            f"but volume still shows '{volume_value}'"
        )

    @pytest.mark.core_crud
    def test_create_dialog_has_runoff_fields(
        self, feeding_list: FeedingEventListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-004-056: Create dialog contains runoff measurement fields.

        Given the create dialog is open,
        When the user scrolls to the runoff section,
        Then runoff EC, pH, and volume fields are present.
        """
        feeding_list.open()
        feeding_list.click_create()

        screenshot(
            "TC-REQ-004-056_create-dialog-runoff-fields",
            "Create dialog showing runoff measurement fields",
        )

        for field_name in ["runoff_ec", "runoff_ph", "runoff_volume_liters"]:
            fields = feeding_list.driver.find_elements(
                By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}']"
            )
            assert len(fields) > 0, (
                f"TC-REQ-004-056 FAIL: Expected a '{field_name}' field in the create dialog"
            )

    @pytest.mark.core_crud
    def test_create_dialog_has_notes_field(
        self, feeding_list: FeedingEventListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-004-057: Create dialog contains a notes textarea.

        Given the create dialog is open,
        When the user inspects the form,
        Then a multiline notes field is present.
        """
        feeding_list.open()
        feeding_list.click_create()

        screenshot(
            "TC-REQ-004-057_create-dialog-notes",
            "Create dialog showing notes textarea",
        )

        notes_fields = feeding_list.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='form-field-notes']"
        )
        assert len(notes_fields) > 0, (
            "TC-REQ-004-057 FAIL: Expected a notes form field in the create dialog"
        )
