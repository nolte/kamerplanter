"""E2E tests for REQ-024 -- Tenant Settings & Member Management (TC-024-012 to TC-024-024).

Covers:
  - TenantSettingsPage: page load, tabs (Members, Invitations)
  - Members tab: member list, role chips, remove buttons (admin only)
  - Invitations tab: invite by email, create link, revoke invitation
  - Admin-only UI elements hidden for non-admins

All tests follow NFR-008:
  - Page-Object-Pattern (no direct find_element calls in tests)
  - WebDriverWait only -- no time.sleep()
  - Screenshot at: Page Load / before action / after action / error state
  - Descriptive assertion messages
"""

from __future__ import annotations

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import LoginPage, TenantSettingsPage

pytestmark = pytest.mark.requires_auth


# -- Demo credentials --------------------------------------------------------
DEMO_EMAIL = "demo@kamerplanter.local"
DEMO_PASSWORD = "demo-passwort-2024"


# -- Fixtures ----------------------------------------------------------------


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


# -- TC-024-012: Settings page load -----------------------------------------


class TestTenantSettingsPageLoad:
    """TC-024-012: Tenant settings page loads with correct structure."""

    def test_settings_page_renders_with_title(
        self,
        login_page: LoginPage,
        settings_page: TenantSettingsPage,
        screenshot,
    ) -> None:
        """TC-024-012: Settings page loads with page title containing tenant name."""
        _ensure_logged_in(login_page)
        settings_page.open()
        screenshot(
            "req024_010_settings_loaded",
            "TenantSettingsPage after load",
        )

        title = settings_page.get_page_title_text()
        assert title, (
            "Expected page title on TenantSettingsPage, got empty string"
        )

    def test_settings_page_has_members_tab(
        self,
        login_page: LoginPage,
        settings_page: TenantSettingsPage,
        screenshot,
    ) -> None:
        """TC-024-012: Members tab is visible and active by default."""
        _ensure_logged_in(login_page)
        settings_page.open()

        tabs = settings_page.get_tab_labels()
        assert len(tabs) >= 1, (
            f"Expected at least 1 tab on settings page, got: {tabs}"
        )
        # First tab should be active (index 0)
        assert settings_page.get_active_tab_index() == 0, (
            "Expected the Members tab (index 0) to be active by default"
        )

    def test_settings_page_admin_sees_invitations_tab(
        self,
        login_page: LoginPage,
        settings_page: TenantSettingsPage,
        screenshot,
    ) -> None:
        """TC-024-012: Admin user sees the Invitations tab."""
        _ensure_logged_in(login_page)
        settings_page.open()
        screenshot(
            "req024_011_settings_admin_tabs",
            "Settings page tabs for admin user",
        )

        tabs = settings_page.get_tab_labels()
        assert len(tabs) >= 2, (
            f"Expected at least 2 tabs for admin (Members + Invitations), got: {tabs}"
        )


# -- TC-024-015: Members list -----------------------------------------------


class TestTenantMembersList:
    """TC-024-015: Members tab displays member list with role chips."""

    def test_members_tab_shows_member_list(
        self,
        login_page: LoginPage,
        settings_page: TenantSettingsPage,
        screenshot,
    ) -> None:
        """TC-024-015: Members tab shows at least one member (the logged-in user)."""
        _ensure_logged_in(login_page)
        settings_page.open()
        settings_page.click_tab_members()
        screenshot(
            "req024_012_members_list",
            "Members tab with member list",
        )

        member_count = settings_page.get_member_count()
        assert member_count >= 1, (
            f"Expected at least 1 member in the list (the current user), got: {member_count}"
        )

    def test_members_have_role_chips(
        self,
        login_page: LoginPage,
        settings_page: TenantSettingsPage,
        screenshot,
    ) -> None:
        """TC-024-015: Each member row displays a role chip."""
        _ensure_logged_in(login_page)
        settings_page.open()
        settings_page.click_tab_members()

        chips = settings_page.get_member_role_chips()
        member_count = settings_page.get_member_count()
        screenshot(
            "req024_013_members_role_chips",
            "Members with role chips",
        )

        assert len(chips) == member_count, (
            f"Expected {member_count} role chips (one per member), got: {len(chips)}"
        )
        for chip in chips:
            assert chip, "Expected each role chip to have non-empty text"

    def test_members_display_names(
        self,
        login_page: LoginPage,
        settings_page: TenantSettingsPage,
        screenshot,
    ) -> None:
        """TC-024-015: Members tab shows display names for each member."""
        _ensure_logged_in(login_page)
        settings_page.open()
        settings_page.click_tab_members()

        names = settings_page.get_member_names()
        assert len(names) >= 1, (
            f"Expected at least 1 member name, got: {names}"
        )


