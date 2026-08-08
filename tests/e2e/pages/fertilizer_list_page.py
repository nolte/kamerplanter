"""Page object for the Fertilizer list page (REQ-004)."""

from __future__ import annotations

from contextlib import suppress

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import IMPLICIT_WAIT_EQUIVALENT, BasePage


class FertilizerListPage(BasePage):
    """Interact with the Fertilizer list (``/duengung/fertilizers``)."""

    PATH = "/duengung/fertilizers"

    # Locators — data-testid first per NFR-008 §3.2
    PAGE = (By.CSS_SELECTOR, "[data-testid='fertilizer-list-page']")
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
    FORM_PRODUCT_NAME = (By.CSS_SELECTOR, "[data-testid='form-field-product_name'] input")
    FORM_BRAND = (By.CSS_SELECTOR, "[data-testid='form-field-brand'] input")
    FORM_NPK_N = (By.CSS_SELECTOR, "[data-testid='form-field-npk_n'] input")
    FORM_NPK_P = (By.CSS_SELECTOR, "[data-testid='form-field-npk_p'] input")
    FORM_NPK_K = (By.CSS_SELECTOR, "[data-testid='form-field-npk_k'] input")
    FORM_EC_CONTRIBUTION = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-ec_contribution_per_ml'] input",
    )
    FORM_MIXING_PRIORITY = (By.CSS_SELECTOR, "[data-testid='form-field-mixing_priority'] input")
    FORM_NOTES = (By.CSS_SELECTOR, "[data-testid='form-field-notes'] textarea")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    # MUI Dialog
    CREATE_DIALOG = (By.CSS_SELECTOR, ".MuiDialog-root")
    #: The create dialog by its own testid. `CREATE_DIALOG` above matches *any*
    #: MUI dialog on the page, which is enough for "a dialog opened" but not for
    #: "this dialog closed" — the statement that a create returned 2xx.
    CREATE_DIALOG_EXACT = (By.CSS_SELECTOR, "[data-testid='fertilizer-create-dialog']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> FertilizerListPage:
        """Navigate to the fertilizer list and wait for it to load."""
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        return self

    # ── Table interactions ─────────────────────────────────────────────

    #: The three states this list settles into: rows, the terminal "no source
    #: data" `EmptyState`, or the terminal "search matched nothing" panel
    #: `DataTable` renders while the source rows are still there. `PAGE`
    #: mounts synchronously in `FertilizerListPage.tsx` -- before the first
    #: fetch resolves -- so a read taken right after `open()` can land in a
    #: frame where none of the three has committed yet, the same
    #: just-navigated window `wait_for_dashboard_content` was built for
    #: (`pflege_dashboard_page.py`). `wait_for_loading_complete()` cannot
    #: close that window: it is satisfied whenever no skeleton has mounted
    #: *yet*, which is exactly true in that same frame.
    #:
    #: What this does **not** cover: a read taken while a specific search
    #: term's ~300 ms debounce is still in flight. The *previous*, unfiltered
    #: rows keep `TABLE_ROWS` satisfied throughout that window -- there is no
    #: frame in which none of the three branches is present -- so this anchor
    #: is a no-op there. A caller reading after `search()` needs
    #: `wait_for_search_applied`/`wait_for_no_search_results` first, which
    #: wait for a *new* thing (the chip, the results panel) rather than for
    #: "something, anything" to be present.
    def wait_for_list_content(self, timeout: int = IMPLICIT_WAIT_EQUIVALENT) -> None:
        """Wait until the table has rows, its empty state, or its no-results panel.

        Deliberately does not raise: this is an *anchor* for the readers below,
        not an assertion of its own. A tenant with an empty fertilizer
        catalogue is a state the caller's own assertion must still be able to
        observe.
        """
        with suppress(AssertionError):
            self.wait_for_any_present(
                (self.TABLE_ROWS, self.EMPTY_STATE, self.NO_SEARCH_RESULTS),
                "fertilizer list content",
                timeout=timeout,
            )

    def get_row_count(self) -> int:
        """Return the number of visible data rows.

        Anchored on :meth:`wait_for_list_content`. Several call sites gate a
        `pytest.skip(...)` or a bidirectional count comparison on this,
        immediately after `open()` -- an unanchored `0` read in the pre-fetch
        window before `open()`'s data has arrived is indistinguishable from a
        table that genuinely has no rows, which is the `has_care_card` defect
        class this mirrors (#946).
        """
        self.wait_for_list_content()
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        return len(rows)

    #: Column id of the identifying column (FertilizerListPage `columns`).
    NAME_COLUMN_ID = "product_name"

    def get_first_column_texts(self) -> list[str]:
        """Return the product name of every visible row.

        Addressed by column id, not by position: the leading ``<td>`` is the
        favourite-star column (empty text), and below the DataTable's mobile
        breakpoint the rows are `MobileCard`s with no ``<td>`` at all.
        """
        return self.get_column_texts(self.NAME_COLUMN_ID)

    def get_column_headers(self) -> list[str]:
        """Return all visible column header texts."""
        headers = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='data-table'] th")
        return [h.text for h in headers if h.text]

    #: Column the row is activated through. Deliberately not the row centre:
    #: the table's first column is a favourite `IconButton` that
    #: `stopPropagation`s, so a centre click can toggle a favourite instead of
    #: opening the fertilizer. `product_name` renders `r.product_name` and
    #: carries no `hideBelowBreakpoint`.
    ROW_CLICK_COLUMN_ID = NAME_COLUMN_ID

    def click_row(self, index: int) -> None:
        """Open the fertilizer at *index* via its inert `product_name` cell."""
        self.click_data_table_row(
            index, self.ROW_CLICK_COLUMN_ID, self.TABLE_ROWS, "fertilizer row"
        )

    # ── Search and filter ──────────────────────────────────────────────

    def search(self, term: str) -> None:
        """Type a search term into the table search field."""
        search_input = self.wait_for_element_clickable(self.SEARCH_INPUT)
        self.clear_and_fill(search_input, term)

    def clear_search(self) -> None:
        """Clear the search field."""
        search_input = self.wait_for_element_clickable(self.SEARCH_INPUT)
        self.clear_and_fill(search_input, "")

    def click_reset_filters(self) -> None:
        """Click the reset filters button."""
        self.wait_for_element_clickable(self.RESET_FILTERS).click()

    def has_reset_filters_button(self) -> bool:
        """Return True if the reset filters button is present."""
        return len(self.driver.find_elements(*self.RESET_FILTERS)) > 0

    def get_showing_count_text(self) -> str:
        """Return the text of the showing count element."""
        el = self.wait_for_element(self.SHOWING_COUNT)
        return el.text

    def has_table(self) -> bool:
        """Return True if the DataTable is present."""
        return len(self.driver.find_elements(*self.TABLE)) > 0

    def get_search_input_value(self) -> str:
        """Return the current value typed into the search input."""
        el = self.wait_for_element(self.SEARCH_INPUT)
        return el.get_attribute("value") or ""

    def has_form_field(self, field_name: str) -> bool:
        """Return True if a ``form-field-{field_name}`` element is in the dialog.

        Waits: every caller asserts the field *is* there, right after the
        dialog opened, and a MUI Dialog mounts its paper before its form
        children. The raw read this replaces could answer for the frame in
        between. A field that never renders still answers ``False``.
        """
        return bool(
            self.await_presence((By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}']"))
        )

    # ── Create dialog ──────────────────────────────────────────────────

    def click_create(self) -> None:
        """Click the create button and wait for the dialog to appear."""
        self.wait_for_element_clickable(self.CREATE_BUTTON).click()
        self.wait_for_element_visible(self.CREATE_DIALOG)

    def is_create_dialog_open(self) -> bool:
        """Return True if the create dialog is visible."""
        dialogs = self.driver.find_elements(*self.CREATE_DIALOG)
        return any(d.is_displayed() for d in dialogs)

    def fill_product_name(self, name: str) -> None:
        """Fill the product name field."""
        el = self.wait_for_element_clickable(self.FORM_PRODUCT_NAME)
        self.clear_and_fill(el, name)

    def fill_brand(self, brand: str) -> None:
        """Fill the brand field."""
        el = self.wait_for_element_clickable(self.FORM_BRAND)
        self.clear_and_fill(el, brand)

    def fill_npk(self, n: float, p: float, k: float) -> None:
        """Fill the NPK N, P, K fields."""
        for locator, value in [
            (self.FORM_NPK_N, str(n)),
            (self.FORM_NPK_P, str(p)),
            (self.FORM_NPK_K, str(k)),
        ]:
            el = self.wait_for_element_clickable(locator)
            self.clear_and_fill(el, value)

    def fill_ec_contribution(self, value: float) -> None:
        """Fill the EC contribution field."""
        el = self.wait_for_element_clickable(self.FORM_EC_CONTRIBUTION)
        self.clear_and_fill(el, str(value))

    def fill_mixing_priority(self, value: int) -> None:
        """Fill the mixing priority field."""
        el = self.wait_for_element_clickable(self.FORM_MIXING_PRIORITY)
        self.clear_and_fill(el, str(value))

    def fill_notes(self, notes: str) -> None:
        """Fill the notes textarea."""
        el = self.wait_for_element_clickable(self.FORM_NOTES)
        self.clear_and_fill(el, notes)

    def select_fertilizer_type(self, value_text: str) -> None:
        """Open the fertilizer type select and pick an option.

        Routed through the shared, verified select helpers -- see
        ``BotanicalFamilyListPage.select_option`` for the rationale.
        """
        self.open_select("fertilizer_type")
        self.select_option_by_label(value_text)

    def select_ph_effect(self, value_text: str) -> None:
        """Open the pH effect select and pick an option."""
        self.open_select("ph_effect")
        self.select_option_by_label(value_text)

    def submit_create_form(self) -> None:
        """Submit the create form."""
        self.wait_and_click(self.FORM_SUBMIT)

    def wait_for_create_dialog_closed(self) -> None:
        """Wait until the create dialog is gone, i.e. the fertilizer really was created.

        The read-back :meth:`submit_create_form` does not have, and an exact one
        rather than a proxy: ``FertilizerCreateDialog.onSubmit`` calls
        ``onCreated()`` -- the only thing that clears ``createOpen`` on the
        submit path -- **after** ``await api.createFertilizer(...)`` resolves. A
        rejected create runs ``handleError`` instead and leaves the dialog up.
        So the dialog being gone means the POST returned 2xx, and nothing weaker
        does (#956/#966).

        Scoped to the dialog's own testid rather than to :data:`CREATE_DIALOG`
        (``.MuiDialog-root``): an unrelated dialog or a lingering MUI portal
        would keep the generic selector alive and turn this wait into a timeout
        that names the wrong thing.
        """
        self.wait_for_element_hidden(self.CREATE_DIALOG_EXACT)

    def cancel_create_form(self) -> None:
        """Cancel the create form."""
        self.wait_and_click(self.FORM_CANCEL)

    def get_product_name_field_value(self) -> str:
        """Return the current value of the product_name input."""
        el = self.wait_for_element(self.FORM_PRODUCT_NAME)
        return el.get_attribute("value") or ""

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
