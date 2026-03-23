"""Page object for the Tenant Create page (REQ-024)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage, DEFAULT_TIMEOUT


class TenantCreatePage(BasePage):
    """Interact with the Tenant Create page (``/tenants/create``)."""

    PATH = "/tenants/create"

    # -- Locators ----------------------------------------------------------
    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")
    INTRO_TEXT = (By.CSS_SELECTOR, ".MuiTypography-body2.MuiTypography-colorTextSecondary")
    NAME_INPUT = (By.CSS_SELECTOR, "input[required]")
    DESCRIPTION_INPUT = (By.CSS_SELECTOR, "textarea")
    SUBMIT_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    ERROR_TEXT = (By.CSS_SELECTOR, ".MuiTypography-colorError")
    SNACKBAR = (By.CSS_SELECTOR, "#notistack-snackbar")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    # -- Navigation --------------------------------------------------------

    def open(self) -> TenantCreatePage:
        """Navigate to the tenant creation page and wait for it to load."""
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE_TITLE)
        return self

    # -- Queries -----------------------------------------------------------

    def get_page_title_text(self) -> str:
        """Return the page title text."""
        return self.wait_for_element(self.PAGE_TITLE).text

    def get_intro_text(self) -> str:
        """Return the intro/description text below the title."""
        el = self.wait_for_element(self.INTRO_TEXT)
        return el.text

    def get_error_text(self) -> str:
        """Return the inline error text, or empty string if not present."""
        elements = self.driver.find_elements(*self.ERROR_TEXT)
        if elements and elements[0].is_displayed():
            return elements[0].text
        return ""

    def is_error_displayed(self) -> bool:
        """Check if an inline error message is visible."""
        elements = self.driver.find_elements(*self.ERROR_TEXT)
        return len(elements) > 0 and elements[0].is_displayed()

    def is_submit_enabled(self) -> bool:
        """Check whether the submit button is enabled."""
        btn = self.driver.find_element(*self.SUBMIT_BUTTON)
        return btn.is_enabled()

    def get_name_value(self) -> str:
        """Return the current value of the name input."""
        return self.driver.find_element(*self.NAME_INPUT).get_attribute("value") or ""

    def get_snackbar_text(self, timeout: int = DEFAULT_TIMEOUT) -> str:
        """Wait for a notistack snackbar and return its text."""
        el = self.wait_for_element_visible(self.SNACKBAR, timeout=timeout)
        return el.text

    def has_snackbar(self) -> bool:
        """Check if a snackbar is currently visible."""
        elements = self.driver.find_elements(*self.SNACKBAR)
        return len(elements) > 0 and elements[0].is_displayed()

    # -- Interactions ------------------------------------------------------

    def enter_name(self, name: str) -> None:
        """Type into the name field."""
        field = self.wait_for_element(self.NAME_INPUT)
        field.clear()
        field.send_keys(name)

    def enter_description(self, description: str) -> None:
        """Type into the description field."""
        field = self.wait_for_element(self.DESCRIPTION_INPUT)
        field.clear()
        field.send_keys(description)

    def click_submit(self) -> None:
        """Click the submit/create button."""
        btn = self.wait_for_element_clickable(self.SUBMIT_BUTTON)
        self.scroll_and_click(btn)

    # -- Compound actions --------------------------------------------------

    def create_tenant(self, name: str, description: str = "") -> None:
        """Fill in the form and submit to create a tenant."""
        self.enter_name(name)
        if description:
            self.enter_description(description)
        self.click_submit()
