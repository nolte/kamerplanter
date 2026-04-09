"""Page object for the Watering Log list page (REQ-004)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class WateringLogListPage(BasePage):
    """Interact with the Watering Log list page (``/giessprotokoll``)."""

    PATH = "/giessprotokoll"

    # -- Page-level locators ------------------------------------------------
    PAGE = (By.CSS_SELECTOR, "[data-testid='watering-log-list-page']")
    CREATE_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-watering-log-button']")
    TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")
    SEARCH_INPUT = (By.CSS_SELECTOR, "[data-testid='table-search-input'] input")
    SEARCH_CHIP = (By.CSS_SELECTOR, "[data-testid='search-chip']")
    SORT_CHIP = (By.CSS_SELECTOR, "[data-testid='sort-chip']")
    RESET_FILTERS = (By.CSS_SELECTOR, "[data-testid='reset-filters-button']")
    SHOWING_COUNT = (By.CSS_SELECTOR, "[data-testid='showing-count']")
    EMPTY_STATE = (By.CSS_SELECTOR, "[data-testid='empty-state']")

    # -- Create dialog locators ---------------------------------------------
    CREATE_DIALOG = (By.CSS_SELECTOR, "div[role='dialog']")
    PLANT_KEYS_INPUT = (By.CSS_SELECTOR, "[data-testid='plant-keys-input'] input")
    PLANT_KEYS_AUTOCOMPLETE = (By.CSS_SELECTOR, "[data-testid='plant-keys-autocomplete']")
    ADD_FERTILIZER_BUTTON = (By.CSS_SELECTOR, "[data-testid='add-fertilizer-button']")

    # -- Create form field locators -----------------------------------------
    FORM_APPLICATION_METHOD = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-application_method'] .MuiSelect-select",
    )
    FORM_VOLUME = (By.CSS_SELECTOR, "[data-testid='form-field-volume_liters'] input")
    FORM_WATER_SOURCE = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-water_source'] .MuiSelect-select",
    )
    FORM_IS_SUPPLEMENTAL = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-is_supplemental'] .MuiSwitch-root",
    )
    FORM_EC_BEFORE = (By.CSS_SELECTOR, "[data-testid='form-field-ec_before'] input")
    FORM_EC_AFTER = (By.CSS_SELECTOR, "[data-testid='form-field-ec_after'] input")
    FORM_PH_BEFORE = (By.CSS_SELECTOR, "[data-testid='form-field-ph_before'] input")
    FORM_PH_AFTER = (By.CSS_SELECTOR, "[data-testid='form-field-ph_after'] input")
    FORM_PERFORMED_BY = (By.CSS_SELECTOR, "[data-testid='form-field-performed_by'] input")
    FORM_NOTES = (By.CSS_SELECTOR, "[data-testid='form-field-notes'] textarea")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> WateringLogListPage:
        """Navigate to the watering log list and wait for it to load."""
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        return self

    # -- Table interactions -------------------------------------------------

    def get_row_count(self) -> int:
        """Return the number of visible table rows."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        return len(rows)

    def get_column_headers(self) -> list[str]:
        """Return all visible column header texts."""
        headers = self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='data-table'] th"
        )
        return [h.text for h in headers if h.text]

    def click_row(self, index: int = 0) -> None:
        """Click the row at *index*."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        if index < len(rows):
            self.scroll_and_click(rows[index])

    def get_row_texts(self) -> list[list[str]]:
        """Return all cell texts for every visible row."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        result = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            result.append([c.text for c in cells])
        return result

    # -- Search and filter --------------------------------------------------

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

    def has_empty_state(self) -> bool:
        """Return True if the empty state illustration is visible."""
        return len(self.driver.find_elements(*self.EMPTY_STATE)) > 0

    def get_showing_count_text(self) -> str:
        """Return the text from the 'showing X of Y' counter."""
        el = self.wait_for_element(self.SHOWING_COUNT)
        return el.text

    def click_reset_filters(self) -> None:
        """Click the reset filters button."""
        self.wait_for_element_clickable(self.RESET_FILTERS).click()

    def has_reset_filters_button(self) -> bool:
        """Return True if the reset-filters button exists."""
        return len(self.driver.find_elements(*self.RESET_FILTERS)) > 0

    # -- Create dialog ------------------------------------------------------

    def click_create(self) -> None:
        """Click the Create button and wait for the dialog."""
        self.wait_for_element_clickable(self.CREATE_BUTTON).click()
        self.wait_for_element_visible(self.CREATE_DIALOG)

    def is_create_dialog_open(self) -> bool:
        """Return True if the create dialog is visible."""
        return len(self.driver.find_elements(*self.CREATE_DIALOG)) > 0

    def select_first_plant(self) -> bool:
        """Type into the plant autocomplete and select the first option.

        Returns True if a plant was selected, False if no options appeared.
        """
        import time

        input_el = self.wait_for_element_clickable(self.PLANT_KEYS_INPUT)
        input_el.click()
        # Type a space to trigger the dropdown, then clear it
        input_el.send_keys(" ")
        time.sleep(0.3)
        input_el.clear()
        time.sleep(0.3)

        # MUI Autocomplete renders options in a listbox
        options = self.driver.find_elements(
            By.CSS_SELECTOR, "li[role='option']"
        )
        if not options:
            # Try clicking the input again to open the dropdown
            input_el.click()
            time.sleep(0.5)
            options = self.driver.find_elements(
                By.CSS_SELECTOR, "li[role='option']"
            )

        if options:
            options[0].click()
            time.sleep(0.3)
            return True
        return False

    def fill_volume(self, volume: float) -> None:
        """Fill the volume_liters field in the create dialog."""
        el = self.wait_for_element_clickable(self.FORM_VOLUME)
        self.clear_and_fill(el, str(volume))

    def select_application_method(self, label_text: str) -> None:
        """Select an application method by its visible label."""
        self.select_option("application_method", label_text)

    def select_water_source(self, label_text: str) -> None:
        """Select a water source by its visible label."""
        self.select_option("water_source", label_text)

    def fill_ec_before(self, value: float) -> None:
        """Fill the EC before field."""
        el = self.wait_for_element_clickable(self.FORM_EC_BEFORE)
        self.clear_and_fill(el, str(value))

    def fill_ph_before(self, value: float) -> None:
        """Fill the pH before field."""
        el = self.wait_for_element_clickable(self.FORM_PH_BEFORE)
        self.clear_and_fill(el, str(value))

    def fill_notes(self, notes: str) -> None:
        """Fill the Notes textarea."""
        el = self.wait_for_element_clickable(self.FORM_NOTES)
        self.clear_and_fill(el, notes)

    def submit_create_form(self) -> None:
        """Submit the create form."""
        btn = self.wait_for_element_clickable(self.FORM_SUBMIT)
        self.scroll_and_click(btn)

    def cancel_create_form(self) -> None:
        """Cancel the create dialog."""
        btn = self.wait_for_element_clickable(self.FORM_CANCEL)
        self.scroll_and_click(btn)

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
