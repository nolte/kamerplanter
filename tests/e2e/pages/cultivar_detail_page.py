"""Page object for the Cultivar detail page."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class CultivarDetailPage(BasePage):
    """Interact with the Cultivar detail page."""

    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")
    DELETE_BUTTON = (By.XPATH, "//button[contains(@class, 'MuiButton-colorError')]")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    CONFIRM_DIALOG = (By.CSS_SELECTOR, "[data-testid='confirm-dialog']")
    CONFIRM_BUTTON = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-confirm']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self, species_key: str, cultivar_key: str) -> CultivarDetailPage:
        self.navigate(f"/stammdaten/species/{species_key}/cultivars/{cultivar_key}")
        self.wait_for_element(self.PAGE_TITLE)
        self.wait_for_loading_complete()
        return self

    def get_title(self) -> str:
        return self.wait_for_element(self.PAGE_TITLE).text

    def get_field_value(self, field_name: str) -> str:
        el = self.driver.find_element(
            By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] input"
        )
        return el.get_attribute("value") or ""

    def set_field(self, field_name: str, value: str) -> None:
        el = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] input")
        )
        el.clear()
        el.send_keys(value)

    def add_chip(self, field_name: str, value: str) -> None:
        el = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] input")
        )
        el.send_keys(value)
        el.send_keys(Keys.ENTER)

    def click_save(self) -> None:
        self.wait_for_element_clickable(self.FORM_SUBMIT).click()

    def click_delete(self) -> None:
        self.wait_for_element_clickable(self.DELETE_BUTTON).click()
        self.wait_for_element_visible(self.CONFIRM_DIALOG)

    def confirm_delete(self) -> None:
        self.wait_for_element_clickable(self.CONFIRM_BUTTON).click()

    def has_delete_button(self) -> bool:
        return len(self.driver.find_elements(*self.DELETE_BUTTON)) > 0
