"""E2E tests for REQ-023 — Password Reset flows (TC-023-020 to TC-023-025).

Covers:
  Password reset request: enumeration protection (known + unknown email),
  success message, back-to-login link
  Password reset confirm: password mismatch, invalid token

All tests follow NFR-008:
  - Page-Object-Pattern (no direct find_element calls in tests)
  - WebDriverWait only — no time.sleep()
  - Screenshot at: Page Load / before action / after action / error state
  - Descriptive assertion messages
"""

from __future__ import annotations

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import PasswordResetConfirmPage, PasswordResetRequestPage

pytestmark = pytest.mark.requires_auth

# ── Demo credentials ────────────────────────────────────────────────────────
DEMO_EMAIL = "demo@kamerplanter.local"


# ── Fixtures ────────────────────────────────────────────────────────────────


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


# ── TC-023-020: Password reset request with known email ─────────────────────


class TestPasswordResetRequest:
    """TC-023-020 to TC-023-022: Password reset request page."""

    def test_reset_request_page_renders(
        self,
        reset_request_page: PasswordResetRequestPage,
        screenshot,
    ) -> None:
        """TC-023-020a: Password-reset-request page renders with heading and form."""
        _ensure_logged_out(reset_request_page.driver, reset_request_page.base_url)
        reset_request_page.open()
        screenshot("req023_030_reset_request_loaded", "Passwort-Reset-Seite nach dem Laden")

        heading = reset_request_page.get_heading_text()
        assert "zurücksetzen" in heading.lower() or "reset" in heading.lower(), (
            f"Expected heading about password reset, got: '{heading}'"
        )
        assert reset_request_page.is_email_form_visible(), (
            "Expected email form to be visible on password-reset page"
        )
        assert reset_request_page.is_back_to_login_visible(), (
            "Expected 'back to login' link to be visible"
        )

    def test_reset_request_known_email_shows_success(
        self,
        reset_request_page: PasswordResetRequestPage,
        screenshot,
    ) -> None:
        """TC-023-020: Reset request with known email shows success alert (enumeration protection)."""
        _ensure_logged_out(reset_request_page.driver, reset_request_page.base_url)
        reset_request_page.open()
        screenshot("req023_031_reset_before_submit", "Vor Absenden des Reset-Requests")

        reset_request_page.request_reset(DEMO_EMAIL)

        # Wait for success alert
        reset_request_page.wait_for_element_visible(PasswordResetRequestPage.SUCCESS_ALERT)
        screenshot("req023_032_reset_success_known_email", "Erfolgs-Alert nach Reset-Request (bekannte E-Mail)")

        assert reset_request_page.is_success_alert_visible(), (
            "Expected success alert after password reset request"
        )
        success_text = reset_request_page.get_success_alert_text()
        assert "reset" in success_text.lower() or "link" in success_text.lower() or "konto" in success_text.lower(), (
            f"Expected success message about reset link, got: '{success_text}'"
        )
        # Form should be replaced by success state
        assert not reset_request_page.is_email_form_visible(), (
            "Expected email form to be hidden after successful reset request"
        )

    def test_reset_request_unknown_email_shows_same_success(
        self,
        reset_request_page: PasswordResetRequestPage,
        screenshot,
    ) -> None:
        """TC-023-021: Reset request with unknown email shows identical success (enumeration protection)."""
        _ensure_logged_out(reset_request_page.driver, reset_request_page.base_url)
        reset_request_page.open()

        reset_request_page.request_reset("nicht-vorhanden@example.com")

        reset_request_page.wait_for_element_visible(PasswordResetRequestPage.SUCCESS_ALERT)
        screenshot("req023_033_reset_success_unknown_email", "Erfolgs-Alert nach Reset-Request (unbekannte E-Mail)")

        assert reset_request_page.is_success_alert_visible(), (
            "Expected same success alert for unknown email (enumeration protection)"
        )

    def test_back_to_login_link(
        self,
        reset_request_page: PasswordResetRequestPage,
        screenshot,
    ) -> None:
        """TC-023-022: 'Back to login' link navigates to /login."""
        _ensure_logged_out(reset_request_page.driver, reset_request_page.base_url)
        reset_request_page.open()

        reset_request_page.click_back_to_login()
        reset_request_page.wait_for_url_contains("/login")
        screenshot("req023_034_reset_back_to_login", "Navigation zurueck zu /login")

        assert "/login" in reset_request_page.driver.current_url, (
            f"Expected /login, got: {reset_request_page.driver.current_url}"
        )


# ── TC-023-024 to TC-023-025: Password reset confirm ───────────────────────


class TestPasswordResetConfirm:
    """TC-023-024 to TC-023-025: Password reset confirm page."""

    def test_reset_confirm_page_renders(
        self,
        reset_confirm_page: PasswordResetConfirmPage,
        screenshot,
    ) -> None:
        """TC-023-023a: Password-reset-confirm page renders with heading and form."""
        _ensure_logged_out(reset_confirm_page.driver, reset_confirm_page.base_url)
        reset_confirm_page.open(token="test-token-placeholder")
        screenshot("req023_035_reset_confirm_loaded", "Neues-Passwort-Seite nach dem Laden")

        heading = reset_confirm_page.get_heading_text()
        assert "passwort" in heading.lower() or "password" in heading.lower(), (
            f"Expected heading about new password, got: '{heading}'"
        )

    def test_reset_confirm_password_mismatch(
        self,
        reset_confirm_page: PasswordResetConfirmPage,
        screenshot,
    ) -> None:
        """TC-023-024: Password mismatch on confirm page shows error."""
        _ensure_logged_out(reset_confirm_page.driver, reset_confirm_page.base_url)
        reset_confirm_page.open(token="test-token-placeholder")

        reset_confirm_page.reset_password(
            password="neues-passwort-2024",
            confirm_password="anderes-passwort",
        )
        screenshot("req023_036_reset_confirm_mismatch", "Passwort-Mismatch bei Passwort-Reset")

        assert reset_confirm_page.is_error_alert_visible(), (
            "Expected error alert when passwords do not match"
        )
        error_msg = reset_confirm_page.get_error_message()
        assert "stimmen nicht" in error_msg.lower() or "mismatch" in error_msg.lower(), (
            f"Expected password mismatch error, got: '{error_msg}'"
        )

    def test_reset_confirm_invalid_token(
        self,
        reset_confirm_page: PasswordResetConfirmPage,
        screenshot,
    ) -> None:
        """TC-023-025: Invalid or expired token shows error after submission."""
        _ensure_logged_out(reset_confirm_page.driver, reset_confirm_page.base_url)
        reset_confirm_page.open(token="invalid-expired-token-abc123")

        screenshot("req023_037_reset_confirm_before_submit", "Vor Absenden mit ungueltigem Token")

        reset_confirm_page.reset_password(password="neues-sicheres-passwort-2024")

        # Wait for error alert (server rejects invalid token)
        reset_confirm_page.wait_for_element(PasswordResetConfirmPage.ERROR_ALERT)
        screenshot("req023_038_reset_confirm_invalid_token", "Fehler bei ungueltigem Token")

        assert reset_confirm_page.is_error_alert_visible(), (
            "Expected error alert for invalid/expired token"
        )
