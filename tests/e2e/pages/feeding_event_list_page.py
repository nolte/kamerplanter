"""Page object for the Feeding Event list page (REQ-004)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class FeedingEventListPage(BasePage):
    """Interact with the Feeding Event list (``/duengung/feeding-events``)."""

    PATH = "/duengung/feeding-events"

    # Locators -- data-testid first per NFR-008 sec. 3.2
    PAGE = (By.CSS_SELECTOR, "[data-testid='feeding-event-list-page']")
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
    CREATE_DIALOG = (By.CSS_SELECTOR, ".MuiDialog-root")
    FORM_PLANT_KEY = (By.CSS_SELECTOR, "[data-testid='form-field-plant_key']")
    FORM_PLANT_KEY_SELECT = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-plant_key'] .MuiSelect-select",
    )
    FORM_APPLICATION_METHOD = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-application_method'] .MuiSelect-select",
    )
    FORM_VOLUME = (By.CSS_SELECTOR, "[data-testid='form-field-volume_applied_liters'] input")
    FORM_IS_SUPPLEMENTAL = (By.CSS_SELECTOR, "[data-testid='form-field-is_supplemental']")
    FORM_EC_BEFORE = (By.CSS_SELECTOR, "[data-testid='form-field-measured_ec_before'] input")
    FORM_EC_AFTER = (By.CSS_SELECTOR, "[data-testid='form-field-measured_ec_after'] input")
    FORM_PH_BEFORE = (By.CSS_SELECTOR, "[data-testid='form-field-measured_ph_before'] input")
    FORM_PH_AFTER = (By.CSS_SELECTOR, "[data-testid='form-field-measured_ph_after'] input")
    FORM_RUNOFF_EC = (By.CSS_SELECTOR, "[data-testid='form-field-runoff_ec'] input")
    FORM_RUNOFF_PH = (By.CSS_SELECTOR, "[data-testid='form-field-runoff_ph'] input")
    FORM_RUNOFF_VOLUME = (By.CSS_SELECTOR, "[data-testid='form-field-runoff_volume_liters'] input")
    FORM_NOTES = (By.CSS_SELECTOR, "[data-testid='form-field-notes'] textarea")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> FeedingEventListPage:
        """Navigate to the feeding event list and wait for it to load."""
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        return self

    # -- Table interactions ------------------------------------------------

    def get_row_count(self) -> int:
        """Return the number of visible data rows."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        return len(rows)

    def get_column_headers(self) -> list[str]:
        """Return all visible column header texts."""
        headers = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='data-table'] th")
        return [h.text for h in headers if h.text]

    def get_first_column_texts(self) -> list[str]:
        """Return text of the first column for all visible rows."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        texts = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if cells:
                texts.append(cells[0].text)
        return texts

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

    # -- Search and filter -------------------------------------------------

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

    def has_empty_state(self) -> bool:
        """Return True if the empty state is shown."""
        return len(self.driver.find_elements(*self.EMPTY_STATE)) > 0

    def get_showing_count_text(self) -> str:
        """Return the text of the showing count element."""
        el = self.wait_for_element(self.SHOWING_COUNT)
        return el.text

    # -- Create dialog -----------------------------------------------------

    def click_create(self) -> None:
        """Click the create button and wait for the dialog to appear."""
        self.wait_for_element_clickable(self.CREATE_BUTTON).click()
        self.wait_for_element_visible(self.CREATE_DIALOG)

    def is_create_dialog_open(self) -> bool:
        """Return True if the create dialog is visible."""
        dialogs = self.driver.find_elements(*self.CREATE_DIALOG)
        return any(d.is_displayed() for d in dialogs)

    def select_plant(self, option_text: str) -> None:
        """Open the plant_key select and pick an option by label text."""
        from selenium.webdriver.common.keys import Keys

        field = self.wait_for_element_clickable(self.FORM_PLANT_KEY_SELECT)
        self.scroll_and_click(field)
        option = self.wait_for_element_clickable(
            (By.XPATH, f"//li[@role='option' and contains(text(), '{option_text}')]")
        )
        option.click()
        self.close_mui_dropdown()

    def select_application_method(self, option_text: str) -> None:
        """Open the application_method select and pick an option."""
        field = self.wait_for_element_clickable(self.FORM_APPLICATION_METHOD)
        self.scroll_and_click(field)
        option = self.wait_for_element_clickable(
            (By.XPATH, f"//li[@role='option' and contains(text(), '{option_text}')]")
        )
        option.click()
        self.close_mui_dropdown()

    def fill_volume(self, value: float) -> None:
        """Fill the volume_applied_liters field."""
        el = self.wait_for_element_clickable(self.FORM_VOLUME)
        self.clear_and_fill(el, str(value))

    def fill_ec_before(self, value: float) -> None:
        """Fill the measured_ec_before field."""
        el = self.wait_for_element_clickable(self.FORM_EC_BEFORE)
        self.clear_and_fill(el, str(value))

    def fill_ec_after(self, value: float) -> None:
        """Fill the measured_ec_after field."""
        el = self.wait_for_element_clickable(self.FORM_EC_AFTER)
        self.clear_and_fill(el, str(value))

    def fill_notes(self, notes: str) -> None:
        """Fill the notes textarea."""
        el = self.wait_for_element_clickable(self.FORM_NOTES)
        self.clear_and_fill(el, notes)

    def submit_create_form(self) -> None:
        """Submit the create form."""
        self.wait_for_element_clickable(self.FORM_SUBMIT).click()

    def cancel_create_form(self) -> None:
        """Cancel the create form."""
        self.wait_for_element_clickable(self.FORM_CANCEL).click()

    def get_volume_field_value(self) -> str:
        """Return the current value of the volume input."""
        el = self.wait_for_element(self.FORM_VOLUME)
        return el.get_attribute("value") or ""

    def has_plant_key_field(self) -> bool:
        """Return True if the plant_key form field is present."""
        return len(self.driver.find_elements(*self.FORM_PLANT_KEY)) > 0

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
