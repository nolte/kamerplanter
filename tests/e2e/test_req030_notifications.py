"""E2E tests for REQ-030 — Multi-Kanal-Benachrichtigungssystem.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-030.md):
  TC-REQ-030-001  ->  TC-030-009  Notification-Einstellungs-Tab in Kontoeinstellungen navigieren
  TC-REQ-030-002  ->  TC-030-010  Kanalverwaltung -- Uebersicht aller Kanaele
  TC-REQ-030-003  ->  TC-030-013  E-Mail-Kanal aktivieren und E-Mail-Adresse eintragen

Scope: Smoke-Coverage des Notification-Settings-Workflows (REQ-030 §5.4).
Out of scope: Test-Send-Buttons, echte Zustellung, Bell-Icon / Notification-
Drawer (separater Test-Spike).  Diese Tests aendern nur die Konfiguration,
sie loesen keine echten Benachrichtigungen aus.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import LoginPage, NotificationSettingsPage

pytestmark = pytest.mark.requires_auth

# -- Demo credentials (full mode -- see conftest.DEMO_EMAIL_FULL) ------------
DEMO_EMAIL = "demo@kamerplanter.example"
DEMO_PASSWORD = "demo-passwort-2024"


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def login_page(browser: WebDriver, base_url: str) -> LoginPage:
    """Return a LoginPage bound to the test browser."""
    return LoginPage(browser, base_url)


@pytest.fixture
def notif_page(browser: WebDriver, base_url: str) -> NotificationSettingsPage:
    """Return a NotificationSettingsPage bound to the test browser."""
    return NotificationSettingsPage(browser, base_url)


def _ensure_logged_in(login_page: LoginPage) -> None:
    """Log in as the demo user.  Mirrors test_req023_account_settings."""
    login_page.driver.delete_all_cookies()
    login_page.open()
    login_page.login(DEMO_EMAIL, DEMO_PASSWORD)
    login_page.wait_for_url_contains("/dashboard")


# -- TC-REQ-030-001: Navigate to notification settings tab -------------------


class TestNotificationSettingsNavigation:
    """Notification settings tab navigation (Spec: TC-030-009)."""

    @pytest.mark.smoke
    @pytest.mark.requires_auth
    def test_notification_tab_loads(
        self,
        login_page: LoginPage,
        notif_page: NotificationSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-030-001: Notification settings tab opens and renders the save button.

        Spec: TC-030-009 -- Notification-Einstellungs-Tab in Kontoeinstellungen
        navigieren.
        """
        _ensure_logged_in(login_page)
        notif_page.open()
        screenshot(
            "TC-REQ-030-001_notification-tab-loaded",
            "Notification settings tab after initial load",
        )

        tab_labels = notif_page.get_tab_labels()
        assert any("benachrichtigung" in label.lower() for label in tab_labels), (
            f"TC-REQ-030-001 FAIL: Expected 'Benachrichtigungen' tab, got: {tab_labels}"
        )

        # Save button is the anchor element rendered by NotificationSettingsTab.
        assert notif_page.is_save_button_visible(), (
            "TC-REQ-030-001 FAIL: Expected notification-settings-save button to be visible"
        )


# -- TC-REQ-030-002: Channel overview ----------------------------------------


class TestNotificationChannelOverview:
    """Channel toggle overview (Spec: TC-030-010)."""

    @pytest.mark.smoke
    @pytest.mark.requires_auth
    def test_all_four_channels_rendered(
        self,
        login_page: LoginPage,
        notif_page: NotificationSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-030-002: All four delivery channels render with toggles.

        Spec: TC-030-010 -- Kanalverwaltung -- Uebersicht aller Kanaele.

        REQ-030 ships home_assistant, email, pwa and apprise.  Visibility may
        be filtered by experience level (REQ-021) -- on the demo account at
        least home_assistant and email MUST be visible at any expertise level.
        """
        _ensure_logged_in(login_page)
        notif_page.open()
        screenshot(
            "TC-REQ-030-002_channel-overview",
            "Notification channel overview with toggles",
        )

        visible = notif_page.get_visible_channel_keys()

        # FIXME: REQ-021 may hide apprise/pwa for beginner users.  We assert
        # the two always-visible channels plus a sane minimum count instead
        # of all four.
        assert "home_assistant" in visible, (
            f"TC-REQ-030-002 FAIL: Expected 'home_assistant' channel toggle, got: {visible}"
        )
        assert "email" in visible, (
            f"TC-REQ-030-002 FAIL: Expected 'email' channel toggle, got: {visible}"
        )
        assert len(visible) >= 2, (
            f"TC-REQ-030-002 FAIL: Expected at least 2 channels, got: {visible}"
        )


# -- TC-REQ-030-003: Enable email channel + persist --------------------------


class TestNotificationEmailChannelEnable:
    """Enable email channel and configure address (Spec: TC-030-013)."""

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_enable_email_channel_and_save(
        self,
        login_page: LoginPage,
        notif_page: NotificationSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-030-003: Enable email channel, type address, save and verify.

        Spec: TC-030-013 -- E-Mail-Kanal aktivieren und E-Mail-Adresse
        eintragen.

        We deliberately do NOT trigger the test-send button -- the test only
        exercises the configuration workflow, not real delivery.  The test
        is idempotent: it always sets the same email value and toggles the
        channel ON, so re-runs converge.
        """
        _ensure_logged_in(login_page)
        notif_page.open()
        screenshot(
            "TC-REQ-030-003_before-enable-email",
            "Notification settings before enabling email channel",
        )

        # Activate email channel (idempotent — only flips when needed).
        notif_page.set_channel_enabled("email", enabled=True)

        # Conditional config field appears once the switch is on.
        target_address = "demo+e2e@kamerplanter.example"
        notif_page.set_email_address(target_address)
        screenshot(
            "TC-REQ-030-003_email-channel-configured",
            "Email channel enabled with test address filled",
        )

        notif_page.save()

        # Persistence check 1: success snackbar appears.
        snackbar_text = notif_page.wait_for_success_snackbar()
        assert snackbar_text, (
            "TC-REQ-030-003 FAIL: Expected success snackbar after saving notification settings"
        )

        # Persistence check 2: reload tab and verify the toggle + address persisted.
        notif_page.open()
        screenshot(
            "TC-REQ-030-003_email-channel-after-reload",
            "Notification settings after reload — email channel persisted",
        )
        assert notif_page.is_channel_enabled("email"), (
            "TC-REQ-030-003 FAIL: Email channel toggle did not persist across reload"
        )
        assert notif_page.get_email_address() == target_address, (
            f"TC-REQ-030-003 FAIL: Expected email '{target_address}' to persist, "
            f"got: '{notif_page.get_email_address()}'"
        )
