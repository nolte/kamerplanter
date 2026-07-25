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
    CREATE_DIALOG = (By.CSS_SELECTOR, "[data-testid='species-create-dialog']")
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
        """Return the scientific name of every visible row.

        Addressed by column id, not by position: the species table leads with a
        favourite-star and an image column (both empty text), so ``cells[0]``
        returned a list of empty strings even on the desktop table -- and an
        empty list in the mobile card layout.
        """
        return self.get_column_texts(self.NAME_COLUMN_ID)

    def get_row_texts(self) -> list[list[str]]:
        """Return every visible row's cell texts, in column order.

        Column-position based on purpose: the only caller (TC-REQ-001-094)
        inspects specific enum columns, which the mobile card layout does not
        render as addressable cells. Guarded so it fails loudly there instead
        of returning ``[]`` and passing the "no raw English enum" assertion
        vacuously; that caller is marked ``requires_desktop``.
        """
        self.require_table_layout("SpeciesListPage.get_row_texts")
        return [
            [c.text for c in row.find_elements(By.TAG_NAME, "td")]
            for row in self.driver.find_elements(*self.TABLE_ROWS)
        ]

    def click_row(self, index: int) -> None:
        """Open the species at *index* via its inert scientific-name cell.

        The row navigates via ``onRowClick``, but the "Familie" cell holds a
        ``stopPropagation`` link to the botanical-family detail and the first
        column is a favourite `IconButton` — so the row's geometric centre is
        not a safe target. This replaces the previous "first ``<td>`` with text
        and no ``<a>``" scan, which silently fell back to the row element when
        it found nothing (mobile card layout) and so re-armed exactly that bet.
        """
        self.click_data_table_row(
            index, self.NAME_COLUMN_ID, self.TABLE_ROWS, "species row"
        )

    def search(self, query: str) -> None:
        """Filter the table via the DataTable search box (debounced 300ms)."""
        import time

        el = self.wait_for_element_clickable(self.SEARCH_INPUT)
        self.clear_and_fill(el, query)
        time.sleep(0.5)  # DataTable debounces the search input by 300ms
        self.wait_for_loading_complete()

    #: Column id of the identifying column (SpeciesListPage `columns`).
    NAME_COLUMN_ID = "scientificName"

    def click_row_by_name(self, name: str) -> None:
        """Click the row whose scientific name matches *name*.

        Addressed by column id, not by position: the species table starts with
        a star/favorite and an image column (both empty text), and below the
        DataTable's mobile breakpoint the row is a `MobileCard` with no
        ``<td>`` cells at all -- a ``By.TAG_NAME, 'td'`` scan finds nothing
        there and would raise "Row with name … not found" on every mobile and
        tablet run.

        The DataTable is client-side sorted (scientific name asc) and paginated
        at 25 rows/page, so a freshly created species can land on a later page
        that is not in the page-1 DOM. Search first to filter it onto page 1
        before scanning — mirrors ``provision_plant`` in ``_journey_helpers.py``.
        """
        self.search(name)
        for row in self.driver.find_elements(*self.TABLE_ROWS):
            if self.get_row_primary_text(row, self.NAME_COLUMN_ID) == name:
                self.click_row_via_column(row, self.NAME_COLUMN_ID)
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

    def open_dropdown_and_get_options(self, field_name: str) -> list[str]:
        """Open the MUI Select for *field_name* and return its option texts.

        Leaves the dropdown open; callers should close it via
        :meth:`close_mui_dropdown` when done inspecting the options.
        """
        field = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] .MuiSelect-select")
        )
        self.scroll_and_click(field)
        options = self.driver.find_elements(By.CSS_SELECTOR, "li[role='option']")
        return [o.text for o in options]

    def select_option(self, field_name: str, value_text: str) -> None:
        field = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] .MuiSelect-select")
        )
        self.scroll_and_click(field)
        option = self.wait_for_element_clickable(
            (By.XPATH, f"//li[@role='option' and contains(text(), '{value_text}')]")
        )
        option.click()
        # MUI auto-closes on option click; ensure the popover is fully gone
        self.close_mui_dropdown()

    def add_chip(self, field_name: str, value: str) -> None:
        from selenium.webdriver.common.keys import Keys

        el = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] input")
        )
        el.send_keys(value)
        el.send_keys(Keys.ENTER)

    def submit_form(self) -> None:
        self.wait_and_click(self.FORM_SUBMIT)

    def cancel_form(self) -> None:
        self.wait_and_click(self.FORM_CANCEL)

    def is_create_dialog_open(self) -> bool:
        return len(self.driver.find_elements(*self.CREATE_DIALOG)) > 0

    def has_validation_error(self, field_name: str) -> bool:
        locator = (By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] .MuiFormHelperText-root.Mui-error")
        return len(self.driver.find_elements(*locator)) > 0
