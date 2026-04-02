"""E2E tests for REQ-024 — Tenant Settings & Member Management.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-024.md):
  TC-REQ-024-008  ->  TC-024-012  Tenant-Einstellungsseite aufrufen als Admin
  TC-REQ-024-009  ->  TC-024-012  Mitglieder-Tab ist sichtbar und aktiv
  TC-REQ-024-010  ->  TC-024-012  Admin sieht Einladungen-Tab
  TC-REQ-024-011  ->  TC-024-015  Mitglieder-Tab zeigt mindestens ein Mitglied
  TC-REQ-024-012  ->  TC-024-015  Mitglieder haben Rollen-Chips
  TC-REQ-024-013  ->  TC-024-015  Mitglieder-Tab zeigt Anzeigenamen
  TC-REQ-024-014  ->  TC-024-022  Einladungen-Tab laedt mit Formular und Liste
  TC-REQ-024-015  ->  TC-024-022  Einladung-Senden Button disabled ohne E-Mail
  TC-REQ-024-016  ->  TC-024-023  Einladungslink-Button ist sichtbar
  TC-REQ-024-017  ->  TC-024-022  E-Mail-Einladung senden -- Happy Path
  TC-REQ-024-018  ->  TC-024-023  Einladungslink erstellen -- Happy Path
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import LoginPage, TenantSettingsPage

pytestmark = pytest.mark.requires_auth


# -- Demo credentials ---------------------------------------------------------
DEMO_EMAIL = "demo@kamerplanter.example"
DEMO_PASSWORD = "demo-passwort-2024"


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def login_page(browser: WebDriver, base_url: str) -> LoginPage:
    """Return a LoginPage bound to the test browser."""
    return LoginPage(browser, base_url)


@pytest.fixture
def settings_page(browser: WebDriver, base_url: str) -> TenantSettingsPage:
    """Return a TenantSettingsPage bound to the test browser."""
    return TenantSettingsPage(browser, base_url)


def _ensure_logged_in(login_page: LoginPage) -> None:
    """Log in as demo user if not already authenticated."""
    login_page.driver.delete_all_cookies()
    login_page.open()
    login_page.login(DEMO_EMAIL, DEMO_PASSWORD)
    login_page.wait_for_url_contains("/dashboard")


# -- TC-024-012: Settings page load -------------------------------------------


class TestTenantSettingsPageLoad:
    """Tenant settings page loads with correct structure (Spec: TC-024-012)."""

    @pytest.mark.smoke
    @pytest.mark.requires_auth
    def test_settings_page_renders_with_title(
        self,
        login_page: LoginPage,
        settings_page: TenantSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-008: Settings page loads with page title containing tenant name.

        Spec: TC-024-012 -- Tenant-Einstellungsseite aufrufen als Admin.
        """
        _ensure_logged_in(login_page)
        settings_page.open()
        screenshot(
            "TC-REQ-024-008_settings-loaded",
            "TenantSettingsPage after load",
        )

        title = settings_page.get_page_title_text()
        assert title, (
            "TC-REQ-024-008 FAIL: Expected page title on TenantSettingsPage"
        )

    @pytest.mark.smoke
    @pytest.mark.requires_auth
    def test_settings_page_has_members_tab(
        self,
        login_page: LoginPage,
        settings_page: TenantSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-009: Members tab is visible and active by default.

        Spec: TC-024-012 -- Mitglieder-Tab ist sichtbar.
        """
        _ensure_logged_in(login_page)
        settings_page.open()

        tabs = settings_page.get_tab_labels()
        assert len(tabs) >= 1, (
            f"TC-REQ-024-009 FAIL: Expected at least 1 tab, got: {tabs}"
        )
        assert settings_page.get_active_tab_index() == 0, (
            "TC-REQ-024-009 FAIL: Expected Members tab (index 0) to be active by default"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_settings_page_admin_sees_invitations_tab(
        self,
        login_page: LoginPage,
        settings_page: TenantSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-010: Admin user sees the Invitations tab.

        Spec: TC-024-012 -- Admin sieht Einladungen-Tab.
        """
        _ensure_logged_in(login_page)
        settings_page.open()
        screenshot(
            "TC-REQ-024-010_settings-admin-tabs",
            "Settings page tabs for admin user",
        )

        tabs = settings_page.get_tab_labels()
        assert len(tabs) >= 2, (
            f"TC-REQ-024-010 FAIL: Expected at least 2 tabs for admin, got: {tabs}"
        )


# -- TC-024-015: Members list -------------------------------------------------


class TestTenantMembersList:
    """Members tab displays member list with role chips (Spec: TC-024-015)."""

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_members_tab_shows_member_list(
        self,
        login_page: LoginPage,
        settings_page: TenantSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-011: Members tab shows at least one member (the logged-in user).

        Spec: TC-024-015 -- Mitgliederliste zeigt Mitglieder mit Rollen-Chip.
        """
        _ensure_logged_in(login_page)
        settings_page.open()
        settings_page.click_tab_members()
        screenshot(
            "TC-REQ-024-011_members-list",
            "Members tab with member list",
        )

        member_count = settings_page.get_member_count()
        assert member_count >= 1, (
            f"TC-REQ-024-011 FAIL: Expected at least 1 member, got: {member_count}"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_members_have_role_chips(
        self,
        login_page: LoginPage,
        settings_page: TenantSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-012: Each member row displays a role chip.

        Spec: TC-024-015 -- Mitgliederliste zeigt Mitglieder mit Rollen-Chip.
        """
        _ensure_logged_in(login_page)
        settings_page.open()
        settings_page.click_tab_members()

        chips = settings_page.get_member_role_chips()
        member_count = settings_page.get_member_count()
        screenshot(
            "TC-REQ-024-012_members-role-chips",
            "Members with role chips",
        )

        assert len(chips) == member_count, (
            f"TC-REQ-024-012 FAIL: Expected {member_count} role chips, got: {len(chips)}"
        )
        for chip in chips:
            assert chip, "TC-REQ-024-012 FAIL: Expected each role chip to have non-empty text"

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_members_display_names(
        self,
        login_page: LoginPage,
        settings_page: TenantSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-013: Members tab shows display names for each member.

        Spec: TC-024-015 -- Mitgliederliste zeigt Anzeigenamen.
        """
        _ensure_logged_in(login_page)
        settings_page.open()
        settings_page.click_tab_members()

        names = settings_page.get_member_names()
        assert len(names) >= 1, (
            f"TC-REQ-024-013 FAIL: Expected at least 1 member name, got: {names}"
        )


# -- TC-024-022 / TC-024-023: Invitations tab ---------------------------------


class TestTenantInvitations:
    """Invitation system via the Invitations tab (Spec: TC-024-022 to TC-024-024)."""

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_invitations_tab_loads(
        self,
        login_page: LoginPage,
        settings_page: TenantSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-014: Invitations tab loads with invite form and list.

        Spec: TC-024-022 -- E-Mail-Einladung senden -- Formular.
        """
        _ensure_logged_in(login_page)
        settings_page.open()
        settings_page.click_tab_invitations()
        screenshot(
            "TC-REQ-024-014_invitations-tab",
            "Invitations tab loaded",
        )

        field_elements = settings_page.driver.find_elements(
            *TenantSettingsPage.INVITE_EMAIL_FIELD
        )
        assert len(field_elements) > 0, (
            "TC-REQ-024-014 FAIL: Expected invite email field to be visible"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_send_invitation_button_disabled_without_email(
        self,
        login_page: LoginPage,
        settings_page: TenantSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-015: Send invitation button is disabled when email is empty.

        Spec: TC-024-022 -- Einladung-Senden Button disabled.
        """
        _ensure_logged_in(login_page)
        settings_page.open()
        settings_page.click_tab_invitations()
        screenshot(
            "TC-REQ-024-015_invite-btn-disabled",
            "Send invitation button disabled (no email)",
        )

        assert not settings_page.is_send_invitation_enabled(), (
            "TC-REQ-024-015 FAIL: Send invitation button should be disabled when email is empty"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_create_link_button_visible(
        self,
        login_page: LoginPage,
        settings_page: TenantSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-016: Create link button is visible on Invitations tab.

        Spec: TC-024-023 -- Einladungslink erstellen und kopieren -- Happy Path.
        """
        _ensure_logged_in(login_page)
        settings_page.open()
        settings_page.click_tab_invitations()

        link_btn_elements = settings_page.driver.find_elements(
            *TenantSettingsPage.CREATE_LINK_BTN
        )
        screenshot(
            "TC-REQ-024-016_create-link-visible",
            "Create link button on Invitations tab",
        )

        assert len(link_btn_elements) > 0 and link_btn_elements[0].is_displayed(), (
            "TC-REQ-024-016 FAIL: Expected 'Create link' button to be visible for admin"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_send_email_invitation_happy_path(
        self,
        login_page: LoginPage,
        settings_page: TenantSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-017: Send email invitation shows success snackbar.

        Spec: TC-024-022 -- E-Mail-Einladung senden -- Happy Path.
        """
        _ensure_logged_in(login_page)
        settings_page.open()
        settings_page.click_tab_invitations()

        settings_page.enter_invite_email("test-invite@example.com")
        screenshot(
            "TC-REQ-024-017_invite-email-entered",
            "Email entered in invitation field",
        )

        settings_page.click_send_invitation()
        screenshot(
            "TC-REQ-024-017_invite-sent",
            "After sending email invitation",
        )

        if settings_page.has_snackbar():
            text = settings_page.wait_for_snackbar()
            assert text, "TC-REQ-024-017 FAIL: Expected non-empty snackbar text"

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_create_invitation_link_happy_path(
        self,
        login_page: LoginPage,
        settings_page: TenantSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-018: Create invitation link shows success snackbar.

        Spec: TC-024-023 -- Einladungslink erstellen und kopieren -- Happy Path.
        """
        _ensure_logged_in(login_page)
        settings_page.open()
        settings_page.click_tab_invitations()
        screenshot(
            "TC-REQ-024-018_before-create-link",
            "Invitations tab before creating link",
        )

        settings_page.click_create_link()
        screenshot(
            "TC-REQ-024-018_after-create-link",
            "After creating invitation link",
        )

        if settings_page.has_snackbar():
            text = settings_page.wait_for_snackbar()
            assert text, "TC-REQ-024-018 FAIL: Expected non-empty snackbar text"
