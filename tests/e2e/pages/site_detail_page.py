"""Page object for the Site detail page."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from .base_page import BasePage


class SiteDetailPage(BasePage):
    """Interact with a Site detail page (``/standorte/sites/:key``).

    Covers REQ-002: Site editing, Location sub-section, Delete flow.
    """

    PATH_PREFIX = "/standorte/sites"

    # ── Page markers ───────────────────────────────────────────────────
    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")
    LOADING_SKELETON = (By.CSS_SELECTOR, "[data-testid='loading-skeleton']")
    ERROR_DISPLAY = (By.CSS_SELECTOR, "[data-testid='error-display']")

    # ── Edit form ─────────────────────────────────────────────────────
    FORM_NAME = (By.CSS_SELECTOR, "[data-testid='form-field-name'] input")
    FORM_TYPE = (By.CSS_SELECTOR, "[data-testid='form-field-type']")
    FORM_CLIMATE_ZONE = (By.CSS_SELECTOR, "[data-testid='form-field-climate_zone'] input")
    FORM_TOTAL_AREA = (By.CSS_SELECTOR, "[data-testid='form-field-total_area_m2'] input")
    FORM_TIMEZONE = (By.CSS_SELECTOR, "[data-testid='form-field-timezone'] input")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    # ── Delete flow ────────────────────────────────────────────────────
    # The delete button does not have data-testid — select by icon/color pattern
    DELETE_BUTTON = (By.XPATH, "//button[contains(@class, 'MuiButton') and .//svg[contains(@class, 'MuiSvgIcon')]][@color='error' or contains(., 'Löschen') or contains(., 'Delete')]")
    CONFIRM_DIALOG = (By.CSS_SELECTOR, "[data-testid='confirm-dialog']")
    CONFIRM_OK = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-confirm']")
    CONFIRM_CANCEL = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-cancel']")

    # ── Location sub-section ──────────────────────────────────────────
    # The Location table is a nested DataTable rendered by LocationListSection
    LOCATION_TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    LOCATION_TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self, key: str) -> SiteDetailPage:
        self.navigate(f"{self.PATH_PREFIX}/{key}")
        self.wait_for_element(self.PAGE_TITLE)
        self._wait_for_skeleton_gone()
        return self

    # ── Private helpers ────────────────────────────────────────────────

    def _wait_for_skeleton_gone(self, timeout: int = 15) -> None:
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        WebDriverWait(self.driver, timeout).until(
            EC.invisibility_of_element_located(self.LOADING_SKELETON)
        )

    # ── Page state ─────────────────────────────────────────────────────

    def get_title(self) -> str:
        return self.wait_for_element_visible(self.PAGE_TITLE).text

    def is_error_shown(self) -> bool:
        elements = self.driver.find_elements(*self.ERROR_DISPLAY)
        return bool(elements) and elements[0].is_displayed()

    # ── Form interactions ──────────────────────────────────────────────

    def get_name_value(self) -> str:
        el = self.wait_for_element(self.FORM_NAME)
        return el.get_attribute("value") or ""

    def set_name(self, value: str) -> None:
        el = self.wait_for_element_clickable(self.FORM_NAME)
        el.clear()
        el.send_keys(value)

    def set_climate_zone(self, value: str) -> None:
        el = self.wait_for_element_clickable(self.FORM_CLIMATE_ZONE)
        el.clear()
        el.send_keys(value)

    def select_type(self, value_text: str) -> None:
        """Open the MUI Select for 'type' and pick an option by visible text."""
        select_el = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, "[data-testid='form-field-type'] .MuiSelect-select")
        )
        self.scroll_and_click(select_el)
        option = self.wait_for_element_clickable(
            (By.XPATH, f"//li[@role='option' and contains(text(), '{value_text}')]")
        )
        option.click()

    def submit_form(self) -> None:
        self.wait_for_element_clickable(self.FORM_SUBMIT).click()

    def cancel_form(self) -> None:
        self.wait_for_element_clickable(self.FORM_CANCEL).click()

    # ── Delete flow ────────────────────────────────────────────────────

    def click_delete(self) -> None:
        """Click the destructive delete button (MUI error-colored Button)."""
        btn = self.wait_for_element_clickable(
            (By.XPATH, "//button[.//text()='Löschen' or .//text()='Delete']")
        )
        self.scroll_and_click(btn)
        self.wait_for_element_visible(self.CONFIRM_DIALOG)

    def confirm_delete(self) -> None:
        self.wait_for_element_clickable(self.CONFIRM_OK).click()

    def cancel_delete(self) -> None:
        self.wait_for_element_clickable(self.CONFIRM_CANCEL).click()

    def is_confirm_dialog_visible(self) -> bool:
        elements = self.driver.find_elements(*self.CONFIRM_DIALOG)
        return bool(elements) and elements[0].is_displayed()

    # ── Location sub-section ──────────────────────────────────────────

    def get_location_row_count(self) -> int:
        rows = self.driver.find_elements(*self.LOCATION_TABLE_ROWS)
        return len(rows)

    def click_location_row(self, index: int) -> None:
        rows = self.driver.find_elements(*self.LOCATION_TABLE_ROWS)
        if index < len(rows):
            self.scroll_and_click(rows[index])

    def is_location_table_visible(self) -> bool:
        elements = self.driver.find_elements(*self.LOCATION_TABLE)
        return bool(elements) and elements[0].is_displayed()