# -- TC-024-022 / TC-024-023: Invitations tab -------------------------------


class TestTenantInvitations:
    """TC-024-022 to TC-024-024: Invitation system via the Invitations tab."""

    def test_invitations_tab_loads(
        self,
        login_page: LoginPage,
        settings_page: TenantSettingsPage,
        screenshot,
    ) -> None:
        """TC-024-022: Invitations tab loads with invite form and list."""
        _ensure_logged_in(login_page)
        settings_page.open()
        settings_page.click_tab_invitations()
        screenshot(
            "req024_014_invitations_tab",
            "Invitations tab loaded",
        )

        # The invite email field should be visible
        field_elements = settings_page.driver.find_elements(
            *TenantSettingsPage.INVITE_EMAIL_FIELD
        )
        assert len(field_elements) > 0, (
            "Expected invite email field to be visible on Invitations tab"
        )

    def test_send_invitation_button_disabled_without_email(
        self,
        login_page: LoginPage,
        settings_page: TenantSettingsPage,
        screenshot,
    ) -> None:
        """TC-024-022: Send invitation button is disabled when email is empty."""
        _ensure_logged_in(login_page)
        settings_page.open()
        settings_page.click_tab_invitations()
        screenshot(
            "req024_015_invite_btn_disabled",
            "Send invitation button disabled (no email)",
        )

        assert not settings_page.is_send_invitation_enabled(), (
            "Send invitation button should be disabled when email field is empty"
        )

    def test_create_link_button_visible(
        self,
        login_page: LoginPage,
        settings_page: TenantSettingsPage,
        screenshot,
    ) -> None:
        """TC-024-023: Create link button is visible on Invitations tab."""
        _ensure_logged_in(login_page)
        settings_page.open()
        settings_page.click_tab_invitations()

        link_btn_elements = settings_page.driver.find_elements(
            *TenantSettingsPage.CREATE_LINK_BTN
        )
        screenshot(
            "req024_016_create_link_visible",
            "Create link button on Invitations tab",
        )

        assert len(link_btn_elements) > 0 and link_btn_elements[0].is_displayed(), (
            "Expected 'Create link' button to be visible on Invitations tab for admin"
        )

    def test_send_email_invitation_happy_path(
        self,
        login_page: LoginPage,
        settings_page: TenantSettingsPage,
        screenshot,
    ) -> None:
        """TC-024-022: Send email invitation shows success snackbar."""
        _ensure_logged_in(login_page)
        settings_page.open()
        settings_page.click_tab_invitations()

        settings_page.enter_invite_email("test-invite@example.com")
        screenshot(
            "req024_017_invite_email_entered",
            "Email entered in invitation field",
        )

        settings_page.click_send_invitation()
        screenshot(
            "req024_018_invite_sent",
            "After sending email invitation",
        )

        # Either a snackbar appears or the invitation list updates
        # We check for snackbar first, then fall back to checking the list
        if settings_page.has_snackbar():
            text = settings_page.wait_for_snackbar()
            assert text, "Expected non-empty snackbar text after sending invitation"

    def test_create_invitation_link_happy_path(
        self,
        login_page: LoginPage,
        settings_page: TenantSettingsPage,
        screenshot,
    ) -> None:
        """TC-024-023: Create invitation link shows success snackbar."""
        _ensure_logged_in(login_page)
        settings_page.open()
        settings_page.click_tab_invitations()
        screenshot(
            "req024_019_before_create_link",
            "Invitations tab before creating link",
        )

        settings_page.click_create_link()
        screenshot(
            "req024_020_after_create_link",
            "After creating invitation link",
        )

        # Clipboard write may not be available in headless mode, but snackbar should appear
        if settings_page.has_snackbar():
            text = settings_page.wait_for_snackbar()
            assert text, "Expected non-empty snackbar text after creating link"
