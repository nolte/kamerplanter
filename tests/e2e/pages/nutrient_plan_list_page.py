"""Page object for the Nutrient Plan list page (REQ-004)."""

from __future__ import annotations

from contextlib import suppress

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC

from .base_page import DEFAULT_TIMEOUT, IMPLICIT_WAIT_EQUIVALENT, BasePage


class NutrientPlanListPage(BasePage):
    """Interact with the Nutrient Plan list (``/duengung/plans``)."""

    PATH = "/duengung/plans"

    # Locators
    PAGE = (By.CSS_SELECTOR, "[data-testid='nutrient-plan-list-page']")
    CREATE_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-button']")
    TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")
    SEARCH_INPUT = (By.CSS_SELECTOR, "[data-testid='table-search-input'] input")
    SEARCH_CHIP = (By.CSS_SELECTOR, "[data-testid='search-chip']")
    SORT_CHIP = (By.CSS_SELECTOR, "[data-testid='sort-chip']")
    RESET_FILTERS = (By.CSS_SELECTOR, "[data-testid='reset-filters-button']")
    SHOWING_COUNT = (By.CSS_SELECTOR, "[data-testid='showing-count']")
    EMPTY_STATE = (By.CSS_SELECTOR, "[data-testid='empty-state']")

    # MUI Dialog (create). Addressed by the app's own hook
    # (`NutrientPlanCreateDialog.tsx`) rather than by `.MuiDialog-root`, which
    # matches *whichever* dialog is open -- so "the create dialog is still open"
    # and "some confirm dialog is open" were the same observation.
    CREATE_DIALOG = (By.CSS_SELECTOR, "[data-testid='nutrient-plan-create-dialog']")

    # Create form fields
    FORM_NAME = (By.CSS_SELECTOR, "[data-testid='form-field-name'] input")
    FORM_DESCRIPTION = (By.CSS_SELECTOR, "[data-testid='form-field-description'] textarea")
    FORM_AUTHOR = (By.CSS_SELECTOR, "[data-testid='form-field-author'] input")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> NutrientPlanListPage:
        """Navigate to the nutrient plan list and wait for it to load."""
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE, timeout=20)
        self.wait_for_loading_complete(timeout=20)
        return self

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
        not an assertion of its own. A tenant with no nutrient plans is a
        state the caller's own assertion must still be able to observe.
        """
        with suppress(AssertionError):
            self.wait_for_any_present(
                (self.TABLE_ROWS, self.EMPTY_STATE, self.NO_SEARCH_RESULTS),
                "nutrient plan list content",
                timeout=timeout,
            )

    def get_row_count(self) -> int:
        """Return the number of visible data rows.

        Anchored on :meth:`wait_for_list_content`. Several call sites gate a
        `pytest.skip(...)` or a bidirectional count comparison on this,
        immediately after `open()` -- an unanchored `0` read in the pre-fetch
        window is indistinguishable from a table that genuinely has no rows,
        which is the `has_care_card` defect class this mirrors (#946).
        """
        self.wait_for_list_content()
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        return len(rows)

    #: Column id of the identifying column (NutrientPlanListPage `columns`).
    NAME_COLUMN_ID = "name"

    def get_first_column_texts(self) -> list[str]:
        """Return the plan name of every visible row.

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
    #: the table's first column is a favourite `IconButton` and its last an
    #: actions button, both `stopPropagation`, so a centre click can silently
    #: toggle a favourite instead of opening the plan. `name` renders `r.name`
    #: and carries no `hideBelowBreakpoint`.
    ROW_CLICK_COLUMN_ID = NAME_COLUMN_ID

    def click_row(self, index: int) -> None:
        """Open the nutrient plan at *index* via its inert `name` cell."""
        self.click_data_table_row(
            index, self.ROW_CLICK_COLUMN_ID, self.TABLE_ROWS, "nutrient plan row"
        )

    # ── Clone action ───────────────────────────────────────────────────

    def click_clone_on_row(self, index: int) -> None:
        """Click the clone icon button on a given row."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        row = self.require_index(rows, index, "nutrient plan row")
        clone_btn = row.find_element(By.CSS_SELECTOR, "button[title]")
        self.scroll_and_click(clone_btn)

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

    def get_showing_count_text(self) -> str:
        """Return the text of the showing count element."""
        el = self.wait_for_element(self.SHOWING_COUNT)
        return el.text

    # ── Create dialog ──────────────────────────────────────────────────

    def click_create(self) -> None:
        """Click the create button and wait for the dialog."""
        self.wait_for_element_clickable(self.CREATE_BUTTON).click()
        self.wait_for_element_visible(self.CREATE_DIALOG)

    def is_create_dialog_open(self) -> bool:
        """Return True if a MUI dialog is currently visible."""
        dialogs = self.driver.find_elements(*self.CREATE_DIALOG)
        return any(d.is_displayed() for d in dialogs)

    def fill_name(self, name: str) -> None:
        """Fill the plan name field."""
        el = self.wait_for_element_clickable(self.FORM_NAME)
        self.clear_and_fill(el, name)

    def fill_description(self, description: str) -> None:
        """Fill the description textarea."""
        el = self.wait_for_element_clickable(self.FORM_DESCRIPTION)
        self.clear_and_fill(el, description)

    def fill_author(self, author: str) -> None:
        """Fill the author field."""
        el = self.wait_for_element_clickable(self.FORM_AUTHOR)
        self.clear_and_fill(el, author)

    def select_substrate_type(self, value_text: str) -> None:
        """Open the substrate type select and pick an option.

        Routed through the shared, verified select helpers -- see
        ``BotanicalFamilyListPage.select_option`` for the rationale.
        """
        self.open_select("recommended_substrate_type")
        self.select_option_by_label(value_text)

    def toggle_is_template(self) -> None:
        """Toggle the is_template switch."""
        switch = self.wait_for_element(
            (By.CSS_SELECTOR, "[data-testid='form-field-is_template'] input[type='checkbox']")
        )
        self.scroll_and_click(switch)

    def submit_create_form(self) -> None:
        """Submit the create form.

        Waits for the button to be *clickable*, not merely present. Presence is
        satisfied by a button that is still `disabled` while the form finishes
        validating, and clicking a disabled button is a silent no-op that leaves
        the dialog open with no error to show for it — indistinguishable, from
        the outside, from a create that was rejected.
        """
        self.scroll_and_click(self.wait_for_element_clickable(self.FORM_SUBMIT))

    def wait_for_create_dialog_closed(self) -> None:
        """Wait until the create dialog is gone, i.e. the plan really was created.

        The read-back :meth:`submit_create_form` does not have, and an exact one
        rather than a proxy: ``NutrientPlanCreateDialog.onSubmit`` calls
        ``onCreated()`` -- which is what closes the dialog -- only **after**
        ``await api.createNutrientPlan(...)`` resolves. A rejected create runs
        ``handleError`` instead and leaves the dialog up, which TC-004-046
        already relies on. So the dialog being gone means the POST returned 2xx,
        and nothing weaker does.

        It also removes a race the implicit wait had been paying for. Callers
        used to follow the submit with ``wait_for_loading_complete()`` and then
        ``open()``. That wait is an *absence* poll on a skeleton that never
        mounts here, so its whole cost was the implicit wait inside its empty
        ``find_element`` -- roughly 3 s, which is what let the POST land before
        ``open()`` fired a hard navigation. #835 removed the implicit wait, the
        pause went to zero, and the navigation could abort the create in flight:
        TC-004-027 then found its freshly created plan missing from the list.

        Fails with what the dialog is actually showing. The first version of
        this let ``wait_for_element_hidden``'s bare ``TimeoutException`` out,
        whose message is the empty string -- it proved the create had failed and
        then said nothing about *why*, which is the diagnosis defect this whole
        round has been removing from other people's code.
        """
        try:
            self.poll(DEFAULT_TIMEOUT).until(EC.invisibility_of_element_located(self.CREATE_DIALOG))
        except TimeoutException as exc:
            raise AssertionError(
                f"The nutrient-plan create dialog was still open {DEFAULT_TIMEOUT}s "
                f"after submit, so `createNutrientPlan` never resolved 2xx — the "
                f"plan does not exist. Submit button enabled: "
                f"{self._submit_enabled()}. Field errors: {self._dialog_field_errors()}. "
                f"Page alerts: {self._alert_texts()}. An enabled button with no "
                f"error means the request failed or is still in flight; a disabled "
                f"one means the form never validated and the click was a no-op."
            ) from exc

    def _submit_enabled(self) -> bool | None:
        """Whether the dialog's submit button is enabled, or ``None`` if it is gone."""
        buttons = self.driver.find_elements(*self.FORM_SUBMIT)
        return buttons[0].is_enabled() if buttons else None

    def _dialog_field_errors(self) -> list[str]:
        """Every ``Mui-error`` helper text currently rendered inside the dialog."""
        return [
            (el.get_attribute("textContent") or "").strip()
            for el in self.driver.find_elements(
                By.CSS_SELECTOR,
                "[data-testid='nutrient-plan-create-dialog'] .MuiFormHelperText-root.Mui-error",
            )
        ]

    def _alert_texts(self) -> list[str]:
        """Every ``role='alert'`` text on the page — the app's error notifications."""
        return [
            (el.get_attribute("textContent") or "").strip()
            for el in self.driver.find_elements(By.CSS_SELECTOR, "[role='alert']")
        ]

    def cancel_create_form(self) -> None:
        """Cancel the create form."""
        btn = self.wait_for_element(self.FORM_CANCEL)
        self.scroll_and_click(btn)

    def get_name_field_value(self) -> str:
        """Return the current value of the name input field."""
        el = self.wait_for_element(self.FORM_NAME)
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
