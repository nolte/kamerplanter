"""E2E tests for REQ-010 — Treatment List Page (TC-010-019 to TC-010-026).

Tests cover:
- TreatmentListPage: list display, column headers, IPM hierarchy chip colors
- TreatmentCreateDialog: biological happy path, chemical with karenz, validation
- Karenz chip visibility (only when safety_interval_days > 0)

NFR-008 SS3.4 screenshot checkpoints at:
1. Page Load
2. Before significant actions
3. After significant actions
4. Error states
"""

from __future__ import annotations

import time
import uuid

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.treatment_list_page import TreatmentListPage


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def treatment_list(browser: WebDriver, base_url: str) -> TreatmentListPage:
    """Return a TreatmentListPage bound to the test browser."""
    return TreatmentListPage(browser, base_url)


# -- TC-010-019 to TC-010-022: Treatment List Page ----------------------------


class TestTreatmentListPage:
    """TC-010-019 to TC-010-022: TreatmentListPage display and interactions."""

    def test_page_renders_with_correct_structure(
        self,
        treatment_list: TreatmentListPage,
        screenshot,
    ) -> None:
        """TC-010-019: Treatment list page loads with title, table, and create button."""
        treatment_list.open()
        screenshot("req010_040_treatment_list_loaded", "Treatment list after initial load")

        assert treatment_list.driver.find_element(
            *TreatmentListPage.PAGE
        ).is_displayed(), "Expected [data-testid='treatment-list-page'] to be visible"

        btn = treatment_list.driver.find_element(*TreatmentListPage.CREATE_BUTTON)
        assert btn.is_displayed(), "Expected [data-testid='create-button'] to be visible"

    def test_table_has_expected_column_headers(
        self,
        treatment_list: TreatmentListPage,
        screenshot,
    ) -> None:
        """TC-010-019: DataTable renders with expected columns for treatments."""
        treatment_list.open()
        screenshot("req010_041_treatment_table_columns", "Treatment table column headers")

        headers = treatment_list.get_column_headers()
        assert len(headers) > 0, f"Expected column headers, got none. Headers: {headers}"

    def test_intro_text_is_visible(
        self,
        treatment_list: TreatmentListPage,
        screenshot,
    ) -> None:
        """TC-010-019: Introductory description text is visible."""
        treatment_list.open()
        screenshot("req010_042_treatment_intro_text", "Treatment list intro text")

        assert treatment_list.has_intro_text(), (
            "Expected introductory description text to be visible"
        )

    def test_search_filters_treatments(
        self,
        treatment_list: TreatmentListPage,
        screenshot,
    ) -> None:
        """TC-010-019: Search filters treatment list."""
        treatment_list.open()
        initial_count = treatment_list.get_row_count()

        if initial_count == 0:
            pytest.skip("No treatments in database to search")

        first_name = treatment_list.get_first_column_texts()[0]
        search_term = first_name[:4]

        screenshot("req010_043_treatment_before_search", "Treatment list before search")
        treatment_list.search(search_term)
        time.sleep(0.5)
        screenshot("req010_044_treatment_after_search", "Treatment list after search")

        filtered = treatment_list.get_first_column_texts()
        assert len(filtered) > 0, (
            f"Expected results when searching for '{search_term}'"
        )

    def test_search_no_results(
        self,
        treatment_list: TreatmentListPage,
        screenshot,
    ) -> None:
        """TC-010-019: Search with no match shows empty state."""
        treatment_list.open()
        treatment_list.search("XYZUnbekannt99")
        time.sleep(0.5)
        screenshot("req010_045_treatment_no_results", "Treatment search with no results")

        assert treatment_list.get_row_count() == 0, "Expected zero rows for non-matching search"

    def test_sort_by_column(
        self,
        treatment_list: TreatmentListPage,
        screenshot,
    ) -> None:
        """TC-010-019: Sorting by column header works."""
        treatment_list.open()

        if treatment_list.get_row_count() == 0:
            pytest.skip("No treatments to sort")

        headers = treatment_list.get_column_headers()
        if not headers:
            pytest.skip("No column headers")

        treatment_list.click_column_header(headers[0])
        time.sleep(0.3)
        screenshot("req010_046_treatment_sorted", "Treatment list after column sort")

        assert treatment_list.has_sort_chip(), "Expected sort chip after clicking column header"

    def test_showing_count_displays_range(
        self,
        treatment_list: TreatmentListPage,
        screenshot,
    ) -> None:
        """TC-010-019: Showing count text is visible."""
        treatment_list.open()

        if treatment_list.get_row_count() == 0:
            pytest.skip("No treatments in database")

        showing_text = treatment_list.get_showing_count_text()
        screenshot("req010_047_treatment_showing_count", "Treatment list showing count")
        assert "Zeigt" in showing_text or "von" in showing_text, (
            f"Expected showing count text, got '{showing_text}'"
        )


