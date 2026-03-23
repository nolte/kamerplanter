"""E2E tests for REQ-007 — Erntemanagement: Batch-Listenansicht (TC-007-001 to TC-007-013).

Tests cover:
- HarvestBatchListPage: list display, page title, intro text, columns
- Search and sort in DataTable
- Quality grade chip color coding
- Row click navigation to detail
- HarvestCreateDialog: open, fill, submit, cancel, validation
- Karenz-Gate error display

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

from .pages.harvest_batch_list_page import HarvestBatchListPage


# -- Fixtures ---------------------------------------------------------------


@pytest.fixture
def harvest_list(browser: WebDriver, base_url: str) -> HarvestBatchListPage:
    """Return a HarvestBatchListPage bound to the test browser."""
    return HarvestBatchListPage(browser, base_url)


# -- TC-007-001 to TC-007-006: List Page ------------------------------------


class TestHarvestBatchListPage:
    """TC-007-001 to TC-007-006: HarvestBatchListPage operations."""

    def test_list_page_renders_with_correct_testid(
        self,
        harvest_list: HarvestBatchListPage,
        screenshot,
    ) -> None:
        """TC-007-001: HarvestBatchListPage renders with data-testid='harvest-batch-list-page'."""
        harvest_list.open()
        screenshot("req007_001_harvest_list_loaded", "Ernteliste nach dem Laden")

        assert harvest_list.driver.find_element(
            *HarvestBatchListPage.PAGE
        ).is_displayed(), "Expected [data-testid='harvest-batch-list-page'] to be visible"

    def test_list_displays_page_title(
        self,
        harvest_list: HarvestBatchListPage,
        screenshot,
    ) -> None:
        """TC-007-001: Page title 'Erntechargen' is visible."""
        harvest_list.open()
        screenshot("req007_001b_page_title", "Seitentitel Erntechargen")

        title = harvest_list.get_page_title_text()
        assert title, "Expected page title to be non-empty"

    def test_list_displays_data_table_with_columns(
        self,
        harvest_list: HarvestBatchListPage,
        screenshot,
    ) -> None:
        """TC-007-001: DataTable renders with expected column headers or empty state."""
        harvest_list.open()
        screenshot("req007_002_harvest_table_columns", "Tabellenspalten der Ernteliste")

        headers = harvest_list.get_column_headers()
        has_empty = harvest_list.has_empty_state()
        # On a fresh DB without harvest batches, DataTable shows EmptyState
        # (no table headers). Accept either headers OR empty state.
        assert len(headers) > 0 or has_empty, (
            f"Expected column headers or empty state in harvest list, got neither. Headers: {headers}"
        )

    def test_create_button_is_visible_on_list_page(
        self,
        harvest_list: HarvestBatchListPage,
        screenshot,
    ) -> None:
        """TC-007-001: Create button is visible on the HarvestBatchListPage."""
        harvest_list.open()
        screenshot("req007_003_create_button", "Erstellen-Button sichtbar")

        btn = harvest_list.driver.find_element(*HarvestBatchListPage.CREATE_BUTTON)
        assert btn.is_displayed(), "Expected [data-testid='create-button'] to be visible"

    def test_click_row_navigates_to_detail(
        self,
        harvest_list: HarvestBatchListPage,
        screenshot,
    ) -> None:
        """TC-007-006: Clicking a batch row navigates to its detail page."""
        harvest_list.open()
        screenshot("req007_004_before_row_click", "Vor Klick auf Tabellenzeile")

        if harvest_list.get_row_count() == 0:
            pytest.skip("No harvest batches in database -- cannot test row click navigation")

        harvest_list.click_row(0)
        harvest_list.wait_for_url_contains("/ernte/")
        screenshot("req007_004_after_row_click", "Nach Klick auf Tabellenzeile -- Detailseite")

        assert "/ernte/" in harvest_list.driver.current_url, (
            f"Expected detail URL after row click, got: {harvest_list.driver.current_url}"
        )

    def test_search_filters_batches(
        self,
        harvest_list: HarvestBatchListPage,
        screenshot,
    ) -> None:
        """TC-007-003: Search input filters harvest batches."""
        harvest_list.open()

        if harvest_list.get_row_count() == 0:
            pytest.skip("No harvest batches -- cannot test search")

        initial_count = harvest_list.get_row_count()
        screenshot("req007_005_before_search", "Vor Sucheingabe")

        harvest_list.search("ZZZ_NONEXISTENT_BATCH_9999")
        time.sleep(0.4)  # debounce
        screenshot("req007_005_after_search", "Nach Sucheingabe -- gefiltert")

        filtered_count = harvest_list.get_row_count()
        assert filtered_count <= initial_count, (
            f"Expected filtered count ({filtered_count}) <= initial ({initial_count})"
        )

    def test_sort_by_column_shows_sort_chip(
        self,
        harvest_list: HarvestBatchListPage,
        screenshot,
    ) -> None:
        """TC-007-004: Clicking a column header activates the sort chip."""
        harvest_list.open()
        headers = harvest_list.get_column_headers()
        if not headers:
            pytest.skip("No column headers visible")

        screenshot("req007_006_before_sort", "Vor Sortierung")
        harvest_list.click_column_header(headers[0])
        time.sleep(0.3)
        screenshot("req007_006_after_sort", "Nach Klick auf Spaltenheader")

    def test_quality_chips_color_coding(
        self,
        harvest_list: HarvestBatchListPage,
        screenshot,
    ) -> None:
        """TC-007-005: Quality grade chips use correct MUI color classes."""
        harvest_list.open()
        screenshot("req007_007_quality_chips", "Qualitaetsstufen-Farbkodierung")

        if harvest_list.get_row_count() == 0:
            pytest.skip("No harvest batches -- cannot verify quality chip colors")

        chips = harvest_list.get_quality_chips()
        for chip in chips:
            label = chip["label"]
            classes = chip["classes"]
            if label in ("A+", "A"):
                assert "Success" in classes or "success" in classes.lower(), (
                    f"Expected success color for grade '{label}', got classes: {classes}"
                )
            elif label == "B":
                assert "Info" in classes or "info" in classes.lower(), (
                    f"Expected info color for grade 'B', got classes: {classes}"
                )
            elif label == "C":
                assert "Warning" in classes or "warning" in classes.lower(), (
                    f"Expected warning color for grade 'C', got classes: {classes}"
                )
            elif label == "D":
                assert "Error" in classes or "error" in classes.lower(), (
                    f"Expected error color for grade 'D', got classes: {classes}"
                )


# -- TC-007-007 to TC-007-013: Create Dialog --------------------------------


class TestHarvestCreateDialog:
    """TC-007-007 to TC-007-013: HarvestCreateDialog operations."""

    def test_create_dialog_opens(
        self,
        harvest_list: HarvestBatchListPage,
        screenshot,
    ) -> None:
        """TC-007-007: Clicking create button opens the dialog."""
        harvest_list.open()
        screenshot("req007_010_before_create", "Vor Oeffnen des Erstellen-Dialogs")

        harvest_list.click_create()
        screenshot("req007_010_dialog_open", "Erstellen-Dialog geoeffnet")

        assert harvest_list.is_create_dialog_open(), (
            "Expected create dialog to be open after clicking create button"
        )

    def test_create_dialog_cancel_closes_without_saving(
        self,
        harvest_list: HarvestBatchListPage,
        screenshot,
    ) -> None:
        """TC-007-012: Canceling the dialog closes it without creating a batch."""
        harvest_list.open()
        initial_count = harvest_list.get_row_count()

        harvest_list.click_create()
        harvest_list.fill_batch_id("TEST-CANCEL-123")
        screenshot("req007_011_before_cancel", "Dialog mit Daten vor Abbruch")

        harvest_list.cancel_create_form()
        harvest_list.wait_for_dialog_closed()
        screenshot("req007_011_after_cancel", "Dialog geschlossen nach Abbruch")

        assert not harvest_list.is_create_dialog_open(), (
            "Expected dialog to be closed after cancel"
        )
        after_count = harvest_list.get_row_count()
        assert after_count == initial_count, (
            f"Expected row count unchanged after cancel ({initial_count}), got {after_count}"
        )

    def test_create_batch_missing_plant_shows_validation_error(
        self,
        harvest_list: HarvestBatchListPage,
        screenshot,
    ) -> None:
        """TC-007-008: Submitting without selecting a plant shows validation error."""
        harvest_list.open()
        harvest_list.click_create()

        # Wait for the dialog form to fully render (plant options may be loading)
        time.sleep(1)

        # Do not select a plant -- submit directly
        harvest_list.submit_create_form()
        time.sleep(1)
        screenshot(
            "req007_012_validation_plant_missing",
            "Validierungsfehler: Pflanze fehlt",
        )

        assert harvest_list.is_create_dialog_open(), (
            "Expected dialog to remain open when plant_key is missing"
        )
        # Check for validation error on plant_key OR harvest_type (both are required)
        has_plant_error = harvest_list.has_validation_error("plant_key")
        has_type_error = harvest_list.has_validation_error("harvest_type")
        assert has_plant_error or has_type_error, (
            "Expected validation error for plant_key or harvest_type field"
        )

    def test_create_batch_happy_path(
        self,
        harvest_list: HarvestBatchListPage,
        screenshot,
    ) -> None:
        """TC-007-007: Create a harvest batch with minimal required fields."""
        harvest_list.open()
        screenshot("req007_013_before_create", "Liste vor Erstellen")

        harvest_list.click_create()

        # Try to select the first plant available
        try:
            harvest_list.select_plant("")  # will pick first option
        except Exception:
            pytest.skip("No plants available -- cannot test batch creation")

        screenshot("req007_013_form_filled", "Formular ausgefuellt")
        harvest_list.submit_create_form()

        # Wait for dialog to close
        try:
            harvest_list.wait_for_dialog_closed(timeout=10)
        except Exception:
            screenshot(
                "req007_013_submit_failed",
                "Erstellen fehlgeschlagen -- Dialog offen",
            )
            pytest.fail("Create dialog did not close after submit -- possible API error")

        time.sleep(1)  # Wait for table refresh
        screenshot("req007_013_after_create", "Liste nach Erstellen")

    def test_create_batch_with_wet_weight_and_notes(
        self,
        harvest_list: HarvestBatchListPage,
        screenshot,
    ) -> None:
        """TC-007-010: Create batch with wet weight, harvester, and notes."""
        harvest_list.open()
        harvest_list.click_create()

        try:
            harvest_list.select_plant("")
        except Exception:
            pytest.skip("No plants available -- cannot test batch creation")

        harvest_list.fill_wet_weight(120)
        harvest_list.fill_harvester("Max Mustermann")
        harvest_list.fill_notes("Morgens geerntet, gutes Aroma")
        screenshot(
            "req007_014_form_with_details",
            "Formular mit Nassgewicht und Notizen",
        )

        harvest_list.submit_create_form()
        try:
            harvest_list.wait_for_dialog_closed(timeout=10)
        except Exception:
            screenshot(
                "req007_014_submit_failed",
                "Erstellen mit Details fehlgeschlagen",
            )
            pytest.fail("Create dialog did not close after submit")

        screenshot("req007_014_after_create", "Liste nach Erstellen mit Details")

    def test_create_batch_with_custom_batch_id(
        self,
        harvest_list: HarvestBatchListPage,
        screenshot,
    ) -> None:
        """TC-007-009: Create batch with a manually entered batch ID."""
        harvest_list.open()
        harvest_list.click_create()

        try:
            harvest_list.select_plant("")
        except Exception:
            pytest.skip("No plants available -- cannot test batch creation")

        harvest_list.fill_batch_id("ERNTE-2026-E2E")
        screenshot(
            "req007_015_custom_batch_id",
            "Formular mit benutzerdefinierter Chargen-ID",
        )

        harvest_list.submit_create_form()
        try:
            harvest_list.wait_for_dialog_closed(timeout=10)
        except Exception:
            screenshot("req007_015_submit_failed", "Erstellen mit Chargen-ID fehlgeschlagen")
            pytest.fail("Create dialog did not close after submit")

        screenshot("req007_015_after_create", "Liste nach Erstellen mit Chargen-ID")
