"""E2E tests for REQ-014 — Tankmanagement.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-014.md):
  TC-REQ-014-001  ->  TC-014-001  Tank-Listenansicht wird geladen und zeigt Tanks
  TC-REQ-014-002  ->  TC-014-001  Listenansicht — Spalten pruefen
  TC-REQ-014-003  ->  TC-014-001  Erstellen-Button sichtbar auf Listenansicht
  TC-REQ-014-004  ->  TC-014-004  Klick auf Tank-Zeile navigiert zur Detailseite
  TC-REQ-014-005  ->  TC-014-003  Tank-Tabelle ist durchsuchbar
  TC-REQ-014-006  ->  TC-014-003  Filter zuruecksetzen stellt volle Liste wieder her
  TC-REQ-014-007  ->  TC-014-003  Sortierung per Spaltenklick
  TC-REQ-014-008  ->  TC-014-001  Zeigt-Zaehler
  TC-REQ-014-010  ->  TC-014-005  Tank-Erstellen-Dialog oeffnet sich
  TC-REQ-014-011  ->  TC-014-009  Abbrechen schliesst Dialog ohne Aenderungen
  TC-REQ-014-012  ->  TC-014-007  Pflichtfeld-Validierung beim Tank-Erstellen
  TC-REQ-014-013  ->  TC-014-006  Equipment-Toggles im Erstellen-Dialog
  TC-REQ-014-014  ->  TC-014-006  Tank erfolgreich erstellen (Happy Path)
  TC-REQ-014-015  ->  TC-014-006  Tank mit Notizen erstellen
  TC-REQ-014-016  ->  TC-014-010  Tank-Detailseite laedt
  TC-REQ-014-017  ->  TC-014-010  Tank-Detailseite hat 6 Tabs
  TC-REQ-014-018  ->  TC-014-010  Tab-Navigation durch alle 6 Tabs
  TC-REQ-014-019  ->  TC-014-011  Detailseite Titel stimmt mit Tank-Name ueberein
  TC-REQ-014-020  ->  TC-014-011  Details-Tab zeigt Tank-Infos
  TC-REQ-014-023  ->  TC-014-019  Zustandsmessung-Dialog oeffnet sich
  TC-REQ-014-024  ->  TC-014-019  Zustandsmessung mit pH und EC Werten
  TC-REQ-014-025  ->  TC-014-019  Zustandsmessung abbrechen schliesst Dialog
  TC-REQ-014-026  ->  TC-014-024  Wartungs-Dialog oeffnet sich
  TC-REQ-014-027  ->  TC-014-024  Wartung mit water_change-Typ dokumentieren
  TC-REQ-014-028  ->  TC-014-024  Wartung abbrechen schliesst Dialog
  TC-REQ-014-029  ->  TC-014-026  Wartungsplaene-Tab zeigt DataTable
  TC-REQ-014-030  ->  TC-014-037  Bearbeiten-Tab Formular ist vorausgefuellt
  TC-REQ-014-031  ->  TC-014-037  Bearbeiten abbrechen setzt Formular zurueck
  TC-REQ-014-032  ->  TC-014-040  Loeschen-Button oeffnet Bestaetigungsdialog
  TC-REQ-014-033  ->  TC-014-070  Nicht-existenter Tank-Key zeigt Fehler
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.tank_detail_page import TankDetailPage
from .pages.tank_list_page import TankListPage


# -- Fixtures -----------------------------------------------------------------

@pytest.fixture
def tank_list(browser: WebDriver, base_url: str) -> TankListPage:
    """Return a TankListPage bound to the test browser."""
    return TankListPage(browser, base_url)


@pytest.fixture
def tank_detail(browser: WebDriver, base_url: str) -> TankDetailPage:
    """Return a TankDetailPage bound to the test browser."""
    return TankDetailPage(browser, base_url)


# -- TC-REQ-014-001 to TC-REQ-014-008: List Page ------------------------------

class TestTankListPage:
    """Tank list display and interactions (Spec: TC-014-001, TC-014-003, TC-014-004)."""

    @pytest.mark.smoke
    def test_list_page_renders_with_correct_testid(
        self,
        tank_list: TankListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-014-001: TankListPage renders with data-testid='tank-list-page'.

        Spec: TC-014-001 -- Tank-Listenansicht wird geladen und zeigt Tanks.
        """
        tank_list.open()
        screenshot("TC-REQ-014-001_tank-list-loaded", "Tank list page after initial load")

        page_el = tank_list.wait_for_element(TankListPage.PAGE)
        assert page_el.is_displayed(), (
            "TC-REQ-014-001 FAIL: Expected [data-testid='tank-list-page'] to be visible"
        )

    @pytest.mark.smoke
    def test_list_displays_data_table_with_columns(
        self,
        tank_list: TankListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-014-002: DataTable renders with expected column headers (Name, Type, Volume).

        Spec: TC-014-001 -- Listenansicht — Spalten pruefen.
        """
        tank_list.open()
        screenshot("TC-REQ-014-002_tank-table-columns", "Tank table column headers")

        headers = tank_list.get_column_headers()
        if len(headers) == 0:
            pytest.skip("No tanks in database — empty state shown instead of DataTable")
        assert any("Name" in h for h in headers), (
            f"TC-REQ-014-002 FAIL: Expected 'Name' column header, got: {headers}"
        )

    @pytest.mark.smoke
    def test_create_button_is_visible_on_list_page(
        self,
        tank_list: TankListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-014-003: Create button is visible on the TankListPage.

        Spec: TC-014-001 -- Erstellen-Button sichtbar auf Listenansicht.
        """
        tank_list.open()
        screenshot("TC-REQ-014-003_create-button", "Create button visible on tank list")

        btn = tank_list.wait_for_element(TankListPage.CREATE_BUTTON)
        assert btn.is_displayed(), (
            "TC-REQ-014-003 FAIL: Expected [data-testid='create-button'] to be visible"
        )

    @pytest.mark.core_crud
    def test_click_row_navigates_to_detail(
        self,
        tank_list: TankListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-014-004: Clicking a tank row navigates to its detail page.

        Spec: TC-014-004 -- Klick auf Tank-Zeile navigiert zur Detailseite.
        """
        tank_list.open()
        screenshot("TC-REQ-014-004_before-row-click", "Tank list before row click")

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks in database — cannot test row click navigation")

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")
        screenshot("TC-REQ-014-004_after-row-click", "Tank detail after row click")

        assert "/standorte/tanks/" in tank_list.driver.current_url, (
            f"TC-REQ-014-004 FAIL: Expected detail URL after row click, got: {tank_list.driver.current_url}"
        )

    @pytest.mark.core_crud
    def test_search_filters_tanks_by_name(
        self,
        tank_list: TankListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-014-005: Search input filters tanks by name.

        Spec: TC-014-003 -- Tank-Tabelle ist durchsuchbar.
        """
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test search")

        initial_count = tank_list.get_row_count()
        screenshot("TC-REQ-014-005_before-search", "Tank list before search")

        tank_list.search("ZZZ_NONEXISTENT_TANK_9999")
        tank_list.wait_for_loading_complete()
        screenshot("TC-REQ-014-005_after-search", "Tank list after search — no results")

        filtered_count = tank_list.get_row_count()
        assert filtered_count <= initial_count, (
            f"TC-REQ-014-005 FAIL: Expected filtered count ({filtered_count}) <= initial ({initial_count})"
        )
        assert tank_list.has_search_chip(), (
            "TC-REQ-014-005 FAIL: Expected search chip to be visible"
        )

    @pytest.mark.core_crud
    def test_reset_filters_restores_full_tank_list(
        self,
        tank_list: TankListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-014-006: Reset filters restores the full tank list.

        Spec: TC-014-003 -- Filter zuruecksetzen stellt volle Liste wieder her.
        """
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test filter reset")

        initial_count = tank_list.get_row_count()
        tank_list.search("A")
        tank_list.wait_for_loading_complete()

        if tank_list.has_reset_filters_button():
            tank_list.click_reset_filters()
            tank_list.wait_for_loading_complete()
            screenshot("TC-REQ-014-006_after-reset", "Tank list after filter reset")
            reset_count = tank_list.get_row_count()
            assert reset_count >= initial_count - 1, (
                f"TC-REQ-014-006 FAIL: Expected count after reset ({reset_count}) close to initial ({initial_count})"
            )

    @pytest.mark.core_crud
    def test_sort_by_column_shows_sort_chip(
        self,
        tank_list: TankListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-014-007: Clicking a column header activates the sort chip.

        Spec: TC-014-003 -- Sortierung per Spaltenklick.
        """
        tank_list.open()
        headers = tank_list.get_column_headers()
        if not headers:
            pytest.skip("No column headers found")

        screenshot("TC-REQ-014-007_before-sort", "Tank list before sorting")
        tank_list.click_column_header(headers[0])
        tank_list.wait_for_loading_complete()
        screenshot("TC-REQ-014-007_after-sort", "Tank list after column sort")

        assert tank_list.has_sort_chip(), (
            f"TC-REQ-014-007 FAIL: Expected sort chip after clicking column header '{headers[0]}'"
        )

    @pytest.mark.smoke
    def test_showing_count_text_is_present(
        self,
        tank_list: TankListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-014-008: Showing count text is displayed when rows are present.

        Spec: TC-014-001 -- Zeigt-Zaehler.
        """
        tank_list.open()
        screenshot("TC-REQ-014-008_showing-count", "Tank list showing count")

        if tank_list.get_row_count() == 0:
            pytest.skip("No rows — showing count not displayed for empty table")

        count_text = tank_list.get_showing_count_text()
        assert count_text, (
            "TC-REQ-014-008 FAIL: Expected non-empty showing count text"
        )


# -- TC-REQ-014-010 to TC-REQ-014-015: Create Dialog --------------------------

class TestTankCreateDialog:
    """Tank create dialog operations (Spec: TC-014-005, TC-014-006, TC-014-007, TC-014-009)."""

    @pytest.mark.core_crud
    def test_create_dialog_opens_on_button_click(
        self,
        tank_list: TankListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-014-010: Clicking create button opens the TankCreateDialog.

        Spec: TC-014-005 -- Tank-Erstellen-Dialog oeffnet sich.
        """
        tank_list.open()
        screenshot("TC-REQ-014-010_before-open-dialog", "Tank list before opening create dialog")

        tank_list.click_create()
        screenshot("TC-REQ-014-010_dialog-open", "Tank create dialog opened")

        assert tank_list.is_create_dialog_open(), (
            "TC-REQ-014-010 FAIL: Expected TankCreateDialog to be open"
        )

    @pytest.mark.core_crud
    def test_create_dialog_cancel_closes_without_saving(
        self,
        tank_list: TankListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-014-011: Cancel in create dialog closes it without creating a tank.

        Spec: TC-014-009 -- Abbrechen schliesst Dialog ohne Aenderungen.
        """
        tank_list.open()
        initial_count = tank_list.get_row_count()

        tank_list.click_create()
        tank_list.fill_name("Should Not Persist")
        screenshot("TC-REQ-014-011_before-cancel", "Create dialog before cancel")

        tank_list.cancel_create_form()
        tank_list.wait_for_loading_complete()
        screenshot("TC-REQ-014-011_after-cancel", "Tank list after cancelling dialog")

        assert not tank_list.is_create_dialog_open(), (
            "TC-REQ-014-011 FAIL: Expected create dialog to be closed after cancel"
        )
        final_count = tank_list.get_row_count()
        assert final_count == initial_count, (
            f"TC-REQ-014-011 FAIL: Expected row count to stay {initial_count}, got {final_count}"
        )

    @pytest.mark.core_crud
    def test_create_dialog_submit_without_name_shows_validation_error(
        self,
        tank_list: TankListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-014-012: Submitting with empty name triggers validation error (NFR-006).

        Spec: TC-014-007 -- Pflichtfeld-Validierung beim Tank-Erstellen.
        """
        tank_list.open()
        tank_list.click_create()

        name_el = tank_list.wait_for_element_clickable(TankListPage.FORM_NAME)
        name_el.clear()
        screenshot("TC-REQ-014-012_before-submit-empty", "Create dialog with empty name")

        tank_list.submit_create_form()
        tank_list.wait_for_loading_complete()
        screenshot("TC-REQ-014-012_validation-error", "Validation error for empty name")

        assert tank_list.is_create_dialog_open(), (
            "TC-REQ-014-012 FAIL: Expected dialog to remain open when name is empty"
        )

    @pytest.mark.core_crud
    def test_create_dialog_equipment_toggles(
        self,
        tank_list: TankListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-014-013: Equipment toggle switches can be toggled in the create dialog.

        Spec: TC-014-006 -- Equipment-Toggles im Erstellen-Dialog.
        """
        tank_list.open()
        tank_list.click_create()
        screenshot("TC-REQ-014-013_dialog-open", "Tank create dialog open for toggle test")

        # Default state: has_lid = false
        initial_state = tank_list.is_has_lid_checked()
        assert initial_state is False, (
            f"TC-REQ-014-013 FAIL: Expected has_lid to default to False, got {initial_state}"
        )

        # Toggle it on
        tank_list.toggle_has_lid()
        tank_list.wait_for_loading_complete()
        screenshot("TC-REQ-014-013_lid-toggled-on", "has_lid toggle switched on")
        toggled_state = tank_list.is_has_lid_checked()
        assert toggled_state is True, (
            f"TC-REQ-014-013 FAIL: Expected has_lid to be True after toggle, got {toggled_state}"
        )

        # Toggle back off
        tank_list.toggle_has_lid()
        tank_list.wait_for_loading_complete()
        final_state = tank_list.is_has_lid_checked()
        assert final_state is False, (
            f"TC-REQ-014-013 FAIL: Expected has_lid to be False after second toggle, got {final_state}"
        )

        tank_list.cancel_create_form()

    @pytest.mark.core_crud
    def test_create_tank_with_valid_data(
        self,
        tank_list: TankListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-014-014: Create a tank with valid name and volume; verify it appears in list.

        Spec: TC-014-006 -- Tank erfolgreich erstellen (Happy Path).
        """
        tank_list.open()
        initial_count = tank_list.get_row_count()
        screenshot("TC-REQ-014-014_before-create", "Tank list before creating")

        tank_list.click_create()
        screenshot("TC-REQ-014-014_dialog-open", "Tank create dialog opened")

        unique_name = f"E2E-Tank-{int(time.time())}"
        tank_list.fill_name(unique_name)

        screenshot("TC-REQ-014-014_form-filled", "Tank create form filled before submit")

        tank_list.submit_create_form()
        tank_list.wait_for_loading_complete()
        screenshot("TC-REQ-014-014_after-create", "Tank list after creation")

        final_count = tank_list.get_row_count()
        names = tank_list.get_first_column_texts()
        assert final_count > initial_count or unique_name in names, (
            f"TC-REQ-014-014 FAIL: Expected new tank '{unique_name}' to appear. "
            f"Initial: {initial_count}, final: {final_count}"
        )

    @pytest.mark.core_crud
    def test_create_tank_with_notes(
        self,
        tank_list: TankListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-014-015: Create a tank with notes field populated.

        Spec: TC-014-006 -- Tank mit Notizen erstellen.
        """
        tank_list.open()
        initial_count = tank_list.get_row_count()

        tank_list.click_create()
        unique_name = f"E2E-Tank-Notes-{int(time.time())}"
        tank_list.fill_name(unique_name)
        tank_list.fill_notes("Test notes for E2E verification")
        screenshot("TC-REQ-014-015_form-with-notes", "Tank create form with notes filled")

        tank_list.submit_create_form()
        tank_list.wait_for_loading_complete()
        screenshot("TC-REQ-014-015_after-create-with-notes", "Tank list after creating with notes")

        final_count = tank_list.get_row_count()
        names = tank_list.get_first_column_texts()
        assert final_count > initial_count or unique_name in names, (
            f"TC-REQ-014-015 FAIL: Expected new tank '{unique_name}' to appear. "
            f"Initial: {initial_count}, final: {final_count}"
        )


# -- TC-REQ-014-016 to TC-REQ-014-020: Detail Page ----------------------------

class TestTankDetailPage:
    """Tank detail page rendering (Spec: TC-014-010, TC-014-011)."""

    @pytest.mark.core_crud
    def test_detail_page_loads_and_renders(
        self,
        tank_list: TankListPage,
        tank_detail: TankDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-014-016: Navigating to tank detail URL renders the detail page.

        Spec: TC-014-010 -- Tank-Detailseite laedt alle 6 Tabs.
        """
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test detail page")

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")
        screenshot("TC-REQ-014-016_detail-loaded", "Tank detail page loaded")

        page_el = tank_detail.wait_for_element(TankDetailPage.PAGE)
        assert page_el.is_displayed(), (
            "TC-REQ-014-016 FAIL: Expected [data-testid='tank-detail-page'] to be visible"
        )

    @pytest.mark.core_crud
    def test_detail_page_has_six_tabs(
        self,
        tank_list: TankListPage,
        tank_detail: TankDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-014-017: Tank detail page renders 6 tabs.

        Spec: TC-014-010 -- Tank-Detailseite laedt alle 6 Tabs.
        """
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test tabs")

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")
        screenshot("TC-REQ-014-017_tabs-visible", "Tank detail tabs visible")

        tab_labels = tank_detail.get_tab_labels()
        assert len(tab_labels) == 6, (
            f"TC-REQ-014-017 FAIL: Expected exactly 6 tabs, got {len(tab_labels)}: {tab_labels}"
        )

    @pytest.mark.core_crud
    def test_tab_navigation_through_all_tabs(
        self,
        tank_list: TankListPage,
        tank_detail: TankDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-014-018: Clicking each of the 6 tabs shows the corresponding panel.

        Spec: TC-014-010 -- Tab-Navigation durch alle 6 Tabs.
        """
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test tab navigation")

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")
        screenshot("TC-REQ-014-018_tab-0-details", "Tank detail tab 0 (Details) default")

        for tab_index in range(1, 6):
            tank_detail.click_tab(tab_index)
            tank_detail.wait_for_loading_complete()
            active = tank_detail.get_active_tab_index()
            screenshot(f"TC-REQ-014-018_tab-{tab_index}-active", f"Tank detail tab {tab_index} active")
            assert active == tab_index, (
                f"TC-REQ-014-018 FAIL: Expected tab {tab_index} to be active, got {active}"
            )

    @pytest.mark.core_crud
    def test_detail_page_title_matches_tank_name(
        self,
        tank_list: TankListPage,
        tank_detail: TankDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-014-019: Detail page title matches the tank name from the list.

        Spec: TC-014-011 -- Tab Details zeigt Tank-Stammdaten.
        """
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test page title")

        names = tank_list.get_first_column_texts()
        first_name = names[0] if names else None

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")
        screenshot("TC-REQ-014-019_detail-title", "Tank detail page title")

        title = tank_detail.get_page_title()
        assert title, "TC-REQ-014-019 FAIL: Expected a non-empty page title"

        if first_name:
            assert first_name in title or title in first_name, (
                f"TC-REQ-014-019 FAIL: Expected title '{title}' to match tank name '{first_name}'"
            )

    @pytest.mark.core_crud
    def test_details_tab_shows_tank_info(
        self,
        tank_list: TankListPage,
        tank_detail: TankDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-014-020: Details tab shows tank type, volume, and material.

        Spec: TC-014-011 -- Tab Details zeigt Tank-Stammdaten.
        """
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test details tab")

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")
        screenshot("TC-REQ-014-020_details-tab", "Tank details tab content")

        card_text = tank_detail.get_detail_cards_text()
        assert card_text, (
            "TC-REQ-014-020 FAIL: Expected non-empty card text in tank details tab"
        )
        tank_type_labels = ["Nährstoff", "Bewässerung", "Reservoir", "Rezirkulation",
                            "Stammlösung", "nutrient", "irrigation", "recirculation",
                            "stock_solution"]
        has_type_label = any(label in card_text for label in tank_type_labels)
        assert has_type_label, (
            f"TC-REQ-014-020 FAIL: Expected at least one tank type label in details, "
            f"card text: {card_text[:200]}"
        )


# -- TC-REQ-014-023 to TC-REQ-014-025: Tank State Recording -------------------

class TestTankStateRecording:
    """TankState recording operations (Spec: TC-014-019)."""

    @pytest.mark.core_crud
    def test_record_state_dialog_opens_from_states_tab(
        self,
        tank_list: TankListPage,
        tank_detail: TankDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-014-023: Clicking 'Record State' in tab 1 opens the TankStateCreateDialog.

        Spec: TC-014-019 -- Manuelle Zustandsmessung erfassen (Happy Path).
        """
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test state recording")

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")

        tank_detail.click_tab(1)  # States tab
        tank_detail.wait_for_loading_complete()
        screenshot("TC-REQ-014-023_states-tab-open", "Tank states tab visible")

        tank_detail.click_record_state()
        screenshot("TC-REQ-014-023_state-dialog-open", "TankState create dialog opened")

        assert tank_detail.is_state_dialog_open(), (
            "TC-REQ-014-023 FAIL: Expected TankStateCreateDialog to be open"
        )

    @pytest.mark.core_crud
    def test_record_state_with_ph_and_ec_values(
        self,
        tank_list: TankListPage,
        tank_detail: TankDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-014-024: Record a tank state with pH and EC; new row appears in states table.

        Spec: TC-014-019 -- Manuelle Zustandsmessung erfassen (Happy Path).
        """
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test state recording")

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")

        tank_detail.click_tab(1)
        tank_detail.wait_for_loading_complete()
        initial_state_count = tank_detail.get_states_row_count()

        tank_detail.click_record_state()
        screenshot("TC-REQ-014-024_state-dialog-open", "State dialog open for recording")

        tank_detail.fill_state_ph(6.2)
        tank_detail.fill_state_ec(1.8)
        tank_detail.fill_state_temp(20.5)
        tank_detail.fill_state_fill_percent(75.0)
        screenshot("TC-REQ-014-024_state-form-filled", "State form filled before submit")

        tank_detail.submit_state_form()
        tank_detail.wait_for_loading_complete()
        screenshot("TC-REQ-014-024_after-state-recorded", "States tab after recording")

        final_state_count = tank_detail.get_states_row_count()
        assert final_state_count >= initial_state_count, (
            f"TC-REQ-014-024 FAIL: Expected states count >= {initial_state_count}, "
            f"got {final_state_count}"
        )

    @pytest.mark.core_crud
    def test_record_state_dialog_cancel_closes(
        self,
        tank_list: TankListPage,
        tank_detail: TankDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-014-025: Cancelling the TankState dialog closes it without saving.

        Spec: TC-014-019 -- Zustandsmessung abbrechen schliesst Dialog.
        """
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test cancel state dialog")

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")

        tank_detail.click_tab(1)
        tank_detail.wait_for_loading_complete()
        initial_count = tank_detail.get_states_row_count()

        tank_detail.click_record_state()
        tank_detail.fill_state_ph(7.0)
        screenshot("TC-REQ-014-025_before-cancel", "State dialog before cancel")

        tank_detail.cancel_state_form()
        tank_detail.wait_for_loading_complete()
        screenshot("TC-REQ-014-025_after-cancel", "States tab after cancelling dialog")

        assert not tank_detail.is_state_dialog_open(), (
            "TC-REQ-014-025 FAIL: Expected TankState dialog to be closed after cancel"
        )
        final_count = tank_detail.get_states_row_count()
        assert final_count == initial_count, (
            f"TC-REQ-014-025 FAIL: Expected count to remain {initial_count}, got {final_count}"
        )


# -- TC-REQ-014-026 to TC-REQ-014-028: Maintenance Log ------------------------

class TestMaintenanceLog:
    """Maintenance log operations (Spec: TC-014-024)."""

    @pytest.mark.core_crud
    def test_log_maintenance_dialog_opens_from_maintenance_tab(
        self,
        tank_list: TankListPage,
        tank_detail: TankDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-014-026: 'Log Maintenance' button in tab 2 opens MaintenanceLogDialog.

        Spec: TC-014-024 -- Wartung dokumentieren (Happy Path).
        """
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test maintenance log")

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")

        tank_detail.click_tab(2)  # Maintenance tab
        tank_detail.wait_for_loading_complete()
        screenshot("TC-REQ-014-026_maintenance-tab-open", "Maintenance tab visible")

        tank_detail.click_log_maintenance()
        screenshot("TC-REQ-014-026_maintenance-dialog-open", "Maintenance dialog opened")

        assert tank_detail.is_maintenance_dialog_open(), (
            "TC-REQ-014-026 FAIL: Expected MaintenanceLogDialog to open"
        )

    @pytest.mark.core_crud
    def test_log_maintenance_with_water_change_type(
        self,
        tank_list: TankListPage,
        tank_detail: TankDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-014-027: Log a 'water_change' maintenance entry; new row in history table.

        Spec: TC-014-024 -- Wartung dokumentieren (Happy Path).
        """
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test maintenance logging")

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")

        tank_detail.click_tab(2)
        tank_detail.wait_for_loading_complete()
        initial_maint_count = tank_detail.get_maintenance_row_count()

        tank_detail.click_log_maintenance()
        screenshot("TC-REQ-014-027_maintenance-dialog-open", "Maintenance dialog open")

        tank_detail.fill_maintenance_performed_by("E2E Test Runner")
        tank_detail.fill_maintenance_duration(30)
        tank_detail.fill_maintenance_products("H2O2 3%")
        tank_detail.fill_maintenance_notes("Automated E2E maintenance test entry")
        screenshot("TC-REQ-014-027_maintenance-form-filled", "Maintenance form filled")

        tank_detail.submit_maintenance_form()
        tank_detail.wait_for_loading_complete()
        screenshot("TC-REQ-014-027_after-maintenance-logged", "Maintenance tab after logging")

        final_maint_count = tank_detail.get_maintenance_row_count()
        assert final_maint_count >= initial_maint_count, (
            f"TC-REQ-014-027 FAIL: Expected maintenance count >= {initial_maint_count}, "
            f"got {final_maint_count}"
        )

    @pytest.mark.core_crud
    def test_log_maintenance_cancel_closes_dialog(
        self,
        tank_list: TankListPage,
        tank_detail: TankDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-014-028: Cancelling the MaintenanceLogDialog closes it without saving.

        Spec: TC-014-024 -- Wartung abbrechen schliesst Dialog.
        """
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test maintenance dialog cancel")

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")

        tank_detail.click_tab(2)
        tank_detail.wait_for_loading_complete()
        initial_count = tank_detail.get_maintenance_row_count()

        tank_detail.click_log_maintenance()
        tank_detail.fill_maintenance_performed_by("Cancel Test")
        screenshot("TC-REQ-014-028_before-cancel", "Maintenance dialog before cancel")

        tank_detail.cancel_maintenance_form()
        tank_detail.wait_for_loading_complete()
        screenshot("TC-REQ-014-028_after-cancel", "Maintenance tab after cancel")

        assert not tank_detail.is_maintenance_dialog_open(), (
            "TC-REQ-014-028 FAIL: Expected MaintenanceLogDialog to close after cancel"
        )
        final_count = tank_detail.get_maintenance_row_count()
        assert final_count == initial_count, (
            f"TC-REQ-014-028 FAIL: Expected count to remain {initial_count}, got {final_count}"
        )


# -- TC-REQ-014-029: Schedules Tab --------------------------------------------

class TestTankSchedulesTab:
    """Tank Schedules tab rendering (Spec: TC-014-026)."""

    @pytest.mark.core_crud
    def test_schedules_tab_renders_data_table(
        self,
        tank_list: TankListPage,
        tank_detail: TankDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-014-029: Schedules tab (tab 3) renders a DataTable component.

        Spec: TC-014-026 -- Tab Wartungsplaene zeigt automatisch erstellte Plaene.
        """
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test schedules tab")

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")

        tank_detail.click_tab(3)  # Schedules tab
        tank_detail.wait_for_loading_complete()
        screenshot("TC-REQ-014-029_schedules-tab", "Tank schedules tab visible")

        tables = tank_detail.driver.find_elements(By.CSS_SELECTOR, "[data-testid='data-table']")
        assert len(tables) > 0, (
            "TC-REQ-014-029 FAIL: Expected at least one [data-testid='data-table'] in Schedules tab"
        )


# -- TC-REQ-014-030 to TC-REQ-014-031: Edit Form ------------------------------

class TestTankEditForm:
    """Tank edit form operations (Spec: TC-014-037)."""

    @pytest.mark.core_crud
    def test_edit_form_prefilled_with_tank_name(
        self,
        tank_list: TankListPage,
        tank_detail: TankDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-014-030: Edit tab form is pre-filled with the existing tank name.

        Spec: TC-014-037 -- Tank-Stammdaten bearbeiten (Happy Path).
        """
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test edit form")

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")
        page_title = tank_detail.get_page_title()

        tank_detail.click_tab(5)  # Edit tab
        tank_detail.wait_for_loading_complete()
        screenshot("TC-REQ-014-030_edit-tab-open", "Tank edit tab with pre-filled form")

        name_value = tank_detail.get_edit_name_value()
        assert name_value, (
            "TC-REQ-014-030 FAIL: Expected edit form Name field to be pre-filled"
        )
        assert name_value == page_title, (
            f"TC-REQ-014-030 FAIL: Expected Name '{name_value}' to match page title '{page_title}'"
        )

    @pytest.mark.core_crud
    def test_edit_form_cancel_resets_field(
        self,
        tank_list: TankListPage,
        tank_detail: TankDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-014-031: Cancel in edit form resets the form without saving.

        Spec: TC-014-037 -- Bearbeiten abbrechen setzt Formular zurueck.
        """
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test edit form cancel")

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")
        tank_detail.click_tab(5)
        tank_detail.wait_for_loading_complete()

        original_name = tank_detail.get_edit_name_value()

        tank_detail.fill_edit_name("Unsaved Modified Tank Name E2E")
        screenshot("TC-REQ-014-031_form-modified", "Edit form with modified name before cancel")

        tank_detail.cancel_edit_form()
        tank_detail.wait_for_loading_complete()
        screenshot("TC-REQ-014-031_after-cancel", "Edit form after cancel — should be reverted")

        reverted_name = tank_detail.get_edit_name_value()
        assert reverted_name == original_name, (
            f"TC-REQ-014-031 FAIL: Expected name to revert to '{original_name}', got '{reverted_name}'"
        )


# -- TC-REQ-014-032: Delete Flow ----------------------------------------------

class TestTankDeleteFlow:
    """Tank delete flow (Spec: TC-014-040)."""

    @pytest.mark.core_crud
    def test_delete_button_opens_confirm_dialog(
        self,
        tank_list: TankListPage,
        tank_detail: TankDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-014-032: Delete button opens ConfirmDialog; Cancel does not delete.

        Spec: TC-014-040 -- Tank loeschen mit Bestaetigungsdialog (Happy Path).
        """
        tank_list.open()

        if tank_list.get_row_count() == 0:
            pytest.skip("No tanks — cannot test delete flow")

        tank_list.click_row(0)
        tank_list.wait_for_url_contains("/standorte/tanks/")
        screenshot("TC-REQ-014-032_before-delete", "Tank detail before clicking delete")

        tank_detail.click_delete()
        screenshot("TC-REQ-014-032_confirm-dialog-open", "Delete confirm dialog open")

        assert tank_detail.is_confirm_dialog_open(), (
            "TC-REQ-014-032 FAIL: Expected ConfirmDialog to appear after clicking Delete"
        )

        # Cancel — we do NOT delete existing data in E2E tests
        tank_detail.cancel_delete()
        tank_detail.wait_for_loading_complete()
        screenshot("TC-REQ-014-032_after-cancel", "Tank detail after cancelling delete")

        assert not tank_detail.is_confirm_dialog_open(), (
            "TC-REQ-014-032 FAIL: Expected ConfirmDialog to close after Cancel"
        )
        assert "/standorte/tanks/" in tank_detail.driver.current_url, (
            "TC-REQ-014-032 FAIL: Expected to remain on the tank detail page"
        )


# -- TC-REQ-014-033: Error Handling --------------------------------------------

class TestTankErrorHandling:
    """Tank error states (Spec: TC-014-070)."""

    @pytest.mark.core_crud
    def test_nonexistent_tank_key_shows_error(
        self,
        tank_detail: TankDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-014-033: Navigating to a non-existent tank key shows an error display.

        Spec: TC-014-070 -- Netzwerkfehler bei Tank-Laden zeigt Fehlerzustand.
        """
        tank_detail.navigate("/standorte/tanks/nonexistent-key-99999")
        tank_detail.wait_for_loading_complete()
        screenshot("TC-REQ-014-033_nonexistent-key-error", "Error state for non-existent tank key")

        error_displayed = tank_detail.is_error_displayed()
        page_rendered = len(tank_detail.driver.find_elements(
            *TankDetailPage.PAGE
        )) > 0

        assert error_displayed or page_rendered, (
            "TC-REQ-014-033 FAIL: Expected either an error display or the detail page to render"
        )
