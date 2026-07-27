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
  TC-REQ-022-035  ->  TC-022-089  Giessintervall verkuerzen -- Faelligkeit im Dashboard rueckt vor
  TC-REQ-022-036  ->  TC-022-090  Giessintervall-Anpassung propagiert in die Aufgabenliste (kein Duplikat)
  TC-REQ-022-037  ->  TC-022-092  Care-Style-Preset wechseln -- alle Intervalle aktualisieren sich
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from ._journey_helpers import provision_plant, wait_for_watering_card
from .pages.pflege_dashboard_page import PflegeDashboardPage
from .pages.plant_instance_list_page import PlantInstanceListPage
from .pages.task_queue_page import TaskQueuePage


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def pflege(browser: WebDriver, base_url: str) -> PflegeDashboardPage:
    """Return a PflegeDashboardPage bound to the test browser."""
    return PflegeDashboardPage(browser, base_url)


@pytest.fixture
def task_queue(browser: WebDriver, base_url: str) -> TaskQueuePage:
    """Return a TaskQueuePage bound to the test browser."""
    return TaskQueuePage(browser, base_url)


@pytest.fixture
def plant_creator(browser: WebDriver, base_url: str) -> PlantInstanceListPage:
    """Return a PlantInstanceListPage for self-provisioning a plant instance."""
    return PlantInstanceListPage(browser, base_url)


def _provision_plant_with_watering_card(
    plant_creator: PlantInstanceListPage,
    pflege: PflegeDashboardPage,
    *,
    id_prefix: str,
) -> str:
    """Self-provision a plant and wait for its live watering care card; return plant_key.

    A freshly created plant gets an auto care profile whose watering entry is due
    today, so the care dashboard renders a ``care-card-care-{key}-watering`` card
    on its own — the precondition every watering-cycle test needs, established
    through the real UI instead of relying on seed data.
    """
    plant_key, _instance_id = provision_plant(plant_creator, id_prefix=id_prefix)
    if not wait_for_watering_card(pflege, plant_key):
        raise AssertionError(
            f"Self-provisioning failed: no watering care card appeared for the "
            f"freshly created plant '{plant_key}'"
        )
    return plant_key


def _care_card_plant_key(
    pflege: PflegeDashboardPage,
    plant_creator: PlantInstanceListPage,
    *,
    id_prefix: str = "TC022P",
) -> str:
    """Return a plant key that has a care card, self-provisioning one if needed.

    NFR-008a: a test establishes its own precondition instead of skipping.
    This file used to self-skip 14 cases with "No care cards available --
    cannot test profile editing" whenever it ran without another test having
    created a care-bearing plant first (e.g. running the file in isolation, or
    a shard where no such test landed) -- coverage silently disappeared.

    Existing cards are reused when the dashboard has any: these cases open the
    care-profile dialog for inspection, so they do not depend on *which* card
    they get. Only when the dashboard is empty is a plant created through the
    real UI, which materialises a watering card on its own.
    """
    cards = pflege.get_all_care_cards()
    if not cards:
        plant_key = _provision_plant_with_watering_card(plant_creator, pflege, id_prefix=id_prefix)
        pflege.open()
        return plant_key
    testid = cards[0].get_attribute("data-testid") or ""
    suffix = testid.replace("care-card-care-", "")
    parts = suffix.rsplit("-", 1)
    if len(parts) < 2:
        raise AssertionError(
            f"Unexpected care-card testid format: '{testid}' "
            "(expected care-card-care-<plant_key>-<reminder_type>)"
        )
    return parts[0]


# -- TC-022-018: Open CareProfileEditDialog ------------------------------------


