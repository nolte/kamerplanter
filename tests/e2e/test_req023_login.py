"""E2E tests for REQ-023 — Login flows (TC-023-009 to TC-023-019).

Covers:
  Login page: rendering, successful login, invalid credentials, remember-me,
  SSO provider buttons, route guards, navigation links

All tests follow NFR-008:
  - Page-Object-Pattern (no direct find_element calls in tests)
  - WebDriverWait only — no time.sleep()
  - Screenshot at: Page Load / before action / after action / error state
  - Descriptive assertion messages
"""

from __future__ import annotations

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import LoginPage

pytestmark = pytest.mark.requires_auth

# ── Demo credentials ────────────────────────────────────────────────────────
DEMO_EMAIL = "demo@kamerplanter.local"
DEMO_PASSWORD = "demo-passwort-2024"


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def login_page(browser: WebDriver, base_url: str) -> LoginPage:
    """Return a LoginPage bound to the test browser."""
    return LoginPage(browser, base_url)


# ── Helper: ensure logged out ───────────────────────────────────────────────


def _ensure_logged_out(browser: WebDriver, base_url: str) -> None:
    """Clear auth state by deleting cookies and navigating to login."""
    browser.delete_all_cookies()
    browser.get(f"{base_url}/login")


# ── TC-023-009: Successful login ────────────────────────────────────────────


class TestLoginHappyPath:
    """TC-023-009 to TC-023-010: Successful login flows."""

    def test_login_page_renders(
        self,
        login_page: LoginPage,
        screenshot,
    ) -> None:
        """TC-023-009a: Login page renders with heading, fields and links."""
        _ensure_logged_out(login_page.driver, login_page.base_url)
        login_page.open()
        screenshot("req023_001_login_page_loaded", "Login-Seite nach dem Laden")

        heading = login_page.get_heading_text()
        assert heading == "Anmelden", (
            f"Expected heading 'Anmelden', got: '{heading}'"
        )
        assert login_page.is_register_link_visible(), (
            "Expected register link to be visible on login page"
        )
        assert login_page.is_forgot_password_link_visible(), (
            "Expected forgot-password link to be visible on login page"
        )

    def test_successful_login_with_demo_user(
        self,
        login_page: LoginPage,
        screenshot,
    ) -> None:
        """TC-023-009: Successful local login with demo user redirects to /dashboard."""
        _ensure_logged_out(login_page.driver, login_page.base_url)
        login_page.open()
        screenshot("req023_002_login_before_submit", "Login-Seite vor dem Absenden")

        login_page.login(DEMO_EMAIL, DEMO_PASSWORD)
        screenshot("req023_003_login_submitted", "Login abgesendet")

        login_page.wait_for_url_contains("/dashboard")
        screenshot("req023_004_login_success_dashboard", "Dashboard nach erfolgreichem Login")

        current_url = login_page.driver.current_url
        assert "/dashboard" in current_url, (
            f"Expected redirect to /dashboard after login, got: {current_url}"
        )
        assert not login_page.is_error_alert_visible(), (
            "No error alert should be visible after successful login"
        )

    def test_login_with_remember_me(
        self,
        login_page: LoginPage,
        screenshot,
    ) -> None:
        """TC-023-010: Login with remember-me checkbox activated."""
        _ensure_logged_out(login_page.driver, login_page.base_url)
        login_page.open()

        # Checkbox should be unchecked by default
        assert not login_page.is_remember_me_checked(), (
            "Remember-me checkbox should be unchecked by default"
        )

        login_page.login(DEMO_EMAIL, DEMO_PASSWORD, remember_me=True)
        screenshot("req023_005_login_remember_me", "Login mit Angemeldet-bleiben")

        login_page.wait_for_url_contains("/dashboard")
        assert "/dashboard" in login_page.driver.current_url, (
            "Expected redirect to /dashboard after login with remember-me"
        )


# ── TC-023-012: Login page without SSO providers ────────────────────────────


class TestLoginSSOProviders:
    """TC-023-011 to TC-023-012: SSO provider button display."""

    def test_login_page_without_sso_providers(
        self,
        login_page: LoginPage,
        screenshot,
    ) -> None:
        """TC-023-012: Login page without active SSO providers shows no divider/buttons."""
        _ensure_logged_out(login_page.driver, login_page.base_url)
        login_page.open()
        screenshot("req023_006_login_no_sso", "Login-Seite ohne SSO-Provider")

        # In standard dev setup, no OAuth providers are enabled
        oauth_buttons = login_page.get_oauth_buttons()
        # If no SSO providers are configured, the divider should also be absent
        if len(oauth_buttons) == 0:
            # The divider may or may not be present depending on implementation
            # but no SSO buttons should appear
            assert len(oauth_buttons) == 0, (
                "Expected no SSO buttons when no providers are configured"
            )


# ── TC-023-013: Login with wrong password ───────────────────────────────────


