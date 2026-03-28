"""Page object for the Nutrient Plan list page (REQ-004)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class NutrientPlanListPage(BasePage):
    """Interact with the Nutrient Plan list (``/duengung/plans``)."""

    PATH = "/duengung/plans"

    # Locators
    PAGE = (By.CSS_SELECTOR, "[data-testid='nutrient-plan-list-page']")
    CREATE_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-button']")
    TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")
    SEARCH_INPUT = (By.CSS_SELECTOR, "[data-testid='table-search-input'] input")
    SEARCH_CHIP = (By.CSS_SELECTOR, "[data-testid='search-chip']")
    SORT_CHIP = (By.CSS_SELECTOR, "[data-testid='sort-chip']")
    RESET_FILTERS = (By.CSS_SELECTOR, "[data-testid='reset-filters-button']")
    SHOWING_COUNT = (By.CSS_SELECTOR, "[data-testid='showing-count']")
    EMPTY_STATE = (By.CSS_SELECTOR, "[data-testid='empty-state']")

    # MUI Dialog (create)
    CREATE_DIALOG = (By.CSS_SELECTOR, ".MuiDialog-root")

    # Create form fields
    FORM_NAME = (By.CSS_SELECTOR, "[data-testid='form-field-name'] input")
    FORM_DESCRIPTION = (By.CSS_SELECTOR, "[data-testid='form-field-description'] textarea")
    FORM_AUTHOR = (By.CSS_SELECTOR, "[data-testid='form-field-author'] input")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> NutrientPlanListPage:
        """Navigate to the nutrient plan list and wait for it to load."""
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE, timeout=20)
        self.wait_for_loading_complete(timeout=20)
        return self

    # ── Table interactions ─────────────────────────────────────────────

    def get_row_count(self) -> int:
        """Return the number of visible data rows."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        return len(rows)

    def get_first_column_texts(self) -> list[str]:
        """Return the text of the first column (plan name) for all rows."""
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
        """Click a column header by text to trigger sorting."""
        headers = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='data-table'] th")
        for h in headers:
            if h.text == header_text:
                self.scroll_and_click(h)
                return
        raise ValueError(f"Column header '{header_text}' not found")

    # ── Clone action ───────────────────────────────────────────────────

    def click_clone_on_row(self, index: int) -> None:
        """Click the clone icon button on a given row."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        if index < len(rows):
            clone_btn = rows[index].find_element(By.CSS_SELECTOR, "button[title]")
            self.scroll_and_click(clone_btn)

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

    def get_showing_count_text(self) -> str:
        """Return the text of the showing count element."""
        el = self.wait_for_element(self.SHOWING_COUNT)
        return el.text

    def has_empty_state(self) -> bool:
        """Return True if the empty state is shown."""
        return len(self.driver.find_elements(*self.EMPTY_STATE)) > 0

    # ── Create dialog ──────────────────────────────────────────────────

    def click_create(self) -> None:
        """Click the create button and wait for the dialog."""
        self.wait_for_element_clickable(self.CREATE_BUTTON).click()
        self.wait_for_element_visible(self.CREATE_DIALOG)

    def is_create_dialog_open(self) -> bool:
        """Return True if a MUI dialog is currently visible."""
        dialogs = self.driver.find_elements(*self.CREATE_DIALOG)
        return any(d.is_displayed() for d in dialogs)

    def fill_name(self, name: str) -> None:
        """Fill the plan name field."""
        el = self.wait_for_element_clickable(self.FORM_NAME)
        self.clear_and_fill(el, name)

    def fill_description(self, description: str) -> None:
        """Fill the description textarea."""
        el = self.wait_for_element_clickable(self.FORM_DESCRIPTION)
        self.clear_and_fill(el, description)

    def fill_author(self, author: str) -> None:
        """Fill the author field."""
        el = self.wait_for_element_clickable(self.FORM_AUTHOR)
        self.clear_and_fill(el, author)

    def select_substrate_type(self, value_text: str) -> None:
        """Open the substrate type select and pick an option."""
        import time
        from selenium.webdriver.common.keys import Keys

        field = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, "[data-testid='form-field-recommended_substrate_type'] .MuiSelect-select")
        )
        self.scroll_and_click(field)
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

    def toggle_is_template(self) -> None:
        """Toggle the is_template switch."""
        switch = self.wait_for_element(
            (By.CSS_SELECTOR, "[data-testid='form-field-is_template'] input[type='checkbox']")
        )
        self.scroll_and_click(switch)

    def submit_create_form(self) -> None:
        """Submit the create form."""
        btn = self.wait_for_element(self.FORM_SUBMIT)
        self.scroll_and_click(btn)

    def cancel_create_form(self) -> None:
        """Cancel the create form."""
        btn = self.wait_for_element(self.FORM_CANCEL)
        self.scroll_and_click(btn)

    def get_name_field_value(self) -> str:
        """Return the current value of the name input field."""
        el = self.wait_for_element(self.FORM_NAME)
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
