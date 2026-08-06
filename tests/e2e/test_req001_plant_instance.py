"""E2E tests for REQ-001 / REQ-003 — Plant Instance (Pflanzen) management.

Spec-TC Mapping (test TC -> spec/e2e-testcases/):
  TC-REQ-001-PI-001  ->  TC-001-082   Plant instance list page renders with data-testid
  TC-REQ-001-PI-002  ->  TC-001-083   List displays DataTable with column headers
  TC-REQ-001-PI-003  ->  TC-001-084   Create button is visible on list page
  TC-REQ-001-PI-003b ->  TC-001-085   Showing count text is displayed when rows exist
  TC-REQ-001-PI-004  ->  TC-001-086   Create dialog opens on button click
  TC-REQ-001-PI-005  ->  TC-001-080   Create plant instance with valid data (Happy Path;
                                      shares the Core-Journey creation case -- this test
                                      exercises a narrower slice of the same behaviour)
  TC-REQ-001-PI-006  ->  TC-001-087   Submit without species shows validation error
  TC-REQ-001-PI-007  ->  TC-001-088   Cancel closes dialog without creating
  TC-REQ-001-PI-008  ->  TC-001-089   Click on row navigates to detail page
  TC-REQ-001-PI-009  ->  TC-001-090   Detail page shows plant-info-card
  TC-REQ-001-PI-010  ->  TC-001-091   Detail page shows current phase
  TC-REQ-001-PI-011  ->  TC-001-092   Phases tab shows phase history
  TC-REQ-001-PI-012  ->  TC-001-093   Search filters plant instance table
  TC-REQ-001-PI-013  ->  TC-001-094   Sort by column header shows sort chip
  TC-REQ-001-PI-014  ->  TC-001-095   Non-existent plant-instance key shows error
  TC-REQ-001-PI-015  ->  TC-001-096   Reset filters restores the full list

Of the 16 tests below, only PI-005 maps onto an already-declared case (TC-001-080,
the Core-Journey creation happy path); the spec previously described no generic
list-page/dialog/detail-page rendering behaviour for plant instances at all
(Gruppe 21 only covers the self-provisioning journey's data-correctness
assertions), so TC-001-082 through TC-001-096 were newly declared in
spec/e2e-testcases/TC-REQ-001.md (Gruppe 22) rather than guessed from the
numeric "TC-REQ-001-PI-NNN -> TC-001-NNN" coincidence.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.plant_instance_detail_page import PlantInstanceDetailPage
from .pages.plant_instance_list_page import PlantInstanceListPage

# Feature-axis marker(s) for machine-selectable test identification
# (see conftest.py::KNOWN_FEATURE_MARKERS / pytest -m <feature>).
FEATURES = ("plant",)


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def plant_list(browser: WebDriver, base_url: str) -> PlantInstanceListPage:
    """Return a PlantInstanceListPage bound to the test browser."""
    return PlantInstanceListPage(browser, base_url)


@pytest.fixture
def plant_detail(browser: WebDriver, base_url: str) -> PlantInstanceDetailPage:
    """Return a PlantInstanceDetailPage bound to the test browser."""
    return PlantInstanceDetailPage(browser, base_url)


# -- TC-001-082 to TC-001-085: List Page --------------------------------------


class TestPlantInstanceListPage:
    """Plant instance list display and interactions (REQ-001)."""

    @pytest.mark.smoke
    def test_list_page_renders_with_correct_testid(
        self,
        plant_list: PlantInstanceListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-001-082: PlantInstanceListPage renders with data-testid.

        Spec: TC-001-082 -- Pflanzeninstanz-Liste wird geladen und angezeigt.
        """
        plant_list.open()
        screenshot(
            "TC-REQ-001-PI-001_plant-instance-list-loaded",
            "Plant instance list page after initial load",
        )

        page_el = plant_list.wait_for_element(PlantInstanceListPage.PAGE)
        assert page_el.is_displayed(), (
            "TC-REQ-001-PI-001 FAIL: Expected [data-testid='plant-instance-list-page'] "
            "to be visible"
        )

    @pytest.mark.requires_desktop
    @pytest.mark.smoke
    def test_list_displays_data_table_with_columns(
        self,
        plant_list: PlantInstanceListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-001-083: DataTable renders with expected column headers.

        Spec: TC-001-083 -- Pflanzeninstanz-Liste zeigt Tabellenspalten.
        """
        plant_list.open()
        screenshot(
            "TC-REQ-001-PI-002_plant-table-columns",
            "Plant instance table column headers",
        )

        headers = plant_list.get_column_headers()
        if len(headers) == 0:
            pytest.skip("No plant instances in database — empty state shown instead of DataTable")
        assert len(headers) >= 2, (
            f"TC-REQ-001-PI-002 FAIL: Expected at least 2 column headers, got: {headers}"
        )

    @pytest.mark.smoke
    def test_create_button_is_visible_on_list_page(
        self,
        plant_list: PlantInstanceListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-001-084: Create button is visible on the list page.

        Spec: TC-001-084 -- Erstellen-Button ist auf der Pflanzeninstanz-Liste sichtbar.
        """
        plant_list.open()
        screenshot(
            "TC-REQ-001-PI-003_create-button",
            "Create button visible on plant instance list",
        )

        btn = plant_list.wait_for_element(PlantInstanceListPage.CREATE_BUTTON)
        assert btn.is_displayed(), (
            "TC-REQ-001-PI-003 FAIL: Expected [data-testid='create-button'] to be visible"
        )

    @pytest.mark.core_crud
    def test_showing_count_text_is_present(
        self,
        plant_list: PlantInstanceListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-001-085: Showing count text is displayed when rows exist.

        Spec: TC-001-085 -- Zaehler "Zeigt X von Y" wird bei vorhandenen
        Pflanzeninstanzen angezeigt.
        """
        plant_list.open()
        screenshot(
            "TC-REQ-001-PI-003b_showing-count",
            "Plant instance list showing count",
        )

        if plant_list.get_row_count() == 0:
            pytest.skip("No rows — showing count not displayed for empty table")

        count_text = plant_list.get_showing_count_text()
        assert count_text, "TC-REQ-001-PI-003b FAIL: Expected non-empty showing count text"


# -- TC-001-086 to TC-001-088: Create Dialog ----------------------------------


class TestPlantInstanceCreateDialog:
    """Plant instance create dialog operations (REQ-001)."""

    @pytest.mark.core_crud
    def test_create_dialog_opens_on_button_click(
        self,
        plant_list: PlantInstanceListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-001-086: Clicking create button opens the PlantInstanceCreateDialog.

        Spec: TC-001-086 -- Erstellen-Dialog fuer Pflanzeninstanz oeffnet sich per Klick.
        """
        plant_list.open()
        screenshot(
            "TC-REQ-001-PI-004_before-open-dialog",
            "Plant list before opening create dialog",
        )

        plant_list.click_create()
        screenshot(
            "TC-REQ-001-PI-004_dialog-open",
            "Plant instance create dialog opened",
        )

        assert plant_list.is_create_dialog_open(), (
            "TC-REQ-001-PI-004 FAIL: Expected PlantInstanceCreateDialog to be open"
        )

    @pytest.mark.core_crud
    def test_create_plant_instance_happy_path(
        self,
        plant_list: PlantInstanceListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-001-080: Create a plant instance with species + name (Happy Path).

        Spec: TC-001-080 -- Core-Journey: Pflanzeninstanz anlegen und in Liste
        verifizieren. This test exercises the same create-dialog-happy-path
        behaviour as the Core-Journey case with a first-available species
        rather than a self-provisioned one; the case is shared rather than
        duplicated (many-to-one is expected, see the module's docstring
        traceability check).
        Selects the first available species via the autocomplete, enters a
        unique plant name, and verifies the new entry appears in the list.
        """
        plant_list.open()
        initial_count = plant_list.get_row_count()
        screenshot(
            "TC-REQ-001-PI-005_before-create",
            "Plant list before creating",
        )

        plant_list.click_create()
        screenshot(
            "TC-REQ-001-PI-005_dialog-open",
            "Plant instance create dialog opened",
        )

        # Select the first species from the autocomplete by typing a space
        # to trigger the dropdown, then clicking the first option.
        plant_list.select_species("a")

        unique_name = f"E2E-Pflanze-{int(time.time())}"
        plant_list.fill_plant_name(unique_name)

        screenshot(
            "TC-REQ-001-PI-005_form-filled",
            "Plant create form filled before submit",
        )

        # instance_id should have been auto-generated
        instance_id = plant_list.get_instance_id_value()
        assert instance_id, "TC-REQ-001-PI-005 FAIL: Expected instance_id to be auto-generated"

        plant_list.submit_create_form()
        # Two post-conditions replacing a `wait_for_loading_complete()` that was
        # only ever worth the ~3 s the implicit wait charged for its empty
        # lookup. Without that pause the reads below landed *inside* the list's
        # own refetch — `onCreated` dispatches `fetchPlantInstances({})`, which
        # empties `rows` while the request is in flight — and the test reported
        # `final: 0, names: []`: it blamed the create for a table that was
        # merely mid-request (#835).
        #
        # The dialog closing proves the POST resolved; re-opening the list then
        # reads a page that fetched from scratch. `open()`'s own
        # `wait_for_loading_complete` *is* meaningful after a full navigation,
        # where the skeleton reliably mounts — unlike after a client-side
        # mutation, where it may never appear at all.
        plant_list.wait_for_create_dialog_closed()
        plant_list.open()
        screenshot(
            "TC-REQ-001-PI-005_after-create",
            "Plant list after creation",
        )

        final_count = plant_list.get_row_count()
        names = plant_list.get_first_column_texts()
        assert final_count > initial_count or unique_name in names, (
            f"TC-REQ-001-PI-005 FAIL: Expected new plant '{unique_name}' to appear. "
            f"Initial: {initial_count}, final: {final_count}, names: {names}"
        )

    @pytest.mark.core_crud
    def test_submit_without_species_shows_validation_error(
        self,
        plant_list: PlantInstanceListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-001-087: Submitting without species triggers validation error (NFR-006).

        Spec: TC-001-087 -- Pflanzeninstanz erstellen: Pflichtfeld "Art" leer
        wird verhindert.
        """
        plant_list.open()
        plant_list.click_create()
        screenshot(
            "TC-REQ-001-PI-006_dialog-open-empty",
            "Create dialog with no species selected",
        )

        plant_list.submit_create_form()
        plant_list.wait_for_loading_complete()
        screenshot(
            "TC-REQ-001-PI-006_validation-error",
            "Validation error for missing species",
        )

        # Dialog should remain open because the form did not pass validation
        assert plant_list.is_create_dialog_open(), (
            "TC-REQ-001-PI-006 FAIL: Expected dialog to remain open when species is empty"
        )
        plant_list.cancel_create_form()

    @pytest.mark.core_crud
    def test_cancel_closes_dialog_without_creating(
        self,
        plant_list: PlantInstanceListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-001-088: Cancel in create dialog closes without saving.

        Spec: TC-001-088 -- Abbrechen im Pflanzeninstanz-Erstellen-Dialog
        verwirft die Eingabe.
        """
        plant_list.open()
        initial_count = plant_list.get_row_count()

        plant_list.click_create()
        screenshot(
            "TC-REQ-001-PI-007_before-cancel",
            "Create dialog before cancel",
        )

        plant_list.cancel_create_form()
        plant_list.wait_for_loading_complete()
        screenshot(
            "TC-REQ-001-PI-007_after-cancel",
            "Plant list after cancelling dialog",
        )

        assert not plant_list.is_create_dialog_open(), (
            "TC-REQ-001-PI-007 FAIL: Expected create dialog to be closed after cancel"
        )
        final_count = plant_list.get_row_count()
        assert final_count == initial_count, (
            f"TC-REQ-001-PI-007 FAIL: Expected row count to stay {initial_count}, got {final_count}"
        )


# -- TC-001-089 to TC-001-092: Detail Page ------------------------------------


class TestPlantInstanceDetailPage:
    """Plant instance detail page rendering (REQ-001, REQ-003)."""

    @pytest.mark.core_crud
    def test_click_row_navigates_to_detail(
        self,
        plant_list: PlantInstanceListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-001-089: Clicking a row navigates to the detail page.

        Spec: TC-001-089 -- Klick auf Zeile navigiert zur
        Pflanzeninstanz-Detailseite.
        """
        plant_list.open()
        screenshot(
            "TC-REQ-001-PI-008_before-row-click",
            "Plant list before row click",
        )

        if plant_list.get_row_count() == 0:
            pytest.skip("No plant instances — cannot test row click navigation")

        plant_list.click_row(0)
        plant_list.wait_for_url_contains("/pflanzen/plant-instances/")
        screenshot(
            "TC-REQ-001-PI-008_after-row-click",
            "Plant instance detail after row click",
        )

        assert "/pflanzen/plant-instances/" in plant_list.driver.current_url, (
            f"TC-REQ-001-PI-008 FAIL: Expected detail URL after row click, "
            f"got: {plant_list.driver.current_url}"
        )

    @pytest.mark.core_crud
    def test_detail_page_shows_plant_info_card(
        self,
        plant_list: PlantInstanceListPage,
        plant_detail: PlantInstanceDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-001-090: Detail page renders the plant-info-card.

        Spec: TC-001-090 -- Pflanzeninstanz-Detailseite zeigt Pflanzeninfo-Karte.
        """
        plant_list.open()

        if plant_list.get_row_count() == 0:
            pytest.skip("No plant instances — cannot test detail page")

        plant_list.click_row(0)
        plant_list.wait_for_url_contains("/pflanzen/plant-instances/")

        info_card = plant_detail.get_plant_info_card()
        screenshot(
            "TC-REQ-001-PI-009_plant-info-card",
            "Plant instance detail page with info card",
        )

        assert info_card.is_displayed(), (
            "TC-REQ-001-PI-009 FAIL: Expected [data-testid='plant-info-card'] to be visible"
        )

    @pytest.mark.core_crud
    def test_detail_page_shows_current_phase(
        self,
        plant_list: PlantInstanceListPage,
        plant_detail: PlantInstanceDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-001-091: Detail page shows the current phase chip (REQ-003).

        Spec: TC-001-091 -- Pflanzeninstanz-Detailseite zeigt aktuelle Phase.
        """
        plant_list.open()

        if plant_list.get_row_count() == 0:
            pytest.skip("No plant instances — cannot test current phase display")

        plant_list.click_row(0)
        plant_list.wait_for_url_contains("/pflanzen/plant-instances/")

        phase_text = plant_detail.get_current_phase()
        screenshot(
            "TC-REQ-001-PI-010_current-phase",
            "Plant instance detail showing current phase",
        )

        assert phase_text, "TC-REQ-001-PI-010 FAIL: Expected non-empty current phase text"

    @pytest.mark.core_crud
    def test_phases_tab_shows_phase_history(
        self,
        plant_list: PlantInstanceListPage,
        plant_detail: PlantInstanceDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-001-092: Phases tab renders the phase history (REQ-003).

        Spec: TC-001-092 -- Tab "Phasen" zeigt Phasenverlauf der
        Pflanzeninstanz.
        """
        plant_list.open()

        if plant_list.get_row_count() == 0:
            pytest.skip("No plant instances — cannot test phase history")

        plant_list.click_row(0)
        plant_list.wait_for_url_contains("/pflanzen/plant-instances/")

        # Click on the Phases tab (index 1 in the tab bar)
        phases_tab = plant_detail.wait_for_element_clickable(PlantInstanceDetailPage.PHASES_TAB)
        plant_detail.scroll_and_click(phases_tab)
        screenshot(
            "TC-REQ-001-PI-011_phases-tab",
            "Plant instance phases tab with history",
        )

        phases_content = plant_detail.wait_for_element(PlantInstanceDetailPage.PHASES_TAB_CONTENT)
        assert phases_content.is_displayed(), (
            "TC-REQ-001-PI-011 FAIL: Expected phases tab content to be visible"
        )


# -- TC-001-093 to TC-001-096: Search, Sort, Error ----------------------------


class TestPlantInstanceSearchAndSort:
    """Plant instance search, sort, and error handling (REQ-001, NFR-006)."""

    @pytest.mark.core_crud
    def test_search_filters_plant_instances(
        self,
        plant_list: PlantInstanceListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-001-093: Search input filters the plant instance table.

        Spec: TC-001-093 -- Suchfeld filtert die Pflanzeninstanz-Tabelle.
        """
        plant_list.open()

        if plant_list.get_row_count() == 0:
            pytest.skip("No plant instances — cannot test search")

        initial_count = plant_list.get_row_count()
        screenshot(
            "TC-REQ-001-PI-012_before-search",
            "Plant list before search",
        )

        plant_list.search("ZZZ_NONEXISTENT_PLANT_9999")
        plant_list.wait_for_loading_complete()
        screenshot(
            "TC-REQ-001-PI-012_after-search",
            "Plant list after search — no results expected",
        )

        filtered_count = plant_list.get_row_count()
        assert filtered_count <= initial_count, (
            f"TC-REQ-001-PI-012 FAIL: Expected filtered count ({filtered_count}) "
            f"<= initial ({initial_count})"
        )
        assert plant_list.has_search_chip(), (
            "TC-REQ-001-PI-012 FAIL: Expected search chip to be visible"
        )

    @pytest.mark.requires_desktop
    @pytest.mark.core_crud
    def test_sort_by_column_shows_sort_chip(
        self,
        plant_list: PlantInstanceListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-001-094: Clicking a column header activates the sort chip.

        Spec: TC-001-094 -- Sortierung per Spaltenklick zeigt Sortier-Chip.
        """
        plant_list.open()
        headers = plant_list.get_column_headers()
        # `requires_desktop` already guarantees the table layout, so an empty
        # header list here does not mean "card layout" -- it means the table did
        # not render, which is a defect this test used to swallow as a skip
        # (#778 A6).
        assert headers, (
            "TEST FAIL: Expected column headers on a desktop viewport, but the table rendered none"
        )

        screenshot(
            "TC-REQ-001-PI-013_before-sort",
            "Plant list before sorting",
        )
        plant_list.click_column_header(headers[0])
        plant_list.wait_for_loading_complete()
        screenshot(
            "TC-REQ-001-PI-013_after-sort",
            "Plant list after column sort",
        )

        assert plant_list.has_sort_chip(), (
            f"TC-REQ-001-PI-013 FAIL: Expected sort chip after clicking "
            f"column header '{headers[0]}'"
        )

    @pytest.mark.core_crud
    def test_nonexistent_plant_instance_shows_error(
        self,
        plant_detail: PlantInstanceDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-001-095: Navigating to a non-existent key shows an error (NFR-006).

        Spec: TC-001-095 -- Ungueltige Pflanzeninstanz-ID zeigt Fehleranzeige.
        """
        plant_detail.open("NONEXISTENT-PLANT-KEY-99999")
        screenshot(
            "TC-REQ-001-PI-014_nonexistent-plant",
            "Error state for non-existent plant instance key",
        )

        assert plant_detail.is_error_displayed(), (
            "TC-REQ-001-PI-014 FAIL: Expected error display for non-existent plant key"
        )

    @pytest.mark.core_crud
    def test_reset_filters_restores_full_list(
        self,
        plant_list: PlantInstanceListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-001-096: Reset filters restores the full plant instance list.

        Spec: TC-001-096 -- Filter zuruecksetzen stellt die volle
        Pflanzeninstanz-Liste wieder her.
        """
        plant_list.open()

        if plant_list.get_row_count() == 0:
            pytest.skip("No plant instances — cannot test filter reset")

        initial_count = plant_list.get_row_count()
        plant_list.search("A")
        plant_list.wait_for_loading_complete()

        if plant_list.has_reset_filters_button():
            plant_list.click_reset_filters()
            plant_list.wait_for_loading_complete()
            screenshot(
                "TC-REQ-001-PI-015_after-reset",
                "Plant list after filter reset",
            )
            reset_count = plant_list.get_row_count()
            assert reset_count >= initial_count - 1, (
                f"TC-REQ-001-PI-015 FAIL: Expected count after reset ({reset_count}) "
                f"close to initial ({initial_count})"
            )