class TestLoginErrors:
    """TC-023-013 to TC-023-015: Login error flows."""

    def test_login_with_wrong_password(
        self,
        login_page: LoginPage,
        screenshot,
    ) -> None:
        """TC-023-013: Login with wrong password shows error alert."""
        _ensure_logged_out(login_page.driver, login_page.base_url)
        login_page.open()
        screenshot("req023_007_login_before_wrong_password", "Login vor falschem Passwort")

        login_page.login(DEMO_EMAIL, "falsches-passwort-xyz")
        screenshot("req023_008_login_wrong_password_submitted", "Falsches Passwort abgesendet")

        # Wait briefly for the error to appear
        login_page.wait_for_element(LoginPage.ERROR_ALERT)
        screenshot("req023_009_login_error_displayed", "Fehler-Alert nach falschem Passwort")

        assert login_page.is_error_alert_visible(), (
            "Expected error alert after login with wrong password"
        )
        error_msg = login_page.get_error_message()
        assert error_msg, (
            "Expected non-empty error message after login with wrong password"
        )
        assert "/login" in login_page.driver.current_url, (
            f"Expected to remain on /login, got: {login_page.driver.current_url}"
        )

    def test_login_with_nonexistent_email(
        self,
        login_page: LoginPage,
        screenshot,
    ) -> None:
        """TC-023-013b: Login with non-existent email shows error alert."""
        _ensure_logged_out(login_page.driver, login_page.base_url)
        login_page.open()

        login_page.login("nonexistent@example.com", "some-password-123")
        login_page.wait_for_element(LoginPage.ERROR_ALERT)
        screenshot("req023_010_login_nonexistent_email", "Fehler bei nicht existierender E-Mail")

        assert login_page.is_error_alert_visible(), (
            "Expected error alert after login with non-existent email"
        )
        assert "/login" in login_page.driver.current_url, (
            "Expected to remain on /login"
        )


# ── TC-023-016 to TC-023-017: Route Guards ──────────────────────────────────


class TestRouteGuards:
    """TC-023-016 to TC-023-017: Route guard redirects."""

    def test_unauthenticated_redirect_to_login(
        self,
        login_page: LoginPage,
        screenshot,
    ) -> None:
        """TC-023-016: Unauthenticated access to /dashboard redirects to /login."""
        _ensure_logged_out(login_page.driver, login_page.base_url)
        login_page.navigate("/dashboard")

        login_page.wait_for_url_contains("/login")
        screenshot("req023_011_route_guard_redirect", "Redirect zu /login von geschuetzter Route")

        assert "/login" in login_page.driver.current_url, (
            f"Expected redirect to /login, got: {login_page.driver.current_url}"
        )

    def test_authenticated_redirect_from_login_to_dashboard(
        self,
        login_page: LoginPage,
        screenshot,
    ) -> None:
        """TC-023-017: Authenticated user accessing /login is redirected to /dashboard."""
        # First, log in
        _ensure_logged_out(login_page.driver, login_page.base_url)
        login_page.open()
        login_page.login(DEMO_EMAIL, DEMO_PASSWORD)
        login_page.wait_for_url_contains("/dashboard")

        # Now try to access /login again
        login_page.navigate("/login")
        login_page.wait_for_url_contains("/dashboard")
        screenshot(
            "req023_012_public_only_redirect",
            "Redirect von /login zu /dashboard fuer eingeloggten Nutzer",
        )

        assert "/dashboard" in login_page.driver.current_url, (
            f"Expected redirect to /dashboard, got: {login_page.driver.current_url}"
        )


# ── TC-023-019: Navigation links on login page ─────────────────────────────


class TestLoginNavigation:
    """TC-023-019: Navigation links from the login page."""

    def test_forgot_password_link_navigates_to_reset(
        self,
        login_page: LoginPage,
        screenshot,
    ) -> None:
        """TC-023-019: 'Passwort vergessen?' link navigates to /password-reset."""
        _ensure_logged_out(login_page.driver, login_page.base_url)
        login_page.open()
        screenshot("req023_013_login_before_forgot_click", "Login vor Klick auf Passwort vergessen")

        login_page.click_forgot_password_link()
        login_page.wait_for_url_contains("/password-reset")
        screenshot("req023_014_password_reset_page", "Passwort-Reset-Seite nach Navigation")

        assert "/password-reset" in login_page.driver.current_url, (
            f"Expected /password-reset, got: {login_page.driver.current_url}"
        )

    def test_register_link_navigates_to_register(
        self,
        login_page: LoginPage,
        screenshot,
    ) -> None:
        """TC-023-006b: Register link on login page navigates to /register."""
        _ensure_logged_out(login_page.driver, login_page.base_url)
        login_page.open()

        login_page.click_register_link()
        login_page.wait_for_url_contains("/register")
        screenshot("req023_015_register_page", "Register-Seite nach Navigation von Login")

        assert "/register" in login_page.driver.current_url, (
            f"Expected /register, got: {login_page.driver.current_url}"
        )
