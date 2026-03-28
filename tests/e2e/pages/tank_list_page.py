"""Page object for the Tank list page (REQ-014)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class TankListPage(BasePage):
    """Interact with the Tank list page (``/standorte/tanks``)."""

    PATH = "/standorte/tanks"

    # ── Page-level locators ────────────────────────────────────────────
    PAGE = (By.CSS_SELECTOR, "[data-testid='tank-list-page']")
    CREATE_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-button']")
    TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")
    SEARCH_INPUT = (By.CSS_SELECTOR, "[data-testid='table-search-input'] input")
    SEARCH_CHIP = (By.CSS_SELECTOR, "[data-testid='search-chip']")
    SORT_CHIP = (By.CSS_SELECTOR, "[data-testid='sort-chip']")
    RESET_FILTERS = (By.CSS_SELECTOR, "[data-testid='reset-filters-button']")
    SHOWING_COUNT = (By.CSS_SELECTOR, "[data-testid='showing-count']")
    EMPTY_STATE = (By.CSS_SELECTOR, "[data-testid='empty-state']")

    # ── Create dialog locators ─────────────────────────────────────────
    CREATE_DIALOG = (By.CSS_SELECTOR, "div[role='dialog']")
    CONFIRM_DIALOG = (By.CSS_SELECTOR, "[data-testid='confirm-dialog']")
    CONFIRM_BUTTON = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-confirm']")
    CONFIRM_CANCEL = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-cancel']")

    # ── Create form field locators ─────────────────────────────────────
    FORM_NAME = (By.CSS_SELECTOR, "[data-testid='form-field-name'] input")
    FORM_TANK_TYPE = (By.CSS_SELECTOR, "[data-testid='form-field-tank_type'] .MuiSelect-select")
    FORM_VOLUME = (By.CSS_SELECTOR, "[data-testid='form-field-volume_liters'] input")
    FORM_MATERIAL = (By.CSS_SELECTOR, "[data-testid='form-field-material'] .MuiSelect-select")
    FORM_HAS_LID = (By.CSS_SELECTOR, "[data-testid='form-field-has_lid'] .MuiSwitch-root")
    FORM_HAS_AIR_PUMP = (By.CSS_SELECTOR, "[data-testid='form-field-has_air_pump'] .MuiSwitch-root")
    FORM_HAS_CIRCULATION_PUMP = (By.CSS_SELECTOR, "[data-testid='form-field-has_circulation_pump'] .MuiSwitch-root")
    FORM_HAS_HEATER = (By.CSS_SELECTOR, "[data-testid='form-field-has_heater'] .MuiSwitch-root")
    FORM_NOTES = (By.CSS_SELECTOR, "[data-testid='form-field-notes'] textarea")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> TankListPage:
        """Navigate to the tanks list and wait for it to load."""
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
        """Return the text of the Name column for all rows."""
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

    def click_row(self, index: int = 0) -> None:
        """Click the row at *index*."""
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
        raise ValueError(f"Row with name '{name}' not found in tanks table")

    def get_row_texts(self) -> list[list[str]]:
        """Return all cell texts for every visible row."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        result = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            result.append([c.text for c in cells])
        return result

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

    # ── Create dialog ──────────────────────────────────────────────────

    def click_create(self) -> None:
        """Click the Create button and wait for the dialog."""
        self.wait_for_element_clickable(self.CREATE_BUTTON).click()
        self.wait_for_element_visible(self.CREATE_DIALOG)

    def is_create_dialog_open(self) -> bool:
        return len(self.driver.find_elements(*self.CREATE_DIALOG)) > 0

    def fill_name(self, name: str) -> None:
        """Fill the Name field in the create dialog."""
        el = self.wait_for_element_clickable(self.FORM_NAME)
        el.clear()
        el.send_keys(name)

    def fill_volume(self, volume: float) -> None:
        """Fill the volume_liters field."""
        el = self.wait_for_element_clickable(self.FORM_VOLUME)
        el.clear()
        el.send_keys(str(volume))

    def select_tank_type(self, label_text: str) -> None:
        """Select a tank type by its visible label."""
        self.select_option("tank_type", label_text)

    def select_material(self, label_text: str) -> None:
        """Select a material by its visible label."""
        self.select_option("material", label_text)

    def toggle_has_lid(self) -> None:
        """Toggle the 'has lid' switch."""
        el = self.wait_for_element_clickable(self.FORM_HAS_LID)
        self.scroll_and_click(el)

    def toggle_has_air_pump(self) -> None:
        """Toggle the 'has air pump' switch."""
        el = self.wait_for_element_clickable(self.FORM_HAS_AIR_PUMP)
        self.scroll_and_click(el)

    def is_has_lid_checked(self) -> bool:
        el = self.driver.find_element(
            By.CSS_SELECTOR, "[data-testid='form-field-has_lid'] input[type='checkbox']"
        )
        return el.is_selected()

    def fill_notes(self, notes: str) -> None:
        """Fill the Notes textarea."""
        el = self.wait_for_element_clickable(self.FORM_NOTES)
        el.clear()
        el.send_keys(notes)

    def select_option(self, field_testid: str, value_text: str) -> None:
        """Open an MUI Select and pick an option by its visible text."""
        import time
        from selenium.webdriver.common.keys import Keys

        field = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='form-field-{field_testid}'] .MuiSelect-select")
        )
        self.scroll_and_click(field)
        option = self.wait_for_element_clickable(
            (By.XPATH, f"//li[@role='option' and contains(text(), '{value_text}')]")
        )
        option.click()
        # Dismiss MUI Select backdrop/popover to unblock subsequent interactions
        time.sleep(0.3)
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            pass
        time.sleep(0.3)

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
