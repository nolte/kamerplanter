"""Page object for the Botanical Family detail/edit page."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class BotanicalFamilyDetailPage(BasePage):
    """Interact with the Botanical Family detail page (``/stammdaten/botanical-families/:key``)."""

    # Locators
    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")
    DELETE_BUTTON = (By.XPATH, "//button[contains(@class, 'MuiButton-colorError')]")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    CONFIRM_DIALOG = (By.CSS_SELECTOR, "[data-testid='confirm-dialog']")
    CONFIRM_BUTTON = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-confirm']")
    CONFIRM_CANCEL = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-cancel']")

    # Form field locators
    FORM_NAME = (By.CSS_SELECTOR, "[data-testid='form-field-name'] input")
    FORM_COMMON_NAME_DE = (By.CSS_SELECTOR, "[data-testid='form-field-common_name_de'] input")
    FORM_COMMON_NAME_EN = (By.CSS_SELECTOR, "[data-testid='form-field-common_name_en'] input")
    FORM_ORDER = (By.CSS_SELECTOR, "[data-testid='form-field-order'] input")
    FORM_DESCRIPTION = (By.CSS_SELECTOR, "[data-testid='form-field-description'] textarea")
    FORM_PH_MIN = (By.CSS_SELECTOR, "[data-testid='form-field-soil_ph_min'] input")
    FORM_PH_MAX = (By.CSS_SELECTOR, "[data-testid='form-field-soil_ph_max'] input")
    FORM_ROTATION_CAT = (By.CSS_SELECTOR, "[data-testid='form-field-rotation_category'] input")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self, key: str) -> BotanicalFamilyDetailPage:
        self.navigate(f"/stammdaten/botanical-families/{key}")
        self.wait_for_element(self.PAGE_TITLE)
        self.wait_for_loading_complete()
        return self

    def get_title(self) -> str:
        return self.get_text_stable(self.PAGE_TITLE)

    # ── Form reads ─────────────────────────────────────────────────────

    def get_field_value(self, field_name: str) -> str:
        el = self.driver.find_element(
            By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] input"
        )
        return el.get_attribute("value") or ""

    def get_textarea_value(self, field_name: str) -> str:
        el = self.driver.find_element(
            By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] textarea"
        )
        return el.get_attribute("value") or ""

    def get_select_value(self, field_name: str) -> str:
        """Return the displayed text of an MUI Select."""
        el = self.driver.find_element(
            By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] .MuiSelect-select"
        )
        return el.text

    def is_switch_checked(self, field_name: str) -> bool:
        el = self.driver.find_element(
            By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] input[type='checkbox']"
        )
        return el.is_selected()

    # ── Form writes ────────────────────────────────────────────────────

    def set_field(self, field_name: str, value: str) -> None:
        el = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] input")
        )
        el.clear()
        el.send_keys(value)

    def set_textarea(self, field_name: str, value: str) -> None:
        el = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] textarea")
        )
        el.clear()
        el.send_keys(value)

    def add_chip(self, field_name: str, value: str) -> None:
        """Add a chip value to a ChipInput field by typing and pressing Enter."""
        from selenium.webdriver.common.keys import Keys

        el = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] input")
        )
        el.send_keys(value)
        el.send_keys(Keys.ENTER)

    def toggle_switch(self, field_name: str) -> None:
        el = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] input[type='checkbox']")
        )
        self.scroll_and_click(el)

    # ── Actions ────────────────────────────────────────────────────────

    def click_save(self) -> None:
        self.wait_for_element_clickable(self.FORM_SUBMIT).click()

    def click_delete(self) -> None:
        self.wait_for_element_clickable(self.DELETE_BUTTON).click()
        self.wait_for_element_visible(self.CONFIRM_DIALOG)

    def confirm_delete(self) -> None:
        self.wait_for_element_clickable(self.CONFIRM_BUTTON).click()

    def cancel_delete(self) -> None:
        self.wait_for_element_clickable(self.CONFIRM_CANCEL).click()

    def is_confirm_dialog_open(self) -> bool:
        return len(self.driver.find_elements(*self.CONFIRM_DIALOG)) > 0

    def has_delete_button(self) -> bool:
        return len(self.driver.find_elements(*self.DELETE_BUTTON)) > 0
