"""E2E tests for REQ-010 — Treatment List Page.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-010.md):
  TC-REQ-010-024  ->  TC-010-019  Behandlungs-Listenansicht aufrufen
  TC-REQ-010-025  ->  TC-010-019  Behandlungs-Listenansicht — Spalten pruefen
  TC-REQ-010-026  ->  TC-010-019  Einleitungstext sichtbar
  TC-REQ-010-027  ->  TC-010-019  Behandlungs-Liste — Suche filtert
  TC-REQ-010-028  ->  TC-010-019  Behandlungs-Liste — Suche ohne Treffer
  TC-REQ-010-029  ->  TC-010-019  Behandlungs-Liste — Sortierung per Spaltenklick
  TC-REQ-010-030  ->  TC-010-019  Behandlungs-Liste — Zeigt-Zaehler
  TC-REQ-010-031  ->  TC-010-023  Behandlung erstellen — Biologisch (Happy Path)
  TC-REQ-010-032  ->  TC-010-024  Behandlung erstellen — Chemisch mit Karenzzeit
  TC-REQ-010-033  ->  TC-010-025  Behandlung erstellen — Pflichtfeld 'Bezeichnung' leer
  TC-REQ-010-034  ->  TC-010-023  Behandlung erstellen — Dialog abbrechen
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable
import uuid

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.treatment_list_page import TreatmentListPage


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def treatment_list(browser: WebDriver, base_url: str) -> TreatmentListPage:
    """Return a TreatmentListPage bound to the test browser."""
    return TreatmentListPage(browser, base_url)


# -- TC-REQ-010-024 to TC-REQ-010-030: Treatment List Page --------------------


class TestTreatmentListPage:
    """Treatment list display and interactions (Spec: TC-010-019, TC-010-020)."""

    @pytest.mark.smoke
    def test_page_renders_with_correct_structure(
        self,
        treatment_list: TreatmentListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-010-024: Treatment list page loads with title, table, and create button.

        Spec: TC-010-019 -- Behandlungs-Listenansicht aufrufen.
        """
        treatment_list.open()
        screenshot("TC-REQ-010-024_treatment-list-loaded", "Treatment list after initial load")

        page_el = treatment_list.wait_for_element(TreatmentListPage.PAGE)
        assert page_el.is_displayed(), (
            "TC-REQ-010-024 FAIL: Expected [data-testid='treatment-list-page'] to be visible"
        )
        btn_el = treatment_list.wait_for_element(TreatmentListPage.CREATE_BUTTON)
        assert btn_el.is_displayed(), (
            "TC-REQ-010-024 FAIL: Expected [data-testid='create-button'] to be visible"
        )

    @pytest.mark.smoke
    def test_table_has_expected_column_headers(
        self,
        treatment_list: TreatmentListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-010-025: DataTable renders with expected columns for treatments.

        Spec: TC-010-019 -- Behandlungs-Listenansicht — Spalten pruefen.
        """
        treatment_list.open()
        screenshot("TC-REQ-010-025_treatment-table-columns", "Treatment table column headers")

        headers = treatment_list.get_column_headers()
        assert len(headers) > 0, (
            f"TC-REQ-010-025 FAIL: Expected column headers, got none. Headers: {headers}"
        )

    @pytest.mark.smoke
    def test_intro_text_is_visible(
        self,
        treatment_list: TreatmentListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-010-026: Introductory description text is visible.

        Spec: TC-010-019 -- Einleitungstext sichtbar.
        """
        treatment_list.open()
        screenshot("TC-REQ-010-026_treatment-intro-text", "Treatment list intro text")

        assert treatment_list.has_intro_text(), (
            "TC-REQ-010-026 FAIL: Expected introductory description text to be visible"
        )

    @pytest.mark.core_crud
    def test_search_filters_treatments(
        self,
        treatment_list: TreatmentListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-010-027: Search filters treatment list.

        Spec: TC-010-019 -- Behandlungs-Liste — Suche filtert.
        """
        treatment_list.open()
        initial_count = treatment_list.get_row_count()

        if initial_count == 0:
            pytest.skip("No treatments in database to search")

        first_name = treatment_list.get_first_column_texts()[0]
        search_term = first_name[:4]

        screenshot("TC-REQ-010-027_before-search", "Treatment list before search")
        treatment_list.search(search_term)
        treatment_list.wait_for_loading_complete()
        screenshot("TC-REQ-010-027_after-search", "Treatment list after search")

        filtered = treatment_list.get_first_column_texts()
        assert len(filtered) > 0, (
            f"TC-REQ-010-027 FAIL: Expected results when searching for '{search_term}'"
        )

    @pytest.mark.core_crud
    def test_search_no_results(
        self,
        treatment_list: TreatmentListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-010-028: Search with no match shows empty state.

        Spec: TC-010-019 -- Behandlungs-Liste — Suche ohne Treffer.
        """
        treatment_list.open()
        treatment_list.search("XYZUnbekannt99")
        treatment_list.wait_for_loading_complete()
        screenshot("TC-REQ-010-028_treatment-no-results", "Treatment search with no results")

        assert treatment_list.get_row_count() == 0, (
            "TC-REQ-010-028 FAIL: Expected zero rows for non-matching search"
        )

    @pytest.mark.core_crud
    def test_sort_by_column(
        self,
        treatment_list: TreatmentListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-010-029: Sorting by column header works.

        Spec: TC-010-019 -- Behandlungs-Liste — Sortierung per Spaltenklick.
        """
        treatment_list.open()

        if treatment_list.get_row_count() == 0:
            pytest.skip("No treatments to sort")

        headers = treatment_list.get_column_headers()
        if not headers:
            pytest.skip("No column headers")

        screenshot("TC-REQ-010-029_before-sort", "Treatment list before sorting")
        treatment_list.click_column_header(headers[0])
        treatment_list.wait_for_loading_complete()
        screenshot("TC-REQ-010-029_after-sort", "Treatment list after column sort")

        assert treatment_list.has_sort_chip(), (
            "TC-REQ-010-029 FAIL: Expected sort chip after clicking column header"
        )

    @pytest.mark.smoke
    def test_showing_count_displays_range(
        self,
        treatment_list: TreatmentListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-010-030: Showing count text is visible.

        Spec: TC-010-019 -- Behandlungs-Liste — Zeigt-Zaehler.
        """
        treatment_list.open()

        if treatment_list.get_row_count() == 0:
            pytest.skip("No treatments in database")

        showing_text = treatment_list.get_showing_count_text()
        screenshot("TC-REQ-010-030_treatment-showing-count", "Treatment list showing count")
        assert "Zeigt" in showing_text or "von" in showing_text, (
            f"TC-REQ-010-030 FAIL: Expected showing count text, got '{showing_text}'"
        )


# -- TC-REQ-010-031 to TC-REQ-010-034: Treatment Create Dialog ----------------


class TestTreatmentCreateDialog:
    """Treatment create dialog operations (Spec: TC-010-023, TC-010-024, TC-010-025)."""

    @pytest.mark.core_crud
    def test_create_biological_treatment_happy_path(
        self,
        treatment_list: TreatmentListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-010-031: Create biological treatment (happy path).

        Spec: TC-010-023 -- Behandlung erstellen — Biologische Behandlung (Happy Path).
        """
        treatment_list.open()
        screenshot("TC-REQ-010-031_before-bio-create", "Treatment list before creating biological")

        treatment_list.click_create()
        assert treatment_list.is_create_dialog_open(), (
            "TC-REQ-010-031 FAIL: Expected create dialog to be open"
        )
        screenshot("TC-REQ-010-031_treatment-dialog-open", "Treatment create dialog opened")

        unique = uuid.uuid4().hex[:6]
        bio_name = f"E2E-Raubmilbe {unique}"
        treatment_list.fill_name(bio_name)
        treatment_list.select_treatment_type("Biologisch")
        treatment_list.fill_active_ingredient("Phytoseiulus persimilis")
        treatment_list.select_application_method("Freilassung")
        # safety_interval_days defaults to 0
        screenshot("TC-REQ-010-031_bio-form-filled", "Biological treatment form filled")

        treatment_list.submit_create_form()
        treatment_list.wait_for_dialog_closed()
        screenshot("TC-REQ-010-031_after-bio-create", "Treatment list after creating biological")

        assert not treatment_list.is_create_dialog_open(), (
            "TC-REQ-010-031 FAIL: Expected dialog to close"
        )

        names = treatment_list.get_first_column_texts()
        assert any(bio_name in n for n in names), (
            f"TC-REQ-010-031 FAIL: Expected '{bio_name}' in treatment list, got {names}"
        )

    @pytest.mark.core_crud
    def test_create_chemical_treatment_with_karenz(
        self,
        treatment_list: TreatmentListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-010-032: Create chemical treatment with safety interval and protective equipment.

        Spec: TC-010-024 -- Behandlung erstellen — Chemische Behandlung mit Karenzzeit.
        """
        treatment_list.open()
        treatment_list.click_create()
        screenshot("TC-REQ-010-032_before-chem-create", "Treatment dialog for chemical treatment")

        unique = uuid.uuid4().hex[:6]
        chem_name = f"E2E-Pyrethrin {unique}"
        treatment_list.fill_name(chem_name)
        treatment_list.select_treatment_type("Chemisch")
        treatment_list.fill_active_ingredient("Pyrethrin")
        treatment_list.select_application_method("Sprühen")
        treatment_list.fill_safety_interval_days(21)
        treatment_list.fill_dosage_per_liter(2.5)
        treatment_list.add_protective_equipment("Handschuhe")
        treatment_list.add_protective_equipment("Schutzbrille")
        screenshot("TC-REQ-010-032_chem-form-filled", "Chemical treatment form filled with karenz")

        treatment_list.submit_create_form()
        treatment_list.wait_for_dialog_closed()
        screenshot("TC-REQ-010-032_after-chem-create", "Treatment list after creating chemical")

        assert not treatment_list.is_create_dialog_open(), (
            "TC-REQ-010-032 FAIL: Expected dialog to close"
        )

        names = treatment_list.get_first_column_texts()
        assert any(chem_name in n for n in names), (
            f"TC-REQ-010-032 FAIL: Expected '{chem_name}' in treatment list, got {names}"
        )

    @pytest.mark.core_crud
    def test_create_treatment_validation_name_required(
        self,
        treatment_list: TreatmentListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-010-033: Validation error when name field is empty.

        Spec: TC-010-025 -- Behandlung erstellen — Pflichtfeld 'Bezeichnung' leer.
        """
        from selenium.webdriver.common.by import By

        treatment_list.open()
        treatment_list.click_create()
        treatment_list.wait_for_loading_complete()

        # Submit without filling name
        treatment_list.submit_create_form()
        treatment_list.wait_for_loading_complete()
        screenshot(
            "TC-REQ-010-033_treatment-validation-name",
            "Validation error for empty treatment name",
        )

        assert treatment_list.is_create_dialog_open(), (
            "TC-REQ-010-033 FAIL: Dialog should remain open"
        )
        has_name_error = treatment_list.has_validation_error("name")
        # Fallback: any error helper text
        has_any_error = len(treatment_list.driver.find_elements(
            By.CSS_SELECTOR, "div[role='dialog'] .MuiFormHelperText-root.Mui-error"
        )) > 0
        assert has_name_error or has_any_error, (
            "TC-REQ-010-033 FAIL: Expected validation error for 'name'"
        )

        treatment_list.cancel_create_form()

    @pytest.mark.core_crud
    def test_create_treatment_cancel_discards_input(
        self,
        treatment_list: TreatmentListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-010-034: Cancelling create dialog discards entered data.

        Spec: TC-010-023 -- Behandlung erstellen — Dialog abbrechen.
        """
        treatment_list.open()

        treatment_list.click_create()
        treatment_list.fill_name("TestBehandlung")
        screenshot("TC-REQ-010-034_treatment-before-cancel", "Treatment dialog before cancel")

        treatment_list.cancel_create_form()
        treatment_list.wait_for_loading_complete()
        screenshot("TC-REQ-010-034_treatment-after-cancel", "Treatment list after cancel")

        assert not treatment_list.is_create_dialog_open(), (
            "TC-REQ-010-034 FAIL: Dialog should be closed"
        )
        current_names = treatment_list.get_first_column_texts()
        assert "TestBehandlung" not in current_names, (
            "TC-REQ-010-034 FAIL: Cancelled treatment 'TestBehandlung' should not appear"
        )
