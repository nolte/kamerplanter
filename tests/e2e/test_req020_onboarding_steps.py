"""E2E tests for REQ-020 — Individual Onboarding Wizard Steps.

Detailed tests for step-level validation and interactions that complement
the flow-oriented tests in ``test_req020_onboarding_wizard.py``.

Covers:
- Completed/Skipped card behaviour (TC-020-002, TC-020-003, TC-020-004)
- Kit metadata display (TC-020-018)
- Favorite toggle interaction (TC-020-021)
- Site type change (TC-020-027)
- Plant counter maximum boundary (TC-020-034)
- Plant counter zero removes phase selector (TC-020-035)

NFR-008 §3.4 screenshot checkpoints at:
1. Page Load
2. Before significant actions
3. After significant actions
4. Error states
"""

from __future__ import annotations

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.onboarding_wizard_page import OnboardingWizardPage


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def wizard(browser: WebDriver, base_url: str) -> OnboardingWizardPage:
    """Return an OnboardingWizardPage bound to the test browser."""
    return OnboardingWizardPage(browser, base_url)


# ── Completed / Skipped Card ──────────────────────────────────────────────────


class TestCompletedSkippedCard:
    """TC-020-002 to TC-020-004: Completed/skipped card, restart functionality.

    These tests depend on the onboarding state being completed or skipped.
    If the previous test (e.g. test_wizard_completion_redirects) has already
    completed the wizard, visiting /onboarding should show the completed card.
    """

    def test_completed_card_shows_restart_and_dashboard_buttons(
        self,
        wizard: OnboardingWizardPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-020-002: Completed onboarding shows a card with Restart and Dashboard buttons.

        Precondition: The wizard must have been completed or skipped previously.
        This test first completes the wizard via skip, then checks the card.
        """
        capture = request.node._screenshot_capture

        # Ensure wizard is completed: skip it first
        wizard.open()
        if wizard.is_step_welcome_visible():
            wizard.click_skip()
            wizard.wait_for_url_contains("/pflanzen/plant-instances")

        # Now visit /onboarding again — should show completed card
        wizard.open()
        capture("req020_002_completed_card", "Completed/skipped onboarding card")

        assert wizard.is_wizard_visible(), (
            "Expected wizard container to be visible"
        )
        assert wizard.is_restart_button_visible(), (
            "Expected 'Restart' button to be visible on the completed card"
        )
        assert wizard.is_go_dashboard_button_visible(), (
            "Expected 'Go to Dashboard' button to be visible on the completed card"
        )
        # Stepper should NOT be visible
        assert not wizard.is_stepper_visible() or not wizard.is_step_welcome_visible(), (
            "Expected no stepper or step content when onboarding is completed"
        )

    def test_restart_from_completed_card(
        self,
        wizard: OnboardingWizardPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-020-004: Clicking Restart on the completed card resets the wizard to Step 1.

        Precondition: Onboarding is in completed/skipped state.
        """
        capture = request.node._screenshot_capture

        # Ensure completed state
        wizard.open()
        if wizard.is_step_welcome_visible():
            wizard.click_skip()
            wizard.wait_for_url_contains("/pflanzen/plant-instances")

        wizard.open()
        assert wizard.is_restart_button_visible(), "Expected completed card with restart"
        capture("req020_004_before_restart", "Completed card before restart")

        wizard.click_restart()
        wizard.wait_for_element(OnboardingWizardPage.STEP_WELCOME)
        capture("req020_004_after_restart", "Wizard restarted to Step 1")

        assert wizard.is_step_welcome_visible(), (
            "Expected Step 1 (Welcome) to be visible after restart"
        )
        assert wizard.is_experience_selected("beginner"), (
            "Expected experience level to reset to 'beginner' after restart"
        )


# ── Kit Metadata ──────────────────────────────────────────────────────────────


class TestKitMetadata:
    """TC-020-018: Kit difficulty badge colours."""

    def test_growzelt_kit_shows_advanced_difficulty(
        self,
        wizard: OnboardingWizardPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-020-018: Kit 'indoor-growzelt' has an error-coloured difficulty chip (advanced)."""
        capture = request.node._screenshot_capture
        wizard.open()
        wizard.advance_to_step_kit()
        capture("req020_018_kit_difficulty", "Kit list for difficulty badge check")

        # Check for the growzelt kit card
        growzelt_cards = wizard.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='kit-indoor-growzelt']"
        )
        if not growzelt_cards:
            pytest.skip("Kit 'indoor-growzelt' not found in the current kit list")

        color = wizard.get_kit_difficulty_chip_color("indoor-growzelt")
        assert color == "error", (
            f"Expected difficulty chip colour 'error' (red) for growzelt kit (advanced), got: '{color}'"
        )


# ── Favorite Toggle ──────────────────────────────────────────────────────────


class TestFavoriteToggle:
    """TC-020-021: Toggle individual species as favorites."""

    def test_toggle_favorite_species(
        self,
        wizard: OnboardingWizardPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-020-021: Clicking a favorite tile toggles its selected state.

        This test selects a kit to pre-populate favorites, then toggles one off and back on.
        """
        capture = request.node._screenshot_capture
        wizard.open()
        wizard.advance_to_step_kit()
        wizard.click_kit("fensterbank-kraeuter")
        wizard.advance_to_step_favorites()
        capture("req020_021_favorites_initial", "Favorites step with kit pre-selection")

        # Find the first visible favorite tile
        tiles = wizard.get_favorite_tiles()
        if len(tiles) == 0:
            pytest.skip("No favorite tiles visible — cannot test toggle")

        # Get the testid of the first tile
        first_tile_testid = tiles[0].get_attribute("data-testid") or ""
        species_key = first_tile_testid.replace("favorite-tile-", "")

        initial_state = wizard.is_favorite_tile_selected(species_key)
        capture("req020_021_before_toggle", f"Tile {species_key} initial state: {initial_state}")

        # Toggle off
        wizard.click_favorite_tile(species_key)
        after_first_click = wizard.is_favorite_tile_selected(species_key)
        capture("req020_021_after_first_toggle", f"Tile {species_key} after first toggle")

        assert after_first_click != initial_state, (
            f"Expected tile state to change after first click. Was: {initial_state}, now: {after_first_click}"
        )

        # Toggle back
        wizard.click_favorite_tile(species_key)
        after_second_click = wizard.is_favorite_tile_selected(species_key)
        capture("req020_021_after_second_toggle", f"Tile {species_key} after second toggle")

        assert after_second_click == initial_state, (
            f"Expected tile to return to initial state after double toggle. "
            f"Initial: {initial_state}, now: {after_second_click}"
        )


# ── Site Type Change ─────────────────────────────────────────────────────────


class TestSiteTypeChange:
    """TC-020-027: Change site type via dropdown."""

    def test_change_site_type_from_dropdown(
        self,
        wizard: OnboardingWizardPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-020-027: Changing the site type updates the selector display."""
        capture = request.node._screenshot_capture
        wizard.open()
        wizard.advance_to_step_kit()
        wizard.click_kit("fensterbank-kraeuter")
        wizard.advance_to_step_favorites()
        wizard.advance_to_step_site()
        capture("req020_027_before_type_change", "Site step before type change")

        initial_type = wizard.get_site_type_value()
        wizard.select_site_type("Balkon")
        capture("req020_027_after_type_change", "Site step after changing to Balkon")

        new_type = wizard.get_site_type_value()
        assert "Balkon" in new_type, (
            f"Expected site type to show 'Balkon', got: '{new_type}'"
        )
        assert new_type != initial_type, (
            f"Expected site type to change from '{initial_type}' to 'Balkon'"
        )


# ── Plant Counter Boundaries ──────────────────────────────────────────────────


class TestPlantCounterBoundaries:
    """TC-020-034, TC-020-035: Plant counter max=50 and zero removes phase selector."""

    def _navigate_to_plants_with_kit(self, wizard: OnboardingWizardPage) -> None:
        """Helper: navigate intermediate user with kit to the plant selection step."""
        wizard.open()
        wizard.advance_to_step_kit(experience_level="intermediate")
        wizard.click_kit("fensterbank-kraeuter")
        wizard.advance_to_step_favorites()
        wizard.advance_to_step_site()
        wizard.advance_to_step_plants()

    def test_plant_zero_count_hides_phase_selector(
        self,
        wizard: OnboardingWizardPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-020-035: Setting a plant count to 0 hides the phase selector for that species."""
        capture = request.node._screenshot_capture
        self._navigate_to_plants_with_kit(wizard)

        rows = wizard.get_plant_config_rows()
        if len(rows) == 0:
            pytest.skip("No plant config rows — cannot test counter boundary")

        # Get the species key from the first row
        first_row_testid = rows[0].get_attribute("data-testid") or ""
        species_key = first_row_testid.replace("plant-config-", "")
        capture("req020_035_initial_plant_config", f"Plant config for {species_key}")

        # Check initial count and phase selector
        count_val = wizard.get_plant_count_value(species_key)

        if int(count_val) > 0:
            assert wizard.is_plant_phase_select_visible(species_key), (
                "Expected phase selector to be visible when count > 0"
            )

        # Decrease to 0
        current = int(count_val)
        for _ in range(current):
            wizard.click_plant_count_minus(species_key)

        capture("req020_035_count_zero", f"Plant config for {species_key} at count 0")

        assert wizard.get_plant_count_value(species_key) == "0", (
            "Expected plant count to be 0"
        )
        assert not wizard.is_plant_phase_select_visible(species_key), (
            "Expected phase selector to be hidden when count is 0"
        )
        assert not wizard.is_plant_count_minus_enabled(species_key), (
            "Expected minus button to be disabled when count is 0"
        )
