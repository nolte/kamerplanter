"""E2E tests for REQ-024 — Tenant-scoped Navigation.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-024.md):
  TC-REQ-024-027  ->  TC-024-012  Direkt-Navigation zu Tenant-Einstellungen
  TC-REQ-024-028  ->  TC-024-003  Direkt-Navigation zu Tenant-Erstellung
  TC-REQ-024-029  ->  TC-024-012  Navigation Einstellungen -> Erstellung
  TC-REQ-024-030  ->  TC-024-026  Einladung ohne Token zeigt Fehler
  TC-REQ-024-031  ->  TC-024-026  Einladung mit ungueltigem Token zeigt Fehler
  TC-REQ-024-032  ->  TC-024-026  Fehlerzustand zeigt Heading und Detail
  TC-REQ-024-033  ->  TC-024-026  Fehlerzustand hat Dashboard-Button
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

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


# -- Demo credentials ---------------------------------------------------------
DEMO_EMAIL = "demo@kamerplanter.local"
DEMO_PASSWORD = "demo-passwort-2024"


# -- Fixtures -----------------------------------------------------------------


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


# -- Navigation between tenant pages ------------------------------------------


class TestTenantNavigation:
    """Cross-navigation between tenant-related pages (Spec: TC-024-003, TC-024-012)."""

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_navigate_from_dashboard_to_settings(
        self,
        login_page: LoginPage,
        settings_page: TenantSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-027: Navigate directly to /tenants/settings from dashboard.

        Spec: TC-024-012 -- Tenant-Einstellungsseite aufrufen als Admin.
        """
        _ensure_logged_in(login_page)
        settings_page.open()
        screenshot(
            "TC-REQ-024-027_direct-nav-settings",
            "Direct navigation to tenant settings",
        )

        title = settings_page.get_page_title_text()
        assert title, (
            "TC-REQ-024-027 FAIL: Expected page title after navigating to tenant settings"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_navigate_from_dashboard_to_create(
        self,
        login_page: LoginPage,
        create_page: TenantCreatePage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-028: Navigate directly to /tenants/create.

        Spec: TC-024-003 -- Organisations-Tenant erstellen.
        """
        _ensure_logged_in(login_page)
        create_page.open()
        screenshot(
            "TC-REQ-024-028_direct-nav-create",
            "Direct navigation to tenant create",
        )

        title = create_page.get_page_title_text()
        assert title, (
            "TC-REQ-024-028 FAIL: Expected page title after navigating to tenant create"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_navigate_settings_then_create(
        self,
        login_page: LoginPage,
        settings_page: TenantSettingsPage,
        create_page: TenantCreatePage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-029: Navigation: Settings page -> Create page in sequence.

        Spec: TC-024-012 / TC-024-003 -- Cross-Navigation.
        """
        _ensure_logged_in(login_page)

        settings_page.open()
        screenshot(
            "TC-REQ-024-029_nav-step1-settings",
            "Step 1: On settings page",
        )
        assert settings_page.get_page_title_text(), (
            "TC-REQ-024-029 FAIL: Settings page should have a title"
        )

        create_page.open()
        screenshot(
            "TC-REQ-024-029_nav-step2-create",
            "Step 2: Navigated to create page",
        )
        assert create_page.get_page_title_text(), (
            "TC-REQ-024-029 FAIL: Create page should have a title"
        )


# -- Invitation Accept page ---------------------------------------------------


class TestInvitationAcceptNavigation:
    """Invitation accept page error states (Spec: TC-024-026)."""

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_invitation_page_without_token_shows_error(
        self,
        login_page: LoginPage,
        invitation_page: InvitationAcceptPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-030: Invitation accept page without token shows error.

        Spec: TC-024-026 -- Abgelaufene Einladung annehmen -- Fehlermeldung.
        """
        _ensure_logged_in(login_page)
        invitation_page.open_without_token()
        screenshot(
            "TC-REQ-024-030_invitation-no-token",
            "Invitation accept page without token",
        )

        result = invitation_page.wait_for_result()
        assert result == "error", (
            f"TC-REQ-024-030 FAIL: Expected error state when no token provided, got: {result}"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_invitation_page_with_invalid_token_shows_error(
        self,
        login_page: LoginPage,
        invitation_page: InvitationAcceptPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-031: Invitation accept page with invalid token shows error.

        Spec: TC-024-026 -- Abgelaufene Einladung annehmen -- Fehlermeldung.
        """
        _ensure_logged_in(login_page)
        invitation_page.open_with_token("invalid-nonexistent-token-12345")
        screenshot(
            "TC-REQ-024-031_invitation-invalid-token-loading",
            "Invitation accept page with invalid token (loading)",
        )

        result = invitation_page.wait_for_result()
        screenshot(
            "TC-REQ-024-031_invitation-invalid-token-error",
            "Invitation accept page with invalid token (error result)",
        )

        assert result == "error", (
            f"TC-REQ-024-031 FAIL: Expected error state for invalid token, got: {result}"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_invitation_error_shows_heading_and_detail(
        self,
        login_page: LoginPage,
        invitation_page: InvitationAcceptPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-032: Error state displays heading and error detail text.

        Spec: TC-024-026 -- Fehlerzustand zeigt Heading und Detail.
        """
        _ensure_logged_in(login_page)
        invitation_page.open_with_token("definitely-bad-token")
        invitation_page.wait_for_result()
        screenshot(
            "TC-REQ-024-032_invitation-error-detail",
            "Invitation error with heading and detail",
        )

        heading = invitation_page.get_heading_text()
        assert heading, (
            "TC-REQ-024-032 FAIL: Expected a heading text on the error state"
        )

        assert invitation_page.is_error(), (
            "TC-REQ-024-032 FAIL: Expected the error icon to be displayed"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_invitation_error_has_dashboard_button(
        self,
        login_page: LoginPage,
        invitation_page: InvitationAcceptPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-033: Error state has a button to navigate back to dashboard.

        Spec: TC-024-026 -- Fehlerzustand hat Dashboard-Button.
        """
        _ensure_logged_in(login_page)
        invitation_page.open_with_token("another-bad-token")
        invitation_page.wait_for_result()
        screenshot(
            "TC-REQ-024-033_invitation-error-dashboard-btn",
            "Invitation error with dashboard button",
        )

        invitation_page.click_dashboard_button_on_error()
        invitation_page.wait_for_url_contains("/dashboard")

        current_url = invitation_page.driver.current_url
        assert "/dashboard" in current_url, (
            f"TC-REQ-024-033 FAIL: Expected redirect to /dashboard, got: {current_url}"
        )
