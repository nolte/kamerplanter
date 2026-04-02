"""Page object for the Plant Instance detail page."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from .base_page import BasePage


class PlantInstanceDetailPage(BasePage):
    """Interact with a Plant Instance detail page."""

    PATH_PREFIX = "/pflanzen/plant-instances"

    # Locators
    PAGE = (By.CSS_SELECTOR, "[data-testid='plant-instance-detail-page']")
    TRANSITION_BUTTON = (By.CSS_SELECTOR, "[data-testid='transition-button']")
    REMOVE_BUTTON = (By.CSS_SELECTOR, "[data-testid='remove-button']")
    PLANT_INFO_CARD = (By.CSS_SELECTOR, "[data-testid='plant-info-card']")
    PHASE_INFO_CARD = (By.CSS_SELECTOR, "[data-testid='phase-info-card']")
    CURRENT_PHASE = (By.CSS_SELECTOR, "[data-testid='current-phase']")
    PHASE_HISTORY = (By.CSS_SELECTOR, "[data-testid='phase-history']")
    PHASE_HISTORY_ROWS = (By.CSS_SELECTOR, "[data-testid='phase-history'] tbody tr")
    PHASES_TAB = (By.CSS_SELECTOR, "[data-testid='phases-tab']")
    PHASES_TAB_CONTENT = (By.CSS_SELECTOR, "[data-testid='phases-tab-content']")

    # Transition dialog
    TRANSITION_DIALOG = (By.CSS_SELECTOR, "[data-testid='phase-transition-dialog']")
    TARGET_PHASE_SELECT = (By.CSS_SELECTOR, "[data-testid='target-phase-select']")
    TRANSITION_REASON = (By.CSS_SELECTOR, "[data-testid='transition-reason'] input")
    TRANSITION_CANCEL = (By.CSS_SELECTOR, "[data-testid='transition-cancel']")
    TRANSITION_CONFIRM = (By.CSS_SELECTOR, "[data-testid='transition-confirm']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self, key: str) -> PlantInstanceDetailPage:
        self.navigate(f"{self.PATH_PREFIX}/{key}")
        self.wait_for_element(self.PAGE)
        return self

    def get_current_phase(self) -> str:
        """Return the text of the current-phase Chip."""
        el = self.wait_for_element_visible(self.CURRENT_PHASE)
        return el.text

    def get_plant_info_card(self) -> WebElement:
        return self.wait_for_element_visible(self.PLANT_INFO_CARD)

    def get_phase_info_card(self) -> WebElement:
        return self.wait_for_element_visible(self.PHASE_INFO_CARD)

    def initiate_phase_transition(self) -> None:
        """Click the transition button to open the dialog."""
        self.wait_for_element_clickable(self.TRANSITION_BUTTON).click()
        self.wait_for_element_visible(self.TRANSITION_DIALOG)

    def select_target_phase(self, phase_key: str) -> None:
        """Select a target phase from the dropdown in the transition dialog."""
        select_el = self.wait_for_element_clickable(self.TARGET_PHASE_SELECT)
        # MUI Select: click to open, then find the menu item
        select_el.click()
        option = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"li[data-value='{phase_key}']")
        )
        option.click()

    def set_transition_reason(self, reason: str) -> None:
        reason_input = self.wait_for_element_clickable(self.TRANSITION_REASON)
        reason_input.clear()
        reason_input.send_keys(reason)

    def confirm_transition(self) -> None:
        self.wait_for_element_clickable(self.TRANSITION_CONFIRM).click()

    def cancel_transition(self) -> None:
        self.wait_for_element_clickable(self.TRANSITION_CANCEL).click()

    def get_phase_history_count(self) -> int:
        """Return the number of rows in the phase history table."""
        rows = self.driver.find_elements(*self.PHASE_HISTORY_ROWS)
        return len(rows)

    def has_phase_history(self) -> bool:
        """Check if the phase history section is present."""
        elements = self.driver.find_elements(*self.PHASE_HISTORY)
        return len(elements) > 0
