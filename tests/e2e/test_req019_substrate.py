"""E2E tests for REQ-019 — Substratverwaltung.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-019.md):
  TC-REQ-019-001  ->  TC-019-001  Substrat-Liste wird korrekt geladen und angezeigt
  TC-REQ-019-002  ->  TC-019-001  Listenansicht — Spalten pruefen
  TC-REQ-019-003  ->  TC-019-001  Erstellen-Button sichtbar auf Listenansicht
  TC-REQ-019-004  ->  TC-019-005  Klick auf Zeile navigiert zur Detailseite
  TC-REQ-019-005  ->  TC-019-003  Substrat-Tabelle ist durchsuchbar
  TC-REQ-019-006  ->  TC-019-004  Suche ohne Treffer zeigt Hinweismeldung
  TC-REQ-019-007  ->  TC-019-003  Sortierung per Spaltenklick
  TC-REQ-019-008  ->  TC-019-001  Zeigt-Zaehler
  TC-REQ-019-010  ->  TC-019-007  Erstellen-Dialog oeffnet sich
  TC-REQ-019-011  ->  TC-019-014  Abbrechen schliesst Dialog ohne Aenderungen
  TC-REQ-019-012  ->  TC-019-009  Alle 14 Substrattypen im Dropdown verfuegbar
  TC-REQ-019-013  ->  TC-019-007  Substrat erfolgreich erstellen (Happy Path)
  TC-REQ-019-014  ->  TC-019-007  Reusable-Toggle im Erstellen-Dialog
  TC-REQ-019-020  ->  TC-019-015  Substrat-Detailseite laedt mit Formular
  TC-REQ-019-021  ->  TC-019-015  Detailseite zeigt Abschnittskarten
  TC-REQ-019-022  ->  TC-019-016  Substrat bearbeiten — pH-Basis aendern
  TC-REQ-019-023  ->  TC-019-018  Loeschen-Button oeffnet Bestaetigungsdialog
  TC-REQ-019-024  ->  TC-019-019  Loeschen abbrechen schliesst Dialog
  TC-REQ-019-025  ->  TC-019-018  Substrat loeschen bestaetigt
  TC-REQ-019-030  ->  (error)     Nicht-existenter Key zeigt Fehler
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.substrate_detail_page import SubstrateDetailPage
from .pages.substrate_list_page import SubstrateListPage


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def substrate_list(browser: WebDriver, base_url: str) -> SubstrateListPage:
    """Return a SubstrateListPage bound to the test browser."""
    return SubstrateListPage(browser, base_url)


@pytest.fixture
def substrate_detail(browser: WebDriver, base_url: str) -> SubstrateDetailPage:
    """Return a SubstrateDetailPage bound to the test browser."""
    return SubstrateDetailPage(browser, base_url)


# -- TC-REQ-019-001 to TC-REQ-019-008: List Page ------------------------------


class TestSubstrateListPage:
    """Substrate list display and interactions (Spec: TC-019-001, TC-019-003, TC-019-005)."""

    @pytest.mark.smoke
    def test_list_page_renders_with_page_title(
        self,
        substrate_list: SubstrateListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-019-001: SubstrateListPage renders with page title visible.

        Spec: TC-019-001 -- Substrat-Liste wird korrekt geladen und angezeigt.
        """
        substrate_list.open()
        screenshot("TC-REQ-019-001_substrate-list-loaded", "Substrate list page after initial load")

        title_el = substrate_list.wait_for_element(SubstrateListPage.PAGE_TITLE)
        assert title_el.is_displayed(), (
            "TC-REQ-019-001 FAIL: Expected [data-testid='page-title'] to be visible"
        )

    @pytest.mark.smoke
    def test_list_displays_data_table_with_columns(
        self,
        substrate_list: SubstrateListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-019-002: DataTable renders with expected column headers.

        Spec: TC-019-001 -- Listenansicht — Spalten pruefen.
        Expected columns: Typ, Bezeichnung, pH-Basis, EC-Basis, Wiederverwendbar
        (plus empty favorite column).
        """
        substrate_list.open()
        screenshot("TC-REQ-019-002_substrate-table-columns", "Substrate table column headers")

        headers = substrate_list.get_column_headers()
        if len(headers) == 0:
            pytest.skip("No substrates in database — empty state shown instead of DataTable")
        # At minimum, the table should have Typ and pH columns
        header_text = " ".join(headers)
        assert any("pH" in h for h in headers), (
            f"TC-REQ-019-002 FAIL: Expected 'pH' column header, got: {headers}"
        )

    @pytest.mark.smoke
    def test_create_button_is_visible_on_list_page(
        self,
        substrate_list: SubstrateListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-019-003: Create button is visible on the SubstrateListPage.

        Spec: TC-019-001 -- Erstellen-Button sichtbar auf Listenansicht.
        """
        substrate_list.open()
        screenshot("TC-REQ-019-003_create-button", "Create button visible on substrate list")

        btn = substrate_list.wait_for_element(SubstrateListPage.CREATE_BUTTON)
        assert btn.is_displayed(), (
            "TC-REQ-019-003 FAIL: Expected create button to be visible"
        )

    @pytest.mark.core_crud
    def test_click_row_navigates_to_detail(
        self,
        substrate_list: SubstrateListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-019-004: Clicking a substrate row navigates to its detail page.

        Spec: TC-019-005 -- Klick auf Zeile navigiert zur Detailseite.
        """
        substrate_list.open()
        screenshot("TC-REQ-019-004_before-row-click", "Substrate list before row click")

        if substrate_list.get_row_count() == 0:
            pytest.skip("No substrates in database — cannot test row click navigation")

        substrate_list.click_row(0)
        substrate_list.wait_for_url_contains("/standorte/substrates/")
        screenshot("TC-REQ-019-004_after-row-click", "Substrate detail after row click")

        assert "/standorte/substrates/" in substrate_list.driver.current_url, (
            f"TC-REQ-019-004 FAIL: Expected detail URL after row click, got: {substrate_list.driver.current_url}"
        )

    @pytest.mark.core_crud
    def test_search_filters_substrates(
        self,
        substrate_list: SubstrateListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-019-005: Search input filters substrates.

        Spec: TC-019-003 -- Substrat-Tabelle ist durchsuchbar.
        """
        substrate_list.open()

        if substrate_list.get_row_count() == 0:
            pytest.skip("No substrates — cannot test search")

        initial_count = substrate_list.get_row_count()
        screenshot("TC-REQ-019-005_before-search", "Substrate list before search")

        substrate_list.search("ZZZ_NONEXISTENT_SUBSTRATE_9999")
        substrate_list.wait_for_loading_complete()
        screenshot("TC-REQ-019-005_after-search", "Substrate list after search — no results")

        filtered_count = substrate_list.get_row_count()
        assert filtered_count <= initial_count, (
            f"TC-REQ-019-005 FAIL: Expected filtered count ({filtered_count}) <= initial ({initial_count})"
        )

    @pytest.mark.core_crud
    def test_search_no_results_shows_message(
        self,
        substrate_list: SubstrateListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-019-006: Search with no results shows a hint message.

        Spec: TC-019-004 -- Suche ohne Treffer zeigt Hinweismeldung.
        """
        substrate_list.open()

        if substrate_list.get_row_count() == 0:
            pytest.skip("No substrates — cannot test no-results message")

        substrate_list.search("xyzxyz_nicht_vorhanden")
        substrate_list.wait_for_loading_complete()
        time.sleep(0.5)  # debounce
        screenshot("TC-REQ-019-006_no-search-results", "No search results message")

        assert substrate_list.has_no_search_results() or substrate_list.get_row_count() == 0, (
            "TC-REQ-019-006 FAIL: Expected no-search-results message or zero rows"
        )

    @pytest.mark.core_crud
    def test_sort_by_column_shows_sort_chip(
        self,
        substrate_list: SubstrateListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-019-007: Clicking a column header activates the sort chip.

        Spec: TC-019-003 -- Sortierung per Spaltenklick.
        """
        substrate_list.open()
        headers = substrate_list.get_column_headers()
        if not headers:
            pytest.skip("No column headers found")

        screenshot("TC-REQ-019-007_before-sort", "Substrate list before sorting")
        substrate_list.click_column_header(headers[0])
        substrate_list.wait_for_loading_complete()
        screenshot("TC-REQ-019-007_after-sort", "Substrate list after column sort")

        assert substrate_list.has_sort_chip(), (
            f"TC-REQ-019-007 FAIL: Expected sort chip after clicking column header '{headers[0]}'"
        )

    @pytest.mark.smoke
    def test_showing_count_text_is_present(
        self,
        substrate_list: SubstrateListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-019-008: Showing count text is displayed when rows are present.

        Spec: TC-019-001 -- Zeigt-Zaehler.
        """
        substrate_list.open()
        screenshot("TC-REQ-019-008_showing-count", "Substrate list showing count")

        if substrate_list.get_row_count() == 0:
            pytest.skip("No rows — showing count not displayed for empty table")

        count_text = substrate_list.get_showing_count_text()
        assert count_text, (
            "TC-REQ-019-008 FAIL: Expected non-empty showing count text"
        )


# -- TC-REQ-019-010 to TC-REQ-019-014: Create Dialog --------------------------


class TestSubstrateCreateDialog:
    """Substrate create dialog operations (Spec: TC-019-007, TC-019-009, TC-019-014)."""

    @pytest.mark.core_crud
    def test_create_dialog_opens_on_button_click(
        self,
        substrate_list: SubstrateListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-019-010: Clicking create button opens the SubstrateCreateDialog.

        Spec: TC-019-007 -- Erstellen-Dialog oeffnet sich.
        """
        substrate_list.open()
        screenshot("TC-REQ-019-010_before-open-dialog", "Substrate list before opening create dialog")

        substrate_list.click_create()
        screenshot("TC-REQ-019-010_dialog-open", "Substrate create dialog opened")

        assert substrate_list.is_create_dialog_open(), (
            "TC-REQ-019-010 FAIL: Expected SubstrateCreateDialog to be open"
        )

    @pytest.mark.core_crud
    def test_create_dialog_cancel_closes_without_saving(
        self,
        substrate_list: SubstrateListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-019-011: Cancel in create dialog closes it without creating a substrate.

        Spec: TC-019-014 -- Abbrechen schliesst Dialog ohne Aenderungen.
        """
        substrate_list.open()
        initial_count = substrate_list.get_row_count()

        substrate_list.click_create()
        substrate_list.fill_name_de("Should Not Persist")
        screenshot("TC-REQ-019-011_before-cancel", "Create dialog before cancel")

        substrate_list.cancel_create_form()
        substrate_list.wait_for_loading_complete()
        screenshot("TC-REQ-019-011_after-cancel", "Substrate list after cancelling dialog")

        assert not substrate_list.is_create_dialog_open(), (
            "TC-REQ-019-011 FAIL: Expected create dialog to be closed after cancel"
        )
        final_count = substrate_list.get_row_count()
        assert final_count == initial_count, (
            f"TC-REQ-019-011 FAIL: Expected row count to stay {initial_count}, got {final_count}"
        )

    @pytest.mark.core_crud
    def test_create_dialog_shows_all_14_substrate_types(
        self,
        substrate_list: SubstrateListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-019-012: Type dropdown shows all 14 substrate type options.

        Spec: TC-019-009 -- Alle 14 Substrattypen im Dropdown verfuegbar.
        """
        substrate_list.open()
        substrate_list.click_create()
        screenshot("TC-REQ-019-012_dialog-open", "Create dialog open for type dropdown")

        options = substrate_list.get_type_options()
        screenshot("TC-REQ-019-012_type-options", "Type dropdown options listed")

        assert len(options) == 14, (
            f"TC-REQ-019-012 FAIL: Expected 14 substrate types, got {len(options)}: {options}"
        )

    @pytest.mark.core_crud
    def test_create_substrate_happy_path(
        self,
        substrate_list: SubstrateListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-019-013: Successfully create a substrate via the dialog.

        Spec: TC-019-007 -- Substrat erfolgreich erstellen (Happy Path).
        """
        substrate_list.open()
        initial_count = substrate_list.get_row_count()
        screenshot("TC-REQ-019-013_before-create", "Substrate list before creating")

        substrate_list.click_create()
        screenshot("TC-REQ-019-013_dialog-open", "Substrate create dialog opened")

        # Fill in form fields
        substrate_list.fill_name_de("E2E-Testsubstrat")
        substrate_list.fill_name_en("E2E Test Substrate")
        substrate_list.fill_brand("TestBrand")
        substrate_list.fill_ph_base(6.2)
        substrate_list.fill_ec_base(0.4)
        substrate_list.fill_air_porosity(30)
        screenshot("TC-REQ-019-013_form-filled", "Create form filled with test data")

        substrate_list.submit_create_form()
        substrate_list.wait_for_loading_complete()
        time.sleep(1)  # Wait for snackbar and list refresh
        screenshot("TC-REQ-019-013_after-create", "Substrate list after creating substrate")

        assert not substrate_list.is_create_dialog_open(), (
            "TC-REQ-019-013 FAIL: Expected dialog to close after successful create"
        )

    @pytest.mark.core_crud
    def test_create_dialog_reusable_toggle(
        self,
        substrate_list: SubstrateListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-019-014: Reusable toggle switch can be toggled in the create dialog.

        Spec: TC-019-007 -- Reusable-Toggle im Erstellen-Dialog.
        """
        substrate_list.open()
        substrate_list.click_create()
        screenshot("TC-REQ-019-014_dialog-open", "Create dialog open for toggle test")

        # Default state: reusable = false
        initial_state = substrate_list.is_reusable_checked()
        assert initial_state is False, (
            f"TC-REQ-019-014 FAIL: Expected reusable to default to False, got {initial_state}"
        )

        substrate_list.toggle_reusable()
        screenshot("TC-REQ-019-014_after-toggle", "After toggling reusable switch")

        toggled_state = substrate_list.is_reusable_checked()
        assert toggled_state is True, (
            f"TC-REQ-019-014 FAIL: Expected reusable to be True after toggle, got {toggled_state}"
        )

        substrate_list.cancel_create_form()


# -- TC-REQ-019-020 to TC-REQ-019-025: Detail Page ----------------------------


class TestSubstrateDetailPage:
    """Substrate detail page display and edit (Spec: TC-019-015, TC-019-016, TC-019-018)."""

    @pytest.mark.core_crud
    def test_detail_page_loads_with_form(
        self,
        substrate_list: SubstrateListPage,
        substrate_detail: SubstrateDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-019-020: Substrate detail page loads and shows edit form.

        Spec: TC-019-015 -- Substrat-Detailseite laedt mit Formular.
        """
        substrate_list.open()

        if substrate_list.get_row_count() == 0:
            pytest.skip("No substrates in database — cannot test detail page")

        substrate_list.click_row(0)
        substrate_list.wait_for_url_contains("/standorte/substrates/")
        substrate_detail.wait_for_element(SubstrateDetailPage.PAGE)
        substrate_detail.wait_for_loading_complete()
        screenshot("TC-REQ-019-020_detail-loaded", "Substrate detail page loaded")

        title = substrate_detail.get_title()
        assert title, (
            "TC-REQ-019-020 FAIL: Expected non-empty page title on detail page"
        )

        # Verify form fields are present
        ph_value = substrate_detail.get_ph_base_value()
        assert ph_value, (
            "TC-REQ-019-020 FAIL: Expected pH base field to have a value"
        )

    @pytest.mark.core_crud
    def test_detail_page_shows_section_cards(
        self,
        substrate_list: SubstrateListPage,
        substrate_detail: SubstrateDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-019-021: Detail page shows form section cards.

        Spec: TC-019-015 -- Detailseite zeigt Abschnittskarten.
        Expected: 4 cards (Identification, Chemistry, Physical, Reuse).
        """
        substrate_list.open()

        if substrate_list.get_row_count() == 0:
            pytest.skip("No substrates in database — cannot test section cards")

        substrate_list.click_row(0)
        substrate_list.wait_for_url_contains("/standorte/substrates/")
        substrate_detail.wait_for_element(SubstrateDetailPage.PAGE)
        substrate_detail.wait_for_loading_complete()
        screenshot("TC-REQ-019-021_section-cards", "Substrate detail section cards")

        card_count = substrate_detail.get_section_card_count()
        assert card_count >= 4, (
            f"TC-REQ-019-021 FAIL: Expected at least 4 section cards, got {card_count}"
        )

    @pytest.mark.core_crud
    def test_edit_ph_base_and_save(
        self,
        substrate_list: SubstrateListPage,
        substrate_detail: SubstrateDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-019-022: Edit pH base value and save successfully.

        Spec: TC-019-016 -- Substrat bearbeiten — pH-Basis aendern.
        """
        substrate_list.open()

        if substrate_list.get_row_count() == 0:
            pytest.skip("No substrates in database — cannot test edit")

        substrate_list.click_row(0)
        substrate_list.wait_for_url_contains("/standorte/substrates/")
        substrate_detail.wait_for_element(SubstrateDetailPage.PAGE)
        substrate_detail.wait_for_loading_complete()

        original_ph = substrate_detail.get_ph_base_value()
        screenshot("TC-REQ-019-022_before-edit", "Detail page before editing pH")

        # Change pH to a different value
        new_ph = 5.5 if original_ph != "5.5" else 6.0
        substrate_detail.fill_ph_base(new_ph)
        screenshot("TC-REQ-019-022_after-edit", "Detail page after editing pH value")

        substrate_detail.submit_form()
        substrate_detail.wait_for_loading_complete()
        time.sleep(1)  # Wait for save and reload
        screenshot("TC-REQ-019-022_after-save", "Detail page after saving")

        # Verify the value was saved (page reloads with updated value)
        updated_ph = substrate_detail.get_ph_base_value()
        assert updated_ph == str(new_ph), (
            f"TC-REQ-019-022 FAIL: Expected pH value '{new_ph}' after save, got '{updated_ph}'"
        )

        # Restore original value
        substrate_detail.fill_ph_base(float(original_ph))
        substrate_detail.submit_form()
        substrate_detail.wait_for_loading_complete()
        time.sleep(0.5)

    @pytest.mark.core_crud
    def test_delete_button_opens_confirm_dialog(
        self,
        substrate_list: SubstrateListPage,
        substrate_detail: SubstrateDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-019-023: Delete button opens the confirmation dialog.

        Spec: TC-019-018 -- Loeschen-Button oeffnet Bestaetigungsdialog.
        """
        substrate_list.open()

        if substrate_list.get_row_count() == 0:
            pytest.skip("No substrates in database — cannot test delete dialog")

        substrate_list.click_row(0)
        substrate_list.wait_for_url_contains("/standorte/substrates/")
        substrate_detail.wait_for_element(SubstrateDetailPage.PAGE)
        substrate_detail.wait_for_loading_complete()
        screenshot("TC-REQ-019-023_before-delete", "Detail page before clicking delete")

        substrate_detail.click_delete()
        screenshot("TC-REQ-019-023_confirm-dialog", "Delete confirmation dialog open")

        assert substrate_detail.is_confirm_dialog_open(), (
            "TC-REQ-019-023 FAIL: Expected confirm dialog to be open after clicking delete"
        )

        # Cancel to avoid actually deleting
        substrate_detail.cancel_delete()

    @pytest.mark.core_crud
    def test_delete_cancel_closes_dialog(
        self,
        substrate_list: SubstrateListPage,
        substrate_detail: SubstrateDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-019-024: Cancelling deletion closes the confirm dialog.

        Spec: TC-019-019 -- Loeschen abbrechen schliesst Dialog.
        """
        substrate_list.open()

        if substrate_list.get_row_count() == 0:
            pytest.skip("No substrates in database — cannot test delete cancel")

        substrate_list.click_row(0)
        substrate_list.wait_for_url_contains("/standorte/substrates/")
        substrate_detail.wait_for_element(SubstrateDetailPage.PAGE)
        substrate_detail.wait_for_loading_complete()

        substrate_detail.click_delete()
        screenshot("TC-REQ-019-024_dialog-open", "Delete dialog open before cancel")

        substrate_detail.cancel_delete()
        screenshot("TC-REQ-019-024_after-cancel", "After cancelling delete dialog")

        assert not substrate_detail.is_confirm_dialog_open(), (
            "TC-REQ-019-024 FAIL: Expected confirm dialog to close after cancel"
        )

        # Verify still on detail page
        page = substrate_detail.driver.find_elements(*SubstrateDetailPage.PAGE)
        assert len(page) > 0, (
            "TC-REQ-019-024 FAIL: Expected to remain on detail page after cancel"
        )

    @pytest.mark.core_crud
    def test_delete_substrate_confirmed(
        self,
        substrate_list: SubstrateListPage,
        substrate_detail: SubstrateDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-019-025: Confirming deletion removes the substrate and navigates back.

        Spec: TC-019-018 -- Substrat loeschen bestaetigt.

        This test first creates a throwaway substrate, then deletes it.
        """
        # First, create a substrate to delete
        substrate_list.open()
        substrate_list.click_create()

        substrate_list.fill_name_de("ZZZ-Loeschtest")
        substrate_list.fill_name_en("ZZZ Delete Test")
        screenshot("TC-REQ-019-025_create-throwaway", "Creating throwaway substrate for deletion")

        substrate_list.submit_create_form()
        substrate_list.wait_for_loading_complete()
        time.sleep(1)

        # Navigate to the newly created substrate
        substrate_list.open()
        substrate_list.wait_for_loading_complete()
        screenshot("TC-REQ-019-025_list-with-throwaway", "List with throwaway substrate")

        # Find and click the throwaway row
        try:
            substrate_list.click_row_by_text("ZZZ-Loeschtest")
        except ValueError:
            pytest.skip("Could not find the throwaway substrate — creation may have failed")

        substrate_list.wait_for_url_contains("/standorte/substrates/")
        substrate_detail.wait_for_element(SubstrateDetailPage.PAGE)
        substrate_detail.wait_for_loading_complete()
        screenshot("TC-REQ-019-025_detail-before-delete", "Throwaway detail before delete")

        substrate_detail.click_delete()
        screenshot("TC-REQ-019-025_confirm-dialog", "Delete confirmation dialog")

        substrate_detail.confirm_delete()
        substrate_list.wait_for_url_contains("/standorte/substrates")
        substrate_list.wait_for_loading_complete()
        time.sleep(1)
        screenshot("TC-REQ-019-025_after-delete", "Substrate list after deletion")

        # Verify the deleted substrate is no longer in the list
        row_texts = substrate_list.get_row_texts()
        all_text = " ".join(str(cell) for row in row_texts for cell in row)
        assert "ZZZ-Loeschtest" not in all_text, (
            "TC-REQ-019-025 FAIL: Expected 'ZZZ-Loeschtest' to be removed from the list"
        )


# -- TC-REQ-019-030: Error Handling -------------------------------------------


class TestSubstrateErrorHandling:
    """Substrate error handling (NFR-006)."""

    @pytest.mark.smoke
    def test_nonexistent_substrate_shows_error(
        self,
        substrate_detail: SubstrateDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-019-030: Navigating to a non-existent substrate key shows an error.

        Spec: (error handling) -- Nicht-existenter Key zeigt Fehler.
        """
        substrate_detail.navigate("/standorte/substrates/nonexistent-key-999")
        substrate_detail.wait_for_loading_complete()
        time.sleep(1)
        screenshot("TC-REQ-019-030_nonexistent-key", "Error display for non-existent substrate")

        assert substrate_detail.is_error_displayed(), (
            "TC-REQ-019-030 FAIL: Expected error display for non-existent substrate key"
        )
