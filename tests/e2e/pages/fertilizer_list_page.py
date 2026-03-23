"""Page object for the Fertilizer list page (REQ-004)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from .base_page import BasePage


class FertilizerListPage(BasePage):
    """Interact with the Fertilizer list (``/duengung/fertilizers``)."""

    PATH = "/duengung/fertilizers"

    # Locators — data-testid first per NFR-008 §3.2
    PAGE = (By.CSS_SELECTOR, "[data-testid='fertilizer-list-page']")
    CREATE_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-button']")
    TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")
    SEARCH_INPUT = (By.CSS_SELECTOR, "[data-testid='table-search-input'] input")
    SEARCH_CHIP = (By.CSS_SELECTOR, "[data-testid='search-chip']")
    SORT_CHIP = (By.CSS_SELECTOR, "[data-testid='sort-chip']")
    RESET_FILTERS = (By.CSS_SELECTOR, "[data-testid='reset-filters-button']")
    SHOWING_COUNT = (By.CSS_SELECTOR, "[data-testid='showing-count']")
    EMPTY_STATE = (By.CSS_SELECTOR, "[data-testid='empty-state']")

    # Create dialog
    FORM_PRODUCT_NAME = (By.CSS_SELECTOR, "[data-testid='form-field-product_name'] input")
    FORM_BRAND = (By.CSS_SELECTOR, "[data-testid='form-field-brand'] input")
    FORM_NPK_N = (By.CSS_SELECTOR, "[data-testid='form-field-npk_n'] input")
    FORM_NPK_P = (By.CSS_SELECTOR, "[data-testid='form-field-npk_p'] input")
    FORM_NPK_K = (By.CSS_SELECTOR, "[data-testid='form-field-npk_k'] input")
    FORM_EC_CONTRIBUTION = (By.CSS_SELECTOR, "[data-testid='form-field-ec_contribution_per_ml'] input")
    FORM_MIXING_PRIORITY = (By.CSS_SELECTOR, "[data-testid='form-field-mixing_priority'] input")
    FORM_NOTES = (By.CSS_SELECTOR, "[data-testid='form-field-notes'] textarea")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    # MUI Dialog
    CREATE_DIALOG = (By.CSS_SELECTOR, ".MuiDialog-root")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> FertilizerListPage:
        """Navigate to the fertilizer list and wait for it to load."""
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        return self

    # ── Table interactions ─────────────────────────────────────────────

    def get_row_count(self) -> int:
        """Return the number of visible data rows."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        return len(rows)

    def get_first_column_texts(self) -> list[str]:
        """Return the text of the first column (product name) for all rows."""
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

    def click_row(self, index: int) -> None:
        """Click the table row at the given index."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        if index < len(rows):
            self.scroll_and_click(rows[index])

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
        """Type a search term into the table search field."""
        search_input = self.wait_for_element_clickable(self.SEARCH_INPUT)
        self.clear_and_fill(search_input, term)

    def clear_search(self) -> None:
        """Clear the search field."""
        search_input = self.wait_for_element_clickable(self.SEARCH_INPUT)
        self.clear_and_fill(search_input, "")

    def has_search_chip(self) -> bool:
        """Return True if the search chip is visible."""
        return len(self.driver.find_elements(*self.SEARCH_CHIP)) > 0

    def has_sort_chip(self) -> bool:
        """Return True if the sort chip is visible."""
        return len(self.driver.find_elements(*self.SORT_CHIP)) > 0

    def click_reset_filters(self) -> None:
        """Click the reset filters button."""
        self.wait_for_element_clickable(self.RESET_FILTERS).click()

    def has_reset_filters_button(self) -> bool:
        """Return True if the reset filters button is present."""
        return len(self.driver.find_elements(*self.RESET_FILTERS)) > 0

    def get_showing_count_text(self) -> str:
        """Return the text of the showing count element."""
        el = self.wait_for_element(self.SHOWING_COUNT)
        return el.text

    def has_empty_state(self) -> bool:
        """Return True if the empty state is shown."""
        return len(self.driver.find_elements(*self.EMPTY_STATE)) > 0

    # ── Create dialog ──────────────────────────────────────────────────

    def click_create(self) -> None:
        """Click the create button and wait for the dialog to appear."""
        self.wait_for_element_clickable(self.CREATE_BUTTON).click()
        self.wait_for_element_visible(self.CREATE_DIALOG)

    def is_create_dialog_open(self) -> bool:
        """Return True if the create dialog is visible."""
        dialogs = self.driver.find_elements(*self.CREATE_DIALOG)
        return any(d.is_displayed() for d in dialogs)

    def fill_product_name(self, name: str) -> None:
        """Fill the product name field."""
        el = self.wait_for_element_clickable(self.FORM_PRODUCT_NAME)
        self.clear_and_fill(el, name)

    def fill_brand(self, brand: str) -> None:
        """Fill the brand field."""
        el = self.wait_for_element_clickable(self.FORM_BRAND)
        self.clear_and_fill(el, brand)

    def fill_npk(self, n: float, p: float, k: float) -> None:
        """Fill the NPK N, P, K fields."""
        for locator, value in [
            (self.FORM_NPK_N, str(n)),
            (self.FORM_NPK_P, str(p)),
            (self.FORM_NPK_K, str(k)),
        ]:
            el = self.wait_for_element_clickable(locator)
            self.clear_and_fill(el, value)

    def fill_ec_contribution(self, value: float) -> None:
        """Fill the EC contribution field."""
        el = self.wait_for_element_clickable(self.FORM_EC_CONTRIBUTION)
        self.clear_and_fill(el, str(value))

    def fill_mixing_priority(self, value: int) -> None:
        """Fill the mixing priority field."""
        el = self.wait_for_element_clickable(self.FORM_MIXING_PRIORITY)
        self.clear_and_fill(el, str(value))

    def fill_notes(self, notes: str) -> None:
        """Fill the notes textarea."""
        el = self.wait_for_element_clickable(self.FORM_NOTES)
        self.clear_and_fill(el, notes)

    def select_fertilizer_type(self, value_text: str) -> None:
        """Open the fertilizer type select and pick an option."""
        field = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, "[data-testid='form-field-fertilizer_type'] .MuiSelect-select")
        )
        self.scroll_and_click(field)
        option = self.wait_for_element_clickable(
            (By.XPATH, f"//li[@role='option' and contains(text(), '{value_text}')]")
        )
        option.click()

    def select_ph_effect(self, value_text: str) -> None:
        """Open the pH effect select and pick an option."""
        field = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, "[data-testid='form-field-ph_effect'] .MuiSelect-select")
        )
        self.scroll_and_click(field)
        option = self.wait_for_element_clickable(
            (By.XPATH, f"//li[@role='option' and contains(text(), '{value_text}')]")
        )
        option.click()

    def submit_create_form(self) -> None:
        """Submit the create form."""
        self.wait_for_element_clickable(self.FORM_SUBMIT).click()

    def cancel_create_form(self) -> None:
        """Cancel the create form."""
        self.wait_for_element_clickable(self.FORM_CANCEL).click()

    def get_product_name_field_value(self) -> str:
        """Return the current value of the product_name input."""
        el = self.wait_for_element(self.FORM_PRODUCT_NAME)
        return el.get_attribute("value") or ""

    def get_validation_error(self, field_name: str) -> str:
        """Return the validation error text for a given form field."""
        locator = (
            By.CSS_SELECTOR,
            f"[data-testid='form-field-{field_name}'] .MuiFormHelperText-root.Mui-error",
        )
        elements = self.driver.find_elements(*locator)
        return elements[0].text if elements else ""

    def has_validation_error(self, field_name: str) -> bool:
        """Return True if a validation error is shown for the field."""
        return bool(self.get_validation_error(field_name))
