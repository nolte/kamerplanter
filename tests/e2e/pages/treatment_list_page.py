"""Page object for the Treatment list page (REQ-010)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class TreatmentListPage(BasePage):
    """Interact with the Treatment list page (``/pflanzenschutz/treatments``)."""

    PATH = "/pflanzenschutz/treatments"

    # -- Page-level locators --------------------------------------------------
    PAGE = (By.CSS_SELECTOR, "[data-testid='treatment-list-page']")
    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")
    INTRO_TEXT = (By.CSS_SELECTOR, "[data-testid='treatment-list-page'] .MuiTypography-body2")
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
    CREATE_DIALOG = (By.CSS_SELECTOR, ".MuiDialog-root [role='dialog']")

    # -- Create form field locators -------------------------------------------
    FORM_NAME = (By.CSS_SELECTOR, "[data-testid='form-field-name'] input")
    FORM_TREATMENT_TYPE = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-treatment_type'] .MuiSelect-select",
    )
    FORM_ACTIVE_INGREDIENT = (By.CSS_SELECTOR, "[data-testid='form-field-active_ingredient'] input")
    FORM_APPLICATION_METHOD = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-application_method'] .MuiSelect-select",
    )
    FORM_SAFETY_INTERVAL_DAYS = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-safety_interval_days'] input",
    )
    FORM_DOSAGE_PER_LITER = (By.CSS_SELECTOR, "[data-testid='form-field-dosage_per_liter'] input")
    FORM_PROTECTIVE_EQUIPMENT = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-protective_equipment'] input",
    )
    FORM_DESCRIPTION = (By.CSS_SELECTOR, "[data-testid='form-field-description'] textarea")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> TreatmentListPage:
        """Navigate to the treatment list and wait for it to load."""
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

    #: Column id of the identifying column (TreatmentListPage `columns`).
    NAME_COLUMN_ID = "name"

    def get_first_column_texts(self) -> list[str]:
        """Return the treatment name of every visible row.

        Addressed by column id, not by position: below the DataTable's mobile
        breakpoint the rows are `MobileCard`s with no ``<td>`` at all.
        """
        return self.get_column_texts(self.NAME_COLUMN_ID)

    def get_column_headers(self) -> list[str]:
        """Return all visible column header texts."""
        headers = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='data-table'] th")
        return [h.text for h in headers if h.text]

    def get_row_texts(self) -> list[list[str]]:
        """Return the readable text fragments of every visible row."""
        return self.get_all_row_text_fragments()

    #: Column the row is activated through: `name` renders the localised
    #: treatment name as plain text, is the first column and carries no
    #: `hideBelowBreakpoint`. Not the row centre — that is a viewport-dependent
    #: bet on which cell the row's midpoint happens to hit.
    ROW_CLICK_COLUMN_ID = NAME_COLUMN_ID

    def click_row(self, index: int = 0) -> None:
        """Open the treatment at *index* via its inert `name` cell."""
        self.click_data_table_row(index, self.ROW_CLICK_COLUMN_ID, self.TABLE_ROWS, "treatment row")

    #: Chip-carrying column id (TreatmentListPage `columns`).
    TREATMENT_TYPE_COLUMN_ID = "treatmentType"

    def get_chip_texts_in_column(self, col_id: str) -> list[str]:
        """Return the chip labels of column *col_id* across all visible rows.

        Takes a column *id* rather than a column *index*: the mobile card
        layout has no columns, so an index-based reader silently returned
        ``[]`` there.
        """
        return self.get_column_chip_texts(col_id)

    def get_chip_colors_in_column(self, col_id: str) -> list[str]:
        """Return the MUI palette name of column *col_id*'s chips (e.g. 'success')."""
        return self.get_column_chip_colors(col_id)

    def get_cell_text(self, row_index: int, col_id: str) -> str:
        """Return the text of column *col_id* in the row at *row_index*.

        Addressed by column id, not by position. Guarded against the mobile
        card layout, which renders no addressable cells at all and would make
        this return ``""`` for every column.
        """
        self.require_table_layout("TreatmentListPage.get_cell_text")
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        if row_index >= len(rows):
            return ""
        return self.get_row_cell_text(rows[row_index], col_id)

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
        elements = self.driver.find_elements(*self.CREATE_DIALOG)
        return any(el.is_displayed() for el in elements)

    def fill_name(self, name: str) -> None:
        el = self.wait_for_element_clickable(self.FORM_NAME)
        el.clear()
        el.send_keys(name)

    def select_treatment_type(self, label_text: str) -> None:
        """Select a treatment type by its visible label."""
        self._select_option("treatment_type", label_text)

    def fill_active_ingredient(self, ingredient: str) -> None:
        el = self.wait_for_element_clickable(self.FORM_ACTIVE_INGREDIENT)
        el.clear()
        el.send_keys(ingredient)

    def select_application_method(self, label_text: str) -> None:
        """Select an application method by its visible label."""
        self._select_option("application_method", label_text)

    def fill_safety_interval_days(self, days: int) -> None:
        el = self.wait_for_element_clickable(self.FORM_SAFETY_INTERVAL_DAYS)
        el.clear()
        el.send_keys(str(days))

    def fill_dosage_per_liter(self, dosage: float) -> None:
        el = self.wait_for_element_clickable(self.FORM_DOSAGE_PER_LITER)
        el.clear()
        el.send_keys(str(dosage))

    def add_protective_equipment(self, text: str) -> None:
        """Type equipment in the chip input and press Enter to create a chip."""
        el = self.wait_for_element_clickable(self.FORM_PROTECTIVE_EQUIPMENT)
        el.send_keys(text)
        el.send_keys(Keys.ENTER)

    def fill_description(self, text: str) -> None:
        el = self.wait_for_element_clickable(self.FORM_DESCRIPTION)
        el.clear()
        el.send_keys(text)

    def submit_create_form(self) -> None:
        """Submit the create form by clicking its submit button.

        Routed through the actual button -- see ``PestListPage.submit_create_form``
        for why the previous raw ``dispatchEvent('submit')`` on the dialog's
        ``form`` (guarded by an ``if (form) { … }`` with no ``else``) was a
        silent no-op on a missing form and bypassed the button entirely.
        """
        self.wait_and_click_coordinate_free(self.FORM_SUBMIT)

    def wait_for_dialog_closed(self, timeout: int = 15) -> None:
        """Wait until the create dialog is no longer in the DOM."""
        from selenium.webdriver.support import expected_conditions as EC

        self.poll(timeout).until(EC.invisibility_of_element_located(self.CREATE_DIALOG))

    def cancel_create_form(self) -> None:
        """Cancel the create dialog."""
        btn = self.wait_for_element(self.FORM_CANCEL)
        self.scroll_and_click(btn)

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

        def _check(_driver):
            return bool(self.get_validation_error(field_name))

        try:
            self.poll(3).until(_check)
            return True
        except Exception:
            return False

    def has_any_dialog_error_helper_text(self) -> bool:
        """Return True if any MUI error helper text is visible in the open dialog.

        Fallback check used when the exact field emitting the error is uncertain.
        """
        return (
            len(
                self.driver.find_elements(
                    By.CSS_SELECTOR,
                    ".MuiDialog-root [role='dialog'] .MuiFormHelperText-root.Mui-error",
                )
            )
            > 0
        )

    # -- Internal helpers -----------------------------------------------------

    def _select_option(self, field_testid: str, value_text: str) -> None:
        """Open an MUI Select and pick an option by its visible text.

        Routed through the shared, verified select helpers -- see
        ``BotanicalFamilyListPage.select_option`` for the rationale.
        ``select_option_by_label`` already closes the popover via
        ``close_mui_dropdown`` internally (the same guarded-Escape mechanism
        this used to call directly), so the surrounding Dialog is never at
        risk of being closed by a stray Escape.
        """
        self.open_select(field_testid)
        self.select_option_by_label(value_text)
