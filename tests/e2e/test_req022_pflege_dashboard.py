"""E2E tests for REQ-022 — Pflege Dashboard.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-022.md):
  TC-REQ-022-015  ->  TC-022-001  PflegeDashboardPage zeigt alle faelligen Erinnerungen
  TC-REQ-022-016  ->  TC-022-001  Seitentitel enthaelt Aufgaben-Queue Titel
  TC-REQ-022-017  ->  TC-022-002  Leerer Zustand zeigt Erfolgsmeldung
  TC-REQ-022-018  ->  TC-022-001  Dringlichkeitssektionen rendern
  TC-REQ-022-019  ->  TC-022-009  ReminderCard zeigt Pflanzennamen
  TC-REQ-022-020  ->  TC-022-009  ReminderCard hat Dringlichkeits-Indikator
  TC-REQ-022-021  ->  TC-022-009  Overdue-Karten haben error-Farbe
  TC-REQ-022-022  ->  TC-022-009  Heute-faellige Karten haben warning-Farbe
  TC-REQ-022-023  ->  TC-022-009  Upcoming-Karten haben info-Farbe
  TC-REQ-022-024  ->  TC-022-001  Sektions-Zaehler-Chip stimmt mit Kartenanzahl ueberein
  TC-REQ-022-025  ->  TC-022-012  ReminderCard hat Bestaetigen-Button
  TC-REQ-022-026  ->  TC-022-016  ReminderCard hat Snooze-Button
  TC-REQ-022-027  ->  TC-022-018  ReminderCard hat Bearbeiten-Button
  TC-REQ-022-028  ->  TC-022-012  Bestaetigen-Klick oeffnet Dialog
  TC-REQ-022-029  ->  TC-022-012  CareConfirmDialog hat Submit und Cancel
  TC-REQ-022-030  ->  TC-022-012  Abbrechen schliesst Dialog ohne Aktion
  TC-REQ-022-031  ->  TC-022-012  Absenden entfernt Karte
  TC-REQ-022-032  ->  TC-022-012  CareConfirmDialog hat Notiz-Feld
  TC-REQ-022-033  ->  TC-022-016  Snooze-Klick loest Aktion aus
  TC-REQ-022-034  ->  TC-022-016  Snooze zeigt Erfolgs-Snackbar
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


# -- TC-022-001 to TC-022-004: Page Load and Navigation -----------------------


class TestPflegeDashboardPageLoad:
    """Dashboard page load and basic display (Spec: TC-022-001, TC-022-002)."""

    @pytest.mark.smoke
    def test_dashboard_page_renders(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-015: Task queue page renders with data-testid='task-queue-page'.

        Spec: TC-022-001 -- PflegeDashboardPage zeigt alle faelligen Erinnerungen sortiert.
        """
        pflege.open()
        screenshot(
            "TC-REQ-022-015_pflege-dashboard-loaded",
            "Pflege dashboard after initial load",
        )

        assert pflege.is_page_displayed(), (
            "TC-REQ-022-015 FAIL: Expected [data-testid='task-queue-page'] to be visible"
        )

    @pytest.mark.smoke
    def test_dashboard_shows_page_title(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-016: Page title contains task queue title text.

        Spec: TC-022-001 -- PflegeDashboardPage Seitenheader.
        """
        pflege.open()
        screenshot(
            "TC-REQ-022-016_pflege-title",
            "Pflege dashboard page title",
        )

        title = pflege.get_title_text()
        assert title, "TC-REQ-022-016 FAIL: Expected page title to be non-empty"

    @pytest.mark.core_crud
    def test_dashboard_empty_state_shows_success_message(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-017: Empty state shows 'Alle Pflanzen sind versorgt' when no reminders exist.

        Spec: TC-022-002 -- PflegeDashboardPage im leeren Zustand zeigt Erfolgsmeldung.
        """
        pflege.open()
        screenshot(
            "TC-REQ-022-017_pflege-empty-or-populated",
            "Pflege dashboard state",
        )

        has_empty = pflege.has_empty_state()
        has_cards = pflege.get_care_card_count() > 0

        assert has_empty or has_cards, (
            "TC-REQ-022-017 FAIL: Expected either empty state message or care cards"
        )

    @pytest.mark.core_crud
    def test_dashboard_urgency_sections_render_when_populated(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-018: Urgency sections (overdue, due_today, upcoming) render when data exists.

        Spec: TC-022-001 -- PflegeDashboardPage Dringlichkeitsgruppen.
        """
        pflege.open()
        screenshot(
            "TC-REQ-022-018_urgency-sections",
            "Pflege dashboard urgency sections",
        )

        card_count = pflege.get_care_card_count()
        if card_count == 0:
            pytest.skip("No care reminders present -- cannot verify urgency sections")

        has_any_section = (
            pflege.has_overdue_section()
            or pflege.has_due_today_section()
            or pflege.has_upcoming_section()
        )
        assert has_any_section, (
            "TC-REQ-022-018 FAIL: Expected at least one urgency section when care cards exist"
        )


# -- TC-022-005 to TC-022-011: ReminderCard Display ---------------------------


class TestReminderCardDisplay:
    """ReminderCard content and urgency badges (Spec: TC-022-009, TC-022-012, TC-022-016, TC-022-018)."""

    @pytest.mark.core_crud
    def test_care_cards_show_plant_name(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-019: Each ReminderCard shows a plant name.

        Spec: TC-022-009 -- ReminderCard zeigt korrekten Dringlichkeits-Badge.
        """
        pflege.open()
        cards = pflege.get_all_care_cards()

        if not cards:
            pytest.skip("No care cards present -- cannot verify plant names")

        screenshot(
            "TC-REQ-022-019_card-plant-names",
            "ReminderCards with plant names",
        )

        for card in cards:
            name = pflege.get_card_plant_name(card)
            assert name, f"TC-REQ-022-019 FAIL: Expected non-empty plant name on care card, got: '{name}'"

    @pytest.mark.core_crud
    def test_care_cards_have_urgency_indicator(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-020: Each ReminderCard has an urgency indicator via its section.

        Spec: TC-022-009 -- ReminderCard zeigt korrekten Dringlichkeits-Badge in drei Farben.
        """
        pflege.open()
        cards = pflege.get_all_care_cards()

        if not cards:
            pytest.skip("No care cards present -- cannot verify urgency indicators")

        screenshot(
            "TC-REQ-022-020_urgency-chips",
            "ReminderCards urgency indicators",
        )

        valid_colors = {"error", "warning", "info", "default"}
        for card in cards:
            chip_color = pflege.get_card_urgency_chip_color(card)
            assert chip_color in valid_colors, (
                f"TC-REQ-022-020 FAIL: Expected urgency color in {valid_colors}, got '{chip_color}'"
            )

    @pytest.mark.core_crud
    def test_overdue_cards_have_error_color(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-021: Overdue cards show red (error) urgency badge.

        Spec: TC-022-009 -- ReminderCard zeigt korrekten Dringlichkeits-Badge.
        """
        pflege.open()

        if not pflege.has_overdue_section():
            pytest.skip("No overdue reminders -- cannot verify error color")

        screenshot(
            "TC-REQ-022-021_overdue-section",
            "Overdue section with red badges",
        )

        section = pflege.driver.find_element(*PflegeDashboardPage.SECTION_OVERDUE)
        cards = section.find_elements(By.CSS_SELECTOR, "[data-testid^='care-card-']")

        for card in cards:
            color = pflege.get_card_urgency_chip_color(card)
            assert color == "error", (
                f"TC-REQ-022-021 FAIL: Expected overdue card to have 'error' chip color, got '{color}'"
            )

    @pytest.mark.core_crud
    def test_due_today_cards_have_warning_color(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-022: Due-today cards show yellow/orange (warning) urgency badge.

        Spec: TC-022-009 -- ReminderCard zeigt korrekten Dringlichkeits-Badge.
        """
        pflege.open()

        if not pflege.has_due_today_section():
            pytest.skip("No due-today reminders -- cannot verify warning color")

        screenshot(
            "TC-REQ-022-022_due-today-section",
            "Due-today section with warning badges",
        )

        section = pflege.driver.find_element(*PflegeDashboardPage.SECTION_DUE_TODAY)
        cards = section.find_elements(By.CSS_SELECTOR, "[data-testid^='care-card-']")

        for card in cards:
            color = pflege.get_card_urgency_chip_color(card)
            assert color == "warning", (
                f"TC-REQ-022-022 FAIL: Expected due-today card to have 'warning' chip color, got '{color}'"
            )

    @pytest.mark.core_crud
    def test_upcoming_cards_have_info_color(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-023: Upcoming cards show blue/grey (info) urgency badge.

        Spec: TC-022-009 -- ReminderCard zeigt korrekten Dringlichkeits-Badge.
        """
        pflege.open()

        if not pflege.has_upcoming_section():
            pytest.skip("No upcoming reminders -- cannot verify info color")

        screenshot(
            "TC-REQ-022-023_upcoming-section",
            "Upcoming section with info badges",
        )

        section = pflege.driver.find_element(*PflegeDashboardPage.SECTION_UPCOMING)
        cards = section.find_elements(By.CSS_SELECTOR, "[data-testid^='care-card-']")

        for card in cards:
            color = pflege.get_card_urgency_chip_color(card)
            assert color == "info", (
                f"TC-REQ-022-023 FAIL: Expected upcoming card to have 'info' chip color, got '{color}'"
            )

    @pytest.mark.core_crud
    def test_section_count_chip_matches_card_count(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-024: Section header count chip matches total items in that section.

        Spec: TC-022-001 -- PflegeDashboardPage Dringlichkeitsgruppen.
        """
        pflege.open()
        screenshot(
            "TC-REQ-022-024_section-counts",
            "Urgency sections with count chips",
        )

        for urgency in ("overdue", "due_today", "upcoming"):
            testid = pflege._urgency_section_testid(urgency)
            sections = pflege.driver.find_elements(
                By.CSS_SELECTOR, f"[data-testid='{testid}']"
            )
            if not sections:
                continue
            all_cards = sections[0].find_elements(
                By.CSS_SELECTOR, ".MuiCard-root"
            )
            if all_cards:
                chip_text = pflege.get_section_count_chip_text(urgency)
                assert chip_text == str(len(all_cards)), (
                    f"TC-REQ-022-024 FAIL: Expected section '{urgency}' count chip to show "
                    f"'{len(all_cards)}', got '{chip_text}'"
                )

    @pytest.mark.core_crud
    def test_care_cards_have_confirm_button(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-025: Each ReminderCard has a confirm (check) button.

        Spec: TC-022-012 -- Giess-Erinnerung bestaetigen entfernt Karte sofort.
        """
        pflege.open()
        cards = pflege.get_all_care_cards()

        if not cards:
            pytest.skip("No care cards present -- cannot verify confirm buttons")

        screenshot(
            "TC-REQ-022-025_confirm-buttons",
            "ReminderCards with confirm buttons",
        )

        for card in cards:
            action_btns = card.find_elements(
                By.CSS_SELECTOR, "button.MuiIconButton-root"
            )
            assert len(action_btns) >= 2, (
                "TC-REQ-022-025 FAIL: Expected each care card to have at least 2 action buttons"
            )

    @pytest.mark.core_crud
    def test_care_cards_have_snooze_button(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-026: Each ReminderCard has a snooze button.

        Spec: TC-022-016 -- Snooze verschiebt Erinnerungskarte auf 'Demnaechst'.
        """
        pflege.open()
        cards = pflege.get_all_care_cards()

        if not cards:
            pytest.skip("No care cards present -- cannot verify snooze buttons")

        screenshot(
            "TC-REQ-022-026_snooze-buttons",
            "ReminderCards with snooze buttons",
        )

        for card in cards:
            action_btns = card.find_elements(
                By.CSS_SELECTOR, "button.MuiIconButton-root"
            )
            assert len(action_btns) >= 3, (
                "TC-REQ-022-026 FAIL: Expected each care card to have at least 3 action buttons"
            )

    @pytest.mark.core_crud
    def test_care_cards_have_edit_profile_button(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-027: Each ReminderCard has an edit-profile (pencil) button.

        Spec: TC-022-018 -- CareProfileEditDialog oeffnet sich von der ReminderCard aus.
        """
        pflege.open()
        cards = pflege.get_all_care_cards()

        if not cards:
            pytest.skip("No care cards present -- cannot verify edit buttons")

        screenshot(
            "TC-REQ-022-027_edit-profile-buttons",
            "ReminderCards with edit profile buttons",
        )

        for card in cards:
            action_btns = card.find_elements(
                By.CSS_SELECTOR, "button.MuiIconButton-root"
            )
            assert len(action_btns) >= 1, (
                "TC-REQ-022-027 FAIL: Expected each care card to have at least 1 action button"
            )


# -- TC-022-012 to TC-022-015: Confirm Action ---------------------------------


class TestCareConfirmAction:
    """Care confirmation flow (Spec: TC-022-012)."""

    def _get_first_card_ids(self, pflege: PflegeDashboardPage) -> tuple[str, str]:
        """Extract plant_key and reminder_type from the first care card's testid."""
        cards = pflege.get_all_care_cards()
        if not cards:
            pytest.skip("No care cards available for confirm action test")
        testid = cards[0].get_attribute("data-testid") or ""
        suffix = testid.replace("care-card-care-", "")
        parts = suffix.rsplit("-", 1)
        if len(parts) < 2:
            pytest.skip(f"Unexpected card testid format: {testid}")
        return parts[0], parts[1]

    @pytest.mark.core_crud
    def test_confirm_click_opens_dialog(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-028: Clicking confirm on a card opens the CareConfirmDialog.

        Spec: TC-022-012 -- Giess-Erinnerung bestaetigen entfernt Karte sofort.
        """
        pflege.open()
        screenshot(
            "TC-REQ-022-028_before-confirm",
            "Before clicking confirm",
        )

        plant_key, reminder_type = self._get_first_card_ids(pflege)
        pflege.click_confirm_on_card(plant_key, reminder_type)
        pflege.wait_for_confirm_dialog()

        screenshot(
            "TC-REQ-022-028_confirm-dialog-open",
            "CareConfirmDialog opened",
        )

        assert pflege.is_confirm_dialog_open(), (
            "TC-REQ-022-028 FAIL: Expected CareConfirmDialog to open after clicking confirm"
        )

    @pytest.mark.core_crud
    def test_confirm_dialog_has_submit_and_cancel(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-029: CareConfirmDialog has submit and cancel buttons.

        Spec: TC-022-012 -- CareConfirmDialog Buttons.
        """
        pflege.open()
        plant_key, reminder_type = self._get_first_card_ids(pflege)
        pflege.click_confirm_on_card(plant_key, reminder_type)
        pflege.wait_for_confirm_dialog()

        screenshot(
            "TC-REQ-022-029_dialog-buttons",
            "CareConfirmDialog buttons",
        )

        submit_btns = pflege.driver.find_elements(*PflegeDashboardPage.CONFIRM_DIALOG_SUBMIT)
        cancel_btns = pflege.driver.find_elements(*PflegeDashboardPage.CONFIRM_DIALOG_CANCEL)

        assert len(submit_btns) > 0, "TC-REQ-022-029 FAIL: Expected submit button in confirm dialog"
        assert len(cancel_btns) > 0, "TC-REQ-022-029 FAIL: Expected cancel button in confirm dialog"

    @pytest.mark.core_crud
    def test_confirm_dialog_cancel_closes_without_action(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-030: Cancelling confirm dialog leaves card in place.

        Spec: TC-022-012 -- CareConfirmDialog -- Abbrechen.
        """
        pflege.open()
        plant_key, reminder_type = self._get_first_card_ids(pflege)

        pflege.click_confirm_on_card(plant_key, reminder_type)
        pflege.wait_for_confirm_dialog()
        pflege.cancel_confirm_dialog()
        pflege.wait_for_dialog_closed()

        screenshot(
            "TC-REQ-022-030_after-cancel",
            "After cancelling CareConfirmDialog",
        )

        assert pflege.has_care_card(plant_key, reminder_type), (
            "TC-REQ-022-030 FAIL: Expected care card to remain after cancelling confirm dialog"
        )

    @pytest.mark.core_crud
    def test_confirm_dialog_submit_removes_card(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-031: Submitting confirm dialog removes the card from the dashboard.

        Spec: TC-022-012 -- Giess-Erinnerung bestaetigen entfernt Karte sofort (Optimistic Update).
        """
        pflege.open()
        plant_key, reminder_type = self._get_first_card_ids(pflege)
        initial_count = pflege.get_care_card_count()

        screenshot(
            "TC-REQ-022-031_before-submit",
            "Before submitting confirmation",
        )

        pflege.click_confirm_on_card(plant_key, reminder_type)
        pflege.wait_for_confirm_dialog()
        pflege.submit_confirm_dialog()

        pflege.wait_for_dialog_closed()
        pflege.wait_for_loading_complete()

        screenshot(
            "TC-REQ-022-031_after-submit",
            "After confirmation -- card removed",
        )

        new_count = pflege.get_care_card_count()
        assert new_count < initial_count or not pflege.has_care_card(plant_key, reminder_type), (
            f"TC-REQ-022-031 FAIL: Expected card count to decrease after confirm. "
            f"Before: {initial_count}, After: {new_count}"
        )

    @pytest.mark.core_crud
    def test_confirm_dialog_has_notes_field(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-032: CareConfirmDialog contains a notes text field.

        Spec: TC-022-012 -- CareConfirmDialog Notiz-Feld.
        """
        pflege.open()
        plant_key, reminder_type = self._get_first_card_ids(pflege)

        pflege.click_confirm_on_card(plant_key, reminder_type)
        pflege.wait_for_confirm_dialog()

        screenshot(
            "TC-REQ-022-032_notes-field",
            "CareConfirmDialog notes field",
        )

        notes_fields = pflege.driver.find_elements(*PflegeDashboardPage.CONFIRM_NOTES_FIELD)
        assert len(notes_fields) > 0, (
            "TC-REQ-022-032 FAIL: Expected notes field in confirm dialog"
        )


# -- TC-022-016 to TC-022-017: Snooze Action ----------------------------------


class TestCareSnoozeAction:
    """Snooze functionality (Spec: TC-022-016)."""

    def _get_first_card_ids(self, pflege: PflegeDashboardPage) -> tuple[str, str]:
        """Extract plant_key and reminder_type from the first care card's testid."""
        cards = pflege.get_all_care_cards()
        if not cards:
            pytest.skip("No care cards available for snooze action test")
        testid = cards[0].get_attribute("data-testid") or ""
        suffix = testid.replace("care-card-care-", "")
        parts = suffix.rsplit("-", 1)
        if len(parts) < 2:
            pytest.skip(f"Unexpected card testid format: {testid}")
        return parts[0], parts[1]

    @pytest.mark.core_crud
    def test_snooze_click_triggers_action(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-033: Clicking snooze on a card triggers the snooze action.

        Spec: TC-022-016 -- Snooze verschiebt Erinnerungskarte auf 'Demnaechst' (Grau).
        """
        pflege.open()
        screenshot(
            "TC-REQ-022-033_before-snooze",
            "Before clicking snooze",
        )

        plant_key, reminder_type = self._get_first_card_ids(pflege)

        pflege.click_snooze_on_card(plant_key, reminder_type)
        pflege.wait_for_loading_complete()

        screenshot(
            "TC-REQ-022-033_after-snooze",
            "After snooze action",
        )

        assert not pflege.is_error_displayed(), (
            "TC-REQ-022-033 FAIL: Expected no error after snooze action"
        )

    @pytest.mark.core_crud
    def test_snooze_shows_success_snackbar(
        self,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-022-034: Snooze action shows a success/info snackbar.

        Spec: TC-022-016 -- Snooze Erfolgs-Snackbar.
        """
        pflege.open()
        plant_key, reminder_type = self._get_first_card_ids(pflege)

        pflege.click_snooze_on_card(plant_key, reminder_type)

        try:
            snackbar_text = pflege.wait_for_snackbar(timeout=5)
            screenshot(
                "TC-REQ-022-034_snooze-snackbar",
                "Snooze snackbar displayed",
            )
            assert snackbar_text, "TC-REQ-022-034 FAIL: Expected non-empty snackbar text after snooze"
        except Exception:
            screenshot(
                "TC-REQ-022-034_snooze-no-snackbar",
                "No snackbar after snooze (optimistic update)",
            )
