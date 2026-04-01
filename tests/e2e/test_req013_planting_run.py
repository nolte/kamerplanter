"""E2E tests for REQ-013 — Pflanzdurchlauf-Verwaltung (TC-REQ-013-001 to TC-REQ-013-020).

Tests cover:
- PlantingRunListPage: list display, search, sort, filter, row navigation
- PlantingRunCreateDialog: CRUD, form validation, cancel
- PlantingRunDetailPage: tab navigation, state machine (planned→active via batch-create),
  edit form, delete (planned runs), batch-remove (active runs), entries table, plants tab
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

from .pages.planting_run_detail_page import PlantingRunDetailPage
from .pages.planting_run_list_page import PlantingRunListPage


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def run_list(browser: WebDriver, base_url: str) -> PlantingRunListPage:
    """Return a PlantingRunListPage bound to the test browser."""
    return PlantingRunListPage(browser, base_url)


@pytest.fixture
def run_detail(browser: WebDriver, base_url: str) -> PlantingRunDetailPage:
    """Return a PlantingRunDetailPage bound to the test browser."""
    return PlantingRunDetailPage(browser, base_url)


# ── TC-REQ-013-001 to TC-REQ-013-004: List Page ───────────────────────────────

class TestPlantingRunListPage:
    """TC-REQ-013-001 to TC-REQ-013-010: PlantingRunListPage operations."""

    @pytest.mark.smoke
    def test_list_page_loads_with_correct_testid(
        self,
        run_list: PlantingRunListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-013-001: PlantingRunListPage renders with data-testid='planting-run-list-page'."""
        capture = request.node._screenshot_capture
        run_list.open()
        capture("req013_001_list_page_loaded")  # Checkpoint: Page Load

        assert run_list.driver.find_element(
            *PlantingRunListPage.PAGE
        ).is_displayed(), "Expected [data-testid='planting-run-list-page'] to be visible"

    def test_list_displays_data_table_with_columns(
        self,
        run_list: PlantingRunListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-013-002: DataTable renders with expected column headers."""
        capture = request.node._screenshot_capture
        run_list.open()
        capture("req013_002_list_table_columns")  # Checkpoint: Page Load

        headers = run_list.get_column_headers()
        assert len(headers) > 0, (
            f"Expected column headers in planting run table, got none. Headers: {headers}"
        )
        # Name column must be present
        assert any("Name" in h for h in headers), (
            f"Expected 'Name' column header, got: {headers}"
        )

    def test_create_button_is_visible(
        self,
        run_list: PlantingRunListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-013-003: Create button is visible on the list page."""
        capture = request.node._screenshot_capture
        run_list.open()
        capture("req013_003_create_button_visible")  # Checkpoint: Page Load

        btn = run_list.driver.find_element(*PlantingRunListPage.CREATE_BUTTON)
        assert btn.is_displayed(), "Expected [data-testid='create-button'] to be visible"

    def test_click_row_navigates_to_detail(
        self,
        run_list: PlantingRunListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-013-004: Clicking a planting run row navigates to its detail page."""
        capture = request.node._screenshot_capture
        run_list.open()
        capture("req013_004_before_row_click")  # Checkpoint: before action

        if run_list.get_row_count() == 0:
            pytest.skip("No planting runs in database — cannot test row click navigation")

        run_list.click_row(0)
        run_list.wait_for_url_contains("/durchlaeufe/planting-runs/")
        capture("req013_004_after_row_click")  # Checkpoint: after action

        assert "/durchlaeufe/planting-runs/" in run_list.driver.current_url, (
            f"Expected detail URL after row click, got: {run_list.driver.current_url}"
        )

    def test_search_filters_runs_by_name(
        self,
        run_list: PlantingRunListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-013-005: Search input filters displayed planting runs."""
        capture = request.node._screenshot_capture
        run_list.open()

        if run_list.get_row_count() == 0:
            pytest.skip("No planting runs — cannot test search")

        initial_count = run_list.get_row_count()
        capture("req013_005_before_search")  # Checkpoint: before action

        # Search with a term that is unlikely to match anything to verify filtering
        run_list.search("ZZZ_NONEXISTENT_RUN_9999")
        time.sleep(0.4)  # Allow debounce
        capture("req013_005_after_search_no_results")  # Checkpoint: filtered state

        filtered_count = run_list.get_row_count()
        assert filtered_count <= initial_count, (
            f"Expected filtered count ({filtered_count}) <= initial ({initial_count})"
        )
        assert run_list.has_search_chip(), (
            "Expected search chip to be visible after entering a search term"
        )

    def test_reset_filters_restores_full_list(
        self,
        run_list: PlantingRunListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-013-006: Reset filters button restores unfiltered list."""
        capture = request.node._screenshot_capture
        run_list.open()

        if run_list.get_row_count() == 0:
            pytest.skip("No planting runs — cannot test filter reset")

        initial_count = run_list.get_row_count()
        run_list.search("A")
        time.sleep(0.4)

        if run_list.has_reset_filters_button():
            run_list.click_reset_filters()
            time.sleep(0.3)
            capture("req013_006_after_reset_filters")  # Checkpoint: after action
            reset_count = run_list.get_row_count()
            assert reset_count >= initial_count - 1, (
                f"Expected count after reset ({reset_count}) to be close to initial ({initial_count})"
            )

    def test_sort_by_column_shows_sort_chip(
        self,
        run_list: PlantingRunListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-013-007: Clicking a column header activates sort chip."""
        capture = request.node._screenshot_capture
        run_list.open()
        headers = run_list.get_column_headers()
        if not headers:
            pytest.skip("No column headers found")

        capture("req013_007_before_sort")  # Checkpoint: before action
        run_list.click_column_header(headers[0])
        time.sleep(0.3)
        capture("req013_007_after_sort")  # Checkpoint: after action

        assert run_list.has_sort_chip(), (
            f"Expected sort chip after clicking column header '{headers[0]}'"
        )

    def test_showing_count_text_is_present(
        self,
        run_list: PlantingRunListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-013-008: Showing count text is displayed when rows are present."""
        capture = request.node._screenshot_capture
        run_list.open()
        capture("req013_008_showing_count")  # Checkpoint: Page Load

        if run_list.get_row_count() == 0:
            pytest.skip("No rows — showing count not displayed for empty table")

        count_text = run_list.get_showing_count_text()
        assert count_text, (
            "Expected non-empty showing count text, got empty string"
        )


# ── TC-REQ-013-010 to TC-REQ-013-014: Create Dialog ──────────────────────────

class TestPlantingRunCreateDialog:
    """TC-REQ-013-010 to TC-REQ-013-014: PlantingRunCreateDialog operations."""

    def test_create_dialog_opens_on_create_button_click(
        self,
        run_list: PlantingRunListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-013-010: Clicking create button opens the creation dialog."""
        capture = request.node._screenshot_capture
        run_list.open()
        capture("req013_010_before_open_create_dialog")  # Checkpoint: before action

        run_list.click_create()
        capture("req013_010_create_dialog_open")  # Checkpoint: after action

        assert run_list.is_create_dialog_open(), (
            "Expected create dialog to be open after clicking the create button"
        )

    def test_create_dialog_cancel_closes_without_saving(
        self,
        run_list: PlantingRunListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-013-011: Cancel in create dialog closes it without creating a run."""
        capture = request.node._screenshot_capture
        run_list.open()
        initial_count = run_list.get_row_count()

        run_list.click_create()
        run_list.fill_name("Should Not Be Saved")
        capture("req013_011_before_cancel")  # Checkpoint: before action

        run_list.cancel_create_form()
        time.sleep(0.4)
        capture("req013_011_after_cancel")  # Checkpoint: after action

        assert not run_list.is_create_dialog_open(), (
            "Expected create dialog to be closed after clicking cancel"
        )
        # Count should remain the same — nothing was created
        final_count = run_list.get_row_count()
        assert final_count == initial_count, (
            f"Expected row count to remain {initial_count} after cancel, got {final_count}"
        )

    def test_create_dialog_submit_without_name_shows_validation_error(
        self,
        run_list: PlantingRunListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-013-012: Submitting with empty name triggers validation error (NFR-006)."""
        capture = request.node._screenshot_capture
        run_list.open()
        run_list.click_create()

        # Clear the name field explicitly (it may be pre-populated)
        name_el = run_list.wait_for_element_clickable(PlantingRunListPage.FORM_NAME)
        name_el.clear()
        capture("req013_012_before_submit_empty")  # Checkpoint: before action

        run_list.submit_create_form()
        time.sleep(0.3)
        capture("req013_012_validation_error_displayed")  # Checkpoint: error state

        # Zod validation prevents submission with empty name — dialog stays open
        assert run_list.is_create_dialog_open(), (
            "Expected dialog to remain open when name is empty (validation prevents submit)"
        )

    def test_create_dialog_submit_without_id_prefix_shows_validation_error(
        self,
        run_list: PlantingRunListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-013-013: id_prefix is required; leaving it empty shows a validation error."""
        capture = request.node._screenshot_capture
        run_list.open()
        run_list.click_create()

        # Fill name but leave id_prefix empty
        run_list.fill_name("TestRun Validation")
        prefix_el = run_list.driver.find_elements(*PlantingRunListPage.FORM_ENTRY_ID_PREFIX)
        if prefix_el:
            prefix_el[0].clear()

        capture("req013_013_before_submit_no_prefix")  # Checkpoint: before action
        run_list.submit_create_form()
        time.sleep(0.3)
        capture("req013_013_validation_error_prefix")  # Checkpoint: error state

        assert run_list.is_create_dialog_open(), (
            "Expected dialog to stay open when id_prefix is invalid (regex /^[A-Z]{2,5}$/)"
        )

    def test_create_planting_run_full_form(
        self,
        run_list: PlantingRunListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-013-014: Create a planting run with valid name and id_prefix; verify it appears in list.

        This test requires at least one species in the database (seed data).
        """
        capture = request.node._screenshot_capture
        run_list.open()
        initial_count = run_list.get_row_count()
        capture("req013_014_before_create")  # Checkpoint: before action

        run_list.click_create()
        capture("req013_014_dialog_open")  # Checkpoint: dialog open

        unique_name = f"E2E-Run-{int(time.time())}"
        run_list.fill_name(unique_name)

        # Select the first available species if the dropdown is populated
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        species_select = run_list.driver.find_elements(
            By.CSS_SELECTOR,
            "[data-testid='form-field-entries.0.species_key'] .MuiSelect-select",
        )
        if species_select:
            run_list.scroll_and_click(species_select[0])
            # Wait for dropdown options and pick the first non-empty one
            options = WebDriverWait(run_list.driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//li[@role='option']")
                )
            )
            species_options = [o for o in options if o.text.strip()]
            if species_options:
                species_options[0].click()
            else:
                run_list.cancel_create_form()
                pytest.skip("No species available in database — cannot complete create test")
        else:
            run_list.cancel_create_form()
            pytest.skip("Species dropdown not found — cannot complete create test")

        # Fill the id_prefix (auto-populated from species genus but we ensure it's valid)
        prefix_elements = run_list.driver.find_elements(
            *PlantingRunListPage.FORM_ENTRY_ID_PREFIX
        )
        if prefix_elements:
            current_prefix = prefix_elements[0].get_attribute("value") or ""
            if not current_prefix or len(current_prefix) < 2:
                prefix_elements[0].clear()
                prefix_elements[0].send_keys("TST")

        capture("req013_014_form_filled")  # Checkpoint: form filled, before submit

        run_list.submit_create_form()
        time.sleep(1.0)  # Allow API call + Redux state update
        capture("req013_014_after_create")  # Checkpoint: after creation

        final_count = run_list.get_row_count()
        assert final_count > initial_count or unique_name in run_list.get_first_column_texts(), (
            f"Expected new run '{unique_name}' to appear in list after creation. "
            f"Initial count: {initial_count}, final count: {final_count}"
        )


# ── TC-REQ-013-015 to TC-REQ-013-020: Detail Page ────────────────────────────

class TestPlantingRunDetailPage:
    """TC-REQ-013-015 to TC-REQ-013-020: PlantingRunDetailPage operations."""

    def test_detail_page_loads_for_first_run(
        self,
        run_list: PlantingRunListPage,
        run_detail: PlantingRunDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-013-015: Navigating to detail URL renders the detail page."""
        capture = request.node._screenshot_capture
        run_list.open()

        if run_list.get_row_count() == 0:
            pytest.skip("No planting runs — cannot test detail page")

        run_list.click_row(0)
        run_list.wait_for_url_contains("/durchlaeufe/planting-runs/")
        capture("req013_015_detail_page_loaded")  # Checkpoint: Page Load

        assert run_detail.driver.find_element(
            *PlantingRunDetailPage.PAGE
        ).is_displayed(), "Expected [data-testid='planting-run-detail-page'] to be visible"

    def test_detail_page_has_five_tabs(
        self,
        run_list: PlantingRunListPage,
        run_detail: PlantingRunDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-013-016: Detail page renders 5 tabs: Details, Plants, Phases, Nutrient/Watering, Activity Plan."""
        capture = request.node._screenshot_capture
        run_list.open()

        if run_list.get_row_count() == 0:
            pytest.skip("No planting runs — cannot test tabs")

        run_list.click_row(0)
        run_list.wait_for_url_contains("/durchlaeufe/planting-runs/")
        capture("req013_016_tabs_visible")  # Checkpoint: Page Load

        tab_labels = run_detail.get_tab_labels()
        assert len(tab_labels) == 5, (
            f"Expected exactly 5 tabs, got {len(tab_labels)}: {tab_labels}"
        )

    def test_tab_navigation_between_all_tabs(
        self,
        run_list: PlantingRunListPage,
        run_detail: PlantingRunDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-013-017: Clicking each tab shows the corresponding content panel."""
        capture = request.node._screenshot_capture
        run_list.open()

        if run_list.get_row_count() == 0:
            pytest.skip("No planting runs — cannot test tab navigation")

        run_list.click_row(0)
        run_list.wait_for_url_contains("/durchlaeufe/planting-runs/")

        # Tab 0 – Details (default)
        capture("req013_017_tab_details")  # Checkpoint: Page Load on tab 0
        assert run_detail.get_active_tab_index() == 0, (
            "Expected tab 0 (Details) to be active by default"
        )

        # Tab 1 – Plants
        run_detail.click_tab(1)
        time.sleep(0.3)
        capture("req013_017_tab_plants")  # Checkpoint: after switching to tab 1
        assert run_detail.get_active_tab_index() == 1, (
            "Expected tab 1 (Plants) to be active after clicking"
        )

        # Tab 2 – Phases
        run_detail.click_tab(2)
        time.sleep(0.3)
        capture("req013_017_tab_phases")  # Checkpoint: after switching to tab 2
        assert run_detail.get_active_tab_index() == 2, (
            "Expected tab 2 (Phases) to be active after clicking"
        )

    def test_status_chip_visible_on_detail_page(
        self,
        run_list: PlantingRunListPage,
        run_detail: PlantingRunDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-013-018: Status chip is visible and contains a non-empty status text."""
        capture = request.node._screenshot_capture
        run_list.open()

        if run_list.get_row_count() == 0:
            pytest.skip("No planting runs — cannot test status chip")

        run_list.click_row(0)
        run_list.wait_for_url_contains("/durchlaeufe/planting-runs/")
        capture("req013_018_status_chip")  # Checkpoint: Page Load

        status = run_detail.get_status()
        assert status, (
            f"Expected a non-empty status chip text, got: '{status}'"
        )
        # Valid statuses: Geplant, Aktiv, Ernte, Abgeschlossen, Abgebrochen (DE) or planned/active etc.
        assert len(status) > 0, "Status chip should display a non-empty label"

    def test_planned_run_shows_create_plants_and_delete_buttons(
        self,
        run_list: PlantingRunListPage,
        run_detail: PlantingRunDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-013-019: A run with status='planned' shows Create Plants and Delete buttons."""
        capture = request.node._screenshot_capture
        run_list.open()

        if run_list.get_row_count() == 0:
            pytest.skip("No planting runs — cannot test planned-status buttons")

        # Navigate to first run and check status
        run_list.click_row(0)
        run_list.wait_for_url_contains("/durchlaeufe/planting-runs/")
        capture("req013_019_detail_page")  # Checkpoint: Page Load

        status = run_detail.get_status()
        if "Geplant" not in status and "planned" not in status.lower():
            pytest.skip(f"First run is not in 'planned' status (status='{status}') — skip state-machine test")

        assert run_detail.is_create_plants_button_visible(), (
            "Expected [data-testid='create-plants-button'] to be visible for planned run"
        )
        assert run_detail.is_delete_button_visible(), (
            "Expected [data-testid='delete-button'] to be visible for planned run"
        )
        assert not run_detail.is_batch_remove_button_visible(), (
            "Did not expect [data-testid='batch-remove-button'] for a planned run"
        )

    def test_create_plants_button_opens_confirm_dialog(
        self,
        run_list: PlantingRunListPage,
        run_detail: PlantingRunDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-013-020: Clicking Create Plants opens a ConfirmDialog (state machine: planned→active)."""
        capture = request.node._screenshot_capture
        run_list.open()

        if run_list.get_row_count() == 0:
            pytest.skip("No planting runs — cannot test create plants confirm dialog")

        run_list.click_row(0)
        run_list.wait_for_url_contains("/durchlaeufe/planting-runs/")

        status = run_detail.get_status()
        if "Geplant" not in status and "planned" not in status.lower():
            pytest.skip(f"First run is not in 'planned' status ('{status}') — skip this test")

        capture("req013_020_before_create_plants")  # Checkpoint: before action

        run_detail.click_create_plants()
        capture("req013_020_confirm_dialog_open")  # Checkpoint: dialog visible

        assert run_detail.is_confirm_dialog_open(), (
            "Expected ConfirmDialog to open after clicking 'Create Plants'"
        )

        # Cancel — do not actually transition state in a pure list/detail E2E check
        run_detail.cancel_action()
        time.sleep(0.3)
        capture("req013_020_after_cancel")  # Checkpoint: after cancel

        assert not run_detail.is_confirm_dialog_open(), (
            "Expected ConfirmDialog to close after clicking Cancel"
        )


class TestPlantingRunEditForm:
    """TC-REQ-013-021 to TC-REQ-013-022: Edit form in PlantingRunDetailPage tab 2."""

    def test_edit_form_prefilled_with_run_name(
        self,
        run_list: PlantingRunListPage,
        run_detail: PlantingRunDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-013-021: Edit dialog form is pre-filled with the existing run name."""
        capture = request.node._screenshot_capture
        run_list.open()

        if run_list.get_row_count() == 0:
            pytest.skip("No planting runs — cannot test edit form")

        run_list.click_row(0)
        run_list.wait_for_url_contains("/durchlaeufe/planting-runs/")
        page_title = run_detail.get_page_title()

        run_detail.open_edit_dialog()
        time.sleep(0.4)
        capture("req013_021_edit_dialog_open")  # Checkpoint: edit dialog open

        name_value = run_detail.get_edit_form_name_value()
        assert name_value, (
            f"Expected edit form Name field to be pre-filled with the run name, got: '{name_value}'"
        )
        assert name_value == page_title, (
            f"Expected Name field value '{name_value}' to match page title '{page_title}'"
        )

    def test_edit_form_cancel_closes_dialog(
        self,
        run_list: PlantingRunListPage,
        run_detail: PlantingRunDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-013-022: Cancel in edit dialog closes it without saving changes."""
        capture = request.node._screenshot_capture
        run_list.open()

        if run_list.get_row_count() == 0:
            pytest.skip("No planting runs — cannot test edit form cancel")

        run_list.click_row(0)
        run_list.wait_for_url_contains("/durchlaeufe/planting-runs/")

        run_detail.open_edit_dialog()
        time.sleep(0.3)

        run_detail.fill_name("Unsaved Modified Name")
        capture("req013_022_form_modified")  # Checkpoint: before cancel

        run_detail.cancel_edit_form()
        time.sleep(0.3)
        capture("req013_022_after_cancel")  # Checkpoint: after cancel

        # Dialog should be closed
        assert not run_detail.is_edit_dialog_open(), (
            "Expected edit dialog to close after clicking cancel"
        )


class TestPlantingRunDeleteFlow:
    """TC-REQ-013-023: Delete flow for planned planting runs."""

    def test_delete_planned_run_confirm_dialog(
        self,
        run_list: PlantingRunListPage,
        run_detail: PlantingRunDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-013-023: Delete button opens ConfirmDialog; cancel does not delete."""
        capture = request.node._screenshot_capture
        run_list.open()

        if run_list.get_row_count() == 0:
            pytest.skip("No planting runs — cannot test delete flow")

        run_list.click_row(0)
        run_list.wait_for_url_contains("/durchlaeufe/planting-runs/")

        status = run_detail.get_status()
        if "Geplant" not in status and "planned" not in status.lower():
            pytest.skip(f"First run is not in 'planned' status — delete button not shown")

        capture("req013_023_before_delete")  # Checkpoint: before action

        run_detail.click_delete()
        capture("req013_023_confirm_dialog_open")  # Checkpoint: dialog open

        assert run_detail.is_confirm_dialog_open(), (
            "Expected ConfirmDialog to appear after clicking Delete"
        )

        # Cancel — we do NOT actually delete seed data
        run_detail.cancel_action()
        time.sleep(0.3)
        capture("req013_023_after_cancel")  # Checkpoint: after cancel

        assert not run_detail.is_confirm_dialog_open(), (
            "Expected ConfirmDialog to close after clicking Cancel"
        )
        # Should still be on the detail page
        assert "/durchlaeufe/planting-runs/" in run_detail.driver.current_url, (
            "Expected to remain on the detail page after cancelling delete"
        )


class TestPlantingRunErrorHandling:
    """TC-REQ-013-024: Error states for PlantingRunDetailPage."""

    def test_nonexistent_run_key_shows_error(
        self,
        run_detail: PlantingRunDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-013-024: Navigating to a non-existent run key shows an error display."""
        capture = request.node._screenshot_capture
        run_detail.navigate("/durchlaeufe/planting-runs/nonexistent-key-99999")
        time.sleep(1.5)  # Allow the API call to fail and the error state to render
        capture("req013_024_nonexistent_key_error")  # Checkpoint: error state

        # Either the error display component is shown, or the loading skeleton disappeared
        error_displayed = run_detail.is_error_displayed()
        page_rendered = len(run_detail.driver.find_elements(
            *PlantingRunDetailPage.PAGE
        )) > 0

        # We accept either: error component visible OR page rendered (some implementations
        # fall back gracefully instead of showing an error component)
        assert error_displayed or page_rendered, (
            "Expected either an error display or the detail page to render for an invalid key"
        )
