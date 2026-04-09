"""Page object for the Dashboard page."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class DashboardPage(BasePage):
    """Interact with the Dashboard page (``/dashboard``)."""

    PATH = "/dashboard"

    # Locators
    PAGE = (By.CSS_SELECTOR, "[data-testid='dashboard-page']")
    WELCOME = (By.CSS_SELECTOR, "[data-testid='dashboard-welcome']")
    QUICK_ACTIONS = (By.CSS_SELECTOR, "[data-testid^='quick-action-']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> DashboardPage:
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        return self

    def get_welcome_text(self) -> str:
        return self.wait_for_element_visible(self.WELCOME).text

    def get_quick_action_count(self) -> int:
        self.wait_for_element(self.QUICK_ACTIONS)
        return len(self.find_all_by_testid("quick-action-"))

    def get_quick_actions(self) -> list[str]:
        """Return ``data-testid`` values of all quick-action cards."""
        elements = self.driver.find_elements(*self.QUICK_ACTIONS)
        return [el.get_attribute("data-testid") or "" for el in elements]

    def click_quick_action(self, path: str) -> None:
        """Click the quick-action card whose testid ends with *path*."""
        locator = (By.CSS_SELECTOR, f"[data-testid='quick-action-{path}']")
        self.wait_for_element_clickable(locator).click()
