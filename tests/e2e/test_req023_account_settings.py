"""E2E tests for REQ-023 — Account Settings.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-023.md):
  TC-REQ-023-024  ->  TC-023-026  Profil anzeigen (Happy Path)
  TC-REQ-023-025  ->  TC-023-027  Anzeigename aendern und speichern
  TC-REQ-023-026  ->  TC-023-029  Passwort aendern (lokales Passwort vorhanden)
  TC-REQ-023-027  ->  TC-023-029  Passwort-aendern Button disabled wenn leer
  TC-REQ-023-028  ->  TC-023-032  Verknuepfte Auth-Provider anzeigen
  TC-REQ-023-029  ->  TC-023-033  Letzten Auth-Provider entfernen -- verhindert
  TC-REQ-023-030  ->  TC-023-026  Tab-Navigation in Kontoeinstellungen
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import AccountSettingsPage, LoginPage

pytestmark = pytest.mark.requires_auth

# -- Demo credentials ---------------------------------------------------------
DEMO_EMAIL = "demo@kamerplanter.local"
DEMO_PASSWORD = "demo-passwort-2024"


# -- Fixtures -----------------------------------------------------------------


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


# -- TC-023-026: Profile tab display -------------------------------------------


class TestAccountSettingsProfile:
    """Account settings profile tab (Spec: TC-023-026 to TC-023-028)."""

    @pytest.mark.smoke
    @pytest.mark.requires_auth
    def test_profile_tab_displays_user_info(
        self,
        login_page: LoginPage,
        account_page: AccountSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-024: Profile tab shows display name, email, and tabs.

        Spec: TC-023-026 -- Profil anzeigen (Happy Path).
        """
        _ensure_logged_in(login_page)
        account_page.open(tab="profile")
        screenshot(
            "TC-REQ-023-024_account-profile-loaded",
            "Account settings profile tab after load",
        )

        tab_labels = account_page.get_tab_labels()
        assert len(tab_labels) > 0, (
            "TC-REQ-023-024 FAIL: Expected at least one tab in account settings"
        )
        assert any("Profil" in label for label in tab_labels), (
            f"TC-REQ-023-024 FAIL: Expected 'Profil' tab, got: {tab_labels}"
        )

        display_name = account_page.get_display_name()
        assert display_name, (
            "TC-REQ-023-024 FAIL: Expected display name to be prefilled"
        )

        email = account_page.get_email()
        assert email == DEMO_EMAIL, (
            f"TC-REQ-023-024 FAIL: Expected email '{DEMO_EMAIL}', got: '{email}'"
        )
        assert account_page.is_email_disabled(), (
            "TC-REQ-023-024 FAIL: Expected email field to be disabled (read-only)"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_update_display_name(
        self,
        login_page: LoginPage,
        account_page: AccountSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-025: Update display name and save.

        Spec: TC-023-027 -- Anzeigename aendern und speichern.
        """
        _ensure_logged_in(login_page)
        account_page.open(tab="profile")

        original_name = account_page.get_display_name()
        screenshot(
            "TC-REQ-023-025_before-edit",
            "Profile before name change",
        )

        new_name = "Aktualisierter Gaertner"
        account_page.set_display_name(new_name)
        account_page.click_profile_save()

        screenshot(
            "TC-REQ-023-025_after-save",
            "Profile after saving",
        )

        current_name = account_page.get_display_name()
        assert current_name == new_name, (
            f"TC-REQ-023-025 FAIL: Expected display name '{new_name}', got: '{current_name}'"
        )

        # Restore original name
        account_page.set_display_name(original_name)
        account_page.click_profile_save()


# -- TC-023-029 to TC-023-030: Security tab ------------------------------------


class TestAccountSettingsSecurity:
    """Account settings security tab (Spec: TC-023-029 to TC-023-033)."""

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_security_tab_displays_password_fields(
        self,
        login_page: LoginPage,
        account_page: AccountSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-026: Security tab shows password change fields for local account.

        Spec: TC-023-029 -- Passwort aendern (lokales Passwort vorhanden).
        """
        _ensure_logged_in(login_page)
        account_page.open(tab="security")
        screenshot(
            "TC-REQ-023-026_security-tab-loaded",
            "Security tab after load",
        )

        assert account_page.is_current_password_visible(), (
            "TC-REQ-023-026 FAIL: Expected current-password field for local account"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_change_password_button_disabled_when_empty(
        self,
        login_page: LoginPage,
        account_page: AccountSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-027: Change-password button is disabled when fields are empty.

        Spec: TC-023-029 -- Passwort aendern Button disabled.
        """
        _ensure_logged_in(login_page)
        account_page.open(tab="security")
        screenshot(
            "TC-REQ-023-027_security-button-disabled",
            "Change password button disabled",
        )

        assert not account_page.is_change_password_button_enabled(), (
            "TC-REQ-023-027 FAIL: Expected change-password button to be disabled when fields are empty"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_linked_providers_displayed(
        self,
        login_page: LoginPage,
        account_page: AccountSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-028: Linked auth providers are displayed in the security tab.

        Spec: TC-023-032 -- Verknuepfte Auth-Provider anzeigen.
        """
        _ensure_logged_in(login_page)
        account_page.open(tab="security")
        screenshot(
            "TC-REQ-023-028_linked-providers",
            "Linked auth providers in security tab",
        )

        providers = account_page.get_linked_providers()
        assert len(providers) > 0, (
            "TC-REQ-023-028 FAIL: Expected at least one linked auth provider (local)"
        )
        assert any("local" in p.lower() or "lokal" in p.lower() for p in providers), (
            f"TC-REQ-023-028 FAIL: Expected 'local' provider for demo user, got: {providers}"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_single_provider_unlink_button_absent(
        self,
        login_page: LoginPage,
        account_page: AccountSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-029: Unlink button is not shown when only one provider exists.

        Spec: TC-023-033 -- Letzten Auth-Provider entfernen -- verhindert.
        """
        _ensure_logged_in(login_page)
        account_page.open(tab="security")
        screenshot(
            "TC-REQ-023-029_single-provider-no-unlink",
            "No unlink button for single provider",
        )

        providers = account_page.get_linked_providers()
        unlink_buttons = account_page.get_unlink_buttons()

        if len(providers) <= 1:
            assert len(unlink_buttons) == 0, (
                "TC-REQ-023-029 FAIL: Expected no unlink button when only one provider exists"
            )


# -- TC-023-026c: Tab navigation -----------------------------------------------


class TestAccountSettingsTabs:
    """Tab navigation in account settings (Spec: TC-023-026)."""

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_tab_navigation(
        self,
        login_page: LoginPage,
        account_page: AccountSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-030: Tabs in account settings are clickable and switch content.

        Spec: TC-023-026 -- Profil anzeigen -- Tab-Navigation.
        """
        _ensure_logged_in(login_page)
        account_page.open()
        screenshot(
            "TC-REQ-023-030_account-default-tab",
            "Account settings default tab",
        )

        tab_labels = account_page.get_tab_labels()

        expected_tabs = ["Profil", "Sicherheit"]
        for expected in expected_tabs:
            assert any(expected in label for label in tab_labels), (
                f"TC-REQ-023-030 FAIL: Expected tab '{expected}' in tab list, got: {tab_labels}"
            )

        account_page.click_tab("Sicherheit")
        screenshot(
            "TC-REQ-023-030_security-tab-active",
            "Security tab active after click",
        )

        assert account_page.is_current_password_visible(), (
            "TC-REQ-023-030 FAIL: Expected security tab content after tab click"
        )
