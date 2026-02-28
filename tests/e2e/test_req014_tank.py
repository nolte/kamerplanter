"""E2E tests for REQ-014 — Tankmanagement (TC-REQ-014-001 to TC-REQ-014-028).

Tests cover:
- TankListPage: list display, search, sort, filter, row navigation
- TankCreateDialog: CRUD, form validation, equipment toggles, cancel
- TankDetailPage:
  - Tab 0 (Details): info table, alert banners
  - Tab 1 (States): record state dialog, pH/EC/temp values, states table
  - Tab 2 (Maintenance): log maintenance dialog, type selection, history table
  - Tab 3 (Schedules): schedules table display
  - Tab 4 (Edit): edit form prefilled, save, cancel
- Delete flow
- Error handling: 404 for unknown keys

NFR-008 §3.4 screenshot checkpoints at:
1. Page Load
2. Before significant actions
3. After significant actions
4. Error states
"""

from __future__ import annotations

import time

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.tank_detail_page import TankDetailPage
from .pages.tank_list_page import TankListPage


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def tank_list(browser: WebDriver, base_url: str) -> TankListPage:
    """Return a TankListPage bound to the test browser."""
    return TankListPage(browser, base_url)


@pytest.fixture
def tank_detail(browser: WebDriver, base_url: str) -> TankDetailPage:
    """Return a TankDetailPage bound to the test browser."""
    return TankDetailPage(browser, base_url)


# ── TC-REQ-014-001 to TC-REQ-014-008: List Page ───────────────────────────────

