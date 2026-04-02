"""E2E tests for REQ-023 — Password Reset flows.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-023.md):
  TC-REQ-023-017  ->  TC-023-020  Passwort-Reset anfordern -- bekannte E-Mail
  TC-REQ-023-018  ->  TC-023-020  Passwort-Reset-Request Seite rendert
  TC-REQ-023-019  ->  TC-023-021  Passwort-Reset anfordern -- unbekannte E-Mail (Enumeration-Schutz)
  TC-REQ-023-020  ->  TC-023-022  Zurueck zur Anmeldung von Passwort-Reset-Seite
  TC-REQ-023-021  ->  TC-023-023  Neues-Passwort-Seite rendert
  TC-REQ-023-022  ->  TC-023-024  Neues Passwort -- Passwoerter stimmen nicht ueberein
  TC-REQ-023-023  ->  TC-023-025  Neues Passwort -- Token ungueltig
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import PasswordResetConfirmPage, PasswordResetRequestPage

pytestmark = pytest.mark.requires_auth

# -- Demo credentials ---------------------------------------------------------
DEMO_EMAIL = "demo@kamerplanter.example"


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def reset_request_page(browser: WebDriver, base_url: str) -> PasswordResetRequestPage:
    """Return a PasswordResetRequestPage bound to the test browser."""
    return PasswordResetRequestPage(browser, base_url)


@pytest.fixture
def reset_confirm_page(browser: WebDriver, base_url: str) -> PasswordResetConfirmPage:
    """Return a PasswordResetConfirmPage bound to the test browser."""
    return PasswordResetConfirmPage(browser, base_url)


def _ensure_logged_out(browser: WebDriver, base_url: str) -> None:
    """Clear auth state by deleting cookies."""
    browser.delete_all_cookies()
    browser.get(f"{base_url}/login")


# -- TC-023-020: Password reset request with known email -----------------------


class TestPasswordResetRequest:
    """Password reset request page (Spec: TC-023-020 to TC-023-022)."""

    @pytest.mark.smoke
    @pytest.mark.requires_auth
    def test_reset_request_page_renders(
        self,
        reset_request_page: PasswordResetRequestPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-018: Password-reset-request page renders with heading and form.

        Spec: TC-023-020 -- Passwort-Reset anfordern Seitenstruktur.
        """
        _ensure_logged_out(reset_request_page.driver, reset_request_page.base_url)
        reset_request_page.open()
        screenshot(
            "TC-REQ-023-018_reset-request-loaded",
            "Password reset request page after load",
        )

        heading = reset_request_page.get_heading_text()
        assert "zurücksetzen" in heading.lower() or "reset" in heading.lower(), (
            f"TC-REQ-023-018 FAIL: Expected heading about password reset, got: '{heading}'"
        )
        assert reset_request_page.is_email_form_visible(), (
            "TC-REQ-023-018 FAIL: Expected email form to be visible"
        )
        assert reset_request_page.is_back_to_login_visible(), (
            "TC-REQ-023-018 FAIL: Expected 'back to login' link to be visible"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_reset_request_known_email_shows_success(
        self,
        reset_request_page: PasswordResetRequestPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-017: Reset request with known email shows success alert (enumeration protection).

        Spec: TC-023-020 -- Passwort-Reset anfordern -- bekannte E-Mail (Enumeration-Schutz).
        """
        _ensure_logged_out(reset_request_page.driver, reset_request_page.base_url)
        reset_request_page.open()
        screenshot(
            "TC-REQ-023-017_before-submit",
            "Before submitting reset request",
        )

        reset_request_page.request_reset(DEMO_EMAIL)

        reset_request_page.wait_for_element_visible(PasswordResetRequestPage.SUCCESS_ALERT)
        screenshot(
            "TC-REQ-023-017_reset-success-known-email",
            "Success alert after reset request (known email)",
        )

        assert reset_request_page.is_success_alert_visible(), (
            "TC-REQ-023-017 FAIL: Expected success alert after password reset request"
        )
        success_text = reset_request_page.get_success_alert_text()
        assert "reset" in success_text.lower() or "link" in success_text.lower() or "konto" in success_text.lower(), (
            f"TC-REQ-023-017 FAIL: Expected success message about reset link, got: '{success_text}'"
        )
        assert not reset_request_page.is_email_form_visible(), (
            "TC-REQ-023-017 FAIL: Expected email form to be hidden after successful request"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_reset_request_unknown_email_shows_same_success(
        self,
        reset_request_page: PasswordResetRequestPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-019: Reset request with unknown email shows identical success (enumeration protection).

        Spec: TC-023-021 -- Passwort-Reset anfordern -- unbekannte E-Mail (Enumeration-Schutz).
        """
        _ensure_logged_out(reset_request_page.driver, reset_request_page.base_url)
        reset_request_page.open()

        reset_request_page.request_reset("nicht-vorhanden@example.com")

        reset_request_page.wait_for_element_visible(PasswordResetRequestPage.SUCCESS_ALERT)
        screenshot(
            "TC-REQ-023-019_reset-success-unknown-email",
            "Success alert after reset request (unknown email)",
        )

        assert reset_request_page.is_success_alert_visible(), (
            "TC-REQ-023-019 FAIL: Expected same success alert for unknown email (enumeration protection)"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_back_to_login_link(
        self,
        reset_request_page: PasswordResetRequestPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-020: 'Back to login' link navigates to /login.

        Spec: TC-023-022 -- Zurueck zur Anmeldung von Passwort-Reset-Seite.
        """
        _ensure_logged_out(reset_request_page.driver, reset_request_page.base_url)
        reset_request_page.open()

        reset_request_page.click_back_to_login()
        reset_request_page.wait_for_url_contains("/login")
        screenshot(
            "TC-REQ-023-020_back-to-login",
            "Navigation back to /login",
        )

        assert "/login" in reset_request_page.driver.current_url, (
            f"TC-REQ-023-020 FAIL: Expected /login, got: {reset_request_page.driver.current_url}"
        )


# -- TC-023-024 to TC-023-025: Password reset confirm -------------------------


class TestPasswordResetConfirm:
    """Password reset confirm page (Spec: TC-023-023 to TC-023-025)."""

    @pytest.mark.smoke
    @pytest.mark.requires_auth
    def test_reset_confirm_page_renders(
        self,
        reset_confirm_page: PasswordResetConfirmPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-021: Password-reset-confirm page renders with heading and form.

        Spec: TC-023-023 -- Neues Passwort setzen -- Seitenstruktur.
        """
        _ensure_logged_out(reset_confirm_page.driver, reset_confirm_page.base_url)
        reset_confirm_page.open(token="test-token-placeholder")
        screenshot(
            "TC-REQ-023-021_reset-confirm-loaded",
            "New password page after load",
        )

        heading = reset_confirm_page.get_heading_text()
        assert "passwort" in heading.lower() or "password" in heading.lower(), (
            f"TC-REQ-023-021 FAIL: Expected heading about new password, got: '{heading}'"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_reset_confirm_password_mismatch(
        self,
        reset_confirm_page: PasswordResetConfirmPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-022: Password mismatch on confirm page shows error.

        Spec: TC-023-024 -- Neues Passwort -- Passwoerter stimmen nicht ueberein.
        """
        _ensure_logged_out(reset_confirm_page.driver, reset_confirm_page.base_url)
        reset_confirm_page.open(token="test-token-placeholder")

        reset_confirm_page.reset_password(
            password="neues-passwort-2024",
            confirm_password="anderes-passwort",
        )
        screenshot(
            "TC-REQ-023-022_reset-confirm-mismatch",
            "Password mismatch on reset confirm page",
        )

        assert reset_confirm_page.is_error_alert_visible(), (
            "TC-REQ-023-022 FAIL: Expected error alert when passwords do not match"
        )
        error_msg = reset_confirm_page.get_error_message()
        assert "stimmen nicht" in error_msg.lower() or "mismatch" in error_msg.lower(), (
            f"TC-REQ-023-022 FAIL: Expected password mismatch error, got: '{error_msg}'"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_reset_confirm_invalid_token(
        self,
        reset_confirm_page: PasswordResetConfirmPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-023: Invalid or expired token shows error after submission.

        Spec: TC-023-025 -- Neues Passwort -- Token ungueltig.
        """
        _ensure_logged_out(reset_confirm_page.driver, reset_confirm_page.base_url)
        reset_confirm_page.open(token="invalid-expired-token-abc123")

        screenshot(
            "TC-REQ-023-023_before-submit-invalid-token",
            "Before submitting with invalid token",
        )

        reset_confirm_page.reset_password(password="neues-sicheres-passwort-2024")

        reset_confirm_page.wait_for_element(PasswordResetConfirmPage.ERROR_ALERT)
        screenshot(
            "TC-REQ-023-023_invalid-token-error",
            "Error after submitting with invalid token",
        )

        assert reset_confirm_page.is_error_alert_visible(), (
            "TC-REQ-023-023 FAIL: Expected error alert for invalid/expired token"
        )
