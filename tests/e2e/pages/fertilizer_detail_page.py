"""Page object for the Fertilizer detail page (REQ-004)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class FertilizerDetailPage(BasePage):
    """Interact with a Fertilizer detail page (``/duengung/fertilizers/:key``)."""

    # Locators
    PAGE = (By.CSS_SELECTOR, "[data-testid='fertilizer-detail-page']")
    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")
    DELETE_BUTTON = (By.XPATH, "//button[contains(@class, 'MuiButton-colorError')]")
    CONFIRM_DIALOG = (By.CSS_SELECTOR, "[data-testid='confirm-dialog']")
    CONFIRM_BUTTON = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-confirm']")
    CONFIRM_CANCEL = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-cancel']")

    # Tabs — MUI Tabs renders tab buttons; locate by role
    TAB_DETAILS = (By.XPATH, "//button[@role='tab'][1]")
    TAB_STOCK = (By.XPATH, "//button[@role='tab'][2]")
    TAB_EDIT = (By.XPATH, "//button[@role='tab'][3]")

    # Detail view (Tab 0) — DetailRow components rendered as flex Boxes (no <table>)
    # Each DetailRow has a label Typography (text.secondary) and a value Box.
    DETAIL_LABELS = (
        By.CSS_SELECTOR,
        "[data-testid='fertilizer-detail-page'] .MuiTypography-body2[class*='textSecondary']",
    )

    # Stock tab (Tab 1)
    STOCK_TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    STOCK_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")

    # Edit tab (Tab 2) — form fields
    FORM_PRODUCT_NAME = (By.CSS_SELECTOR, "[data-testid='form-field-product_name'] input")
    FORM_BRAND = (By.CSS_SELECTOR, "[data-testid='form-field-brand'] input")
    FORM_EC_CONTRIBUTION = (By.CSS_SELECTOR, "[data-testid='form-field-ec_contribution_per_ml'] input")
    FORM_MIXING_PRIORITY = (By.CSS_SELECTOR, "[data-testid='form-field-mixing_priority'] input")
    FORM_SHELF_LIFE = (By.CSS_SELECTOR, "[data-testid='form-field-shelf_life_days'] input")
    FORM_NOTES = (By.CSS_SELECTOR, "[data-testid='form-field-notes'] textarea")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    # Error / not-found states
    ERROR_DISPLAY = (By.CSS_SELECTOR, "[data-testid='error-display']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self, key: str) -> FertilizerDetailPage:
        """Navigate to a fertilizer detail page and wait for it to load."""
        self.navigate(f"/duengung/fertilizers/{key}")
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        return self

    # ── Navigation ─────────────────────────────────────────────────────

    def get_page_title_text(self) -> str:
        """Return the text of the page title."""
        el = self.wait_for_element(self.PAGE_TITLE)
        return el.text

    # ── Tab navigation ─────────────────────────────────────────────────

    def click_tab_details(self) -> None:
        """Click the first tab (Details)."""
        self.wait_for_element_clickable(self.TAB_DETAILS).click()

    def click_tab_stock(self) -> None:
        """Click the second tab (Stock)."""
        self.wait_for_element_clickable(self.TAB_STOCK).click()

    def click_tab_edit(self) -> None:
        """Click the third tab (Edit)."""
        self.wait_for_element_clickable(self.TAB_EDIT).click()

    def get_active_tab_text(self) -> str:
        """Return the text of the currently active tab."""
        active = self.driver.find_element(By.CSS_SELECTOR, "[role='tab'][aria-selected='true']")
        return active.text

    # ── Details tab (Tab 0) ────────────────────────────────────────────

    def get_detail_row_value(self, label_text: str) -> str:
        """Return the value for a detail row matching the given label.

        The FertilizerDetailPage renders DetailRow components as flex Boxes
        (not table rows).  Each DetailRow has a label Typography and a sibling
        value Box.
        """
        labels = self.driver.find_elements(*self.DETAIL_LABELS)
        for lbl in labels:
            if lbl.text.strip() == label_text:
                # The value is in the next sibling element
                parent = lbl.find_element(By.XPATH, "./..")
                value_box = parent.find_elements(By.CSS_SELECTOR, ":scope > div:last-child")
                if value_box:
                    return value_box[0].text.strip()
        return ""

    def get_all_detail_labels(self) -> list[str]:
        """Return all detail label texts from the detail view.

        DetailRow components use Typography.body2 with color text.secondary for
        labels, rendered in flex layout (no ``<table>``).  We also look for
        section headings (h6/subtitle2) and any caption-style text that acts as
        a property label.
        """
        # Primary: DetailRow labels
        labels_els = self.driver.find_elements(*self.DETAIL_LABELS)
        labels = [el.text.strip() for el in labels_els if el.text.strip()]
        if labels:
            return labels
        # Fallback: any Typography caption used as labels on the detail tab
        captions = self.driver.find_elements(
            By.CSS_SELECTOR,
            "[data-testid='fertilizer-detail-page'] .MuiTypography-caption",
        )
        return [c.text.strip() for c in captions if c.text.strip()]

    # ── Stock tab (Tab 1) ──────────────────────────────────────────────

    def get_stock_row_count(self) -> int:
        """Return the number of stock rows."""
        rows = self.driver.find_elements(*self.STOCK_ROWS)
        return len(rows)

    def get_stock_headers(self) -> list[str]:
        """Return column header texts from the stock table."""
        headers = self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='data-table'] th"
        )
        return [h.text for h in headers if h.text]

    # ── Edit tab (Tab 2) ───────────────────────────────────────────────

    def fill_product_name(self, name: str) -> None:
        """Clear and fill the product name field in the edit form."""
        el = self.wait_for_element_clickable(self.FORM_PRODUCT_NAME)
        self.clear_and_fill(el, name)

    def fill_brand(self, brand: str) -> None:
        """Clear and fill the brand field in the edit form."""
        el = self.wait_for_element_clickable(self.FORM_BRAND)
        self.clear_and_fill(el, brand)

    def fill_mixing_priority(self, value: int) -> None:
        """Clear and fill the mixing priority field."""
        el = self.wait_for_element_clickable(self.FORM_MIXING_PRIORITY)
        self.clear_and_fill(el, str(value))

    def fill_notes(self, notes: str) -> None:
        """Clear and fill the notes textarea."""
        el = self.wait_for_element_clickable(self.FORM_NOTES)
        self.clear_and_fill(el, notes)

    def get_product_name_field_value(self) -> str:
        """Return the current value of the product_name field."""
        el = self.wait_for_element(self.FORM_PRODUCT_NAME)
        return el.get_attribute("value") or ""

    def get_brand_field_value(self) -> str:
        """Return the current value of the brand field."""
        el = self.wait_for_element(self.FORM_BRAND)
        return el.get_attribute("value") or ""

    def is_submit_button_enabled(self) -> bool:
        """Return True if the submit (save) button is enabled."""
        el = self.wait_for_element(self.FORM_SUBMIT)
        return el.is_enabled()

    def submit_edit_form(self) -> None:
        """Submit the edit form."""
        self.wait_for_element_clickable(self.FORM_SUBMIT).click()

    def cancel_edit_form(self) -> None:
        """Click cancel on the edit form to reset changes."""
        self.wait_for_element_clickable(self.FORM_CANCEL).click()

    def get_validation_error(self, field_name: str) -> str:
        """Return the validation error text for the given form field."""
        locator = (
            By.CSS_SELECTOR,
            f"[data-testid='form-field-{field_name}'] .MuiFormHelperText-root.Mui-error",
        )
        elements = self.driver.find_elements(*locator)
        return elements[0].text if elements else ""

    # ── Delete ─────────────────────────────────────────────────────────

    def click_delete(self) -> None:
        """Click the delete button to open the confirm dialog."""
        self.wait_for_element_clickable(self.DELETE_BUTTON).click()
        self.wait_for_element_visible(self.CONFIRM_DIALOG)

    def is_confirm_dialog_open(self) -> bool:
        """Return True if the confirm dialog is open."""
        dialogs = self.driver.find_elements(*self.CONFIRM_DIALOG)
        return any(d.is_displayed() for d in dialogs)

    def confirm_delete(self) -> None:
        """Click the confirm button in the delete dialog."""
        self.wait_for_element_clickable(self.CONFIRM_BUTTON).click()

    def cancel_delete(self) -> None:
        """Click the cancel button in the delete dialog."""
        self.wait_for_element_clickable(self.CONFIRM_CANCEL).click()

    # ── Error state ────────────────────────────────────────────────────

    def is_error_displayed(self) -> bool:
        """Return True if an error or not-found display is visible."""
        elements = self.driver.find_elements(*self.ERROR_DISPLAY)
        return len(elements) > 0 and elements[0].is_displayed()
