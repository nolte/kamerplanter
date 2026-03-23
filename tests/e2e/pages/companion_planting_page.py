"""Page object for the Companion Planting page."""

from __future__ import annotations

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class CompanionPlantingPage(BasePage):
    """Interact with the Companion Planting page (``/stammdaten/companion-planting``)."""

    PATH = "/stammdaten/companion-planting"

    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")
    SPECIES_SELECT = (By.CSS_SELECTOR, "[data-testid='species-select'] .MuiSelect-select")
    COMPATIBLE_CARD = (By.XPATH, "//h6[starts-with(normalize-space(text()), 'Kompatible')]/ancestor::div[contains(@class, 'MuiCard-root')]")
    INCOMPATIBLE_CARD = (By.XPATH, "//h6[starts-with(normalize-space(text()), 'Inkompatible')]/ancestor::div[contains(@class, 'MuiCard-root')]")
    ADD_COMPATIBLE_BTN = (By.CSS_SELECTOR, "[data-testid='add-compatible-button']")
    ADD_INCOMPATIBLE_BTN = (By.CSS_SELECTOR, "[data-testid='add-incompatible-button']")

    # Dialog locators
    DIALOG = (By.CSS_SELECTOR, "div[role='dialog']")
    DIALOG_TARGET_SELECT = (By.CSS_SELECTOR, "[data-testid='target-species-select'] .MuiSelect-select")
    DIALOG_SCORE_INPUT = (By.CSS_SELECTOR, "[data-testid='score-input'] input")
    DIALOG_REASON_INPUT = (By.CSS_SELECTOR, "[data-testid='reason-input'] textarea")
    DIALOG_CREATE_BTN = (By.XPATH, "//div[@role='dialog']//button[contains(text(), 'Erstellen')]")
    DIALOG_CANCEL_BTN = (By.XPATH, "//div[@role='dialog']//button[contains(text(), 'Abbrechen')]")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> CompanionPlantingPage:
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE_TITLE)
        self.wait_for_loading_complete()
        return self

    def get_title(self) -> str:
        return self.wait_for_element(self.PAGE_TITLE).text

    def select_species(self, species_name: str) -> None:
        """Select a species from the dropdown."""
        from selenium.webdriver.common.keys import Keys
        # Ensure any previously open dropdown is closed first
        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        time.sleep(0.3)
        select = self.wait_for_element_clickable(self.SPECIES_SELECT)
        self.driver.execute_script("arguments[0].click();", select)
        option = self.wait_for_element_clickable(
            (By.XPATH, f"//li[@role='option' and contains(text(), '{species_name}')]")
        )
        option.click()
        time.sleep(1)  # Wait for companion data to load

    def get_species_options(self) -> list[str]:
        """Return available species names in the dropdown."""
        select = self.wait_for_element_clickable(self.SPECIES_SELECT)
        self.driver.execute_script("arguments[0].click();", select)
        time.sleep(0.3)
        options = self.driver.find_elements(By.CSS_SELECTOR, "li[role='option']")
        texts = [o.text for o in options]
        # Close dropdown by pressing Escape
        from selenium.webdriver.common.keys import Keys
        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        time.sleep(0.3)
        return texts

    def get_compatible_species(self) -> list[str]:
        """Return names of compatible species."""
        try:
            cards = self.driver.find_elements(*self.COMPATIBLE_CARD)
            if not cards:
                return []
            items = cards[0].find_elements(By.CSS_SELECTOR, ".MuiListItemText-primary")
            return [i.text for i in items]
        except Exception:
            return []

    def get_incompatible_species(self) -> list[str]:
        try:
            cards = self.driver.find_elements(*self.INCOMPATIBLE_CARD)
            if not cards:
                return []
            items = cards[0].find_elements(By.CSS_SELECTOR, ".MuiListItemText-primary")
            return [i.text for i in items]
        except Exception:
            return []

    def has_compatible_empty_state(self) -> bool:
        try:
            cards = self.driver.find_elements(*self.COMPATIBLE_CARD)
            if not cards:
                return False
            return len(cards[0].find_elements(By.CSS_SELECTOR, "[data-testid='empty-state']")) > 0
        except Exception:
            return False

    def has_incompatible_empty_state(self) -> bool:
        try:
            cards = self.driver.find_elements(*self.INCOMPATIBLE_CARD)
            if not cards:
                return False
            return len(cards[0].find_elements(By.CSS_SELECTOR, "[data-testid='empty-state']")) > 0
        except Exception:
            return False

    def click_add_compatible(self) -> None:
        self.wait_for_element_clickable(self.ADD_COMPATIBLE_BTN).click()
        self.wait_for_element_visible(self.DIALOG)

    def click_add_incompatible(self) -> None:
        self.wait_for_element_clickable(self.ADD_INCOMPATIBLE_BTN).click()
        self.wait_for_element_visible(self.DIALOG)

    def is_dialog_create_button_enabled(self) -> bool:
        btn = self.driver.find_element(*self.DIALOG_CREATE_BTN)
        return btn.is_enabled()

    def select_dialog_target(self, species_name: str) -> None:
        from selenium.webdriver.common.keys import Keys
        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        time.sleep(0.3)
        select = self.wait_for_element_clickable(self.DIALOG_TARGET_SELECT)
        self.driver.execute_script("arguments[0].click();", select)
        option = self.wait_for_element_clickable(
            (By.XPATH, f"//li[@role='option' and contains(text(), '{species_name}')]")
        )
        option.click()

    def get_dialog_target_options(self) -> list[str]:
        select = self.wait_for_element_clickable(self.DIALOG_TARGET_SELECT)
        self.driver.execute_script("arguments[0].click();", select)
        time.sleep(0.3)
        options = self.driver.find_elements(By.CSS_SELECTOR, "li[role='option']")
        texts = [o.text for o in options]
        from selenium.webdriver.common.keys import Keys
        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        time.sleep(0.3)
        return texts

    def set_dialog_score(self, score: str) -> None:
        el = self.wait_for_element_clickable(self.DIALOG_SCORE_INPUT)
        el.clear()
        el.send_keys(score)

    def set_dialog_reason(self, reason: str) -> None:
        el = self.wait_for_element_clickable(self.DIALOG_REASON_INPUT)
        el.clear()
        el.send_keys(reason)

    def click_dialog_create(self) -> None:
        self.wait_for_element_clickable(self.DIALOG_CREATE_BTN).click()

    def click_dialog_cancel(self) -> None:
        self.wait_for_element_clickable(self.DIALOG_CANCEL_BTN).click()
