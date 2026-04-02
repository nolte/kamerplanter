"""E2E tests for REQ-023 — Registration flows.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-023.md):
  TC-REQ-023-011  ->  TC-023-001  Erfolgreiche lokale Registrierung (Happy Path)
  TC-REQ-023-012  ->  TC-023-001  Registrierungsseite rendert mit Heading und Feldern
  TC-REQ-023-013  ->  TC-023-002  Registrierung -- Passwoerter stimmen nicht ueberein
  TC-REQ-023-014  ->  TC-023-003  Registrierung -- Passwort zu kurz (Hinweistext)
  TC-REQ-023-015  ->  TC-023-005  Registrierung -- E-Mail bereits registriert (Enumeration-Schutz)
  TC-REQ-023-016  ->  TC-023-006  Link zu Login von der Registrierungsseite
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable
import uuid

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

pytestmark = pytest.mark.requires_auth

from .pages import RegisterPage

# -- Demo credentials ---------------------------------------------------------
DEMO_EMAIL = "demo@kamerplanter.local"


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def register_page(browser: WebDriver, base_url: str) -> RegisterPage:
    """Return a RegisterPage bound to the test browser."""
    return RegisterPage(browser, base_url)


def _ensure_logged_out(browser: WebDriver, base_url: str) -> None:
    """Clear auth state by deleting cookies."""
    browser.delete_all_cookies()
    browser.get(f"{base_url}/login")


# -- TC-023-001: Successful registration ---------------------------------------


class TestRegistrationHappyPath:
    """Successful local registration (Spec: TC-023-001)."""

    @pytest.mark.smoke
    @pytest.mark.requires_auth
    def test_register_page_renders(
        self,
        register_page: RegisterPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-012: Registration page renders with heading and form fields.

        Spec: TC-023-001 -- Erfolgreiche lokale Registrierung (Seitenstruktur).
        """
        _ensure_logged_out(register_page.driver, register_page.base_url)
        register_page.open()
        screenshot(
            "TC-REQ-023-012_register-page-loaded",
            "Registration page after initial load",
        )

        heading = register_page.get_heading_text()
        assert heading == "Registrieren", (
            f"TC-REQ-023-012 FAIL: Expected heading 'Registrieren', got: '{heading}'"
        )
        assert register_page.is_login_link_visible(), (
            "TC-REQ-023-012 FAIL: Expected 'Already registered? Login' link to be visible"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_successful_registration(
        self,
        register_page: RegisterPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-011: Successful registration with valid data redirects to /login.

        Spec: TC-023-001 -- Erfolgreiche lokale Registrierung (Happy Path).
        """
        _ensure_logged_out(register_page.driver, register_page.base_url)
        register_page.open()

        unique_email = f"test-{uuid.uuid4().hex[:8]}@example.com"

        screenshot(
            "TC-REQ-023-011_register-before-submit",
            "Registration before submit",
        )

        register_page.register(
            display_name="Neuer Gaertner",
            email=unique_email,
            password="sicheres-passwort-2024",
        )

        register_page.wait_for_url_contains("/login")
        screenshot(
            "TC-REQ-023-011_register-success-redirect",
            "Redirect to /login after registration",
        )

        assert "/login" in register_page.driver.current_url, (
            f"TC-REQ-023-011 FAIL: Expected redirect to /login, got: {register_page.driver.current_url}"
        )


# -- TC-023-002: Password mismatch --------------------------------------------


class TestRegistrationValidation:
    """Registration form validation (Spec: TC-023-002, TC-023-003)."""

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_password_mismatch_shows_error(
        self,
        register_page: RegisterPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-013: Password mismatch shows error alert.

        Spec: TC-023-002 -- Registrierung -- Passwoerter stimmen nicht ueberein.
        """
        _ensure_logged_out(register_page.driver, register_page.base_url)
        register_page.open()

        register_page.register(
            display_name="Test User",
            email="test@example.com",
            password="passwort-2024",
            confirm_password="anderes-passwort",
        )

        screenshot(
            "TC-REQ-023-013_register-password-mismatch",
            "Password mismatch error message",
        )

        assert register_page.is_error_alert_visible(), (
            "TC-REQ-023-013 FAIL: Expected error alert when passwords do not match"
        )
        error_msg = register_page.get_error_message()
        assert "stimmen nicht" in error_msg.lower() or "mismatch" in error_msg.lower(), (
            f"TC-REQ-023-013 FAIL: Expected password mismatch message, got: '{error_msg}'"
        )
        assert "/register" in register_page.driver.current_url, (
            f"TC-REQ-023-013 FAIL: Expected to stay on /register, got: {register_page.driver.current_url}"
        )

    @pytest.mark.smoke
    @pytest.mark.requires_auth
    def test_password_helper_text_visible(
        self,
        register_page: RegisterPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-014: Password field shows helper text with minimum length requirement.

        Spec: TC-023-003 -- Registrierung -- Passwort zu kurz (Hinweistext).
        """
        _ensure_logged_out(register_page.driver, register_page.base_url)
        register_page.open()
        screenshot(
            "TC-REQ-023-014_register-password-helper",
            "Password helper text visible",
        )

        helper_text = register_page.get_password_helper_text()
        assert "10" in helper_text, (
            f"TC-REQ-023-014 FAIL: Expected password helper text to mention '10' characters, got: '{helper_text}'"
        )


# -- TC-023-005: Duplicate email (enumeration protection) ---------------------


class TestRegistrationEnumerationProtection:
    """Registration with existing email shows same response (Spec: TC-023-005)."""

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_duplicate_email_shows_same_response(
        self,
        register_page: RegisterPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-015: Registering with existing email shows success (enumeration protection).

        Spec: TC-023-005 -- Registrierung -- E-Mail-Adresse bereits registriert (Enumeration-Schutz).
        """
        _ensure_logged_out(register_page.driver, register_page.base_url)
        register_page.open()

        screenshot(
            "TC-REQ-023-015_before-duplicate",
            "Before registration with existing email",
        )

        register_page.register(
            display_name="Demo Kopie",
            email=DEMO_EMAIL,
            password="sicheres-passwort-2024",
        )

        register_page.wait_for_url_contains("/login")
        screenshot(
            "TC-REQ-023-015_after-duplicate",
            "After registration with existing email",
        )

        assert "/login" in register_page.driver.current_url, (
            f"TC-REQ-023-015 FAIL: Expected redirect to /login (enumeration protection), "
            f"got: {register_page.driver.current_url}"
        )


# -- TC-023-006: Navigation link to login -------------------------------------


class TestRegistrationNavigation:
    """Navigation from registration to login page (Spec: TC-023-006)."""

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_login_link_navigates_to_login(
        self,
        register_page: RegisterPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-016: 'Already registered? Login' link navigates to /login.

        Spec: TC-023-006 -- Link zu Login von der Registrierungsseite.
        """
        _ensure_logged_out(register_page.driver, register_page.base_url)
        register_page.open()

        register_page.click_login_link()
        register_page.wait_for_url_contains("/login")
        screenshot(
            "TC-REQ-023-016_register-to-login",
            "Navigation from register to login",
        )

        assert "/login" in register_page.driver.current_url, (
            f"TC-REQ-023-016 FAIL: Expected /login, got: {register_page.driver.current_url}"
        )
