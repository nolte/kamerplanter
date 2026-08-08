"""Page object for the Email Verification page (REQ-023)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import DEFAULT_TIMEOUT, BasePage


class EmailVerificationPage(BasePage):
    """Interact with the Email Verification page (``/verify-email/:token``)."""

    # ── Locators ────────────────────────────────────────────────────────
    HEADING = (By.CSS_SELECTOR, "h5")
    LOADING_INDICATOR = (By.CSS_SELECTOR, ".MuiCircularProgress-root")
    SUCCESS_ALERT = (By.CSS_SELECTOR, ".MuiAlert-colorSuccess")
    ERROR_ALERT = (By.CSS_SELECTOR, ".MuiAlert-colorError")
    LOGIN_BUTTON = (By.CSS_SELECTOR, "a[href='/login']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    # ── Navigation ──────────────────────────────────────────────────────

    def open(self, token: str) -> EmailVerificationPage:
        """Navigate to the email verification page with a token."""
        self.navigate(f"/verify-email/{token}")
        self.wait_for_element(self.HEADING)
        return self

    # ── Queries ─────────────────────────────────────────────────────────

    def get_heading_text(self) -> str:
        """Return the heading text."""
        return self.wait_for_element(self.HEADING).text

    def wait_for_result(self, timeout: int = DEFAULT_TIMEOUT) -> str:
        """Wait until the token-verification request has settled, success or error.

        Returns ``'success'`` or ``'error'``.

        `EmailVerificationPage.tsx` seeds ``status`` at ``'loading'`` and only
        flips it to ``'success'``/``'error'`` once its own ``verifyEmail(token)``
        call resolves; `HEADING` renders unconditionally and in the very same
        commit as the loading spinner, so ``open()``'s wait for it says nothing
        about whether that round-trip has finished. Several call sites read
        :meth:`is_error_alert_visible` as their **primary** assertion right
        after ``open()`` with a comment claiming to "wait for processing to
        complete" that was never backed by an actual wait -- this is that wait
        (mirrors ``InvitationAcceptPage.wait_for_result``, #946).
        """

        def _check_result(driver):
            error = driver.find_elements(*self.ERROR_ALERT)
            success = driver.find_elements(*self.SUCCESS_ALERT)
            if error and error[0].is_displayed():
                return "error"
            if success and success[0].is_displayed():
                return "success"
            return False

        return self.poll(timeout).until(_check_result)

    def is_loading(self) -> bool:
        """Check if the loading spinner is visible."""
        elements = self.driver.find_elements(*self.LOADING_INDICATOR)
        return len(elements) > 0 and elements[0].is_displayed()

    def is_success_alert_visible(self) -> bool:
        """Check if the success alert is visible."""
        elements = self.driver.find_elements(*self.SUCCESS_ALERT)
        return len(elements) > 0 and elements[0].is_displayed()

    def get_success_alert_text(self) -> str:
        """Return the success alert text."""
        el = self.wait_for_element_visible(self.SUCCESS_ALERT)
        return el.text

    def is_error_alert_visible(self) -> bool:
        """Check if the error alert is visible."""
        elements = self.driver.find_elements(*self.ERROR_ALERT)
        return len(elements) > 0 and elements[0].is_displayed()

    def get_error_alert_text(self) -> str:
        """Return the error alert text."""
        el = self.wait_for_element_visible(self.ERROR_ALERT)
        return el.text

    def is_login_button_visible(self) -> bool:
        """Check if the login button/link is visible."""
        elements = self.driver.find_elements(*self.LOGIN_BUTTON)
        return len(elements) > 0 and elements[0].is_displayed()

    # ── Interactions ────────────────────────────────────────────────────

    def click_login(self) -> None:
        """Click the login button to go back to the login page."""
        btn = self.wait_for_element_clickable(self.LOGIN_BUTTON)
        self.scroll_and_click(btn)
