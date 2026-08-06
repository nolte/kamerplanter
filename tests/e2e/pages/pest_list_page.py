"""Page object for the Pest list page (REQ-010)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class PestListPage(BasePage):
    """Interact with the Pest list page (``/pflanzenschutz/pests``)."""

    PATH = "/pflanzenschutz/pests"

    # -- Page-level locators --------------------------------------------------
    PAGE = (By.CSS_SELECTOR, "[data-testid='pest-list-page']")
    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")
    INTRO_TEXT = (By.CSS_SELECTOR, "[data-testid='pest-list-page'] .MuiTypography-body2")
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
    FORM_SCIENTIFIC_NAME = (By.CSS_SELECTOR, "[data-testid='form-field-scientific_name'] input")
    FORM_COMMON_NAME = (By.CSS_SELECTOR, "[data-testid='form-field-common_name'] input")
    FORM_PEST_TYPE = (By.CSS_SELECTOR, "[data-testid='form-field-pest_type'] .MuiSelect-select")
    FORM_LIFECYCLE_DAYS = (By.CSS_SELECTOR, "[data-testid='form-field-lifecycle_days'] input")
    FORM_OPTIMAL_TEMP_MIN = (By.CSS_SELECTOR, "[data-testid='form-field-optimal_temp_min'] input")
    FORM_OPTIMAL_TEMP_MAX = (By.CSS_SELECTOR, "[data-testid='form-field-optimal_temp_max'] input")
    FORM_DETECTION_DIFFICULTY = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-detection_difficulty'] .MuiSelect-select",
    )
    FORM_DESCRIPTION = (By.CSS_SELECTOR, "[data-testid='form-field-description'] textarea")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> PestListPage:
        """Navigate to the pest list and wait for it to load."""
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

    #: Column id of the identifying column (PestListPage `columns`).
    NAME_COLUMN_ID = "scientificName"

    def get_first_column_texts(self) -> list[str]:
        """Return the scientific name of every visible row.

        Addressed by column id, not by position: the leading ``<td>`` is the
        conditionally rendered recognition-chip column when pest recognition is
        available, and below the DataTable's mobile breakpoint there is no
        ``<td>`` at all (MobileCard layout).
        """
        return self.get_column_texts(self.NAME_COLUMN_ID)

    def get_column_headers(self) -> list[str]:
        """Return all visible column header texts."""
        headers = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='data-table'] th")
        return [h.text for h in headers if h.text]

    def get_row_texts(self) -> list[list[str]]:
        """Return the readable text fragments of every visible row."""
        return self.get_all_row_text_fragments()

    #: Column the row is activated through: `scientificName` renders
    #: `r.scientific_name` as plain text, is the first column and carries no
    #: `hideBelowBreakpoint`. Not the row centre — that is a viewport-dependent
    #: bet on which cell the row's midpoint happens to hit.
    ROW_CLICK_COLUMN_ID = NAME_COLUMN_ID

    def click_row(self, index: int = 0) -> None:
        """Open the pest at *index* via its inert scientific-name cell."""
        self.click_data_table_row(index, self.ROW_CLICK_COLUMN_ID, self.TABLE_ROWS, "pest row")

    #: Chip-carrying column ids (PestListPage `columns`).
    PEST_TYPE_COLUMN_ID = "pestType"
    DIFFICULTY_COLUMN_ID = "detectionDifficulty"

    #: Recognition-availability column (REQ-044), only rendered while pest
    #: detection is enabled. Readable through the column helpers below in both
    #: layouts: the desktop chip sits inside ``cell-recognition`` and carries
    #: `PestListPage`'s own ``data-testid='recognition-chip'``, the card chip
    #: is keyed ``card-chip-recognition``.
    RECOGNITION_COLUMN_ID = "recognition"

    def get_chip_texts_in_column(self, col_id: str) -> list[str]:
        """Return the chip labels of column *col_id* across all visible rows.

        Takes a column *id* rather than a column *index* and resolves it in
        both layouts (``cell-<id>`` / ``card-chip-<id>``): the pest table's
        column set is conditional (the recognition column only exists while
        pest detection is enabled), and the mobile card layout has no columns
        at all -- an index-based reader silently returned ``[]`` there.
        """
        return self.get_column_chip_texts(col_id)

    def get_chip_colors_in_column(self, col_id: str) -> list[str]:
        """Return the MUI palette name of column *col_id*'s chips (e.g. 'success')."""
        return self.get_column_chip_colors(col_id)

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

    def click_reset_filters(self) -> None:
        self.wait_for_element_clickable(self.RESET_FILTERS).click()

    def has_reset_filters_button(self) -> bool:
        return len(self.driver.find_elements(*self.RESET_FILTERS)) > 0

    def get_showing_count_text(self) -> str:
        el = self.wait_for_element(self.SHOWING_COUNT)
        return el.text

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

    def fill_scientific_name(self, name: str) -> None:
        el = self.wait_for_element_clickable(self.FORM_SCIENTIFIC_NAME)
        self.clear_and_fill(el, name)

    def fill_common_name(self, name: str) -> None:
        el = self.wait_for_element_clickable(self.FORM_COMMON_NAME)
        self.clear_and_fill(el, name)

    def select_pest_type(self, label_text: str) -> None:
        """Select a pest type by its visible label."""
        self._select_option("pest_type", label_text)

    def fill_lifecycle_days(self, days: int) -> None:
        el = self.wait_for_element_clickable(self.FORM_LIFECYCLE_DAYS)
        el.clear()
        el.send_keys(str(days))

    def fill_optimal_temp_min(self, temp: float) -> None:
        el = self.wait_for_element_clickable(self.FORM_OPTIMAL_TEMP_MIN)
        el.clear()
        el.send_keys(str(temp))

    def fill_optimal_temp_max(self, temp: float) -> None:
        el = self.wait_for_element_clickable(self.FORM_OPTIMAL_TEMP_MAX)
        el.clear()
        el.send_keys(str(temp))

    def select_detection_difficulty(self, label_text: str) -> None:
        """Select a detection difficulty by its visible label."""
        self._select_option("detection_difficulty", label_text)

    def fill_description(self, text: str) -> None:
        el = self.wait_for_element_clickable(self.FORM_DESCRIPTION)
        el.clear()
        el.send_keys(text)

    def submit_create_form(self) -> None:
        """Submit the create form by clicking its submit button.

        The predecessor bypassed the button entirely, dispatching a raw
        ``submit`` Event straight onto ``.MuiDialog-root [role='dialog'] form``
        -- guarded by ``if (form) { … }`` with no ``else``, so a form that was
        not found made this a *silent no-op reporting success* (`e2e-test-
        stability` §D), and a broken or permanently-disabled submit button
        would never be noticed, since the button was never touched.

        ``wait_and_click_coordinate_free`` clicks the *actual* button via a JS
        ``click()`` dispatched on the resolved element rather than at native
        pointer coordinates -- sound for a ``<button type='submit'>`` (see
        ``BasePage.click_coordinate_free``), so it still reliably triggers
        react-hook-form's ``handleSubmit`` under Selenium Grid, and it raises
        loudly (``TimeoutException``) if the button never becomes clickable,
        and again if it is disabled.
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
        Also checks for ``aria-invalid="true"`` on the input as a fallback.
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

        Fallback check for tests where the exact field emitting the error is
        uncertain (e.g. `has_validation_error` looked at the wrong field id).
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

    def field_has_aria_invalid(self, field_name: str) -> bool:
        """Return True if the input for *field_name* carries ``aria-invalid='true'``."""
        return (
            len(
                self.driver.find_elements(
                    By.CSS_SELECTOR,
                    f".MuiDialog-root [role='dialog'] [data-testid='form-field-{field_name}'] input[aria-invalid='true']",
                )
            )
            > 0
        )

    def has_any_aria_invalid_in_dialog(self) -> bool:
        """Return True if any input in the open dialog carries ``aria-invalid='true'``."""
        return (
            len(
                self.driver.find_elements(
                    By.CSS_SELECTOR, ".MuiDialog-root [role='dialog'] input[aria-invalid='true']"
                )
            )
            > 0
        )

    def get_field_debug_state(self, field_name: str) -> tuple[str, str]:
        """Return ``(value, aria-invalid)`` for *field_name*'s input — for failure messages.

        Returns ``("NOT FOUND: <field_name>", "N/A")`` if the field is absent.
        """
        elements = self.driver.find_elements(
            By.CSS_SELECTOR,
            f".MuiDialog-root [role='dialog'] [data-testid='form-field-{field_name}'] input",
        )
        if not elements:
            return f"NOT FOUND: form-field-{field_name}", "N/A"
        el = elements[0]
        return el.get_attribute("value") or "", el.get_attribute("aria-invalid") or ""

    # -- Internal helpers -----------------------------------------------------

    def _select_option(self, field_testid: str, value_text: str) -> None:
        """Open an MUI Select and pick an option by its visible text.

        Routed through the shared, verified select helpers -- see
        ``BotanicalFamilyListPage.select_option`` for the rationale.
        """
        self.open_select(field_testid)
        self.select_option_by_label(value_text)
