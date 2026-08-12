"""E2E tests for REQ-023 — QR device-pairing dialog (#1118).

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-023.md):
  TC-023-073  ->  TC-023-073  Kopplungsdialog aus dem Sitzungen-Tab oeffnen
  TC-023-074  ->  TC-023-074  QR-Code wird angezeigt und ist nicht leer
  TC-023-075  ->  TC-023-075  Ablauf-Countdown ist sichtbar und zaehlt herunter
  TC-023-076  ->  TC-023-076  Neu angeforderter Code erzeugt einen anderen QR-Code

The dialog (account settings -> Sessions tab -> "Connect mobile device") exists
only in FULL mode; ``requires_auth`` makes the whole module skip in light mode.
Every test self-serves its data: opening the dialog issues a fresh one-time
pairing code for the *currently logged-in* user via
``POST /api/v1/auth/device-pairing`` — no shared fixture row, no seed coupling,
nothing another parallel test reads or mutates. It uses the same demo account
the other authenticated REQ-023 suites (``test_req023_account_settings.py``) do.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import ConnectDeviceDialogPage, LoginPage
from ._auth_helpers import clear_auth_session

pytestmark = pytest.mark.requires_auth

# -- Demo credentials (same account as test_req023_account_settings.py) --------
DEMO_EMAIL = "demo@kamerplanter.example"
DEMO_PASSWORD = "demo-passwort-2024"


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def login_page(browser: WebDriver, base_url: str) -> LoginPage:
    """Return a LoginPage bound to the test browser."""
    return LoginPage(browser, base_url)


@pytest.fixture
def pairing_page(browser: WebDriver, base_url: str) -> ConnectDeviceDialogPage:
    """Return a ConnectDeviceDialogPage bound to the test browser."""
    return ConnectDeviceDialogPage(browser, base_url)


def _ensure_logged_in(login_page: LoginPage) -> None:
    """Log in as the demo user, landing on the dashboard."""
    clear_auth_session(login_page.driver)
    login_page.open()
    login_page.login(DEMO_EMAIL, DEMO_PASSWORD)
    login_page.wait_for_url_contains("/dashboard")


# -- TC-023-073: Open the pairing dialog --------------------------------------


class TestDevicePairingDialogOpen:
    """Opening the QR pairing dialog from the Sessions tab (Spec: TC-023-073)."""

    @pytest.mark.smoke
    @pytest.mark.requires_auth
    def test_open_dialog_from_sessions_tab(
        self,
        login_page: LoginPage,
        pairing_page: ConnectDeviceDialogPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-023-073: "Connect mobile device" opens the pairing dialog.

        Spec: TC-023-073 -- Kopplungsdialog aus dem Sitzungen-Tab oeffnen.
        """
        _ensure_logged_in(login_page)
        pairing_page.open_sessions_tab()
        screenshot(
            "TC-023-073_sessions-tab-loaded",
            "Sessions tab with the Connect-mobile-device button",
        )

        pairing_page.open_dialog()
        screenshot(
            "TC-023-073_dialog-opened",
            "QR device-pairing dialog opened",
        )

        assert pairing_page.is_dialog_visible(), (
            "TC-023-073 FAIL: Expected the device-pairing dialog to be visible "
            "after clicking 'Connect mobile device'"
        )


# -- TC-023-074: QR image appears and is non-empty ----------------------------


