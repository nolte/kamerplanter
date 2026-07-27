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

    #: Column the row is activated through, should this page ever render a
    #: `DataTable`; see `SiteListPageExt` for the accordion-card layout it
    #: actually renders today.
    ROW_CLICK_COLUMN_ID = "name"

    def click_row(self, index: int) -> None:
        """Open the site at *index* via its inert `name` cell."""
        self.click_data_table_row(index, self.ROW_CLICK_COLUMN_ID, self.TABLE_ROWS, "site row")