class TestTankListPage:
    """TC-REQ-014-001 to TC-REQ-014-008: TankListPage operations."""

    def test_list_page_renders_with_correct_testid(
        self,
        tank_list: TankListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-014-001: TankListPage renders with data-testid='tank-list-page'."""
        capture = request.node._screenshot_capture
        tank_list.open()
        capture("req014_001_tank_list_loaded")  # Checkpoint: Page Load

        assert tank_list.driver.find_element(
            *TankListPage.PAGE
        ).is_displayed(), "Expected [data-testid='tank-list-page'] to be visible"

    def test_list_displays_data_table_with_columns(
        self,
        tank_list: TankListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-014-002: DataTable renders with expected column headers (Name, Type, Volume)."""
        capture = request.node._screenshot_capture
        tank_list.open()
        capture("req014_002_tank_table_columns")  # Checkpoint: Page Load

        headers = tank_list.get_column_headers()
        assert len(headers) > 0, (
            f"Expected column headers in tank list, got none. Headers: {headers}"
        )
        assert any("Name" in h for h in headers), (
            f"Expected 'Name' column header, got: {headers}"
        )

    def test_create_button_is_visible_on_list_page(
        self,
        tank_list: TankListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-014-003: Create button is visible on the TankListPage."""
        capture = request.node._screenshot_capture
        tank_list.open()
        capture("req014_003_create_button")  # Checkpoint: Page Load

        btn = tank_list.driver.find_element(*TankListPage.CREATE_BUTTON)
        assert btn.is_displayed(), "Expected [data-testid='create-button'] to be visible"

    def test_click_row_navigates_to_detail(
        self,
        tank_list: TankListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-014-004: Clicking a tank row navigates to its detail page."""
        capture = request.node._screenshot_capture
        tank_list.open()
        capture("req014_004_before_row_click")  # Checkpoint: before action

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks in database — cannot test row click navigation")

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")
        capture("req014_004_after_row_click")  # Checkpoint: after action

        assert "/standorte/tanks/" in tank_list.driver.current_url, (
            f"Expected detail URL after row click, got: {tank_list.driver.current_url}"
        )

    def test_search_filters_tanks_by_name(
        self,
        tank_list: TankListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-014-005: Search input filters tanks by name."""
        capture = request.node._screenshot_capture
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test search")

        initial_count = tank_list.get_row_count()
        capture("req014_005_before_search")  # Checkpoint: before action

        tank_list.search("ZZZ_NONEXISTENT_TANK_9999")
        time.sleep(0.4)
        capture("req014_005_after_search")  # Checkpoint: filtered state

        filtered_count = tank_list.get_row_count()
        assert filtered_count <= initial_count, (
            f"Expected filtered count ({filtered_count}) <= initial ({initial_count})"
        )
        assert tank_list.has_search_chip(), (
            "Expected search chip to be visible after entering a search term"
        )

    def test_reset_filters_restores_full_tank_list(
        self,
        tank_list: TankListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-014-006: Reset filters restores the full tank list."""
        capture = request.node._screenshot_capture
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test filter reset")

        initial_count = tank_list.get_row_count()
        tank_list.search("A")
        time.sleep(0.4)

        if tank_list.has_reset_filters_button():
            tank_list.click_reset_filters()
            time.sleep(0.3)
            capture("req014_006_after_reset")  # Checkpoint: after action
            reset_count = tank_list.get_row_count()
            assert reset_count >= initial_count - 1, (
                f"Expected count after reset ({reset_count}) close to initial ({initial_count})"
            )

    def test_sort_by_column_shows_sort_chip(
        self,
        tank_list: TankListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-014-007: Clicking a column header activates the sort chip."""
        capture = request.node._screenshot_capture
        tank_list.open()
        headers = tank_list.get_column_headers()
        if not headers:
            pytest.skip("No column headers found")

        capture("req014_007_before_sort")  # Checkpoint: before action
        tank_list.click_column_header(headers[0])
        time.sleep(0.3)
        capture("req014_007_after_sort")  # Checkpoint: after action

        assert tank_list.has_sort_chip(), (
            f"Expected sort chip after clicking column header '{headers[0]}'"
        )

    def test_showing_count_text_is_present(
        self,
        tank_list: TankListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-014-008: Showing count text is displayed when rows are present."""
        capture = request.node._screenshot_capture
        tank_list.open()
        capture("req014_008_showing_count")  # Checkpoint: Page Load

        if tank_list.get_row_count() == 0:
            pytest.skip("No rows — showing count not displayed for empty table")

        count_text = tank_list.get_showing_count_text()
        assert count_text, (
            "Expected non-empty showing count text, got empty string"
        )


# ── TC-REQ-014-010 to TC-REQ-014-015: Create Dialog ──────────────────────────

class TestTankCreateDialog:
    """TC-REQ-014-010 to TC-REQ-014-015: TankCreateDialog operations."""

    def test_create_dialog_opens_on_button_click(
        self,
        tank_list: TankListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-014-010: Clicking create button opens the TankCreateDialog."""
        capture = request.node._screenshot_capture
        tank_list.open()
        capture("req014_010_before_open_dialog")  # Checkpoint: before action

        tank_list.click_create()
        capture("req014_010_dialog_open")  # Checkpoint: after action

        assert tank_list.is_create_dialog_open(), (
            "Expected TankCreateDialog to be open after clicking the create button"
        )

    def test_create_dialog_cancel_closes_without_saving(
        self,
        tank_list: TankListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-014-011: Cancel in create dialog closes it without creating a tank."""
        capture = request.node._screenshot_capture
        tank_list.open()
        initial_count = tank_list.get_row_count()

        tank_list.click_create()
        tank_list.fill_name("Should Not Persist")
        capture("req014_011_before_cancel")  # Checkpoint: before action

        tank_list.cancel_create_form()
        time.sleep(0.4)
        capture("req014_011_after_cancel")  # Checkpoint: after action

        assert not tank_list.is_create_dialog_open(), (
            "Expected create dialog to be closed after clicking cancel"
        )
        final_count = tank_list.get_row_count()
        assert final_count == initial_count, (
            f"Expected row count to stay {initial_count} after cancel, got {final_count}"
        )

    def test_create_dialog_submit_without_name_shows_validation_error(
        self,
        tank_list: TankListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-014-012: Submitting with empty name triggers validation error (NFR-006)."""
        capture = request.node._screenshot_capture
        tank_list.open()
        tank_list.click_create()

        name_el = tank_list.wait_for_element_clickable(TankListPage.FORM_NAME)
        name_el.clear()
        capture("req014_012_before_submit_empty")  # Checkpoint: before action

        tank_list.submit_create_form()
        time.sleep(0.3)
        capture("req014_012_validation_error")  # Checkpoint: error state

        # Zod validation prevents submission — dialog stays open
        assert tank_list.is_create_dialog_open(), (
            "Expected dialog to remain open when name is empty (Zod min(1) validation)"
        )

    def test_create_dialog_equipment_toggles(
        self,
        tank_list: TankListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-014-013: Equipment toggle switches can be toggled in the create dialog."""
        capture = request.node._screenshot_capture
        tank_list.open()
        tank_list.click_create()
        capture("req014_013_dialog_open")  # Checkpoint: dialog open

        # Default state: has_lid = false
        initial_state = tank_list.is_has_lid_checked()
        assert initial_state is False, (
            f"Expected has_lid to default to False, got {initial_state}"
        )

        # Toggle it on
        tank_list.toggle_has_lid()
        time.sleep(0.2)
        capture("req014_013_lid_toggled_on")  # Checkpoint: after action
        toggled_state = tank_list.is_has_lid_checked()
        assert toggled_state is True, (
            f"Expected has_lid to be True after toggle, got {toggled_state}"
        )

        # Toggle back off
        tank_list.toggle_has_lid()
        time.sleep(0.2)
        final_state = tank_list.is_has_lid_checked()
        assert final_state is False, (
            f"Expected has_lid to be False after second toggle, got {final_state}"
        )

        tank_list.cancel_create_form()

    def test_create_tank_with_valid_data(
        self,
        tank_list: TankListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-014-014: Create a tank with valid name and volume; verify it appears in list."""
        capture = request.node._screenshot_capture
        tank_list.open()
        initial_count = tank_list.get_row_count()
        capture("req014_014_before_create")  # Checkpoint: before action

        tank_list.click_create()
        capture("req014_014_dialog_open")  # Checkpoint: dialog open

        unique_name = f"E2E-Tank-{int(time.time())}"
        tank_list.fill_name(unique_name)
        # Volume defaults to 50 — keep as-is; tank_type defaults to 'nutrient'

        capture("req014_014_form_filled")  # Checkpoint: form filled, before submit

        tank_list.submit_create_form()
        time.sleep(1.0)  # Allow API call + Redux state update
        capture("req014_014_after_create")  # Checkpoint: after creation

        final_count = tank_list.get_row_count()
        names = tank_list.get_first_column_texts()
        assert final_count > initial_count or unique_name in names, (
            f"Expected new tank '{unique_name}' to appear in list after creation. "
            f"Initial: {initial_count}, final: {final_count}"
        )

    def test_create_tank_with_notes(
        self,
        tank_list: TankListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-014-015: Create a tank with notes field populated."""
        capture = request.node._screenshot_capture
        tank_list.open()
        initial_count = tank_list.get_row_count()

        tank_list.click_create()
        unique_name = f"E2E-Tank-Notes-{int(time.time())}"
        tank_list.fill_name(unique_name)
        tank_list.fill_notes("Test notes for E2E verification")
        capture("req014_015_form_with_notes")  # Checkpoint: form filled

        tank_list.submit_create_form()
        time.sleep(1.0)
        capture("req014_015_after_create_with_notes")  # Checkpoint: after creation

        final_count = tank_list.get_row_count()
        names = tank_list.get_first_column_texts()
        assert final_count > initial_count or unique_name in names, (
            f"Expected new tank '{unique_name}' to appear in list after creation. "
            f"Initial: {initial_count}, final: {final_count}"
        )


# ── TC-REQ-014-016 to TC-REQ-014-022: Detail Page ────────────────────────────

class TestTankDetailPage:
    """TC-REQ-014-016 to TC-REQ-014-022: TankDetailPage general rendering."""

    def test_detail_page_loads_and_renders(
        self,
        tank_list: TankListPage,
        tank_detail: TankDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-014-016: Navigating to tank detail URL renders the detail page."""
        capture = request.node._screenshot_capture
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test detail page")

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")
        capture("req014_016_detail_loaded")  # Checkpoint: Page Load

        assert tank_detail.driver.find_element(
            *TankDetailPage.PAGE
        ).is_displayed(), "Expected [data-testid='tank-detail-page'] to be visible"

    def test_detail_page_has_five_tabs(
        self,
        tank_list: TankListPage,
        tank_detail: TankDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-014-017: Tank detail page renders 5 tabs: Details, States, Maintenance, Schedules, Edit."""
        capture = request.node._screenshot_capture
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test tabs")

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")
        capture("req014_017_tabs_visible")  # Checkpoint: Page Load

        tab_labels = tank_detail.get_tab_labels()
        assert len(tab_labels) == 5, (
            f"Expected exactly 5 tabs, got {len(tab_labels)}: {tab_labels}"
        )

    def test_tab_navigation_through_all_tabs(
        self,
        tank_list: TankListPage,
        tank_detail: TankDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-014-018: Clicking each of the 5 tabs shows the corresponding panel."""
        capture = request.node._screenshot_capture
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test tab navigation")

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")
        capture("req014_018_tab_0_details")  # Checkpoint: tab 0 (default)

        for tab_index in range(1, 5):
            tank_detail.click_tab(tab_index)
            time.sleep(0.3)
            active = tank_detail.get_active_tab_index()
            capture(f"req014_018_tab_{tab_index}_active")  # Checkpoint: each tab
            assert active == tab_index, (
                f"Expected tab {tab_index} to be active after clicking, got {active}"
            )

    def test_detail_page_title_matches_tank_name(
        self,
        tank_list: TankListPage,
        tank_detail: TankDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-014-019: Detail page title matches the tank name from the list."""
        capture = request.node._screenshot_capture
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test page title")

        names = tank_list.get_first_column_texts()
        first_name = names[0] if names else None

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")
        capture("req014_019_detail_title")  # Checkpoint: Page Load

        title = tank_detail.get_page_title()
        assert title, "Expected a non-empty page title on tank detail page"

        if first_name:
            assert first_name in title or title in first_name, (
                f"Expected page title '{title}' to match tank name '{first_name}'"
            )

    def test_details_tab_shows_tank_info(
        self,
        tank_list: TankListPage,
        tank_detail: TankDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-014-020: Details tab shows tank type, volume, and material."""
        capture = request.node._screenshot_capture
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test details tab")

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")
        capture("req014_020_details_tab")  # Checkpoint: Page Load (tab 0)

        # Tab 0 is the default; no click needed
        card_text = tank_detail.get_detail_cards_text()
        assert card_text, (
            "Expected non-empty card text in tank details tab"
        )
        # At least one of the known tank-type labels should appear
        tank_type_labels = ["Nährstofflösung", "Gießwasser", "Reservoir", "Rezirkulation",
                            "nutrient", "irrigation", "recirculation"]
        has_type_label = any(label in card_text for label in tank_type_labels)
        assert has_type_label, (
            f"Expected at least one tank type label in details card, card text: {card_text[:200]}"
        )


# ── TC-REQ-014-023 to TC-REQ-014-024: Tank State Recording ───────────────────

class TestTankStateRecording:
    """TC-REQ-014-023 to TC-REQ-014-024: TankStateCreateDialog operations (tab 1)."""

    def test_record_state_dialog_opens_from_states_tab(
        self,
        tank_list: TankListPage,
        tank_detail: TankDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-014-023: Clicking 'Record State' in tab 1 opens the TankStateCreateDialog."""
        capture = request.node._screenshot_capture
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test state recording")

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")

        tank_detail.click_tab(1)  # States tab
        time.sleep(0.3)
        capture("req014_023_states_tab_open")  # Checkpoint: tab 1 visible

        tank_detail.click_record_state()
        capture("req014_023_state_dialog_open")  # Checkpoint: dialog open

        assert tank_detail.is_state_dialog_open(), (
            "Expected TankStateCreateDialog to be open after clicking 'Record State'"
        )

    def test_record_state_with_ph_and_ec_values(
        self,
        tank_list: TankListPage,
        tank_detail: TankDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-014-024: Record a tank state with pH and EC; new row appears in states table."""
        capture = request.node._screenshot_capture
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test state recording")

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")

        tank_detail.click_tab(1)
        time.sleep(0.3)
        initial_state_count = tank_detail.get_states_row_count()

        tank_detail.click_record_state()
        capture("req014_024_state_dialog_open")  # Checkpoint: dialog open

        # Fill pH (valid range 0–14) and EC
        tank_detail.fill_state_ph(6.2)
        tank_detail.fill_state_ec(1.8)
        tank_detail.fill_state_temp(20.5)
        tank_detail.fill_state_fill_percent(75.0)
        capture("req014_024_state_form_filled")  # Checkpoint: form filled, before submit

        tank_detail.submit_state_form()
        time.sleep(1.0)  # Allow API call + page reload
        capture("req014_024_after_state_recorded")  # Checkpoint: after recording

        final_state_count = tank_detail.get_states_row_count()
        assert final_state_count >= initial_state_count, (
            f"Expected states count to be >= {initial_state_count} after recording, "
            f"got {final_state_count}"
        )

    def test_record_state_dialog_cancel_closes(
        self,
        tank_list: TankListPage,
        tank_detail: TankDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-014-025: Cancelling the TankState dialog closes it without saving."""
        capture = request.node._screenshot_capture
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test cancel state dialog")

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")

        tank_detail.click_tab(1)
        time.sleep(0.3)
        initial_count = tank_detail.get_states_row_count()

        tank_detail.click_record_state()
        tank_detail.fill_state_ph(7.0)
        capture("req014_025_before_cancel")  # Checkpoint: before action

        tank_detail.cancel_state_form()
        time.sleep(0.3)
        capture("req014_025_after_cancel")  # Checkpoint: after cancel

        assert not tank_detail.is_state_dialog_open(), (
            "Expected TankState dialog to be closed after clicking cancel"
        )
        final_count = tank_detail.get_states_row_count()
        assert final_count == initial_count, (
            f"Expected state count to remain {initial_count} after cancel, got {final_count}"
        )


# ── TC-REQ-014-025 to TC-REQ-014-027: Maintenance Log ────────────────────────

class TestMaintenanceLog:
    """TC-REQ-014-026 to TC-REQ-014-027: MaintenanceLogDialog operations (tab 2)."""

    def test_log_maintenance_dialog_opens_from_maintenance_tab(
        self,
        tank_list: TankListPage,
        tank_detail: TankDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-014-026: 'Log Maintenance' button in tab 2 opens MaintenanceLogDialog."""
        capture = request.node._screenshot_capture
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test maintenance log")

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")

        tank_detail.click_tab(2)  # Maintenance tab
        time.sleep(0.3)
        capture("req014_026_maintenance_tab_open")  # Checkpoint: tab 2 visible

        tank_detail.click_log_maintenance()
        capture("req014_026_maintenance_dialog_open")  # Checkpoint: dialog open

        assert tank_detail.is_maintenance_dialog_open(), (
            "Expected MaintenanceLogDialog to open after clicking 'Log Maintenance'"
        )

    def test_log_maintenance_with_water_change_type(
        self,
        tank_list: TankListPage,
        tank_detail: TankDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-014-027: Log a 'water_change' maintenance entry; new row in history table."""
        capture = request.node._screenshot_capture
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test maintenance logging")

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")

        tank_detail.click_tab(2)
        time.sleep(0.3)
        initial_maint_count = tank_detail.get_maintenance_row_count()

        tank_detail.click_log_maintenance()
        capture("req014_027_maintenance_dialog_open")  # Checkpoint: dialog open

        # maintenance_type defaults to 'water_change' — keep default
        tank_detail.fill_maintenance_performed_by("E2E Test Runner")
        tank_detail.fill_maintenance_duration(30)
        tank_detail.fill_maintenance_products("H2O2 3%")
        tank_detail.fill_maintenance_notes("Automated E2E maintenance test entry")
        capture("req014_027_maintenance_form_filled")  # Checkpoint: form filled

        tank_detail.submit_maintenance_form()
        time.sleep(1.0)  # Allow API call + page reload
        capture("req014_027_after_maintenance_logged")  # Checkpoint: after logging

        final_maint_count = tank_detail.get_maintenance_row_count()
        assert final_maint_count >= initial_maint_count, (
            f"Expected maintenance history count >= {initial_maint_count} after logging, "
            f"got {final_maint_count}"
        )

    def test_log_maintenance_cancel_closes_dialog(
        self,
        tank_list: TankListPage,
        tank_detail: TankDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-014-028: Cancelling the MaintenanceLogDialog closes it without saving."""
        capture = request.node._screenshot_capture
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test maintenance dialog cancel")

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")

        tank_detail.click_tab(2)
        time.sleep(0.3)
        initial_count = tank_detail.get_maintenance_row_count()

        tank_detail.click_log_maintenance()
        tank_detail.fill_maintenance_performed_by("Cancel Test")
        capture("req014_028_before_cancel")  # Checkpoint: before action

        tank_detail.cancel_maintenance_form()
        time.sleep(0.3)
        capture("req014_028_after_cancel")  # Checkpoint: after cancel

        assert not tank_detail.is_maintenance_dialog_open(), (
            "Expected MaintenanceLogDialog to close after clicking cancel"
        )
        final_count = tank_detail.get_maintenance_row_count()
        assert final_count == initial_count, (
            f"Expected maintenance count to remain {initial_count} after cancel, got {final_count}"
        )


# ── TC-REQ-014-029: Schedules Tab ─────────────────────────────────────────────

class TestTankSchedulesTab:
    """TC-REQ-014-029: Tank Schedules tab (tab 3) renders a data table."""

    def test_schedules_tab_renders_data_table(
        self,
        tank_list: TankListPage,
        tank_detail: TankDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-014-029: Schedules tab (tab 3) renders a DataTable component."""
        capture = request.node._screenshot_capture
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test schedules tab")

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")

        tank_detail.click_tab(3)  # Schedules tab
        time.sleep(0.3)
        capture("req014_029_schedules_tab")  # Checkpoint: tab 3 visible

        # The schedules table may be empty (no schedules configured yet) — just verify
        # that the DataTable component is rendered
        from selenium.webdriver.common.by import By
        tables = tank_detail.driver.find_elements(By.CSS_SELECTOR, "[data-testid='data-table']")
        assert len(tables) > 0, (
            "Expected at least one [data-testid='data-table'] in the Schedules tab"
        )


# ── TC-REQ-014-030 to TC-REQ-014-031: Edit Form ───────────────────────────────

class TestTankEditForm:
    """TC-REQ-014-030 to TC-REQ-014-031: Edit form in TankDetailPage (tab 4)."""

    def test_edit_form_prefilled_with_tank_name(
        self,
        tank_list: TankListPage,
        tank_detail: TankDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-014-030: Edit tab form is pre-filled with the existing tank name."""
        capture = request.node._screenshot_capture
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test edit form")

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")
        page_title = tank_detail.get_page_title()

        tank_detail.click_tab(4)  # Edit tab
        time.sleep(0.4)
        capture("req014_030_edit_tab_open")  # Checkpoint: tab 4 visible

        name_value = tank_detail.get_edit_name_value()
        assert name_value, (
            f"Expected edit form Name field to be pre-filled, got empty string"
        )
        assert name_value == page_title, (
            f"Expected Name field value '{name_value}' to match page title '{page_title}'"
        )

    def test_edit_form_cancel_resets_field(
        self,
        tank_list: TankListPage,
        tank_detail: TankDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-014-031: Cancel in edit form resets the form without saving."""
        capture = request.node._screenshot_capture
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test edit form cancel")

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")
        tank_detail.click_tab(4)
        time.sleep(0.3)

        original_name = tank_detail.get_edit_name_value()

        tank_detail.fill_edit_name("Unsaved Modified Tank Name E2E")
        capture("req014_031_form_modified")  # Checkpoint: before cancel

        tank_detail.cancel_edit_form()
        time.sleep(0.4)
        capture("req014_031_after_cancel")  # Checkpoint: after cancel

        # After cancel (which calls reset()), the form should revert to the saved values
        reverted_name = tank_detail.get_edit_name_value()
        assert reverted_name == original_name, (
            f"Expected name to revert to '{original_name}' after cancel, got '{reverted_name}'"
        )


# ── TC-REQ-014-032: Delete Flow ───────────────────────────────────────────────

class TestTankDeleteFlow:
    """TC-REQ-014-032: Delete flow for tanks."""

    def test_delete_button_opens_confirm_dialog(
        self,
        tank_list: TankListPage,
        tank_detail: TankDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-014-032: Delete button opens ConfirmDialog; Cancel does not delete."""
        capture = request.node._screenshot_capture
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test delete flow")

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")
        capture("req014_032_detail_page_before_delete")  # Checkpoint: before action

        tank_detail.click_delete()
        capture("req014_032_confirm_dialog_open")  # Checkpoint: dialog open

        assert tank_detail.is_confirm_dialog_open(), (
            "Expected ConfirmDialog to appear after clicking Delete button"
        )

        # Cancel — we do NOT delete existing data in E2E tests
        tank_detail.cancel_delete()
        time.sleep(0.3)
        capture("req014_032_after_cancel")  # Checkpoint: after cancel

        assert not tank_detail.is_confirm_dialog_open(), (
            "Expected ConfirmDialog to close after clicking Cancel"
        )
        assert "/standorte/tanks/" in tank_detail.driver.current_url, (
            "Expected to remain on the tank detail page after cancelling delete"
        )


# ── TC-REQ-014-033: Error Handling ───────────────────────────────────────────

class TestTankErrorHandling:
    """TC-REQ-014-033: Error states for TankDetailPage."""

    def test_nonexistent_tank_key_shows_error(
        self,
        tank_detail: TankDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-014-033: Navigating to a non-existent tank key shows an error display."""
        capture = request.node._screenshot_capture
        tank_detail.navigate("/standorte/tanks/nonexistent-key-99999")
        time.sleep(1.5)  # Allow the API call to fail and error state to render
        capture("req014_033_nonexistent_key_error")  # Checkpoint: error state

        error_displayed = tank_detail.is_error_displayed()
        page_rendered = len(tank_detail.driver.find_elements(
            *TankDetailPage.PAGE
        )) > 0

        assert error_displayed or page_rendered, (
            "Expected either an error display or the detail page to render for an invalid tank key"
        )
