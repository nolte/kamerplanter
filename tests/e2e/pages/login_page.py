"""Page object for the Login page (REQ-023)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from .base_page import BasePage


class LoginPage(BasePage):
    """Interact with the Login page (``/login``)."""

    PATH = "/login"

    # ── Locators ────────────────────────────────────────────────────────
    HEADING = (By.CSS_SELECTOR, "h5")
    EMAIL_INPUT = (By.CSS_SELECTOR, "input[type='email']")
    PASSWORD_INPUT = (By.CSS_SELECTOR, "input[type='password']")
    REMEMBER_ME_CHECKBOX = (By.CSS_SELECTOR, "input[type='checkbox']")
    REMEMBER_ME_LABEL = (By.CSS_SELECTOR, "label .MuiFormControlLabel-label")
    SUBMIT_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    LOADING_INDICATOR = (By.CSS_SELECTOR, "button[type='submit'] .MuiCircularProgress-root")
    ERROR_ALERT = (By.CSS_SELECTOR, ".MuiAlert-standardError")
    REGISTER_LINK = (By.CSS_SELECTOR, "a[href='/register']")
    FORGOT_PASSWORD_LINK = (By.CSS_SELECTOR, "a[href='/password-reset']")
    DIVIDER = (By.CSS_SELECTOR, ".MuiDivider-root")
    OAUTH_BUTTONS = (By.CSS_SELECTOR, "button.MuiButton-outlined")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    # ── Navigation ──────────────────────────────────────────────────────

    def open(self) -> LoginPage:
        """Navigate to the login page and wait for it to load."""
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
        """Check if an error alert is visible on the page."""
        elements = self.driver.find_elements(*self.ERROR_ALERT)
        return len(elements) > 0 and elements[0].is_displayed()

    def is_loading(self) -> bool:
        """Check if the submit button shows a loading indicator."""
        elements = self.driver.find_elements(*self.LOADING_INDICATOR)
        return len(elements) > 0

    def is_register_link_visible(self) -> bool:
        """Check if the register link is present."""
        elements = self.driver.find_elements(*self.REGISTER_LINK)
        return len(elements) > 0 and elements[0].is_displayed()

    def is_forgot_password_link_visible(self) -> bool:
        """Check if the forgot-password link is present."""
        elements = self.driver.find_elements(*self.FORGOT_PASSWORD_LINK)
        return len(elements) > 0 and elements[0].is_displayed()

    def is_divider_visible(self) -> bool:
        """Check if the SSO divider ('oder') is present."""
        elements = self.driver.find_elements(*self.DIVIDER)
        return len(elements) > 0 and elements[0].is_displayed()

    def get_oauth_buttons(self) -> list[WebElement]:
        """Return all SSO/OAuth provider buttons."""
        return self.driver.find_elements(*self.OAUTH_BUTTONS)

    def is_remember_me_checked(self) -> bool:
        """Check if the remember-me checkbox is checked."""
        cb = self.driver.find_element(*self.REMEMBER_ME_CHECKBOX)
        return cb.is_selected()

    # ── Interactions ────────────────────────────────────────────────────

    def enter_email(self, email: str) -> None:
        """Type into the email field."""
        field = self.wait_for_element(self.EMAIL_INPUT)
        field.clear()
        field.send_keys(email)

    def enter_password(self, password: str) -> None:
        """Type into the password field."""
        field = self.wait_for_element(self.PASSWORD_INPUT)
        field.clear()
        field.send_keys(password)

    def toggle_remember_me(self) -> None:
        """Click the remember-me checkbox."""
        cb = self.wait_for_element_clickable(self.REMEMBER_ME_CHECKBOX)
        self.scroll_and_click(cb)

    def click_login(self) -> None:
        """Click the login/submit button."""
        btn = self.wait_for_element_clickable(self.SUBMIT_BUTTON)
        self.scroll_and_click(btn)

    def click_register_link(self) -> None:
        """Click the 'Register' link."""
        link = self.wait_for_element_clickable(self.REGISTER_LINK)
        self.scroll_and_click(link)

    def click_forgot_password_link(self) -> None:
        """Click the 'Forgot password' link."""
        link = self.wait_for_element_clickable(self.FORGOT_PASSWORD_LINK)
        self.scroll_and_click(link)

    # ── Compound actions ────────────────────────────────────────────────

    def login(self, email: str, password: str, remember_me: bool = False) -> None:
        """Fill in credentials and submit the login form."""
        self.enter_email(email)
        self.enter_password(password)
        if remember_me and not self.is_remember_me_checked():
            self.toggle_remember_me()
        elif not remember_me and self.is_remember_me_checked():
            self.toggle_remember_me()
        self.click_login()
