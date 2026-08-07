"""Page object for the Watering Log list page (REQ-004)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class WateringLogListPage(BasePage):
    """Interact with the Watering Log list page (``/giessprotokoll``)."""

    PATH = "/giessprotokoll"

    # -- Page-level locators ------------------------------------------------
    PAGE = (By.CSS_SELECTOR, "[data-testid='watering-log-list-page']")
    CREATE_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-watering-log-button']")
    TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")
    # Linked plant chips of a row (Chip mounted on a RouterLink → a real
    # anchor). Addressed by the *per-plant* hook the product emits in both
    # layouts, `plant-link-<plant key>`, rather than by the container that
    # happens to hold it: `cell-plants` exists only in the desktop table, so
    # scoping to it made this reader return ``[]`` below `DataTable`'s `sm`
    # breakpoint — the mobile / full-mobile profiles (TC-004-092). Keying on the
    # thing being read is also what `spec/project/e2e-test-stability/` §G asks
    # for: key-based access into a responsive collection, one hook per plant, so
    # a specific plant stays addressable without counting chip positions.
    PLANT_CHIP_LINKS = (By.CSS_SELECTOR, "a[data-testid^='plant-link-']")
    # The `plants` group carrier, emitted unconditionally in both layouts
    # (desktop ``<td>`` / `MobileCard` chip). Its absence means the row is not
    # readable at all — which must fail loudly rather than read as "no plants".
    PLANT_GROUP = (
        By.CSS_SELECTOR,
        "[data-testid='cell-plants'], [data-testid='card-field-plants'],"
        " [data-testid='card-chip-plants']",
    )
    SEARCH_INPUT = (By.CSS_SELECTOR, "[data-testid='table-search-input'] input")
    SEARCH_CHIP = (By.CSS_SELECTOR, "[data-testid='search-chip']")
    SORT_CHIP = (By.CSS_SELECTOR, "[data-testid='sort-chip']")
    RESET_FILTERS = (By.CSS_SELECTOR, "[data-testid='reset-filters-button']")
    SHOWING_COUNT = (By.CSS_SELECTOR, "[data-testid='showing-count']")
    EMPTY_STATE = (By.CSS_SELECTOR, "[data-testid='empty-state']")

    # -- Create dialog locators ---------------------------------------------
    CREATE_DIALOG = (By.CSS_SELECTOR, ".MuiDialog-root [role='dialog']")
    PLANT_KEYS_INPUT = (By.CSS_SELECTOR, "[data-testid='plant-keys-input'] input")
    PLANT_KEYS_AUTOCOMPLETE = (By.CSS_SELECTOR, "[data-testid='plant-keys-autocomplete']")
    ADD_FERTILIZER_BUTTON = (By.CSS_SELECTOR, "[data-testid='add-fertilizer-button']")
    REMOVE_FERTILIZER_BUTTON_0 = (By.CSS_SELECTOR, "[data-testid='remove-fertilizer-0']")

    # -- Create form field locators -----------------------------------------
    FORM_APPLICATION_METHOD = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-application_method'] .MuiSelect-select",
    )
    FORM_VOLUME = (By.CSS_SELECTOR, "[data-testid='form-field-volume_liters'] input")
    FORM_WATER_SOURCE = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-water_source'] .MuiSelect-select",
    )
    FORM_IS_SUPPLEMENTAL = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-is_supplemental'] .MuiSwitch-root",
    )
    FORM_EC_BEFORE = (By.CSS_SELECTOR, "[data-testid='form-field-ec_before'] input")
    FORM_EC_AFTER = (By.CSS_SELECTOR, "[data-testid='form-field-ec_after'] input")
    FORM_PH_BEFORE = (By.CSS_SELECTOR, "[data-testid='form-field-ph_before'] input")
    FORM_PH_AFTER = (By.CSS_SELECTOR, "[data-testid='form-field-ph_after'] input")
    FORM_PERFORMED_BY = (By.CSS_SELECTOR, "[data-testid='form-field-performed_by'] input")
    FORM_NOTES = (By.CSS_SELECTOR, "[data-testid='form-field-notes'] textarea")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> WateringLogListPage:
        """Navigate to the watering log list and wait for it to load."""
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        return self

    # -- Table interactions -------------------------------------------------

    def get_row_count(self) -> int:
        """Return the number of visible table rows."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        return len(rows)

    def get_column_headers(self) -> list[str]:
        """Return all visible column header texts."""
        headers = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='data-table'] th")
        return [h.text for h in headers if h.text]

    #: Column the row is activated through. `loggedAt` is the identifying
    #: column: it is the first column, carries no `hideBelowBreakpoint`, is not
    #: in the page's `optionalColumnChecks` (so it is never dropped), renders a
    #: plain formatted timestamp, and `MobileCard` keys it as `titleId`, so the
    #: same id addresses it in the card layout too.
    #:
    #: Explicitly NOT the `plants` column: it renders one `Chip` per plant as a
    #: `RouterLink` with `onClick={(e) => e.stopPropagation()}`, and clicking
    #: the row's *centre* landed on that chip at 820px — the row navigated to
    #: the plant instead of the watering log (TC-REQ-004-J090, tablet profile).
    LOGGED_AT_COLUMN_ID = "loggedAt"

    def click_row(self, index: int = 0) -> None:
        """Open the watering log at *index* via its inert `loggedAt` cell."""
        self.click_data_table_row(
            index, self.LOGGED_AT_COLUMN_ID, self.TABLE_ROWS, "watering log row"
        )

    def get_row_cell(self, index: int, col_id: str) -> str:
        """Return the text of the *col_id* cell in the row at *index*.

        Addresses the cell by column id rather than by position, so column
        reordering does not break callers.

        Raises ``IndexError`` when *index* is out of range. A missing row is a
        different failure than an empty cell, and returning ``""`` silently
        would surface it downstream as a confusing value mismatch instead of
        "the row you asked for is not there".
        """
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        if not -len(rows) <= index < len(rows):
            raise IndexError(
                f"Watering-log row index {index} out of range (table has {len(rows)} rows)"
            )
        return self.get_row_cell_text(rows[index], col_id)

    def get_row_plant_links(self, index: int) -> list[tuple[str, str]]:
        """Return ``(label, href)`` for each linked plant chip in the row at *index*.

        The ``plants`` column renders every resolved plant as a chip mounted on a
        router link, so a correctly linked chip is an ``<a href=…>`` carrying the
        plant's own ``plant-link-<key>`` hook — the same hook in the desktop
        table and in the `MobileCard`, which is why this reader is addressed by
        it rather than by a layout-specific container.

        Returns the pairs rather than a verdict: the page object reports state,
        the caller decides what the state has to be. An empty list means the
        chips rendered without a link (or no plant is attached at all) — a
        statement this method is only allowed to make once it has seen the row's
        ``plants`` group; a row that keys none is unreadable and raises.

        Raises ``IndexError`` when *index* is out of range, mirroring
        :meth:`get_row_cell`.
        """
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        if not -len(rows) <= index < len(rows):
            raise IndexError(
                f"Watering-log row index {index} out of range (table has {len(rows)} rows)"
            )
        row = rows[index]
        if not row.find_elements(*self.PLANT_GROUP):
            raise AssertionError(
                f"The 'plants' group of watering-log row {index} is not readable: "
                "the row keys neither 'cell-plants' (desktop table) nor "
                "'card-field-plants'/'card-chip-plants' (MobileCard). Returning an "
                "empty link list here would report 'no linked plant' for a row that "
                "was never read."
            )
        anchors = row.find_elements(*self.PLANT_CHIP_LINKS)
        return [(a.text.strip(), a.get_attribute("href") or "") for a in anchors]

    def get_row_texts(self) -> list[list[str]]:
        """Return the readable text fragments of every visible row."""
        return self.get_all_row_text_fragments()

    # -- Search and filter --------------------------------------------------

    def search(self, term: str) -> None:
        """Type *term* into the search field.

        **This does not settle the table.** The comment that used to claim it
        did -- "callers can rely on the result being settled once this method
        returns" -- was wrong by exactly the margin that matters: the sleep
        below is the *same* 300 ms as the debounce it is waiting out, so whether
        the re-render has happened on return is a coin flip. A caller that then
        reads or counts rows must gate on
        :meth:`BasePage.wait_for_search_applied` (#835).
        """
        import time

        search_input = self.wait_for_element_clickable(self.SEARCH_INPUT)
        search_input.clear()
        search_input.send_keys(term)
        # Nudges past the bulk of the 300 ms debounce so a following poll
        # usually succeeds on its first cycle. It is not the post-condition.
        time.sleep(0.3)

    def clear_search(self) -> None:
        """Clear the search field."""
        import time

        search_input = self.wait_for_element_clickable(self.SEARCH_INPUT)
        search_input.clear()
        search_input.send_keys(Keys.BACKSPACE)
        # debounce: bounded, justified (same 300ms debounce as search())
        time.sleep(0.3)

    def has_table(self) -> bool:
        """Return True if the DataTable is present."""
        return len(self.driver.find_elements(*self.TABLE)) > 0

    def get_showing_count_text(self) -> str:
        """Return the text from the 'showing X of Y' counter."""
        el = self.wait_for_element(self.SHOWING_COUNT)
        return el.text

    def click_reset_filters(self) -> None:
        """Click the reset filters button."""
        self.wait_for_element_clickable(self.RESET_FILTERS).click()

    def has_reset_filters_button(self) -> bool:
        """Return True if the reset-filters button exists."""
        return len(self.driver.find_elements(*self.RESET_FILTERS)) > 0

    # -- Create dialog ------------------------------------------------------

    def click_create(self) -> None:
        """Click the Create button and wait for the dialog."""
        self.wait_for_element_clickable(self.CREATE_BUTTON).click()
        self.wait_for_element_visible(self.CREATE_DIALOG)

    def is_create_dialog_open(self) -> bool:
        """Return True if the create dialog is visible."""
        return len(self.driver.find_elements(*self.CREATE_DIALOG)) > 0

    def has_plant_autocomplete(self) -> bool:
        """Return True if the plant-keys autocomplete is present in the dialog."""
        return len(self.driver.find_elements(*self.PLANT_KEYS_AUTOCOMPLETE)) > 0

    def click_add_fertilizer(self) -> None:
        """Click 'add fertilizer' coordinate-free and wait for the new row.

        Coordinate-free because this button is the shape
        :meth:`BasePage.click_coordinate_free` was written for, reached from a
        second direction. It is the *last* control of a scrolling
        ``DialogContent`` -- the fertilizer rows render above it, the
        performed-by and notes fields below -- so on the light profile it sits
        below the dialog's fold. `scroll_into_view` centres it, then
        ``WebElement.click()`` resolves an in-view centre point and dispatches
        at those coordinates, and any residual scrolling in between puts the
        point off the button. Nothing raises: the hit-test passed, the events
        went out, and ``append()`` never ran. That is why the JS fallback in
        `scroll_and_click` could not save it either -- the fallback only fires
        on an exception, and this failure mode produces none.

        Measured as a 2-in-5 flake on TC-004-106 (runs `20260806_204527` and
        `20260806_214842`): the failure screenshot shows the button in view,
        no fertilizer row, and 15 s of `wait_for_element_visible` spent on a row
        that was never appended. The same class is on record for the mobile
        profile in `click_coordinate_free`; this is its desktop instance.

        Sound for this target: the button activates on ``onClick``
        (``append({...})`` from `useFieldArray`), which is pure client-side
        state, so ``HTMLElement.click()`` produces exactly the activation a
        pointer does. `click_coordinate_free` rejects a disabled control or a
        mousedown-only opener itself, so the soundness condition is enforced
        rather than assumed.
        """
        self.click_coordinate_free(self.wait_for_element_clickable(self.ADD_FERTILIZER_BUTTON))
        self.wait_for_element_visible(self.REMOVE_FERTILIZER_BUTTON_0)

    def has_remove_fertilizer_button(self) -> bool:
        """Return True if a remove-fertilizer button is present (row 0).

        Waits, even though :meth:`click_add_fertilizer` already waited for this
        very button -- because something between the two can take it away again
        and put it straight back. TC-REQ-004-W004b failed with the action's wait
        satisfied and this read empty one line later, with only a `screenshot()`
        checkpoint in between: `_cdp_full_page_screenshot` passes
        ``captureBeyondViewport``, which resizes the layout viewport to the
        document height, and MUI re-evaluates every `useMediaQuery` on the
        resulting resize. The checkpoint is not observation-neutral, so a raw
        read taken after one is exposed to a re-render it did not cause.

        The checkpoint now verifies the restore and holds one frame before
        returning (#959, ``conftest._settle_after_capture``), which removes the
        *known* instance of that window. The wait here stays: it costs nothing
        when the button is there, and the frame barrier is a bounded heuristic
        about React's scheduler, not a proof that no re-render can outlive it.
        """
        return bool(self.await_presence(self.REMOVE_FERTILIZER_BUTTON_0))

    def select_first_plant(self) -> bool:
        """Type into the plant autocomplete and select the first option.

        Returns True if a plant was selected, False if no options appeared.
        """
        import time

        option_locator = (By.CSS_SELECTOR, "li[role='option']")
        input_el = self.wait_for_element_clickable(self.PLANT_KEYS_INPUT)
        input_el.click()
        # Type a space to trigger the dropdown, then clear it
        input_el.send_keys(" ")
        try:
            self.poll(5).until(lambda d: len(d.find_elements(*option_locator)) > 0)
        except Exception:
            pass  # options may not populate for an empty catalog
        input_el.clear()
        # bounded: clearing re-filters via MUI's ~300ms client-side debounce,
        # which exposes no DOM transition once options already exist
        time.sleep(0.3)

        # MUI Autocomplete renders options in a listbox
        options = self.driver.find_elements(*option_locator)
        if not options:
            # Try clicking the input again to open the dropdown
            input_el.click()
            try:
                self.poll(5).until(lambda d: len(d.find_elements(*option_locator)) > 0)
            except Exception:
                pass
            options = self.driver.find_elements(*option_locator)

        if options:
            self.click_menu_option(options[0])
            self.wait_for_element_hidden(option_locator)
            return True
        return False

    def select_plant_by_text(self, text: str) -> bool:
        """Type *text* into the plant autocomplete and pick the matching option.

        Returns True if an option was selected, False if none appeared. Used by
        the self-provisioning journey to attach the freshly created plant
        (identified by its unique instance id) to the watering log.

        The dialog loads up to 500 plant options asynchronously on open, so a
        fixed sleep + single read races the fetch. Wait explicitly for an option
        and retry the type (mirrors ``select_first_plant``); the plant label is
        ``"{instance_id} ({name})"`` so prefer the option whose text starts with
        the instance id rather than blindly taking the first.

        Matched via ``textContent``, not ``.text``: WebElement.text yields only
        *rendered* text, so an option scrolled outside the popover's visible
        area (MUI scrolls to the selected item on open) reads back as "" and
        would never match. Clicked via :meth:`click_menu_option` rather than
        :meth:`scroll_and_click` -- the previous coordinate-based click landed
        on whichever option had slid into that spot while an open MUI menu was
        still repositioning (#778 A2).
        """

        for _ in range(3):
            input_el = self.wait_for_element_clickable(self.PLANT_KEYS_INPUT)
            input_el.click()
            self.clear_and_fill(input_el, text)
            try:
                self.poll(5).until(
                    lambda d: len(d.find_elements(By.CSS_SELECTOR, "li[role='option']")) > 0
                )
            except Exception:
                continue  # options not populated yet — re-type and retry
            options = self.driver.find_elements(By.CSS_SELECTOR, "li[role='option']")
            target = next(
                (
                    o
                    for o in options
                    if (o.get_attribute("textContent") or "").strip().startswith(text)
                ),
                options[0] if options else None,
            )
            if target is not None:
                self.click_menu_option(target)
                self.wait_for_element_hidden((By.CSS_SELECTOR, "li[role='option']"))
                return True
        return False

    def fill_volume(self, volume: float) -> None:
        """Fill the volume_liters field in the create dialog."""
        el = self.wait_for_element_clickable(self.FORM_VOLUME)
        self.clear_and_fill(el, str(volume))

    def select_application_method(self, label_text: str) -> None:
        """Select an application method by its visible label."""
        self.select_option("application_method", label_text)

    def select_water_source(self, label_text: str) -> None:
        """Select a water source by its visible label."""
        self.select_option("water_source", label_text)

    def fill_ec_before(self, value: float) -> None:
        """Fill the EC before field."""
        el = self.wait_for_element_clickable(self.FORM_EC_BEFORE)
        self.clear_and_fill(el, str(value))

    def fill_ph_before(self, value: float) -> None:
        """Fill the pH before field."""
        el = self.wait_for_element_clickable(self.FORM_PH_BEFORE)
        self.clear_and_fill(el, str(value))

    def fill_notes(self, notes: str) -> None:
        """Fill the Notes textarea."""
        el = self.wait_for_element_clickable(self.FORM_NOTES)
        self.clear_and_fill(el, notes)

    def submit_create_form(self) -> None:
        """Submit the create form."""
        btn = self.wait_for_element_clickable(self.FORM_SUBMIT)
        self.scroll_and_click(btn)

    def cancel_create_form(self) -> None:
        """Cancel the create dialog."""
        btn = self.wait_for_element_clickable(self.FORM_CANCEL)
        self.scroll_and_click(btn)

    def select_option(self, field_testid: str, value_text: str) -> None:
        """Open a `FormSelectField` and pick the option carrying *value_text*.

        Routed through the shared, verified helpers. The predecessor opened the
        Select with a coordinate click on ``.MuiSelect-select`` (MUI opens a
        Select from ``onMouseDown`` only, so a swallowed click opened nothing),
        resolved the option through an **unscoped** ``//li[@role='option']``
        XPath matched on its *translated* label with ``contains()`` — which
        prefix-matches, so a label that is the prefix of another picks the wrong
        entry — and verified nothing afterwards.

        ``open_select`` raises unless the menu is verifiably open, and
        ``select_option_by_label`` resolves the label to the option's own
        ``data-value`` and delegates to ``select_option_by_value``, which
        dispatches on the resolved element and reads the committed value back.
        The label stays the caller's vocabulary (the watering journeys pass the
        rendered German enum labels), but an exact match now wins over a
        substring match irrespective of DOM order, so "Gießen" can no longer be
        answered by whichever option happens to contain it first.
        """
        self.open_select(field_testid)
        self.select_option_by_label(value_text)

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
