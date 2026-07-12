"""Page object for the Privacy Settings page (REQ-025)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class PrivacySettingsPage(BasePage):
    """Interact with the Privacy Settings page (``/privacy``).

    Covers the 4-tab layout for consents, data export, account erasure and
    processing restriction (REQ-025 §4 Frontend).
    """

    PATH = "/privacy"

    # ── Page markers ──────────────────────────────────────────────────
    PAGE = (By.CSS_SELECTOR, "[data-testid='privacy-settings-page']")
    TABS = (By.CSS_SELECTOR, "[data-testid='privacy-tabs']")
    TAB_CONSENTS = (By.CSS_SELECTOR, "[data-testid='privacy-tab-consents']")
    TAB_EXPORT = (By.CSS_SELECTOR, "[data-testid='privacy-tab-export']")
    TAB_ERASURE = (By.CSS_SELECTOR, "[data-testid='privacy-tab-erasure']")
    TAB_RESTRICT = (By.CSS_SELECTOR, "[data-testid='privacy-tab-restrict']")

    TABS_BY_NAME = {
        "consents": TAB_CONSENTS,
        "export": TAB_EXPORT,
        "erasure": TAB_ERASURE,
        "restrict": TAB_RESTRICT,
    }

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> "PrivacySettingsPage":
        """Navigate to the privacy settings page.

        Does not wait for ``PAGE`` here — the route may not yet be wired
        into ``AppRoutes.tsx``; callers use ``wait_for_element`` themselves
        so they can distinguish an unwired route (skip) from a real failure.
        """
        self.navigate(self.PATH)
        return self

    def is_tab_visible(self, tab_name: str) -> bool:
        """Return True if the named tab (see ``TABS_BY_NAME``) is present and displayed."""
        locator = self.TABS_BY_NAME[tab_name]
        elements = self.driver.find_elements(*locator)
        return len(elements) > 0 and elements[0].is_displayed()
