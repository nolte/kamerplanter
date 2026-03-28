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
    FAMILY_SELECT = (By.CSS_SELECTOR, "[data-testid='from-family-select'] .MuiSelect-select")
    SUCCESSOR_LIST = (By.CSS_SELECTOR, ".MuiList-root .MuiListItem-root")
    ADD_SUCCESSOR_BTN = (By.CSS_SELECTOR, "[data-testid='add-successor-button']")
    EMPTY_STATE = (By.CSS_SELECTOR, "[data-testid='empty-state']")

    # Dialog locators
    DIALOG = (By.CSS_SELECTOR, "div[role='dialog']")
    DIALOG_TARGET_SELECT = (By.CSS_SELECTOR, "[data-testid='to-family-select'] .MuiSelect-select")
    DIALOG_WAIT_YEARS = (By.CSS_SELECTOR, "[data-testid='wait-years-input'] input")
    DIALOG_CREATE_BTN = (By.XPATH, "//div[@role='dialog']//button[contains(text(), 'Erstellen')]")
    DIALOG_CANCEL_BTN = (By.XPATH, "//div[@role='dialog']//button[contains(text(), 'Abbrechen')]")

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
        from selenium.webdriver.support.ui import WebDriverWait
        self.close_mui_dropdown()
        select = self.wait_for_element_clickable(self.FAMILY_SELECT)
        self.scroll_and_click(select)
        option = self.wait_for_element_clickable(
            (By.XPATH, f"//li[@role='option' and contains(text(), '{family_name}')]")
        )
        self.scroll_and_click(option)
        # Wait for options to be removed from DOM (natural close after selection)
        WebDriverWait(self.driver, 5).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, "li[role='option']")) == 0
        )
        time.sleep(1)  # Wait for successors to load

    def get_family_options(self) -> list[str]:
        self.close_mui_dropdown()
        select = self.wait_for_element_clickable(self.FAMILY_SELECT)
        self.scroll_and_click(select)
        self.wait_for_element_visible((By.CSS_SELECTOR, "li[role='option']"), timeout=10)
        options = self.driver.find_elements(By.CSS_SELECTOR, "li[role='option']")
        texts = [o.text for o in options if o.text]
        self.close_mui_dropdown()
        return texts

    def get_successor_count(self) -> int:
        return len(self.driver.find_elements(*self.SUCCESSOR_LIST))

    def get_successor_names(self) -> list[str]:
        items = self.driver.find_elements(*self.SUCCESSOR_LIST)
        return [i.find_element(By.CSS_SELECTOR, ".MuiListItemText-primary").text for i in items]

    def has_empty_state(self) -> bool:
        return len(self.driver.find_elements(*self.EMPTY_STATE)) > 0

    def click_add_successor(self) -> None:
        self.close_mui_dropdown()
        time.sleep(0.5)  # Wait for MUI animation to complete before clicking
        btn = self.wait_for_element_clickable(self.ADD_SUCCESSOR_BTN)
        self.scroll_and_click(btn)
        self.wait_for_element_visible(self.DIALOG)

    def is_dialog_create_button_enabled(self) -> bool:
        btn = self.driver.find_element(*self.DIALOG_CREATE_BTN)
        return btn.is_enabled()

    def select_dialog_target(self, family_name: str) -> None:
        from selenium.webdriver.support.ui import WebDriverWait
        self.close_mui_dropdown()
        select = self.wait_for_element_clickable(self.DIALOG_TARGET_SELECT)
        self.scroll_and_click(select)
        option = self.wait_for_element_clickable(
            (By.XPATH, f"//li[@role='option' and contains(text(), '{family_name}')]")
        )
        self.scroll_and_click(option)
        WebDriverWait(self.driver, 5).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, "li[role='option']")) == 0
        )

    def get_dialog_target_options(self) -> list[str]:
        self.close_mui_dropdown()
        select = self.wait_for_element_clickable(self.DIALOG_TARGET_SELECT)
        self.scroll_and_click(select)
        self.wait_for_element_visible((By.CSS_SELECTOR, "li[role='option']"), timeout=10)
        options = self.driver.find_elements(By.CSS_SELECTOR, "li[role='option']")
        texts = [o.text for o in options if o.text]
        self.close_mui_dropdown()
        return texts

    def set_dialog_wait_years(self, years: str) -> None:
        el = self.wait_for_element_clickable(self.DIALOG_WAIT_YEARS)
        el.clear()
        el.send_keys(years)

    def click_dialog_create(self) -> None:
        self.close_mui_dropdown()
        btn = self.wait_for_element_clickable(self.DIALOG_CREATE_BTN)
        self.scroll_and_click(btn)

    def click_dialog_cancel(self) -> None:
        self.close_mui_dropdown()
        btn = self.wait_for_element_clickable(self.DIALOG_CANCEL_BTN)
        self.scroll_and_click(btn)
