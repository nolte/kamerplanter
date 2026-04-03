"""Page object for the Account Settings page (REQ-023)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .base_page import DEFAULT_TIMEOUT, BasePage


class AccountSettingsPage(BasePage):
    """Interact with the Account Settings page (``/settings``)."""

    PATH = "/settings"

    # ── Page-level locators ─────────────────────────────────────────────
    PAGE = (By.CSS_SELECTOR, "[data-testid='account-settings-page']")
    TABS = (By.CSS_SELECTOR, ".MuiTabs-root")
    TAB_BUTTONS = (By.CSS_SELECTOR, ".MuiTab-root")
    ERROR_ALERT = (By.CSS_SELECTOR, ".MuiAlert-standardError")

    # ── Profile tab locators ────────────────────────────────────────────
    DISPLAY_NAME_INPUT = (By.CSS_SELECTOR, "[data-testid='profile-display-name'] input")
    EMAIL_INPUT = (By.CSS_SELECTOR, "[data-testid='profile-email'] input")
    PROFILE_SAVE_BUTTON = (By.CSS_SELECTOR, "[data-testid='profile-save-btn']")
    LOCALE_SELECT = (By.CSS_SELECTOR, "[data-testid='profile-locale']")
    TIMEZONE_INPUT = (By.CSS_SELECTOR, "[data-testid='profile-timezone'] input")

    # ── Security tab locators ───────────────────────────────────────────
    CURRENT_PASSWORD_INPUT = (By.CSS_SELECTOR, "[data-testid='current-password-field'] input")
    NEW_PASSWORD_INPUT = (By.CSS_SELECTOR, "[data-testid='new-password-field'] input")
    CHANGE_PASSWORD_BUTTON = (By.CSS_SELECTOR, "[data-testid='change-password-btn']")

    # ── Experience tab locators ─────────────────────────────────────────
    EXPERIENCE_BEGINNER = (By.CSS_SELECTOR, "[data-testid='experience-toggle-beginner']")
    EXPERIENCE_INTERMEDIATE = (By.CSS_SELECTOR, "[data-testid='experience-toggle-intermediate']")
    EXPERIENCE_EXPERT = (By.CSS_SELECTOR, "[data-testid='experience-toggle-expert']")

    # ── Account tab locators ────────────────────────────────────────────
    DELETE_ACCOUNT_BUTTON = (By.CSS_SELECTOR, "[data-testid='delete-account-btn']")

    # ── Snackbar ────────────────────────────────────────────────────────
    SNACKBAR_SUCCESS = (By.CSS_SELECTOR, "#notistack-snackbar, .SnackbarItem-variantSuccess")
    SNACKBAR_ERROR = (By.CSS_SELECTOR, ".SnackbarItem-variantError")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    # ── Navigation ──────────────────────────────────────────────────────

    def open(self, tab: str | None = None) -> AccountSettingsPage:
        """Navigate to the account settings page and wait for it to load.

        Args:
            tab: Optional tab key to select (profile, security, sessions, etc.)
        """
        path = self.PATH
        if tab:
            path = f"{self.PATH}?tab={tab}"
        self.navigate(path)
        self.wait_for_element(self.PAGE)
        return self

    # ── Tab navigation ──────────────────────────────────────────────────

    def get_tab_labels(self) -> list[str]:
        """Return the text labels of all visible tabs."""
        tabs = self.driver.find_elements(*self.TAB_BUTTONS)
        return [tab.text for tab in tabs if tab.is_displayed()]

    def click_tab(self, label: str) -> None:
        """Click a tab by its label text (case-insensitive)."""
        tabs = self.driver.find_elements(*self.TAB_BUTTONS)
        target = label.lower()
        for tab in tabs:
            if tab.text.strip().lower() == target:
                self.scroll_and_click(tab)
                return
        msg = f"Tab '{label}' not found. Available: {self.get_tab_labels()}"
        raise ValueError(msg)

    def click_tab_by_index(self, index: int) -> None:
        """Click a tab by its zero-based index."""
        tabs = self.driver.find_elements(*self.TAB_BUTTONS)
        if index < len(tabs):
            self.scroll_and_click(tabs[index])

    # ── Profile tab ─────────────────────────────────────────────────────

    def get_display_name(self) -> str:
        """Return the current value of the display-name field."""
        el = self.wait_for_element(self.DISPLAY_NAME_INPUT)
        return el.get_attribute("value") or ""

    def set_display_name(self, name: str) -> None:
        """Clear and type a new display name.

        Uses Ctrl+A instead of .clear() because React controlled inputs
        do not reliably clear with the WebDriver clear() method.
        """
        from selenium.webdriver.common.keys import Keys

        field = self.wait_for_element(self.DISPLAY_NAME_INPUT)
        field.send_keys(Keys.CONTROL, "a")
        field.send_keys(name)

    def get_email(self) -> str:
        """Return the (read-only) email value."""
        el = self.wait_for_element(self.EMAIL_INPUT)
        return el.get_attribute("value") or ""

    def is_email_disabled(self) -> bool:
        """Check if the email field is disabled."""
        el = self.wait_for_element(self.EMAIL_INPUT)
        return el.get_attribute("disabled") == "true"

    def click_profile_save(self) -> None:
        """Click the profile save button."""
        btn = self.wait_for_element_clickable(self.PROFILE_SAVE_BUTTON)
        self.scroll_and_click(btn)

    # ── Security tab ────────────────────────────────────────────────────

    def is_current_password_visible(self) -> bool:
        """Check if the current-password field is visible (only for local accounts)."""
        elements = self.driver.find_elements(*self.CURRENT_PASSWORD_INPUT)
        return len(elements) > 0 and elements[0].is_displayed()

    def enter_current_password(self, password: str) -> None:
        """Type into the current-password field."""
        field = self.wait_for_element(self.CURRENT_PASSWORD_INPUT)
        field.clear()
        field.send_keys(password)

    def enter_new_password(self, password: str) -> None:
        """Type into the new-password field."""
        field = self.wait_for_element(self.NEW_PASSWORD_INPUT)
        field.clear()
        field.send_keys(password)

    def click_change_password(self) -> None:
        """Click the change-password button."""
        btn = self.wait_for_element_clickable(self.CHANGE_PASSWORD_BUTTON)
        self.scroll_and_click(btn)

    def is_change_password_button_enabled(self) -> bool:
        """Check if the change-password button is enabled."""
        btn = self.driver.find_element(*self.CHANGE_PASSWORD_BUTTON)
        return btn.is_enabled()

    def get_linked_providers(self) -> list[str]:
        """Return the list of linked auth provider names."""
        items = self.driver.find_elements(By.CSS_SELECTOR, ".MuiListItemText-primary")
        return [item.text for item in items if item.is_displayed()]

    def get_unlink_buttons(self) -> list[WebElement]:
        """Return all unlink-provider buttons."""
        return self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid^='unlink-provider-']"
        )

    # ── Snackbar helpers ────────────────────────────────────────────────

    def wait_for_success_snackbar(self, timeout: int = DEFAULT_TIMEOUT) -> str:
        """Wait for and return the text of a success snackbar."""
        el = WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(self.SNACKBAR_SUCCESS)
        )
        return el.text

    def wait_for_error_snackbar(self, timeout: int = DEFAULT_TIMEOUT) -> str:
        """Wait for and return the text of an error snackbar."""
        el = WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(self.SNACKBAR_ERROR)
        )
        return el.text
