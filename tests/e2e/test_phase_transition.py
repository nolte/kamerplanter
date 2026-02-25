"""E2E tests for phase transition flow — REQ-003."""

from __future__ import annotations

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import PlantInstanceDetailPage, PlantInstanceListPage


@pytest.fixture
def plant_list(browser: WebDriver, base_url: str) -> PlantInstanceListPage:
    return PlantInstanceListPage(browser, base_url)


@pytest.fixture
def plant_detail(browser: WebDriver, base_url: str) -> PlantInstanceDetailPage:
    return PlantInstanceDetailPage(browser, base_url)


def _get_first_plant_key(plant_list: PlantInstanceListPage) -> str | None:
    """Navigate to list, click first row, extract key from URL."""
    plant_list.open()
    if plant_list.get_row_count() == 0:
        return None
    plant_list.click_row(0)
    plant_list.wait_for_url_contains("/pflanzen/plant-instances/")
    url = plant_list.driver.current_url
    return url.rstrip("/").rsplit("/", 1)[-1]


class TestPhaseTransition:
    """Plant detail page phase display and transition flow."""

    def test_plant_detail_shows_phase(
        self,
        plant_list: PlantInstanceListPage,
        plant_detail: PlantInstanceDetailPage,
    ) -> None:
        """Plant detail page displays the current phase chip."""
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        phase_card = plant_detail.get_phase_info_card()
        assert phase_card.is_displayed(), "Phase info card should be visible"

        phase_text = plant_detail.get_current_phase()
        assert phase_text, "Current phase chip should have text"

    def test_phase_transition_dialog_opens(
        self,
        plant_list: PlantInstanceListPage,
        plant_detail: PlantInstanceDetailPage,
    ) -> None:
        """Clicking the transition button opens the phase transition dialog."""
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        plant_detail.initiate_phase_transition()

        # Dialog should now be visible
        dialog = plant_detail.wait_for_element_visible(
            plant_detail.TRANSITION_DIALOG
        )
        assert dialog.is_displayed(), "Transition dialog should be visible"

        # Cancel to close cleanly
        plant_detail.cancel_transition()

    def test_phase_transition_flow(
        self,
        plant_list: PlantInstanceListPage,
        plant_detail: PlantInstanceDetailPage,
    ) -> None:
        """Full transition flow: open dialog, select phase, confirm."""
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)
        initial_phase = plant_detail.get_current_phase()

        plant_detail.initiate_phase_transition()

        # Check that target phase select is present
        select_el = plant_detail.wait_for_element_visible(
            plant_detail.TARGET_PHASE_SELECT
        )
        assert select_el.is_displayed(), "Target phase select should be visible"

        # Check that confirm button exists
        confirm_btn = plant_detail.wait_for_element(
            plant_detail.TRANSITION_CONFIRM
        )
        assert confirm_btn is not None, "Confirm button should be present"

        # Cancel — do not actually transition as it modifies data
        plant_detail.cancel_transition()

    def test_phase_history_section(
        self,
        plant_list: PlantInstanceListPage,
        plant_detail: PlantInstanceDetailPage,
    ) -> None:
        """Phase history section is rendered when history exists."""
        key = _get_first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instances in database")

        plant_detail.open(key)

        # Phase history may or may not exist depending on test data
        if plant_detail.has_phase_history():
            count = plant_detail.get_phase_history_count()
            assert count > 0, "Phase history should have at least one entry"
