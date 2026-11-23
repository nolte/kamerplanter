"""E2E tests for REQ-023 — Account Settings.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-023.md):
  TC-REQ-023-024  ->  TC-023-026  Profil anzeigen (Happy Path)
  TC-REQ-023-025  ->  TC-023-027  Anzeigename aendern und speichern
  TC-REQ-023-026  ->  TC-023-029  Passwort aendern (lokales Passwort vorhanden)
  TC-REQ-023-027  ->  TC-023-029  Passwort-aendern Button disabled wenn leer
  TC-REQ-023-028  ->  TC-023-032  Verknuepfte Auth-Provider anzeigen
  TC-REQ-023-029  ->  TC-023-033  Letzten Auth-Provider entfernen -- verhindert
  TC-REQ-023-030  ->  TC-023-085  Gruppen-Navigation in den Einstellungen
  TC-REQ-023-031  ->  TC-023-082  Abschnitt per Deep Link oeffnen
  TC-REQ-023-032  ->  TC-023-083  Unbekannte Einstellungsgruppe zeigt 404
  TC-REQ-023-033  ->  TC-023-084  Betreiber-Gruppe fuer Mitglied nicht erreichbar
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from selenium.webdriver.common.by import By

from .pages import AccountSettingsPage, LoginPage
from ._auth_helpers import clear_auth_session

pytestmark = pytest.mark.requires_auth

# -- Demo credentials ---------------------------------------------------------
DEMO_EMAIL = "demo@kamerplanter.example"
DEMO_PASSWORD = "demo-passwort-2024"

NOT_FOUND_PAGE = (By.CSS_SELECTOR, "[data-testid='not-found-page']")
#: The app theme's `md` breakpoint (``src/frontend/src/theme/tokens.ts``: 768 px, not
#: MUI's default 900): below it the settings show the group list and detail views. The
#: tablet profile (820 px) is above it and gets the desktop side navigation.
MD_BREAKPOINT_PX = 768


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
    clear_auth_session(login_page.driver)
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
        """TC-023-026: Profile section shows display name and email in its group.

        Spec: TC-023-026 -- Profil anzeigen (Happy Path).
        """
        _ensure_logged_in(login_page)
        account_page.open(section="profile")
        screenshot(
            "TC-REQ-023-024_account-profile-loaded",
            "Account settings profile tab after load",
        )

        group_title = account_page.get_group_title()
        assert "profil" in group_title.lower(), (
            f"TC-REQ-023-024 FAIL: Expected the group 'Profil & Konto', got: {group_title!r}"
        )

        display_name = account_page.get_display_name()
        assert display_name, "TC-REQ-023-024 FAIL: Expected display name to be prefilled"

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
        """TC-023-027: Update display name and save.

        Spec: TC-023-027 -- Anzeigename aendern und speichern.
        """
        _ensure_logged_in(login_page)
        account_page.open(section="profile")

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
        """TC-023-029: Security tab shows password change fields for local account.

        Spec: TC-023-029 -- Passwort aendern (lokales Passwort vorhanden).
        """
        _ensure_logged_in(login_page)
        account_page.open(section="security")
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
        """TC-023-029: Change-password button is disabled when fields are empty.

        Spec: TC-023-029 -- Passwort aendern Button disabled.
        """
        _ensure_logged_in(login_page)
        account_page.open(section="security")
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
        """TC-023-032: Linked auth providers are displayed in the security tab.

        Spec: TC-023-032 -- Verknuepfte Auth-Provider anzeigen.
        """
        _ensure_logged_in(login_page)
        account_page.open(section="security")
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
        """TC-023-033: Unlink button is not shown when only one provider exists.

        Spec: TC-023-033 -- Letzten Auth-Provider entfernen -- verhindert.
        """
        _ensure_logged_in(login_page)
        account_page.open(section="security")
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


# -- TC-023-082..085: Group navigation -----------------------------------------------


class TestAccountSettingsTabs:
    """Group navigation in the settings (Spec: TC-023-082 to TC-023-085)."""

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_group_navigation(
        self,
        login_page: LoginPage,
        account_page: AccountSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-023-085: The settings groups are listed and open their content (F-11).

        Spec: TC-023-085 -- Gruppen-Navigation in den Einstellungen. On a desktop
        the groups sit in a side navigation, on a phone in a group list whose
        detail view carries a back arrow; both use the same entry ids.
        """
        _ensure_logged_in(login_page)
        account_page.open()
        screenshot(
            "TC-REQ-023-030_settings-groups",
            "Settings page with its group navigation",
        )

        groups = account_page.get_group_keys()
        for expected in ("account", "display", "notifications", "security", "integrations"):
            assert expected in groups, (
                f"TC-REQ-023-030 FAIL: Expected group '{expected}' in the navigation, got: {groups}"
            )
        # The demo member is no operator: the Installation group is not offered.
        assert "installation" not in groups, (
            f"TC-REQ-023-030 FAIL: Expected no Installation group for a member, got: {groups}"
        )

        account_page.click_group("security")
        screenshot(
            "TC-REQ-023-030_security-group-open",
            "Security group open after click",
        )

        assert account_page.is_current_password_visible(), (
            "TC-REQ-023-030 FAIL: Expected the password form in the security group"
        )
        account_page.wait_for_url_contains("/settings/security")

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_section_deep_link(
        self,
        login_page: LoginPage,
        account_page: AccountSettingsPage,
        device_profile: dict,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-023-082: /settings/<group>#<section> opens the group at the section.

        Spec: TC-023-082 -- Abschnitt per Deep Link oeffnen.
        """
        _ensure_logged_in(login_page)
        account_page.open(section="apikeys")
        screenshot("TC-REQ-023-031_apikeys-deep-link", "Security group opened at the API keys")

        section = account_page.wait_for_element_visible(account_page.section("apikeys"))
        assert section.is_displayed(), (
            "TC-REQ-023-031 FAIL: Expected the API keys section to be visible"
        )
        title = account_page.get_group_title()
        assert "sicherheit" in title.lower(), (
            f"TC-REQ-023-031 FAIL: Expected the group 'Sicherheit & Zugang', got: {title!r}"
        )
        if device_profile["width"] < MD_BREAKPOINT_PX:
            # Below the `md` breakpoint (the phone profile) the group is a detail
            # view that leads back to the group list.
            assert account_page.is_back_button_visible(), (
                "TC-REQ-023-031 FAIL: Expected a back arrow in the group's detail view"
            )
            account_page.click_back()
            account_page.wait_for_element_visible(account_page.GROUP_LIST)
            assert "security" in account_page.get_group_keys(), (
                "TC-REQ-023-031 FAIL: Expected the group list after the back arrow"
            )
        else:
            # From `md` up (desktop and tablet profiles) the group sits next to the
            # side navigation; there is no detail view to leave.
            assert not account_page.is_back_button_visible(), (
                "TC-REQ-023-031 FAIL: Expected no back arrow next to the side navigation"
            )

    def test_unknown_group_shows_not_found(
        self,
        login_page: LoginPage,
        account_page: AccountSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-023-083: An unknown settings group shows the 404 page.

        Spec: TC-023-083 -- Unbekannte Einstellungsgruppe zeigt 404.
        """
        _ensure_logged_in(login_page)
        account_page.open_path("/settings/no-such-group", NOT_FOUND_PAGE)
        not_found = account_page.wait_for_element_visible(NOT_FOUND_PAGE)
        screenshot("TC-REQ-023-032_unknown-group", "404 page for an unknown settings group")
        assert not_found.is_displayed(), "TC-REQ-023-032 FAIL: Expected the 404 page"

    def test_operator_group_not_reachable_for_member(
        self,
        login_page: LoginPage,
        account_page: AccountSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-023-084: A member's deep link into Installation lands on the first group.

        Spec: TC-023-084 -- Betreiber-Gruppe fuer Mitglied nicht erreichbar.
        """
        _ensure_logged_in(login_page)
        account_page.open_path(
            "/settings/installation#storage", account_page.group_panel("account")
        )
        account_page.wait_for_url_contains("/settings/account")
        screenshot("TC-REQ-023-033_installation-redirect", "Member lands on the first group")
        assert account_page.is_absent_within(account_page.section("storage")), (
            "TC-REQ-023-033 FAIL: Expected no storage section for an ordinary member"
        )
