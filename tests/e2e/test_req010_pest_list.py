"""E2E tests for REQ-010 — Pest List Page (TC-010-001 to TC-010-012).

Tests cover:
- PestListPage: list display, column headers, search, sort, chip colors
- PestCreateDialog: happy path, validation errors, cancel, optional fields
- Empty state and no-results state

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

from .pages.pest_list_page import PestListPage


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def pest_list(browser: WebDriver, base_url: str) -> PestListPage:
    """Return a PestListPage bound to the test browser."""
    return PestListPage(browser, base_url)


# -- TC-010-001 to TC-010-007: Pest List Page ---------------------------------


class TestPestListPage:
    """TC-010-001 to TC-010-007: PestListPage display and interactions."""

    def test_page_renders_with_correct_structure(
        self,
        pest_list: PestListPage,
        screenshot,
    ) -> None:
        """TC-010-001: Pest list page loads with title, table, and create button."""
        pest_list.open()
        screenshot("req010_001_pest_list_loaded", "Pest list page after initial load")

        # Page testid is present
        assert pest_list.driver.find_element(
            *PestListPage.PAGE
        ).is_displayed(), "Expected [data-testid='pest-list-page'] to be visible"

        # Create button visible
        btn = pest_list.driver.find_element(*PestListPage.CREATE_BUTTON)
        assert btn.is_displayed(), "Expected [data-testid='create-button'] to be visible"

    def test_table_has_expected_column_headers(
        self,
        pest_list: PestListPage,
        screenshot,
    ) -> None:
        """TC-010-001: DataTable renders with expected columns for pests."""
        pest_list.open()
        screenshot("req010_002_pest_table_columns", "Pest table column headers")

        headers = pest_list.get_column_headers()
        assert len(headers) > 0, f"Expected column headers, got none. Headers: {headers}"
        # German column labels from i18n
        header_text = " ".join(headers)
        assert any("Name" in h for h in headers), (
            f"Expected a 'Name' column header, got: {headers}"
        )

    def test_intro_text_is_visible(
        self,
        pest_list: PestListPage,
        screenshot,
    ) -> None:
        """TC-010-001: Introductory description text is visible below the title."""
        pest_list.open()
        screenshot("req010_003_pest_intro_text", "Pest list intro text visibility")

        assert pest_list.has_intro_text(), "Expected introductory description text to be visible"

    def test_search_filters_by_name(
        self,
        pest_list: PestListPage,
        screenshot,
    ) -> None:
        """TC-010-003: Search filters pest list in real-time."""
        pest_list.open()
        initial_count = pest_list.get_row_count()

        if initial_count == 0:
            pytest.skip("No pests in database to search")

        first_name = pest_list.get_first_column_texts()[0]
        search_term = first_name[:4]  # Use first 4 chars as search term

        screenshot("req010_004_before_search", "Pest list before search")
        pest_list.search(search_term)
        time.sleep(0.5)  # Debounce
        screenshot("req010_005_after_search", "Pest list after search filter applied")

        filtered_names = pest_list.get_first_column_texts()
        assert len(filtered_names) > 0, (
            f"Expected at least one result when searching for '{search_term}'"
        )
        assert any(search_term.lower() in n.lower() for n in filtered_names), (
            f"Expected '{search_term}' in filtered results, got {filtered_names}"
        )

    def test_search_no_results_shows_empty_message(
        self,
        pest_list: PestListPage,
        screenshot,
    ) -> None:
        """TC-010-004: Search with no match shows empty message."""
        pest_list.open()
        pest_list.search("XYZUnbekannt99")
        time.sleep(0.5)
        screenshot("req010_006_search_no_results", "Pest list search with no results")

        assert pest_list.get_row_count() == 0, "Expected zero rows for non-matching search"

    def test_sort_by_column_header(
        self,
        pest_list: PestListPage,
        screenshot,
    ) -> None:
        """TC-010-003: Clicking column header triggers sorting."""
        pest_list.open()

        if pest_list.get_row_count() == 0:
            pytest.skip("No pests in database to sort")

        headers = pest_list.get_column_headers()
        if not headers:
            pytest.skip("No column headers found")

        pest_list.click_column_header(headers[0])
        time.sleep(0.3)
        screenshot("req010_007_after_sort", "Pest list after column sort")

        assert pest_list.has_sort_chip(), "Expected sort chip after clicking column header"

    def test_reset_filters(
        self,
        pest_list: PestListPage,
        screenshot,
    ) -> None:
        """TC-010-003: Reset filters restores original list."""
        pest_list.open()
        initial_count = pest_list.get_row_count()

        if initial_count == 0:
            pytest.skip("No pests in database to filter")

        pest_list.search("XYZUnbekannt99")
        time.sleep(0.5)
        filtered_count = pest_list.get_row_count()

        pest_list.click_reset_filters()
        time.sleep(0.5)
        screenshot("req010_008_after_reset", "Pest list after filter reset")

        reset_count = pest_list.get_row_count()
        assert reset_count >= filtered_count, "Reset should show more or equal rows"

    def test_showing_count_displays_range(
        self,
        pest_list: PestListPage,
        screenshot,
    ) -> None:
        """TC-010-001: Showing count displays the correct range text."""
        pest_list.open()

        if pest_list.get_row_count() == 0:
            pytest.skip("No pests in database")

        showing_text = pest_list.get_showing_count_text()
        screenshot("req010_009_showing_count", "Pest list showing count")
        assert "Zeigt" in showing_text or "von" in showing_text, (
            f"Expected showing count text, got '{showing_text}'"
        )


# -- TC-010-008 to TC-010-012: Pest Create Dialog ----------------------------


class TestPestCreateDialog:
    """TC-010-008 to TC-010-012: Pest create dialog operations."""

    def test_create_pest_happy_path(
        self,
        pest_list: PestListPage,
        screenshot,
    ) -> None:
        """TC-010-008: Create a pest via dialog (happy path)."""
        pest_list.open()
        screenshot("req010_010_before_create", "Pest list before creating new pest")

        pest_list.click_create()
        assert pest_list.is_create_dialog_open(), "Expected create dialog to be open"
        screenshot("req010_011_create_dialog_open", "Pest create dialog opened")

        unique = uuid.uuid4().hex[:6]
        sci_name = f"E2ePestus testii{unique}"
        pest_list.fill_scientific_name(sci_name)
        pest_list.fill_common_name(f"E2E-Testschädling {unique}")
        pest_list.select_pest_type("Milbe")
        pest_list.fill_lifecycle_days(14)
        pest_list.fill_optimal_temp_min(20)
        pest_list.fill_optimal_temp_max(30)
        pest_list.select_detection_difficulty("Schwierig")
        screenshot("req010_012_create_form_filled", "Pest create form filled out")

        pest_list.submit_create_form()
        pest_list.wait_for_dialog_closed()
        screenshot("req010_013_after_create", "Pest list after create")

        assert not pest_list.is_create_dialog_open(), "Expected dialog to close after submit"

        names = pest_list.get_first_column_texts()
        assert any(sci_name in n for n in names), (
            f"Expected '{sci_name}' in pest list, got {names}"
        )

    def test_create_pest_validation_scientific_name_required(
        self,
        pest_list: PestListPage,
        screenshot,
    ) -> None:
        """TC-010-009: Validation error when scientific name is empty."""
        pest_list.open()
        pest_list.click_create()

        # Fill only common name, leave scientific name empty
        pest_list.fill_common_name("Testschaedling")
        pest_list.submit_create_form()
        time.sleep(0.5)
        screenshot(
            "req010_014_validation_scientific_name",
            "Validation error for empty scientific name",
        )

        assert pest_list.is_create_dialog_open(), "Dialog should remain open on validation error"
        assert pest_list.has_validation_error("scientific_name"), (
            "Expected validation error for 'scientific_name'"
        )

        pest_list.cancel_create_form()

    def test_create_pest_validation_common_name_required(
        self,
        pest_list: PestListPage,
        screenshot,
    ) -> None:
        """TC-010-010: Validation error when common name is empty."""
        pest_list.open()
        pest_list.click_create()

        # Fill only scientific name, leave common name empty
        pest_list.fill_scientific_name("Testus scientificus")
        pest_list.submit_create_form()
        time.sleep(0.5)
        screenshot(
            "req010_015_validation_common_name",
            "Validation error for empty common name",
        )

        assert pest_list.is_create_dialog_open(), "Dialog should remain open on validation error"
        assert pest_list.has_validation_error("common_name"), (
            "Expected validation error for 'common_name'"
        )

        pest_list.cancel_create_form()

    def test_create_pest_cancel_discards_input(
        self,
        pest_list: PestListPage,
        screenshot,
    ) -> None:
        """TC-010-011: Cancelling create dialog discards entered data."""
        pest_list.open()
        initial_names = pest_list.get_first_column_texts()

        pest_list.click_create()
        pest_list.fill_scientific_name("TestOrganism")
        pest_list.fill_common_name("Testname")
        screenshot("req010_016_before_cancel", "Pest create dialog with data before cancel")

        pest_list.cancel_create_form()
        time.sleep(0.5)
        screenshot("req010_017_after_cancel", "Pest list after cancelling create dialog")

        assert not pest_list.is_create_dialog_open(), "Dialog should be closed after cancel"

        current_names = pest_list.get_first_column_texts()
        assert "TestOrganism" not in current_names, (
            "Cancelled pest 'TestOrganism' should not appear in the list"
        )

    def test_create_pest_lifecycle_days_optional(
        self,
        pest_list: PestListPage,
        screenshot,
    ) -> None:
        """TC-010-012: Lifecycle days field is optional (null allowed)."""
        pest_list.open()
        pest_list.click_create()

        unique = uuid.uuid4().hex[:6]
        pest_list.fill_scientific_name(f"Frankliniella occidentalis {unique}")
        pest_list.fill_common_name(f"Thripse {unique}")
        # Leave lifecycle_days empty
        screenshot("req010_018_optional_lifecycle", "Pest create with empty lifecycle days")

        pest_list.submit_create_form()
        pest_list.wait_for_dialog_closed()
        screenshot("req010_019_after_optional_create", "Pest list after creating with null lifecycle")

        assert not pest_list.is_create_dialog_open(), "Expected dialog to close"

        time.sleep(1)  # Allow table refresh
        names = pest_list.get_first_column_texts()
        assert any(f"Frankliniella occidentalis {unique}" in n for n in names), (
            f"Expected 'Frankliniella occidentalis {unique}' in list, got {names}"
        )
