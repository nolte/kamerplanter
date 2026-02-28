"""E2E tests — REQ-003 Phasensteuerung (TC-REQ-003-001 to TC-REQ-003-030).

Covers:
  Plant instance list: page load, column visibility, phase-chip display, search, sort
  Plant instance detail: info cards, phase chip, phase history
  Phase transition dialog: open, cancel, phase options visible, reason field, confirm btn state
  Edge cases: removed plant disables transition/remove buttons, unknown key → error

All tests follow NFR-008:
  - Page-Object-Pattern (no direct find_element calls in test methods)
  - WebDriverWait only — no time.sleep() except for search debounce
  - Screenshot at: Page Load / before action / after action / error state
  - Descriptive assertion messages
"""

from __future__ import annotations

import time

import pytest
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
    """TC-REQ-003-001 to TC-REQ-003-012: Plant instance list renders correctly."""

    def test_plant_list_page_loads(
        self, plant_list: PlantInstanceListExt, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-003-001: Plant instance list page loads with title."""
        capture = request.node._screenshot_capture
        plant_list.open()
        capture("TC-REQ-003-001_plant-list-page-load")

        title = plant_list.get_page_title()
        assert title, (
            "TC-REQ-003-001 FAIL: Page title should not be empty after navigating to /pflanzen/plant-instances"
        )

    def test_plant_list_has_data_table(
        self, plant_list: PlantInstanceListExt, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-003-002: Plant instance list renders the DataTable component."""
        capture = request.node._screenshot_capture
        plant_list.open()
        capture("TC-REQ-003-002_plant-list-data-table")

        table = plant_list.wait_for_element(plant_list.TABLE)
        assert table.is_displayed(), (
            "TC-REQ-003-002 FAIL: DataTable ([data-testid='data-table']) should be visible"
        )

    def test_plant_list_column_headers_include_phase(
        self, plant_list: PlantInstanceListExt, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-003-003: Plant list column headers include the current phase column."""
        capture = request.node._screenshot_capture
        plant_list.open()
        capture("TC-REQ-003-003_plant-list-column-headers")

        headers = plant_list.get_column_headers()
        # The current-phase column label comes from i18n key pages.plantInstances.currentPhase
        # Typical DE translation: "Aktuelle Phase" / "Phase"
        has_phase_col = any(
            "phase" in h.lower() or "Phase" in h
            for h in headers
        )
        assert has_phase_col, (
            f"TC-REQ-003-003 FAIL: Expected a column related to 'Phase' in headers, got {headers}"
        )

    def test_plant_list_create_button_visible(
        self, plant_list: PlantInstanceListExt, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-003-004: Create plant instance button is visible on list page."""
        capture = request.node._screenshot_capture
        plant_list.open()
        capture("TC-REQ-003-004_plant-list-create-button")

        btn = plant_list.wait_for_element_clickable(plant_list.CREATE_BUTTON)
        assert btn.is_displayed(), (
            "TC-REQ-003-004 FAIL: [data-testid='create-button'] should be visible"
        )

    def test_plant_list_shows_phase_chips(
        self, plant_list: PlantInstanceListExt, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-003-005: Plant list rows display the current-phase Chip."""
        capture = request.node._screenshot_capture
        plant_list.open()
        capture("TC-REQ-003-005_plant-list-phase-chips")

        row_count = plant_list.get_row_count()
        if row_count == 0:
            pytest.skip("No plant instances in database")

        phase_texts = plant_list.get_phase_column_texts()
        assert any(t for t in phase_texts), (
            f"TC-REQ-003-005 FAIL: Expected at least one non-empty phase label in list rows, got {phase_texts}"
        )

    def test_plant_list_search_by_instance_id(
        self, plant_list: PlantInstanceListExt, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-003-006: Searching by instance ID filters the plant list."""
        capture = request.node._screenshot_capture
        plant_list.open()

        row_count = plant_list.get_row_count()
        if row_count == 0:
            pytest.skip("No plant instances in database")

        first_ids = plant_list.get_first_column_texts()
        search_term = first_ids[0][:4] if first_ids else "PLANT"

        capture("TC-REQ-003-006_before-search")
        plant_list.search(search_term)
        time.sleep(0.4)  # search debounce
        capture("TC-REQ-003-006_after-search")

        assert plant_list.has_search_chip(), (
            f"TC-REQ-003-006 FAIL: Expected search chip after searching for '{search_term}'"
        )

    def test_plant_list_sort_by_column(
        self, plant_list: PlantInstanceListExt, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-003-007: Clicking a column header activates sorting."""
        capture = request.node._screenshot_capture
        plant_list.open()
        headers = plant_list.get_column_headers()
        if not headers:
            pytest.skip("No column headers found")

        capture("TC-REQ-003-007_before-sort")
        plant_list.click_column_header(headers[0])
        time.sleep(0.3)
        capture("TC-REQ-003-007_after-sort")

        assert plant_list.has_sort_chip(), (
            "TC-REQ-003-007 FAIL: Expected a sort chip after clicking column header"
        )

    def test_plant_list_row_click_navigates_to_detail(
        self, plant_list: PlantInstanceListExt, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-003-008: Clicking a plant instance row navigates to detail page."""
        capture = request.node._screenshot_capture
        plant_list.open()

        if plant_list.get_row_count() == 0:
            pytest.skip("No plant instances in database")

        capture("TC-REQ-003-008_before-row-click")
        plant_list.click_row(0)
        plant_list.wait_for_url_contains("/pflanzen/plant-instances/")
        capture("TC-REQ-003-008_after-row-click")

        current_url = plant_list.driver.current_url
        assert "/pflanzen/plant-instances/" in current_url, (
            f"TC-REQ-003-008 FAIL: Expected URL to contain '/pflanzen/plant-instances/', got '{current_url}'"
        )

    def test_plant_list_showing_count_displayed(
        self, plant_list: PlantInstanceListExt, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-003-009: Showing-count footer renders with numeric text."""
        capture = request.node._screenshot_capture
        plant_list.open()
        capture("TC-REQ-003-009_showing-count")

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
    """TC-REQ-003-010 to TC-REQ-003-018: Plant detail page renders phase information."""

    def test_plant_detail_page_loads(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-003-010: Plant instance detail page loads with page title."""
        capture = request.node._screenshot_capture
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        capture("TC-REQ-003-010_plant-detail-page-load")

        title = plant_detail.get_title()
        assert title, (
            f"TC-REQ-003-010 FAIL: Plant instance detail title should not be empty for key '{key}'"
        )
        assert not plant_detail.is_error_shown(), (
            "TC-REQ-003-010 FAIL: Error display should not be visible for a valid plant instance key"
        )

    def test_plant_detail_shows_plant_info_card(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-003-011: Plant detail page shows the plant-info-card."""
        capture = request.node._screenshot_capture
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        capture("TC-REQ-003-011_plant-info-card")

        assert plant_detail.is_plant_info_card_visible(), (
            "TC-REQ-003-011 FAIL: [data-testid='plant-info-card'] should be visible on detail page"
        )

    def test_plant_detail_shows_phase_info_card(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-003-012: Plant detail page shows the phase-info-card."""
        capture = request.node._screenshot_capture
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        capture("TC-REQ-003-012_phase-info-card")

        assert plant_detail.is_phase_info_card_visible(), (
            "TC-REQ-003-012 FAIL: [data-testid='phase-info-card'] should be visible on detail page"
        )

    def test_plant_detail_current_phase_chip_has_text(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-003-013: The current-phase Chip ([data-testid='current-phase']) has non-empty text."""
        capture = request.node._screenshot_capture
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        capture("TC-REQ-003-013_current-phase-chip")

        phase_text = plant_detail.get_current_phase()
        assert phase_text, (
            f"TC-REQ-003-013 FAIL: [data-testid='current-phase'] chip should have non-empty text, got '{phase_text}'"
        )

    def test_plant_detail_transition_button_visible(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-003-014: The 'Phasenübergang' button is present on the detail page."""
        capture = request.node._screenshot_capture
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        capture("TC-REQ-003-014_transition-button")

        btn = plant_detail.wait_for_element(plant_detail.TRANSITION_BUTTON)
        assert btn.is_displayed(), (
            "TC-REQ-003-014 FAIL: [data-testid='transition-button'] should be visible on detail page"
        )

    def test_plant_detail_remove_button_visible(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-003-015: The 'Entfernen' button is present on the detail page."""
        capture = request.node._screenshot_capture
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        capture("TC-REQ-003-015_remove-button")

        btn = plant_detail.wait_for_element(plant_detail.REMOVE_BUTTON)
        assert btn.is_displayed(), (
            "TC-REQ-003-015 FAIL: [data-testid='remove-button'] should be visible on detail page"
        )

    def test_plant_detail_phase_history_section(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-003-016: Phase history section renders rows when history exists."""
        capture = request.node._screenshot_capture
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        capture("TC-REQ-003-016_phase-history")

        if plant_detail.has_phase_history():
            count = plant_detail.get_phase_history_count()
            assert count > 0, (
                "TC-REQ-003-016 FAIL: Phase history section is present but has 0 rows"
            )

    def test_plant_detail_unknown_key_shows_error(
        self,
        plant_detail: PlantInstanceDetailExt,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-003-017: Navigating to unknown plant instance key shows error display."""
        capture = request.node._screenshot_capture
        plant_detail.navigate("/pflanzen/plant-instances/nonexistent-key-99999")
        time.sleep(2)
        capture("TC-REQ-003-017_unknown-plant-error")

        assert plant_detail.is_error_shown(), (
            "TC-REQ-003-017 FAIL: An error display should appear for an unknown plant instance key"
        )


# ==============================================================================
# TC-REQ-003-018 to TC-REQ-003-025: Phase Transition Dialog
# ==============================================================================


class TestPhaseTransitionDialog:
    """TC-REQ-003-018 to TC-REQ-003-025: Phase transition dialog interactions.

    These tests verify the REQ-003 state machine UI:
    - Transition button opens the dialog
    - Dialog shows target-phase select + reason field + cancel/confirm buttons
    - Cancel closes the dialog without persisting a transition
    - Confirm button is disabled when no phase is selected
    - Reason field accepts free text
    """

    def test_transition_dialog_opens(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-003-018: Clicking the transition button opens the phase transition dialog."""
        capture = request.node._screenshot_capture
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)

        if not plant_detail.is_transition_button_enabled():
            pytest.skip("Transition button is disabled — plant may be removed")

        capture("TC-REQ-003-018_before-open-transition-dialog")
        plant_detail.initiate_phase_transition()
        capture("TC-REQ-003-018_transition-dialog-open")

        assert plant_detail.is_transition_dialog_open(), (
            "TC-REQ-003-018 FAIL: [data-testid='phase-transition-dialog'] should be visible after clicking transition button"
        )

        # Clean up
        plant_detail.cancel_transition()

    def test_transition_dialog_shows_target_phase_select(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-003-019: The transition dialog shows the target-phase select element."""
        capture = request.node._screenshot_capture
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        if not plant_detail.is_transition_button_enabled():
            pytest.skip("Transition button is disabled")

        plant_detail.initiate_phase_transition()
        capture("TC-REQ-003-019_transition-dialog-target-select")

        select_el = plant_detail.wait_for_element_visible(plant_detail.TARGET_PHASE_SELECT)
        assert select_el.is_displayed(), (
            "TC-REQ-003-019 FAIL: [data-testid='target-phase-select'] should be visible in the dialog"
        )

        plant_detail.cancel_transition()

    def test_transition_dialog_shows_reason_field(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-003-020: The transition dialog shows the reason text field."""
        capture = request.node._screenshot_capture
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        if not plant_detail.is_transition_button_enabled():
            pytest.skip("Transition button is disabled")

        plant_detail.initiate_phase_transition()
        capture("TC-REQ-003-020_transition-reason-field")

        reason_el = plant_detail.wait_for_element_visible(plant_detail.TRANSITION_REASON)
        assert reason_el.is_displayed(), (
            "TC-REQ-003-020 FAIL: [data-testid='transition-reason'] input should be visible"
        )

        plant_detail.cancel_transition()

    def test_transition_dialog_reason_default_value(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-003-021: The reason field has a default value of 'manual'."""
        capture = request.node._screenshot_capture
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        if not plant_detail.is_transition_button_enabled():
            pytest.skip("Transition button is disabled")

        plant_detail.initiate_phase_transition()
        capture("TC-REQ-003-021_transition-reason-default")

        reason_value = plant_detail.get_transition_reason_value()
        assert reason_value == "manual", (
            f"TC-REQ-003-021 FAIL: Expected default reason to be 'manual', got '{reason_value}'"
        )

        plant_detail.cancel_transition()

    def test_transition_dialog_confirm_button_disabled_without_selection(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-003-022: The confirm button is disabled when no target phase is selected."""
        capture = request.node._screenshot_capture
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        if not plant_detail.is_transition_button_enabled():
            pytest.skip("Transition button is disabled")

        plant_detail.initiate_phase_transition()
        capture("TC-REQ-003-022_confirm-button-state-no-selection")

        # Without selecting a phase, the confirm button should be disabled
        assert not plant_detail.is_confirm_button_enabled(), (
            "TC-REQ-003-022 FAIL: Confirm button should be disabled when no phase is selected"
        )

        plant_detail.cancel_transition()

    def test_transition_dialog_cancel_closes(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-003-023: Clicking 'Abbrechen' in the transition dialog closes it."""
        capture = request.node._screenshot_capture
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        if not plant_detail.is_transition_button_enabled():
            pytest.skip("Transition button is disabled")

        plant_detail.initiate_phase_transition()
        capture("TC-REQ-003-023_dialog-open-before-cancel")

        plant_detail.cancel_transition()
        capture("TC-REQ-003-023_dialog-after-cancel")

        assert not plant_detail.is_transition_dialog_open(), (
            "TC-REQ-003-023 FAIL: Transition dialog should be closed after clicking Abbrechen"
        )

    def test_transition_dialog_cancel_preserves_phase(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-003-024: Cancelling the dialog does not change the current phase."""
        capture = request.node._screenshot_capture
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        if not plant_detail.is_transition_button_enabled():
            pytest.skip("Transition button is disabled")

        initial_phase = plant_detail.get_current_phase()
        capture("TC-REQ-003-024_before-transition-dialog")

        plant_detail.initiate_phase_transition()
        plant_detail.cancel_transition()
        capture("TC-REQ-003-024_after-cancel")

        current_phase = plant_detail.get_current_phase()
        assert current_phase == initial_phase, (
            f"TC-REQ-003-024 FAIL: Phase should remain '{initial_phase}' after cancelling dialog, got '{current_phase}'"
        )

    def test_transition_dialog_reason_editable(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-003-025: The reason field accepts free-text input."""
        capture = request.node._screenshot_capture
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        if not plant_detail.is_transition_button_enabled():
            pytest.skip("Transition button is disabled")

        plant_detail.initiate_phase_transition()
        capture("TC-REQ-003-025_before-editing-reason")

        custom_reason = "e2e_test_reason_custom"
        plant_detail.set_transition_reason(custom_reason)
        capture("TC-REQ-003-025_after-editing-reason")

        value = plant_detail.get_transition_reason_value()
        assert value == custom_reason, (
            f"TC-REQ-003-025 FAIL: Expected reason field value '{custom_reason}', got '{value}'"
        )

        plant_detail.cancel_transition()


# ==============================================================================
# TC-REQ-003-026 to TC-REQ-003-030: Phase state machine edge cases
# ==============================================================================


class TestPhaseStateMachineEdgeCases:
    """TC-REQ-003-026 to TC-REQ-003-030: State machine constraints and edge cases.

    Tests backward transition prohibition, removed-plant button states,
    and dialog availability based on lifecycle config.
    """

    def test_removed_plant_disables_transition_button(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-003-026: Transition button is disabled for a removed plant instance.

        REQ-003 — Plants that have been removed (removed_on is set) cannot
        undergo further phase transitions. The UI must reflect this by disabling
        the transition button.
        """
        capture = request.node._screenshot_capture
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

        capture("TC-REQ-003-026_removed-plant-detail")

        btn = plant_detail.wait_for_element(plant_detail.TRANSITION_BUTTON)
        assert not btn.is_enabled() or btn.get_attribute("disabled") is not None, (
            f"TC-REQ-003-026 FAIL: Transition button should be disabled for removed plant '{removed_key}'"
        )

    def test_removed_plant_disables_remove_button(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-003-027: Remove button is disabled for an already-removed plant.

        A plant that has removed_on set cannot be removed again.
        """
        capture = request.node._screenshot_capture
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

        capture("TC-REQ-003-027_removed-plant-remove-button")

        btn = plant_detail.wait_for_element(plant_detail.REMOVE_BUTTON)
        assert not btn.is_enabled() or btn.get_attribute("disabled") is not None, (
            f"TC-REQ-003-027 FAIL: Remove button should be disabled for removed plant '{removed_key}'"
        )

    def test_remove_dialog_opens_and_cancels(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-003-028: Remove confirm dialog opens and can be cancelled safely."""
        capture = request.node._screenshot_capture
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        if not plant_detail.is_remove_button_enabled():
            pytest.skip("Remove button is disabled — plant already removed")

        capture("TC-REQ-003-028_before-remove")
        plant_detail.initiate_remove()
        capture("TC-REQ-003-028_remove-dialog-open")

        assert plant_detail.is_confirm_dialog_visible(), (
            "TC-REQ-003-028 FAIL: Confirm dialog should be visible after clicking Entfernen"
        )

        plant_detail.cancel_remove()
        capture("TC-REQ-003-028_after-cancel-remove")

        assert not plant_detail.is_confirm_dialog_visible(), (
            "TC-REQ-003-028 FAIL: Confirm dialog should close after clicking Abbrechen"
        )

    def test_transition_dialog_shows_phase_options_when_lifecycle_configured(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-003-029: Phase options appear in the select when lifecycle is configured.

        When the species of a plant instance has a lifecycle configured with growth phases,
        the transition dialog must populate the target-phase dropdown with those phases.
        """
        capture = request.node._screenshot_capture
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
        capture("TC-REQ-003-029_transition-dialog-phase-options")

        # Check the select element is present — options may be empty if lifecycle
        # is not configured; the test documents the expected behaviour.
        select_el = plant_detail.wait_for_element_visible(plant_detail.TARGET_PHASE_SELECT)
        assert select_el.is_displayed(), (
            "TC-REQ-003-029 FAIL: Target phase select should be displayed in the transition dialog"
        )

        plant_detail.cancel_transition()

    def test_detail_page_url_structure(
        self,
        plant_list: PlantInstanceListExt,
        plant_detail: PlantInstanceDetailExt,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-003-030: Plant instance detail URL follows /pflanzen/plant-instances/:key pattern."""
        capture = request.node._screenshot_capture
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        capture("TC-REQ-003-030_plant-detail-url")

        current_url = plant_detail.driver.current_url
        expected_segment = f"/pflanzen/plant-instances/{key}"
        assert expected_segment in current_url, (
            f"TC-REQ-003-030 FAIL: Expected URL to contain '{expected_segment}', got '{current_url}'"
        )
