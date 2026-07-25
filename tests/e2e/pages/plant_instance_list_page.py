"""Page object for the Plant Instance list page."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class PlantInstanceListPage(BasePage):
    """Interact with the Plant Instances list (``/pflanzen/plant-instances``)."""

    PATH = "/pflanzen/plant-instances"

    # ── Page-level locators ────────────────────────────────────────────
    PAGE = (By.CSS_SELECTOR, "[data-testid='plant-instance-list-page']")
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
    CREATE_DIALOG = (By.CSS_SELECTOR, ".MuiDialog-root [role='dialog']")
    FORM_SPECIES = (By.CSS_SELECTOR, "[data-testid='form-field-species_key']")
    FORM_SPECIES_INPUT = (By.CSS_SELECTOR, "[data-testid='form-field-species_key'] input")
    FORM_PLANT_NAME = (By.CSS_SELECTOR, "[data-testid='form-field-plant_name'] input")
    FORM_INSTANCE_ID = (By.CSS_SELECTOR, "[data-testid='form-field-instance_id'] input")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> PlantInstanceListPage:
        """Navigate to the plant instances list and wait for it to load."""
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
        """Return the text of the first column (Name) for all rows."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        texts = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if cells:
                texts.append(cells[0].text)
        return texts

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

    def click_column_header(self, header_text: str) -> None:
        """Click a column header by its text to trigger sorting."""
        headers = self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='data-table'] th"
        )
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
        """Return True if the search chip is visible."""
        return len(self.driver.find_elements(*self.SEARCH_CHIP)) > 0

    def has_sort_chip(self) -> bool:
        """Return True if the sort chip is visible."""
        return len(self.driver.find_elements(*self.SORT_CHIP)) > 0

    def click_reset_filters(self) -> None:
        """Click the reset filters button."""
        self.wait_for_element_clickable(self.RESET_FILTERS).click()

    def has_reset_filters_button(self) -> bool:
        """Return True if the reset-filters button is visible."""
        return len(self.driver.find_elements(*self.RESET_FILTERS)) > 0

    def get_showing_count_text(self) -> str:
        """Return the text of the showing-count element."""
        el = self.wait_for_element(self.SHOWING_COUNT)
        return el.text

    def has_empty_state(self) -> bool:
        """Return True if the empty state element is visible."""
        return len(self.driver.find_elements(*self.EMPTY_STATE)) > 0

    # ── Create dialog ──────────────────────────────────────────────────

    def click_create(self) -> None:
        """Click the Create button and wait for the dialog."""
        self.wait_for_element_clickable(self.CREATE_BUTTON).click()
        self.wait_for_element_visible(self.CREATE_DIALOG)

    def is_create_dialog_open(self) -> bool:
        """Return True if the create dialog is currently open."""
        return len(self.driver.find_elements(*self.CREATE_DIALOG)) > 0

    def select_species(self, search_text: str) -> None:
        """Select a species in the SpeciesAutocompleteField by typing and picking the first option.

        The MUI Autocomplete requires typing to filter, then clicking the
        matching option from the dropdown listbox.
        """
        import time

        species_input = self.wait_for_element_clickable(self.FORM_SPECIES_INPUT)
        species_input.clear()
        species_input.send_keys(search_text)
        # bounded: MUI Autocomplete filters with a ~300ms client-side debounce
        # that exposes no DOM transition, so allow it to settle before picking
        time.sleep(0.5)

        option = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, "li[role='option']")
        )
        option.click()
        self.wait_for_element_hidden((By.CSS_SELECTOR, "li[role='option']"))

    def fill_plant_name(self, name: str) -> None:
        """Fill the plant_name field in the create dialog."""
        el = self.wait_for_element_clickable(self.FORM_PLANT_NAME)
        self.clear_and_fill(el, name)

    def get_instance_id_value(self) -> str:
        """Return the current value of the instance_id field."""
        el = self.wait_for_element(self.FORM_INSTANCE_ID)
        return el.get_attribute("value") or ""

    def set_instance_id(self, instance_id: str) -> None:
        """Overwrite the auto-generated instance_id with an explicit value.

        Used by the self-provisioning core-lifecycle journeys to give the
        freshly created plant a recognizable, unique instance id so a later
        search can locate exactly this row.
        """
        el = self.wait_for_element_clickable(self.FORM_INSTANCE_ID)
        self.clear_and_fill(el, instance_id)

    def select_current_phase_by_index(self, index: int) -> None:
        """Select an entry in the 'Aktuelle Phase' (current_phase_key) MUI Select.

        Picks the option at *index* from the rendered option list. Negative
        indices count from the end (e.g. ``-2`` selects the second-to-last
        phase, useful to start a plant in a late phase such as 'flowering'
        for the Ist-Stand journey).
        """
        field = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, "[data-testid='form-field-current_phase_key'] .MuiSelect-select")
        )
        self.scroll_and_click(field)
        options = self.driver.find_elements(By.CSS_SELECTOR, "li[role='option']")
        if options:
            options[index].click()
        # MUI auto-closes on option click; ensure the popover is fully gone
        self.close_mui_dropdown()

    def get_current_phase_option_count(self) -> int:
        """Return how many options the current-phase select currently offers."""
        from selenium.webdriver.support.ui import WebDriverWait

        field = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, "[data-testid='form-field-current_phase_key'] .MuiSelect-select")
        )
        self.scroll_and_click(field)
        try:
            WebDriverWait(self.driver, 5).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, "li[role='option']")) > 0
            )
        except Exception:
            pass
        count = len(self.driver.find_elements(By.CSS_SELECTOR, "li[role='option']"))
        self.close_mui_dropdown()
        return count

    def submit_create_form(self) -> None:
        """Submit the create form."""
        self.wait_and_click(self.FORM_SUBMIT)

    def cancel_create_form(self) -> None:
        """Cancel the create dialog."""
        self.wait_and_click(self.FORM_CANCEL)

    def has_validation_error(self, field_name: str) -> bool:
        """Return True if a validation error is visible for *field_name*."""
        locator = (
            By.CSS_SELECTOR,
            f"[data-testid='form-field-{field_name}'] .MuiFormHelperText-root.Mui-error",
        )
        elements = self.driver.find_elements(*locator)
        return len(elements) > 0
