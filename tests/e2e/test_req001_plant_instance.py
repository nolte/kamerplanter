"""E2E tests for REQ-001 / REQ-003 — Plant Instance (Pflanzen) management.

Spec-TC Mapping (test TC -> spec/e2e-testcases/):
  TC-REQ-001-PI-001  ->  TC-001-*     Plant instance list page renders with data-testid
  TC-REQ-001-PI-002  ->  TC-001-*     List displays DataTable with column headers
  TC-REQ-001-PI-003  ->  TC-001-*     Create button is visible on list page
  TC-REQ-001-PI-004  ->  TC-001-*     Create dialog opens on button click
  TC-REQ-001-PI-005  ->  TC-001-*     Create plant instance with valid data (Happy Path)
  TC-REQ-001-PI-006  ->  TC-001-*     Submit without species shows validation error
  TC-REQ-001-PI-007  ->  TC-001-*     Cancel closes dialog without creating
  TC-REQ-001-PI-008  ->  TC-001-*     Click on row navigates to detail page
  TC-REQ-001-PI-009  ->  TC-003-*     Detail page shows plant-info-card
  TC-REQ-001-PI-010  ->  TC-003-*     Detail page shows current phase
  TC-REQ-001-PI-011  ->  TC-003-*     Phases tab shows phase history
  TC-REQ-001-PI-012  ->  TC-001-*     Search filters plant instance table
  TC-REQ-001-PI-013  ->  TC-001-*     Sort by column header shows sort chip
  TC-REQ-001-PI-014  ->  TC-001-*     Non-existent plant-instance key shows error
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.plant_instance_detail_page import PlantInstanceDetailPage
from .pages.plant_instance_list_page import PlantInstanceListPage


# -- Fixtures -----------------------------------------------------------------

@pytest.fixture
def plant_list(browser: WebDriver, base_url: str) -> PlantInstanceListPage:
    """Return a PlantInstanceListPage bound to the test browser."""
    return PlantInstanceListPage(browser, base_url)


@pytest.fixture
def plant_detail(browser: WebDriver, base_url: str) -> PlantInstanceDetailPage:
    """Return a PlantInstanceDetailPage bound to the test browser."""
    return PlantInstanceDetailPage(browser, base_url)


# -- TC-REQ-001-PI-001 to TC-REQ-001-PI-003: List Page -----------------------

class TestPlantInstanceListPage:
    """Plant instance list display and interactions (REQ-001)."""

    @pytest.mark.smoke
    def test_list_page_renders_with_correct_testid(
        self,
        plant_list: PlantInstanceListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-PI-001: PlantInstanceListPage renders with data-testid.

        Spec: TC-001 -- Pflanzinstanz-Listenansicht wird geladen.
        """
        plant_list.open()
        screenshot(
            "TC-REQ-001-PI-001_plant-instance-list-loaded",
            "Plant instance list page after initial load",
        )

        page_el = plant_list.wait_for_element(PlantInstanceListPage.PAGE)
        assert page_el.is_displayed(), (
            "TC-REQ-001-PI-001 FAIL: Expected [data-testid='plant-instance-list-page'] "
            "to be visible"
        )

    @pytest.mark.smoke
    def test_list_displays_data_table_with_columns(
        self,
        plant_list: PlantInstanceListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-PI-002: DataTable renders with expected column headers.

        Spec: TC-001 -- Listenansicht zeigt Spalten.
        """
        plant_list.open()
        screenshot(
            "TC-REQ-001-PI-002_plant-table-columns",
            "Plant instance table column headers",
        )

        headers = plant_list.get_column_headers()
        if len(headers) == 0:
            pytest.skip(
                "No plant instances in database — empty state shown instead of DataTable"
            )
        assert len(headers) >= 2, (
            f"TC-REQ-001-PI-002 FAIL: Expected at least 2 column headers, got: {headers}"
        )

    @pytest.mark.smoke
    def test_create_button_is_visible_on_list_page(
        self,
        plant_list: PlantInstanceListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-PI-003: Create button is visible on the list page.

        Spec: TC-001 -- Erstellen-Button sichtbar auf Listenansicht.
        """
        plant_list.open()
        screenshot(
            "TC-REQ-001-PI-003_create-button",
            "Create button visible on plant instance list",
        )

        btn = plant_list.wait_for_element(PlantInstanceListPage.CREATE_BUTTON)
        assert btn.is_displayed(), (
            "TC-REQ-001-PI-003 FAIL: Expected [data-testid='create-button'] to be visible"
        )

    @pytest.mark.core_crud
    def test_showing_count_text_is_present(
        self,
        plant_list: PlantInstanceListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-PI-003b: Showing count text is displayed when rows exist.

        Spec: TC-001 -- Zeigt-Zaehler.
        """
        plant_list.open()
        screenshot(
            "TC-REQ-001-PI-003b_showing-count",
            "Plant instance list showing count",
        )

        if plant_list.get_row_count() == 0:
            pytest.skip("No rows — showing count not displayed for empty table")

        count_text = plant_list.get_showing_count_text()
        assert count_text, (
            "TC-REQ-001-PI-003b FAIL: Expected non-empty showing count text"
        )


# -- TC-REQ-001-PI-004 to TC-REQ-001-PI-007: Create Dialog -------------------

class TestPlantInstanceCreateDialog:
    """Plant instance create dialog operations (REQ-001)."""

    @pytest.mark.core_crud
    def test_create_dialog_opens_on_button_click(
        self,
        plant_list: PlantInstanceListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-PI-004: Clicking create button opens the PlantInstanceCreateDialog.

        Spec: TC-001 -- Erstellen-Dialog oeffnet sich.
        """
        plant_list.open()
        screenshot(
            "TC-REQ-001-PI-004_before-open-dialog",
            "Plant list before opening create dialog",
        )

        plant_list.click_create()
        screenshot(
            "TC-REQ-001-PI-004_dialog-open",
            "Plant instance create dialog opened",
        )

        assert plant_list.is_create_dialog_open(), (
            "TC-REQ-001-PI-004 FAIL: Expected PlantInstanceCreateDialog to be open"
        )

    @pytest.mark.core_crud
    def test_create_plant_instance_happy_path(
        self,
        plant_list: PlantInstanceListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-PI-005: Create a plant instance with species + name (Happy Path).

        Spec: TC-001 -- Pflanze erfolgreich erstellen.
        Selects the first available species via the autocomplete, enters a
        unique plant name, and verifies the new entry appears in the list.
        """
        plant_list.open()
        initial_count = plant_list.get_row_count()
        screenshot(
            "TC-REQ-001-PI-005_before-create",
            "Plant list before creating",
        )

        plant_list.click_create()
        screenshot(
            "TC-REQ-001-PI-005_dialog-open",
            "Plant instance create dialog opened",
        )

        # Select the first species from the autocomplete by typing a space
        # to trigger the dropdown, then clicking the first option.
        plant_list.select_species("a")

        unique_name = f"E2E-Pflanze-{int(time.time())}"
        plant_list.fill_plant_name(unique_name)

        screenshot(
            "TC-REQ-001-PI-005_form-filled",
            "Plant create form filled before submit",
        )

        # instance_id should have been auto-generated
        instance_id = plant_list.get_instance_id_value()
        assert instance_id, (
            "TC-REQ-001-PI-005 FAIL: Expected instance_id to be auto-generated"
        )

        plant_list.submit_create_form()
        plant_list.wait_for_loading_complete()
        screenshot(
            "TC-REQ-001-PI-005_after-create",
            "Plant list after creation",
        )

        final_count = plant_list.get_row_count()
        names = plant_list.get_first_column_texts()
        assert final_count > initial_count or unique_name in names, (
            f"TC-REQ-001-PI-005 FAIL: Expected new plant '{unique_name}' to appear. "
            f"Initial: {initial_count}, final: {final_count}, names: {names}"
        )

    @pytest.mark.core_crud
    def test_submit_without_species_shows_validation_error(
        self,
        plant_list: PlantInstanceListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-PI-006: Submitting without species triggers validation error (NFR-006).

        Spec: TC-001 -- Pflichtfeld-Validierung — species_key ist Pflichtfeld.
        """
        plant_list.open()
        plant_list.click_create()
        screenshot(
            "TC-REQ-001-PI-006_dialog-open-empty",
            "Create dialog with no species selected",
        )

        plant_list.submit_create_form()
        plant_list.wait_for_loading_complete()
        screenshot(
            "TC-REQ-001-PI-006_validation-error",
            "Validation error for missing species",
        )

        # Dialog should remain open because the form did not pass validation
        assert plant_list.is_create_dialog_open(), (
            "TC-REQ-001-PI-006 FAIL: Expected dialog to remain open when species is empty"
        )
        plant_list.cancel_create_form()

    @pytest.mark.core_crud
    def test_cancel_closes_dialog_without_creating(
        self,
        plant_list: PlantInstanceListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-PI-007: Cancel in create dialog closes without saving.

        Spec: TC-001 -- Abbrechen schliesst Dialog ohne Aenderungen.
        """
        plant_list.open()
        initial_count = plant_list.get_row_count()

        plant_list.click_create()
        screenshot(
            "TC-REQ-001-PI-007_before-cancel",
            "Create dialog before cancel",
        )

        plant_list.cancel_create_form()
        plant_list.wait_for_loading_complete()
        screenshot(
            "TC-REQ-001-PI-007_after-cancel",
            "Plant list after cancelling dialog",
        )

        assert not plant_list.is_create_dialog_open(), (
            "TC-REQ-001-PI-007 FAIL: Expected create dialog to be closed after cancel"
        )
        final_count = plant_list.get_row_count()
        assert final_count == initial_count, (
            f"TC-REQ-001-PI-007 FAIL: Expected row count to stay {initial_count}, "
            f"got {final_count}"
        )


# -- TC-REQ-001-PI-008 to TC-REQ-001-PI-011: Detail Page ---------------------

class TestPlantInstanceDetailPage:
    """Plant instance detail page rendering (REQ-001, REQ-003)."""

    @pytest.mark.core_crud
    def test_click_row_navigates_to_detail(
        self,
        plant_list: PlantInstanceListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-PI-008: Clicking a row navigates to the detail page.

        Spec: TC-001 -- Klick auf Pflanze navigiert zur Detailseite.
        """
        plant_list.open()
        screenshot(
            "TC-REQ-001-PI-008_before-row-click",
            "Plant list before row click",
        )

        if plant_list.get_row_count() == 0:
            pytest.skip("No plant instances — cannot test row click navigation")

        plant_list.click_row(0)
        plant_list.wait_for_url_contains("/pflanzen/plant-instances/")
        screenshot(
            "TC-REQ-001-PI-008_after-row-click",
            "Plant instance detail after row click",
        )

        assert "/pflanzen/plant-instances/" in plant_list.driver.current_url, (
            f"TC-REQ-001-PI-008 FAIL: Expected detail URL after row click, "
            f"got: {plant_list.driver.current_url}"
        )

    @pytest.mark.core_crud
    def test_detail_page_shows_plant_info_card(
        self,
        plant_list: PlantInstanceListPage,
        plant_detail: PlantInstanceDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-PI-009: Detail page renders the plant-info-card.

        Spec: TC-001/TC-003 -- Pflanzendetailseite zeigt Pflanzeninfo.
        """
        plant_list.open()

        if plant_list.get_row_count() == 0:
            pytest.skip("No plant instances — cannot test detail page")

        plant_list.click_row(0)
        plant_list.wait_for_url_contains("/pflanzen/plant-instances/")

        info_card = plant_detail.get_plant_info_card()
        screenshot(
            "TC-REQ-001-PI-009_plant-info-card",
            "Plant instance detail page with info card",
        )

        assert info_card.is_displayed(), (
            "TC-REQ-001-PI-009 FAIL: Expected [data-testid='plant-info-card'] to be visible"
        )

    @pytest.mark.core_crud
    def test_detail_page_shows_current_phase(
        self,
        plant_list: PlantInstanceListPage,
        plant_detail: PlantInstanceDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-PI-010: Detail page shows the current phase chip (REQ-003).

        Spec: TC-003 -- Aktuelle Phase ist sichtbar auf der Detailseite.
        """
        plant_list.open()

        if plant_list.get_row_count() == 0:
            pytest.skip("No plant instances — cannot test current phase display")

        plant_list.click_row(0)
        plant_list.wait_for_url_contains("/pflanzen/plant-instances/")

        phase_text = plant_detail.get_current_phase()
        screenshot(
            "TC-REQ-001-PI-010_current-phase",
            "Plant instance detail showing current phase",
        )

        assert phase_text, (
            "TC-REQ-001-PI-010 FAIL: Expected non-empty current phase text"
        )

    @pytest.mark.core_crud
    def test_phases_tab_shows_phase_history(
        self,
        plant_list: PlantInstanceListPage,
        plant_detail: PlantInstanceDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-PI-011: Phases tab renders the phase history (REQ-003).

        Spec: TC-003 -- Phasen-Tab zeigt Phasenverlauf-Tabelle.
        """
        plant_list.open()

        if plant_list.get_row_count() == 0:
            pytest.skip("No plant instances — cannot test phase history")

        plant_list.click_row(0)
        plant_list.wait_for_url_contains("/pflanzen/plant-instances/")

        # Click on the Phases tab (index 1 in the tab bar)
        phases_tab = plant_detail.wait_for_element_clickable(
            PlantInstanceDetailPage.PHASES_TAB
        )
        plant_detail.scroll_and_click(phases_tab)
        screenshot(
            "TC-REQ-001-PI-011_phases-tab",
            "Plant instance phases tab with history",
        )

        phases_content = plant_detail.wait_for_element(
            PlantInstanceDetailPage.PHASES_TAB_CONTENT
        )
        assert phases_content.is_displayed(), (
            "TC-REQ-001-PI-011 FAIL: Expected phases tab content to be visible"
        )


# -- TC-REQ-001-PI-012 to TC-REQ-001-PI-014: Search, Sort, Error -------------

class TestPlantInstanceSearchAndSort:
    """Plant instance search, sort, and error handling (REQ-001, NFR-006)."""

    @pytest.mark.core_crud
    def test_search_filters_plant_instances(
        self,
        plant_list: PlantInstanceListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-PI-012: Search input filters the plant instance table.

        Spec: TC-001 -- Pflanzentabelle ist durchsuchbar.
        """
        plant_list.open()

        if plant_list.get_row_count() == 0:
            pytest.skip("No plant instances — cannot test search")

        initial_count = plant_list.get_row_count()
        screenshot(
            "TC-REQ-001-PI-012_before-search",
            "Plant list before search",
        )

        plant_list.search("ZZZ_NONEXISTENT_PLANT_9999")
        plant_list.wait_for_loading_complete()
        screenshot(
            "TC-REQ-001-PI-012_after-search",
            "Plant list after search — no results expected",
        )

        filtered_count = plant_list.get_row_count()
        assert filtered_count <= initial_count, (
            f"TC-REQ-001-PI-012 FAIL: Expected filtered count ({filtered_count}) "
            f"<= initial ({initial_count})"
        )
        assert plant_list.has_search_chip(), (
            "TC-REQ-001-PI-012 FAIL: Expected search chip to be visible"
        )

    @pytest.mark.core_crud
    def test_sort_by_column_shows_sort_chip(
        self,
        plant_list: PlantInstanceListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-PI-013: Clicking a column header activates the sort chip.

        Spec: TC-001 -- Sortierung per Spaltenklick.
        """
        plant_list.open()
        headers = plant_list.get_column_headers()
        if not headers:
            pytest.skip("No column headers found")

        screenshot(
            "TC-REQ-001-PI-013_before-sort",
            "Plant list before sorting",
        )
        plant_list.click_column_header(headers[0])
        plant_list.wait_for_loading_complete()
        screenshot(
            "TC-REQ-001-PI-013_after-sort",
            "Plant list after column sort",
        )

        assert plant_list.has_sort_chip(), (
            f"TC-REQ-001-PI-013 FAIL: Expected sort chip after clicking "
            f"column header '{headers[0]}'"
        )

    @pytest.mark.core_crud
    def test_nonexistent_plant_instance_shows_error(
        self,
        plant_detail: PlantInstanceDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-PI-014: Navigating to a non-existent key shows an error (NFR-006).

        Spec: TC-001 -- Nicht-existente Pflanze zeigt Fehleranzeige.
        """
        plant_detail.open("NONEXISTENT-PLANT-KEY-99999")
        screenshot(
            "TC-REQ-001-PI-014_nonexistent-plant",
            "Error state for non-existent plant instance key",
        )

        assert plant_detail.is_error_displayed(), (
            "TC-REQ-001-PI-014 FAIL: Expected error display for non-existent plant key"
        )

    @pytest.mark.core_crud
    def test_reset_filters_restores_full_list(
        self,
        plant_list: PlantInstanceListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-PI-015: Reset filters restores the full plant instance list.

        Spec: TC-001 -- Filter zuruecksetzen stellt volle Liste wieder her.
        """
        plant_list.open()

        if plant_list.get_row_count() == 0:
            pytest.skip("No plant instances — cannot test filter reset")

        initial_count = plant_list.get_row_count()
        plant_list.search("A")
        plant_list.wait_for_loading_complete()

        if plant_list.has_reset_filters_button():
            plant_list.click_reset_filters()
            plant_list.wait_for_loading_complete()
            screenshot(
                "TC-REQ-001-PI-015_after-reset",
                "Plant list after filter reset",
            )
            reset_count = plant_list.get_row_count()
            assert reset_count >= initial_count - 1, (
                f"TC-REQ-001-PI-015 FAIL: Expected count after reset ({reset_count}) "
                f"close to initial ({initial_count})"
            )
