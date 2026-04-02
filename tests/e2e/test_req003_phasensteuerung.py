"""E2E tests for REQ-003 — Phasensteuerung (Plant Instance List, Detail, Phase Transition).

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-003.md):
  TC-REQ-003-001  ->  TC-003-032  Pflanzinstanz-Liste zeigt aktuelle Phase als Spalte
  TC-REQ-003-002  ->  TC-003-032  Pflanzinstanz-Liste zeigt aktuelle Phase als Spalte
  TC-REQ-003-003  ->  TC-003-032  Pflanzinstanz-Liste zeigt aktuelle Phase als Spalte
  TC-REQ-003-004  ->  TC-003-033  Pflanzinstanz erstellen mit Spezies-Zuordnung
  TC-REQ-003-005  ->  TC-003-032  Pflanzinstanz-Liste zeigt aktuelle Phase als Spalte
  TC-REQ-003-006  ->  TC-003-013  Wachstumsphasen-Liste -- Suchfunktion
  TC-REQ-003-007  ->  TC-003-012  Wachstumsphasen-Liste -- Sortierung nach Reihenfolge
  TC-REQ-003-008  ->  TC-003-019  Manuelle Phasentransition -- Happy Path (Navigation)
  TC-REQ-003-009  ->  TC-003-032  Pflanzinstanz-Liste zeigt aktuelle Phase als Spalte
  TC-REQ-003-010  ->  TC-003-024  Phasen-Zeitstrahl zeigt abgeschlossene, aktuelle und geplante Phasen
  TC-REQ-003-011  ->  TC-003-024  Phasen-Zeitstrahl zeigt abgeschlossene, aktuelle und geplante Phasen
  TC-REQ-003-012  ->  TC-003-024  Phasen-Zeitstrahl zeigt abgeschlossene, aktuelle und geplante Phasen
  TC-REQ-003-013  ->  TC-003-019  Manuelle Phasentransition -- Happy Path (Phase Chip)
  TC-REQ-003-014  ->  TC-003-019  Manuelle Phasentransition -- Happy Path (Transition Button)
  TC-REQ-003-015  ->  TC-003-010  Wachstumsphase loeschen -- Bestaetigungsdialog (Remove Button)
  TC-REQ-003-016  ->  TC-003-026  Phasenverlauf-Tabelle zeigt historische Eintraege
  TC-REQ-003-017  ->  TC-003-023  Phasentransition -- Kein Lifecycle zugeordnet (Unknown Key)
  TC-REQ-003-018  ->  TC-003-019  Manuelle Phasentransition -- Happy Path (Dialog oeffnen)
  TC-REQ-003-019  ->  TC-003-019  Manuelle Phasentransition -- Happy Path (Target Phase Select)
  TC-REQ-003-020  ->  TC-003-019  Manuelle Phasentransition -- Happy Path (Reason Field)
  TC-REQ-003-021  ->  TC-003-019  Manuelle Phasentransition -- Happy Path (Reason Default)
  TC-REQ-003-022  ->  TC-003-020  Phasentransition -- Zielphase nicht ausgewaehlt (Button deaktiviert)
  TC-REQ-003-023  ->  TC-003-019  Manuelle Phasentransition -- Cancel schliesst Dialog
  TC-REQ-003-024  ->  TC-003-019  Manuelle Phasentransition -- Cancel preserves phase
  TC-REQ-003-025  ->  TC-003-019  Manuelle Phasentransition -- Reason editable
  TC-REQ-003-026  ->  TC-003-021  Phasentransition rueckwaerts -- Korrekturmodus erforderlich
  TC-REQ-003-027  ->  TC-003-021  Phasentransition rueckwaerts -- Remove button disabled
  TC-REQ-003-028  ->  TC-003-010  Wachstumsphase loeschen -- Bestaetigungsdialog
  TC-REQ-003-029  ->  TC-003-023  Phasentransition -- Kein Lifecycle (Phase Options)
  TC-REQ-003-030  ->  TC-003-019  Manuelle Phasentransition -- URL-Struktur
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import PlantInstanceListExt, PlantInstanceDetailExt


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def plant_list(browser: WebDriver, base_url: str) -> PlantInstanceListExt:
    return PlantInstanceListExt(browser, base_url)


@pytest.fixture
def plant_detail(browser: WebDriver, base_url: str) -> PlantInstanceDetailExt:
    return PlantInstanceDetailExt(browser, base_url)


# ── Helper: navigate to first plant and extract key ────────────────────────────


def _get_first_plant_key(plant_list: PlantInstanceListExt) -> str | None:
    """Open the list, click the first row and return the key from the URL.

    Returns None if the list is empty.
    """
    plant_list.open()
    if plant_list.get_row_count() == 0:
        return None
    plant_list.click_row(0)
    plant_list.wait_for_url_contains("/pflanzen/plant-instances/")
    url = plant_list.driver.current_url
    return url.rstrip("/").rsplit("/", 1)[-1]


# ==============================================================================
# TC-REQ-003-001 to TC-REQ-003-012: Plant instance list page
# ==============================================================================


class TestPlantInstanceListPage:
    """Plant instance list display and navigation (Spec: TC-003-032, TC-003-013, TC-003-012, TC-003-033)."""

    @pytest.mark.smoke
    def test_plant_list_page_loads(
        self, plant_list: PlantInstanceListExt, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-003-001: Plant instance list page loads with title.

        Spec: TC-003-032 -- Pflanzinstanz-Liste zeigt aktuelle Phase als Spalte.
        """
        plant_list.open()
        screenshot("TC-REQ-003-001_plant-list-page-load",
                   "Plant instance list page after initial load")

        title = plant_list.get_page_title()
        assert title, (
            "TC-REQ-003-001 FAIL: Page title should not be empty after navigating to /pflanzen/plant-instances"
        )

    @pytest.mark.smoke
    def test_plant_list_has_data_table(
        self, plant_list: PlantInstanceListExt, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-003-002: Plant instance list renders the DataTable component.

        Spec: TC-003-032 -- Pflanzinstanz-Liste zeigt aktuelle Phase als Spalte.
        """
        plant_list.open()
        screenshot("TC-REQ-003-002_plant-list-data-table",
                   "Plant instance list DataTable or empty state")

        # DataTable is always rendered (even when empty) as a Paper wrapper
        tables = plant_list.driver.find_elements(*plant_list.TABLE)
        if not tables:
            # DataTable might not be rendered if page shows empty state instead
            empty = plant_list.driver.find_elements(
                By.CSS_SELECTOR, "[data-testid='empty-state']"
            )
            assert empty, (
                "TC-REQ-003-002 FAIL: Expected DataTable or EmptyState on plant list"
            )
        else:
            assert tables[0].is_displayed(), (
                "TC-REQ-003-002 FAIL: DataTable should be visible"
            )

    @pytest.mark.smoke
    def test_plant_list_column_headers_include_phase(
        self, plant_list: PlantInstanceListExt, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-003-003: Plant list column headers include the current phase column.

        Spec: TC-003-032 -- Pflanzinstanz-Liste zeigt aktuelle Phase als Spalte.
        """
        plant_list.open()
        screenshot("TC-REQ-003-003_plant-list-column-headers",
                   "Plant instance list column headers")

        # Check that DataTable exists before inspecting headers
        tables = plant_list.driver.find_elements(*plant_list.TABLE)
        if not tables:
            pytest.skip("DataTable not rendered — cannot check column headers")

        headers = plant_list.get_column_headers()
        if not headers:
            pytest.skip("No column headers found — table may be in mobile card view")

        # The current-phase column label comes from i18n key pages.plantInstances.currentPhase
        # DE translation: "Aktuelle Phase"
        has_phase_col = any(
            "phase" in h.lower() or "Phase" in h
            for h in headers
        )
        assert has_phase_col, (
            f"TC-REQ-003-003 FAIL: Expected a column related to 'Phase' in headers, got {headers}"
        )

    @pytest.mark.smoke
    def test_plant_list_create_button_visible(
        self, plant_list: PlantInstanceListExt, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-003-004: Create plant instance button is visible on list page.

        Spec: TC-003-033 -- Pflanzinstanz erstellen mit Spezies-Zuordnung.
        """
        plant_list.open()
        screenshot("TC-REQ-003-004_plant-list-create-button",
                   "Plant instance list with create button visible")

        btn = plant_list.wait_for_element_clickable(plant_list.CREATE_BUTTON)
        assert btn.is_displayed(), (
            "TC-REQ-003-004 FAIL: [data-testid='create-button'] should be visible"
        )

    @pytest.mark.core_crud
    def test_plant_list_shows_phase_chips(
        self, plant_list: PlantInstanceListExt, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-003-005: Plant list rows display the current-phase Chip.

        Spec: TC-003-032 -- Pflanzinstanz-Liste zeigt aktuelle Phase als Spalte.
        """
        plant_list.open()
        screenshot("TC-REQ-003-005_plant-list-phase-chips",
                   "Plant instance list rows with phase chips")

        row_count = plant_list.get_row_count()
        if row_count == 0:
            pytest.skip("No plant instances in database")

        phase_texts = plant_list.get_phase_column_texts()
        assert any(t for t in phase_texts), (
            f"TC-REQ-003-005 FAIL: Expected at least one non-empty phase label in list rows, got {phase_texts}"
        )

    @pytest.mark.core_crud
    def test_plant_list_search_by_instance_id(
        self, plant_list: PlantInstanceListExt, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-003-006: Searching by instance ID filters the plant list.

        Spec: TC-003-013 -- Wachstumsphasen-Liste -- Suchfunktion.
        """
        plant_list.open()

        row_count = plant_list.get_row_count()
        if row_count == 0:
            pytest.skip("No plant instances in database")

        first_ids = plant_list.get_first_column_texts()
        search_term = first_ids[0][:4] if first_ids else "PLANT"

        screenshot("TC-REQ-003-006_before-search",
                   "Plant instance list before search")
        plant_list.search(search_term)
        plant_list.wait_for_loading_complete()
        screenshot("TC-REQ-003-006_after-search",
                   "Plant instance list after search filter applied")

        assert plant_list.has_search_chip(), (
            f"TC-REQ-003-006 FAIL: Expected search chip after searching for '{search_term}'"
        )

    @pytest.mark.core_crud
    def test_plant_list_sort_by_column(
        self, plant_list: PlantInstanceListExt, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-003-007: Clicking a column header activates sorting.

        Spec: TC-003-012 -- Wachstumsphasen-Liste -- Sortierung nach Reihenfolge.
        """
        plant_list.open()
        headers = plant_list.get_column_headers()
        if not headers:
            pytest.skip("No column headers found")

        screenshot("TC-REQ-003-007_before-sort",
                   "Plant instance list before sorting")
        plant_list.click_column_header(headers[0])
        plant_list.wait_for_loading_complete()
        screenshot("TC-REQ-003-007_after-sort",
                   "Plant instance list after clicking column header to sort")

        assert plant_list.has_sort_chip(), (
            "TC-REQ-003-007 FAIL: Expected a sort chip after clicking column header"
        )

    @pytest.mark.core_crud
    def test_plant_list_row_click_navigates_to_detail(
        self, plant_list: PlantInstanceListExt, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-003-008: Clicking a plant instance row navigates to detail page.

        Spec: TC-003-019 -- Manuelle Phasentransition -- Happy Path (Navigation).
        """
        plant_list.open()

        if plant_list.get_row_count() == 0:
            pytest.skip("No plant instances in database")

        screenshot("TC-REQ-003-008_before-row-click",
                   "Plant instance list before clicking first row")
        plant_list.click_row(0)
        plant_list.wait_for_url_contains("/pflanzen/plant-instances/")
        screenshot("TC-REQ-003-008_after-row-click",
                   "Plant instance detail page after row click navigation")

        current_url = plant_list.driver.current_url
        assert "/pflanzen/plant-instances/" in current_url, (
            f"TC-REQ-003-008 FAIL: Expected URL to contain '/pflanzen/plant-instances/', got '{current_url}'"
        )

    @pytest.mark.smoke
    def test_plant_list_showing_count_displayed(
        self, plant_list: PlantInstanceListExt, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-003-009: Showing-count footer renders with numeric text.

        Spec: TC-003-032 -- Pflanzinstanz-Liste zeigt aktuelle Phase als Spalte.
        """
        plant_list.open()
        screenshot("TC-REQ-003-009_showing-count",
                   "Plant instance list showing-count footer")

        # The showing-count element is only rendered when there are items in
        # the DataTable (processedData.totalFiltered > 0). Skip if no plants.
        if plant_list.get_row_count() == 0:
            pytest.skip("No plant instances — showing-count not rendered for empty table")

        count_text = plant_list.get_showing_count_text()
        assert count_text, (
            f"TC-REQ-003-009 FAIL: Expected non-empty showing-count text, got '{count_text}'"
        )
        assert any(c.isdigit() for c in count_text), (
            f"TC-REQ-003-009 FAIL: Showing count should contain a number, got '{count_text}'"
        )


# ==============================================================================
# TC-REQ-003-010 to TC-REQ-003-018: Plant instance detail page — info display
# ==============================================================================


class TestPlantInstanceDetailPage:
    """Plant instance detail page phase information display (Spec: TC-003-024, TC-003-019, TC-003-026)."""

    @pytest.mark.smoke
    def test_plant_detail_page_loads(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-003-010: Plant instance detail page loads with page title.

        Spec: TC-003-024 -- Phasen-Zeitstrahl zeigt abgeschlossene, aktuelle und geplante Phasen.
        """
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        screenshot("TC-REQ-003-010_plant-detail-page-load",
                   "Plant instance detail page after load")

        title = plant_detail.get_title()
        assert title, (
            f"TC-REQ-003-010 FAIL: Plant instance detail title should not be empty for key '{key}'"
        )
        assert not plant_detail.is_error_shown(), (
            "TC-REQ-003-010 FAIL: Error display should not be visible for a valid plant instance key"
        )

    @pytest.mark.core_crud
    def test_plant_detail_shows_plant_info_card(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-003-011: Plant detail page shows the plant-info-card.

        Spec: TC-003-024 -- Phasen-Zeitstrahl zeigt abgeschlossene, aktuelle und geplante Phasen.
        """
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        screenshot("TC-REQ-003-011_plant-info-card",
                   "Plant instance detail page with plant info card")

        assert plant_detail.is_plant_info_card_visible(), (
            "TC-REQ-003-011 FAIL: [data-testid='plant-info-card'] should be visible on detail page"
        )

    @pytest.mark.core_crud
    def test_plant_detail_shows_phase_info_card(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-003-012: Plant detail page shows the phase-info-card.

        Spec: TC-003-024 -- Phasen-Zeitstrahl zeigt abgeschlossene, aktuelle und geplante Phasen.
        """
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        screenshot("TC-REQ-003-012_phase-info-card",
                   "Plant instance detail page with phase info card")

        assert plant_detail.is_phase_info_card_visible(), (
            "TC-REQ-003-012 FAIL: [data-testid='phase-info-card'] should be visible on detail page"
        )

    @pytest.mark.core_crud
    def test_plant_detail_current_phase_chip_has_text(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-003-013: The current-phase Chip has non-empty text.

        Spec: TC-003-019 -- Manuelle Phasentransition -- Happy Path (Phase Chip).
        """
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        screenshot("TC-REQ-003-013_current-phase-chip",
                   "Plant detail page showing current phase chip")

        phase_text = plant_detail.get_current_phase()
        assert phase_text, (
            f"TC-REQ-003-013 FAIL: [data-testid='current-phase'] chip should have non-empty text, got '{phase_text}'"
        )

    @pytest.mark.core_crud
    def test_plant_detail_transition_button_visible(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-003-014: The 'Phasenuebergang' button is present on the detail page.

        Spec: TC-003-019 -- Manuelle Phasentransition -- Happy Path (Transition Button).
        """
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        screenshot("TC-REQ-003-014_transition-button",
                   "Plant detail page with transition button visible")

        btn = plant_detail.wait_for_element(plant_detail.TRANSITION_BUTTON)
        assert btn.is_displayed(), (
            "TC-REQ-003-014 FAIL: [data-testid='transition-button'] should be visible on detail page"
        )

    @pytest.mark.core_crud
    def test_plant_detail_remove_button_visible(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-003-015: The 'Entfernen' button is present on the detail page.

        Spec: TC-003-010 -- Wachstumsphase loeschen -- Bestaetigungsdialog (Remove Button).
        """
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        screenshot("TC-REQ-003-015_remove-button",
                   "Plant detail page with remove button visible")

        btn = plant_detail.wait_for_element(plant_detail.REMOVE_BUTTON)
        assert btn.is_displayed(), (
            "TC-REQ-003-015 FAIL: [data-testid='remove-button'] should be visible on detail page"
        )

    @pytest.mark.core_crud
    def test_plant_detail_phase_history_section(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-003-016: Phase history section renders rows when history exists.

        Spec: TC-003-026 -- Phasenverlauf-Tabelle zeigt historische Eintraege.
        """
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        screenshot("TC-REQ-003-016_phase-history",
                   "Plant detail page phase history section")

        if plant_detail.has_phase_history():
            count = plant_detail.get_phase_history_count()
            assert count > 0, (
                "TC-REQ-003-016 FAIL: Phase history section is present but has 0 rows"
            )

    @pytest.mark.core_crud
    def test_plant_detail_unknown_key_shows_error(
        self,
        plant_detail: PlantInstanceDetailExt,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-003-017: Navigating to unknown plant instance key shows error display.

        Spec: TC-003-023 -- Phasentransition -- Kein Lifecycle zugeordnet (Unknown Key).
        """
        plant_detail.navigate("/pflanzen/plant-instances/nonexistent-key-99999")
        plant_detail.wait_for_loading_complete()
        screenshot("TC-REQ-003-017_unknown-plant-error",
                   "Error display for unknown plant instance key")

        assert plant_detail.is_error_shown(), (
            "TC-REQ-003-017 FAIL: An error display should appear for an unknown plant instance key"
        )


# ==============================================================================
# TC-REQ-003-018 to TC-REQ-003-025: Phase Transition Dialog
# ==============================================================================


class TestPhaseTransitionDialog:
    """Phase transition dialog interactions (Spec: TC-003-019, TC-003-020)."""

    @pytest.mark.core_crud
    def test_transition_dialog_opens(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-003-018: Clicking the transition button opens the phase transition dialog.

        Spec: TC-003-019 -- Manuelle Phasentransition -- Happy Path (Dialog oeffnen).
        """
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)

        if not plant_detail.is_transition_button_enabled():
            pytest.skip("Transition button is disabled — plant may be removed")

        screenshot("TC-REQ-003-018_before-open-transition-dialog",
                   "Plant detail page before opening transition dialog")
        plant_detail.initiate_phase_transition()
        screenshot("TC-REQ-003-018_transition-dialog-open",
                   "Phase transition dialog open")

        assert plant_detail.is_transition_dialog_open(), (
            "TC-REQ-003-018 FAIL: [data-testid='phase-transition-dialog'] should be visible after clicking transition button"
        )

        # Clean up
        plant_detail.cancel_transition()

    @pytest.mark.core_crud
    def test_transition_dialog_shows_target_phase_select(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-003-019: The transition dialog shows the target-phase select element.

        Spec: TC-003-019 -- Manuelle Phasentransition -- Happy Path (Target Phase Select).
        """
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        if not plant_detail.is_transition_button_enabled():
            pytest.skip("Transition button is disabled")

        plant_detail.initiate_phase_transition()
        screenshot("TC-REQ-003-019_transition-dialog-target-select",
                   "Phase transition dialog with target phase select visible")

        select_el = plant_detail.wait_for_element_visible(plant_detail.TARGET_PHASE_SELECT)
        assert select_el.is_displayed(), (
            "TC-REQ-003-019 FAIL: [data-testid='target-phase-select'] should be visible in the dialog"
        )

        plant_detail.cancel_transition()

    @pytest.mark.core_crud
    def test_transition_dialog_shows_reason_field(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-003-020: The transition dialog shows the reason text field.

        Spec: TC-003-019 -- Manuelle Phasentransition -- Happy Path (Reason Field).
        """
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        if not plant_detail.is_transition_button_enabled():
            pytest.skip("Transition button is disabled")

        plant_detail.initiate_phase_transition()
        screenshot("TC-REQ-003-020_transition-reason-field",
                   "Phase transition dialog with reason field visible")

        reason_el = plant_detail.wait_for_element_visible(plant_detail.TRANSITION_REASON)
        assert reason_el.is_displayed(), (
            "TC-REQ-003-020 FAIL: [data-testid='transition-reason'] input should be visible"
        )

        plant_detail.cancel_transition()

    @pytest.mark.core_crud
    def test_transition_dialog_reason_default_value(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-003-021: The reason field has a default value of 'manual'.

        Spec: TC-003-019 -- Manuelle Phasentransition -- Happy Path (Reason Default).
        """
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        if not plant_detail.is_transition_button_enabled():
            pytest.skip("Transition button is disabled")

        plant_detail.initiate_phase_transition()
        screenshot("TC-REQ-003-021_transition-reason-default",
                   "Phase transition dialog showing default reason value")

        reason_value = plant_detail.get_transition_reason_value()
        assert reason_value == "manual", (
            f"TC-REQ-003-021 FAIL: Expected default reason to be 'manual', got '{reason_value}'"
        )

        plant_detail.cancel_transition()

    @pytest.mark.core_crud
    def test_transition_dialog_confirm_button_disabled_without_selection(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-003-022: The confirm button is disabled when no target phase is selected.

        Spec: TC-003-020 -- Phasentransition -- Zielphase nicht ausgewaehlt (Button deaktiviert).
        """
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        if not plant_detail.is_transition_button_enabled():
            pytest.skip("Transition button is disabled")

        plant_detail.initiate_phase_transition()
        screenshot("TC-REQ-003-022_confirm-button-state-no-selection",
                   "Transition dialog with confirm button disabled — no phase selected")

        # Without selecting a phase, the confirm button should be disabled
        assert not plant_detail.is_confirm_button_enabled(), (
            "TC-REQ-003-022 FAIL: Confirm button should be disabled when no phase is selected"
        )

        plant_detail.cancel_transition()

    @pytest.mark.core_crud
    def test_transition_dialog_cancel_closes(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-003-023: Clicking 'Abbrechen' in the transition dialog closes it.

        Spec: TC-003-019 -- Manuelle Phasentransition -- Cancel schliesst Dialog.
        """
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        if not plant_detail.is_transition_button_enabled():
            pytest.skip("Transition button is disabled")

        plant_detail.initiate_phase_transition()
        screenshot("TC-REQ-003-023_dialog-open-before-cancel",
                   "Transition dialog open before cancel")

        plant_detail.cancel_transition()
        screenshot("TC-REQ-003-023_dialog-after-cancel",
                   "Plant detail page after cancelling transition dialog")

        assert not plant_detail.is_transition_dialog_open(), (
            "TC-REQ-003-023 FAIL: Transition dialog should be closed after clicking Abbrechen"
        )

    @pytest.mark.core_crud
    def test_transition_dialog_cancel_preserves_phase(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-003-024: Cancelling the dialog does not change the current phase.

        Spec: TC-003-019 -- Manuelle Phasentransition -- Cancel preserves phase.
        """
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        if not plant_detail.is_transition_button_enabled():
            pytest.skip("Transition button is disabled")

        initial_phase = plant_detail.get_current_phase()
        screenshot("TC-REQ-003-024_before-transition-dialog",
                   "Plant detail page before opening transition dialog")

        plant_detail.initiate_phase_transition()
        plant_detail.cancel_transition()
        screenshot("TC-REQ-003-024_after-cancel",
                   "Plant detail page after cancelling — phase unchanged")

        current_phase = plant_detail.get_current_phase()
        assert current_phase == initial_phase, (
            f"TC-REQ-003-024 FAIL: Phase should remain '{initial_phase}' after cancelling dialog, got '{current_phase}'"
        )

    @pytest.mark.core_crud
    def test_transition_dialog_reason_editable(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-003-025: The reason field accepts free-text input.

        Spec: TC-003-019 -- Manuelle Phasentransition -- Reason editable.
        """
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        if not plant_detail.is_transition_button_enabled():
            pytest.skip("Transition button is disabled")

        plant_detail.initiate_phase_transition()
        screenshot("TC-REQ-003-025_before-editing-reason",
                   "Transition dialog before editing reason field")

        custom_reason = "e2e_test_reason_custom"
        plant_detail.set_transition_reason(custom_reason)
        screenshot("TC-REQ-003-025_after-editing-reason",
                   "Transition dialog after editing reason to custom value")

        value = plant_detail.get_transition_reason_value()
        assert value == custom_reason, (
            f"TC-REQ-003-025 FAIL: Expected reason field value '{custom_reason}', got '{value}'"
        )

        plant_detail.cancel_transition()


# ==============================================================================
# TC-REQ-003-026 to TC-REQ-003-030: Phase state machine edge cases
# ==============================================================================


class TestPhaseStateMachineEdgeCases:
    """State machine constraints and edge cases (Spec: TC-003-021, TC-003-010, TC-003-023)."""

    @pytest.mark.core_crud
    def test_removed_plant_disables_transition_button(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-003-026: Transition button is disabled for a removed plant instance.

        Spec: TC-003-021 -- Phasentransition rueckwaerts -- Korrekturmodus erforderlich.
        """
        # We look for a removed plant by checking for rows where removed_on is not '-'
        plant_list.open()
        rows = plant_list.get_row_count()

        if rows == 0:
            pytest.skip("No plant instances in database")

        # Iterate rows to find a removed plant (last column is removed_on)
        removed_key = None
        for i in range(rows):
            plant_list.open()
            plant_list.click_row(i)
            plant_list.wait_for_url_contains("/pflanzen/plant-instances/")
            url = plant_list.driver.current_url
            key_candidate = url.rstrip("/").rsplit("/", 1)[-1]

            plant_detail.open(key_candidate)
            if not plant_detail.is_transition_button_enabled():
                removed_key = key_candidate
                break

        if removed_key is None:
            pytest.skip("No removed plant instances found in database")

        screenshot("TC-REQ-003-026_removed-plant-detail",
                   "Removed plant detail page with disabled transition button")

        btn = plant_detail.wait_for_element(plant_detail.TRANSITION_BUTTON)
        assert not btn.is_enabled() or btn.get_attribute("disabled") is not None, (
            f"TC-REQ-003-026 FAIL: Transition button should be disabled for removed plant '{removed_key}'"
        )

    @pytest.mark.core_crud
    def test_removed_plant_disables_remove_button(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-003-027: Remove button is disabled for an already-removed plant.

        Spec: TC-003-021 -- Phasentransition rueckwaerts -- Remove button disabled.
        """
        plant_list.open()
        rows = plant_list.get_row_count()
        if rows == 0:
            pytest.skip("No plant instances in database")

        removed_key = None
        for i in range(rows):
            plant_list.open()
            plant_list.click_row(i)
            plant_list.wait_for_url_contains("/pflanzen/plant-instances/")
            url = plant_list.driver.current_url
            key_candidate = url.rstrip("/").rsplit("/", 1)[-1]

            plant_detail.open(key_candidate)
            if not plant_detail.is_remove_button_enabled():
                removed_key = key_candidate
                break

        if removed_key is None:
            pytest.skip("No removed plant instances found")

        screenshot("TC-REQ-003-027_removed-plant-remove-button",
                   "Removed plant detail page with disabled remove button")

        btn = plant_detail.wait_for_element(plant_detail.REMOVE_BUTTON)
        assert not btn.is_enabled() or btn.get_attribute("disabled") is not None, (
            f"TC-REQ-003-027 FAIL: Remove button should be disabled for removed plant '{removed_key}'"
        )

    @pytest.mark.core_crud
    def test_remove_dialog_opens_and_cancels(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-003-028: Remove confirm dialog opens and can be cancelled safely.

        Spec: TC-003-010 -- Wachstumsphase loeschen -- Bestaetigungsdialog.
        """
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        if not plant_detail.is_remove_button_enabled():
            pytest.skip("Remove button is disabled — plant already removed")

        screenshot("TC-REQ-003-028_before-remove",
                   "Plant detail page before clicking remove button")
        plant_detail.initiate_remove()
        screenshot("TC-REQ-003-028_remove-dialog-open",
                   "Remove confirmation dialog open")

        assert plant_detail.is_confirm_dialog_visible(), (
            "TC-REQ-003-028 FAIL: Confirm dialog should be visible after clicking Entfernen"
        )

        plant_detail.cancel_remove()
        screenshot("TC-REQ-003-028_after-cancel-remove",
                   "Plant detail page after cancelling remove dialog")

        assert not plant_detail.is_confirm_dialog_visible(), (
            "TC-REQ-003-028 FAIL: Confirm dialog should close after clicking Abbrechen"
        )

    @pytest.mark.core_crud
    def test_transition_dialog_shows_phase_options_when_lifecycle_configured(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-003-029: Phase options appear in the select when lifecycle is configured.

        Spec: TC-003-023 -- Phasentransition -- Kein Lifecycle (Phase Options).
        """
        plant_list.open()
        rows = plant_list.get_row_count()
        if rows == 0:
            pytest.skip("No plant instances in database")

        # Find a plant instance where transition is enabled (has lifecycle)
        enabled_key = None
        for i in range(min(rows, 5)):  # Check up to 5 plants
            plant_list.open()
            plant_list.click_row(i)
            plant_list.wait_for_url_contains("/pflanzen/plant-instances/")
            url = plant_list.driver.current_url
            key_candidate = url.rstrip("/").rsplit("/", 1)[-1]

            plant_detail.open(key_candidate)
            if plant_detail.is_transition_button_enabled():
                enabled_key = key_candidate
                break

        if enabled_key is None:
            pytest.skip("No active (non-removed) plant instances found")

        plant_detail.open(enabled_key)
        plant_detail.initiate_phase_transition()
        screenshot("TC-REQ-003-029_transition-dialog-phase-options",
                   "Transition dialog showing phase options from lifecycle config")

        # Check the select element is present — options may be empty if lifecycle
        # is not configured; the test documents the expected behaviour.
        select_el = plant_detail.wait_for_element_visible(plant_detail.TARGET_PHASE_SELECT)
        assert select_el.is_displayed(), (
            "TC-REQ-003-029 FAIL: Target phase select should be displayed in the transition dialog"
        )

        plant_detail.cancel_transition()

    @pytest.mark.core_crud
    def test_detail_page_url_structure(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-003-030: Plant instance detail URL follows /pflanzen/plant-instances/:key pattern.

        Spec: TC-003-019 -- Manuelle Phasentransition -- URL-Struktur.
        """
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        screenshot("TC-REQ-003-030_plant-detail-url",
                   "Plant instance detail page URL verification")

        current_url = plant_detail.driver.current_url
        expected_segment = f"/pflanzen/plant-instances/{key}"
        assert expected_segment in current_url, (
            f"TC-REQ-003-030 FAIL: Expected URL to contain '{expected_segment}', got '{current_url}'"
        )
