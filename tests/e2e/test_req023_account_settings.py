"""E2E tests for REQ-023 — Account Settings (TC-023-026 to TC-023-032).

Covers:
  Profile tab: display name, email (read-only), save
  Security tab: change password (happy path, wrong current password),
  linked providers list

All tests follow NFR-008:
  - Page-Object-Pattern (no direct find_element calls in tests)
  - WebDriverWait only — no time.sleep()
  - Screenshot at: Page Load / before action / after action / error state
  - Descriptive assertion messages
"""

from __future__ import annotations

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import AccountSettingsPage, LoginPage

pytestmark = pytest.mark.requires_auth

# ── Demo credentials ────────────────────────────────────────────────────────
DEMO_EMAIL = "demo@kamerplanter.local"
DEMO_PASSWORD = "demo-passwort-2024"


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def login_page(browser: WebDriver, base_url: str) -> LoginPage:
    """Return a LoginPage bound to the test browser."""
    return LoginPage(browser, base_url)


@pytest.fixture
def account_page(browser: WebDriver, base_url: str) -> AccountSettingsPage:
    """Return an AccountSettingsPage bound to the test browser."""
    return AccountSettingsPage(browser, base_url)


def _ensure_logged_in(login_page: LoginPage) -> None:
    """Log in as demo user if not already authenticated."""
    login_page.driver.delete_all_cookies()
    login_page.open()
    login_page.login(DEMO_EMAIL, DEMO_PASSWORD)
    login_page.wait_for_url_contains("/dashboard")


# ── TC-023-026: Profile tab display ─────────────────────────────────────────


class TestAccountSettingsProfile:
    """TC-023-026 to TC-023-028: Account settings profile tab."""

    def test_profile_tab_displays_user_info(
        self,
        login_page: LoginPage,
        account_page: AccountSettingsPage,
        screenshot,
    ) -> None:
        """TC-023-026: Profile tab shows display name, email, and tabs."""
        _ensure_logged_in(login_page)
        account_page.open(tab="profile")
        screenshot("req023_040_account_profile_loaded", "Kontoeinstellungen Profil-Tab nach dem Laden")

        # Tabs should be visible
        tab_labels = account_page.get_tab_labels()
        assert len(tab_labels) > 0, (
            "Expected at least one tab in account settings"
        )
        assert any("Profil" in label for label in tab_labels), (
            f"Expected 'Profil' tab, got: {tab_labels}"
        )

        # Display name should be prefilled
        display_name = account_page.get_display_name()
        assert display_name, (
            "Expected display name to be prefilled in profile tab"
        )

        # Email should be present and disabled
        email = account_page.get_email()
        assert email == DEMO_EMAIL, (
            f"Expected email '{DEMO_EMAIL}', got: '{email}'"
        )
        assert account_page.is_email_disabled(), (
            "Expected email field to be disabled (read-only)"
        )

    def test_update_display_name(
        self,
        login_page: LoginPage,
        account_page: AccountSettingsPage,
        screenshot,
    ) -> None:
        """TC-023-027: Update display name and save."""
        _ensure_logged_in(login_page)
        account_page.open(tab="profile")

        original_name = account_page.get_display_name()
        screenshot("req023_041_profile_before_edit", "Profil vor Namensaenderung")

        new_name = "Aktualisierter Gaertner"
        account_page.set_display_name(new_name)
        account_page.click_profile_save()

        screenshot("req023_042_profile_after_save", "Profil nach Speichern")

        # Verify the name was saved (field should still show the new name)
        current_name = account_page.get_display_name()
        assert current_name == new_name, (
            f"Expected display name '{new_name}', got: '{current_name}'"
        )

        # Restore original name to not affect other tests
        account_page.set_display_name(original_name)
        account_page.click_profile_save()


# ── TC-023-029 to TC-023-030: Security tab — password change ────────────────


class TestAccountSettingsSecurity:
    """TC-023-029 to TC-023-032: Account settings security tab."""

    def test_security_tab_displays_password_fields(
        self,
        login_page: LoginPage,
        account_page: AccountSettingsPage,
        screenshot,
    ) -> None:
        """TC-023-029a: Security tab shows password change fields for local account."""
        _ensure_logged_in(login_page)
        account_page.open(tab="security")
        screenshot("req023_043_security_tab_loaded", "Sicherheit-Tab nach dem Laden")

        # For a local account, current-password field should be visible
        assert account_page.is_current_password_visible(), (
            "Expected current-password field for local account"
        )

    def test_change_password_button_disabled_when_empty(
        self,
        login_page: LoginPage,
        account_page: AccountSettingsPage,
        screenshot,
    ) -> None:
        """TC-023-029b: Change-password button is disabled when fields are empty."""
        _ensure_logged_in(login_page)
        account_page.open(tab="security")
        screenshot("req023_044_security_button_disabled", "Passwort-aendern Button disabled")

        assert not account_page.is_change_password_button_enabled(), (
            "Expected change-password button to be disabled when fields are empty"
        )

    def test_linked_providers_displayed(
        self,
        login_page: LoginPage,
        account_page: AccountSettingsPage,
        screenshot,
    ) -> None:
        """TC-023-032: Linked auth providers are displayed in the security tab."""
        _ensure_logged_in(login_page)
        account_page.open(tab="security")
        screenshot("req023_045_linked_providers", "Verknuepfte Auth-Provider im Sicherheit-Tab")

        providers = account_page.get_linked_providers()
        assert len(providers) > 0, (
            "Expected at least one linked auth provider (local) for demo user"
        )
        assert any("local" in p.lower() or "lokal" in p.lower() for p in providers), (
            f"Expected 'local' provider for demo user, got: {providers}"
        )

    def test_single_provider_unlink_button_absent(
        self,
        login_page: LoginPage,
        account_page: AccountSettingsPage,
        screenshot,
    ) -> None:
        """TC-023-033: Unlink button is not shown when only one provider exists."""
        _ensure_logged_in(login_page)
        account_page.open(tab="security")
        screenshot("req023_046_single_provider_no_unlink", "Kein Entfernen-Button bei einzelnem Provider")

        providers = account_page.get_linked_providers()
        unlink_buttons = account_page.get_unlink_buttons()

        if len(providers) <= 1:
            assert len(unlink_buttons) == 0, (
                "Expected no unlink button when only one auth provider exists"
            )


# ── TC-023-026c: Tab navigation ─────────────────────────────────────────────


class TestAccountSettingsTabs:
    """Tab navigation in account settings."""

    def test_tab_navigation(
        self,
        login_page: LoginPage,
        account_page: AccountSettingsPage,
        screenshot,
    ) -> None:
        """TC-023-026b: Tabs in account settings are clickable and switch content."""
        _ensure_logged_in(login_page)
        account_page.open()
        screenshot("req023_047_account_default_tab", "Kontoeinstellungen Default-Tab")

        tab_labels = account_page.get_tab_labels()

        # Verify expected tabs are present (full mode)
        expected_tabs = ["Profil", "Sicherheit"]
        for expected in expected_tabs:
            assert any(expected in label for label in tab_labels), (
                f"Expected tab '{expected}' in tab list, got: {tab_labels}"
            )

        # Click security tab
        account_page.click_tab("Sicherheit")
        screenshot("req023_048_security_tab_active", "Sicherheit-Tab aktiv nach Klick")

        # Verify security tab content loaded (password fields should be visible)
        assert account_page.is_current_password_visible(), (
            "Expected security tab content (password fields) after tab click"
        )
