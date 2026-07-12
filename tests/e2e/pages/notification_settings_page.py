"""Page object for the Notification Settings tab (REQ-030).

The notification settings live as a tab inside the AccountSettingsPage at
``/settings?tab=notifications``.  This page object encapsulates the channel
toggles, channel-specific configuration fields and the save button rendered
by ``NotificationSettingsTab.tsx``.

REQ-030 ships a fixed set of four channels (home_assistant, email, pwa,
apprise).  The user does not "create" channels — they enable/disable them
and fill in channel-specific configuration.  This page object therefore
exposes ``toggle_channel(key)`` and ``set_email_address(...)`` helpers
rather than a generic CRUD-list interface.
"""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .base_page import DEFAULT_TIMEOUT, BasePage


class NotificationSettingsPage(BasePage):
    """Interact with the Notification Settings tab (``/settings?tab=notifications``).

    Locators reference the data-testid attributes defined in
    ``src/frontend/src/pages/auth/NotificationSettingsTab.tsx``.
    """

    PATH = "/settings?tab=notifications"

    # ── Container / structural ──────────────────────────────────────────
    PAGE = (By.CSS_SELECTOR, "[data-testid='account-settings-page']")
    SAVE_BUTTON = (By.CSS_SELECTOR, "[data-testid='notification-settings-save']")
    TAB_BUTTONS = (By.CSS_SELECTOR, ".MuiTab-root")

    # ── Channel toggles ─────────────────────────────────────────────────
    CHANNEL_KEYS: tuple[str, ...] = ("home_assistant", "email", "pwa", "apprise")

    @staticmethod
    def _channel_toggle_locator(channel_key: str) -> tuple[str, str]:
        """Return the locator for a channel's enable-switch."""
        return (
            By.CSS_SELECTOR,
            f"[data-testid='channel-toggle-{channel_key}'] input",
        )

    @staticmethod
    def _channel_toggle_root_locator(channel_key: str) -> tuple[str, str]:
        """Return the locator for the channel toggle's root MUI element."""
        return (
            By.CSS_SELECTOR,
            f"[data-testid='channel-toggle-{channel_key}']",
        )

    # ── Channel-specific configuration fields ──────────────────────────
    EMAIL_ADDRESS_INPUT = (
        By.CSS_SELECTOR,
        "[data-testid='email-address'] input",
    )
    HA_PERSISTENT_TOGGLE = (
        By.CSS_SELECTOR,
        "[data-testid='ha-persistent-notification-toggle'] input",
    )
    HA_MOBILE_PUSH_TOGGLE = (
        By.CSS_SELECTOR,
        "[data-testid='ha-mobile-push-toggle'] input",
    )
    APPRISE_URLS_TEXTAREA = (
        By.CSS_SELECTOR,
        "[data-testid='apprise-urls'] textarea",
    )

    # ── Quiet hours / batching / escalation ────────────────────────────
    QUIET_HOURS_TOGGLE = (
        By.CSS_SELECTOR,
        "[data-testid='quiet-hours-toggle'] input",
    )
    QUIET_HOURS_START = (
        By.CSS_SELECTOR,
        "[data-testid='quiet-hours-start'] input",
    )
    QUIET_HOURS_END = (By.CSS_SELECTOR, "[data-testid='quiet-hours-end'] input")
    BATCHING_TOGGLE = (By.CSS_SELECTOR, "[data-testid='batching-toggle'] input")
    ESCALATION_TOGGLE = (
        By.CSS_SELECTOR,
        "[data-testid='escalation-toggle'] input",
    )

    # ── Snackbars ───────────────────────────────────────────────────────
    SNACKBAR_SUCCESS = (
        By.CSS_SELECTOR,
        "#notistack-snackbar, .SnackbarItem-variantSuccess",
    )
    SNACKBAR_ERROR = (By.CSS_SELECTOR, ".SnackbarItem-variantError")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    # ── Navigation ──────────────────────────────────────────────────────

    def open(self) -> NotificationSettingsPage:
        """Navigate to the notification settings tab and wait for it to load."""
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE)
        # The tab content lazy-loads — wait for the save button as anchor.
        self.wait_for_element(self.SAVE_BUTTON)
        return self

    def is_save_button_visible(self) -> bool:
        """Return True if the notification-settings save button is present and displayed."""
        elements = self.driver.find_elements(*self.SAVE_BUTTON)
        return len(elements) > 0 and elements[0].is_displayed()

    def get_tab_labels(self) -> list[str]:
        """Return the visible tab labels in the AccountSettings tab strip."""
        tabs = self.driver.find_elements(*self.TAB_BUTTONS)
        return [tab.text for tab in tabs if tab.is_displayed()]

    # ── Channel queries ─────────────────────────────────────────────────

    def get_visible_channel_keys(self) -> list[str]:
        """Return the keys of all channel toggles currently rendered."""
        rendered: list[str] = []
        for key in self.CHANNEL_KEYS:
            elements = self.driver.find_elements(
                *self._channel_toggle_root_locator(key)
            )
            if elements:
                rendered.append(key)
        return rendered

    def is_channel_enabled(self, channel_key: str) -> bool:
        """Return True if the channel's switch is currently checked."""
        toggle = self.wait_for_element(self._channel_toggle_locator(channel_key))
        return toggle.is_selected()

    # ── Channel actions ─────────────────────────────────────────────────

    def toggle_channel(self, channel_key: str) -> None:
        """Click the enable-switch of a channel.

        We click the root MUI Switch element rather than the hidden ``<input>``
        so that the click reaches the visible thumb without scroll/overlay
        issues.
        """
        root = self.wait_for_element_clickable(
            self._channel_toggle_root_locator(channel_key)
        )
        self.scroll_and_click(root)

    def set_channel_enabled(self, channel_key: str, enabled: bool) -> None:
        """Ensure the channel's switch matches *enabled*; toggle if it does not."""
        if self.is_channel_enabled(channel_key) != enabled:
            self.toggle_channel(channel_key)

    def set_email_address(self, address: str) -> None:
        """Fill in the email-channel address field.

        Requires the email channel to be enabled (the field is conditionally
        rendered).
        """
        field = self.wait_for_element_visible(self.EMAIL_ADDRESS_INPUT)
        self.clear_and_fill(field, address)

    def get_email_address(self) -> str:
        """Return the current value of the email-channel address field."""
        elements = self.driver.find_elements(*self.EMAIL_ADDRESS_INPUT)
        if not elements:
            return ""
        return elements[0].get_attribute("value") or ""

    # ── Save ────────────────────────────────────────────────────────────

    def save(self) -> None:
        """Click the save button at the bottom of the tab."""
        btn = self.wait_for_element_clickable(self.SAVE_BUTTON)
        self.scroll_and_click(btn)

    def wait_for_success_snackbar(self, timeout: int = DEFAULT_TIMEOUT) -> str:
        """Wait for and return the text of a success snackbar after save."""
        el = WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(self.SNACKBAR_SUCCESS)
        )
        return el.text
