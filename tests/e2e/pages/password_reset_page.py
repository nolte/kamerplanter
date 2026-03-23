"""Page objects for the Password Reset pages (REQ-023)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class PasswordResetRequestPage(BasePage):
    """Interact with the Password-Reset-Request page (``/password-reset``)."""

    PATH = "/password-reset"

    # ── Locators ────────────────────────────────────────────────────────
    HEADING = (By.CSS_SELECTOR, "h5")
    EMAIL_INPUT = (By.CSS_SELECTOR, "input[type='email']")
    SUBMIT_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    SUCCESS_ALERT = (By.CSS_SELECTOR, ".MuiAlert-standardSuccess")
    BACK_TO_LOGIN_LINK = (By.CSS_SELECTOR, "a[href='/login']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    # ── Navigation ──────────────────────────────────────────────────────

    def open(self) -> PasswordResetRequestPage:
        """Navigate to the password-reset-request page and wait for it to load."""
        self.navigate(self.PATH)
        self.wait_for_element(self.HEADING)
        return self

    # ── Queries ─────────────────────────────────────────────────────────

    def get_heading_text(self) -> str:
        """Return the heading text."""
        return self.wait_for_element(self.HEADING).text

    def is_success_alert_visible(self) -> bool:
        """Check if the success alert is visible."""
        elements = self.driver.find_elements(*self.SUCCESS_ALERT)
        return len(elements) > 0 and elements[0].is_displayed()

    def get_success_alert_text(self) -> str:
        """Return the success alert text."""
        el = self.wait_for_element_visible(self.SUCCESS_ALERT)
        return el.text

    def is_email_form_visible(self) -> bool:
        """Check if the email input form is still visible (not replaced by success state)."""
        elements = self.driver.find_elements(*self.EMAIL_INPUT)
        return len(elements) > 0 and elements[0].is_displayed()

    def is_back_to_login_visible(self) -> bool:
        """Check if the 'back to login' link is visible."""
        elements = self.driver.find_elements(*self.BACK_TO_LOGIN_LINK)
        return len(elements) > 0 and elements[0].is_displayed()

    # ── Interactions ────────────────────────────────────────────────────

    def enter_email(self, email: str) -> None:
        """Type into the email field."""
        field = self.wait_for_element(self.EMAIL_INPUT)
        field.clear()
        field.send_keys(email)

    def click_submit(self) -> None:
        """Click the submit button."""
        btn = self.wait_for_element_clickable(self.SUBMIT_BUTTON)
        self.scroll_and_click(btn)

    def click_back_to_login(self) -> None:
        """Click the 'back to login' link."""
        link = self.wait_for_element_clickable(self.BACK_TO_LOGIN_LINK)
        self.scroll_and_click(link)

    # ── Compound actions ────────────────────────────────────────────────

    def request_reset(self, email: str) -> None:
        """Fill in the email and submit the reset request."""
        self.enter_email(email)
        self.click_submit()


class PasswordResetConfirmPage(BasePage):
    """Interact with the Password-Reset-Confirm page (``/password-reset/:token``)."""

    # ── Locators ────────────────────────────────────────────────────────
    HEADING = (By.CSS_SELECTOR, "h5")
    PASSWORD_INPUT = (By.CSS_SELECTOR, "input[autocomplete='new-password']")
    PASSWORD_FIELDS = (By.CSS_SELECTOR, "input[autocomplete='new-password']")
    SUBMIT_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    ERROR_ALERT = (By.CSS_SELECTOR, ".MuiAlert-standardError")
    PASSWORD_HELPER_TEXT = (By.CSS_SELECTOR, ".MuiFormHelperText-root")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    # ── Navigation ──────────────────────────────────────────────────────

    def open(self, token: str) -> PasswordResetConfirmPage:
        """Navigate to the password-reset-confirm page with a token."""
        self.navigate(f"/password-reset/{token}")
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

    # ── Interactions ────────────────────────────────────────────────────

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

    def click_submit(self) -> None:
        """Click the 'save password' button."""
        btn = self.wait_for_element_clickable(self.SUBMIT_BUTTON)
        self.scroll_and_click(btn)

    # ── Compound actions ────────────────────────────────────────────────

    def reset_password(self, password: str, confirm_password: str | None = None) -> None:
        """Fill in the new password and submit."""
        self.enter_password(password)
        self.enter_confirm_password(confirm_password if confirm_password is not None else password)
        self.click_submit()
