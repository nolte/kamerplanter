"""E2E tests for REQ-001 — Botanical Family List Page (TC-006 to TC-012)."""

from __future__ import annotations

import time

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import BotanicalFamilyListPage


@pytest.fixture
def family_list(browser: WebDriver, base_url: str) -> BotanicalFamilyListPage:
    return BotanicalFamilyListPage(browser, base_url)


class TestBotanicalFamilyListPage:
    """TC-REQ-001-006 to TC-REQ-001-012: Botanical Family list operations."""

    def test_display_families_in_data_table(
        self, family_list: BotanicalFamilyListPage
    ) -> None:
        """TC-REQ-001-006: Display botanical families in a data table."""
        family_list.open()
        headers = family_list.get_column_headers()

        assert "Name" in headers, f"Expected 'Name' column, got {headers}"
        assert any("Deutscher Name" in h for h in headers), f"Expected 'Deutscher Name', got {headers}"
        assert any("hrstoffbedarf" in h for h in headers), f"Expected 'Nährstoffbedarf', got {headers}"

        row_count = family_list.get_row_count()
        assert row_count > 0, "Expected at least one family row (seed data)"

    def test_search_families_by_name(
        self, family_list: BotanicalFamilyListPage
    ) -> None:
        """TC-REQ-001-007: Search botanical families by name."""
        family_list.open()
        family_list.search("Solan")
        time.sleep(0.5)  # Debounce

        names = family_list.get_first_column_texts()
        assert any("Solanaceae" in n for n in names), (
            f"Expected Solanaceae in filtered results, got {names}"
        )
        assert family_list.has_search_chip(), "Expected search chip to be visible"

    def test_search_families_by_translated_enum(
        self, family_list: BotanicalFamilyListPage
    ) -> None:
        """TC-REQ-001-008: Search botanical families by translated enum value."""
        family_list.open()
        family_list.search("Starkzehrer")
        time.sleep(0.5)

        row_count = family_list.get_row_count()
        assert row_count > 0, "Expected at least one family matching 'Starkzehrer'"

    def test_sort_families_by_column(
        self, family_list: BotanicalFamilyListPage
    ) -> None:
        """TC-REQ-001-009: Sort botanical families by column."""
        family_list.open()
        names_before = family_list.get_first_column_texts()

        family_list.click_column_header("Name")
        time.sleep(0.3)

        assert family_list.has_sort_chip(), "Expected sort chip after clicking column header"

    def test_reset_all_filters(
        self, family_list: BotanicalFamilyListPage
    ) -> None:
        """TC-REQ-001-010: Reset all filters in botanical families table."""
        family_list.open()
        initial_count = family_list.get_row_count()

        family_list.search("Fabaceae")
        time.sleep(0.5)
        filtered_count = family_list.get_row_count()
        assert filtered_count <= initial_count, "Filtered count should be less or equal"

        family_list.click_reset_filters()
        time.sleep(0.5)
        reset_count = family_list.get_row_count()
        assert reset_count >= filtered_count, "Reset should show more or equal rows"

    def test_click_row_navigates_to_detail(
        self, family_list: BotanicalFamilyListPage
    ) -> None:
        """TC-REQ-001-011: Click on a botanical family row navigates to detail page."""
        family_list.open()

        if family_list.get_row_count() == 0:
            pytest.skip("No botanical families in database")

        family_list.click_row(0)
        family_list.wait_for_url_contains("/stammdaten/botanical-families/")

        assert "/stammdaten/botanical-families/" in family_list.driver.current_url, (
            f"Expected detail URL, got {family_list.driver.current_url}"
        )

    def test_showing_count_displays_correct_range(
        self, family_list: BotanicalFamilyListPage
    ) -> None:
        """TC-REQ-001-081: Showing count displays correct range."""
        family_list.open()

        showing_text = family_list.get_showing_count_text()
        assert "Zeigt" in showing_text or "von" in showing_text, (
            f"Expected showing count text, got '{showing_text}'"
        )
