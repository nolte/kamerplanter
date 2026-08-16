"""Page object for the Botanical Family list page."""

from __future__ import annotations

from contextlib import suppress

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import IMPLICIT_WAIT_EQUIVALENT, BasePage


class BotanicalFamilyListPage(BasePage):
    """Interact with the Botanical Families list (``/stammdaten/botanical-families``)."""

    PATH = "/stammdaten/botanical-families"

    # Locators
    PAGE = (By.CSS_SELECTOR, "[data-testid='botanical-family-list-page']")
    CREATE_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-button']")
    TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")
    SEARCH_INPUT = (By.CSS_SELECTOR, "[data-testid='table-search-input'] input")
    SEARCH_CHIP = (By.CSS_SELECTOR, "[data-testid='search-chip']")
    SORT_CHIP = (By.CSS_SELECTOR, "[data-testid='sort-chip']")
    RESET_FILTERS = (By.CSS_SELECTOR, "[data-testid='reset-filters-button']")
    SHOWING_COUNT = (By.CSS_SELECTOR, "[data-testid='showing-count']")
    EMPTY_STATE = (By.CSS_SELECTOR, "[data-testid='empty-state']")
    CREATE_DIALOG = (By.CSS_SELECTOR, "[data-testid='botanical-family-create-dialog']")
    CONFIRM_DIALOG = (By.CSS_SELECTOR, "[data-testid='confirm-dialog']")
    CONFIRM_BUTTON = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-confirm']")
    CONFIRM_CANCEL = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-cancel']")

    # Form locators
    FORM_NAME = (By.CSS_SELECTOR, "[data-testid='form-field-name'] input")
    FORM_COMMON_NAME_DE = (By.CSS_SELECTOR, "[data-testid='form-field-common_name_de'] input")
    FORM_COMMON_NAME_EN = (By.CSS_SELECTOR, "[data-testid='form-field-common_name_en'] input")
    FORM_ORDER = (By.CSS_SELECTOR, "[data-testid='form-field-order'] input")
    FORM_DESCRIPTION = (By.CSS_SELECTOR, "[data-testid='form-field-description'] textarea")
    FORM_NUTRIENT_DEMAND = (By.CSS_SELECTOR, "[data-testid='form-field-typical_nutrient_demand']")
    FORM_NITROGEN_FIXING = (By.CSS_SELECTOR, "[data-testid='form-field-nitrogen_fixing']")
    FORM_ROOT_DEPTH = (By.CSS_SELECTOR, "[data-testid='form-field-typical_root_depth']")
    FORM_PH_MIN = (By.CSS_SELECTOR, "[data-testid='form-field-soil_ph_min'] input")
    FORM_PH_MAX = (By.CSS_SELECTOR, "[data-testid='form-field-soil_ph_max'] input")
    FORM_FROST_TOLERANCE = (By.CSS_SELECTOR, "[data-testid='form-field-frost_tolerance']")
    FORM_GROWTH_FORMS = (By.CSS_SELECTOR, "[data-testid='form-field-typical_growth_forms']")
    FORM_PESTS = (By.CSS_SELECTOR, "[data-testid='form-field-common_pests']")
    FORM_DISEASES = (By.CSS_SELECTOR, "[data-testid='form-field-common_diseases']")
    FORM_POLLINATION = (By.CSS_SELECTOR, "[data-testid='form-field-pollination_type']")
    FORM_ROTATION_CAT = (By.CSS_SELECTOR, "[data-testid='form-field-rotation_category'] input")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> BotanicalFamilyListPage:
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        return self

    def is_page_visible(self) -> bool:
        """Check whether the list page root element is present (waits)."""
        return bool(self.await_presence(self.PAGE))

    def get_form_field_count(self) -> int:
        """Return the number of ``form-field-*`` elements rendered on the current page."""
        return len(self.driver.find_elements(By.CSS_SELECTOR, "[data-testid^='form-field-']"))

    # ── Table interactions ─────────────────────────────────────────────

    #: The three states this list settles into: rows, the terminal "no source
    #: data" `EmptyState`, or the terminal "search matched nothing" panel
    #: `DataTable` renders while the source rows are still there. `PAGE`
    #: mounts synchronously -- before the first fetch resolves -- so a read
    #: right after `open()` can land in a frame where none of the three has
    #: committed yet, the same just-navigated window `wait_for_dashboard_content`
    #: was built for (`pflege_dashboard_page.py`). `wait_for_loading_complete()`
    #: cannot close that window: it is satisfied whenever no skeleton has
    #: mounted *yet*, which is exactly true in that same frame.
    #:
    #: What this does **not** cover: a read taken while a specific search
    #: term's ~300 ms debounce is still in flight. The *previous*, unfiltered
    #: rows keep `TABLE_ROWS` satisfied throughout that window, so this anchor
    #: is a no-op there -- a caller reading after `search()` needs
    #: `wait_for_search_applied`/`wait_for_no_search_results` first, which
    #: wait for a *new* thing rather than for "something, anything".
    def wait_for_list_content(self, timeout: int = IMPLICIT_WAIT_EQUIVALENT) -> None:
        """Wait until the table has rows, its empty state, or its no-results panel.

        Deliberately does not raise: this is an *anchor* for the readers below,
        not an assertion of its own. A tenant with no botanical families is a
        state the caller's own assertion must still be able to observe.
        """
        with suppress(AssertionError):
            self.wait_for_any_present(
                (self.TABLE_ROWS, self.EMPTY_STATE, self.NO_SEARCH_RESULTS),
                "botanical family list content",
                timeout=timeout,
            )

    def get_row_count(self) -> int:
        """Return the number of visible data rows.

        Anchored on :meth:`wait_for_list_content`. Several call sites gate a
        `pytest.skip(...)` on this immediately after `open()` -- an unanchored
        `0` read in the pre-fetch window is indistinguishable from a table
        that genuinely has no rows, which is the `has_care_card` defect class
        this mirrors (#946).
        """
        self.wait_for_list_content()
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        return len(rows)

    def get_row_texts(self) -> list[list[str]]:
        """Return every visible row's cell texts, in column order.

        Column-position based on purpose: the only caller (TC-REQ-001-093)
        inspects specific enum columns by index, which the mobile card layout
        does not render as addressable cells. Guarded so it fails loudly there
        instead of returning ``[]`` and passing the "no raw English enum"
        assertion vacuously; that caller is marked ``requires_desktop``.
        """
        self.require_table_layout("BotanicalFamilyListPage.get_row_texts")
        return [
            [c.text for c in row.find_elements(By.TAG_NAME, "td")]
            for row in self.driver.find_elements(*self.TABLE_ROWS)
        ]

    #: Column id of the identifying column (BotanicalFamilyListPage `columns`).
    NAME_COLUMN_ID = "name"

    def get_first_column_texts(self) -> list[str]:
        """Return the family name of every visible row.

        Addressed by column id, not by position: below the DataTable's mobile
        breakpoint the rows are `MobileCard`s with no ``<td>`` at all.
        """
        return self.get_column_texts(self.NAME_COLUMN_ID)

    #: Column the row is activated through: `name` renders `r.name` as plain
    #: text, is the first column and carries no `hideBelowBreakpoint`. Not the
    #: row centre — that is a viewport-dependent bet on which cell the row's
    #: midpoint happens to hit.
    ROW_CLICK_COLUMN_ID = NAME_COLUMN_ID

    def click_row(self, index: int) -> None:
        """Open the botanical family at *index* via its inert `name` cell."""
        self.click_data_table_row(
            index, self.ROW_CLICK_COLUMN_ID, self.TABLE_ROWS, "botanical family row"
        )

    def click_row_by_name(self, name: str) -> None:
        """Click the row whose name column matches *name*.

        Addressed by column id, not by position, so it works for both the
        desktop table and the mobile card layout.
        """
        for row in self.driver.find_elements(*self.TABLE_ROWS):
            if self.get_row_primary_text(row, self.NAME_COLUMN_ID) == name:
                self.click_row_via_column(row, self.ROW_CLICK_COLUMN_ID)
                return
        raise ValueError(f"Row with name '{name}' not found")

    def get_column_headers(self) -> list[str]:
        """Return all visible column header texts."""
        headers = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='data-table'] th")
        return [h.text for h in headers if h.text]

    # ── Search and filter ──────────────────────────────────────────────

    def search(self, term: str) -> None:
        """Type a search term into the search field."""
        import time

        self.fill_table_search(self.SEARCH_INPUT, term)
        # debounce: bounded, justified (table-search-input has a 300ms
        # debounce before it re-filters, so callers can rely on the result
        # being settled once this method returns)
        time.sleep(0.3)

    def clear_search(self) -> None:
        self.fill_table_search(self.SEARCH_INPUT, "")

    def click_reset_filters(self) -> None:
        self.wait_for_element_clickable(self.RESET_FILTERS).click()

    def has_reset_filters_button(self) -> bool:
        return len(self.driver.find_elements(*self.RESET_FILTERS)) > 0

    def get_showing_count_text(self) -> str:
        el = self.wait_for_element(self.SHOWING_COUNT)
        return el.text

    # ── Create dialog ──────────────────────────────────────────────────

    def has_create_button(self) -> bool:
        """Return True if the create affordance is offered to the current user.

        Read after the table has rows, never on its own: the button and the table
        render in the same commit, so "no button" on a page that is still loading
        is true of an administrator too, and an absence assertion taken there
        would pass for every user (#1155).
        """
        return len(self.driver.find_elements(*self.CREATE_BUTTON)) > 0

    def click_create(self) -> None:
        self.wait_for_element_clickable(self.CREATE_BUTTON).click()
        self.wait_for_element_visible(self.CREATE_DIALOG)

    def fill_create_form(self, name: str, **kwargs: str) -> None:
        """Fill the create form. Only *name* is required."""
        name_input = self.wait_for_element_clickable(self.FORM_NAME)
        name_input.clear()
        name_input.send_keys(name)

        if "common_name_de" in kwargs:
            el = self.wait_for_element_clickable(self.FORM_COMMON_NAME_DE)
            el.clear()
            el.send_keys(kwargs["common_name_de"])

        if "common_name_en" in kwargs:
            el = self.wait_for_element_clickable(self.FORM_COMMON_NAME_EN)
            el.clear()
            el.send_keys(kwargs["common_name_en"])

        if "order" in kwargs:
            el = self.wait_for_element_clickable(self.FORM_ORDER)
            el.clear()
            el.send_keys(kwargs["order"])

        if "description" in kwargs:
            el = self.wait_for_element_clickable(self.FORM_DESCRIPTION)
            el.clear()
            el.send_keys(kwargs["description"])

        if "ph_min" in kwargs:
            el = self.wait_for_element_clickable(self.FORM_PH_MIN)
            el.clear()
            el.send_keys(kwargs["ph_min"])

        if "ph_max" in kwargs:
            el = self.wait_for_element_clickable(self.FORM_PH_MAX)
            el.clear()
            el.send_keys(kwargs["ph_max"])

        if "rotation_category" in kwargs:
            el = self.wait_for_element_clickable(self.FORM_ROTATION_CAT)
            el.clear()
            el.send_keys(kwargs["rotation_category"])

    def fill_name_only(self, name: str) -> None:
        """Fill just the name field."""
        name_input = self.wait_for_element_clickable(self.FORM_NAME)
        name_input.clear()
        name_input.send_keys(name)

    def get_name_field_value(self) -> str:
        el = self.wait_for_element(self.FORM_NAME)
        return el.get_attribute("value") or ""

    def submit_create_form(self) -> None:
        self.wait_and_click(self.FORM_SUBMIT)

    def wait_for_create_dialog_closed(self) -> None:
        """Wait until the create dialog is gone, i.e. the family really was created.

        The read-back :meth:`submit_create_form` does not have, and an exact one
        rather than a proxy: ``BotanicalFamilyCreateDialog.onSubmit`` calls
        ``onCreated()`` -- the only thing that clears ``createOpen`` on the
        submit path -- **after** ``await api.createBotanicalFamily(...)``
        resolves. A rejected create runs ``handleError`` instead and leaves the
        dialog up. So the dialog being gone means the POST returned 2xx, and
        nothing weaker does (#956/#966).
        """
        self.wait_for_element_hidden(self.CREATE_DIALOG)

    def cancel_create_form(self) -> None:
        self.wait_and_click(self.FORM_CANCEL)

    def is_create_dialog_open(self) -> bool:
        return len(self.driver.find_elements(*self.CREATE_DIALOG)) > 0

    def get_validation_error(self, field_name: str) -> str:
        """Return the validation error text for a form field."""
        locator = (
            By.CSS_SELECTOR,
            f"[data-testid='form-field-{field_name}'] .MuiFormHelperText-root.Mui-error",
        )
        elements = self.driver.find_elements(*locator)
        return elements[0].text if elements else ""

    def has_validation_error(self, field_name: str) -> bool:
        return bool(self.get_validation_error(field_name))

    # ── MUI Select helpers ─────────────────────────────────────────────

    def select_option(self, field_testid: str, value_text: str) -> None:
        """Open an MUI Select and pick an option by its visible text.

        Routed through the shared, verified select helpers: ``open_select``
        raises unless the menu is verifiably open, and ``select_option_by_label``
        resolves *value_text* against the option's own ``data-value`` (via
        ``textContent``, not the unscoped ``contains(text(), …)`` XPath this used
        to run, which only sees an option's first text node and can match any
        listbox in the DOM) and reads the committed value back.
        """
        self.open_select(field_testid)
        self.select_option_by_label(value_text)

    def is_switch_checked(self, field_testid: str) -> bool:
        switch = self.find_present(
            (By.CSS_SELECTOR, f"[data-testid='form-field-{field_testid}'] input[type='checkbox']")
        )
        return switch.is_selected()

    # ── Keyboard navigation ────────────────────────────────────────────

    def focus_row_and_press_enter(self, index: int) -> None:
        """Tab to a row and press Enter."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        row = self.require_index(rows, index, "botanical family row")
        row.send_keys(Keys.ENTER)

    # ── Pagination ─────────────────────────────────────────────────────

    def get_rows_per_page_options(self) -> list[str]:
        """Return available page size options (MUI TablePagination)."""
        # MUI pagination select
        elements = self.driver.find_elements(By.CSS_SELECTOR, ".MuiTablePagination-select option")
        return [e.text for e in elements]