class TestDevicePairingQrRendered:
    """The dialog renders a real, non-empty QR (Spec: TC-023-074)."""

    @pytest.mark.smoke
    @pytest.mark.requires_auth
    def test_qr_code_is_rendered_and_non_empty(
        self,
        login_page: LoginPage,
        pairing_page: ConnectDeviceDialogPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-023-074: A non-empty QR ``<svg>`` appears after the code is fetched.

        Spec: TC-023-074 -- QR-Code wird angezeigt und ist nicht leer.

        Falsifiable by construction: the QR must carry a background path AND a
        payload-bearing data path, and the svg must have a non-zero drawn size.
        An empty QR (no svg, or a background-only svg) makes ``qr_path_ds`` time
        out or leaves the data signature empty — either way this test fails loud.
        """
        _ensure_logged_in(login_page)
        pairing_page.open_sessions_tab()
        pairing_page.open_dialog()

        width, height = pairing_page.qr_svg_size()
        screenshot(
            "TC-023-074_qr-rendered",
            "Rendered QR code inside the pairing dialog",
        )

        assert width > 0 and height > 0, (
            f"TC-023-074 FAIL: Expected the QR svg to have a non-zero drawn size, "
            f"got width={width}, height={height}"
        )

        path_ds = pairing_page.qr_path_ds()
        assert len(path_ds) >= 2, (
            f"TC-023-074 FAIL: Expected the QR svg to contain at least a background "
            f"and a data path, got {len(path_ds)} path element(s)"
        )

        data_signature = pairing_page.qr_data_signature()
        assert data_signature, (
            "TC-023-074 FAIL: Expected the QR to carry a non-empty data path "
            "(the payload-bearing path, background square excluded) — an empty QR "
            "means no pairing code was rendered"
        )


# -- TC-023-075: Countdown is visible and ticks -------------------------------


class TestDevicePairingCountdown:
    """The expiry countdown is visible and actually decrements (Spec: TC-023-075)."""

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_countdown_is_visible_and_decrements(
        self,
        login_page: LoginPage,
        pairing_page: ConnectDeviceDialogPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-023-075: The countdown shows a value and ticks down (no fixed sleep).

        Spec: TC-023-075 -- Ablauf-Countdown ist sichtbar und zaehlt herunter.

        The tick is proven with a condition-based wait on the text *changing*,
        not by sleeping and re-reading, so it cannot pass on a frozen label.
        """
        _ensure_logged_in(login_page)
        pairing_page.open_sessions_tab()
        pairing_page.open_dialog()
        pairing_page.wait_for_qr()

        initial_text = pairing_page.countdown_text()
        screenshot(
            "TC-023-075_countdown-visible",
            "Expiry countdown visible in the pairing dialog",
        )

        assert initial_text.strip(), (
            "TC-023-075 FAIL: Expected the countdown element to show non-empty text"
        )
        assert any(ch.isdigit() for ch in initial_text), (
            f"TC-023-075 FAIL: Expected the countdown to contain remaining seconds "
            f"as a number, got: '{initial_text}'"
        )

        ticked_text = pairing_page.wait_for_countdown_tick(initial_text)
        assert ticked_text != initial_text, (
            f"TC-023-075 FAIL: Expected the countdown to decrement from "
            f"'{initial_text}', but it did not change"
        )


# -- TC-023-076: Re-requesting a code yields a different QR --------------------


class TestDevicePairingRefresh:
    """Re-issuing a code renders a genuinely different QR (Spec: TC-023-076)."""

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_new_request_yields_a_different_qr(
        self,
        login_page: LoginPage,
        pairing_page: ConnectDeviceDialogPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-023-076: A freshly requested code replaces the QR with a different one.

        Spec: TC-023-076 -- Neu angeforderter Code erzeugt einen anderen QR-Code.

        The dialog's dedicated ``device-pairing-refresh`` button is reachable
        only from the *expired* state, i.e. after the 60-120 s TTL elapses —
        waiting that long is exactly the fixed-sleep anti-pattern the stability
        rules forbid. So this drives the *same* ``requestCode()`` code path the
        refresh button invokes, via a dialog close+reopen, which re-issues a
        fresh code without any wall-clock wait. The change is made observable by
        comparing the QR's **data** path (the background square is constant for
        two equal-length codes and would mask the difference).
        """
        _ensure_logged_in(login_page)
        pairing_page.open_sessions_tab()

        pairing_page.open_dialog()
        first_signature = pairing_page.qr_data_signature()
        screenshot(
            "TC-023-076_first-qr",
            "First issued QR code",
        )
        assert first_signature, (
            "TC-023-076 FAIL: Expected the first QR to carry a non-empty data path"
        )

        pairing_page.close_dialog()

        pairing_page.open_dialog()
        second_signature = pairing_page.qr_data_signature()
        screenshot(
            "TC-023-076_second-qr",
            "Second (re-issued) QR code",
        )
        assert second_signature, (
            "TC-023-076 FAIL: Expected the re-issued QR to carry a non-empty data path"
        )

        assert second_signature != first_signature, (
            "TC-023-076 FAIL: Expected re-requesting a pairing code to render a "
            "different QR (different data path), but the QR was unchanged — a new "
            "code was not actually issued and rendered"
        )
