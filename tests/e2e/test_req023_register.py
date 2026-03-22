"""E2E tests for REQ-023 — Registration flows (TC-023-001 to TC-023-006).

Covers:
  Registration page: rendering, successful registration (happy path),
  password mismatch validation, password helper text, duplicate email
  (enumeration protection), navigation link to login

All tests follow NFR-008:
  - Page-Object-Pattern (no direct find_element calls in tests)
  - WebDriverWait only — no time.sleep()
  - Screenshot at: Page Load / before action / after action / error state
  - Descriptive assertion messages
"""

from __future__ import annotations

import uuid

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

pytestmark = pytest.mark.requires_auth

from .pages import RegisterPage

# ── Demo credentials ────────────────────────────────────────────────────────
DEMO_EMAIL = "demo@kamerplanter.local"


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def register_page(browser: WebDriver, base_url: str) -> RegisterPage:
    """Return a RegisterPage bound to the test browser."""
    return RegisterPage(browser, base_url)


def _ensure_logged_out(browser: WebDriver, base_url: str) -> None:
    """Clear auth state by deleting cookies."""
    browser.delete_all_cookies()
    browser.get(f"{base_url}/login")


# ── TC-023-001: Successful registration ─────────────────────────────────────


class TestRegistrationHappyPath:
    """TC-023-001: Successful local registration."""

    def test_register_page_renders(
        self,
        register_page: RegisterPage,
        screenshot,
    ) -> None:
        """TC-023-001a: Registration page renders with heading and form fields."""
        _ensure_logged_out(register_page.driver, register_page.base_url)
        register_page.open()
        screenshot("req023_020_register_page_loaded", "Registrierungs-Seite nach dem Laden")

        heading = register_page.get_heading_text()
        assert heading == "Registrieren", (
            f"Expected heading 'Registrieren', got: '{heading}'"
        )
        assert register_page.is_login_link_visible(), (
            "Expected 'Already registered? Login' link to be visible"
        )

    def test_successful_registration(
        self,
        register_page: RegisterPage,
        screenshot,
    ) -> None:
        """TC-023-001: Successful registration with valid data redirects to /login."""
        _ensure_logged_out(register_page.driver, register_page.base_url)
        register_page.open()

        # Use unique email to avoid conflicts
        unique_email = f"test-{uuid.uuid4().hex[:8]}@example.com"

        screenshot("req023_021_register_before_submit", "Registrierung vor dem Absenden")

        register_page.register(
            display_name="Neuer Gaertner",
            email=unique_email,
            password="sicheres-passwort-2024",
        )

        # After successful registration, expect redirect to /login
        register_page.wait_for_url_contains("/login")
        screenshot("req023_022_register_success_redirect", "Redirect zu /login nach Registrierung")

        assert "/login" in register_page.driver.current_url, (
            f"Expected redirect to /login after registration, got: {register_page.driver.current_url}"
        )


# ── TC-023-002: Password mismatch ──────────────────────────────────────────


class TestRegistrationValidation:
    """TC-023-002 to TC-023-004: Registration form validation."""

    def test_password_mismatch_shows_error(
        self,
        register_page: RegisterPage,
        screenshot,
    ) -> None:
        """TC-023-002: Password mismatch shows error alert."""
        _ensure_logged_out(register_page.driver, register_page.base_url)
        register_page.open()

        register_page.register(
            display_name="Test User",
            email="test@example.com",
            password="passwort-2024",
            confirm_password="anderes-passwort",
        )

        screenshot("req023_023_register_password_mismatch", "Passwort-Mismatch Fehlermeldung")

        assert register_page.is_error_alert_visible(), (
            "Expected error alert when passwords do not match"
        )
        error_msg = register_page.get_error_message()
        assert "stimmen nicht" in error_msg.lower() or "mismatch" in error_msg.lower(), (
            f"Expected password mismatch message, got: '{error_msg}'"
        )
        # Should stay on /register
        assert "/register" in register_page.driver.current_url, (
            f"Expected to stay on /register, got: {register_page.driver.current_url}"
        )

    def test_password_helper_text_visible(
        self,
        register_page: RegisterPage,
        screenshot,
    ) -> None:
        """TC-023-003: Password field shows helper text with minimum length requirement."""
        _ensure_logged_out(register_page.driver, register_page.base_url)
        register_page.open()
        screenshot("req023_024_register_password_helper", "Passwort-Hilfetext sichtbar")

        helper_text = register_page.get_password_helper_text()
        assert "10" in helper_text, (
            f"Expected password helper text to mention '10' characters, got: '{helper_text}'"
        )


# ── TC-023-005: Duplicate email (enumeration protection) ───────────────────


class TestRegistrationEnumerationProtection:
    """TC-023-005: Registration with existing email shows same response as new registration."""

    def test_duplicate_email_shows_same_response(
        self,
        register_page: RegisterPage,
        screenshot,
    ) -> None:
        """TC-023-005: Registering with existing email shows success (enumeration protection)."""
        _ensure_logged_out(register_page.driver, register_page.base_url)
        register_page.open()

        screenshot("req023_025_register_duplicate_before", "Vor Registrierung mit existierender E-Mail")

        register_page.register(
            display_name="Demo Kopie",
            email=DEMO_EMAIL,
            password="sicheres-passwort-2024",
        )

        # Enumeration protection: should show success and redirect to /login
        # just like a real new registration
        register_page.wait_for_url_contains("/login")
        screenshot("req023_026_register_duplicate_after", "Nach Registrierung mit existierender E-Mail")

        assert "/login" in register_page.driver.current_url, (
            f"Expected redirect to /login (enumeration protection), got: {register_page.driver.current_url}"
        )


# ── TC-023-006: Navigation link to login ────────────────────────────────────


class TestRegistrationNavigation:
    """TC-023-006: Navigation from registration to login page."""

    def test_login_link_navigates_to_login(
        self,
        register_page: RegisterPage,
        screenshot,
    ) -> None:
        """TC-023-006: 'Already registered? Login' link navigates to /login."""
        _ensure_logged_out(register_page.driver, register_page.base_url)
        register_page.open()

        register_page.click_login_link()
        register_page.wait_for_url_contains("/login")
        screenshot("req023_027_register_to_login", "Navigation von Register zu Login")

        assert "/login" in register_page.driver.current_url, (
            f"Expected /login, got: {register_page.driver.current_url}"
        )
