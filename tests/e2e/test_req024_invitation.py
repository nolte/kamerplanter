"""E2E tests for REQ-024 -- Invitation Workflow.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-024.md):
  TC-REQ-024-030  ->  TC-024-025  Einladung annehmen -- InvitationAcceptPage rendert
  TC-REQ-024-031  ->  TC-024-025  Gueltige Einladung zeigt Erfolgs-Icon und Dashboard-Button
  TC-REQ-024-032  ->  TC-024-026  Abgelaufener Token zeigt Fehler-Icon und Fehlermeldung
  TC-REQ-024-033  ->  TC-024-026  Einladung ohne Token zeigt Fehlermeldung
  TC-REQ-024-034  ->  TC-024-025  Nach erfolgreicher Annahme navigiert Dashboard-Button weiter
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import InvitationAcceptPage, LoginPage
from ._auth_helpers import clear_auth_session

pytestmark = pytest.mark.requires_auth


# -- Demo credentials ---------------------------------------------------------
DEMO_EMAIL = "demo@kamerplanter.example"
DEMO_PASSWORD = "demo-passwort-2024"


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def login_page(browser: WebDriver, base_url: str) -> LoginPage:
    """Return a LoginPage bound to the test browser."""
    return LoginPage(browser, base_url)


@pytest.fixture
def invitation_page(browser: WebDriver, base_url: str) -> InvitationAcceptPage:
    """Return an InvitationAcceptPage bound to the test browser."""
    return InvitationAcceptPage(browser, base_url)


def _ensure_logged_in(login_page: LoginPage) -> None:
    """Log in as demo user if not already authenticated."""
    clear_auth_session(login_page.driver)
    login_page.open()
    login_page.login(DEMO_EMAIL, DEMO_PASSWORD)
    login_page.wait_for_url_contains("/dashboard")


# -- TC-024-025: InvitationAcceptPage renders ----------------------------------


class TestInvitationPageLoad:
    """InvitationAcceptPage renders with heading (Spec: TC-024-025, TC-024-026)."""

    @pytest.mark.smoke
    @pytest.mark.requires_auth
    def test_invitation_page_renders_with_token(
        self,
        login_page: LoginPage,
        invitation_page: InvitationAcceptPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-024-025: InvitationAcceptPage loads and shows heading when opened with a token.

        Spec: TC-024-025 -- Einladung annehmen -- InvitationAcceptPage rendert.
        """
        _ensure_logged_in(login_page)
        invitation_page.open_with_token("test-token-e2e")

        result = invitation_page.wait_for_result()
        screenshot(
            "TC-REQ-024-030_invitation-page-loaded",
            "InvitationAcceptPage after load with token",
        )

        heading = invitation_page.get_heading_text()
        expected = InvitationAcceptPage.RESULT_HEADINGS[result]
        assert heading in expected, (
            f"TC-REQ-024-030 FAIL: Expected the invitation result card to show one "
            f"of {expected} in its '{result}' state, got: '{heading}'"
        )

    @pytest.mark.smoke
    @pytest.mark.requires_auth
    def test_invitation_page_renders_without_token(
        self,
        login_page: LoginPage,
        invitation_page: InvitationAcceptPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-024-026: InvitationAcceptPage without token shows error state.

        Spec: TC-024-026 -- Einladung ohne Token zeigt Fehlermeldung.
        """
        _ensure_logged_in(login_page)
        invitation_page.open_without_token()

        result = invitation_page.wait_for_result()
        screenshot(
            "TC-REQ-024-033_invitation-no-token",
            "InvitationAcceptPage opened without token",
        )

        assert result == "error", (
            f"TC-REQ-024-033 FAIL: Expected error state when no token provided, got: '{result}'"
        )
        assert invitation_page.is_error(), (
            "TC-REQ-024-033 FAIL: Expected error icon to be visible when no token is provided"
        )


# -- TC-024-026: Invalid / expired token --------------------------------------


class TestInvitationInvalidToken:
    """Invalid or expired invitation tokens show error (Spec: TC-024-026, TC-024-027)."""

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_invalid_token_shows_error(
        self,
        login_page: LoginPage,
        invitation_page: InvitationAcceptPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-024-026: Expired or invalid token shows error icon and message.

        Spec: TC-024-026 -- Abgelaufene Einladung annehmen -- Fehlermeldung.
        """
        _ensure_logged_in(login_page)
        invitation_page.open_with_token("ungueltig-abgelaufen-token-999")

        screenshot(
            "TC-REQ-024-032_invitation-before-result",
            "InvitationAcceptPage loading with invalid token",
        )

        result = invitation_page.wait_for_result()
        screenshot(
            "TC-REQ-024-032_invitation-invalid-token-error",
            "InvitationAcceptPage error state for invalid token",
        )

        assert result == "error", (
            f"TC-REQ-024-032 FAIL: Expected error state for invalid token, got: '{result}'"
        )
        assert invitation_page.is_error(), (
            "TC-REQ-024-032 FAIL: Expected error icon to be displayed for invalid token"
        )

        heading = invitation_page.get_heading_text()
        expected = InvitationAcceptPage.RESULT_HEADINGS["error"]
        assert heading in expected, (
            f"TC-REQ-024-032 FAIL: Expected the error heading to be one of "
            f"{expected} for an invalid token, got: '{heading}'"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_invalid_token_shows_error_detail(
        self,
        login_page: LoginPage,
        invitation_page: InvitationAcceptPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-024-026: Error detail text is displayed for invalid token.

        Spec: TC-024-026 -- Fehlermeldung mit Detail-Text.
        """
        _ensure_logged_in(login_page)
        invitation_page.open_with_token("expired-token-456")

        result = invitation_page.wait_for_result()
        screenshot(
            "TC-REQ-024-032b_invitation-error-detail",
            "InvitationAcceptPage error detail for expired token",
        )

        assert result == "error", f"TC-REQ-024-032b FAIL: Expected error state, got: '{result}'"

        assert invitation_page.is_error(), "TC-REQ-024-032b FAIL: Expected error icon to be visible"
        # The detail text used to be treated as optional, which made this case a
        # duplicate of TC-REQ-024-032 -- both only proved "an error happened",
        # while the name and `Spec:` line promise the *detail* is shown. It was
        # optional because the locator could never match: `ERROR_DETAIL` used
        # MUI v4 class naming that MUI 9 does not emit, so the call returned ''
        # unconditionally (#778 A11). With the product hook in place the
        # assertion the case was always named for can finally be made.
        error_detail = invitation_page.get_error_detail()
        assert error_detail.strip(), (
            "TC-REQ-024-032b FAIL: Expected the error card to render a detail text explaining "
            "why the invitation failed, but it was empty"
        )


# -- TC-024-025: Successful acceptance and navigation --------------------------


class TestInvitationAcceptNavigation:
    """After accepting invitation, dashboard button navigates (Spec: TC-024-025)."""

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_error_state_has_dashboard_button(
        self,
        login_page: LoginPage,
        invitation_page: InvitationAcceptPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-024-025: Error state shows outlined dashboard button for navigation.

        Spec: TC-024-025 -- Dashboard-Button auf Fehlerseite.
        Note: Testing with an invalid token since we cannot create valid tokens
        in E2E without backend seeding. The outlined dashboard button on the
        error page is verified instead.
        """
        _ensure_logged_in(login_page)
        invitation_page.open_with_token("invalid-token-for-nav-test")

        result = invitation_page.wait_for_result()
        screenshot(
            "TC-REQ-024-034_invitation-error-with-button",
            "InvitationAcceptPage error state with dashboard button",
        )

        assert result == "error", f"TC-REQ-024-034 FAIL: Expected error state, got: '{result}'"

        invitation_page.click_dashboard_button_on_error()
        invitation_page.wait_for_url_contains("/dashboard")
        screenshot(
            "TC-REQ-024-034_invitation-navigated-dashboard",
            "Dashboard after clicking button on invitation error page",
        )

        assert "/dashboard" in invitation_page.driver.current_url, (
            f"TC-REQ-024-034 FAIL: Expected navigation to /dashboard, "
            f"got: {invitation_page.driver.current_url}"
        )