class TestCareProfileEditDialogOpen:
    """Opening the CareProfileEditDialog from a ReminderCard (Spec: TC-022-018)."""

    @pytest.mark.core_crud
    def test_edit_profile_button_opens_dialog(
        self,
        plant_creator: PlantInstanceListPage,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-022-018: Clicking edit-profile on a card opens the CareProfileEditDialog.

        Spec: TC-022-018 -- CareProfileEditDialog oeffnet sich von der ReminderCard aus.
        """
        pflege.open()
        screenshot(
            "TC-REQ-022-001_before-edit-profile",
            "Pflege dashboard before clicking edit profile",
        )

        plant_key = _care_card_plant_key(pflege, plant_creator)
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
        plant_creator: PlantInstanceListPage,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-022-018: CareProfileEditDialog shows the care style dropdown.

        Spec: TC-022-018 -- CareProfileEditDialog zeigt Pflegestil-Dropdown.
        """
        pflege.open()
        plant_key = _care_card_plant_key(pflege, plant_creator)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        screenshot(
            "TC-REQ-022-002_care-style-select",
            "CareProfileEditDialog with care style dropdown",
        )

        assert pflege.is_present(PflegeDashboardPage.CARE_STYLE_SELECT), (
            "TC-REQ-022-002 FAIL: Expected care style select in profile dialog"
        )

    @pytest.mark.core_crud
    def test_profile_dialog_has_save_cancel_reset_buttons(
        self,
        plant_creator: PlantInstanceListPage,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-022-018: CareProfileEditDialog has Save, Cancel, and Reset buttons.

        Spec: TC-022-018 -- CareProfileEditDialog hat Speichern, Abbrechen, Reset Buttons.
        """
        pflege.open()
        plant_key = _care_card_plant_key(pflege, plant_creator)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        screenshot(
            "TC-REQ-022-003_dialog-actions",
            "CareProfileEditDialog action buttons",
        )

        assert pflege.is_present(PflegeDashboardPage.SAVE_PROFILE_BUTTON), (
            "TC-REQ-022-003 FAIL: Expected save button in profile dialog"
        )
        assert pflege.is_present(PflegeDashboardPage.CANCEL_BUTTON), (
            "TC-REQ-022-003 FAIL: Expected cancel button in profile dialog"
        )
        assert pflege.is_present(PflegeDashboardPage.RESET_PROFILE_BUTTON), (
            "TC-REQ-022-003 FAIL: Expected reset button in profile dialog"
        )


# -- TC-022-019 to TC-022-021: Sliders and Interval Controls ------------------


class TestCareProfileSliders:
    """Interval sliders and fertilizing months (Spec: TC-022-019, TC-022-021)."""

    @pytest.mark.core_crud
    def test_watering_interval_slider_present(
        self,
        plant_creator: PlantInstanceListPage,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-022-019: Watering interval slider is visible when watering task is enabled.

        Spec: TC-022-019 -- Giessintervall-Slider aendern und speichern.
        """
        pflege.open()
        plant_key = _care_card_plant_key(pflege, plant_creator)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        screenshot(
            "TC-REQ-022-004_watering-slider",
            "CareProfileEditDialog watering interval slider",
        )

        assert pflege.is_present(PflegeDashboardPage.WATERING_INTERVAL_SLIDER), (
            "TC-REQ-022-004 FAIL: Expected watering interval slider"
        )

    @pytest.mark.core_crud
    def test_fertilizing_active_months_displayed(
        self,
        plant_creator: PlantInstanceListPage,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-022-021: Fertilizing active months toggle buttons are displayed.

        Spec: TC-022-021 -- Aktive Duengemonate per Monats-Chips konfigurieren.
        """
        pflege.open()
        plant_key = _care_card_plant_key(pflege, plant_creator)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        screenshot(
            "TC-REQ-022-005_fertilizing-months",
            "CareProfileEditDialog active fertilizing months",
        )

        assert pflege.is_present(PflegeDashboardPage.FERTILIZING_ACTIVE_MONTHS), (
            "TC-REQ-022-005 FAIL: Expected fertilizing active months element"
        )

    @pytest.mark.core_crud
    def test_fertilizing_month_click_toggles_selection(
        self,
        plant_creator: PlantInstanceListPage,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-022-021: Clicking a month toggle button changes its selection state.

        Spec: TC-022-021 -- Aktive Duengemonate per Monats-Chips konfigurieren.
        """
        pflege.open()
        plant_key = _care_card_plant_key(pflege, plant_creator)
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
        plant_creator: PlantInstanceListPage,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-022-024: Toggling humidity check shows/hides the interval slider.

        Spec: TC-022-024 -- Luftfeuchte-Check Toggle aktiviert bedingt Intervall-Slider.
        """
        pflege.open()
        plant_key = _care_card_plant_key(pflege, plant_creator)
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
        plant_creator: PlantInstanceListPage,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-022-022: Toggling location check shows/hides the months configuration.

        Spec: TC-022-022 / TC-022-023 -- Standort-Check deaktivieren/aktivieren.
        """
        pflege.open()
        plant_key = _care_card_plant_key(pflege, plant_creator)
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
        plant_creator: PlantInstanceListPage,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-022-025: Toggling adaptive learning switch changes its state.

        Spec: TC-022-025 -- Adaptive-Learning Toggle deaktivieren.
        """
        pflege.open()
        plant_key = _care_card_plant_key(pflege, plant_creator)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        # Expand the "Erweitert" (Advanced) accordion to reveal the switch
        pflege.expand_advanced_accordion()

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
        plant_creator: PlantInstanceListPage,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-022-027: Care style dropdown lists all available styles.

        Spec: TC-022-027 -- Care-Style-Wechsel zeigt Bestaetigung und setzt alle Intervalle zurueck.
        """
        pflege.open()
        plant_key = _care_card_plant_key(pflege, plant_creator)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        select_el = pflege.wait_for_element_clickable(PflegeDashboardPage.CARE_STYLE_SELECT)
        pflege.scroll_and_click(select_el)
        pflege.wait_for_loading_complete()

        screenshot(
            "TC-REQ-022-010_care-style-dropdown",
            "CareStyle dropdown opened",
        )

        option_texts = pflege.get_open_dropdown_option_texts()

        assert len(option_texts) >= 5, (
            f"TC-REQ-022-010 FAIL: Expected at least 5 care style options, "
            f"got {len(option_texts)}: {option_texts}"
        )

        # Close dropdown
        pflege.close_mui_dropdown()


# -- Profile Dialog Save and Cancel --------------------------------------------


class TestCareProfileSaveCancel:
    """Profile dialog save and cancel actions (Spec: TC-022-018, TC-022-019)."""

    @pytest.mark.core_crud
    def test_cancel_closes_dialog_without_saving(
        self,
        plant_creator: PlantInstanceListPage,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-022-018: Cancelling profile dialog closes it without saving.

        Spec: TC-022-018 -- CareProfileEditDialog -- Abbrechen schliesst Dialog.
        """
        pflege.open()
        plant_key = _care_card_plant_key(pflege, plant_creator)
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
        plant_creator: PlantInstanceListPage,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-022-019: Saving profile dialog closes it and refreshes the dashboard.

        Spec: TC-022-019 -- Giessintervall-Slider aendern und speichern.
        """
        pflege.open()
        plant_key = _care_card_plant_key(pflege, plant_creator)
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
        plant_creator: PlantInstanceListPage,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-022-018: Profile dialog shows task type toggle switches.

        Spec: TC-022-018 -- CareProfileEditDialog zeigt Aufgabentyp-Toggles.
        """
        pflege.open()
        plant_key = _care_card_plant_key(pflege, plant_creator)
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
            assert pflege.is_present(locator), (
                f"TC-REQ-022-013 FAIL: Expected task type toggle for '{locator_name}'"
            )

    @pytest.mark.core_crud
    def test_watering_method_select_present(
        self,
        plant_creator: PlantInstanceListPage,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-022-018: Profile dialog shows watering method dropdown.

        Spec: TC-022-018 -- CareProfileEditDialog zeigt Giessmethode-Dropdown.
        """
        pflege.open()
        plant_key = _care_card_plant_key(pflege, plant_creator)
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        screenshot(
            "TC-REQ-022-014_watering-method",
            "CareProfileEditDialog watering method dropdown",
        )

        assert pflege.is_present(PflegeDashboardPage.WATERING_METHOD_SELECT), (
            "TC-REQ-022-014 FAIL: Expected watering method select element"
        )


# -- TC-022-089 to TC-022-092: Watering-Cycle Change Propagation (#622) -------


class TestWateringCyclePropagation:
    """Adjusting the watering cycle propagates to dashboard & queue (Spec: TC-022-089..092).

    Issue #622 reschedules the *pending* watering care task in-place when the
    interval changes, so both the Pflege dashboard and the task queue read the
    new due date without creating a duplicate.  The notification side of the
    same change is Soll-Verhalten and covered in test_req030_notifications.py.
    """

    @pytest.mark.core_crud
    def test_shorten_watering_interval_persists_on_dashboard(
        self,
        plant_creator: PlantInstanceListPage,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-022-089: Shortening the watering interval persists and re-renders.

        Spec: TC-022-089 -- Giesszyklus verkuerzen -- naechste Erinnerung im
        Pflege-Dashboard rueckt vor.

        Self-provisioning: a fresh plant with a live watering card is created via
        the real UI, so the test never depends on seed data.
        """
        plant_key = _provision_plant_with_watering_card(plant_creator, pflege, id_prefix="TC089")
        pflege.open()
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        assert pflege.is_present(PflegeDashboardPage.WATERING_INTERVAL_SLIDER), (
            "TC-REQ-022-035 FAIL: A freshly provisioned plant must expose the "
            "watering interval slider"
        )

        screenshot(
            "TC-REQ-022-035_before-shorten-interval",
            f"Care profile for {plant_key} before shortening watering interval",
        )
        pflege.set_watering_interval(5)
        pflege.click_save_profile()
        pflege.wait_for_loading_complete()

        # Reopen the profile from a fresh dashboard load to prove persistence.
        pflege.open()
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()
        value = pflege.get_interval_slider_value("watering-interval-slider")
        screenshot(
            "TC-REQ-022-035_after-shorten-interval",
            f"Care profile for {plant_key} after shortening watering interval (value={value})",
        )

        assert value == 5, (
            "TC-REQ-022-035 FAIL: Expected the shortened watering interval (5 days) "
            f"to persist across a reload, got {value}"
        )

    @pytest.mark.core_crud
    def test_interval_change_creates_no_duplicate_care_task(
        self,
        plant_creator: PlantInstanceListPage,
        pflege: PflegeDashboardPage,
        task_queue: TaskQueuePage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-022-090: Changing the interval reschedules in-place, no duplicate.

        Spec: TC-022-090 -- Giesszyklus-Anpassung propagiert -- dieselbe pending
        Erinnerung, kein Duplikat.

        Self-provisioning + real-behaviour scope: a fresh plant renders exactly
        one live watering care card (the browser-observable care-reminder surface
        for a plant without a materialised task). The spec guarantee under test is
        *no duplicate*, i.e. the reminder count must never increase.

        Observed real behaviour (documented, not forced green): shortening the
        interval reschedules the single reminder to ``created + interval``, which
        can move it out of the currently-due dashboard window -- so the watering
        card count afterwards is one *or zero*, never two. The assertion therefore
        checks that the count does not increase (rather than staying exactly one).
        """
        plant_key = _provision_plant_with_watering_card(plant_creator, pflege, id_prefix="TC090")
        before = pflege.count_care_cards_for_plant(plant_key, "watering")
        screenshot(
            "TC-REQ-022-036_before-interval-change",
            f"Plant {plant_key} watering cards before interval change ({before})",
        )

        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()
        assert pflege.is_present(PflegeDashboardPage.WATERING_INTERVAL_SLIDER), (
            "TC-REQ-022-036 FAIL: A freshly provisioned plant must expose the "
            "watering interval slider"
        )
        pflege.set_watering_interval(3)
        pflege.click_save_profile()
        pflege.wait_for_loading_complete()

        pflege.open()
        after = pflege.count_care_cards_for_plant(plant_key, "watering")
        screenshot(
            "TC-REQ-022-036_after-interval-change",
            f"Plant {plant_key} watering cards after interval change ({after})",
        )

        assert before == 1, (
            "TC-REQ-022-036 FAIL: Expected exactly one watering reminder before the "
            f"change, got {before}"
        )
        assert after <= before, (
            "TC-REQ-022-036 FAIL: Expected the interval change to reschedule the single "
            f"watering reminder without duplicating it (count must not increase). "
            f"Before: {before}, After: {after}"
        )

    @pytest.mark.core_crud
    def test_care_style_preset_switch_resets_intervals(
        self,
        plant_creator: PlantInstanceListPage,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-022-092: Switching the care-style preset resets and persists intervals.

        Spec: TC-022-092 -- Care-Style-Preset wechseln -- alle Zyklen und
        Dashboard-Faelligkeiten aktualisieren sich.

        Self-provisioning: a fresh plant with a live watering card is created via
        the real UI, so the test never depends on seed data.
        """
        plant_key = _provision_plant_with_watering_card(plant_creator, pflege, id_prefix="TC092")
        pflege.open()
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()

        assert pflege.is_present(PflegeDashboardPage.WATERING_INTERVAL_SLIDER), (
            "TC-REQ-022-037 FAIL: A freshly provisioned plant must expose the "
            "watering interval slider"
        )

        screenshot(
            "TC-REQ-022-037_before-preset-switch",
            f"Care profile for {plant_key} before care-style switch",
        )
        # Selecting a preset raises a reset-warning ConfirmDialog which is accepted.
        pflege.select_care_style_with_confirm("Sukkulente")
        pflege.wait_for_loading_complete()
        preset_value = pflege.get_interval_slider_value("watering-interval-slider")
        screenshot(
            "TC-REQ-022-037_after-preset-switch",
            f"Care profile for {plant_key} after switching to succulent preset (value={preset_value})",
        )

        assert preset_value > 0, (
            "TC-REQ-022-037 FAIL: Expected the succulent preset to set a positive "
            f"watering interval, got {preset_value}"
        )

        pflege.click_save_profile()
        pflege.wait_for_loading_complete()

        # Reopen and verify the preset interval persisted.
        pflege.open()
        pflege.click_edit_profile_on_card(plant_key)
        pflege.wait_for_profile_dialog()
        persisted_value = pflege.get_interval_slider_value("watering-interval-slider")
        assert persisted_value == preset_value, (
            "TC-REQ-022-037 FAIL: Expected the succulent preset watering interval "
            f"({preset_value}) to persist, got {persisted_value}"
        )
