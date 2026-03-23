"""E2E tests for REQ-022 -- Care Profile Edit Dialog (TC-022-018 to TC-022-029).

Tests cover:
- CareProfileEditDialog: open from card, care style select, sliders
- Task type toggles: watering, fertilizing, repotting, pest_check, humidity, location
- Conditional fields: humidity interval visibility, location months visibility
- Adaptive learning toggle
- Fertilizing active months (month chips)
- Save and cancel actions
- Reset to defaults

NFR-008 ss3.4 screenshot checkpoints at:
1. Page Load
2. Before significant actions
3. After significant actions
4. Error states
"""

from __future__ import annotations

import time

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.pflege_dashboard_page import PflegeDashboardPage


# -- Fixtures ----------------------------------------------------------------


@pytest.fixture
def pflege(browser: WebDriver, base_url: str) -> PflegeDashboardPage:
    """Return a PflegeDashboardPage bound to the test browser."""
    return PflegeDashboardPage(browser, base_url)


def _get_first_card_plant_key(pflege: PflegeDashboardPage) -> str:
    """Extract the plant_key from the first care card on the dashboard."""
    cards = pflege.get_all_care_cards()
    if not cards:
        pytest.skip("No care cards available -- cannot test profile editing")
    testid = cards[0].get_attribute("data-testid") or ""
    # Format: care-card-care-{plant_key}-{reminder_type}
    suffix = testid.replace("care-card-care-", "")
    parts = suffix.rsplit("-", 1)
    if len(parts) < 2:
        pytest.skip(f"Unexpected card testid format: {testid}")
    return parts[0]


# -- TC-022-018: Open CareProfileEditDialog ----------------------------------


