"""Page object for the Planting Run list page (REQ-013)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from .base_page import BasePage


class PlantingRunListPage(BasePage):
    """Interact with the Planting Run list page (``/durchlaeufe/planting-runs``)."""

    PATH = "/durchlaeufe/planting-runs"

    # ── Page-level locators ────────────────────────────────────────────
    PAGE = (By.CSS_SELECTOR, "[data-testid='planting-run-list-page']")
    CREATE_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-button']")
    TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")
    SEARCH_INPUT = (By.CSS_SELECTOR, "[data-testid='table-search-input'] input")
    SEARCH_CHIP = (By.CSS_SELECTOR, "[data-testid='search-chip']")
    SORT_CHIP = (By.CSS_SELECTOR, "[data-testid='sort-chip']")
    RESET_FILTERS = (By.CSS_SELECTOR, "[data-testid='reset-filters-button']")
    SHOWING_COUNT = (By.CSS_SELECTOR, "[data-testid='showing-count']")
    EMPTY_STATE = (By.CSS_SELECTOR, "[data-testid='empty-state']")

    # ── Dialog locators ────────────────────────────────────────────────
    # PlantingRunCreateDialog does not use data-testid="create-dialog" — it uses
    # MUI Dialog with aria role="dialog". We locate it by DialogTitle text via role.
    CREATE_DIALOG = (By.CSS_SELECTOR, "div[role='dialog']")
    CONFIRM_DIALOG = (By.CSS_SELECTOR, "[data-testid='confirm-dialog']")
    CONFIRM_BUTTON = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-confirm']")
    CONFIRM_CANCEL = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-cancel']")

    # ── Create form field locators (inside Dialog) ─────────────────────
    FORM_NAME = (By.CSS_SELECTOR, "[data-testid='form-field-name'] input")
    FORM_RUN_TYPE = (By.CSS_SELECTOR, "[data-testid='form-field-run_type'] .MuiSelect-select")
    FORM_SITE_KEY = (By.CSS_SELECTOR, "[data-testid='form-field-site_key'] .MuiSelect-select")
    FORM_LOCATION_KEY = (By.CSS_SELECTOR, "[data-testid='form-field-location_key'] .MuiSelect-select")
    FORM_PLANNED_START = (By.CSS_SELECTOR, "[data-testid='form-field-planned_start_date'] input")
    FORM_NOTES = (By.CSS_SELECTOR, "[data-testid='form-field-notes'] input")
    # Entry row fields — zero-indexed entry
    FORM_ENTRY_SPECIES = (By.CSS_SELECTOR, "[data-testid='form-field-entries.0.species_key'] .MuiSelect-select")
    FORM_ENTRY_QUANTITY = (By.CSS_SELECTOR, "[data-testid='form-field-entries.0.quantity'] input")
    FORM_ENTRY_ID_PREFIX = (By.CSS_SELECTOR, "[data-testid='form-field-entries.0.id_prefix'] input")
    FORM_ENTRY_ROLE = (By.CSS_SELECTOR, "[data-testid='form-field-entries.0.role'] .MuiSelect-select")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> PlantingRunListPage:
        """Navigate to the planting runs list and wait for it to load."""
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        return self

    # ── Table interactions ─────────────────────────────────────────────

    def get_row_count(self) -> int:
        """Return the number of visible table rows."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        return len(rows)

    def get_first_column_texts(self) -> list[str]:
        """Return the text of the first cell (Name column) for all rows."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        texts = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if cells:
                texts.append(cells[0].text)
        return texts

    def get_row_texts(self) -> list[list[str]]:
        """Return all cell texts for every visible row."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        result = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            result.append([c.text for c in cells])
        return result

    def get_column_headers(self) -> list[str]:
        """Return all visible column header texts."""
        headers = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='data-table'] th")
        return [h.text for h in headers if h.text]

    def click_row(self, index: int = 0) -> None:
        """Click the row at *index* to navigate to its detail page."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        if index < len(rows):
            self.scroll_and_click(rows[index])

    def click_row_by_name(self, name: str) -> None:
        """Click the row whose first cell matches *name*."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if cells and cells[0].text == name:
                self.scroll_and_click(row)
                return
        raise ValueError(f"Row with name '{name}' not found in planting runs table")

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
        return len(self.driver.find_elements(*self.SEARCH_CHIP)) > 0

    def has_sort_chip(self) -> bool:
        return len(self.driver.find_elements(*self.SORT_CHIP)) > 0

    def click_reset_filters(self) -> None:
        self.wait_for_element_clickable(self.RESET_FILTERS).click()

    def has_reset_filters_button(self) -> bool:
        return len(self.driver.find_elements(*self.RESET_FILTERS)) > 0

    def get_showing_count_text(self) -> str:
        el = self.wait_for_element(self.SHOWING_COUNT)
        return el.text

    def has_empty_state(self) -> bool:
        return len(self.driver.find_elements(*self.EMPTY_STATE)) > 0

    def click_column_header(self, header_text: str) -> None:
        """Click a column header by its text to trigger sorting."""
        headers = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='data-table'] th")
        for h in headers:
            if h.text == header_text:
                self.scroll_and_click(h)
                return
        raise ValueError(f"Column header '{header_text}' not found")

    # ── Create dialog ──────────────────────────────────────────────────

    def click_create(self) -> None:
        """Click the Create button and wait for the dialog to open."""
        self.wait_for_element_clickable(self.CREATE_BUTTON).click()
        self.wait_for_element_visible(self.CREATE_DIALOG)

    def is_create_dialog_open(self) -> bool:
        """Return True if the create dialog is currently open."""
        return len(self.driver.find_elements(*self.CREATE_DIALOG)) > 0

    def fill_name(self, name: str) -> None:
        """Fill the Name field in the create dialog."""
        el = self.wait_for_element_clickable(self.FORM_NAME)
        el.clear()
        el.send_keys(name)

    def set_run_type(self, label_text: str) -> None:
        """Select a run type by its visible label text."""
        self.select_option("run_type", label_text)

    def fill_id_prefix(self, prefix: str) -> None:
        """Fill the id_prefix field for the first entry row."""
        el = self.wait_for_element_clickable(self.FORM_ENTRY_ID_PREFIX)
        el.clear()
        el.send_keys(prefix)

    def fill_quantity(self, quantity: int) -> None:
        """Fill the quantity field for the first entry row."""
        el = self.wait_for_element_clickable(self.FORM_ENTRY_QUANTITY)
        el.clear()
        el.send_keys(str(quantity))

    def select_option(self, field_testid: str, value_text: str) -> None:
        """Open an MUI Select dropdown and pick an option by its visible text."""
        field = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='form-field-{field_testid}'] .MuiSelect-select")
        )
        self.scroll_and_click(field)
        option = self.wait_for_element_clickable(
            (By.XPATH, f"//li[@role='option' and contains(text(), '{value_text}')]")
        )
        option.click()

    def submit_create_form(self) -> None:
        """Submit the create form by clicking the Save button."""
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

    # ── Confirm dialog helpers ─────────────────────────────────────────

    def confirm(self) -> None:
        """Click Confirm in the ConfirmDialog."""
        self.wait_for_element_clickable(self.CONFIRM_BUTTON).click()

    def cancel_confirm(self) -> None:
        """Click Cancel in the ConfirmDialog."""
        self.wait_for_element_clickable(self.CONFIRM_CANCEL).click()
