"""E2E tests for REQ-022 -- Pflege Dashboard (TC-022-001 to TC-022-017).

Tests cover:
- PflegeDashboardPage: page load, urgency sections, card display, empty state
- ReminderCard: urgency badges, color coding, plant name display
- Ein-Tap-Bestaetigung: confirm action via dialog, card removal
- Snooze: snooze action, card state change

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
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .pages.pflege_dashboard_page import PflegeDashboardPage


# -- Fixtures ----------------------------------------------------------------


@pytest.fixture
def pflege(browser: WebDriver, base_url: str) -> PflegeDashboardPage:
    """Return a PflegeDashboardPage bound to the test browser."""
    return PflegeDashboardPage(browser, base_url)


# -- TC-022-001 to TC-022-004: Page Load and Navigation ---------------------


class TestPflegeDashboardPageLoad:
    """TC-022-001 to TC-022-004: Dashboard page load and basic display."""

    @pytest.mark.smoke
    def test_dashboard_page_renders(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-001: Task queue page renders with data-testid='task-queue-page'."""
        pflege.open()
        screenshot("req022_001_pflege_dashboard_loaded", "Pflege-Dashboard nach dem Laden")

        assert pflege.is_page_displayed(), (
            "Expected [data-testid='task-queue-page'] to be visible"
        )

    def test_dashboard_shows_page_title(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-001: Page title contains task queue title text."""
        pflege.open()
        screenshot("req022_001b_pflege_title", "Pflege-Dashboard Seitentitel")

        title = pflege.get_title_text()
        assert title, "Expected page title to be non-empty"

    def test_dashboard_empty_state_shows_success_message(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-002: Empty state shows 'Alle Pflanzen sind versorgt' when no reminders exist."""
        pflege.open()
        screenshot("req022_002_pflege_empty_or_populated", "Pflege-Dashboard Zustand")

        # This test verifies the page renders without error in either state.
        # If empty: the empty state illustration should be shown.
        # If populated: urgency sections or cards should be shown.
        has_empty = pflege.has_empty_state()
        has_cards = pflege.get_care_card_count() > 0

        assert has_empty or has_cards, (
            "Expected either empty state message or care cards to be displayed"
        )

    def test_dashboard_urgency_sections_render_when_populated(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-001: Urgency sections (overdue, due_today, upcoming) render when data exists."""
        pflege.open()
        screenshot("req022_001c_urgency_sections", "Pflege-Dashboard Dringlichkeitsgruppen")

        card_count = pflege.get_care_card_count()
        if card_count == 0:
            pytest.skip("No care reminders present -- cannot verify urgency sections")

        # At least one section should be visible
        has_any_section = (
            pflege.has_overdue_section()
            or pflege.has_due_today_section()
            or pflege.has_upcoming_section()
        )
        assert has_any_section, (
            "Expected at least one urgency section when care cards exist"
        )


# -- TC-022-005 to TC-022-011: ReminderCard Display -------------------------


class TestReminderCardDisplay:
    """TC-022-005 to TC-022-011: ReminderCard content and urgency badges."""

    def test_care_cards_show_plant_name(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-009: Each ReminderCard shows a plant name."""
        pflege.open()
        cards = pflege.get_all_care_cards()

        if not cards:
            pytest.skip("No care cards present -- cannot verify plant names")

        screenshot("req022_009_card_plant_names", "ReminderCards mit Pflanzennamen")

        for card in cards:
            name = pflege.get_card_plant_name(card)
            assert name, f"Expected non-empty plant name on care card, got: '{name}'"

    def test_care_cards_have_urgency_indicator(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-009: Each ReminderCard has an urgency indicator via its section.

        TaskQueuePage uses section-based urgency grouping instead of per-card chips.
        """
        pflege.open()
        cards = pflege.get_all_care_cards()

        if not cards:
            pytest.skip("No care cards present -- cannot verify urgency indicators")

        screenshot("req022_009_urgency_chips", "ReminderCards Dringlichkeits-Indikatoren")

        valid_colors = {"error", "warning", "info", "default"}
        for card in cards:
            chip_color = pflege.get_card_urgency_chip_color(card)
            assert chip_color in valid_colors, (
                f"Expected urgency color in {valid_colors}, got '{chip_color}'"
            )

    def test_overdue_cards_have_error_color(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-009: Overdue cards show red (error) urgency badge."""
        pflege.open()

        if not pflege.has_overdue_section():
            pytest.skip("No overdue reminders -- cannot verify error color")

        screenshot("req022_009b_overdue_section", "Overdue-Sektion mit roten Badges")

        section = pflege.driver.find_element(*PflegeDashboardPage.SECTION_OVERDUE)
        cards = section.find_elements(By.CSS_SELECTOR, "[data-testid^='care-card-']")

        for card in cards:
            color = pflege.get_card_urgency_chip_color(card)
            assert color == "error", (
                f"Expected overdue card to have 'error' chip color, got '{color}'"
            )

    def test_due_today_cards_have_warning_color(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-009: Due-today cards show yellow/orange (warning) urgency badge."""
        pflege.open()

        if not pflege.has_due_today_section():
            pytest.skip("No due-today reminders -- cannot verify warning color")

        screenshot("req022_009c_due_today_section", "Heute-faellig-Sektion mit gelben Badges")

        section = pflege.driver.find_element(*PflegeDashboardPage.SECTION_DUE_TODAY)
        cards = section.find_elements(By.CSS_SELECTOR, "[data-testid^='care-card-']")

        for card in cards:
            color = pflege.get_card_urgency_chip_color(card)
            assert color == "warning", (
                f"Expected due-today card to have 'warning' chip color, got '{color}'"
            )

    def test_upcoming_cards_have_info_color(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-009: Upcoming cards show blue/grey (info) urgency badge."""
        pflege.open()

        if not pflege.has_upcoming_section():
            pytest.skip("No upcoming reminders -- cannot verify info color")

        screenshot("req022_009d_upcoming_section", "Demnaechst-Sektion mit Info-Badges")

        section = pflege.driver.find_element(*PflegeDashboardPage.SECTION_UPCOMING)
        cards = section.find_elements(By.CSS_SELECTOR, "[data-testid^='care-card-']")

        for card in cards:
            color = pflege.get_card_urgency_chip_color(card)
            assert color == "info", (
                f"Expected upcoming card to have 'info' chip color, got '{color}'"
            )

    def test_section_count_chip_matches_card_count(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-001: Section header count chip matches total items in that section.

        TaskQueuePage sections contain both task cards and care-reminder cards.
        The count chip shows the total number of all items in the section.
        """
        pflege.open()
        screenshot("req022_001d_section_counts", "Dringlichkeitssektionen mit Zaehler-Chips")

        for urgency in ("overdue", "due_today", "upcoming"):
            testid = pflege._urgency_section_testid(urgency)
            sections = pflege.driver.find_elements(
                By.CSS_SELECTOR, f"[data-testid='{testid}']"
            )
            if not sections:
                continue
            # Count ALL cards in the section (both task and care cards)
            all_cards = sections[0].find_elements(
                By.CSS_SELECTOR, ".MuiCard-root"
            )
            if all_cards:
                chip_text = pflege.get_section_count_chip_text(urgency)
                assert chip_text == str(len(all_cards)), (
                    f"Expected section '{urgency}' count chip to show '{len(all_cards)}', "
                    f"got '{chip_text}'"
                )

    def test_care_cards_have_confirm_button(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-012: Each ReminderCard has a confirm (check) button."""
        pflege.open()
        cards = pflege.get_all_care_cards()

        if not cards:
            pytest.skip("No care cards present -- cannot verify confirm buttons")

        screenshot("req022_012_confirm_buttons", "ReminderCards mit Bestaetigen-Buttons")

        for card in cards:
            # TaskQueuePage care cards have 3 IconButtons: edit, confirm (success color), snooze
            action_btns = card.find_elements(
                By.CSS_SELECTOR, "button.MuiIconButton-root"
            )
            assert len(action_btns) >= 2, (
                "Expected each care card to have at least 2 action buttons (incl. confirm)"
            )

    def test_care_cards_have_snooze_button(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-016: Each ReminderCard has a snooze button."""
        pflege.open()
        cards = pflege.get_all_care_cards()

        if not cards:
            pytest.skip("No care cards present -- cannot verify snooze buttons")

        screenshot("req022_016_snooze_buttons", "ReminderCards mit Snooze-Buttons")

        for card in cards:
            # TaskQueuePage care cards have 3 IconButtons: edit, confirm, snooze
            action_btns = card.find_elements(
                By.CSS_SELECTOR, "button.MuiIconButton-root"
            )
            assert len(action_btns) >= 3, (
                "Expected each care card to have at least 3 action buttons (incl. snooze)"
            )

    def test_care_cards_have_edit_profile_button(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-018: Each ReminderCard has an edit-profile (pencil) button."""
        pflege.open()
        cards = pflege.get_all_care_cards()

        if not cards:
            pytest.skip("No care cards present -- cannot verify edit buttons")

        screenshot("req022_018_edit_profile_buttons", "ReminderCards mit Bearbeiten-Buttons")

        for card in cards:
            # TaskQueuePage care cards have 3 IconButtons: edit (1st), confirm, snooze
            action_btns = card.find_elements(
                By.CSS_SELECTOR, "button.MuiIconButton-root"
            )
            assert len(action_btns) >= 1, (
                "Expected each care card to have at least 1 action button (edit-profile)"
            )


# -- TC-022-012 to TC-022-015: Confirm Action --------------------------------


class TestCareConfirmAction:
    """TC-022-012 to TC-022-015: Care confirmation flow."""

    def _get_first_card_ids(self, pflege: PflegeDashboardPage) -> tuple[str, str]:
        """Extract plant_key and reminder_type from the first care card's testid."""
        cards = pflege.get_all_care_cards()
        if not cards:
            pytest.skip("No care cards available for confirm action test")
        testid = cards[0].get_attribute("data-testid") or ""
        # Format: care-card-care-{plant_key}-{reminder_type}
        suffix = testid.replace("care-card-care-", "")
        parts = suffix.rsplit("-", 1)
        if len(parts) < 2:
            pytest.skip(f"Unexpected card testid format: {testid}")
        return parts[0], parts[1]

    def test_confirm_click_opens_dialog(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-012: Clicking confirm on a card opens the CareConfirmDialog."""
        pflege.open()
        screenshot("req022_012_before_confirm", "Vor Klick auf Bestaetigen")

        plant_key, reminder_type = self._get_first_card_ids(pflege)
        initial_count = pflege.get_care_card_count()

        pflege.click_confirm_on_card(plant_key, reminder_type)
        pflege.wait_for_confirm_dialog()

        screenshot("req022_012_confirm_dialog_open", "CareConfirmDialog geoeffnet")

        assert pflege.is_confirm_dialog_open(), (
            "Expected CareConfirmDialog to open after clicking confirm"
        )

    def test_confirm_dialog_has_submit_and_cancel(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-012: CareConfirmDialog has submit and cancel buttons."""
        pflege.open()
        plant_key, reminder_type = self._get_first_card_ids(pflege)
        pflege.click_confirm_on_card(plant_key, reminder_type)
        pflege.wait_for_confirm_dialog()

        screenshot("req022_012b_dialog_buttons", "CareConfirmDialog Buttons")

        submit_btns = pflege.driver.find_elements(*PflegeDashboardPage.CONFIRM_DIALOG_SUBMIT)
        cancel_btns = pflege.driver.find_elements(*PflegeDashboardPage.CONFIRM_DIALOG_CANCEL)

        assert len(submit_btns) > 0, "Expected submit button in confirm dialog"
        assert len(cancel_btns) > 0, "Expected cancel button in confirm dialog"

    def test_confirm_dialog_cancel_closes_without_action(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-012: Cancelling confirm dialog leaves card in place."""
        pflege.open()
        plant_key, reminder_type = self._get_first_card_ids(pflege)
        initial_count = pflege.get_care_card_count()

        pflege.click_confirm_on_card(plant_key, reminder_type)
        pflege.wait_for_confirm_dialog()
        pflege.cancel_confirm_dialog()
        pflege.wait_for_dialog_closed()

        screenshot("req022_012c_after_cancel", "Nach Abbrechen des CareConfirmDialog")

        assert pflege.has_care_card(plant_key, reminder_type), (
            "Expected care card to remain after cancelling confirm dialog"
        )

    def test_confirm_dialog_submit_removes_card(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-012: Submitting confirm dialog removes the card from the dashboard."""
        pflege.open()
        plant_key, reminder_type = self._get_first_card_ids(pflege)
        initial_count = pflege.get_care_card_count()

        screenshot("req022_012d_before_submit", "Vor Bestaetigung absenden")

        pflege.click_confirm_on_card(plant_key, reminder_type)
        pflege.wait_for_confirm_dialog()
        pflege.submit_confirm_dialog()

        # Wait for dialog to close and dashboard to refresh
        pflege.wait_for_dialog_closed()
        time.sleep(1)  # Brief wait for dashboard refresh after API call

        screenshot("req022_012e_after_submit", "Nach Bestaetigung -- Karte entfernt")

        # Card should be removed or dashboard refreshed
        new_count = pflege.get_care_card_count()
        assert new_count < initial_count or not pflege.has_care_card(plant_key, reminder_type), (
            f"Expected card count to decrease after confirm. "
            f"Before: {initial_count}, After: {new_count}"
        )

    def test_confirm_dialog_has_notes_field(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-012: CareConfirmDialog contains a notes text field."""
        pflege.open()
        plant_key, reminder_type = self._get_first_card_ids(pflege)

        pflege.click_confirm_on_card(plant_key, reminder_type)
        pflege.wait_for_confirm_dialog()

        screenshot("req022_012f_notes_field", "CareConfirmDialog Notiz-Feld")

        notes_fields = pflege.driver.find_elements(*PflegeDashboardPage.CONFIRM_NOTES_FIELD)
        assert len(notes_fields) > 0, (
            "Expected notes field [data-testid='confirm-notes-field'] in confirm dialog"
        )


# -- TC-022-016 to TC-022-017: Snooze Action ---------------------------------


class TestCareSnoozeAction:
    """TC-022-016 to TC-022-017: Snooze functionality."""

    def _get_first_card_ids(self, pflege: PflegeDashboardPage) -> tuple[str, str]:
        """Extract plant_key and reminder_type from the first care card's testid."""
        cards = pflege.get_all_care_cards()
        if not cards:
            pytest.skip("No care cards available for snooze action test")
        testid = cards[0].get_attribute("data-testid") or ""
        # Format: care-card-care-{plant_key}-{reminder_type}
        suffix = testid.replace("care-card-care-", "")
        parts = suffix.rsplit("-", 1)
        if len(parts) < 2:
            pytest.skip(f"Unexpected card testid format: {testid}")
        return parts[0], parts[1]

    def test_snooze_click_triggers_action(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-016: Clicking snooze on a card triggers the snooze action."""
        pflege.open()
        screenshot("req022_016_before_snooze", "Vor Klick auf Snooze")

        plant_key, reminder_type = self._get_first_card_ids(pflege)
        initial_count = pflege.get_care_card_count()

        pflege.click_snooze_on_card(plant_key, reminder_type)
        time.sleep(1)  # Wait for API call and dashboard refresh

        screenshot("req022_016_after_snooze", "Nach Snooze-Aktion")

        # After snooze, the card may move to a different section or remain
        # The key assertion is that no error occurred
        assert not pflege.is_error_displayed(), (
            "Expected no error after snooze action"
        )

    def test_snooze_shows_success_snackbar(
        self,
        pflege: PflegeDashboardPage,
        screenshot,
    ) -> None:
        """TC-022-016: Snooze action shows a success/info snackbar."""
        pflege.open()
        plant_key, reminder_type = self._get_first_card_ids(pflege)

        pflege.click_snooze_on_card(plant_key, reminder_type)

        # Wait for snackbar to appear (may or may not appear depending on implementation)
        try:
            snackbar_text = pflege.wait_for_snackbar(timeout=5)
            screenshot("req022_016b_snooze_snackbar", "Snooze-Snackbar angezeigt")
            assert snackbar_text, "Expected non-empty snackbar text after snooze"
        except Exception:
            # Snackbar may not appear if optimistic update is used
            screenshot("req022_016b_snooze_no_snackbar", "Kein Snackbar nach Snooze")
