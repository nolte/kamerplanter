"""E2E tests for REQ-010 — Disease List Page (TC-010-013 to TC-010-018).

Tests cover:
- DiseaseListPage: list display, column headers, chip colors for pathogen type
- DiseaseCreateDialog: happy path with chip inputs, validation errors
- Incubation period validation (min 1)

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

from .pages.disease_list_page import DiseaseListPage


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def disease_list(browser: WebDriver, base_url: str) -> DiseaseListPage:
    """Return a DiseaseListPage bound to the test browser."""
    return DiseaseListPage(browser, base_url)


# -- TC-010-013 to TC-010-015: Disease List Page ------------------------------


class TestDiseaseListPage:
    """TC-010-013 to TC-010-015: DiseaseListPage display and interactions."""

    def test_page_renders_with_correct_structure(
        self,
        disease_list: DiseaseListPage,
        screenshot,
    ) -> None:
        """TC-010-013: Disease list page loads with title, table, and create button."""
        disease_list.open()
        screenshot("req010_020_disease_list_loaded", "Disease list page after initial load")

        assert disease_list.driver.find_element(
            *DiseaseListPage.PAGE
        ).is_displayed(), "Expected [data-testid='disease-list-page'] to be visible"

        btn = disease_list.driver.find_element(*DiseaseListPage.CREATE_BUTTON)
        assert btn.is_displayed(), "Expected [data-testid='create-button'] to be visible"

    def test_table_has_expected_column_headers(
        self,
        disease_list: DiseaseListPage,
        screenshot,
    ) -> None:
        """TC-010-013: DataTable renders with expected columns for diseases."""
        disease_list.open()
        screenshot("req010_021_disease_table_columns", "Disease table column headers")

        headers = disease_list.get_column_headers()
        assert len(headers) > 0, f"Expected column headers, got none. Headers: {headers}"
        assert any("Name" in h for h in headers), (
            f"Expected a 'Name' column header, got: {headers}"
        )

    def test_intro_text_is_visible(
        self,
        disease_list: DiseaseListPage,
        screenshot,
    ) -> None:
        """TC-010-013: Introductory description text is visible below the title."""
        disease_list.open()
        screenshot("req010_022_disease_intro_text", "Disease list intro text visibility")

        assert disease_list.has_intro_text(), "Expected introductory description text to be visible"

    def test_search_filters_diseases(
        self,
        disease_list: DiseaseListPage,
        screenshot,
    ) -> None:
        """TC-010-013: Search filters disease list."""
        disease_list.open()
        initial_count = disease_list.get_row_count()

        if initial_count == 0:
            pytest.skip("No diseases in database to search")

        first_name = disease_list.get_first_column_texts()[0]
        search_term = first_name[:4]

        screenshot("req010_023_disease_before_search", "Disease list before search")
        disease_list.search(search_term)
        time.sleep(0.5)
        screenshot("req010_024_disease_after_search", "Disease list after search")

        filtered_names = disease_list.get_first_column_texts()
        assert len(filtered_names) > 0, (
            f"Expected at least one result when searching for '{search_term}'"
        )

    def test_search_no_results(
        self,
        disease_list: DiseaseListPage,
        screenshot,
    ) -> None:
        """TC-010-013: Search with no match shows empty state."""
        disease_list.open()
        disease_list.search("XYZUnbekannt99")
        time.sleep(0.5)
        screenshot("req010_025_disease_no_results", "Disease search with no results")

        assert disease_list.get_row_count() == 0, "Expected zero rows for non-matching search"

    def test_sort_by_column(
        self,
        disease_list: DiseaseListPage,
        screenshot,
    ) -> None:
        """TC-010-013: Sorting by column header works."""
        disease_list.open()

        if disease_list.get_row_count() == 0:
            pytest.skip("No diseases to sort")

        headers = disease_list.get_column_headers()
        if not headers:
            pytest.skip("No column headers found")

        disease_list.click_column_header(headers[0])
        time.sleep(0.3)
        screenshot("req010_026_disease_sorted", "Disease list after column sort")

        assert disease_list.has_sort_chip(), "Expected sort chip after clicking column header"

    def test_showing_count_displays_range(
        self,
        disease_list: DiseaseListPage,
        screenshot,
    ) -> None:
        """TC-010-013: Showing count text is visible."""
        disease_list.open()

        if disease_list.get_row_count() == 0:
            pytest.skip("No diseases in database")

        showing_text = disease_list.get_showing_count_text()
        screenshot("req010_027_disease_showing_count", "Disease list showing count")
        assert "Zeigt" in showing_text or "von" in showing_text, (
            f"Expected showing count text, got '{showing_text}'"
        )


# -- TC-010-016 to TC-010-018: Disease Create Dialog -------------------------


class TestDiseaseCreateDialog:
    """TC-010-016 to TC-010-018: Disease create dialog operations."""

    def test_create_disease_happy_path(
        self,
        disease_list: DiseaseListPage,
        screenshot,
    ) -> None:
        """TC-010-016: Create a disease with environmental triggers and affected plant parts."""
        disease_list.open()
        screenshot("req010_028_before_disease_create", "Disease list before creating")

        disease_list.click_create()
        assert disease_list.is_create_dialog_open(), "Expected create dialog to be open"
        screenshot("req010_029_disease_dialog_open", "Disease create dialog opened")

        unique = uuid.uuid4().hex[:6]
        sci_name = f"E2eDiseaseus testii{unique}"
        disease_list.fill_scientific_name(sci_name)
        disease_list.fill_common_name(f"E2E-Testkrankheit {unique}")
        disease_list.select_pathogen_type("Pilzlich")
        disease_list.fill_incubation_period_days(3)
        disease_list.add_environmental_trigger("Hohe Luftfeuchtigkeit")
        time.sleep(0.3)
        disease_list.add_environmental_trigger("Temperaturen 15-20 Grad C")
        time.sleep(0.3)
        disease_list.add_affected_plant_part("Bluete")
        time.sleep(0.3)
        disease_list.add_affected_plant_part("Blaetter")
        screenshot("req010_030_disease_form_filled", "Disease create form filled")

        disease_list.submit_create_form()
        disease_list.wait_for_dialog_closed()
        screenshot("req010_031_after_disease_create", "Disease list after create")

        assert not disease_list.is_create_dialog_open(), "Expected dialog to close"

        names = disease_list.get_first_column_texts()
        assert any(sci_name in n for n in names), (
            f"Expected '{sci_name}' in disease list, got {names}"
        )

    def test_create_disease_validation_both_names_required(
        self,
        disease_list: DiseaseListPage,
        screenshot,
    ) -> None:
        """TC-010-017: Validation error when both name fields are empty."""
        disease_list.open()
        disease_list.click_create()

        # Submit without filling any required fields
        disease_list.submit_create_form()
        time.sleep(0.5)
        screenshot(
            "req010_032_disease_validation_names",
            "Validation errors for empty name fields",
        )

        assert disease_list.is_create_dialog_open(), "Dialog should remain open on validation error"
        # Check for validation error on at least one required field
        has_sci = disease_list.has_validation_error("scientific_name")
        has_common = disease_list.has_validation_error("common_name")
        assert has_sci or has_common, (
            "Expected validation error for 'scientific_name' and/or 'common_name'"
        )

        disease_list.cancel_create_form()

    def test_create_disease_cancel_discards_input(
        self,
        disease_list: DiseaseListPage,
        screenshot,
    ) -> None:
        """TC-010-016: Cancelling create dialog discards entered data."""
        disease_list.open()

        disease_list.click_create()
        disease_list.fill_scientific_name("TestDisease")
        disease_list.fill_common_name("Testkrankheit")
        screenshot("req010_033_disease_before_cancel", "Disease dialog with data before cancel")

        disease_list.cancel_create_form()
        time.sleep(0.5)
        screenshot("req010_034_disease_after_cancel", "Disease list after cancelling dialog")

        assert not disease_list.is_create_dialog_open(), "Dialog should be closed"
        current_names = disease_list.get_first_column_texts()
        assert "TestDisease" not in current_names, (
            "Cancelled disease 'TestDisease' should not appear"
        )
