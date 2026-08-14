"""Page object for the Substrate list page (REQ-019)."""

from __future__ import annotations

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class SubstrateListPage(BasePage):
    """Interact with the Substrate list page (``/standorte/substrates``)."""

    PATH = "/standorte/substrates"

    # ── Page-level locators ────────────────────────────────────────────
    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")
    TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")
    SEARCH_INPUT = (By.CSS_SELECTOR, "[data-testid='table-search-input'] input")
    SEARCH_CHIP = (By.CSS_SELECTOR, "[data-testid='search-chip']")
    SORT_CHIP = (By.CSS_SELECTOR, "[data-testid='sort-chip']")
    RESET_FILTERS = (By.CSS_SELECTOR, "[data-testid='reset-filters-button']")
    SHOWING_COUNT = (By.CSS_SELECTOR, "[data-testid='showing-count']")
    NO_SEARCH_RESULTS = (By.CSS_SELECTOR, "[data-testid='no-search-results']")

    # ── Action buttons (no data-testid — located by text/icon) ────────
    # The SubstrateListPage uses inline MUI Buttons without data-testid.
    # We use the button text rendered via i18n.
    # Addressed by data-testid rather than by MUI class (the suite's locator
    # convention, tests/e2e/README.md):
    # the classes moved when the header adopted `PageHeaderActions`, and on `xs`
    # the mix action is a menu entry with no button class at all (#832).
    CREATE_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-button']")
    MIX_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-mix-button']")

    # ── Create dialog locators ─────────────────────────────────────────
    CREATE_DIALOG = (By.CSS_SELECTOR, ".MuiDialog-root [role='dialog']")
    FORM_TYPE = (By.CSS_SELECTOR, "[data-testid='form-field-type'] .MuiSelect-select")
    FORM_BRAND = (By.CSS_SELECTOR, "[data-testid='form-field-brand'] input")
    FORM_NAME_DE = (By.CSS_SELECTOR, "[data-testid='form-field-name_de'] input")
    FORM_NAME_EN = (By.CSS_SELECTOR, "[data-testid='form-field-name_en'] input")
    FORM_PH_BASE = (By.CSS_SELECTOR, "[data-testid='form-field-ph_base'] input")
    FORM_EC_BASE = (By.CSS_SELECTOR, "[data-testid='form-field-ec_base_ms'] input")
    FORM_WATER_RETENTION = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-water_retention'] .MuiSelect-select",
    )
    FORM_AIR_POROSITY = (By.CSS_SELECTOR, "[data-testid='form-field-air_porosity_percent'] input")
    FORM_BUFFER_CAPACITY = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-buffer_capacity'] .MuiSelect-select",
    )
    FORM_REUSABLE = (By.CSS_SELECTOR, "[data-testid='form-field-reusable'] .MuiSwitch-root")
    FORM_MAX_REUSE = (By.CSS_SELECTOR, "[data-testid='form-field-max_reuse_cycles'] input")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> SubstrateListPage:
        """Navigate to the substrates list and wait for it to load."""
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE_TITLE)
        self.wait_for_loading_complete()
        return self

    # ── Table interactions ─────────────────────────────────────────────

    def get_row_count(self) -> int:
        """Return the number of visible table rows."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        return len(rows)

    #: Column id of the identifying column (SubstrateListPage `columns`).
    NAME_COLUMN_ID = "name"

    def get_first_column_texts(self) -> list[str]:
        """Return the substrate name of every visible row.

        Addressed by column id, not by position: the substrate table leads with
        a favourite-star and a type column, and below the DataTable's mobile
        breakpoint the rows are `MobileCard`s with no ``<td>`` at all.
        """
        return self.get_column_texts(self.NAME_COLUMN_ID)

    def get_column_headers(self) -> list[str]:
        """Return all visible column header texts."""
        headers = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='data-table'] th")
        return [h.text for h in headers if h.text]

    def get_row_texts(self) -> list[list[str]]:
        """Return the readable text fragments of every visible row.

        Layout-tolerant: TC-REQ-019-025 asserts a deleted substrate is *absent*
        from this list, which the ``<td>``-only reader satisfied trivially in
        the mobile card layout by returning nothing at all.
        """
        return self.get_all_row_text_fragments()

    #: Column the row is activated through. Deliberately not the row centre:
    #: the table's first column is a favourite `IconButton` that
    #: `stopPropagation`s, so a centre click can toggle a favourite instead of
    #: opening the substrate. `name` renders plain text and carries no
    #: `hideBelowBreakpoint`.
    ROW_CLICK_COLUMN_ID = NAME_COLUMN_ID

    def click_row(self, index: int = 0) -> None:
        """Open the substrate at *index* via its inert `name` cell."""
        self.click_data_table_row(index, self.ROW_CLICK_COLUMN_ID, self.TABLE_ROWS, "substrate row")

    def click_row_by_text(self, text: str) -> None:
        """Open the substrate whose row contains *text*, via its `name` cell."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        for row in rows:
            if text in row.text:
                self.click_row_via_column(row, self.ROW_CLICK_COLUMN_ID)
                return
        raise ValueError(f"Row containing '{text}' not found in substrate table")

    # ── Search and filter ──────────────────────────────────────────────

    def search(self, term: str) -> None:
        """Type *term* into the search field.

        Uses ``clear_and_fill`` rather than ``WebElement.clear()``: the search
        box is a React-controlled input, where ``clear()`` empties the DOM value
        without notifying React, so the previous term can survive and the next
        one is appended to it. A single call happens to work; calling this twice
        -- as the create test does when it counts before and after -- produced
        ``E2E-TestsubstratE2E-Testsubstrat`` and therefore zero matches, which
        looked exactly like the created row never appearing (#802).
        """
        self.fill_table_search(self.SEARCH_INPUT, term)
        # debounce: bounded, justified (table-search-input has a 300ms
        # debounce before it re-filters, so callers can rely on the result
        # being settled once this method returns)
        time.sleep(0.3)

    def clear_search(self) -> None:
        """Empty the search field, React state included (see ``search``)."""
        self.fill_table_search(self.SEARCH_INPUT, "")

    def click_reset_filters(self) -> None:
        """Click the reset filters button."""
        self.wait_for_element_clickable(self.RESET_FILTERS).click()

    def has_reset_filters_button(self) -> bool:
        """Return True if the reset filters button is visible."""
        return len(self.driver.find_elements(*self.RESET_FILTERS)) > 0

    def has_no_search_results(self) -> bool:
        """Return True if the 'no search results' message is shown."""
        return len(self.driver.find_elements(*self.NO_SEARCH_RESULTS)) > 0

    def get_showing_count_text(self) -> str:
        """Return the text of the showing count element."""
        el = self.wait_for_element(self.SHOWING_COUNT)
        return el.text

    # ── Create dialog ──────────────────────────────────────────────────

    def click_create(self) -> None:
        """Click the Create button and wait for the dialog."""
        self.click_header_action("create-button")
        self.wait_for_element_visible(self.CREATE_DIALOG)

    def is_create_dialog_open(self) -> bool:
        """Return True if any dialog is open."""
        return len(self.driver.find_elements(*self.CREATE_DIALOG)) > 0

    def wait_for_create_dialog_closed(self, timeout: int = 15) -> None:
        """Wait until the create dialog is no longer visible (post-submit)."""
        self.wait_for_element_hidden(self.CREATE_DIALOG, timeout=timeout)

    def wait_for_row_absent(self, text: str, timeout: int = 15) -> None:
        """Wait until no row contains *text* (e.g. after a delete)."""

        self.poll(timeout).until(
            lambda d: text not in " ".join(cell for row in self.get_row_texts() for cell in row)
        )

    def fill_brand(self, value: str) -> None:
        """Fill the Brand field in the create dialog."""
        el = self.wait_for_element_clickable(self.FORM_BRAND)
        self.clear_and_fill(el, value)

    def fill_name_de(self, value: str) -> None:
        """Fill the Name (DE) field in the create dialog."""
        el = self.wait_for_element_clickable(self.FORM_NAME_DE)
        self.clear_and_fill(el, value)

    def fill_name_en(self, value: str) -> None:
        """Fill the Name (EN) field in the create dialog."""
        el = self.wait_for_element_clickable(self.FORM_NAME_EN)
        self.clear_and_fill(el, value)

    def fill_ph_base(self, value: float) -> None:
        """Fill the pH base field."""
        el = self.wait_for_element_clickable(self.FORM_PH_BASE)
        self.clear_and_fill(el, str(value))

    def fill_ec_base(self, value: float) -> None:
        """Fill the EC base field."""
        el = self.wait_for_element_clickable(self.FORM_EC_BASE)
        self.clear_and_fill(el, str(value))

    def fill_air_porosity(self, value: float) -> None:
        """Fill the air porosity field."""
        el = self.wait_for_element_clickable(self.FORM_AIR_POROSITY)
        self.clear_and_fill(el, str(value))

    def fill_max_reuse_cycles(self, value: int) -> None:
        """Fill the max reuse cycles field."""
        el = self.wait_for_element_clickable(self.FORM_MAX_REUSE)
        self.clear_and_fill(el, str(value))

    def select_type(self, label_text: str) -> None:
        """Select a substrate type by its visible label."""
        self._select_option("type", label_text)

    def select_water_retention(self, label_text: str) -> None:
        """Select a water retention value by its visible label."""
        self._select_option("water_retention", label_text)

    def select_buffer_capacity(self, label_text: str) -> None:
        """Select a buffer capacity by its visible label."""
        self._select_option("buffer_capacity", label_text)

    def toggle_reusable(self) -> None:
        """Toggle the reusable switch."""
        el = self.wait_for_element_clickable(self.FORM_REUSABLE)
        self.scroll_and_click(el)

    def is_reusable_checked(self) -> bool:
        """Return True if the reusable switch is checked."""
        el = self.find_present(
            (By.CSS_SELECTOR, "[data-testid='form-field-reusable'] input[type='checkbox']")
        )
        return el.is_selected()

    def submit_create_form(self) -> None:
        """Submit the create form."""
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

    # ── Private helpers ────────────────────────────────────────────────

    def _select_option(self, field_testid: str, value_text: str) -> None:
        """Open an MUI Select and pick an option by its visible text.

        Routed through the shared, verified select helpers -- see
        ``BotanicalFamilyListPage.select_option`` for the rationale.
        """
        self.open_select(field_testid)
        self.select_option_by_label(value_text)

    def get_type_options(self) -> list[str]:
        """Open the type dropdown and return all option texts.

        The dropdown is closed again afterwards.
        """
        field = self.wait_for_element_clickable(self.FORM_TYPE)
        self.scroll_and_click(field)
        options = self.driver.find_elements(By.CSS_SELECTOR, "li[role='option']")
        texts = [o.text for o in options]
        self.close_mui_dropdown()
        return texts
