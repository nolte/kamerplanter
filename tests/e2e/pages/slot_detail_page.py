"""Page object for the Slot detail page."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class SlotDetailPage(BasePage):
    """Interact with a Slot detail page (``/standorte/slots/:key``).

    Covers REQ-002: Slot editing (slot_id, capacity), Delete flow.
    """

    PATH_PREFIX = "/standorte/slots"

    # ── Page markers ───────────────────────────────────────────────────
    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")
    LOADING_SKELETON = (By.CSS_SELECTOR, "[data-testid='loading-skeleton']")
    ERROR_DISPLAY = (By.CSS_SELECTOR, "[data-testid='error-display']")

    # ── Edit form ─────────────────────────────────────────────────────
    FORM_SLOT_ID = (By.CSS_SELECTOR, "[data-testid='form-field-slot_id'] input")
    FORM_CAPACITY = (By.CSS_SELECTOR, "[data-testid='form-field-capacity_plants'] input")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    # ── Delete flow ────────────────────────────────────────────────────
    CONFIRM_DIALOG = (By.CSS_SELECTOR, "[data-testid='confirm-dialog']")
    CONFIRM_OK = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-confirm']")
    CONFIRM_CANCEL = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-cancel']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self, key: str) -> SlotDetailPage:
        self.navigate(f"{self.PATH_PREFIX}/{key}")
        self.wait_for_element(self.PAGE_TITLE)
        self._wait_for_skeleton_gone()
        return self

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

    def get_slot_id_value(self) -> str:
        el = self.wait_for_element(self.FORM_SLOT_ID)
        return el.get_attribute("value") or ""

    def get_capacity_value(self) -> str:
        el = self.wait_for_element(self.FORM_CAPACITY)
        return el.get_attribute("value") or ""

    def set_slot_id(self, value: str) -> None:
        el = self.wait_for_element_clickable(self.FORM_SLOT_ID)
        el.clear()
        el.send_keys(value)

    def set_capacity(self, value: str) -> None:
        el = self.wait_for_element_clickable(self.FORM_CAPACITY)
        el.clear()
        el.send_keys(value)

    def submit_form(self) -> None:
        self.wait_for_element_clickable(self.FORM_SUBMIT).click()

    def cancel_form(self) -> None:
        self.wait_for_element_clickable(self.FORM_CANCEL).click()

    # ── Delete flow ────────────────────────────────────────────────────

    def click_delete(self) -> None:
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
