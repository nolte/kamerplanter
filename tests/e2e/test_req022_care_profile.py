"""E2E tests for REQ-022 — Care Profile Edit Dialog.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-022.md):
  TC-REQ-022-001  ->  TC-022-018  CareProfileEditDialog oeffnet sich von der ReminderCard aus
  TC-REQ-022-002  ->  TC-022-018  CareProfileEditDialog zeigt Pflegestil-Dropdown
  TC-REQ-022-003  ->  TC-022-018  CareProfileEditDialog hat Speichern, Abbrechen, Reset Buttons
  TC-REQ-022-004  ->  TC-022-019  Giessintervall-Slider aendern und speichern
  TC-REQ-022-005  ->  TC-022-021  Aktive Duengemonate per Monats-Chips konfigurieren
  TC-REQ-022-006  ->  TC-022-021  Klick auf Monats-Toggle aendert Auswahl
  TC-REQ-022-007  ->  TC-022-024  Luftfeuchte-Check Toggle aktiviert Intervall-Slider
  TC-REQ-022-008  ->  TC-022-022  Standort-Check deaktivieren blendet Monats-Konfiguration aus
  TC-REQ-022-009  ->  TC-022-025  Adaptive-Learning Toggle deaktivieren
  TC-REQ-022-010  ->  TC-022-027  Care-Style-Dropdown listet alle Stile auf
  TC-REQ-022-011  ->  TC-022-018  Abbrechen schliesst Dialog ohne Speichern
  TC-REQ-022-012  ->  TC-022-019  Speichern schliesst Dialog und aktualisiert Dashboard
  TC-REQ-022-013  ->  TC-022-018  Profil-Dialog zeigt Aufgabentyp-Toggles
  TC-REQ-022-014  ->  TC-022-018  Profil-Dialog zeigt Giessmethode-Dropdown
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.pflege_dashboard_page import PflegeDashboardPage


# -- Fixtures -----------------------------------------------------------------


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
    suffix = testid.replace("care-card-care-", "")
    parts = suffix.rsplit("-", 1)
    if len(parts) < 2:
        pytest.skip(f"Unexpected card testid format: {testid}")
    return parts[0]


# -- TC-022-018: Open CareProfileEditDialog ------------------------------------


class TestCareProfileEditDialogOpen:
    """Opening the CareProfileEditDialog from a ReminderCard (Spec: TC-022-018)."""

    @pytest.mark.core_crud
    def test_edit_profile_button_opens_dialog(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-001: Clicking edit-profile on a card opens the CareProfileEditDialog.

        Spec: TC-022-018 -- CareProfileEditDialog oeffnet sich von der ReminderCard aus.
        """
        pflege.open()
        screenshot(
            "TC-REQ-022-001_before-edit-profile",
            "Pflege dashboard before clicking edit profile",
        )

        plant_key = _get_first_card_plant_key(pflege)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        screenshot(
            "TC-REQ-022-001_profile-dialog-open",
            "CareProfileEditDialog opened",
        )

        assert pflege.is_profile_dialog_open(), (
            "TC-REQ-022-001 FAIL: Expected CareProfileEditDialog to be visible"
        )

    @pytest.mark.core_crud
    def test_profile_dialog_shows_care_style_select(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-002: CareProfileEditDialog shows the care style dropdown.

        Spec: TC-022-018 -- CareProfileEditDialog zeigt Pflegestil-Dropdown.
        """
        pflege.open()
        plant_key = _get_first_card_plant_key(pflege)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        screenshot(
            "TC-REQ-022-002_care-style-select",
            "CareProfileEditDialog with care style dropdown",
        )

        style_selects = pflege.driver.find_elements(*PflegeDashboardPage.CARE_STYLE_SELECT)
        assert len(style_selects) > 0, (
            "TC-REQ-022-002 FAIL: Expected care style select in profile dialog"
        )

    @pytest.mark.core_crud
    def test_profile_dialog_has_save_cancel_reset_buttons(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-003: CareProfileEditDialog has Save, Cancel, and Reset buttons.

        Spec: TC-022-018 -- CareProfileEditDialog hat Speichern, Abbrechen, Reset Buttons.
        """
        pflege.open()
        plant_key = _get_first_card_plant_key(pflege)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        screenshot(
            "TC-REQ-022-003_dialog-actions",
            "CareProfileEditDialog action buttons",
        )

        save_btns = pflege.driver.find_elements(*PflegeDashboardPage.SAVE_PROFILE_BUTTON)
        cancel_btns = pflege.driver.find_elements(*PflegeDashboardPage.CANCEL_BUTTON)
        reset_btns = pflege.driver.find_elements(*PflegeDashboardPage.RESET_PROFILE_BUTTON)

        assert len(save_btns) > 0, "TC-REQ-022-003 FAIL: Expected save button in profile dialog"
        assert len(cancel_btns) > 0, "TC-REQ-022-003 FAIL: Expected cancel button in profile dialog"
        assert len(reset_btns) > 0, "TC-REQ-022-003 FAIL: Expected reset button in profile dialog"


# -- TC-022-019 to TC-022-021: Sliders and Interval Controls ------------------


class TestCareProfileSliders:
    """Interval sliders and fertilizing months (Spec: TC-022-019, TC-022-021)."""

    @pytest.mark.core_crud
    def test_watering_interval_slider_present(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-004: Watering interval slider is visible when watering task is enabled.

        Spec: TC-022-019 -- Giessintervall-Slider aendern und speichern.
        """
        pflege.open()
        plant_key = _get_first_card_plant_key(pflege)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        screenshot(
            "TC-REQ-022-004_watering-slider",
            "CareProfileEditDialog watering interval slider",
        )

        sliders = pflege.driver.find_elements(*PflegeDashboardPage.WATERING_INTERVAL_SLIDER)
        assert len(sliders) > 0, (
            "TC-REQ-022-004 FAIL: Expected watering interval slider"
        )

    @pytest.mark.core_crud
    def test_fertilizing_active_months_displayed(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-005: Fertilizing active months toggle buttons are displayed.

        Spec: TC-022-021 -- Aktive Duengemonate per Monats-Chips konfigurieren.
        """
        pflege.open()
        plant_key = _get_first_card_plant_key(pflege)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        screenshot(
            "TC-REQ-022-005_fertilizing-months",
            "CareProfileEditDialog active fertilizing months",
        )

        month_groups = pflege.driver.find_elements(*PflegeDashboardPage.FERTILIZING_ACTIVE_MONTHS)
        assert len(month_groups) > 0, (
            "TC-REQ-022-005 FAIL: Expected fertilizing active months element"
        )

    @pytest.mark.core_crud
    def test_fertilizing_month_click_toggles_selection(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-006: Clicking a month toggle button changes its selection state.

        Spec: TC-022-021 -- Aktive Duengemonate per Monats-Chips konfigurieren.
        """
        pflege.open()
        plant_key = _get_first_card_plant_key(pflege)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        initial_months = pflege.get_fertilizing_active_month_values()
        screenshot(
            "TC-REQ-022-006_months-before-click",
            "Fertilizing months before clicking",
        )

        target_month = 11  # November
        pflege.click_fertilizing_month(target_month)
        pflege.wait_for_loading_complete()

        screenshot(
            "TC-REQ-022-006_months-after-click",
            "Fertilizing months after clicking month 11",
        )

        updated_months = pflege.get_fertilizing_active_month_values()
        assert updated_months != initial_months, (
            f"TC-REQ-022-006 FAIL: Expected month selection to change after clicking month {target_month}. "
            f"Before: {initial_months}, After: {updated_months}"
        )


# -- TC-022-022 to TC-022-024: Conditional Fields (Toggles) -------------------


class TestCareProfileConditionalFields:
    """Toggle switches controlling conditional field visibility (Spec: TC-022-022 to TC-022-025)."""

    @pytest.mark.core_crud
    def test_humidity_check_toggle_controls_interval_visibility(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-007: Toggling humidity check shows/hides the interval slider.

        Spec: TC-022-024 -- Luftfeuchte-Check Toggle aktiviert bedingt Intervall-Slider.
        """
        pflege.open()
        plant_key = _get_first_card_plant_key(pflege)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        was_enabled = pflege.is_humidity_check_enabled()
        screenshot(
            "TC-REQ-022-007_humidity-toggle-initial",
            f"Humidity toggle initial state (enabled={was_enabled})",
        )

        pflege.toggle_humidity_check()
        pflege.wait_for_loading_complete()

        is_now_enabled = pflege.is_humidity_check_enabled()
        screenshot(
            "TC-REQ-022-007_humidity-toggle-after",
            f"Humidity toggle after click (enabled={is_now_enabled})",
        )

        assert is_now_enabled != was_enabled, (
            f"TC-REQ-022-007 FAIL: Expected humidity check toggle to change state. "
            f"Before: {was_enabled}, After: {is_now_enabled}"
        )

        if is_now_enabled:
            assert pflege.is_humidity_interval_visible(), (
                "TC-REQ-022-007 FAIL: Expected humidity interval slider to be visible when toggle is ON"
            )

    @pytest.mark.core_crud
    def test_location_check_toggle_controls_months_visibility(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-008: Toggling location check shows/hides the months configuration.

        Spec: TC-022-022 / TC-022-023 -- Standort-Check deaktivieren/aktivieren.
        """
        pflege.open()
        plant_key = _get_first_card_plant_key(pflege)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        was_enabled = pflege.is_location_check_enabled()
        screenshot(
            "TC-REQ-022-008_location-toggle-initial",
            f"Location check toggle initial state (enabled={was_enabled})",
        )

        pflege.toggle_location_check()
        pflege.wait_for_loading_complete()

        is_now_enabled = pflege.is_location_check_enabled()
        screenshot(
            "TC-REQ-022-008_location-toggle-after",
            f"Location check toggle after click (enabled={is_now_enabled})",
        )

        assert is_now_enabled != was_enabled, (
            f"TC-REQ-022-008 FAIL: Expected location check toggle to change state. "
            f"Before: {was_enabled}, After: {is_now_enabled}"
        )

        if is_now_enabled:
            assert pflege.is_location_check_months_visible(), (
                "TC-REQ-022-008 FAIL: Expected location check months to be visible when toggle is ON"
            )

    @pytest.mark.core_crud
    def test_adaptive_learning_toggle(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-009: Toggling adaptive learning switch changes its state.

        Spec: TC-022-025 -- Adaptive-Learning Toggle deaktivieren.
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
            pflege.wait_for_loading_complete()

        screenshot(
            "TC-REQ-022-009_adaptive-learning-initial",
            "Adaptive Learning Toggle initial state",
        )

        was_enabled = pflege.is_adaptive_learning_enabled()
        pflege.toggle_adaptive_learning()
        pflege.wait_for_loading_complete()

        is_now_enabled = pflege.is_adaptive_learning_enabled()
        screenshot(
            "TC-REQ-022-009_adaptive-learning-after",
            "Adaptive Learning Toggle after click",
        )

        assert is_now_enabled != was_enabled, (
            f"TC-REQ-022-009 FAIL: Expected adaptive learning toggle to change state. "
            f"Before: {was_enabled}, After: {is_now_enabled}"
        )


# -- TC-022-027 to TC-022-029: Care Style Change ------------------------------


class TestCareStyleChange:
    """Changing care style in profile dialog (Spec: TC-022-027)."""

    @pytest.mark.core_crud
    def test_care_style_dropdown_lists_all_styles(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-010: Care style dropdown lists all available styles.

        Spec: TC-022-027 -- Care-Style-Wechsel zeigt Bestaetigung und setzt alle Intervalle zurueck.
        """
        pflege.open()
        plant_key = _get_first_card_plant_key(pflege)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        select_el = pflege.wait_for_element_clickable(PflegeDashboardPage.CARE_STYLE_SELECT)
        pflege.scroll_and_click(select_el)
        pflege.wait_for_loading_complete()

        screenshot(
            "TC-REQ-022-010_care-style-dropdown",
            "CareStyle dropdown opened",
        )

        options = pflege.driver.find_elements(By.CSS_SELECTOR, "li[role='option']")
        option_texts = [opt.text for opt in options]

        assert len(options) >= 5, (
            f"TC-REQ-022-010 FAIL: Expected at least 5 care style options, "
            f"got {len(options)}: {option_texts}"
        )

        # Close dropdown
        pflege.driver.find_element(By.TAG_NAME, "body").click()


# -- Profile Dialog Save and Cancel --------------------------------------------


class TestCareProfileSaveCancel:
    """Profile dialog save and cancel actions (Spec: TC-022-018, TC-022-019)."""

    @pytest.mark.core_crud
    def test_cancel_closes_dialog_without_saving(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-011: Cancelling profile dialog closes it without saving.

        Spec: TC-022-018 -- CareProfileEditDialog -- Abbrechen schliesst Dialog.
        """
        pflege.open()
        plant_key = _get_first_card_plant_key(pflege)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        screenshot(
            "TC-REQ-022-011_before-cancel",
            "CareProfileEditDialog before cancel",
        )

        pflege.click_cancel_profile()
        pflege.wait_for_dialog_closed()

        screenshot(
            "TC-REQ-022-011_after-cancel",
            "After cancelling CareProfileEditDialog",
        )

        assert not pflege.is_profile_dialog_open(), (
            "TC-REQ-022-011 FAIL: Expected profile dialog to close after clicking cancel"
        )

    @pytest.mark.core_crud
    def test_save_closes_dialog_and_refreshes_dashboard(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-012: Saving profile dialog closes it and refreshes the dashboard.

        Spec: TC-022-019 -- Giessintervall-Slider aendern und speichern.
        """
        pflege.open()
        plant_key = _get_first_card_plant_key(pflege)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        screenshot(
            "TC-REQ-022-012_before-save",
            "CareProfileEditDialog before save",
        )

        pflege.click_save_profile()
        pflege.wait_for_loading_complete()

        screenshot(
            "TC-REQ-022-012_after-save",
            "After saving CareProfileEditDialog",
        )

        assert not pflege.is_profile_dialog_open(), (
            "TC-REQ-022-012 FAIL: Expected profile dialog to close after clicking save"
        )

    @pytest.mark.core_crud
    def test_task_type_toggles_are_present(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-013: Profile dialog shows task type toggle switches.

        Spec: TC-022-018 -- CareProfileEditDialog zeigt Aufgabentyp-Toggles.
        """
        pflege.open()
        plant_key = _get_first_card_plant_key(pflege)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        screenshot(
            "TC-REQ-022-013_task-toggles",
            "CareProfileEditDialog task type toggles",
        )

        for locator_name, locator in [
            ("watering", PflegeDashboardPage.AUTO_CREATE_WATERING_SWITCH),
            ("fertilizing", PflegeDashboardPage.AUTO_CREATE_FERTILIZING_SWITCH),
            ("repotting", PflegeDashboardPage.AUTO_CREATE_REPOTTING_SWITCH),
            ("pest_check", PflegeDashboardPage.AUTO_CREATE_PEST_CHECK_SWITCH),
        ]:
            elements = pflege.driver.find_elements(*locator)
            assert len(elements) > 0, (
                f"TC-REQ-022-013 FAIL: Expected task type toggle for '{locator_name}'"
            )

    @pytest.mark.core_crud
    def test_watering_method_select_present(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-014: Profile dialog shows watering method dropdown.

        Spec: TC-022-018 -- CareProfileEditDialog zeigt Giessmethode-Dropdown.
        """
        pflege.open()
        plant_key = _get_first_card_plant_key(pflege)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        screenshot(
            "TC-REQ-022-014_watering-method",
            "CareProfileEditDialog watering method dropdown",
        )

        method_selects = pflege.driver.find_elements(*PflegeDashboardPage.WATERING_METHOD_SELECT)
        assert len(method_selects) > 0, (
            "TC-REQ-022-014 FAIL: Expected watering method select element"
        )