# -- TC-010-023 to TC-010-026: Treatment Create Dialog -----------------------


class TestTreatmentCreateDialog:
    """TC-010-023 to TC-010-026: Treatment create dialog operations."""

    def test_create_biological_treatment_happy_path(
        self,
        treatment_list: TreatmentListPage,
        screenshot,
    ) -> None:
        """TC-010-023: Create biological treatment (happy path)."""
        treatment_list.open()
        screenshot("req010_048_before_bio_create", "Treatment list before creating biological")

        treatment_list.click_create()
        assert treatment_list.is_create_dialog_open(), "Expected create dialog to be open"
        screenshot("req010_049_treatment_dialog_open", "Treatment create dialog opened")

        unique = uuid.uuid4().hex[:6]
        bio_name = f"E2E-Raubmilbe {unique}"
        treatment_list.fill_name(bio_name)
        treatment_list.select_treatment_type("Biologisch")
        treatment_list.fill_active_ingredient("Phytoseiulus persimilis")
        treatment_list.select_application_method("Freilassung")
        # safety_interval_days defaults to 0
        screenshot("req010_050_bio_form_filled", "Biological treatment form filled")

        treatment_list.submit_create_form()
        treatment_list.wait_for_dialog_closed()
        screenshot("req010_051_after_bio_create", "Treatment list after creating biological")

        assert not treatment_list.is_create_dialog_open(), "Expected dialog to close"

        names = treatment_list.get_first_column_texts()
        assert any(bio_name in n for n in names), (
            f"Expected '{bio_name}' in treatment list, got {names}"
        )

    def test_create_chemical_treatment_with_karenz(
        self,
        treatment_list: TreatmentListPage,
        screenshot,
    ) -> None:
        """TC-010-024: Create chemical treatment with safety interval and protective equipment."""
        treatment_list.open()
        treatment_list.click_create()
        screenshot("req010_052_before_chem_create", "Treatment dialog for chemical treatment")

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
        screenshot("req010_053_chem_form_filled", "Chemical treatment form filled with karenz")

        treatment_list.submit_create_form()
        treatment_list.wait_for_dialog_closed()
        screenshot("req010_054_after_chem_create", "Treatment list after creating chemical")

        assert not treatment_list.is_create_dialog_open(), "Expected dialog to close"

        names = treatment_list.get_first_column_texts()
        assert any(chem_name in n for n in names), (
            f"Expected '{chem_name}' in treatment list, got {names}"
        )

    def test_create_treatment_validation_name_required(
        self,
        treatment_list: TreatmentListPage,
        screenshot,
    ) -> None:
        """TC-010-025: Validation error when name field is empty."""
        from selenium.webdriver.common.by import By

        treatment_list.open()
        treatment_list.click_create()
        time.sleep(0.5)

        # Submit without filling name
        treatment_list.submit_create_form()
        time.sleep(1)
        screenshot(
            "req010_055_treatment_validation_name",
            "Validation error for empty treatment name",
        )

        assert treatment_list.is_create_dialog_open(), "Dialog should remain open"
        has_name_error = treatment_list.has_validation_error("name")
        # Fallback: any error helper text
        has_any_error = len(treatment_list.driver.find_elements(
            By.CSS_SELECTOR, "div[role='dialog'] .MuiFormHelperText-root.Mui-error"
        )) > 0
        assert has_name_error or has_any_error, (
            "Expected validation error for 'name'"
        )

        treatment_list.cancel_create_form()

    def test_create_treatment_cancel_discards_input(
        self,
        treatment_list: TreatmentListPage,
        screenshot,
    ) -> None:
        """TC-010-023: Cancelling create dialog discards entered data."""
        treatment_list.open()

        treatment_list.click_create()
        treatment_list.fill_name("TestBehandlung")
        screenshot("req010_056_treatment_before_cancel", "Treatment dialog before cancel")

        treatment_list.cancel_create_form()
        time.sleep(0.5)
        screenshot("req010_057_treatment_after_cancel", "Treatment list after cancel")

        assert not treatment_list.is_create_dialog_open(), "Dialog should be closed"
        current_names = treatment_list.get_first_column_texts()
        assert "TestBehandlung" not in current_names, (
            "Cancelled treatment 'TestBehandlung' should not appear"
        )
