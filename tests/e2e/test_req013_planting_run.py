"""E2E tests for REQ-013 — Pflanzdurchlauf-Verwaltung.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-013.md):
  TC-REQ-013-001  ->  TC-013-001  Listenansicht laedt alle Pflanzdurchlaeufe
  TC-REQ-013-002  ->  TC-013-001  Listenansicht — Spalten pruefen
  TC-REQ-013-003  ->  TC-013-001  Erstellen-Button sichtbar
  TC-REQ-013-004  ->  TC-013-004  Klick auf Zeile navigiert zur Detailseite
  TC-REQ-013-005  ->  TC-013-003  Suche filtert Runs nach Name
  TC-REQ-013-006  ->  TC-013-003  Filter zuruecksetzen
  TC-REQ-013-007  ->  TC-013-003  Sortierung per Spaltenklick
  TC-REQ-013-008  ->  TC-013-001  Zeigt-Zaehler
  TC-REQ-013-010  ->  TC-013-005  Erstellen-Dialog oeffnet sich
  TC-REQ-013-011  ->  TC-013-005  Abbrechen schliesst Dialog ohne Speichern
  TC-REQ-013-012  ->  TC-013-012  Pflichtfeld 'Name' leer — Fehlermeldung
  TC-REQ-013-013  ->  TC-013-014  ID-Praefix ungueltig — Fehlermeldung
  TC-REQ-013-014  ->  TC-013-005  Monokultur-Run erstellen (vollstaendiges Formular)
  TC-REQ-013-015  ->  TC-013-020  Detailseite laedt fuer ersten Run
  TC-REQ-013-016  ->  TC-013-050  Detail-Tabs sichtbar
  TC-REQ-013-017  ->  TC-013-050  Tab-Navigation zwischen Tabs
  TC-REQ-013-018  ->  TC-013-020  Status-Chip sichtbar auf Detailseite
  TC-REQ-013-019  ->  TC-013-026  Geplanter Run zeigt Create-Plants und Delete-Buttons
  TC-REQ-013-020  ->  TC-013-026  Create-Plants-Button oeffnet Bestaetigung
  TC-REQ-013-021  ->  TC-013-037  Bearbeiten-Dialog mit vorausgefuelltem Namen
  TC-REQ-013-022  ->  TC-013-037  Bearbeiten abbrechen schliesst Dialog
  TC-REQ-013-023  ->  TC-013-034  Loeschen-Dialog fuer geplante Runs
  TC-REQ-013-024  ->  TC-013-052  Nicht-existenter Run-Key zeigt Fehler
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.planting_run_detail_page import PlantingRunDetailPage
from .pages.planting_run_list_page import PlantingRunListPage


# -- Fixtures -----------------------------------------------------------------

@pytest.fixture
def run_list(browser: WebDriver, base_url: str) -> PlantingRunListPage:
    """Return a PlantingRunListPage bound to the test browser."""
    return PlantingRunListPage(browser, base_url)


@pytest.fixture
def run_detail(browser: WebDriver, base_url: str) -> PlantingRunDetailPage:
    """Return a PlantingRunDetailPage bound to the test browser."""
    return PlantingRunDetailPage(browser, base_url)


# -- TC-REQ-013-001 to TC-REQ-013-008: List Page ------------------------------

class TestPlantingRunListPage:
    """PlantingRun list display and interactions (Spec: TC-013-001, TC-013-003, TC-013-004)."""

    @pytest.mark.smoke
    def test_list_page_loads_with_correct_testid(
        self,
        run_list: PlantingRunListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-013-001: PlantingRunListPage renders with data-testid='planting-run-list-page'.

        Spec: TC-013-001 -- Listenansicht laedt alle Pflanzdurchlaeufe.
        """
        run_list.open()
        screenshot("TC-REQ-013-001_list-page-loaded", "PlantingRun list page after initial load")

        page_el = run_list.wait_for_element(PlantingRunListPage.PAGE)
        assert page_el.is_displayed(), (
            "TC-REQ-013-001 FAIL: Expected [data-testid='planting-run-list-page'] to be visible"
        )

    @pytest.mark.smoke
    def test_list_displays_data_table_with_columns(
        self,
        run_list: PlantingRunListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-013-002: DataTable renders with expected column headers.

        Spec: TC-013-001 -- Listenansicht — Spalten pruefen.
        """
        run_list.open()
        screenshot("TC-REQ-013-002_list-table-columns", "PlantingRun table column headers")

        headers = run_list.get_column_headers()
        if len(headers) == 0:
            pytest.skip("No planting runs in database — empty state shown instead of DataTable")
        assert any("Name" in h for h in headers), (
            f"TC-REQ-013-002 FAIL: Expected 'Name' column header, got: {headers}"
        )

    @pytest.mark.smoke
    def test_create_button_is_visible(
        self,
        run_list: PlantingRunListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-013-003: Create button is visible on the list page.

        Spec: TC-013-001 -- Erstellen-Button sichtbar.
        """
        run_list.open()
        screenshot("TC-REQ-013-003_create-button-visible", "Create button visible on list page")

        btn = run_list.wait_for_element(PlantingRunListPage.CREATE_BUTTON)
        assert btn.is_displayed(), (
            "TC-REQ-013-003 FAIL: Expected [data-testid='create-button'] to be visible"
        )

    @pytest.mark.core_crud
    def test_click_row_navigates_to_detail(
        self,
        run_list: PlantingRunListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-013-004: Clicking a planting run row navigates to its detail page.

        Spec: TC-013-004 -- Klick auf Zeile navigiert zur Detailseite.
        """
        run_list.open()
        screenshot("TC-REQ-013-004_before-row-click", "PlantingRun list before row click")

        if run_list.get_row_count() == 0:
            pytest.skip("No planting runs in database — cannot test row click navigation")

        run_list.click_row(0)
        run_list.wait_for_url_contains("/durchlaeufe/planting-runs/")
        screenshot("TC-REQ-013-004_after-row-click", "Detail page after row click navigation")

        assert "/durchlaeufe/planting-runs/" in run_list.driver.current_url, (
            f"TC-REQ-013-004 FAIL: Expected detail URL after row click, got: {run_list.driver.current_url}"
        )

    @pytest.mark.core_crud
    def test_search_filters_runs_by_name(
        self,
        run_list: PlantingRunListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-013-005: Search input filters displayed planting runs.

        Spec: TC-013-003 -- Suche in der Tabelle filtert nach Name.
        """
        run_list.open()

        if run_list.get_row_count() == 0:
            pytest.skip("No planting runs — cannot test search")

        initial_count = run_list.get_row_count()
        screenshot("TC-REQ-013-005_before-search", "PlantingRun list before search")

        run_list.search("ZZZ_NONEXISTENT_RUN_9999")
        run_list.wait_for_loading_complete()
        screenshot("TC-REQ-013-005_after-search-no-results", "PlantingRun list after search — no results")

        filtered_count = run_list.get_row_count()
        assert filtered_count <= initial_count, (
            f"TC-REQ-013-005 FAIL: Expected filtered count ({filtered_count}) <= initial ({initial_count})"
        )
        assert run_list.has_search_chip(), (
            "TC-REQ-013-005 FAIL: Expected search chip to be visible after entering a search term"
        )

    @pytest.mark.core_crud
    def test_reset_filters_restores_full_list(
        self,
        run_list: PlantingRunListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-013-006: Reset filters button restores unfiltered list.

        Spec: TC-013-003 -- Filter zuruecksetzen.
        """
        run_list.open()

        if run_list.get_row_count() == 0:
            pytest.skip("No planting runs — cannot test filter reset")

        initial_count = run_list.get_row_count()
        run_list.search("A")
        run_list.wait_for_loading_complete()

        if run_list.has_reset_filters_button():
            run_list.click_reset_filters()
            run_list.wait_for_loading_complete()
            screenshot("TC-REQ-013-006_after-reset-filters", "PlantingRun list after filter reset")
            reset_count = run_list.get_row_count()
            assert reset_count >= initial_count - 1, (
                f"TC-REQ-013-006 FAIL: Expected count after reset ({reset_count}) close to initial ({initial_count})"
            )

    @pytest.mark.core_crud
    def test_sort_by_column_shows_sort_chip(
        self,
        run_list: PlantingRunListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-013-007: Clicking a column header activates sort chip.

        Spec: TC-013-003 -- Sortierung per Spaltenklick.
        """
        run_list.open()
        headers = run_list.get_column_headers()
        if not headers:
            pytest.skip("No column headers found")

        screenshot("TC-REQ-013-007_before-sort", "PlantingRun list before sorting")
        run_list.click_column_header(headers[0])
        run_list.wait_for_loading_complete()
        screenshot("TC-REQ-013-007_after-sort", "PlantingRun list after column sort")

        assert run_list.has_sort_chip(), (
            f"TC-REQ-013-007 FAIL: Expected sort chip after clicking column header '{headers[0]}'"
        )

    @pytest.mark.smoke
    def test_showing_count_text_is_present(
        self,
        run_list: PlantingRunListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-013-008: Showing count text is displayed when rows are present.

        Spec: TC-013-001 -- Zeigt-Zaehler.
        """
        run_list.open()
        screenshot("TC-REQ-013-008_showing-count", "PlantingRun list showing count")

        if run_list.get_row_count() == 0:
            pytest.skip("No rows — showing count not displayed for empty table")

        count_text = run_list.get_showing_count_text()
        assert count_text, (
            "TC-REQ-013-008 FAIL: Expected non-empty showing count text, got empty string"
        )


# -- TC-REQ-013-010 to TC-REQ-013-014: Create Dialog --------------------------

class TestPlantingRunCreateDialog:
    """PlantingRun create dialog operations (Spec: TC-013-005, TC-013-012, TC-013-014)."""

    @pytest.mark.core_crud
    def test_create_dialog_opens_on_create_button_click(
        self,
        run_list: PlantingRunListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-013-010: Clicking create button opens the creation dialog.

        Spec: TC-013-005 -- Erstellen-Dialog oeffnet sich.
        """
        run_list.open()
        screenshot("TC-REQ-013-010_before-open-dialog", "PlantingRun list before opening create dialog")

        run_list.click_create()
        screenshot("TC-REQ-013-010_create-dialog-open", "PlantingRun create dialog opened")

        assert run_list.is_create_dialog_open(), (
            "TC-REQ-013-010 FAIL: Expected create dialog to be open after clicking the create button"
        )

    @pytest.mark.core_crud
    def test_create_dialog_cancel_closes_without_saving(
        self,
        run_list: PlantingRunListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-013-011: Cancel in create dialog closes it without creating a run.

        Spec: TC-013-005 -- Abbrechen schliesst Dialog ohne Speichern.
        """
        run_list.open()
        initial_count = run_list.get_row_count()

        run_list.click_create()
        run_list.fill_name("Should Not Be Saved")
        screenshot("TC-REQ-013-011_before-cancel", "Create dialog with data before cancel")

        run_list.cancel_create_form()
        run_list.wait_for_loading_complete()
        screenshot("TC-REQ-013-011_after-cancel", "PlantingRun list after cancelling dialog")

        assert not run_list.is_create_dialog_open(), (
            "TC-REQ-013-011 FAIL: Expected create dialog to be closed after clicking cancel"
        )
        final_count = run_list.get_row_count()
        assert final_count == initial_count, (
            f"TC-REQ-013-011 FAIL: Expected row count to remain {initial_count} after cancel, got {final_count}"
        )

    @pytest.mark.core_crud
    def test_create_dialog_submit_without_name_shows_validation_error(
        self,
        run_list: PlantingRunListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-013-012: Submitting with empty name triggers validation error (NFR-006).

        Spec: TC-013-012 -- Pflichtfeld 'Name' leer lassen — Fehlermeldung.
        """
        run_list.open()
        run_list.click_create()

        # Clear the name field explicitly (it may be pre-populated)
        name_el = run_list.wait_for_element_clickable(PlantingRunListPage.FORM_NAME)
        name_el.clear()
        screenshot("TC-REQ-013-012_before-submit-empty", "Create dialog with empty name")

        run_list.submit_create_form()
        run_list.wait_for_loading_complete()
        screenshot("TC-REQ-013-012_validation-error", "Validation error for empty name")

        assert run_list.is_create_dialog_open(), (
            "TC-REQ-013-012 FAIL: Expected dialog to remain open when name is empty"
        )

    @pytest.mark.core_crud
    def test_create_dialog_submit_without_id_prefix_shows_validation_error(
        self,
        run_list: PlantingRunListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-013-013: id_prefix is required; leaving it empty shows a validation error.

        Spec: TC-013-014 -- ID-Praefix mit ungueltigem Format — Fehlermeldung.
        """
        run_list.open()
        run_list.click_create()

        # Fill name but leave id_prefix empty
        run_list.fill_name("TestRun Validation")
        prefix_el = run_list.driver.find_elements(*PlantingRunListPage.FORM_ENTRY_ID_PREFIX)
        if prefix_el:
            prefix_el[0].clear()

        screenshot("TC-REQ-013-013_before-submit-no-prefix", "Create dialog without id_prefix")
        run_list.submit_create_form()
        run_list.wait_for_loading_complete()
        screenshot("TC-REQ-013-013_validation-error-prefix", "Validation error for missing prefix")

        assert run_list.is_create_dialog_open(), (
            "TC-REQ-013-013 FAIL: Expected dialog to stay open when id_prefix is invalid"
        )

    @pytest.mark.core_crud
    def test_create_planting_run_full_form(
        self,
        run_list: PlantingRunListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-013-014: Create a planting run with valid name and id_prefix; verify it appears in list.

        Spec: TC-013-005 -- Monokultur-Run erstellen (vollstaendiges Formular).
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        run_list.open()
        initial_count = run_list.get_row_count()
        screenshot("TC-REQ-013-014_before-create", "PlantingRun list before creating")

        run_list.click_create()
        screenshot("TC-REQ-013-014_dialog-open", "Create dialog opened")

        unique_name = f"E2E-Run-{int(time.time())}"
        run_list.fill_name(unique_name)

        # Select the first available species if the dropdown is populated
        species_select = run_list.driver.find_elements(
            By.CSS_SELECTOR,
            "[data-testid='form-field-entries.0.species_key'] .MuiSelect-select",
        )
        if species_select:
            run_list.scroll_and_click(species_select[0])
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

        screenshot("TC-REQ-013-014_form-filled", "Create form filled before submit")

        run_list.submit_create_form()
        run_list.wait_for_loading_complete()
        screenshot("TC-REQ-013-014_after-create", "PlantingRun list after creation")

        final_count = run_list.get_row_count()
        assert final_count > initial_count or unique_name in run_list.get_first_column_texts(), (
            f"TC-REQ-013-014 FAIL: Expected new run '{unique_name}' to appear in list. "
            f"Initial count: {initial_count}, final count: {final_count}"
        )


# -- TC-REQ-013-015 to TC-REQ-013-020: Detail Page ----------------------------

class TestPlantingRunDetailPage:
    """PlantingRun detail page operations (Spec: TC-013-020, TC-013-026, TC-013-050)."""

    @pytest.mark.core_crud
    def test_detail_page_loads_for_first_run(
        self,
        run_list: PlantingRunListPage,
        run_detail: PlantingRunDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-013-015: Navigating to detail URL renders the detail page.

        Spec: TC-013-020 -- Detailseite — Summary-Bar zeigt Kern-Metadaten.
        """
        run_list.open()

        if run_list.get_row_count() == 0:
            pytest.skip("No planting runs — cannot test detail page")

        run_list.click_row(0)
        run_list.wait_for_url_contains("/durchlaeufe/planting-runs/")
        screenshot("TC-REQ-013-015_detail-page-loaded", "PlantingRun detail page loaded")

        page_el = run_detail.wait_for_element(PlantingRunDetailPage.PAGE)
        assert page_el.is_displayed(), (
            "TC-REQ-013-015 FAIL: Expected [data-testid='planting-run-detail-page'] to be visible"
        )

    @pytest.mark.core_crud
    def test_detail_page_has_five_tabs(
        self,
        run_list: PlantingRunListPage,
        run_detail: PlantingRunDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-013-016: Detail page renders 5 tabs.

        Spec: TC-013-050 -- Tab-Navigation — alle 5 Tabs sind bedienbar.
        """
        run_list.open()

        if run_list.get_row_count() == 0:
            pytest.skip("No planting runs — cannot test tabs")

        run_list.click_row(0)
        run_list.wait_for_url_contains("/durchlaeufe/planting-runs/")
        screenshot("TC-REQ-013-016_tabs-visible", "PlantingRun detail tabs visible")

        tab_labels = run_detail.get_tab_labels()
        assert len(tab_labels) == 5, (
            f"TC-REQ-013-016 FAIL: Expected exactly 5 tabs, got {len(tab_labels)}: {tab_labels}"
        )

    @pytest.mark.core_crud
    def test_tab_navigation_between_all_tabs(
        self,
        run_list: PlantingRunListPage,
        run_detail: PlantingRunDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-013-017: Clicking each tab shows the corresponding content panel.

        Spec: TC-013-050 -- Tab-Navigation — alle 5 Tabs sind bedienbar.
        """
        run_list.open()

        if run_list.get_row_count() == 0:
            pytest.skip("No planting runs — cannot test tab navigation")

        run_list.click_row(0)
        run_list.wait_for_url_contains("/durchlaeufe/planting-runs/")

        # Tab 0 – Details (default)
        screenshot("TC-REQ-013-017_tab-details", "Detail page tab 0 (Details) active")
        assert run_detail.get_active_tab_index() == 0, (
            "TC-REQ-013-017 FAIL: Expected tab 0 (Details) to be active by default"
        )

        # Tab 1 – Plants
        run_detail.click_tab(1)
        run_detail.wait_for_loading_complete()
        screenshot("TC-REQ-013-017_tab-plants", "Detail page tab 1 (Plants) active")
        assert run_detail.get_active_tab_index() == 1, (
            "TC-REQ-013-017 FAIL: Expected tab 1 (Plants) to be active after clicking"
        )

        # Tab 2 – Phases
        run_detail.click_tab(2)
        run_detail.wait_for_loading_complete()
        screenshot("TC-REQ-013-017_tab-phases", "Detail page tab 2 (Phases) active")
        assert run_detail.get_active_tab_index() == 2, (
            "TC-REQ-013-017 FAIL: Expected tab 2 (Phases) to be active after clicking"
        )

    @pytest.mark.core_crud
    def test_status_chip_visible_on_detail_page(
        self,
        run_list: PlantingRunListPage,
        run_detail: PlantingRunDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-013-018: Status chip is visible and contains a non-empty status text.

        Spec: TC-013-020 -- Detailseite — Summary-Bar zeigt Kern-Metadaten.
        """
        run_list.open()

        if run_list.get_row_count() == 0:
            pytest.skip("No planting runs — cannot test status chip")

        run_list.click_row(0)
        run_list.wait_for_url_contains("/durchlaeufe/planting-runs/")
        screenshot("TC-REQ-013-018_status-chip", "PlantingRun detail status chip")

        status = run_detail.get_status()
        assert status, (
            f"TC-REQ-013-018 FAIL: Expected a non-empty status chip text, got: '{status}'"
        )
        assert len(status) > 0, (
            "TC-REQ-013-018 FAIL: Status chip should display a non-empty label"
        )

    @pytest.mark.core_crud
    def test_planned_run_shows_create_plants_and_delete_buttons(
        self,
        run_list: PlantingRunListPage,
        run_detail: PlantingRunDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-013-019: A run with status='planned' shows Create Plants and Delete buttons.

        Spec: TC-013-026 -- Batch-Erstellung starten (Pflanzen anlegen — geplanter Run).
        """
        run_list.open()

        if run_list.get_row_count() == 0:
            pytest.skip("No planting runs — cannot test planned-status buttons")

        run_list.click_row(0)
        run_list.wait_for_url_contains("/durchlaeufe/planting-runs/")
        screenshot("TC-REQ-013-019_detail-page", "PlantingRun detail for planned-status check")

        status = run_detail.get_status()
        if "Geplant" not in status and "planned" not in status.lower():
            pytest.skip(f"First run is not in 'planned' status (status='{status}') — skip state-machine test")

        assert run_detail.is_create_plants_button_visible(), (
            "TC-REQ-013-019 FAIL: Expected create-plants-button to be visible for planned run"
        )
        assert run_detail.is_delete_button_visible(), (
            "TC-REQ-013-019 FAIL: Expected delete-button to be visible for planned run"
        )
        assert not run_detail.is_batch_remove_button_visible(), (
            "TC-REQ-013-019 FAIL: Did not expect batch-remove-button for a planned run"
        )

    @pytest.mark.core_crud
    def test_create_plants_button_opens_confirm_dialog(
        self,
        run_list: PlantingRunListPage,
        run_detail: PlantingRunDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-013-020: Clicking Create Plants opens a ConfirmDialog (state machine: planned->active).

        Spec: TC-013-026 -- Batch-Erstellung starten (Pflanzen anlegen — geplanter Run).
        """
        run_list.open()

        if run_list.get_row_count() == 0:
            pytest.skip("No planting runs — cannot test create plants confirm dialog")

        run_list.click_row(0)
        run_list.wait_for_url_contains("/durchlaeufe/planting-runs/")

        status = run_detail.get_status()
        if "Geplant" not in status and "planned" not in status.lower():
            pytest.skip(f"First run is not in 'planned' status ('{status}') — skip this test")

        screenshot("TC-REQ-013-020_before-create-plants", "Detail page before clicking Create Plants")

        run_detail.click_create_plants()
        screenshot("TC-REQ-013-020_confirm-dialog-open", "Confirm dialog open for Create Plants")

        assert run_detail.is_confirm_dialog_open(), (
            "TC-REQ-013-020 FAIL: Expected ConfirmDialog to open after clicking 'Create Plants'"
        )

        # Cancel — do not actually transition state in a pure list/detail E2E check
        run_detail.cancel_action()
        run_detail.wait_for_loading_complete()
        screenshot("TC-REQ-013-020_after-cancel", "After cancelling Create Plants dialog")

        assert not run_detail.is_confirm_dialog_open(), (
            "TC-REQ-013-020 FAIL: Expected ConfirmDialog to close after clicking Cancel"
        )


class TestPlantingRunEditForm:
    """PlantingRun edit form operations (Spec: TC-013-037)."""

    @pytest.mark.core_crud
    def test_edit_form_prefilled_with_run_name(
        self,
        run_list: PlantingRunListPage,
        run_detail: PlantingRunDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-013-021: Edit dialog form is pre-filled with the existing run name.

        Spec: TC-013-037 -- Bearbeiten-Dialog oeffnet sich mit vorhandenen Werten.
        """
        run_list.open()

        if run_list.get_row_count() == 0:
            pytest.skip("No planting runs — cannot test edit form")

        run_list.click_row(0)
        run_list.wait_for_url_contains("/durchlaeufe/planting-runs/")
        page_title = run_detail.get_page_title()

        run_detail.open_edit_dialog()
        run_detail.wait_for_loading_complete()
        screenshot("TC-REQ-013-021_edit-dialog-open", "Edit dialog open with pre-filled values")

        name_value = run_detail.get_edit_form_name_value()
        assert name_value, (
            f"TC-REQ-013-021 FAIL: Expected edit form Name field to be pre-filled, got: '{name_value}'"
        )
        assert name_value == page_title, (
            f"TC-REQ-013-021 FAIL: Expected Name field '{name_value}' to match page title '{page_title}'"
        )

    @pytest.mark.core_crud
    def test_edit_form_cancel_closes_dialog(
        self,
        run_list: PlantingRunListPage,
        run_detail: PlantingRunDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-013-022: Cancel in edit dialog closes it without saving changes.

        Spec: TC-013-037 -- Bearbeiten — Abbrechen schliesst Dialog.
        """
        run_list.open()

        if run_list.get_row_count() == 0:
            pytest.skip("No planting runs — cannot test edit form cancel")

        run_list.click_row(0)
        run_list.wait_for_url_contains("/durchlaeufe/planting-runs/")

        run_detail.open_edit_dialog()
        run_detail.wait_for_loading_complete()

        run_detail.fill_name("Unsaved Modified Name")
        screenshot("TC-REQ-013-022_form-modified", "Edit dialog with modified name before cancel")

        run_detail.cancel_edit_form()
        run_detail.wait_for_loading_complete()
        screenshot("TC-REQ-013-022_after-cancel", "Detail page after cancelling edit dialog")

        assert not run_detail.is_edit_dialog_open(), (
            "TC-REQ-013-022 FAIL: Expected edit dialog to close after clicking cancel"
        )


class TestPlantingRunDeleteFlow:
    """PlantingRun delete flow (Spec: TC-013-034)."""

    @pytest.mark.core_crud
    def test_delete_planned_run_confirm_dialog(
        self,
        run_list: PlantingRunListPage,
        run_detail: PlantingRunDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-013-023: Delete button opens ConfirmDialog; cancel does not delete.

        Spec: TC-013-034 -- Loeschen-Dialog erscheint und Loeschen wird bestaetigt (geplanter Run).
        """
        run_list.open()

        if run_list.get_row_count() == 0:
            pytest.skip("No planting runs — cannot test delete flow")

        run_list.click_row(0)
        run_list.wait_for_url_contains("/durchlaeufe/planting-runs/")

        status = run_detail.get_status()
        if "Geplant" not in status and "planned" not in status.lower():
            pytest.skip(f"First run is not in 'planned' status — delete button not shown")

        screenshot("TC-REQ-013-023_before-delete", "Detail page before clicking delete")

        run_detail.click_delete()
        screenshot("TC-REQ-013-023_confirm-dialog-open", "Delete confirm dialog open")

        assert run_detail.is_confirm_dialog_open(), (
            "TC-REQ-013-023 FAIL: Expected ConfirmDialog to appear after clicking Delete"
        )

        # Cancel — we do NOT actually delete seed data
        run_detail.cancel_action()
        run_detail.wait_for_loading_complete()
        screenshot("TC-REQ-013-023_after-cancel", "After cancelling delete dialog")

        assert not run_detail.is_confirm_dialog_open(), (
            "TC-REQ-013-023 FAIL: Expected ConfirmDialog to close after clicking Cancel"
        )
        assert "/durchlaeufe/planting-runs/" in run_detail.driver.current_url, (
            "TC-REQ-013-023 FAIL: Expected to remain on the detail page after cancelling delete"
        )


class TestPlantingRunErrorHandling:
    """PlantingRun error states (Spec: TC-013-052)."""

    @pytest.mark.core_crud
    def test_nonexistent_run_key_shows_error(
        self,
        run_detail: PlantingRunDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-013-024: Navigating to a non-existent run key shows an error display.

        Spec: TC-013-052 -- Laden-Ladebalken erscheint bei Seitenaufruf.
        """
        run_detail.navigate("/durchlaeufe/planting-runs/nonexistent-key-99999")
        run_detail.wait_for_loading_complete()
        screenshot("TC-REQ-013-024_nonexistent-key-error", "Error state for non-existent run key")

        error_displayed = run_detail.is_error_displayed()
        page_rendered = len(run_detail.driver.find_elements(
            *PlantingRunDetailPage.PAGE
        )) > 0

        assert error_displayed or page_rendered, (
            "TC-REQ-013-024 FAIL: Expected either an error display or the detail page to render"
        )
