"""Page object for the Invitation Accept page (REQ-024)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage, DEFAULT_TIMEOUT


class InvitationAcceptPage(BasePage):
    """Interact with the Invitation Accept page (``/invitations/accept?token=...``)."""

    PATH = "/invitations/accept"

    # -- Locators ----------------------------------------------------------
    LOADING_SPINNER = (By.CSS_SELECTOR, ".MuiCircularProgress-root")
    SUCCESS_ICON = (By.CSS_SELECTOR, "[data-testid='CheckCircleIcon'],svg.MuiSvgIcon-colorSuccess")
    ERROR_ICON = (By.CSS_SELECTOR, "[data-testid='ErrorIcon'],svg.MuiSvgIcon-colorError")
    HEADING = (By.CSS_SELECTOR, ".MuiTypography-h6")
    ERROR_DETAIL = (By.CSS_SELECTOR, ".MuiTypography-root[class*='colorText'],.MuiTypography-root.MuiTypography-colorTextSecondary")
    DASHBOARD_BUTTON = (By.CSS_SELECTOR, "button.MuiButton-contained")
    DASHBOARD_BUTTON_OUTLINED = (By.CSS_SELECTOR, "button.MuiButton-outlined")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    # -- Navigation --------------------------------------------------------

    def open_with_token(self, token: str) -> InvitationAcceptPage:
        """Navigate to the invitation accept page with the given token."""
        self.navigate(f"{self.PATH}?token={token}")
        return self

    def open_without_token(self) -> InvitationAcceptPage:
        """Navigate to the invitation accept page without a token."""
        self.navigate(self.PATH)
        return self

    # -- Queries -----------------------------------------------------------

    def is_loading(self) -> bool:
        """Check if the loading spinner is displayed."""
        elements = self.driver.find_elements(*self.LOADING_SPINNER)
        return len(elements) > 0 and elements[0].is_displayed()

    def is_success(self) -> bool:
        """Check if the success state is displayed."""
        elements = self.driver.find_elements(*self.SUCCESS_ICON)
        return len(elements) > 0 and elements[0].is_displayed()

    def is_error(self) -> bool:
        """Check if the error state is displayed."""
        elements = self.driver.find_elements(*self.ERROR_ICON)
        return len(elements) > 0 and elements[0].is_displayed()

    def get_heading_text(self) -> str:
        """Return the heading text (success or error title)."""
        el = self.wait_for_element(self.HEADING)
        return el.text

    def get_error_detail(self) -> str:
        """Return the error detail text."""
        elements = self.driver.find_elements(*self.ERROR_DETAIL)
        if elements and elements[0].is_displayed():
            return elements[0].text
        return ""

    def wait_for_result(self, timeout: int = DEFAULT_TIMEOUT) -> str:
        """Wait until either success or error state is reached.

        Returns 'success' or 'error'.
        """
        from selenium.webdriver.support.ui import WebDriverWait

        def _check_result(driver):
            success = driver.find_elements(*self.SUCCESS_ICON)
            error = driver.find_elements(*self.ERROR_ICON)
            if success and success[0].is_displayed():
                return "success"
            if error and error[0].is_displayed():
                return "error"
            return False

        return WebDriverWait(self.driver, timeout).until(_check_result)

    # -- Interactions ------------------------------------------------------

    def click_dashboard_button(self) -> None:
        """Click the 'Go to Dashboard' button (available on success)."""
        btn = self.wait_for_element_clickable(self.DASHBOARD_BUTTON)
        self.scroll_and_click(btn)

    def click_dashboard_button_on_error(self) -> None:
        """Click the outlined dashboard button (available on error)."""
        btn = self.wait_for_element_clickable(self.DASHBOARD_BUTTON_OUTLINED)
        self.scroll_and_click(btn)
