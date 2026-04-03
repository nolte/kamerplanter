"""Page object for the Substrate list page (REQ-019)."""

from __future__ import annotations

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class SubstrateListPage(BasePage):
    """Interact with the Substrate list page (``/standorte/substrates``)."""

    PATH = "/standorte/substrates"

    # ── Page-level locators ────────────────────────────────────────────
    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")
    TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")
    SEARCH_INPUT = (By.CSS_SELECTOR, "[data-testid='table-search-input'] input")
    SEARCH_CHIP = (By.CSS_SELECTOR, "[data-testid='search-chip']")
    SORT_CHIP = (By.CSS_SELECTOR, "[data-testid='sort-chip']")
    RESET_FILTERS = (By.CSS_SELECTOR, "[data-testid='reset-filters-button']")
    SHOWING_COUNT = (By.CSS_SELECTOR, "[data-testid='showing-count']")
    NO_SEARCH_RESULTS = (By.CSS_SELECTOR, "[data-testid='no-search-results']")

    # ── Action buttons (no data-testid — located by text/icon) ────────
    # The SubstrateListPage uses inline MUI Buttons without data-testid.
    # We use the button text rendered via i18n.
    CREATE_BUTTON = (By.XPATH, "//button[contains(@class, 'MuiButton-contained')]")
    MIX_BUTTON = (By.XPATH, "//button[contains(@class, 'MuiButton-outlined')]")

    # ── Create dialog locators ─────────────────────────────────────────
    CREATE_DIALOG = (By.CSS_SELECTOR, "div[role='dialog']")
    FORM_TYPE = (By.CSS_SELECTOR, "[data-testid='form-field-type'] .MuiSelect-select")
    FORM_BRAND = (By.CSS_SELECTOR, "[data-testid='form-field-brand'] input")
    FORM_NAME_DE = (By.CSS_SELECTOR, "[data-testid='form-field-name_de'] input")
    FORM_NAME_EN = (By.CSS_SELECTOR, "[data-testid='form-field-name_en'] input")
    FORM_PH_BASE = (By.CSS_SELECTOR, "[data-testid='form-field-ph_base'] input")
    FORM_EC_BASE = (By.CSS_SELECTOR, "[data-testid='form-field-ec_base_ms'] input")
    FORM_WATER_RETENTION = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-water_retention'] .MuiSelect-select",
    )
    FORM_AIR_POROSITY = (By.CSS_SELECTOR, "[data-testid='form-field-air_porosity_percent'] input")
    FORM_BUFFER_CAPACITY = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-buffer_capacity'] .MuiSelect-select",
    )
    FORM_REUSABLE = (By.CSS_SELECTOR, "[data-testid='form-field-reusable'] .MuiSwitch-root")
    FORM_MAX_REUSE = (By.CSS_SELECTOR, "[data-testid='form-field-max_reuse_cycles'] input")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> SubstrateListPage:
        """Navigate to the substrates list and wait for it to load."""
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE_TITLE)
        self.wait_for_loading_complete()
        return self

    # ── Table interactions ─────────────────────────────────────────────

    def get_row_count(self) -> int:
        """Return the number of visible table rows."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        return len(rows)

    def get_first_column_texts(self) -> list[str]:
        """Return the text of the first column for all rows."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        texts = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if cells:
                texts.append(cells[0].text)
        return texts

    def get_column_headers(self) -> list[str]:
        """Return all visible column header texts."""
        headers = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='data-table'] th")
        return [h.text for h in headers if h.text]

    def get_row_texts(self) -> list[list[str]]:
        """Return all cell texts for every visible row."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        result = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            result.append([c.text for c in cells])
        return result

    def click_row(self, index: int = 0) -> None:
        """Click the row at *index*."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        if index < len(rows):
            self.scroll_and_click(rows[index])

    def click_row_by_text(self, text: str) -> None:
        """Click the row containing *text* in any cell."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        for row in rows:
            if text in row.text:
                self.scroll_and_click(row)
                return
        raise ValueError(f"Row containing '{text}' not found in substrate table")

    def click_column_header(self, header_text: str) -> None:
        """Click a column header by its text to trigger sorting."""
        headers = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='data-table'] th")
        for h in headers:
            if h.text == header_text:
                self.scroll_and_click(h)
                return
        raise ValueError(f"Column header '{header_text}' not found")

    # ── Search and filter ──────────────────────────────────────────────

    def search(self, term: str) -> None:
        """Type *term* into the search field."""
        search_input = self.wait_for_element_clickable(self.SEARCH_INPUT)
        search_input.clear()
        search_input.send_keys(term)

    def clear_search(self) -> None:
        """Clear the search field."""
        search_input = self.wait_for_element_clickable(self.SEARCH_INPUT)
        search_input.clear()
        search_input.send_keys(Keys.BACKSPACE)

    def has_search_chip(self) -> bool:
        """Return True if a search chip is visible."""
        return len(self.driver.find_elements(*self.SEARCH_CHIP)) > 0

    def has_sort_chip(self) -> bool:
        """Return True if a sort chip is visible."""
        return len(self.driver.find_elements(*self.SORT_CHIP)) > 0

    def click_reset_filters(self) -> None:
        """Click the reset filters button."""
        self.wait_for_element_clickable(self.RESET_FILTERS).click()

    def has_reset_filters_button(self) -> bool:
        """Return True if the reset filters button is visible."""
        return len(self.driver.find_elements(*self.RESET_FILTERS)) > 0

    def has_no_search_results(self) -> bool:
        """Return True if the 'no search results' message is shown."""
        return len(self.driver.find_elements(*self.NO_SEARCH_RESULTS)) > 0

    def get_showing_count_text(self) -> str:
        """Return the text of the showing count element."""
        el = self.wait_for_element(self.SHOWING_COUNT)
        return el.text

    # ── Create dialog ──────────────────────────────────────────────────

    def click_create(self) -> None:
        """Click the Create button and wait for the dialog."""
        self.wait_for_element_clickable(self.CREATE_BUTTON).click()
        self.wait_for_element_visible(self.CREATE_DIALOG)

    def is_create_dialog_open(self) -> bool:
        """Return True if any dialog is open."""
        return len(self.driver.find_elements(*self.CREATE_DIALOG)) > 0

    def fill_brand(self, value: str) -> None:
        """Fill the Brand field in the create dialog."""
        el = self.wait_for_element_clickable(self.FORM_BRAND)
        self.clear_and_fill(el, value)

    def fill_name_de(self, value: str) -> None:
        """Fill the Name (DE) field in the create dialog."""
        el = self.wait_for_element_clickable(self.FORM_NAME_DE)
        self.clear_and_fill(el, value)

    def fill_name_en(self, value: str) -> None:
        """Fill the Name (EN) field in the create dialog."""
        el = self.wait_for_element_clickable(self.FORM_NAME_EN)
        self.clear_and_fill(el, value)

    def fill_ph_base(self, value: float) -> None:
        """Fill the pH base field."""
        el = self.wait_for_element_clickable(self.FORM_PH_BASE)
        self.clear_and_fill(el, str(value))

    def fill_ec_base(self, value: float) -> None:
        """Fill the EC base field."""
        el = self.wait_for_element_clickable(self.FORM_EC_BASE)
        self.clear_and_fill(el, str(value))

    def fill_air_porosity(self, value: float) -> None:
        """Fill the air porosity field."""
        el = self.wait_for_element_clickable(self.FORM_AIR_POROSITY)
        self.clear_and_fill(el, str(value))

    def fill_max_reuse_cycles(self, value: int) -> None:
        """Fill the max reuse cycles field."""
        el = self.wait_for_element_clickable(self.FORM_MAX_REUSE)
        self.clear_and_fill(el, str(value))

    def select_type(self, label_text: str) -> None:
        """Select a substrate type by its visible label."""
        self._select_option("type", label_text)

    def select_water_retention(self, label_text: str) -> None:
        """Select a water retention value by its visible label."""
        self._select_option("water_retention", label_text)

    def select_buffer_capacity(self, label_text: str) -> None:
        """Select a buffer capacity by its visible label."""
        self._select_option("buffer_capacity", label_text)

    def toggle_reusable(self) -> None:
        """Toggle the reusable switch."""
        el = self.wait_for_element_clickable(self.FORM_REUSABLE)
        self.scroll_and_click(el)

    def is_reusable_checked(self) -> bool:
        """Return True if the reusable switch is checked."""
        el = self.driver.find_element(
            By.CSS_SELECTOR, "[data-testid='form-field-reusable'] input[type='checkbox']"
        )
        return el.is_selected()

    def submit_create_form(self) -> None:
        """Submit the create form."""
        self.wait_for_element_clickable(self.FORM_SUBMIT).click()

    def cancel_create_form(self) -> None:
        """Cancel the create dialog."""
        self.wait_for_element_clickable(self.FORM_CANCEL).click()

    def get_validation_error(self, field_name: str) -> str:
        """Return the validation error text for a form field."""
        locator = (
            By.CSS_SELECTOR,
            f"[data-testid='form-field-{field_name}'] .MuiFormHelperText-root.Mui-error",
        )
        elements = self.driver.find_elements(*locator)
        return elements[0].text if elements else ""

    def has_validation_error(self, field_name: str) -> bool:
        """Return True if a validation error is visible for *field_name*."""
        return bool(self.get_validation_error(field_name))

    # ── Private helpers ────────────────────────────────────────────────

    def _select_option(self, field_testid: str, value_text: str) -> None:
        """Open an MUI Select and pick an option by its visible text."""
        field = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='form-field-{field_testid}'] .MuiSelect-select")
        )
        self.scroll_and_click(field)
        option = self.wait_for_element_clickable(
            (By.XPATH, f"//li[@role='option' and contains(text(), '{value_text}')]")
        )
        option.click()
        self.close_mui_dropdown()

    def get_type_options(self) -> list[str]:
        """Open the type dropdown and return all option texts.

        The dropdown is closed again afterwards.
        """
        field = self.wait_for_element_clickable(self.FORM_TYPE)
        self.scroll_and_click(field)
        options = self.driver.find_elements(By.CSS_SELECTOR, "li[role='option']")
        texts = [o.text for o in options]
        self.close_mui_dropdown()
        return texts
