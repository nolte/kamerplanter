"""Page object for the Disease list page (REQ-010)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class DiseaseListPage(BasePage):
    """Interact with the Disease list page (``/pflanzenschutz/diseases``)."""

    PATH = "/pflanzenschutz/diseases"

    # -- Page-level locators --------------------------------------------------
    PAGE = (By.CSS_SELECTOR, "[data-testid='disease-list-page']")
    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")
    INTRO_TEXT = (By.CSS_SELECTOR, "[data-testid='disease-list-page'] .MuiTypography-body2")
    CREATE_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-button']")
    TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")
    SEARCH_INPUT = (By.CSS_SELECTOR, "[data-testid='table-search-input'] input")
    SEARCH_CHIP = (By.CSS_SELECTOR, "[data-testid='search-chip']")
    SORT_CHIP = (By.CSS_SELECTOR, "[data-testid='sort-chip']")
    RESET_FILTERS = (By.CSS_SELECTOR, "[data-testid='reset-filters-button']")
    SHOWING_COUNT = (By.CSS_SELECTOR, "[data-testid='showing-count']")
    EMPTY_STATE = (By.CSS_SELECTOR, "[data-testid='empty-state']")
    NO_RESULTS = (By.CSS_SELECTOR, "[data-testid='no-results']")

    # -- Create dialog locators -----------------------------------------------
    CREATE_DIALOG = (By.CSS_SELECTOR, "div[role='dialog']")

    # -- Create form field locators -------------------------------------------
    FORM_SCIENTIFIC_NAME = (By.CSS_SELECTOR, "[data-testid='form-field-scientific_name'] input")
    FORM_COMMON_NAME = (By.CSS_SELECTOR, "[data-testid='form-field-common_name'] input")
    FORM_PATHOGEN_TYPE = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-pathogen_type'] .MuiSelect-select",
    )
    FORM_INCUBATION_PERIOD_DAYS = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-incubation_period_days'] input",
    )
    FORM_ENVIRONMENTAL_TRIGGERS = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-environmental_triggers'] input",
    )
    FORM_AFFECTED_PLANT_PARTS = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-affected_plant_parts'] input",
    )
    FORM_DESCRIPTION = (By.CSS_SELECTOR, "[data-testid='form-field-description'] textarea")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> DiseaseListPage:
        """Navigate to the disease list and wait for it to load."""
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        return self

    # -- Table interactions ---------------------------------------------------

    def get_page_title_text(self) -> str:
        """Return the page title text."""
        return self.wait_for_element(self.PAGE_TITLE).text

    def has_intro_text(self) -> bool:
        """Return True if an introductory description text is visible."""
        elements = self.driver.find_elements(*self.INTRO_TEXT)
        return len(elements) > 0 and elements[0].is_displayed()

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

    def click_column_header(self, header_text: str) -> None:
        """Click a column header by its text to trigger sorting."""
        headers = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='data-table'] th")
        for h in headers:
            if h.text == header_text:
                self.scroll_and_click(h)
                return
        raise ValueError(f"Column header '{header_text}' not found")

    def get_chip_colors_in_column(self, col_index: int) -> list[str]:
        """Return the MUI chip color names for a given column index."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        colors = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) > col_index:
                chips = cells[col_index].find_elements(By.CSS_SELECTOR, ".MuiChip-root")
                for chip in chips:
                    cls = chip.get_attribute("class") or ""
                    for color in ("success", "warning", "error", "info", "secondary", "primary", "default"):
                        if f"MuiChip-color{color.capitalize()}" in cls:
                            colors.append(color)
                            break
                    else:
                        colors.append("default")
        return colors

    def get_chip_texts_in_column(self, col_index: int) -> list[str]:
        """Return the chip label texts for a given column index across all rows."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        texts = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) > col_index:
                chips = cells[col_index].find_elements(By.CSS_SELECTOR, ".MuiChip-label")
                for chip in chips:
                    texts.append(chip.text)
        return texts

    # -- Search and filter ----------------------------------------------------

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

    def get_showing_count_text(self) -> str:
        el = self.wait_for_element(self.SHOWING_COUNT)
        return el.text

    def has_empty_state(self) -> bool:
        return len(self.driver.find_elements(*self.EMPTY_STATE)) > 0

    def has_no_results(self) -> bool:
        """Return True if the 'no results' message is displayed."""
        elements = self.driver.find_elements(*self.NO_RESULTS)
        return len(elements) > 0 and elements[0].is_displayed()

    # -- Create dialog --------------------------------------------------------

    def click_create(self) -> None:
        """Click the Create button and wait for the dialog."""
        self.wait_for_element_clickable(self.CREATE_BUTTON).click()
        self.wait_for_element_visible(self.CREATE_DIALOG)

    def is_create_dialog_open(self) -> bool:
        return len(self.driver.find_elements(*self.CREATE_DIALOG)) > 0

    def fill_scientific_name(self, name: str) -> None:
        el = self.wait_for_element_clickable(self.FORM_SCIENTIFIC_NAME)
        el.clear()
        el.send_keys(name)

    def fill_common_name(self, name: str) -> None:
        el = self.wait_for_element_clickable(self.FORM_COMMON_NAME)
        el.clear()
        el.send_keys(name)

    def select_pathogen_type(self, label_text: str) -> None:
        """Select a pathogen type by its visible label."""
        self._select_option("pathogen_type", label_text)

    def fill_incubation_period_days(self, days: int) -> None:
        el = self.wait_for_element_clickable(self.FORM_INCUBATION_PERIOD_DAYS)
        el.clear()
        el.send_keys(str(days))

    def add_environmental_trigger(self, text: str) -> None:
        """Type a trigger in the chip input and press Enter to create a chip."""
        el = self.wait_for_element_clickable(self.FORM_ENVIRONMENTAL_TRIGGERS)
        el.send_keys(text)
        el.send_keys(Keys.ENTER)

    def add_affected_plant_part(self, text: str) -> None:
        """Type a plant part in the chip input and press Enter to create a chip."""
        el = self.wait_for_element_clickable(self.FORM_AFFECTED_PLANT_PARTS)
        el.send_keys(text)
        el.send_keys(Keys.ENTER)

    def fill_description(self, text: str) -> None:
        el = self.wait_for_element_clickable(self.FORM_DESCRIPTION)
        el.clear()
        el.send_keys(text)

    def submit_create_form(self) -> None:
        """Submit the create form."""
        self.wait_for_element_clickable(self.FORM_SUBMIT).click()

    def wait_for_dialog_closed(self, timeout: int = 15) -> None:
        """Wait until the create dialog is no longer in the DOM."""
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        WebDriverWait(self.driver, timeout).until(
            EC.invisibility_of_element_located(self.CREATE_DIALOG)
        )

    def cancel_create_form(self) -> None:
        """Cancel the create dialog."""
        self.wait_for_element_clickable(self.FORM_CANCEL).click()

    def get_validation_error(self, field_name: str) -> str:
        """Return the validation error text for a form field.

        Checks for both MUI error-class patterns:
        - ``Mui-error`` (global state class, MUI 5/6 style)
        - ``MuiFormHelperText-error`` (component-specific, MUI 7 style)
        """
        locators = [
            f"[data-testid='form-field-{field_name}'] .MuiFormHelperText-root.Mui-error",
            f"[data-testid='form-field-{field_name}'] .MuiFormHelperText-root.MuiFormHelperText-error",
        ]
        for css in locators:
            elements = self.driver.find_elements(By.CSS_SELECTOR, css)
            if elements:
                return elements[0].text
        return ""

    def has_validation_error(self, field_name: str) -> bool:
        """Return True if a validation error is visible for *field_name*.

        Uses a short explicit wait to give react-hook-form time to render errors.
        """
        from selenium.webdriver.support.ui import WebDriverWait

        def _check(_driver):
            return bool(self.get_validation_error(field_name))

        try:
            WebDriverWait(self.driver, 3).until(_check)
            return True
        except Exception:
            return False

    # -- Internal helpers -----------------------------------------------------

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
