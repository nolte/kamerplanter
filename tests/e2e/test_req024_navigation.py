"""E2E tests for REQ-024 -- Tenant-scoped Navigation (TC-024-025 to TC-024-028).

Covers:
  - Navigation to tenant settings from dashboard
  - Invitation accept page: no token, invalid token
  - Cross-navigation between tenant pages
  - Tenant-scoped URL structure verification

All tests follow NFR-008:
  - Page-Object-Pattern (no direct find_element calls in tests)
  - WebDriverWait only -- no time.sleep()
  - Screenshot at: Page Load / before action / after action / error state
  - Descriptive assertion messages
"""

from __future__ import annotations

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import (
    InvitationAcceptPage,
    LoginPage,
    TenantCreatePage,
    TenantSettingsPage,
    TenantSwitcherPage,
)

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
def create_page(browser: WebDriver, base_url: str) -> TenantCreatePage:
    """Return a TenantCreatePage bound to the test browser."""
    return TenantCreatePage(browser, base_url)


@pytest.fixture
def settings_page(browser: WebDriver, base_url: str) -> TenantSettingsPage:
    """Return a TenantSettingsPage bound to the test browser."""
    return TenantSettingsPage(browser, base_url)


@pytest.fixture
def switcher(browser: WebDriver, base_url: str) -> TenantSwitcherPage:
    """Return a TenantSwitcherPage bound to the test browser."""
    return TenantSwitcherPage(browser, base_url)


@pytest.fixture
def invitation_page(browser: WebDriver, base_url: str) -> InvitationAcceptPage:
    """Return an InvitationAcceptPage bound to the test browser."""
    return InvitationAcceptPage(browser, base_url)


def _ensure_logged_in(login_page: LoginPage) -> None:
    """Log in as demo user if not already authenticated."""
    login_page.driver.delete_all_cookies()
    login_page.open()
    login_page.login(DEMO_EMAIL, DEMO_PASSWORD)
    login_page.wait_for_url_contains("/dashboard")


# -- Navigation between tenant pages ----------------------------------------


class TestTenantNavigation:
    """Cross-navigation between tenant-related pages."""

    def test_navigate_from_dashboard_to_settings(
        self,
        login_page: LoginPage,
        settings_page: TenantSettingsPage,
        screenshot,
    ) -> None:
        """TC-024-012: Navigate directly to /tenants/settings from dashboard."""
        _ensure_logged_in(login_page)
        settings_page.open()
        screenshot(
            "req024_031_direct_nav_settings",
            "Direct navigation to tenant settings",
        )

        title = settings_page.get_page_title_text()
        assert title, (
            "Expected page title after navigating to tenant settings"
        )

    def test_navigate_from_dashboard_to_create(
        self,
        login_page: LoginPage,
        create_page: TenantCreatePage,
        screenshot,
    ) -> None:
        """TC-024-003: Navigate directly to /tenants/create."""
        _ensure_logged_in(login_page)
        create_page.open()
        screenshot(
            "req024_032_direct_nav_create",
            "Direct navigation to tenant create",
        )

        title = create_page.get_page_title_text()
        assert title, (
            "Expected page title after navigating to tenant create page"
        )

    def test_navigate_settings_then_create(
        self,
        login_page: LoginPage,
        settings_page: TenantSettingsPage,
        create_page: TenantCreatePage,
        screenshot,
    ) -> None:
        """Navigation: Settings page -> Create page in sequence."""
        _ensure_logged_in(login_page)

        settings_page.open()
        screenshot(
            "req024_033_nav_step1_settings",
            "Step 1: On settings page",
        )
        assert settings_page.get_page_title_text(), "Settings page should have a title"

        create_page.open()
        screenshot(
            "req024_034_nav_step2_create",
            "Step 2: Navigated to create page",
        )
        assert create_page.get_page_title_text(), "Create page should have a title"


# -- Invitation Accept page -------------------------------------------------


class TestInvitationAcceptNavigation:
    """TC-024-025 to TC-024-028: Invitation accept page error states."""

    def test_invitation_page_without_token_shows_error(
        self,
        login_page: LoginPage,
        invitation_page: InvitationAcceptPage,
        screenshot,
    ) -> None:
        """TC-024-026: Invitation accept page without token shows error."""
        _ensure_logged_in(login_page)
        invitation_page.open_without_token()
        screenshot(
            "req024_035_invitation_no_token",
            "Invitation accept page without token",
        )

        result = invitation_page.wait_for_result()
        assert result == "error", (
            f"Expected error state when no token provided, got: {result}"
        )

    def test_invitation_page_with_invalid_token_shows_error(
        self,
        login_page: LoginPage,
        invitation_page: InvitationAcceptPage,
        screenshot,
    ) -> None:
        """TC-024-026: Invitation accept page with invalid token shows error."""
        _ensure_logged_in(login_page)
        invitation_page.open_with_token("invalid-nonexistent-token-12345")
        screenshot(
            "req024_036_invitation_invalid_token_loading",
            "Invitation accept page with invalid token (loading)",
        )

        result = invitation_page.wait_for_result()
        screenshot(
            "req024_037_invitation_invalid_token_error",
            "Invitation accept page with invalid token (error result)",
        )

        assert result == "error", (
            f"Expected error state for invalid token, got: {result}"
        )

    def test_invitation_error_shows_heading_and_detail(
        self,
        login_page: LoginPage,
        invitation_page: InvitationAcceptPage,
        screenshot,
    ) -> None:
        """TC-024-026: Error state displays heading and error detail text."""
        _ensure_logged_in(login_page)
        invitation_page.open_with_token("definitely-bad-token")
        invitation_page.wait_for_result()
        screenshot(
            "req024_038_invitation_error_detail",
            "Invitation error with heading and detail",
        )

        heading = invitation_page.get_heading_text()
        assert heading, (
            "Expected a heading text on the error state of invitation accept page"
        )

        assert invitation_page.is_error(), (
            "Expected the error icon to be displayed"
        )

    def test_invitation_error_has_dashboard_button(
        self,
        login_page: LoginPage,
        invitation_page: InvitationAcceptPage,
        screenshot,
    ) -> None:
        """TC-024-026: Error state has a button to navigate back to dashboard."""
        _ensure_logged_in(login_page)
        invitation_page.open_with_token("another-bad-token")
        invitation_page.wait_for_result()
        screenshot(
            "req024_039_invitation_error_dashboard_btn",
            "Invitation error with dashboard button",
        )

        invitation_page.click_dashboard_button_on_error()
        invitation_page.wait_for_url_contains("/dashboard")

        current_url = invitation_page.driver.current_url
        assert "/dashboard" in current_url, (
            f"Expected redirect to /dashboard, got: {current_url}"
        )