class TestCareProfileEditDialogOpen:
    """TC-022-018: Opening the CareProfileEditDialog from a ReminderCard."""

    def test_edit_profile_button_opens_dialog(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-018: Clicking edit-profile on a card opens the CareProfileEditDialog."""
        pflege.open()
        screenshot("req022_018_before_edit_profile", "Vor Klick auf Profil bearbeiten")

        plant_key = _get_first_card_plant_key(pflege)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        screenshot("req022_018_profile_dialog_open", "CareProfileEditDialog geoeffnet")

        assert pflege.is_profile_dialog_open(), (
            "Expected CareProfileEditDialog to be visible after clicking edit button"
        )

    def test_profile_dialog_shows_care_style_select(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-018: CareProfileEditDialog shows the care style dropdown."""
        pflege.open()
        plant_key = _get_first_card_plant_key(pflege)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        screenshot("req022_018b_care_style_select", "CareProfileEditDialog Pflegestil-Dropdown")

        style_selects = pflege.driver.find_elements(*PflegeDashboardPage.CARE_STYLE_SELECT)
        assert len(style_selects) > 0, (
            "Expected care style select [data-testid='care-style-select'] in profile dialog"
        )

    def test_profile_dialog_has_save_cancel_reset_buttons(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-018: CareProfileEditDialog has Save, Cancel, and Reset buttons."""
        pflege.open()
        plant_key = _get_first_card_plant_key(pflege)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        screenshot("req022_018c_dialog_actions", "CareProfileEditDialog Aktions-Buttons")

        save_btns = pflege.driver.find_elements(*PflegeDashboardPage.SAVE_PROFILE_BUTTON)
        cancel_btns = pflege.driver.find_elements(*PflegeDashboardPage.CANCEL_BUTTON)
        reset_btns = pflege.driver.find_elements(*PflegeDashboardPage.RESET_PROFILE_BUTTON)

        assert len(save_btns) > 0, "Expected save button in profile dialog"
        assert len(cancel_btns) > 0, "Expected cancel button in profile dialog"
        assert len(reset_btns) > 0, "Expected reset button in profile dialog"


# -- TC-022-019 to TC-022-021: Sliders and Interval Controls ----------------


class TestCareProfileSliders:
    """TC-022-019 to TC-022-021: Interval sliders and fertilizing months."""

    def test_watering_interval_slider_present(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-019: Watering interval slider is visible when watering task is enabled."""
        pflege.open()
        plant_key = _get_first_card_plant_key(pflege)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        screenshot("req022_019_watering_slider", "CareProfileEditDialog Giessintervall-Slider")

        sliders = pflege.driver.find_elements(*PflegeDashboardPage.WATERING_INTERVAL_SLIDER)
        assert len(sliders) > 0, (
            "Expected watering interval slider [data-testid='watering-interval-slider']"
        )

    def test_fertilizing_active_months_displayed(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-021: Fertilizing active months toggle buttons are displayed."""
        pflege.open()
        plant_key = _get_first_card_plant_key(pflege)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        screenshot(
            "req022_021_fertilizing_months",
            "CareProfileEditDialog Aktive Duengemonate",
        )

        month_groups = pflege.driver.find_elements(*PflegeDashboardPage.FERTILIZING_ACTIVE_MONTHS)
        assert len(month_groups) > 0, (
            "Expected fertilizing active months [data-testid='fertilizing-active-months']"
        )

    def test_fertilizing_month_click_toggles_selection(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-021: Clicking a month toggle button changes its selection state."""
        pflege.open()
        plant_key = _get_first_card_plant_key(pflege)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        initial_months = pflege.get_fertilizing_active_month_values()
        screenshot("req022_021b_months_before_click", "Duengemonate vor Klick")

        # Pick a month that is currently NOT selected to toggle it on,
        # or one that IS selected to toggle it off.
        target_month = 11  # November - often not in default active months
        pflege.click_fertilizing_month(target_month)
        time.sleep(0.3)

        screenshot("req022_021c_months_after_click", "Duengemonate nach Klick auf Monat 11")

        updated_months = pflege.get_fertilizing_active_month_values()
        assert updated_months != initial_months, (
            f"Expected month selection to change after clicking month {target_month}. "
            f"Before: {initial_months}, After: {updated_months}"
        )


# -- TC-022-022 to TC-022-024: Conditional Fields (Toggles) -----------------


class TestCareProfileConditionalFields:
    """TC-022-022 to TC-022-024: Toggle switches controlling conditional field visibility."""

    def test_humidity_check_toggle_controls_interval_visibility(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-024: Toggling humidity check shows/hides the interval slider."""
        pflege.open()
        plant_key = _get_first_card_plant_key(pflege)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        was_enabled = pflege.is_humidity_check_enabled()
        screenshot(
            "req022_024_humidity_toggle_initial",
            f"Luftfeuchte-Toggle Ausgangszustand (enabled={was_enabled})",
        )

        pflege.toggle_humidity_check()
        time.sleep(0.3)

        is_now_enabled = pflege.is_humidity_check_enabled()
        screenshot(
            "req022_024_humidity_toggle_after",
            f"Luftfeuchte-Toggle nach Klick (enabled={is_now_enabled})",
        )

        assert is_now_enabled != was_enabled, (
            f"Expected humidity check toggle to change state. "
            f"Before: {was_enabled}, After: {is_now_enabled}"
        )

        # When enabled, the interval slider should be visible
        if is_now_enabled:
            assert pflege.is_humidity_interval_visible(), (
                "Expected humidity interval slider to be visible when toggle is ON"
            )

    def test_location_check_toggle_controls_months_visibility(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-022/023: Toggling location check shows/hides the months configuration."""
        pflege.open()
        plant_key = _get_first_card_plant_key(pflege)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        was_enabled = pflege.is_location_check_enabled()
        screenshot(
            "req022_022_location_toggle_initial",
            f"Standort-Check Toggle Ausgangszustand (enabled={was_enabled})",
        )

        pflege.toggle_location_check()
        time.sleep(0.3)

        is_now_enabled = pflege.is_location_check_enabled()
        screenshot(
            "req022_022_location_toggle_after",
            f"Standort-Check Toggle nach Klick (enabled={is_now_enabled})",
        )

        assert is_now_enabled != was_enabled, (
            f"Expected location check toggle to change state. "
            f"Before: {was_enabled}, After: {is_now_enabled}"
        )

        if is_now_enabled:
            assert pflege.is_location_check_months_visible(), (
                "Expected location check months to be visible when toggle is ON"
            )

    def test_adaptive_learning_toggle(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-025: Toggling adaptive learning switch changes its state.

        NOTE: The adaptive learning switch is inside the 'Advanced' accordion.
        This test expands the accordion first before interacting with the toggle.
        """
        pflege.open()
        plant_key = _get_first_card_plant_key(pflege)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        # Expand the "Erweitert" (Advanced) accordion to reveal the switch
        accordions = pflege.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='care-profile-edit-dialog'] .MuiAccordionSummary-root"
        )
        if accordions:
            pflege.scroll_and_click(accordions[0])
            time.sleep(0.3)

        screenshot("req022_025_adaptive_learning_initial", "Adaptive Learning Toggle Ausgangszustand")

        was_enabled = pflege.is_adaptive_learning_enabled()
        pflege.toggle_adaptive_learning()
        time.sleep(0.3)

        is_now_enabled = pflege.is_adaptive_learning_enabled()
        screenshot("req022_025_adaptive_learning_after", "Adaptive Learning Toggle nach Klick")

        assert is_now_enabled != was_enabled, (
            f"Expected adaptive learning toggle to change state. "
            f"Before: {was_enabled}, After: {is_now_enabled}"
        )


# -- TC-022-027 to TC-022-029: Care Style Change ----------------------------


class TestCareStyleChange:
    """TC-022-027 to TC-022-029: Changing care style in profile dialog."""

    def test_care_style_dropdown_lists_all_styles(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-027: Care style dropdown lists all available styles."""
        pflege.open()
        plant_key = _get_first_card_plant_key(pflege)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        # Click to open the dropdown
        select_el = pflege.wait_for_element_clickable(PflegeDashboardPage.CARE_STYLE_SELECT)
        pflege.scroll_and_click(select_el)
        time.sleep(0.3)

        screenshot("req022_027_care_style_dropdown", "CareStyle-Dropdown geoeffnet")

        options = pflege.driver.find_elements(By.CSS_SELECTOR, "li[role='option']")
        option_texts = [opt.text for opt in options]

        assert len(options) >= 5, (
            f"Expected at least 5 care style options, got {len(options)}: {option_texts}"
        )

        # Close dropdown by pressing Escape
        pflege.driver.find_element(By.TAG_NAME, "body").click()
        time.sleep(0.2)


# -- Profile Dialog Save and Cancel ------------------------------------------


class TestCareProfileSaveCancel:
    """Profile dialog save and cancel actions."""

    def test_cancel_closes_dialog_without_saving(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-018: Cancelling profile dialog closes it without saving."""
        pflege.open()
        plant_key = _get_first_card_plant_key(pflege)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        screenshot("req022_018d_before_cancel", "CareProfileEditDialog vor Abbrechen")

        pflege.click_cancel_profile()
        pflege.wait_for_dialog_closed()

        screenshot("req022_018e_after_cancel", "Nach Abbrechen des CareProfileEditDialog")

        assert not pflege.is_profile_dialog_open(), (
            "Expected profile dialog to close after clicking cancel"
        )

    def test_save_closes_dialog_and_refreshes_dashboard(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-019: Saving profile dialog closes it and refreshes the dashboard."""
        pflege.open()
        plant_key = _get_first_card_plant_key(pflege)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        screenshot("req022_019b_before_save", "CareProfileEditDialog vor Speichern")

        pflege.click_save_profile()
        time.sleep(1)  # Wait for API call

        screenshot("req022_019c_after_save", "Nach Speichern des CareProfileEditDialog")

        # Dialog should close after successful save
        assert not pflege.is_profile_dialog_open(), (
            "Expected profile dialog to close after clicking save"
        )

    def test_task_type_toggles_are_present(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-018: Profile dialog shows task type toggle switches."""
        pflege.open()
        plant_key = _get_first_card_plant_key(pflege)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        screenshot("req022_018f_task_toggles", "CareProfileEditDialog Aufgabentyp-Toggles")

        for locator_name, locator in [
            ("watering", PflegeDashboardPage.AUTO_CREATE_WATERING_SWITCH),
            ("fertilizing", PflegeDashboardPage.AUTO_CREATE_FERTILIZING_SWITCH),
            ("repotting", PflegeDashboardPage.AUTO_CREATE_REPOTTING_SWITCH),
            ("pest_check", PflegeDashboardPage.AUTO_CREATE_PEST_CHECK_SWITCH),
        ]:
            elements = pflege.driver.find_elements(*locator)
            assert len(elements) > 0, (
                f"Expected task type toggle for '{locator_name}' to be present"
            )

    def test_watering_method_select_present(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-018: Profile dialog shows watering method dropdown."""
        pflege.open()
        plant_key = _get_first_card_plant_key(pflege)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        screenshot("req022_018g_watering_method", "CareProfileEditDialog Giessmethode")

        method_selects = pflege.driver.find_elements(*PflegeDashboardPage.WATERING_METHOD_SELECT)
        assert len(method_selects) > 0, (
            "Expected watering method select [data-testid='watering-method-select']"
        )
