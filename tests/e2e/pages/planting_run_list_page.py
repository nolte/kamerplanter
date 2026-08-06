"""Page object for the Planting Run list page (REQ-013)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class PlantingRunListPage(BasePage):
    """Interact with the Planting Run list page (``/durchlaeufe/planting-runs``)."""

    PATH = "/durchlaeufe/planting-runs"

    # ── Page-level locators ────────────────────────────────────────────
    PAGE = (By.CSS_SELECTOR, "[data-testid='planting-run-list-page']")
    CREATE_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-button']")
    TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")
    SEARCH_INPUT = (By.CSS_SELECTOR, "[data-testid='table-search-input'] input")
    SEARCH_CHIP = (By.CSS_SELECTOR, "[data-testid='search-chip']")
    SORT_CHIP = (By.CSS_SELECTOR, "[data-testid='sort-chip']")
    RESET_FILTERS = (By.CSS_SELECTOR, "[data-testid='reset-filters-button']")
    SHOWING_COUNT = (By.CSS_SELECTOR, "[data-testid='showing-count']")
    EMPTY_STATE = (By.CSS_SELECTOR, "[data-testid='empty-state']")

    # ── Dialog locators ────────────────────────────────────────────────
    # PlantingRunCreateDialog does not use data-testid="create-dialog" — it uses
    # MUI Dialog with aria role="dialog". We locate it by DialogTitle text via role.
    CREATE_DIALOG = (By.CSS_SELECTOR, ".MuiDialog-root [role='dialog']")
    CONFIRM_DIALOG = (By.CSS_SELECTOR, "[data-testid='confirm-dialog']")
    CONFIRM_BUTTON = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-confirm']")
    CONFIRM_CANCEL = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-cancel']")

    # ── Create form field locators (inside Dialog) ─────────────────────
    FORM_NAME = (By.CSS_SELECTOR, "[data-testid='form-field-name'] input")
    FORM_RUN_TYPE = (By.CSS_SELECTOR, "[data-testid='form-field-run_type'] .MuiSelect-select")
    FORM_SITE_KEY = (By.CSS_SELECTOR, "[data-testid='form-field-site_key'] .MuiSelect-select")
    FORM_LOCATION_KEY = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-location_key'] .MuiSelect-select",
    )
    FORM_PLANNED_START = (By.CSS_SELECTOR, "[data-testid='form-field-planned_start_date'] input")
    FORM_NOTES = (By.CSS_SELECTOR, "[data-testid='form-field-notes'] input")
    # Entry row fields — zero-indexed entry
    FORM_ENTRY_SPECIES = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-entries.0.species_key'] .MuiSelect-select",
    )
    FORM_ENTRY_QUANTITY = (By.CSS_SELECTOR, "[data-testid='form-field-entries.0.quantity'] input")
    FORM_ENTRY_ID_PREFIX = (By.CSS_SELECTOR, "[data-testid='form-field-entries.0.id_prefix'] input")
    FORM_ENTRY_ROLE = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-entries.0.role'] .MuiSelect-select",
    )
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> PlantingRunListPage:
        """Navigate to the planting runs list and wait for it to load."""
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        return self

    # ── Table interactions ─────────────────────────────────────────────

    def get_row_count(self) -> int:
        """Return the number of visible table rows."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        return len(rows)

    #: Column id of the identifying column (PlantingRunListPage `columns`).
    NAME_COLUMN_ID = "name"

    def get_first_column_texts(self) -> list[str]:
        """Return the run name of every visible row.

        Addressed by column id, not by position: below the DataTable's mobile
        breakpoint the rows are `MobileCard`s with no ``<td>`` at all.
        """
        return self.get_column_texts(self.NAME_COLUMN_ID)

    def get_row_texts(self) -> list[list[str]]:
        """Return the readable text fragments of every visible row."""
        return self.get_all_row_text_fragments()

    def get_column_headers(self) -> list[str]:
        """Return all visible column header texts."""
        headers = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='data-table'] th")
        return [h.text for h in headers if h.text]

    #: Column the row is activated through: `name` renders `r.name` as plain
    #: text, is the first column and carries no `hideBelowBreakpoint`. Not the
    #: row centre — that is a viewport-dependent bet on which cell the row's
    #: midpoint happens to hit.
    ROW_CLICK_COLUMN_ID = NAME_COLUMN_ID

    def click_row(self, index: int = 0) -> None:
        """Open the planting run at *index* via its inert `name` cell."""
        self.click_data_table_row(
            index, self.ROW_CLICK_COLUMN_ID, self.TABLE_ROWS, "planting run row"
        )

    def click_row_by_name(self, name: str) -> None:
        """Click the row whose name column matches *name*.

        Addressed by column id, not by position, so it resolves in both the
        desktop table and the mobile card layout.
        """
        for row in self.driver.find_elements(*self.TABLE_ROWS):
            if self.get_row_primary_text(row, self.NAME_COLUMN_ID) == name:
                self.click_row_via_column(row, self.ROW_CLICK_COLUMN_ID)
                return
        raise ValueError(f"Row with name '{name}' not found in planting runs table")

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

    def click_reset_filters(self) -> None:
        self.wait_for_element_clickable(self.RESET_FILTERS).click()

    def has_reset_filters_button(self) -> bool:
        return len(self.driver.find_elements(*self.RESET_FILTERS)) > 0

    def get_showing_count_text(self) -> str:
        el = self.wait_for_element(self.SHOWING_COUNT)
        return el.text

    # ── Create dialog ──────────────────────────────────────────────────

    def click_create(self) -> None:
        """Click the Create button and wait for the dialog to open."""
        self.wait_for_element_clickable(self.CREATE_BUTTON).click()
        self.wait_for_element_visible(self.CREATE_DIALOG)

    def is_create_dialog_open(self) -> bool:
        """Return True if the create dialog is currently open."""
        return len(self.driver.find_elements(*self.CREATE_DIALOG)) > 0

    def fill_name(self, name: str) -> None:
        """Fill the Name field in the create dialog."""
        el = self.wait_for_element_clickable(self.FORM_NAME)
        el.clear()
        el.send_keys(name)

    def set_run_type(self, label_text: str) -> None:
        """Select a run type by its visible label text."""
        self.select_option("run_type", label_text)

    def fill_id_prefix(self, prefix: str) -> None:
        """Fill the id_prefix field for the first entry row."""
        el = self.wait_for_element_clickable(self.FORM_ENTRY_ID_PREFIX)
        el.clear()
        el.send_keys(prefix)

    def clear_id_prefix_if_present(self) -> None:
        """Clear the id_prefix field for entry 0, if it is currently rendered."""
        elements = self.driver.find_elements(*self.FORM_ENTRY_ID_PREFIX)
        if elements:
            elements[0].clear()

    def ensure_valid_id_prefix(self, fallback: str) -> None:
        """Fill entry 0's id_prefix with *fallback* if its current value is too short.

        The prefix is normally auto-populated from the selected species' genus;
        this guards against a genus abbreviation shorter than the required
        2 characters.
        """
        elements = self.driver.find_elements(*self.FORM_ENTRY_ID_PREFIX)
        if not elements:
            return
        current = elements[0].get_attribute("value") or ""
        if not current or len(current) < 2:
            elements[0].clear()
            elements[0].send_keys(fallback)

    def is_species_dropdown_present(self) -> bool:
        """Return True if the species select for entry 0 is rendered."""
        return len(self.driver.find_elements(*self.FORM_ENTRY_SPECIES)) > 0

    def select_first_available_species(self, timeout: int = 10) -> str | None:
        """Open the species select for entry 0 and pick the first non-empty option.

        Returns the selected option's label, or ``None`` if the dropdown opened
        but had no selectable options. Assumes the dropdown itself is present
        (check ``is_species_dropdown_present()`` first).
        """
        from selenium.webdriver.support import expected_conditions as EC

        select_el = self.wait_for_element_clickable(self.FORM_ENTRY_SPECIES)
        self.scroll_and_click(select_el)
        options = self.poll(timeout).until(
            EC.presence_of_all_elements_located((By.XPATH, "//li[@role='option']"))
        )
        species_options = [o for o in options if o.text.strip()]
        if not species_options:
            return None
        label = species_options[0].text
        self.click_menu_option(species_options[0])
        return label

    def fill_quantity(self, quantity: int) -> None:
        """Fill the quantity field for the first entry row."""
        el = self.wait_for_element_clickable(self.FORM_ENTRY_QUANTITY)
        el.clear()
        el.send_keys(str(quantity))

    def select_option(self, field_testid: str, value_text: str) -> None:
        """Open an MUI Select dropdown and pick an option by its visible text.

        Routed through the shared, verified select helpers -- see
        ``BotanicalFamilyListPage.select_option`` for the rationale.
        """
        self.open_select(field_testid)
        self.select_option_by_label(value_text)

    def submit_create_form(self) -> None:
        """Submit the create form by clicking the Save button."""
        self.wait_and_click(self.FORM_SUBMIT)

    def cancel_create_form(self) -> None:
        """Cancel the create dialog."""
        self.wait_and_click(self.FORM_CANCEL)

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

    # ── Confirm dialog helpers ─────────────────────────────────────────

    def confirm(self) -> None:
        """Click Confirm in the ConfirmDialog."""
        self.wait_and_click(self.CONFIRM_BUTTON)

    def cancel_confirm(self) -> None:
        """Click Cancel in the ConfirmDialog."""
        self.wait_and_click(self.CONFIRM_CANCEL)
