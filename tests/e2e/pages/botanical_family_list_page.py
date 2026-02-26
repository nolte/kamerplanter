"""Page object for the Botanical Family list page."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class BotanicalFamilyListPage(BasePage):
    """Interact with the Botanical Families list (``/stammdaten/botanical-families``)."""

    PATH = "/stammdaten/botanical-families"

    # Locators
    PAGE = (By.CSS_SELECTOR, "[data-testid='botanical-family-list-page']")
    CREATE_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-button']")
    TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")
    CREATE_DIALOG = (By.CSS_SELECTOR, "[data-testid='create-dialog']")
    FORM_NAME = (By.CSS_SELECTOR, "[data-testid='form-field-name'] input")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> BotanicalFamilyListPage:
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        return self

    def get_row_count(self) -> int:
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        return len(rows)

    def click_create(self) -> None:
        self.wait_for_element_clickable(self.CREATE_BUTTON).click()
        self.wait_for_element_visible(self.CREATE_DIALOG)

    def fill_create_form(self, name: str) -> None:
        """Fill the name field in the create dialog."""
        name_input = self.wait_for_element_clickable(self.FORM_NAME)
        name_input.clear()
        name_input.send_keys(name)

    def submit_create_form(self) -> None:
        self.wait_for_element_clickable(self.FORM_SUBMIT).click()

    def click_row(self, index: int) -> None:
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        if index < len(rows):
            self.scroll_and_click(rows[index])
