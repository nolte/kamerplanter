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

    #: Column id of the identifying column (PlantInstanceListPage `columns`).
    INSTANCE_ID_COLUMN_ID = "instanceId"

    def get_first_column_texts(self) -> list[str]:
        """Return each visible row's identifying text.

        Addressed by column id, not by position: the leading ``<td>`` is the
        cover-photo column (empty text), so ``cells[0]`` yielded empty strings
        on the desktop table -- and an empty list in the mobile card layout,
        where there is no ``<td>`` at all. In the card layout this resolves to
        the card title (the plant's display name).
        """
        return self.get_column_texts(self.INSTANCE_ID_COLUMN_ID)

    def get_column_headers(self) -> list[str]:
        """Return all visible column header texts."""
        headers = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='data-table'] th")
        return [h.text for h in headers if h.text]

    #: Column the row is activated through. Deliberately not the row centre:
    #: the row carries a `location` link, a `plantingRun` link and an actions
    #: button, all of which `stopPropagation`. `instanceId` renders
    #: `r.instance_id` and carries no `hideBelowBreakpoint`.
    ROW_CLICK_COLUMN_ID = INSTANCE_ID_COLUMN_ID

    def click_row(self, index: int = 0) -> None:
        """Open the plant instance at *index* via its inert id cell."""
        self.click_data_table_row(
            index, self.ROW_CLICK_COLUMN_ID, self.TABLE_ROWS, "plant instance row"
        )

    # ── Search and filter ──────────────────────────────────────────────

    def search(self, term: str) -> None:
        """Type *term* into the search field.

        Uses ``clear_and_fill`` rather than ``WebElement.clear()``: the search
        box is a React-controlled input, where ``clear()`` empties the DOM value
        without notifying React, so the previous term survives and the new one is
        appended to it — the defect measured on the substrate list as #802.

        Typing is only half the post-condition. The `DataTable` filter is
        client-side behind a 300 ms debounce, so on return the table may still
        render the *previous* rows; a caller that then reads or clicks a row must
        gate on :meth:`BasePage.wait_for_search_applied` (and, when it knows
        which record it wants, :meth:`BasePage.wait_for_row_identity`). This
        method deliberately does not do that itself: several call sites search
        for a term that must match *nothing*, and a wait for a filtered row would
        be wrong there.
        """
        search_input = self.wait_for_element_clickable(self.SEARCH_INPUT)
        self.clear_and_fill(search_input, term)

    def clear_search(self) -> None:
        """Clear the search field."""
        search_input = self.wait_for_element_clickable(self.SEARCH_INPUT)
        search_input.clear()
        search_input.send_keys(Keys.BACKSPACE)

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

    def wait_for_create_dialog_closed(self) -> None:
        """Wait until the create dialog has finished fading out.

        The post-condition of :meth:`submit_create_form` for any caller that
        goes on to touch the page *underneath* the dialog. The MUI Dialog's
        backdrop outlives the submit by the length of its fade transition, and
        an element covered by it is not interactable — measured as an
        ``ElementNotInteractableException`` from ``search()`` on the ``full``
        profile of run 31113673507 (#835).
        """
        self.wait_for_element_hidden(self.CREATE_DIALOG)

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

        option = self.wait_for_element_clickable((By.CSS_SELECTOR, "li[role='option']"))
        self.click_menu_option(option)
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
            self.click_menu_option(options[index])
        # MUI auto-closes on option click; ensure the popover is fully gone
        self.close_mui_dropdown()

    def get_current_phase_option_count(self) -> int:
        """Return how many options the current-phase select currently offers."""

        field = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, "[data-testid='form-field-current_phase_key'] .MuiSelect-select")
        )
        self.scroll_and_click(field)
        try:
            self.poll(5).until(
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
