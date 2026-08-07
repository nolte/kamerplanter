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

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import BotanicalFamilyListPage


@pytest.fixture
def family_list(browser: WebDriver, base_url: str) -> BotanicalFamilyListPage:
    return BotanicalFamilyListPage(browser, base_url)


class TestBotanicalFamilyListPage:
    """Botanical Family list operations (Spec: TC-001-001, TC-001-002, TC-001-003, TC-001-005)."""

    @pytest.mark.requires_desktop
    @pytest.mark.smoke
    def test_display_families_in_data_table(
        self, family_list: BotanicalFamilyListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-001-001: Display botanical families in a data table.

        Spec: TC-001-001 -- Botanische Familienliste wird vollstaendig geladen und angezeigt.
        """
        family_list.open()
        screenshot(
            "TC-REQ-001-006_family-list-loaded", "Botanical family list page after initial load"
        )

        headers = family_list.get_column_headers()

        assert "Name" in headers, f"TC-REQ-001-006 FAIL: Expected 'Name' column, got {headers}"
        assert any("Name" in h for h in headers), (
            f"TC-REQ-001-006 FAIL: Expected 'Gebraeuchlicher Name' column, got {headers}"
        )
        assert any("hrstoffbedarf" in h for h in headers), (
            f"TC-REQ-001-006 FAIL: Expected 'Naehrstoffbedarf', got {headers}"
        )

        row_count = family_list.get_row_count()
        assert row_count > 0, "TC-REQ-001-006 FAIL: Expected at least one family row (seed data)"

    @pytest.mark.core_crud
    def test_search_families_by_name(
        self, family_list: BotanicalFamilyListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-001-003: Search botanical families by name.

        Spec: TC-001-003 -- Suchfunktion in Botanische Familien-Liste.
        """
        family_list.open()
        family_list.search("Solan")  # debounce handled inside the page object

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
        """TC-001-003: Search botanical families by translated enum value.

        Spec: TC-001-003 -- Suchfunktion — Suche nach uebersetztem Enum-Wert.
        """
        family_list.open()
        family_list.search("Starkzehrer")  # debounce handled inside the page object

        screenshot("TC-REQ-001-008_enum-search", "Family list after searching for 'Starkzehrer'")

        row_count = family_list.get_row_count()
        assert row_count > 0, (
            "TC-REQ-001-008 FAIL: Expected at least one family matching 'Starkzehrer'"
        )

    @pytest.mark.requires_desktop
    @pytest.mark.core_crud
    def test_sort_families_by_column(
        self, family_list: BotanicalFamilyListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-001-002: Sort botanical families by column.

        Spec: TC-001-002 -- Tabelle sortieren nach Naehrstoffbedarf.
        """
        family_list.open()
        names_before = family_list.get_first_column_texts()
        if len(names_before) < 2:
            pytest.skip("Sorting is only observable with at least two rows")

        family_list.click_column_header("Name")
        family_list.wait_for_loading_complete()

        screenshot("TC-REQ-001-009_after-sort", "Family list after sorting by Name column")

        assert family_list.has_sort_chip(), (
            "TC-REQ-001-009 FAIL: Expected sort chip after clicking column header"
        )
        # The chip alone says nothing about the data: sorting could be entirely
        # broken and this test stayed green (#802). The page is already sorted
        # by Name ascending (`defaultSort`), so clicking that header toggles the
        # direction and the visible order has to change -- either reversed on a
        # single page, or a different slice once the 50-row page size bites.
        names_after = family_list.get_first_column_texts()
        assert names_after != names_before, (
            "TC-REQ-001-009 FAIL: Clicking the Name header changed nothing about the row order, "
            f"so no sort was applied: {names_before[:5]}"
        )

    @pytest.mark.core_crud
    def test_reset_all_filters(
        self, family_list: BotanicalFamilyListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-001-003: Reset all filters in botanical families table.

        Spec: TC-001-003 -- Suchfunktion — Filter zuruecksetzen.
        """
        family_list.open()
        term = "Fabaceae"
        names_before = family_list.get_first_column_texts()
        # The arrange has to be verified, not assumed: with no family outside the
        # term's own match set there is nothing for the reset to restore, and
        # every assertion below would hold for a reset button that does nothing.
        assert [n for n in names_before if term.lower() not in n.lower()], (
            f"TC-REQ-001-010 FAIL: The unfiltered family list must contain at least "
            f"one family that {term!r} excludes, otherwise this test cannot tell a "
            f"working reset from a broken one. It lists {names_before!r}."
        )

        family_list.search(term)  # typing only; the 300 ms sleep inside is a bet
        # …and this is the check that bet needs: the chip is rendered in the same
        # commit that recomputes the filtered rows, so nothing read before it is
        # a statement about the filter.
        family_list.wait_for_search_applied(term, what="botanical family list")
        names_filtered = family_list.get_first_column_texts()
        screenshot("TC-REQ-001-010_filtered", "Family list filtered by 'Fabaceae'")

        # `filtered_count <= initial_count` was satisfied by a filter that does
        # nothing at all -- every one of the rows staying put holds it (#956).
        # `name` is the only searchable column that can carry this term (the
        # others hold common names, translated enum labels and a species count),
        # so the filtered list must name Fabaceae and nothing else.
        assert names_filtered and all(term.lower() in n.lower() for n in names_filtered), (
            f"TC-REQ-001-010 FAIL: Filtering by {term!r} must leave only families "
            f"whose name carries it, but the list reads {names_filtered!r} (it held "
            f"{len(names_before)} rows before). The chip already carries the term, so "
            f"the filter has run -- a surviving row that does not name Fabaceae means "
            f"`processedData` matched it through another column."
        )

        family_list.click_reset_filters()
        # The chip disappears in the same commit that recomputes the *unfiltered*
        # rows, so it is the post-condition of the reset. `wait_for_loading_complete()`,
        # which stood here, polls a skeleton that a client-side reset never mounts.
        family_list.wait_for_element_hidden(family_list.SEARCH_CHIP)
        screenshot("TC-REQ-001-010_after-reset", "Family list after resetting all filters")

        # `reset_count >= filtered_count` is satisfied by a reset that does
        # nothing: the filtered list is a subset of the full one, so the count
        # can only rise. What the reset claims is that the rows the *filter*
        # removed are listed again -- read by name, not counted.
        names_after = family_list.get_first_column_texts()
        restored = [n for n in names_after if term.lower() not in n.lower()]
        assert restored, (
            f"TC-REQ-001-010 FAIL: After resetting the filters the list must name "
            f"families again that {term!r} excluded, but every one of the "
            f"{len(names_after)} rows still carries the term: {names_after!r}. The "
            f"chip is gone, so `tableState.search` is empty and the table re-rendered "
            f"-- the rows it re-rendered are still the filtered ones."
        )

    @pytest.mark.smoke
    def test_click_row_navigates_to_detail(
        self, family_list: BotanicalFamilyListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-001-005: Click on a botanical family row navigates to detail page.

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
        """TC-001-001: Showing count displays correct range.

        Spec: TC-001-001 -- Botanische Familienliste — Zeigt-Zaehler.
        """
        family_list.open()
        screenshot("TC-REQ-001-081_showing-count", "Family list showing count display")

        showing_text = family_list.get_showing_count_text()
        assert "Zeigt" in showing_text or "von" in showing_text, (
            f"TC-REQ-001-081 FAIL: Expected showing count text, got '{showing_text}'"
        )
