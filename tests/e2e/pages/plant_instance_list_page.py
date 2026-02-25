"""Page object for the Plant Instance list page."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class PlantInstanceListPage(BasePage):
    """Interact with the Plant Instances list (``/pflanzen/plant-instances``)."""

    PATH = "/pflanzen/plant-instances"

    # Locators
    PAGE = (By.CSS_SELECTOR, "[data-testid='plant-instance-list-page']")
    CREATE_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-button']")
    TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> PlantInstanceListPage:
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        return self

    def get_row_count(self) -> int:
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        return len(rows)

    def click_create(self) -> None:
        self.wait_for_element_clickable(self.CREATE_BUTTON).click()

    def click_row(self, index: int) -> None:
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        if index < len(rows):
            rows[index].click()
