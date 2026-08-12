"""Page object for the "Connect mobile device" QR pairing dialog (REQ-023, #1118).

The dialog lives in the account-settings *Sessions* tab, which exists only in
FULL mode. Opening it issues a short-lived one-time pairing code via
``POST /api/v1/auth/device-pairing`` and renders it as a ``<QRCodeSVG>``; a
per-second countdown drives the code to an expired state whose refresh button
re-requests a fresh code.

``qrcode.react`` renders the QR as an ``<svg>`` holding, in order, an optional
``<title>``, a **constant background** ``<path d="M0,0 h{N}v{N}H0z">`` (whose
shape depends only on the module count, never on the payload), and the
**data** ``<path>`` whose ``d`` encodes the actual code. Any "the QR changed"
assertion therefore has to compare the data path — the background square is
identical for two codes of equal length. That distinction is encapsulated here
in :meth:`qr_data_signature` so no test re-derives it.
"""

from __future__ import annotations

import re

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import DEFAULT_TIMEOUT, BasePage


class ConnectDeviceDialogPage(BasePage):
    """Drive the QR device-pairing dialog from the account-settings Sessions tab."""

    PATH = "/settings"

    # ── Account-settings shell / sessions tab ───────────────────────────────
    PAGE = (By.CSS_SELECTOR, "[data-testid='account-settings-page']")
    CONNECT_BUTTON = (By.CSS_SELECTOR, "[data-testid='connect-device-button']")

    # ── Dialog surface (all P7 hooks) ───────────────────────────────────────
    DIALOG = (By.CSS_SELECTOR, "[data-testid='connect-device-dialog']")
    CLOSE_BUTTON = (By.CSS_SELECTOR, "[data-testid='connect-device-close']")
    LOADING_SKELETON = (By.CSS_SELECTOR, "[data-testid='loading-skeleton']")
    QR = (By.CSS_SELECTOR, "[data-testid='device-pairing-qr']")
    #: The real `<svg>` the QR renders into — the durable "code fetched and
    #: rendered" signal, and the anchor every QR assertion waits on.
    QR_SVG = (By.CSS_SELECTOR, "[data-testid='device-pairing-qr'] svg")
    #: The QR's module `<path>` elements (background square + data path).
    QR_SVG_PATHS = (By.CSS_SELECTOR, "[data-testid='device-pairing-qr'] svg path")
    COUNTDOWN = (By.CSS_SELECTOR, "[data-testid='device-pairing-countdown']")
    EXPIRED = (By.CSS_SELECTOR, "[data-testid='device-pairing-expired']")
    REFRESH_BUTTON = (By.CSS_SELECTOR, "[data-testid='device-pairing-refresh']")
    ERROR = (By.CSS_SELECTOR, "[data-testid='device-pairing-error']")

    #: The constant background square `qrcode.react` draws first; matching it lets
    #: :meth:`qr_data_signature` strip it out so only the payload-bearing path is
    #: compared. `d` reads e.g. ``M0,0 h25v25H0z`` — the module count varies, the
    #: shape does not.
    _BG_PATH_RE = re.compile(r"^M0,0\s*h\d+v\d+H0z$")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    # ── Navigation ──────────────────────────────────────────────────────────

    def open_sessions_tab(self) -> ConnectDeviceDialogPage:
        """Load the account-settings Sessions tab and wait for it to settle.

        `useTabUrl` keys the active tab off the URL hash, so ``#sessions`` deep-
        links the tab. The durable settle signal is the pairing action button,
        which the tab header always renders — not the async session table, which
        may legitimately be empty.
        """
        self.navigate(f"{self.PATH}#sessions")
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        self.wait_for_element_clickable(self.CONNECT_BUTTON)
        return self

    def open_dialog(self) -> ConnectDeviceDialogPage:
        """Click "Connect mobile device" and wait for the dialog to be visible.

        Coordinate-free by construction: the click targets the button element
        that carries ``connect-device-button`` directly, through the suite's
        guarded ``scroll_and_click`` helper, never a container centre.
        """
        button = self.wait_for_element_clickable(self.CONNECT_BUTTON)
        self.scroll_and_click(button)
        self.wait_for_element_visible(self.DIALOG)
        return self

    def close_dialog(self) -> None:
        """Close the dialog and wait for it to leave the DOM/viewport."""
        button = self.wait_for_element_clickable(self.CLOSE_BUTTON)
        self.scroll_and_click(button)
        self.wait_for_element_hidden(self.DIALOG)

    def is_dialog_visible(self) -> bool:
        """Whether the pairing dialog is currently displayed (after waiting)."""
        return self.is_visible_within(self.DIALOG)

    # ── QR code ─────────────────────────────────────────────────────────────

    def wait_for_qr(self, timeout: int = DEFAULT_TIMEOUT):
        """Wait for the real ``<svg>`` to render — the code-fetched signal.

        This is anchored on the QR ``<svg>`` (which mounts only once the issuance
        request resolves and ``pairing`` is non-null), **never** on the
        countdown timer: the code arrives from the backend, so its render is the
        durable event, while the timer is optimistic UI that ticks regardless.
        """
        return self.wait_for_element_visible(self.QR_SVG, timeout)

    def qr_path_ds(self, timeout: int = DEFAULT_TIMEOUT) -> list[str]:
        """Return the ``d`` of every QR ``<path>``, once at least two have rendered.

        A real QR always draws the background square **and** a data path, so the
        ``>= 2`` gate is the "the QR is not empty" condition: if the dialog ever
        rendered an empty frame (no ``<svg>``, or a background-only ``<svg>``),
        this wait exhausts its budget and raises ``TimeoutException`` — a loud
        failure, never a silent empty list.
        """
        self.poll(timeout).until(lambda d: len(d.find_elements(*self.QR_SVG_PATHS)) >= 2)
        return [el.get_attribute("d") or "" for el in self.driver.find_elements(*self.QR_SVG_PATHS)]

    def qr_data_signature(self, timeout: int = DEFAULT_TIMEOUT) -> str:
        """The concatenated ``d`` of the payload-bearing path(s), background excluded.

        This is the only part of the QR that varies with the code, so it is what
        a "the QR changed" comparison must use (the background square is constant
        for two equal-length codes). An empty return means the QR carried no data
        path — which callers assert against as a non-empty precondition.
        """
        return "".join(d for d in self.qr_path_ds(timeout) if d and not self._BG_PATH_RE.match(d))

    def qr_svg_size(self, timeout: int = DEFAULT_TIMEOUT) -> tuple[int, int]:
        """The ``<svg>`` width/height attributes as integers (0 if unset/invalid)."""
        svg = self.wait_for_qr(timeout)

        def _dim(name: str) -> int:
            raw = svg.get_attribute(name) or ""
            try:
                return int(float(raw))
            except ValueError:
                return 0

        return _dim("width"), _dim("height")

    # ── Countdown ───────────────────────────────────────────────────────────

    def countdown_text(self, timeout: int = DEFAULT_TIMEOUT) -> str:
        """The visible countdown text (e.g. ``"Noch 88 Sekunden gültig"``)."""
        return self.wait_for_element_visible(self.COUNTDOWN, timeout).text

    def wait_for_countdown_tick(self, previous_text: str, timeout: int = DEFAULT_TIMEOUT) -> str:
        """Wait until the countdown text changes from *previous_text* and return it.

        A condition-based proof that the timer actually decrements rather than
        rendering a frozen label — never a fixed sleep. The tick is driven by the
        component's 1 s interval, so it lands within the budget; the assertion is
        on the *change*, so it cannot pass on a static string.
        """
        self.poll(timeout).until(
            lambda d: (d.find_element(*self.COUNTDOWN).text or "") not in ("", previous_text)
        )
        return self.driver.find_element(*self.COUNTDOWN).text
