"""Extended Page object for the Site list page (REQ-002 full coverage).

This module provides SiteListPageExt which extends the existing SiteListPage
with form-filling, search, sort, and dialog validation capabilities needed
for the REQ-002 test suite.
"""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from .base_page import BasePage


class SiteListPageExt(BasePage):
    """Full Page Object for the Site list page (``/standorte/sites``).

    Covers REQ-002 acceptance criteria:
    - List with DataTable (search, sort, filter reset)
    - Create dialog with form validation
    - Row click → detail navigation
    """

    PATH = "/standorte/sites"

    # ── Page root ──────────────────────────────────────────────────────
    PAGE = (By.CSS_SELECTOR, "[data-testid='site-list-page']")
    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")
    CREATE_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-button']")

    # ── Content locators (Site cards or DataTable rows) ─────────────────
    TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")
    SITE_CARDS = (By.CSS_SELECTOR, "[data-testid^='site-card-']")
    SEARCH_INPUT = (By.CSS_SELECTOR, "[data-testid='table-search-input'] input")
    SEARCH_CHIP = (By.CSS_SELECTOR, "[data-testid='search-chip']")
    SORT_CHIP = (By.CSS_SELECTOR, "[data-testid='sort-chip']")
    RESET_FILTERS = (By.CSS_SELECTOR, "[data-testid='reset-filters-button']")
    SHOWING_COUNT = (By.CSS_SELECTOR, "[data-testid='showing-count']")
    EMPTY_STATE = (By.CSS_SELECTOR, "[data-testid='empty-state']")
    NO_SEARCH_RESULTS = (By.CSS_SELECTOR, "[data-testid='no-search-results']")

    # ── Create dialog (SiteCreateDialog — no explicit data-testid on dialog) ──
    # The Dialog wraps form fields with form-field-* testids
    CREATE_DIALOG_TITLE = (By.XPATH, "//div[@role='dialog']//h2")
    FORM_NAME = (By.CSS_SELECTOR, "[data-testid='form-field-name'] input")
    FORM_TYPE = (By.CSS_SELECTOR, "[data-testid='form-field-type']")
    FORM_CLIMATE_ZONE = (By.CSS_SELECTOR, "[data-testid='form-field-climate_zone'] input")
    FORM_TOTAL_AREA = (By.CSS_SELECTOR, "[data-testid='form-field-total_area_m2'] input")
    FORM_TIMEZONE = (By.CSS_SELECTOR, "[data-testid='form-field-timezone'] input")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    # ── Navigation ─────────────────────────────────────────────────────

    def open(self, via_sidebar: bool = False, retries: int = 2) -> SiteListPageExt:
        from selenium.common.exceptions import StaleElementReferenceException
        from selenium.webdriver.support.ui import WebDriverWait
        import time

        for attempt in range(retries + 1):
            try:
                if via_sidebar:
                    self.navigate_via_sidebar(self.PATH)
                else:
                    self.navigate(self.PATH)
                self.wait_for_element(self.PAGE)
                self.wait_for_loading_complete()
                # Wait for content to render (DataTable rows, site cards, or empty state)
                WebDriverWait(self.driver, 10).until(
                    lambda d: (d.find_elements(*self.TABLE_ROWS)
                               or d.find_elements(*self.SITE_CARDS)
                               or d.find_elements(*self.EMPTY_STATE))
                )
                return self
            except StaleElementReferenceException:
                if attempt >= retries:
                    raise
                time.sleep(0.5)
        return self  # unreachable, keeps type checker happy

    # ── Table queries ──────────────────────────────────────────────────

    def get_row_count(self) -> int:
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        if rows:
            return len(rows)
        # Fallback: card-based layout
        cards = self.driver.find_elements(*self.SITE_CARDS)
        return len(cards)

    def get_first_column_texts(self) -> list[str]:
        """Return the text of the first column (Name) for each visible row."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        result: list[str] = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if cells:
                result.append(cells[0].text)
        return result

    def get_column_headers(self) -> list[str]:
        headers = self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='data-table'] th"
        )
        return [h.text for h in headers if h.text]

    def click_column_header(self, header_text: str) -> None:
        """Click a table column header to trigger sorting."""
        headers = self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='data-table'] th"
        )
        for h in headers:
            if h.text == header_text:
                self.scroll_and_click(h)
                return
        raise ValueError(f"Column header '{header_text}' not found")

    def click_row(self, index: int) -> None:
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        if rows and index < len(rows):
            self.scroll_and_click(rows[index])
            return
        # Fallback: card-based layout — click the site name link inside the card
        cards = self.driver.find_elements(*self.SITE_CARDS)
        if cards and index < len(cards):
            name_el = cards[index].find_element(By.CSS_SELECTOR, "[data-testid^='site-name-']")
            self.scroll_and_click(name_el)

    def click_row_by_name(self, name: str) -> None:
        """Click the table row whose first cell matches *name*."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if cells and cells[0].text == name:
                self.scroll_and_click(row)
                return
        raise ValueError(f"Row with name '{name}' not found")

    # ── Search / filter ────────────────────────────────────────────────

    def search(self, term: str) -> None:
        search_input = self.wait_for_element_clickable(self.SEARCH_INPUT)
        search_input.clear()
        search_input.send_keys(term)

    def clear_search(self) -> None:
        search_input = self.wait_for_element_clickable(self.SEARCH_INPUT)
        search_input.send_keys(Keys.CONTROL + "a")
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

    def has_no_search_results(self) -> bool:
        return len(self.driver.find_elements(*self.NO_SEARCH_RESULTS)) > 0

    # ── Create dialog ──────────────────────────────────────────────────

    def click_create(self) -> None:
        """Click the 'Anlegen' button and wait for the form fields to appear."""
        self.wait_for_element_clickable(self.CREATE_BUTTON).click()
        # Wait for dialog form field to become visible
        self.wait_for_element_visible(self.FORM_NAME)

    def fill_name(self, name: str) -> None:
        el = self.wait_for_element_clickable(self.FORM_NAME)
        el.clear()
        el.send_keys(name)

    def fill_climate_zone(self, value: str) -> None:
        el = self.wait_for_element_clickable(self.FORM_CLIMATE_ZONE)
        el.clear()
        el.send_keys(value)

    def fill_total_area(self, value: str) -> None:
        el = self.wait_for_element_clickable(self.FORM_TOTAL_AREA)
        el.clear()
        el.send_keys(value)

    def fill_timezone(self, value: str) -> None:
        el = self.wait_for_element_clickable(self.FORM_TIMEZONE)
        el.clear()
        el.send_keys(value)

    def select_type(self, value_text: str) -> None:
        """Open MUI Select for 'type' and pick option by visible text."""
        import time

        select_el = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, "[data-testid='form-field-type'] .MuiSelect-select")
        )
        self.scroll_and_click(select_el)
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
        self.wait_for_element_clickable(self.FORM_SUBMIT).click()

    def cancel_create_form(self) -> None:
        self.wait_for_element_clickable(self.FORM_CANCEL).click()

    def is_create_dialog_open(self) -> bool:
        """Check whether the create dialog form fields are visible."""
        try:
            elements = self.driver.find_elements(*self.FORM_NAME)
            return bool(elements) and elements[0].is_displayed()
        except Exception:
            return False

    def get_name_field_value(self) -> str:
        el = self.wait_for_element(self.FORM_NAME)
        return el.get_attribute("value") or ""

    def get_validation_error(self, field_name: str) -> str:
        """Return text of a Zod/MUI validation error for a form field."""
        locator = (
            By.CSS_SELECTOR,
            f"[data-testid='form-field-{field_name}'] .MuiFormHelperText-root.Mui-error",
        )
        elements = self.driver.find_elements(*locator)
        return elements[0].text if elements else ""

    def has_validation_error(self, field_name: str) -> bool:
        return bool(self.get_validation_error(field_name))
