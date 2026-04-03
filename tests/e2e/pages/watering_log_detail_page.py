"""Page object for the Watering Log detail page (REQ-004)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class WateringLogDetailPage(BasePage):
    """Interact with the Watering Log detail page (``/giessprotokoll/:key``)."""

    # -- Page-level locators ------------------------------------------------
    PAGE = (By.CSS_SELECTOR, "[data-testid='watering-log-detail-page']")

    # -- Delete button ------------------------------------------------------
    DELETE_BUTTON = (By.CSS_SELECTOR, "[data-testid='delete-watering-log-button']")

    # -- Tab locators -------------------------------------------------------
    TABS = (By.CSS_SELECTOR, "button[role='tab']")
    DETAILS_TAB = (By.CSS_SELECTOR, "[data-testid='details-tab']")
    EDIT_TAB = (By.CSS_SELECTOR, "[data-testid='edit-tab']")

    # -- ConfirmDialog (delete) ---------------------------------------------
    CONFIRM_DIALOG = (By.CSS_SELECTOR, "[data-testid='confirm-dialog']")
    CONFIRM_BUTTON = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-confirm']")
    CONFIRM_CANCEL = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-cancel']")

    # -- Details tab content ------------------------------------------------
    DETAIL_CARDS = (By.CSS_SELECTOR, "[data-testid='watering-log-detail-page'] .MuiCard-root")
    ANALYZE_RUNOFF_BUTTON = (By.CSS_SELECTOR, "[data-testid='analyze-runoff-button']")
    RUNOFF_ANALYSIS_RESULT = (By.CSS_SELECTOR, "[data-testid='runoff-analysis-result']")

    # -- Edit tab form fields -----------------------------------------------
    FORM_APPLICATION_METHOD = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-application_method'] .MuiSelect-select",
    )
    FORM_VOLUME = (By.CSS_SELECTOR, "[data-testid='form-field-volume_liters'] input")
    FORM_NOTES = (By.CSS_SELECTOR, "[data-testid='form-field-notes'] textarea")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self, key: str) -> WateringLogDetailPage:
        """Navigate to the watering log detail page for *key*."""
        self.navigate(f"/giessprotokoll/{key}")
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        return self

    # -- Page info ----------------------------------------------------------

    def get_tab_labels(self) -> list[str]:
        """Return the text of all visible tabs."""
        tabs = self.driver.find_elements(*self.TABS)
        return [t.text for t in tabs if t.text]

    def get_tab_count(self) -> int:
        """Return the number of visible tabs."""
        return len(self.driver.find_elements(*self.TABS))

    def click_tab(self, index: int) -> None:
        """Click the tab at *index*."""
        tabs = self.driver.find_elements(*self.TABS)
        if index < len(tabs):
            self.scroll_and_click(tabs[index])

    def click_details_tab(self) -> None:
        """Click the Details tab."""
        self.wait_for_element_clickable(self.DETAILS_TAB).click()

    def click_edit_tab(self) -> None:
        """Click the Edit tab."""
        self.wait_for_element_clickable(self.EDIT_TAB).click()

    # -- Details tab --------------------------------------------------------

    def get_detail_card_count(self) -> int:
        """Return the number of MUI Cards on the details tab."""
        return len(self.driver.find_elements(*self.DETAIL_CARDS))

    def has_analyze_runoff_button(self) -> bool:
        """Return True if the analyze-runoff button is visible."""
        elements = self.driver.find_elements(*self.ANALYZE_RUNOFF_BUTTON)
        return len(elements) > 0 and elements[0].is_displayed()

    def click_analyze_runoff(self) -> None:
        """Click the analyze-runoff button."""
        self.wait_for_element_clickable(self.ANALYZE_RUNOFF_BUTTON).click()

    def has_runoff_analysis_result(self) -> bool:
        """Return True if the runoff analysis result alert is visible."""
        return len(self.driver.find_elements(*self.RUNOFF_ANALYSIS_RESULT)) > 0

    # -- Delete dialog ------------------------------------------------------

    def click_delete(self) -> None:
        """Click the delete button and wait for the confirmation dialog."""
        self.wait_for_element_clickable(self.DELETE_BUTTON).click()
        self.wait_for_element_visible(self.CONFIRM_DIALOG)

    def confirm_delete(self) -> None:
        """Confirm the deletion in the dialog."""
        self.wait_for_element_clickable(self.CONFIRM_BUTTON).click()

    def cancel_delete(self) -> None:
        """Cancel the deletion dialog."""
        self.wait_for_element_clickable(self.CONFIRM_CANCEL).click()

    # -- Edit tab -----------------------------------------------------------

    def is_edit_form_visible(self) -> bool:
        """Return True if the edit form is visible (volume field present)."""
        return len(self.driver.find_elements(*self.FORM_VOLUME)) > 0

    def get_volume_value(self) -> str:
        """Return the current value of the volume field on the edit tab."""
        el = self.wait_for_element(self.FORM_VOLUME)
        return el.get_attribute("value") or ""
