"""E2E tests for REQ-023 -- Email Verification flows.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-023.md):
  TC-REQ-023-040  ->  TC-023-007  E-Mail-Verifizierung -- Seite rendert mit Heading
  TC-REQ-023-041  ->  TC-023-008  E-Mail-Verifizierung -- Ungueltiger Token zeigt Fehler-Alert
  TC-REQ-023-042  ->  TC-023-008  Fehler-Alert -- Kein Erfolgs-Alert sichtbar
  TC-REQ-023-043  ->  TC-023-007  Login-Link ist sichtbar nach Verarbeitung
  TC-REQ-023-044  ->  TC-023-007  Login-Link navigiert zu /login
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import EmailVerificationPage


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def verification_page(browser: WebDriver, base_url: str) -> EmailVerificationPage:
    """Return an EmailVerificationPage bound to the test browser."""
    return EmailVerificationPage(browser, base_url)


def _ensure_logged_out(browser: WebDriver, base_url: str) -> None:
    """Clear auth state by deleting cookies."""
    browser.delete_all_cookies()
    browser.get(f"{base_url}/login")


# -- TC-023-007 / TC-023-008: Page rendering -----------------------------------


@pytest.mark.requires_auth
class TestEmailVerificationPageLoad:
    """EmailVerificationPage renders with heading (Spec: TC-023-007, TC-023-008)."""

    @pytest.mark.smoke
    def test_verification_page_renders_with_heading(
        self,
        verification_page: EmailVerificationPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-040: Email verification page loads with heading.

        Spec: TC-023-007 -- Seite laed mit Ueberschrift 'E-Mail-Verifizierung'.
        """
        _ensure_logged_out(verification_page.driver, verification_page.base_url)
        verification_page.open("test-token-e2e")
        screenshot(
            "TC-REQ-023-040_verification-page-loaded",
            "EmailVerificationPage after initial load",
        )

        heading = verification_page.get_heading_text()
        assert heading, (
            "TC-REQ-023-040 FAIL: Expected heading text on EmailVerificationPage"
        )


# -- TC-023-008: Invalid token shows error ------------------------------------


@pytest.mark.requires_auth
class TestEmailVerificationInvalidToken:
    """Invalid token shows error alert (Spec: TC-023-008)."""

    @pytest.mark.core_crud
    def test_invalid_token_shows_error_alert(
        self,
        verification_page: EmailVerificationPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-041: Invalid token shows red error alert.

        Spec: TC-023-008 -- E-Mail-Verifizierung mit ungueltigem Token.
        """
        _ensure_logged_out(verification_page.driver, verification_page.base_url)
        verification_page.open("ungueltigertoken123")

        screenshot(
            "TC-REQ-023-041_verification-before-result",
            "EmailVerificationPage loading with invalid token",
        )

        assert verification_page.is_error_alert_visible(), (
            "TC-REQ-023-041 FAIL: Expected error alert for invalid verification token"
        )

        error_text = verification_page.get_error_alert_text()
        screenshot(
            "TC-REQ-023-041_verification-invalid-token-error",
            "EmailVerificationPage error alert for invalid token",
        )

        assert error_text, (
            "TC-REQ-023-041 FAIL: Expected error alert text, got empty string"
        )

    @pytest.mark.core_crud
    def test_invalid_token_no_success_alert(
        self,
        verification_page: EmailVerificationPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-042: Invalid token does NOT show success alert.

        Spec: TC-023-008 -- Es erscheint KEIN Erfolgsmeldung.
        """
        _ensure_logged_out(verification_page.driver, verification_page.base_url)
        verification_page.open("falschertoken456")

        # Wait for error to appear (confirms page has finished processing)
        assert verification_page.is_error_alert_visible(), (
            "TC-REQ-023-042 FAIL: Expected error alert to confirm page finished processing"
        )

        screenshot(
            "TC-REQ-023-042_verification-no-success",
            "EmailVerificationPage with invalid token -- no success alert",
        )

        assert not verification_page.is_success_alert_visible(), (
            "TC-REQ-023-042 FAIL: Success alert should NOT be visible for invalid token"
        )


# -- TC-023-007: Login link visibility and navigation --------------------------


@pytest.mark.requires_auth
class TestEmailVerificationLoginLink:
    """Login link is visible and navigates to /login (Spec: TC-023-007, TC-023-008)."""

    @pytest.mark.core_crud
    def test_login_link_visible_after_error(
        self,
        verification_page: EmailVerificationPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-043: Login link is visible after token processing (error case).

        Spec: TC-023-008 -- Ein Link 'Zurueck zur Anmeldung' ist sichtbar.
        """
        _ensure_logged_out(verification_page.driver, verification_page.base_url)
        verification_page.open("token-fuer-link-test")

        # Wait for error state to confirm processing is done
        assert verification_page.is_error_alert_visible(), (
            "TC-REQ-023-043 FAIL: Expected error alert (precondition for login link check)"
        )

        screenshot(
            "TC-REQ-023-043_verification-login-link-visible",
            "EmailVerificationPage with login link visible",
        )

        assert verification_page.is_login_button_visible(), (
            "TC-REQ-023-043 FAIL: Expected login link/button to be visible after verification"
        )

    @pytest.mark.core_crud
    def test_login_link_navigates_to_login(
        self,
        verification_page: EmailVerificationPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-023-044: Clicking login link navigates to /login.

        Spec: TC-023-007 -- Nutzer kann auf den Link klicken und wird zu /login weitergeleitet.
        """
        _ensure_logged_out(verification_page.driver, verification_page.base_url)
        verification_page.open("token-fuer-nav-test")

        # Wait for processing to complete
        assert verification_page.is_error_alert_visible(), (
            "TC-REQ-023-044 FAIL: Expected error alert (precondition for navigation test)"
        )

        screenshot(
            "TC-REQ-023-044_verification-before-login-click",
            "EmailVerificationPage before clicking login link",
        )

        verification_page.click_login()
        verification_page.wait_for_url_contains("/login")
        screenshot(
            "TC-REQ-023-044_verification-navigated-to-login",
            "Login page after clicking link from verification page",
        )

        assert "/login" in verification_page.driver.current_url, (
            f"TC-REQ-023-044 FAIL: Expected navigation to /login, "
            f"got: {verification_page.driver.current_url}"
        )
