"""Page object for the Crop Rotation page."""

from __future__ import annotations

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class CropRotationPage(BasePage):
    """Interact with the Crop Rotation page (``/stammdaten/crop-rotation``)."""

    PATH = "/stammdaten/crop-rotation"

    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")
    FAMILY_SELECT = (By.CSS_SELECTOR, ".MuiSelect-select")
    SUCCESSOR_LIST = (By.CSS_SELECTOR, ".MuiList-root .MuiListItem-root")
    ADD_SUCCESSOR_BTN = (By.XPATH, "//button[contains(text(), 'Nachfolger')]")
    EMPTY_STATE = (By.CSS_SELECTOR, "[data-testid='empty-state']")

    # Dialog locators
    DIALOG = (By.CSS_SELECTOR, ".MuiDialog-root")
    DIALOG_TARGET_SELECT = (By.CSS_SELECTOR, ".MuiDialog-root .MuiSelect-select")
    DIALOG_WAIT_YEARS = (By.CSS_SELECTOR, ".MuiDialog-root input[type='number']")
    DIALOG_CREATE_BTN = (By.XPATH, "//div[contains(@class, 'MuiDialog-root')]//button[contains(text(), 'Erstellen')]")
    DIALOG_CANCEL_BTN = (By.XPATH, "//div[contains(@class, 'MuiDialog-root')]//button[contains(text(), 'Abbrechen')]")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> CropRotationPage:
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE_TITLE)
        self.wait_for_loading_complete()
        return self

    def get_title(self) -> str:
        return self.wait_for_element(self.PAGE_TITLE).text

    def select_family(self, family_name: str) -> None:
        select = self.wait_for_element_clickable(self.FAMILY_SELECT)
        self.scroll_and_click(select)
        option = self.wait_for_element_clickable(
            (By.XPATH, f"//li[@role='option' and contains(text(), '{family_name}')]")
        )
        option.click()
        time.sleep(1)  # Wait for successors to load

    def get_family_options(self) -> list[str]:
        select = self.wait_for_element_clickable(self.FAMILY_SELECT)
        self.scroll_and_click(select)
        options = self.driver.find_elements(By.CSS_SELECTOR, "li[role='option']")
        texts = [o.text for o in options]
        from selenium.webdriver.common.keys import Keys
        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        return texts

    def get_successor_count(self) -> int:
        return len(self.driver.find_elements(*self.SUCCESSOR_LIST))

    def get_successor_names(self) -> list[str]:
        items = self.driver.find_elements(*self.SUCCESSOR_LIST)
        return [i.find_element(By.CSS_SELECTOR, ".MuiListItemText-primary").text for i in items]

    def has_empty_state(self) -> bool:
        return len(self.driver.find_elements(*self.EMPTY_STATE)) > 0

    def click_add_successor(self) -> None:
        self.wait_for_element_clickable(self.ADD_SUCCESSOR_BTN).click()
        self.wait_for_element_visible(self.DIALOG)

    def is_dialog_create_button_enabled(self) -> bool:
        btn = self.driver.find_element(*self.DIALOG_CREATE_BTN)
        return btn.is_enabled()

    def select_dialog_target(self, family_name: str) -> None:
        select = self.wait_for_element_clickable(self.DIALOG_TARGET_SELECT)
        self.scroll_and_click(select)
        option = self.wait_for_element_clickable(
            (By.XPATH, f"//li[@role='option' and contains(text(), '{family_name}')]")
        )
        option.click()

    def get_dialog_target_options(self) -> list[str]:
        select = self.wait_for_element_clickable(self.DIALOG_TARGET_SELECT)
        self.scroll_and_click(select)
        options = self.driver.find_elements(By.CSS_SELECTOR, "li[role='option']")
        texts = [o.text for o in options]
        from selenium.webdriver.common.keys import Keys
        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        return texts

    def set_dialog_wait_years(self, years: str) -> None:
        el = self.wait_for_element_clickable(self.DIALOG_WAIT_YEARS)
        el.clear()
        el.send_keys(years)

    def click_dialog_create(self) -> None:
        self.wait_for_element_clickable(self.DIALOG_CREATE_BTN).click()

    def click_dialog_cancel(self) -> None:
        self.wait_for_element_clickable(self.DIALOG_CANCEL_BTN).click()
