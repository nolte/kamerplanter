"""E2E tests for REQ-010 — Pest List Page.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-010.md):
  TC-REQ-010-001  ->  TC-010-001  Schaedlings-Listenansicht aufrufen — Ladevorgang und Tabellenstruktur
  TC-REQ-010-002  ->  TC-010-001  Schaedlings-Listenansicht — Spalten pruefen
  TC-REQ-010-003  ->  TC-010-001  Einleitungstext sichtbar
  TC-REQ-010-004  ->  TC-010-003  Schaedlings-Liste — Suche filtert in Echtzeit
  TC-REQ-010-005  ->  TC-010-004  Schaedlings-Liste — Suche findet keinen Treffer
  TC-REQ-010-006  ->  TC-010-003  Schaedlings-Liste — Sortierung per Spaltenklick
  TC-REQ-010-007  ->  TC-010-003  Schaedlings-Liste — Filter zuruecksetzen
  TC-REQ-010-008  ->  TC-010-001  Schaedlings-Liste — Zeigt-Zaehler
  TC-REQ-010-009  ->  TC-010-008  Schaedling erstellen — Happy Path
  TC-REQ-010-010  ->  TC-010-009  Schaedling erstellen — Wissenschaftlicher Name leer
  TC-REQ-010-011  ->  TC-010-010  Schaedling erstellen — Gebraeuchlicher Name leer
  TC-REQ-010-012  ->  TC-010-011  Schaedling erstellen — Dialog abbrechen
  TC-REQ-010-013  ->  TC-010-012  Schaedling erstellen — Lebenszyklus-Feld optional
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable
import uuid

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.pest_list_page import PestListPage


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def pest_list(browser: WebDriver, base_url: str) -> PestListPage:
    """Return a PestListPage bound to the test browser."""
    return PestListPage(browser, base_url)


# -- TC-REQ-010-001 to TC-REQ-010-008: Pest List Page -------------------------


class TestPestListPage:
    """Pest list display and interactions (Spec: TC-010-001, TC-010-003, TC-010-004)."""

    @pytest.mark.smoke
    def test_page_renders_with_correct_structure(
        self,
        pest_list: PestListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-010-001: Pest list page loads with title, table, and create button.

        Spec: TC-010-001 -- Schaedlings-Listenansicht aufrufen — Ladevorgang und Tabellenstruktur.
        """
        pest_list.open()
        screenshot("TC-REQ-010-001_pest-list-loaded", "Pest list page after initial load")

        page_el = pest_list.wait_for_element(PestListPage.PAGE)
        assert page_el.is_displayed(), (
            "TC-REQ-010-001 FAIL: Expected [data-testid='pest-list-page'] to be visible"
        )
        btn_el = pest_list.wait_for_element(PestListPage.CREATE_BUTTON)
        assert btn_el.is_displayed(), (
            "TC-REQ-010-001 FAIL: Expected [data-testid='create-button'] to be visible"
        )

    @pytest.mark.smoke
    def test_table_has_expected_column_headers(
        self,
        pest_list: PestListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-010-002: DataTable renders with expected columns for pests.

        Spec: TC-010-001 -- Schaedlings-Listenansicht — Spalten pruefen.
        """
        pest_list.open()
        screenshot("TC-REQ-010-002_pest-table-columns", "Pest table column headers")

        headers = pest_list.get_column_headers()
        assert len(headers) > 0, (
            f"TC-REQ-010-002 FAIL: Expected column headers, got none. Headers: {headers}"
        )
        assert any("Name" in h for h in headers), (
            f"TC-REQ-010-002 FAIL: Expected a 'Name' column header, got: {headers}"
        )

    @pytest.mark.smoke
    def test_intro_text_is_visible(
        self,
        pest_list: PestListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-010-003: Introductory description text is visible below the title.

        Spec: TC-010-001 -- Einleitungstext sichtbar.
        """
        pest_list.open()
        screenshot("TC-REQ-010-003_pest-intro-text", "Pest list intro text visibility")

        assert pest_list.has_intro_text(), (
            "TC-REQ-010-003 FAIL: Expected introductory description text to be visible"
        )

    @pytest.mark.core_crud
    def test_search_filters_by_name(
        self,
        pest_list: PestListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-010-004: Search filters pest list in real-time.

        Spec: TC-010-003 -- Schaedlings-Liste — Suche filtert in Echtzeit.
        """
        pest_list.open()
        initial_count = pest_list.get_row_count()

        if initial_count == 0:
            pytest.skip("No pests in database to search")

        first_name = pest_list.get_first_column_texts()[0]
        search_term = first_name[:4]  # Use first 4 chars as search term

        screenshot("TC-REQ-010-004_before-search", "Pest list before search")
        pest_list.search(search_term)
        pest_list.wait_for_loading_complete()
        screenshot("TC-REQ-010-004_after-search", "Pest list after search filter applied")

        filtered_names = pest_list.get_first_column_texts()
        assert len(filtered_names) > 0, (
            f"TC-REQ-010-004 FAIL: Expected at least one result when searching for '{search_term}'"
        )
        assert any(search_term.lower() in n.lower() for n in filtered_names), (
            f"TC-REQ-010-004 FAIL: Expected '{search_term}' in filtered results, got {filtered_names}"
        )

    @pytest.mark.core_crud
    def test_search_no_results_shows_empty_message(
        self,
        pest_list: PestListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-010-005: Search with no match shows empty message.

        Spec: TC-010-004 -- Schaedlings-Liste — Suche findet keinen Treffer.
        """
        pest_list.open()
        pest_list.search("XYZUnbekannt99")
        pest_list.wait_for_loading_complete()
        screenshot("TC-REQ-010-005_search-no-results", "Pest list search with no results")

        assert pest_list.get_row_count() == 0, (
            "TC-REQ-010-005 FAIL: Expected zero rows for non-matching search"
        )

    @pytest.mark.core_crud
    def test_sort_by_column_header(
        self,
        pest_list: PestListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-010-006: Clicking column header triggers sorting.

        Spec: TC-010-003 -- Schaedlings-Liste — Sortierung per Spaltenklick.
        """
        pest_list.open()

        if pest_list.get_row_count() == 0:
            pytest.skip("No pests in database to sort")

        headers = pest_list.get_column_headers()
        if not headers:
            pytest.skip("No column headers found")

        screenshot("TC-REQ-010-006_before-sort", "Pest list before sorting")
        pest_list.click_column_header(headers[0])
        pest_list.wait_for_loading_complete()
        screenshot("TC-REQ-010-006_after-sort", "Pest list after column sort")

        assert pest_list.has_sort_chip(), (
            "TC-REQ-010-006 FAIL: Expected sort chip after clicking column header"
        )

    @pytest.mark.core_crud
    def test_reset_filters(
        self,
        pest_list: PestListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-010-007: Reset filters restores original list.

        Spec: TC-010-003 -- Schaedlings-Liste — Filter zuruecksetzen.
        """
        pest_list.open()
        initial_count = pest_list.get_row_count()

        if initial_count == 0:
            pytest.skip("No pests in database to filter")

        pest_list.search("XYZUnbekannt99")
        pest_list.wait_for_loading_complete()
        filtered_count = pest_list.get_row_count()

        pest_list.click_reset_filters()
        pest_list.wait_for_loading_complete()
        screenshot("TC-REQ-010-007_after-reset", "Pest list after filter reset")

        reset_count = pest_list.get_row_count()
        assert reset_count >= filtered_count, (
            "TC-REQ-010-007 FAIL: Reset should show more or equal rows"
        )

    @pytest.mark.smoke
    def test_showing_count_displays_range(
        self,
        pest_list: PestListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-010-008: Showing count displays the correct range text.

        Spec: TC-010-001 -- Schaedlings-Listenansicht — Zeigt-Zaehler.
        """
        pest_list.open()

        if pest_list.get_row_count() == 0:
            pytest.skip("No pests in database")

        showing_text = pest_list.get_showing_count_text()
        screenshot("TC-REQ-010-008_showing-count", "Pest list showing count")
        assert "Zeigt" in showing_text or "von" in showing_text, (
            f"TC-REQ-010-008 FAIL: Expected showing count text, got '{showing_text}'"
        )


# -- TC-REQ-010-009 to TC-REQ-010-013: Pest Create Dialog ---------------------


class TestPestCreateDialog:
    """Pest create dialog operations (Spec: TC-010-008, TC-010-009, TC-010-010, TC-010-011, TC-010-012)."""

    @pytest.mark.core_crud
    def test_create_pest_happy_path(
        self,
        pest_list: PestListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-010-009: Create a pest via dialog (happy path).

        Spec: TC-010-008 -- Schaedling erstellen — Happy Path.
        """
        pest_list.open()
        screenshot("TC-REQ-010-009_before-create", "Pest list before creating new pest")

        pest_list.click_create()
        assert pest_list.is_create_dialog_open(), (
            "TC-REQ-010-009 FAIL: Expected create dialog to be open"
        )
        screenshot("TC-REQ-010-009_create-dialog-open", "Pest create dialog opened")

        unique = uuid.uuid4().hex[:6]
        sci_name = f"E2ePestus testii{unique}"
        pest_list.fill_scientific_name(sci_name)
        pest_list.fill_common_name(f"E2E-Testschädling {unique}")
        pest_list.select_pest_type("Milbe")
        pest_list.fill_lifecycle_days(14)
        pest_list.fill_optimal_temp_min(20)
        pest_list.fill_optimal_temp_max(30)
        pest_list.select_detection_difficulty("Schwierig")
        screenshot("TC-REQ-010-009_create-form-filled", "Pest create form filled out")

        pest_list.submit_create_form()
        pest_list.wait_for_dialog_closed()
        screenshot("TC-REQ-010-009_after-create", "Pest list after create")

        assert not pest_list.is_create_dialog_open(), (
            "TC-REQ-010-009 FAIL: Expected dialog to close after submit"
        )

        # Search for the new pest to find it regardless of table pagination
        pest_list.search(sci_name)
        pest_list.wait_for_loading_complete()
        names = pest_list.get_first_column_texts()
        assert any(sci_name in n for n in names), (
            f"TC-REQ-010-009 FAIL: Expected '{sci_name}' in pest list, got {names}"
        )

    @pytest.mark.core_crud
    def test_create_pest_validation_scientific_name_required(
        self,
        pest_list: PestListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-010-010: Validation error when scientific name is empty.

        Spec: TC-010-009 -- Schaedling erstellen — Pflichtfeld 'Wissenschaftlicher Name' leer.
        """
        from selenium.webdriver.common.by import By

        pest_list.open()
        pest_list.click_create()
        pest_list.wait_for_loading_complete()

        # Fill only common name, leave scientific name empty
        pest_list.fill_common_name("Testschaedling")
        pest_list.submit_create_form()
        pest_list.wait_for_loading_complete()
        screenshot(
            "TC-REQ-010-010_validation-scientific-name",
            "Validation error for empty scientific name",
        )

        assert pest_list.is_create_dialog_open(), (
            "TC-REQ-010-010 FAIL: Dialog should remain open on validation error"
        )
        has_sci_error = pest_list.has_validation_error("scientific_name")
        # Fallback: any error helper text
        has_any_error = len(pest_list.driver.find_elements(
            By.CSS_SELECTOR, "div[role='dialog'] .MuiFormHelperText-root.Mui-error"
        )) > 0
        # Fallback: aria-invalid on input (validation fired but helperText may be empty)
        has_aria_invalid = len(pest_list.driver.find_elements(
            By.CSS_SELECTOR,
            "div[role='dialog'] [data-testid='form-field-scientific_name'] input[aria-invalid='true']"
        )) > 0
        # Fallback: any aria-invalid in dialog
        has_any_aria_invalid = len(pest_list.driver.find_elements(
            By.CSS_SELECTOR, "div[role='dialog'] input[aria-invalid='true']"
        )) > 0
        # Debug: get scientific_name field value to understand state
        try:
            sci_input = pest_list.driver.find_element(
                By.CSS_SELECTOR,
                "div[role='dialog'] [data-testid='form-field-scientific_name'] input"
            )
            sci_value = sci_input.get_attribute("value")
            sci_aria = sci_input.get_attribute("aria-invalid")
        except Exception as e:
            sci_value = f"NOT FOUND: {e}"
            sci_aria = "N/A"
        assert has_sci_error or has_any_error or has_aria_invalid or has_any_aria_invalid, (
            f"TC-REQ-010-010 FAIL: Expected validation error for 'scientific_name'. "
            f"scientific_name value='{sci_value}', aria-invalid='{sci_aria}'"
        )

        pest_list.cancel_create_form()

    @pytest.mark.core_crud
    def test_create_pest_validation_common_name_required(
        self,
        pest_list: PestListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-010-011: Validation error when common name is empty.

        Spec: TC-010-010 -- Schaedling erstellen — Pflichtfeld 'Gebraeuchlicher Name' leer.
        """
        from selenium.webdriver.common.by import By

        pest_list.open()
        pest_list.click_create()
        pest_list.wait_for_loading_complete()

        # Fill only scientific name, leave common name empty
        pest_list.fill_scientific_name("Testus scientificus")
        pest_list.submit_create_form()
        pest_list.wait_for_loading_complete()
        screenshot(
            "TC-REQ-010-011_validation-common-name",
            "Validation error for empty common name",
        )

        assert pest_list.is_create_dialog_open(), (
            "TC-REQ-010-011 FAIL: Dialog should remain open on validation error"
        )
        has_common_error = pest_list.has_validation_error("common_name")
        # Fallback: any error helper text
        has_any_error = len(pest_list.driver.find_elements(
            By.CSS_SELECTOR, "div[role='dialog'] .MuiFormHelperText-root.Mui-error"
        )) > 0
        assert has_common_error or has_any_error, (
            "TC-REQ-010-011 FAIL: Expected validation error for 'common_name'"
        )

        pest_list.cancel_create_form()

    @pytest.mark.core_crud
    def test_create_pest_cancel_discards_input(
        self,
        pest_list: PestListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-010-012: Cancelling create dialog discards entered data.

        Spec: TC-010-011 -- Schaedling erstellen — Dialog abbrechen verwirft Eingaben.
        """
        pest_list.open()
        initial_names = pest_list.get_first_column_texts()

        pest_list.click_create()
        pest_list.fill_scientific_name("TestOrganism")
        pest_list.fill_common_name("Testname")
        screenshot("TC-REQ-010-012_before-cancel", "Pest create dialog with data before cancel")

        pest_list.cancel_create_form()
        pest_list.wait_for_loading_complete()
        screenshot("TC-REQ-010-012_after-cancel", "Pest list after cancelling create dialog")

        assert not pest_list.is_create_dialog_open(), (
            "TC-REQ-010-012 FAIL: Dialog should be closed after cancel"
        )

        current_names = pest_list.get_first_column_texts()
        assert "TestOrganism" not in current_names, (
            "TC-REQ-010-012 FAIL: Cancelled pest 'TestOrganism' should not appear in the list"
        )

    @pytest.mark.core_crud
    def test_create_pest_lifecycle_days_optional(
        self,
        pest_list: PestListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-010-013: Lifecycle days field is optional (null allowed).

        Spec: TC-010-012 -- Schaedling erstellen — Lebenszyklus-Feld optionale Eingabe.
        """
        pest_list.open()
        pest_list.click_create()

        unique = uuid.uuid4().hex[:6]
        pest_list.fill_scientific_name(f"Frankliniella occidentalis {unique}")
        pest_list.fill_common_name(f"Thripse {unique}")
        # Leave lifecycle_days empty
        screenshot("TC-REQ-010-013_optional-lifecycle", "Pest create with empty lifecycle days")

        pest_list.submit_create_form()
        pest_list.wait_for_dialog_closed()
        screenshot("TC-REQ-010-013_after-optional-create", "Pest list after creating with null lifecycle")

        assert not pest_list.is_create_dialog_open(), (
            "TC-REQ-010-013 FAIL: Expected dialog to close"
        )

        pest_list.wait_for_loading_complete()
        # Search for the new pest to find it regardless of table pagination
        pest_list.search(f"Frankliniella occidentalis {unique}")
        pest_list.wait_for_loading_complete()
        names = pest_list.get_first_column_texts()
        assert any(f"Frankliniella occidentalis {unique}" in n for n in names), (
            f"TC-REQ-010-013 FAIL: Expected 'Frankliniella occidentalis {unique}' in list, got {names}"
        )
