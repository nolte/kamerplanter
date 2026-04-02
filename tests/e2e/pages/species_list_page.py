"""Page object for the Species list page."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class SpeciesListPage(BasePage):
    """Interact with the Species list (``/stammdaten/species``)."""

    PATH = "/stammdaten/species"

    PAGE = (By.CSS_SELECTOR, "[data-testid='species-list-page']")
    CREATE_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-button']")
    TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")
    SEARCH_INPUT = (By.CSS_SELECTOR, "[data-testid='table-search-input'] input")
    SHOWING_COUNT = (By.CSS_SELECTOR, "[data-testid='showing-count']")
    EMPTY_STATE = (By.CSS_SELECTOR, "[data-testid='empty-state']")
    NEXT_PAGE = (By.CSS_SELECTOR, "[aria-label='Go to next page']")
    CREATE_DIALOG = (By.CSS_SELECTOR, "[data-testid='create-dialog']")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self, via_sidebar: bool = False) -> SpeciesListPage:
        if via_sidebar:
            self.navigate_via_sidebar(self.PATH)
        else:
            self.navigate(self.PATH)
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        return self

    def get_row_count(self) -> int:
        return len(self.driver.find_elements(*self.TABLE_ROWS))

    def get_first_column_texts(self) -> list[str]:
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
        """Click the row whose scientific name matches *name*.

        The species table has a star/favorite column at index 0 (empty text),
        so we search across all cells rather than only the first one.
        """
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            for cell in cells:
                if cell.text == name:
                    self.scroll_and_click(row)
                    return
        raise ValueError(f"Row with name '{name}' not found")

    def has_empty_state(self) -> bool:
        return len(self.driver.find_elements(*self.EMPTY_STATE)) > 0

    def click_next_page(self) -> None:
        self.wait_for_element_clickable(self.NEXT_PAGE).click()

    def get_column_headers(self) -> list[str]:
        headers = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='data-table'] th")
        return [h.text for h in headers if h.text]

    # ── Create dialog ──────────────────────────────────────────────────

    def click_create(self) -> None:
        self.wait_for_element_clickable(self.CREATE_BUTTON).click()
        self.wait_for_element_visible(self.CREATE_DIALOG)
        self.expand_all_fields()

    def fill_scientific_name(self, name: str) -> None:
        el = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, "[data-testid='form-field-scientific_name'] input")
        )
        el.clear()
        el.send_keys(name)

    def set_field(self, field_name: str, value: str) -> None:
        el = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] input")
        )
        el.clear()
        el.send_keys(value)

    def select_option(self, field_name: str, value_text: str) -> None:
        import time
        from selenium.webdriver.common.keys import Keys

        field = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] .MuiSelect-select")
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

    def add_chip(self, field_name: str, value: str) -> None:
        from selenium.webdriver.common.keys import Keys

        el = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] input")
        )
        el.send_keys(value)
        el.send_keys(Keys.ENTER)

    def submit_form(self) -> None:
        self.wait_for_element_clickable(self.FORM_SUBMIT).click()

    def cancel_form(self) -> None:
        self.wait_for_element_clickable(self.FORM_CANCEL).click()

    def is_create_dialog_open(self) -> bool:
        return len(self.driver.find_elements(*self.CREATE_DIALOG)) > 0

    def has_validation_error(self, field_name: str) -> bool:
        locator = (By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] .MuiFormHelperText-root.Mui-error")
        return len(self.driver.find_elements(*locator)) > 0
