"""Page object for the Botanical Family list page."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from .base_page import BasePage


class BotanicalFamilyListPage(BasePage):
    """Interact with the Botanical Families list (``/stammdaten/botanical-families``)."""

    PATH = "/stammdaten/botanical-families"

    # Locators
    PAGE = (By.CSS_SELECTOR, "[data-testid='botanical-family-list-page']")
    CREATE_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-button']")
    TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")
    SEARCH_INPUT = (By.CSS_SELECTOR, "[data-testid='table-search-input'] input")
    SEARCH_CHIP = (By.CSS_SELECTOR, "[data-testid='search-chip']")
    SORT_CHIP = (By.CSS_SELECTOR, "[data-testid='sort-chip']")
    RESET_FILTERS = (By.CSS_SELECTOR, "[data-testid='reset-filters-button']")
    SHOWING_COUNT = (By.CSS_SELECTOR, "[data-testid='showing-count']")
    EMPTY_STATE = (By.CSS_SELECTOR, "[data-testid='empty-state']")
    CREATE_DIALOG = (By.CSS_SELECTOR, "[data-testid='create-dialog']")
    CONFIRM_DIALOG = (By.CSS_SELECTOR, "[data-testid='confirm-dialog']")
    CONFIRM_BUTTON = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-confirm']")
    CONFIRM_CANCEL = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-cancel']")

    # Form locators
    FORM_NAME = (By.CSS_SELECTOR, "[data-testid='form-field-name'] input")
    FORM_COMMON_NAME_DE = (By.CSS_SELECTOR, "[data-testid='form-field-common_name_de'] input")
    FORM_COMMON_NAME_EN = (By.CSS_SELECTOR, "[data-testid='form-field-common_name_en'] input")
    FORM_ORDER = (By.CSS_SELECTOR, "[data-testid='form-field-order'] input")
    FORM_DESCRIPTION = (By.CSS_SELECTOR, "[data-testid='form-field-description'] textarea")
    FORM_NUTRIENT_DEMAND = (By.CSS_SELECTOR, "[data-testid='form-field-typical_nutrient_demand']")
    FORM_NITROGEN_FIXING = (By.CSS_SELECTOR, "[data-testid='form-field-nitrogen_fixing']")
    FORM_ROOT_DEPTH = (By.CSS_SELECTOR, "[data-testid='form-field-typical_root_depth']")
    FORM_PH_MIN = (By.CSS_SELECTOR, "[data-testid='form-field-soil_ph_min'] input")
    FORM_PH_MAX = (By.CSS_SELECTOR, "[data-testid='form-field-soil_ph_max'] input")
    FORM_FROST_TOLERANCE = (By.CSS_SELECTOR, "[data-testid='form-field-frost_tolerance']")
    FORM_GROWTH_FORMS = (By.CSS_SELECTOR, "[data-testid='form-field-typical_growth_forms']")
    FORM_PESTS = (By.CSS_SELECTOR, "[data-testid='form-field-common_pests']")
    FORM_DISEASES = (By.CSS_SELECTOR, "[data-testid='form-field-common_diseases']")
    FORM_POLLINATION = (By.CSS_SELECTOR, "[data-testid='form-field-pollination_type']")
    FORM_ROTATION_CAT = (By.CSS_SELECTOR, "[data-testid='form-field-rotation_category'] input")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> BotanicalFamilyListPage:
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        return self

    # ── Table interactions ─────────────────────────────────────────────

    def get_row_count(self) -> int:
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        return len(rows)

    def get_row_texts(self) -> list[list[str]]:
        """Return text content of all visible rows as list of cell texts."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        result = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            result.append([c.text for c in cells])
        return result

    def get_first_column_texts(self) -> list[str]:
        """Return text of the first column (Name) for all rows."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        texts = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if cells:
                texts.append(cells[0].text)
        return texts

    def click_row(self, index: int) -> None:
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
        raise ValueError(f"Row with name '{name}' not found")

    def get_column_headers(self) -> list[str]:
        """Return all visible column header texts."""
        headers = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='data-table'] th")
        return [h.text for h in headers if h.text]

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
        """Type a search term into the search field."""
        search_input = self.wait_for_element_clickable(self.SEARCH_INPUT)
        self.clear_and_fill(search_input, term)

    def clear_search(self) -> None:
        search_input = self.wait_for_element_clickable(self.SEARCH_INPUT)
        self.clear_and_fill(search_input, "")

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
        self.wait_for_element_clickable(self.CREATE_BUTTON).click()
        self.wait_for_element_visible(self.CREATE_DIALOG)

    def fill_create_form(self, name: str, **kwargs: str) -> None:
        """Fill the create form. Only *name* is required."""
        name_input = self.wait_for_element_clickable(self.FORM_NAME)
        name_input.clear()
        name_input.send_keys(name)

        if "common_name_de" in kwargs:
            el = self.wait_for_element_clickable(self.FORM_COMMON_NAME_DE)
            el.clear()
            el.send_keys(kwargs["common_name_de"])

        if "common_name_en" in kwargs:
            el = self.wait_for_element_clickable(self.FORM_COMMON_NAME_EN)
            el.clear()
            el.send_keys(kwargs["common_name_en"])

        if "order" in kwargs:
            el = self.wait_for_element_clickable(self.FORM_ORDER)
            el.clear()
            el.send_keys(kwargs["order"])

        if "description" in kwargs:
            el = self.wait_for_element_clickable(self.FORM_DESCRIPTION)
            el.clear()
            el.send_keys(kwargs["description"])

        if "ph_min" in kwargs:
            el = self.wait_for_element_clickable(self.FORM_PH_MIN)
            el.clear()
            el.send_keys(kwargs["ph_min"])

        if "ph_max" in kwargs:
            el = self.wait_for_element_clickable(self.FORM_PH_MAX)
            el.clear()
            el.send_keys(kwargs["ph_max"])

        if "rotation_category" in kwargs:
            el = self.wait_for_element_clickable(self.FORM_ROTATION_CAT)
            el.clear()
            el.send_keys(kwargs["rotation_category"])

    def fill_name_only(self, name: str) -> None:
        """Fill just the name field."""
        name_input = self.wait_for_element_clickable(self.FORM_NAME)
        name_input.clear()
        name_input.send_keys(name)

    def get_name_field_value(self) -> str:
        el = self.wait_for_element(self.FORM_NAME)
        return el.get_attribute("value") or ""

    def submit_create_form(self) -> None:
        self.wait_for_element_clickable(self.FORM_SUBMIT).click()

    def cancel_create_form(self) -> None:
        self.wait_for_element_clickable(self.FORM_CANCEL).click()

    def is_create_dialog_open(self) -> bool:
        return len(self.driver.find_elements(*self.CREATE_DIALOG)) > 0

    def get_validation_error(self, field_name: str) -> str:
        """Return the validation error text for a form field."""
        locator = (By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] .MuiFormHelperText-root.Mui-error")
        elements = self.driver.find_elements(*locator)
        return elements[0].text if elements else ""

    def has_validation_error(self, field_name: str) -> bool:
        return bool(self.get_validation_error(field_name))

    # ── MUI Select helpers ─────────────────────────────────────────────

    def select_option(self, field_testid: str, value_text: str) -> None:
        """Open an MUI Select and pick an option by its visible text."""
        import time

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

    def toggle_switch(self, field_testid: str) -> None:
        """Toggle a MUI Switch by its field testid."""
        switch = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='form-field-{field_testid}'] input[type='checkbox']")
        )
        self.scroll_and_click(switch)

    def is_switch_checked(self, field_testid: str) -> bool:
        switch = self.driver.find_element(
            By.CSS_SELECTOR, f"[data-testid='form-field-{field_testid}'] input[type='checkbox']"
        )
        return switch.is_selected()

    # ── Keyboard navigation ────────────────────────────────────────────

    def focus_row_and_press_enter(self, index: int) -> None:
        """Tab to a row and press Enter."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        if index < len(rows):
            rows[index].send_keys(Keys.ENTER)

    # ── Pagination ─────────────────────────────────────────────────────

    def get_rows_per_page_options(self) -> list[str]:
        """Return available page size options (MUI TablePagination)."""
        # MUI pagination select
        elements = self.driver.find_elements(
            By.CSS_SELECTOR, ".MuiTablePagination-select option"
        )
        return [e.text for e in elements]
