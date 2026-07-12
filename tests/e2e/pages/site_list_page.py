"""Page object for the Site list page."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class SiteListPage(BasePage):
    """Interact with the Sites list (``/standorte/sites``)."""

    PATH = "/standorte/sites"

    # Locators
    PAGE = (By.CSS_SELECTOR, "[data-testid='site-list-page']")
    CREATE_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-button']")
    TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> SiteListPage:
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        return self

    def get_row_count(self) -> int:
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        return len(rows)

    def get_row_texts(self) -> list[str]:
        """Return the text content of every row currently rendered in the table."""
        return [row.text for row in self.driver.find_elements(*self.TABLE_ROWS)]

    def find_row_index_by_text(self, text: str) -> int:
        """Return the index of the first row whose text contains *text*, or -1."""
        for idx, row_text in enumerate(self.get_row_texts()):
            if text in row_text:
                return idx
        return -1

    def click_create(self) -> None:
        self.wait_for_element_clickable(self.CREATE_BUTTON).click()

    def click_row(self, index: int) -> None:
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        if index < len(rows):
            rows[index].click()
