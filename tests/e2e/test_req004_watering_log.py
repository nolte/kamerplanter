"""E2E tests for REQ-004 — Giessprotokoll (Watering Log).

Covers the watering log list page, create dialog, and detail page.
The watering log is a daily-use feature for documenting irrigation events
including volume, EC/pH measurements, and fertilizer usage.

Spec-TC Mapping:
  TC-REQ-004-W001  List page renders with data-testid
  TC-REQ-004-W002  Create button is visible
  TC-REQ-004-W003  Create dialog opens on button click
  TC-REQ-004-W004  Create watering log — Happy Path
  TC-REQ-004-W005  Pflichtfeld-Validierung (volume > 0)
  TC-REQ-004-W006  Cancel closes dialog without changes
  TC-REQ-004-W007  Search filters table rows
  TC-REQ-004-W008  Click on row navigates to detail page
  TC-REQ-004-W009  Detail page shows watering data with tabs
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .pages.watering_log_detail_page import WateringLogDetailPage
from .pages.watering_log_list_page import WateringLogListPage


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def watering_list(browser: WebDriver, base_url: str) -> WateringLogListPage:
    """Return a WateringLogListPage bound to the test browser."""
    return WateringLogListPage(browser, base_url)


@pytest.fixture
def watering_detail(browser: WebDriver, base_url: str) -> WateringLogDetailPage:
    """Return a WateringLogDetailPage bound to the test browser."""
    return WateringLogDetailPage(browser, base_url)


# -- TC-REQ-004-W001 to TC-REQ-004-W002: List Page ----------------------------


class TestWateringLogListPage:
    """Watering log list display and interactions."""

    @pytest.mark.smoke
    def test_list_page_renders_with_correct_testid(
        self,
        watering_list: WateringLogListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-004-W001: WateringLogListPage renders with data-testid='watering-log-list-page'.

        Verifies that the page loads and the root container element is visible.
        """
        watering_list.open()
        screenshot(
            "TC-REQ-004-W001_watering-log-list-loaded",
            "Watering log list page after initial load",
        )

        page_el = watering_list.wait_for_element(WateringLogListPage.PAGE)
        assert page_el.is_displayed(), (
            "TC-REQ-004-W001 FAIL: Expected [data-testid='watering-log-list-page'] to be visible"
        )

    @pytest.mark.smoke
    def test_create_button_is_visible(
        self,
        watering_list: WateringLogListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-004-W002: Create button is visible on the watering log list page.

        The create button allows users to add a new watering log entry.
        """
        watering_list.open()
        screenshot(
            "TC-REQ-004-W002_create-button-visible",
            "Watering log list showing create button",
        )

        create_btn = watering_list.wait_for_element(WateringLogListPage.CREATE_BUTTON)
        assert create_btn.is_displayed(), (
            "TC-REQ-004-W002 FAIL: Expected create button to be visible"
        )

    @pytest.mark.smoke
    def test_list_displays_data_table_or_empty_state(
        self,
        watering_list: WateringLogListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-004-W001b: Page shows either a DataTable or the empty-state illustration.

        When no watering logs exist, the empty state should be displayed.
        When logs exist, the DataTable should be visible.
        """
        watering_list.open()
        screenshot(
            "TC-REQ-004-W001b_table-or-empty",
            "Watering log list — table or empty state",
        )

        has_table = len(watering_list.driver.find_elements(*WateringLogListPage.TABLE)) > 0
        has_empty = watering_list.has_empty_state()

        assert has_table or has_empty, (
            "TC-REQ-004-W001b FAIL: Expected either a DataTable or empty-state illustration"
        )

    def test_showing_count_when_rows_exist(
        self,
        watering_list: WateringLogListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-004-W001c: Showing count text is displayed when rows are present.

        Skips if no watering log entries exist yet.
        """
        watering_list.open()
        screenshot(
            "TC-REQ-004-W001c_showing-count",
            "Watering log list showing count",
        )

        if watering_list.get_row_count() == 0:
            pytest.skip("No rows — showing count not displayed for empty table")

        count_text = watering_list.get_showing_count_text()
        assert count_text, (
            "TC-REQ-004-W001c FAIL: Expected non-empty showing count text"
        )


# -- TC-REQ-004-W003 to TC-REQ-004-W006: Create Dialog ------------------------


class TestWateringLogCreateDialog:
    """Watering log create dialog operations."""

    @pytest.mark.core_crud
    def test_create_dialog_opens_on_button_click(
        self,
        watering_list: WateringLogListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-004-W003: Clicking create button opens the WateringLogCreateDialog.

        Verifies dialog presence and that plant autocomplete is visible.
        """
        watering_list.open()
        screenshot(
            "TC-REQ-004-W003_before-open-dialog",
            "Watering log list before opening create dialog",
        )

        watering_list.click_create()
        screenshot(
            "TC-REQ-004-W003_dialog-open",
            "Watering log create dialog opened",
        )

        assert watering_list.is_create_dialog_open(), (
            "TC-REQ-004-W003 FAIL: Expected WateringLogCreateDialog to be open"
        )

        # Verify the plant autocomplete input is present
        plant_input = watering_list.driver.find_elements(
            *WateringLogListPage.PLANT_KEYS_AUTOCOMPLETE
        )
        assert len(plant_input) > 0, (
            "TC-REQ-004-W003 FAIL: Expected plant-keys-autocomplete to be present in dialog"
        )

        watering_list.cancel_create_form()

    @pytest.mark.core_crud
    def test_create_watering_log_happy_path(
        self,
        watering_list: WateringLogListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-004-W004: Create a watering log with valid data; verify it appears in list.

        Happy path: fill volume, submit, confirm list updates.
        """
        watering_list.open()
        initial_count = watering_list.get_row_count()
        screenshot(
            "TC-REQ-004-W004_before-create",
            "Watering log list before creating entry",
        )

        watering_list.click_create()
        screenshot(
            "TC-REQ-004-W004_dialog-open",
            "Watering log create dialog opened",
        )

        # Fill required field: volume_liters (defaults: application_method=drench, volume=1)
        watering_list.fill_volume(2.5)

        # Fill optional measurement fields for a realistic entry
        watering_list.fill_ec_before(1.2)
        watering_list.fill_ph_before(6.0)

        screenshot(
            "TC-REQ-004-W004_form-filled",
            "Watering log create form filled before submit",
        )

        watering_list.submit_create_form()

        # Wait for dialog to close and list to reload
        WebDriverWait(watering_list.driver, 15).until(
            EC.invisibility_of_element_located(WateringLogListPage.CREATE_DIALOG)
        )
        watering_list.wait_for_loading_complete()
        screenshot(
            "TC-REQ-004-W004_after-create",
            "Watering log list after creation",
        )

        final_count = watering_list.get_row_count()
        assert final_count > initial_count, (
            f"TC-REQ-004-W004 FAIL: Expected row count to increase. "
            f"Initial: {initial_count}, final: {final_count}"
        )

    @pytest.mark.core_crud
    def test_create_dialog_validation_volume_required(
        self,
        watering_list: WateringLogListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-004-W005: Submitting with volume cleared triggers validation; dialog stays open.

        The volume_liters field must be > 0. Clearing it and submitting should
        keep the dialog open (NFR-006 error display).
        """
        watering_list.open()
        watering_list.click_create()

        # Clear the volume field (default is 1)
        volume_el = watering_list.wait_for_element_clickable(
            WateringLogListPage.FORM_VOLUME
        )
        watering_list.clear_and_fill(volume_el, "0")

        screenshot(
            "TC-REQ-004-W005_before-submit-invalid",
            "Create dialog with volume=0 before submit",
        )

        watering_list.submit_create_form()
        time.sleep(0.5)
        screenshot(
            "TC-REQ-004-W005_validation-error",
            "Validation error after submitting with volume=0",
        )

        assert watering_list.is_create_dialog_open(), (
            "TC-REQ-004-W005 FAIL: Expected dialog to remain open when volume is invalid"
        )

        watering_list.cancel_create_form()

    @pytest.mark.core_crud
    def test_create_dialog_cancel_closes_without_saving(
        self,
        watering_list: WateringLogListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-004-W006: Cancel in create dialog closes it without creating a log entry.

        Verifies that the row count remains unchanged after cancelling.
        """
        watering_list.open()
        initial_count = watering_list.get_row_count()

        watering_list.click_create()
        watering_list.fill_volume(99.9)
        screenshot(
            "TC-REQ-004-W006_before-cancel",
            "Create dialog filled before cancel",
        )

        watering_list.cancel_create_form()
        watering_list.wait_for_loading_complete()
        screenshot(
            "TC-REQ-004-W006_after-cancel",
            "Watering log list after cancelling dialog",
        )

        assert not watering_list.is_create_dialog_open(), (
            "TC-REQ-004-W006 FAIL: Expected create dialog to be closed after cancel"
        )
        final_count = watering_list.get_row_count()
        assert final_count == initial_count, (
            f"TC-REQ-004-W006 FAIL: Expected row count to stay {initial_count}, got {final_count}"
        )

    @pytest.mark.core_crud
    def test_create_dialog_add_fertilizer_button(
        self,
        watering_list: WateringLogListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-004-W004b: Add-fertilizer button adds a fertilizer row to the form.

        Verifies that the dynamic fertilizer field array can be extended.
        """
        watering_list.open()
        watering_list.click_create()
        screenshot(
            "TC-REQ-004-W004b_before-add-fertilizer",
            "Create dialog before adding fertilizer",
        )

        add_btn = watering_list.wait_for_element_clickable(
            WateringLogListPage.ADD_FERTILIZER_BUTTON
        )
        watering_list.scroll_and_click(add_btn)
        time.sleep(0.3)
        screenshot(
            "TC-REQ-004-W004b_after-add-fertilizer",
            "Create dialog after adding fertilizer row",
        )

        # Verify at least one remove-fertilizer button appeared
        remove_btns = watering_list.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='remove-fertilizer-0']"
        )
        assert len(remove_btns) > 0, (
            "TC-REQ-004-W004b FAIL: Expected remove-fertilizer-0 button after adding fertilizer"
        )

        watering_list.cancel_create_form()


# -- TC-REQ-004-W007: Search/Filter -------------------------------------------


class TestWateringLogSearch:
    """Watering log search and filter interactions."""

    def test_search_filters_table_rows(
        self,
        watering_list: WateringLogListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-004-W007: Typing into the search field filters visible rows.

        Skips if no watering logs exist (nothing to filter).
        """
        watering_list.open()
        screenshot(
            "TC-REQ-004-W007_before-search",
            "Watering log list before search",
        )

        row_count = watering_list.get_row_count()
        if row_count == 0:
            pytest.skip("No watering log rows to search/filter")

        # Search for a term unlikely to match all rows
        watering_list.search("zzz-no-match-expected")
        time.sleep(0.5)
        screenshot(
            "TC-REQ-004-W007_after-search",
            "Watering log list after search with non-matching term",
        )

        filtered_count = watering_list.get_row_count()
        assert filtered_count < row_count or watering_list.has_search_chip(), (
            "TC-REQ-004-W007 FAIL: Expected search to filter rows or show search chip"
        )

        # Clear search to restore
        watering_list.clear_search()
        time.sleep(0.3)


# -- TC-REQ-004-W008 to TC-REQ-004-W009: Detail Page --------------------------


class TestWateringLogDetailPage:
    """Watering log detail page display and navigation."""

    @pytest.mark.smoke
    def test_click_row_navigates_to_detail(
        self,
        watering_list: WateringLogListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-004-W008: Clicking a row in the list navigates to the detail page.

        Skips if no watering log entries exist.
        """
        watering_list.open()
        screenshot(
            "TC-REQ-004-W008_list-before-click",
            "Watering log list before clicking row",
        )

        if watering_list.get_row_count() == 0:
            pytest.skip("No watering log rows to click")

        watering_list.click_row(0)
        watering_list.wait_for_url_contains("/giessprotokoll/")
        screenshot(
            "TC-REQ-004-W008_detail-after-click",
            "Watering log detail page after row click",
        )

        detail_el = watering_list.wait_for_element(
            WateringLogDetailPage.PAGE, timeout=15
        )
        assert detail_el.is_displayed(), (
            "TC-REQ-004-W008 FAIL: Expected watering-log-detail-page to be visible after row click"
        )

    @pytest.mark.smoke
    def test_detail_page_has_two_tabs(
        self,
        watering_list: WateringLogListPage,
        watering_detail: WateringLogDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-004-W009: Detail page shows 2 tabs (Details, Edit).

        Navigates via list row click, then verifies tab count and labels.
        """
        watering_list.open()

        if watering_list.get_row_count() == 0:
            pytest.skip("No watering log rows — cannot test detail page")

        watering_list.click_row(0)
        watering_list.wait_for_url_contains("/giessprotokoll/")
        watering_detail.wait_for_element(WateringLogDetailPage.PAGE)
        screenshot(
            "TC-REQ-004-W009_detail-tabs",
            "Watering log detail page showing tabs",
        )

        tab_count = watering_detail.get_tab_count()
        assert tab_count == 2, (
            f"TC-REQ-004-W009 FAIL: Expected 2 tabs, got {tab_count}"
        )

    def test_detail_page_shows_measurement_cards(
        self,
        watering_list: WateringLogListPage,
        watering_detail: WateringLogDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-004-W009b: Details tab shows at least one MUI Card with watering data.

        Verifies that the details tab renders measurement/info cards.
        """
        watering_list.open()

        if watering_list.get_row_count() == 0:
            pytest.skip("No watering log rows — cannot test detail page cards")

        watering_list.click_row(0)
        watering_list.wait_for_url_contains("/giessprotokoll/")
        watering_detail.wait_for_element(WateringLogDetailPage.PAGE)
        screenshot(
            "TC-REQ-004-W009b_detail-cards",
            "Watering log detail page — measurement cards",
        )

        card_count = watering_detail.get_detail_card_count()
        assert card_count >= 1, (
            f"TC-REQ-004-W009b FAIL: Expected at least 1 detail card, got {card_count}"
        )

    def test_detail_page_has_analyze_runoff_button(
        self,
        watering_list: WateringLogListPage,
        watering_detail: WateringLogDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-004-W009c: Details tab shows the 'Analyze Runoff' button.

        This button triggers backend runoff analysis for the watering event.
        """
        watering_list.open()

        if watering_list.get_row_count() == 0:
            pytest.skip("No watering log rows — cannot test runoff button")

        watering_list.click_row(0)
        watering_list.wait_for_url_contains("/giessprotokoll/")
        watering_detail.wait_for_element(WateringLogDetailPage.PAGE)
        screenshot(
            "TC-REQ-004-W009c_runoff-button",
            "Watering log detail — analyze runoff button",
        )

        assert watering_detail.has_analyze_runoff_button(), (
            "TC-REQ-004-W009c FAIL: Expected analyze-runoff button to be visible"
        )

    def test_detail_page_delete_dialog_opens(
        self,
        watering_list: WateringLogListPage,
        watering_detail: WateringLogDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-004-W009d: Delete button on detail page opens confirmation dialog.

        Verifies the ConfirmDialog appears and can be cancelled.
        """
        watering_list.open()

        if watering_list.get_row_count() == 0:
            pytest.skip("No watering log rows — cannot test delete dialog")

        watering_list.click_row(0)
        watering_list.wait_for_url_contains("/giessprotokoll/")
        watering_detail.wait_for_element(WateringLogDetailPage.PAGE)

        watering_detail.click_delete()
        screenshot(
            "TC-REQ-004-W009d_delete-dialog",
            "Watering log detail — delete confirmation dialog",
        )

        confirm_dialog = watering_detail.driver.find_elements(
            *WateringLogDetailPage.CONFIRM_DIALOG
        )
        assert len(confirm_dialog) > 0 and confirm_dialog[0].is_displayed(), (
            "TC-REQ-004-W009d FAIL: Expected ConfirmDialog to be visible"
        )

        # Cancel the delete to avoid data loss
        watering_detail.cancel_delete()

    def test_detail_page_edit_tab_shows_form(
        self,
        watering_list: WateringLogListPage,
        watering_detail: WateringLogDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-004-W009e: Edit tab on detail page shows the edit form with pre-filled values.

        Navigates to the edit tab and verifies the volume field is present and pre-filled.
        """
        watering_list.open()

        if watering_list.get_row_count() == 0:
            pytest.skip("No watering log rows — cannot test edit tab")

        watering_list.click_row(0)
        watering_list.wait_for_url_contains("/giessprotokoll/")
        watering_detail.wait_for_element(WateringLogDetailPage.PAGE)

        watering_detail.click_edit_tab()
        time.sleep(0.5)
        screenshot(
            "TC-REQ-004-W009e_edit-tab",
            "Watering log detail — edit tab form",
        )

        assert watering_detail.is_edit_form_visible(), (
            "TC-REQ-004-W009e FAIL: Expected edit form to be visible on edit tab"
        )

        volume_val = watering_detail.get_volume_value()
        assert volume_val, (
            "TC-REQ-004-W009e FAIL: Expected volume field to be pre-filled with a value"
        )
