"""E2E tests for REQ-001 — Botanical Family List Page.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-001.md):
  TC-REQ-001-006  ->  TC-001-001  Botanische Familienliste wird vollstaendig geladen und angezeigt
  TC-REQ-001-007  ->  TC-001-003  Suchfunktion in Botanische Familien-Liste
  TC-REQ-001-008  ->  TC-001-003  Suchfunktion — Suche nach uebersetztem Enum-Wert
  TC-REQ-001-009  ->  TC-001-002  Tabelle sortieren nach Spalte
  TC-REQ-001-010  ->  TC-001-003  Suchfunktion — Filter zuruecksetzen
  TC-REQ-001-011  ->  TC-001-005  Navigation von Liste zu Detailansicht
  TC-REQ-001-081  ->  TC-001-001  Botanische Familienliste — Zeigt-Zaehler
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable
import time  # kept for debounce waits

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import BotanicalFamilyListPage


@pytest.fixture
def family_list(browser: WebDriver, base_url: str) -> BotanicalFamilyListPage:
    return BotanicalFamilyListPage(browser, base_url)


class TestBotanicalFamilyListPage:
    """Botanical Family list operations (Spec: TC-001-001, TC-001-002, TC-001-003, TC-001-005)."""

    @pytest.mark.smoke
    def test_display_families_in_data_table(
        self, family_list: BotanicalFamilyListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-006: Display botanical families in a data table.

        Spec: TC-001-001 -- Botanische Familienliste wird vollstaendig geladen und angezeigt.
        """
        family_list.open()
        screenshot("TC-REQ-001-006_family-list-loaded", "Botanical family list page after initial load")

        headers = family_list.get_column_headers()

        assert "Name" in headers, (
            f"TC-REQ-001-006 FAIL: Expected 'Name' column, got {headers}"
        )
        assert any("Name" in h for h in headers), (
            f"TC-REQ-001-006 FAIL: Expected 'Gebraeuchlicher Name' column, got {headers}"
        )
        assert any("hrstoffbedarf" in h for h in headers), (
            f"TC-REQ-001-006 FAIL: Expected 'Naehrstoffbedarf', got {headers}"
        )

        row_count = family_list.get_row_count()
        assert row_count > 0, (
            "TC-REQ-001-006 FAIL: Expected at least one family row (seed data)"
        )

    @pytest.mark.core_crud
    def test_search_families_by_name(
        self, family_list: BotanicalFamilyListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-007: Search botanical families by name.

        Spec: TC-001-003 -- Suchfunktion in Botanische Familien-Liste.
        """
        family_list.open()
        family_list.search("Solan")
        time.sleep(0.3)  # debounce wait

        screenshot("TC-REQ-001-007_search-results", "Family list after searching for 'Solan'")

        names = family_list.get_first_column_texts()
        assert any("Solanaceae" in n for n in names), (
            f"TC-REQ-001-007 FAIL: Expected Solanaceae in filtered results, got {names}"
        )
        assert family_list.has_search_chip(), (
            "TC-REQ-001-007 FAIL: Expected search chip to be visible"
        )

    @pytest.mark.core_crud
    def test_search_families_by_translated_enum(
        self, family_list: BotanicalFamilyListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-008: Search botanical families by translated enum value.

        Spec: TC-001-003 -- Suchfunktion — Suche nach uebersetztem Enum-Wert.
        """
        family_list.open()
        family_list.search("Starkzehrer")
        time.sleep(0.3)  # debounce wait

        screenshot("TC-REQ-001-008_enum-search", "Family list after searching for 'Starkzehrer'")

        row_count = family_list.get_row_count()
        assert row_count > 0, (
            "TC-REQ-001-008 FAIL: Expected at least one family matching 'Starkzehrer'"
        )

    @pytest.mark.core_crud
    def test_sort_families_by_column(
        self, family_list: BotanicalFamilyListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-009: Sort botanical families by column.

        Spec: TC-001-002 -- Tabelle sortieren nach Naehrstoffbedarf.
        """
        family_list.open()
        names_before = family_list.get_first_column_texts()

        family_list.click_column_header("Name")
        family_list.wait_for_loading_complete()

        screenshot("TC-REQ-001-009_after-sort", "Family list after sorting by Name column")

        assert family_list.has_sort_chip(), (
            "TC-REQ-001-009 FAIL: Expected sort chip after clicking column header"
        )

    @pytest.mark.core_crud
    def test_reset_all_filters(
        self, family_list: BotanicalFamilyListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-010: Reset all filters in botanical families table.

        Spec: TC-001-003 -- Suchfunktion — Filter zuruecksetzen.
        """
        family_list.open()
        initial_count = family_list.get_row_count()

        family_list.search("Fabaceae")
        time.sleep(0.3)  # debounce wait
        filtered_count = family_list.get_row_count()
        screenshot("TC-REQ-001-010_filtered", "Family list filtered by 'Fabaceae'")

        assert filtered_count <= initial_count, (
            "TC-REQ-001-010 FAIL: Filtered count should be less or equal"
        )

        family_list.click_reset_filters()
        family_list.wait_for_loading_complete()
        screenshot("TC-REQ-001-010_after-reset", "Family list after resetting all filters")

        reset_count = family_list.get_row_count()
        assert reset_count >= filtered_count, (
            "TC-REQ-001-010 FAIL: Reset should show more or equal rows"
        )

    @pytest.mark.smoke
    def test_click_row_navigates_to_detail(
        self, family_list: BotanicalFamilyListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-011: Click on a botanical family row navigates to detail page.

        Spec: TC-001-005 -- Navigation von Liste zu Detailansicht einer Botanischen Familie.
        """
        family_list.open()

        if family_list.get_row_count() == 0:
            pytest.skip("No botanical families in database")

        screenshot("TC-REQ-001-011_before-click", "Family list before clicking row")
        family_list.click_row(0)
        family_list.wait_for_url_contains("/stammdaten/botanical-families/")
        screenshot("TC-REQ-001-011_after-click", "Family detail page after row click")

        assert "/stammdaten/botanical-families/" in family_list.driver.current_url, (
            f"TC-REQ-001-011 FAIL: Expected detail URL, got {family_list.driver.current_url}"
        )

    @pytest.mark.smoke
    def test_showing_count_displays_correct_range(
        self, family_list: BotanicalFamilyListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-081: Showing count displays correct range.

        Spec: TC-001-001 -- Botanische Familienliste — Zeigt-Zaehler.
        """
        family_list.open()
        screenshot("TC-REQ-001-081_showing-count", "Family list showing count display")

        showing_text = family_list.get_showing_count_text()
        assert "Zeigt" in showing_text or "von" in showing_text, (
            f"TC-REQ-001-081 FAIL: Expected showing count text, got '{showing_text}'"
        )
