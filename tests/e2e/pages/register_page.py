"""Page object for the Register page (REQ-023)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class RegisterPage(BasePage):
    """Interact with the Registration page (``/register``)."""

    PATH = "/register"

    # ── Locators ────────────────────────────────────────────────────────
    HEADING = (By.CSS_SELECTOR, "h5")
    DISPLAY_NAME_INPUT = (By.CSS_SELECTOR, "input[autocomplete='name']")
    EMAIL_INPUT = (By.CSS_SELECTOR, "input[type='email']")
    PASSWORD_INPUT = (By.CSS_SELECTOR, "input[autocomplete='new-password']")
    # Both password and confirm use autocomplete='new-password'; distinguish by order
    PASSWORD_FIELDS = (By.CSS_SELECTOR, "input[autocomplete='new-password']")
    SUBMIT_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    LOADING_INDICATOR = (By.CSS_SELECTOR, "button[type='submit'] .MuiCircularProgress-root")
    ERROR_ALERT = (By.CSS_SELECTOR, ".MuiAlert-standardError")
    LOGIN_LINK = (By.CSS_SELECTOR, "a[href='/login']")
    PASSWORD_HELPER_TEXT = (By.CSS_SELECTOR, ".MuiFormHelperText-root")
    # Snackbar for success messages (notistack)
    SNACKBAR_SUCCESS = (By.CSS_SELECTOR, ".notistack-SnackbarContainer .SnackbarItem-variantSuccess, #notistack-snackbar")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    # ── Navigation ──────────────────────────────────────────────────────

    def open(self) -> RegisterPage:
        """Navigate to the registration page and wait for it to load."""
        self.navigate(self.PATH)
        self.wait_for_element(self.HEADING)
        return self

    # ── Queries ─────────────────────────────────────────────────────────

    def get_heading_text(self) -> str:
        """Return the heading text."""
        return self.wait_for_element(self.HEADING).text

    def get_error_message(self) -> str:
        """Return the error alert text, or empty string if not present."""
        elements = self.driver.find_elements(*self.ERROR_ALERT)
        if elements and elements[0].is_displayed():
            return elements[0].text
        return ""

    def is_error_alert_visible(self) -> bool:
        """Check if an error alert is visible."""
        elements = self.driver.find_elements(*self.ERROR_ALERT)
        return len(elements) > 0 and elements[0].is_displayed()

    def get_password_helper_text(self) -> str:
        """Return the helper text below the password field."""
        elements = self.driver.find_elements(*self.PASSWORD_HELPER_TEXT)
        for el in elements:
            if el.is_displayed():
                return el.text
        return ""

    def is_loading(self) -> bool:
        """Check if the submit button shows a loading indicator."""
        elements = self.driver.find_elements(*self.LOADING_INDICATOR)
        return len(elements) > 0

    def is_login_link_visible(self) -> bool:
        """Check if the 'Already registered? Login' link is present."""
        elements = self.driver.find_elements(*self.LOGIN_LINK)
        return len(elements) > 0 and elements[0].is_displayed()

    # ── Interactions ────────────────────────────────────────────────────

    def enter_display_name(self, name: str) -> None:
        """Type into the display name field."""
        field = self.wait_for_element(self.DISPLAY_NAME_INPUT)
        field.clear()
        field.send_keys(name)

    def enter_email(self, email: str) -> None:
        """Type into the email field."""
        field = self.wait_for_element(self.EMAIL_INPUT)
        field.clear()
        field.send_keys(email)

    def enter_password(self, password: str) -> None:
        """Type into the password field (first new-password field)."""
        fields = self.driver.find_elements(*self.PASSWORD_FIELDS)
        if fields:
            fields[0].clear()
            fields[0].send_keys(password)

    def enter_confirm_password(self, password: str) -> None:
        """Type into the confirm-password field (second new-password field)."""
        fields = self.driver.find_elements(*self.PASSWORD_FIELDS)
        if len(fields) >= 2:
            fields[1].clear()
            fields[1].send_keys(password)

    def click_register(self) -> None:
        """Click the register/submit button."""
        btn = self.wait_for_element_clickable(self.SUBMIT_BUTTON)
        self.scroll_and_click(btn)

    def click_login_link(self) -> None:
        """Click the 'Already registered? Login' link."""
        link = self.wait_for_element_clickable(self.LOGIN_LINK)
        self.scroll_and_click(link)

    # ── Compound actions ────────────────────────────────────────────────

    def register(
        self,
        display_name: str,
        email: str,
        password: str,
        confirm_password: str | None = None,
    ) -> None:
        """Fill in the registration form and submit."""
        self.enter_display_name(display_name)
        self.enter_email(email)
        self.enter_password(password)
        self.enter_confirm_password(confirm_password if confirm_password is not None else password)
        self.click_register()
