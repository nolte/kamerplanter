"""Page object for the Location detail page."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from .base_page import BasePage


class LocationDetailPage(BasePage):
    """Interact with a Location detail page (``/standorte/locations/:key``).

    Covers REQ-002: Location editing, Slot sub-section, Watering events, Delete flow.
    """

    PATH_PREFIX = "/standorte/locations"

    # ── Page markers ───────────────────────────────────────────────────
    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")
    LOADING_SKELETON = (By.CSS_SELECTOR, "[data-testid='loading-skeleton']")
    ERROR_DISPLAY = (By.CSS_SELECTOR, "[data-testid='error-display']")

    # ── Edit form ─────────────────────────────────────────────────────
    FORM_NAME = (By.CSS_SELECTOR, "[data-testid='form-field-name'] input")
    FORM_AREA = (By.CSS_SELECTOR, "[data-testid='form-field-area_m2'] input")
    FORM_LIGHT_TYPE = (By.CSS_SELECTOR, "[data-testid='form-field-light_type']")
    FORM_IRRIGATION = (By.CSS_SELECTOR, "[data-testid='form-field-irrigation_system']")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    # ── Delete flow ────────────────────────────────────────────────────
    CONFIRM_DIALOG = (By.CSS_SELECTOR, "[data-testid='confirm-dialog']")
    CONFIRM_OK = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-confirm']")
    CONFIRM_CANCEL = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-cancel']")

    # ── Slot sub-section ───────────────────────────────────────────────
    # DataTable rows — there may be multiple DataTables on the page (slots + watering)
    # We select all data-table-row elements; slots table appears first.
    DATA_TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")
    CREATE_WATERING_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-watering-button']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self, key: str) -> LocationDetailPage:
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

    def set_area(self, value: str) -> None:
        el = self.wait_for_element_clickable(self.FORM_AREA)
        el.clear()
        el.send_keys(value)

    def select_light_type(self, value_text: str) -> None:
        """Open the 'light_type' MUI Select and pick by visible text."""
        import time
        from selenium.webdriver.common.keys import Keys

        select_el = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, "[data-testid='form-field-light_type'] .MuiSelect-select")
        )
        self.scroll_and_click(select_el)
        option = self.wait_for_element_clickable(
            (By.XPATH, f"//li[@role='option' and contains(text(), '{value_text}')]")
        )
        option.click()
        # Dismiss MUI Select backdrop/popover
        time.sleep(0.3)
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            pass
        time.sleep(0.3)

    def select_irrigation_system(self, value_text: str) -> None:
        """Open the 'irrigation_system' MUI Select and pick by visible text."""
        import time
        from selenium.webdriver.common.keys import Keys

        select_el = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, "[data-testid='form-field-irrigation_system'] .MuiSelect-select")
        )
        self.scroll_and_click(select_el)
        option = self.wait_for_element_clickable(
            (By.XPATH, f"//li[@role='option' and contains(text(), '{value_text}')]")
        )
        option.click()
        # Dismiss MUI Select backdrop/popover
        time.sleep(0.3)
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            pass
        time.sleep(0.3)

    def submit_form(self) -> None:
        self.wait_for_element_clickable(self.FORM_SUBMIT).click()

    def cancel_form(self) -> None:
        self.wait_for_element_clickable(self.FORM_CANCEL).click()

    # ── Delete flow ────────────────────────────────────────────────────

    def click_delete(self) -> None:
        """Click the destructive Delete button."""
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

    # ── Slot sub-section ───────────────────────────────────────────────

    def get_all_table_row_count(self) -> int:
        """Return total count of data-table-row elements on page (slots + watering)."""
        rows = self.driver.find_elements(*self.DATA_TABLE_ROWS)
        return len(rows)

    def is_create_watering_button_visible(self) -> bool:
        elements = self.driver.find_elements(*self.CREATE_WATERING_BUTTON)
        return bool(elements) and elements[0].is_displayed()

    def click_create_watering(self) -> None:
        self.wait_for_element_clickable(self.CREATE_WATERING_BUTTON).click()
