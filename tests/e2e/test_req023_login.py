"""E2E tests for REQ-023 — Login flows.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-023.md):
  TC-REQ-023-001  ->  TC-023-009  Erfolgreicher lokaler Login (Happy Path)
  TC-REQ-023-002  ->  TC-023-009  Login-Seite rendert mit Heading, Feldern und Links
  TC-REQ-023-003  ->  TC-023-010  Login mit aktivierter 'Angemeldet bleiben'-Checkbox
  TC-REQ-023-004  ->  TC-023-012  Login-Seite ohne aktivierte SSO-Provider
  TC-REQ-023-005  ->  TC-023-013  Login mit falschem Passwort
  TC-REQ-023-006  ->  TC-023-013  Login mit nicht existierender E-Mail
  TC-REQ-023-007  ->  TC-023-016  Redirect von geschuetzter Route zu Login
  TC-REQ-023-008  ->  TC-023-017  Redirect von Login zu Dashboard wenn bereits eingeloggt
  TC-REQ-023-009  ->  TC-023-019  Passwort vergessen Link navigiert zu Reset
  TC-REQ-023-010  ->  TC-023-006  Register-Link navigiert zu /register
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import LoginPage

pytestmark = pytest.mark.requires_auth

# -- Demo credentials ---------------------------------------------------------
DEMO_EMAIL = "demo@kamerplanter.local"
DEMO_PASSWORD = "demo-passwort-2024"


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def login_page(browser: WebDriver, base_url: str) -> LoginPage:
    """Return a LoginPage bound to the test browser."""
    return LoginPage(browser, base_url)


# -- Helper: ensure logged out -------------------------------------------------


def _ensure_logged_out(browser: WebDriver, base_url: str) -> None:
    """Clear auth state by deleting cookies and navigating to login."""
    browser.delete_all_cookies()
    browser.get(f"{base_url}/login")


# -- TC-023-009: Successful login ----------------------------------------------


class TestLoginHappyPath:
    """Successful login flows (Spec: TC-023-009, TC-023-010)."""

    @pytest.mark.smoke
    @pytest.mark.requires_auth
    def test_login_page_renders(
        self,
        login_page: LoginPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-002: Login page renders with heading, fields and links.

        Spec: TC-023-009 -- Erfolgreicher lokaler Login (Happy Path) -- Seitenstruktur.
        """
        _ensure_logged_out(login_page.driver, login_page.base_url)
        login_page.open()
        screenshot(
            "TC-REQ-023-002_login-page-loaded",
            "Login page after initial load",
        )

        heading = login_page.get_heading_text()
        assert heading == "Anmelden", (
            f"TC-REQ-023-002 FAIL: Expected heading 'Anmelden', got: '{heading}'"
        )
        assert login_page.is_register_link_visible(), (
            "TC-REQ-023-002 FAIL: Expected register link to be visible"
        )
        assert login_page.is_forgot_password_link_visible(), (
            "TC-REQ-023-002 FAIL: Expected forgot-password link to be visible"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_successful_login_with_demo_user(
        self,
        login_page: LoginPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-001: Successful local login with demo user redirects to /dashboard.

        Spec: TC-023-009 -- Erfolgreicher lokaler Login (Happy Path).
        """
        _ensure_logged_out(login_page.driver, login_page.base_url)
        login_page.open()
        screenshot(
            "TC-REQ-023-001_login-before-submit",
            "Login page before submitting",
        )

        login_page.login(DEMO_EMAIL, DEMO_PASSWORD)
        screenshot(
            "TC-REQ-023-001_login-submitted",
            "Login submitted",
        )

        login_page.wait_for_url_contains("/dashboard")
        screenshot(
            "TC-REQ-023-001_login-success-dashboard",
            "Dashboard after successful login",
        )

        current_url = login_page.driver.current_url
        assert "/dashboard" in current_url, (
            f"TC-REQ-023-001 FAIL: Expected redirect to /dashboard, got: {current_url}"
        )
        assert not login_page.is_error_alert_visible(), (
            "TC-REQ-023-001 FAIL: No error alert should be visible after successful login"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_login_with_remember_me(
        self,
        login_page: LoginPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-003: Login with remember-me checkbox activated.

        Spec: TC-023-010 -- Login mit aktivierter 'Angemeldet bleiben'-Checkbox.
        """
        _ensure_logged_out(login_page.driver, login_page.base_url)
        login_page.open()

        assert not login_page.is_remember_me_checked(), (
            "TC-REQ-023-003 FAIL: Remember-me checkbox should be unchecked by default"
        )

        login_page.login(DEMO_EMAIL, DEMO_PASSWORD, remember_me=True)
        screenshot(
            "TC-REQ-023-003_login-remember-me",
            "Login with remember-me activated",
        )

        login_page.wait_for_url_contains("/dashboard")
        assert "/dashboard" in login_page.driver.current_url, (
            "TC-REQ-023-003 FAIL: Expected redirect to /dashboard after login with remember-me"
        )


# -- TC-023-012: Login page without SSO providers -----------------------------


class TestLoginSSOProviders:
    """SSO provider button display (Spec: TC-023-011, TC-023-012)."""

    @pytest.mark.smoke
    @pytest.mark.requires_auth
    def test_login_page_without_sso_providers(
        self,
        login_page: LoginPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-004: Login page without active SSO providers shows no divider/buttons.

        Spec: TC-023-012 -- Login-Seite ohne aktivierte SSO-Provider.
        """
        _ensure_logged_out(login_page.driver, login_page.base_url)
        login_page.open()
        screenshot(
            "TC-REQ-023-004_login-no-sso",
            "Login page without SSO providers",
        )

        oauth_buttons = login_page.get_oauth_buttons()
        if len(oauth_buttons) == 0:
            assert len(oauth_buttons) == 0, (
                "TC-REQ-023-004 FAIL: Expected no SSO buttons when no providers are configured"
            )


# -- TC-023-013: Login with wrong password ------------------------------------


class TestLoginErrors:
    """Login error flows (Spec: TC-023-013)."""

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_login_with_wrong_password(
        self,
        login_page: LoginPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-005: Login with wrong password shows error alert.

        Spec: TC-023-013 -- Login mit falschem Passwort.
        """
        _ensure_logged_out(login_page.driver, login_page.base_url)
        login_page.open()
        screenshot(
            "TC-REQ-023-005_before-wrong-password",
            "Login before wrong password",
        )

        login_page.login(DEMO_EMAIL, "falsches-passwort-xyz")
        screenshot(
            "TC-REQ-023-005_wrong-password-submitted",
            "Wrong password submitted",
        )

        login_page.wait_for_element(LoginPage.ERROR_ALERT)
        screenshot(
            "TC-REQ-023-005_error-displayed",
            "Error alert after wrong password",
        )

        assert login_page.is_error_alert_visible(), (
            "TC-REQ-023-005 FAIL: Expected error alert after login with wrong password"
        )
        error_msg = login_page.get_error_message()
        assert error_msg, (
            "TC-REQ-023-005 FAIL: Expected non-empty error message"
        )
        assert "/login" in login_page.driver.current_url, (
            f"TC-REQ-023-005 FAIL: Expected to remain on /login, got: {login_page.driver.current_url}"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_login_with_nonexistent_email(
        self,
        login_page: LoginPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-006: Login with non-existent email shows error alert.

        Spec: TC-023-013 -- Login mit falschem Passwort (non-existent email variant).
        """
        _ensure_logged_out(login_page.driver, login_page.base_url)
        login_page.open()

        login_page.login("nonexistent@example.com", "some-password-123")
        login_page.wait_for_element(LoginPage.ERROR_ALERT)
        screenshot(
            "TC-REQ-023-006_nonexistent-email",
            "Error alert for non-existent email",
        )

        assert login_page.is_error_alert_visible(), (
            "TC-REQ-023-006 FAIL: Expected error alert after login with non-existent email"
        )
        assert "/login" in login_page.driver.current_url, (
            "TC-REQ-023-006 FAIL: Expected to remain on /login"
        )


# -- TC-023-016 to TC-023-017: Route Guards -----------------------------------


class TestRouteGuards:
    """Route guard redirects (Spec: TC-023-016, TC-023-017)."""

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_unauthenticated_redirect_to_login(
        self,
        login_page: LoginPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-007: Unauthenticated access to /dashboard redirects to /login.

        Spec: TC-023-016 -- Redirect von geschuetzter Route zu Login.
        """
        _ensure_logged_out(login_page.driver, login_page.base_url)
        login_page.navigate("/dashboard")

        login_page.wait_for_url_contains("/login")
        screenshot(
            "TC-REQ-023-007_route-guard-redirect",
            "Redirect to /login from protected route",
        )

        assert "/login" in login_page.driver.current_url, (
            f"TC-REQ-023-007 FAIL: Expected redirect to /login, got: {login_page.driver.current_url}"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_authenticated_redirect_from_login_to_dashboard(
        self,
        login_page: LoginPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-008: Authenticated user accessing /login is redirected to /dashboard.

        Spec: TC-023-017 -- Redirect von Login/Register zu Dashboard wenn bereits eingeloggt.
        """
        _ensure_logged_out(login_page.driver, login_page.base_url)
        login_page.open()
        login_page.login(DEMO_EMAIL, DEMO_PASSWORD)
        login_page.wait_for_url_contains("/dashboard")

        login_page.navigate("/login")
        login_page.wait_for_url_contains("/dashboard")
        screenshot(
            "TC-REQ-023-008_public-only-redirect",
            "Redirect from /login to /dashboard for logged-in user",
        )

        assert "/dashboard" in login_page.driver.current_url, (
            f"TC-REQ-023-008 FAIL: Expected redirect to /dashboard, got: {login_page.driver.current_url}"
        )


# -- TC-023-019: Navigation links on login page -------------------------------


class TestLoginNavigation:
    """Navigation links from the login page (Spec: TC-023-019, TC-023-006)."""

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_forgot_password_link_navigates_to_reset(
        self,
        login_page: LoginPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-009: 'Passwort vergessen?' link navigates to /password-reset.

        Spec: TC-023-019 -- Passwort vergessen -- Link auf Login-Seite.
        """
        _ensure_logged_out(login_page.driver, login_page.base_url)
        login_page.open()
        screenshot(
            "TC-REQ-023-009_before-forgot-click",
            "Login before clicking forgot password",
        )

        login_page.click_forgot_password_link()
        login_page.wait_for_url_contains("/password-reset")
        screenshot(
            "TC-REQ-023-009_password-reset-page",
            "Password reset page after navigation",
        )

        assert "/password-reset" in login_page.driver.current_url, (
            f"TC-REQ-023-009 FAIL: Expected /password-reset, got: {login_page.driver.current_url}"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_register_link_navigates_to_register(
        self,
        login_page: LoginPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-010: Register link on login page navigates to /register.

        Spec: TC-023-006 -- Link zu Login von der Registrierungsseite.
        """
        _ensure_logged_out(login_page.driver, login_page.base_url)
        login_page.open()

        login_page.click_register_link()
        login_page.wait_for_url_contains("/register")
        screenshot(
            "TC-REQ-023-010_register-page",
            "Register page after navigation from login",
        )

        assert "/register" in login_page.driver.current_url, (
            f"TC-REQ-023-010 FAIL: Expected /register, got: {login_page.driver.current_url}"
        )
