"""Page object for the Harvest Batch detail page (REQ-007)."""

from __future__ import annotations

from contextlib import suppress

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import DEFAULT_TIMEOUT, IMPLICIT_WAIT_EQUIVALENT, BasePage


class HarvestBatchDetailPage(BasePage):
    """Interact with the Harvest Batch detail page (``/ernte/batches/:key``)."""

    # -- Page-level locators ------------------------------------------------
    PAGE = (By.CSS_SELECTOR, "[data-testid='harvest-batch-detail-page']")
    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")
    QUALITY_CHIP_HEADER = (
        By.CSS_SELECTOR,
        "[data-testid='harvest-batch-detail-page'] > div:first-child .MuiChip-root",
    )

    # -- Tab locators -------------------------------------------------------
    TABS = (By.CSS_SELECTOR, "button[role='tab']")

    # -- Error display ------------------------------------------------------
    ERROR_DISPLAY = (By.CSS_SELECTOR, "[data-testid='error-display']")

    # -- Tab 0: Details table -----------------------------------------------
    DETAILS_TABLE = (
        By.CSS_SELECTOR,
        "[data-testid='harvest-batch-detail-page'] table",
    )
    DETAILS_ROWS = (
        By.CSS_SELECTOR,
        "[data-testid='harvest-batch-detail-page'] table tr",
    )

    # -- Tab 1: Quality — display table or create form ----------------------
    QUALITY_TABLE = (By.CSS_SELECTOR, "table[aria-label]")
    QUALITY_FORM = (By.CSS_SELECTOR, "form")
    QUALITY_ASSESSED_BY = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-assessed_by'] input",
    )
    QUALITY_APPEARANCE = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-appearance_score'] input",
    )
    QUALITY_AROMA = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-aroma_score'] input",
    )
    QUALITY_COLOR = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-color_score'] input",
    )
    QUALITY_DEFECTS = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-defects'] input",
    )
    QUALITY_NOTES = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-notes'] textarea",
    )
    QUALITY_LINEAR_PROGRESS = (By.CSS_SELECTOR, ".MuiLinearProgress-root")

    # -- Tab 2: Yield — display table or create form -----------------------
    YIELD_PER_PLANT = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-yield_per_plant_g'] input",
    )
    YIELD_PER_M2 = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-yield_per_m2_g'] input",
    )
    YIELD_TOTAL = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-total_yield_g'] input",
    )
    YIELD_USABLE = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-usable_yield_g'] input",
    )
    YIELD_TRIM_WASTE = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-trim_waste_percent'] input",
    )

    # -- Tab 3: Edit form --------------------------------------------------
    EDIT_HARVEST_TYPE = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-harvest_type'] .MuiSelect-select",
    )
    EDIT_QUALITY_GRADE = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-quality_grade'] .MuiSelect-select",
    )
    EDIT_HARVESTER = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-harvester'] input",
    )
    EDIT_WET_WEIGHT = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-wet_weight_g'] input",
    )
    EDIT_ESTIMATED_DRY = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-estimated_dry_weight_g'] input",
    )
    EDIT_ACTUAL_DRY = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-actual_dry_weight_g'] input",
    )
    EDIT_NOTES = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-notes'] textarea",
    )

    # -- Shared form buttons ------------------------------------------------
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    # -- Snackbar / notification -------------------------------------------
    SNACKBAR = (
        By.CSS_SELECTOR,
        ".MuiSnackbar-root .MuiAlert-message, .notistack-MuiContent",
    )

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self, batch_key: str) -> HarvestBatchDetailPage:
        """Navigate to the harvest batch detail page for *batch_key*."""
        self.navigate(f"/ernte/batches/{batch_key}")
        # Wait for either the page or an error display
        self.poll(15).until(
            lambda d: d.find_elements(*self.PAGE) or d.find_elements(*self.ERROR_DISPLAY)
        )
        return self

    def open_and_wait(self, batch_key: str) -> HarvestBatchDetailPage:
        """Navigate and wait specifically for the detail page (not error)."""
        self.navigate(f"/ernte/batches/{batch_key}")
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        return self

    # -- Page info ----------------------------------------------------------

    def get_page_title_text(self) -> str:
        """Return the page title text (batch ID)."""
        el = self.wait_for_element(self.PAGE_TITLE)
        return el.text

    def get_header_quality_chip(self) -> str | None:
        """Return the text of the quality chip in the page header, or None."""
        chips = self.driver.find_elements(*self.QUALITY_CHIP_HEADER)
        return chips[0].text if chips else None

    def is_page_loaded(self) -> bool:
        """Return True if the detail page testid is visible.

        No call site in this suite as of #946 wave 4 -- left unanchored
        rather than speculatively converted, since there is no caller whose
        polarity or timing this reader's fix could be verified against.
        """
        return len(self.driver.find_elements(*self.PAGE)) > 0

    # -- Tab navigation -----------------------------------------------------

    def get_tab_labels(self) -> list[str]:
        """Return the labels of all visible tabs."""
        tabs = self.tab_elements(self.TABS)
        return [t.text for t in tabs]

    def click_tab(self, index: int) -> None:
        """Click the tab at *index* (0-based)."""
        tabs = self.tab_elements(self.TABS)
        if index < len(tabs):
            self.scroll_and_click(tabs[index])
        else:
            raise ValueError(f"Tab index {index} out of range (found {len(tabs)} tabs)")

    def get_active_tab_index(self) -> int:
        """Return the index of the currently selected tab."""
        tabs = self.tab_elements(self.TABS)
        for i, tab in enumerate(tabs):
            if tab.get_attribute("aria-selected") == "true":
                return i
        return -1

    # -- Tab 0: Details -----------------------------------------------------

    def get_detail_table_text(self) -> str:
        """Return the combined text of the details table."""
        table = self.wait_for_element(self.DETAILS_TABLE)
        return table.text

    def get_detail_field_value(self, field_label: str) -> str:
        """Return the value cell text for a given field label in the details table."""
        rows = self.driver.find_elements(*self.DETAILS_ROWS)
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            ths = row.find_elements(By.TAG_NAME, "th")
            if ths and field_label in ths[0].text:
                return cells[0].text if cells else ""
        return ""

    # -- Tab 1: Quality -----------------------------------------------------

    #: The Quality and Yield tabs each render one of these two shapes once
    #: their tab panel has committed -- a create form when no assessment/
    #: metric exists yet, a display table once one does. `quality` and
    #: `yieldMetric` are resolved together with `batch` inside the same
    #: `load()` before the page-level `LoadingSkeleton` clears
    #: (`HarvestBatchDetailPage.tsx:267`), so the gap this closes is not that
    #: initial fetch -- it is the render commit after `click_tab()` (a plain
    #: `setTab` state flip, no wait of its own) and, on the create-happy-path
    #: tests, the window between `submit_form()` and the POST response that
    #: swaps the form for the table. `wait_for_loading_complete()`, which
    #: every call site here already runs, is a no-op for both: neither
    #: touches the page-level `loading` flag this page's skeleton is keyed
    #: on.
    TAB_CONTENT_BRANCHES = (QUALITY_FORM, QUALITY_TABLE)

    def wait_for_tab_content(self, timeout: int = IMPLICIT_WAIT_EQUIVALENT) -> None:
        """Wait until the active tab has rendered its form or its display table.

        Deliberately does not raise: an anchor for the readers below, not an
        assertion of its own -- see :meth:`PflegeDashboardPage.wait_for_dashboard_content`
        for the same shape and rationale.
        """
        with suppress(AssertionError):
            self.wait_for_any_present(
                self.TAB_CONTENT_BRANCHES, "quality/yield tab content", timeout=timeout
            )

    def is_quality_form_visible(self) -> bool:
        """Return True if the quality create form is visible.

        Anchored on :meth:`wait_for_tab_content`: its only call site
        (``test_quality_tab_shows_form_or_table``) asserts ``has_form or
        has_table`` unconditionally, and three more gate a ``pytest.skip(...)``
        on ``not is_quality_form_visible()`` right after ``click_tab(1)`` --
        the skip-gate vacuity from #946 wave 1, here on a tab-content read
        instead of a dashboard-section one.
        """
        self.wait_for_tab_content()
        forms = self.driver.find_elements(*self.QUALITY_FORM)
        return len(forms) > 0

    def is_quality_table_visible(self) -> bool:
        """Return True if a quality assessment display table is visible.

        See :meth:`is_quality_form_visible` for why the anchor is
        :meth:`wait_for_tab_content`. Also feeds the create-happy-path
        assertion straight after ``submit_form()``, which has no other
        post-condition wait for the form-to-table swap.
        """
        self.wait_for_tab_content()
        tables = self.driver.find_elements(*self.QUALITY_TABLE)
        return len(tables) > 0

    def fill_quality_assessed_by(self, name: str) -> None:
        """Fill the 'assessed_by' field."""
        el = self.wait_for_element_clickable(self.QUALITY_ASSESSED_BY)
        el.clear()
        el.send_keys(name)

    def fill_quality_appearance(self, score: int) -> None:
        """Fill the appearance score field."""
        el = self.wait_for_element_clickable(self.QUALITY_APPEARANCE)
        el.clear()
        el.send_keys(str(score))

    def fill_quality_aroma(self, score: int) -> None:
        """Fill the aroma score field."""
        el = self.wait_for_element_clickable(self.QUALITY_AROMA)
        el.clear()
        el.send_keys(str(score))

    def fill_quality_color(self, score: int) -> None:
        """Fill the color score field."""
        el = self.wait_for_element_clickable(self.QUALITY_COLOR)
        el.clear()
        el.send_keys(str(score))

    def add_defect(self, defect: str) -> None:
        """Add a defect chip by typing and pressing Enter."""
        import time

        el = self.wait_for_element_clickable(self.QUALITY_DEFECTS)
        el.send_keys(defect)
        el.send_keys(Keys.ENTER)
        # The MUI Autocomplete chip-insert animation is time-based (no DOM
        # condition to wait on); bounded to 0.3s to let the chip settle
        # before the caller adds another one or submits the form.
        time.sleep(0.3)

    def fill_quality_notes(self, notes: str) -> None:
        """Fill the quality notes textarea."""
        el = self.wait_for_element_clickable(self.QUALITY_NOTES)
        el.clear()
        el.send_keys(notes)

    def get_quality_table_text(self) -> str:
        """Return the full text of the quality assessment table."""
        table = self.wait_for_element(self.QUALITY_TABLE)
        return table.text

    def get_overall_score_color(self) -> str:
        """Return the MUI color class of the overall score LinearProgress."""
        progress_bars = self.driver.find_elements(*self.QUALITY_LINEAR_PROGRESS)
        # The overall score is typically the last (or most prominent) progress bar
        for bar in progress_bars:
            classes = bar.get_attribute("class") or ""
            if "colorSuccess" in classes:
                return "success"
            if "colorWarning" in classes:
                return "warning"
            if "colorError" in classes:
                return "error"
        return "unknown"

    def get_defect_chips(self) -> list[str]:
        """Return the text of all defect chips visible on the quality tab."""
        chips = self.driver.find_elements(By.CSS_SELECTOR, ".MuiChip-colorError .MuiChip-label")
        return [c.text for c in chips]

    # -- Tab 2: Yield -------------------------------------------------------

    def is_yield_form_visible(self) -> bool:
        """Return True if the yield create form is visible.

        Same shape, same locators and the same anchor as
        :meth:`is_quality_form_visible` -- the Yield tab reuses the generic
        ``form``/``table[aria-label]`` locators rather than tab-specific
        testids, so it shares :meth:`wait_for_tab_content`. Two call sites
        gate a ``pytest.skip(...)`` right after ``click_tab(2)``.
        """
        self.wait_for_tab_content()
        forms = self.driver.find_elements(*self.QUALITY_FORM)
        return len(forms) > 0

    def is_yield_table_visible(self) -> bool:
        """Return True if a yield metrics display table is visible.

        See :meth:`is_quality_form_visible` for the anchor rationale.
        """
        self.wait_for_tab_content()
        tables = self.driver.find_elements(*self.QUALITY_TABLE)
        return len(tables) > 0

    def fill_yield_per_plant(self, value: float) -> None:
        """Fill yield per plant field."""
        el = self.wait_for_element_clickable(self.YIELD_PER_PLANT)
        el.clear()
        el.send_keys(str(value))

    def fill_yield_per_m2(self, value: float) -> None:
        """Fill yield per m2 field."""
        el = self.wait_for_element_clickable(self.YIELD_PER_M2)
        el.clear()
        el.send_keys(str(value))

    def fill_yield_total(self, value: float) -> None:
        """Fill total yield field."""
        el = self.wait_for_element_clickable(self.YIELD_TOTAL)
        el.clear()
        el.send_keys(str(value))

    def fill_yield_usable(self, value: float) -> None:
        """Fill usable yield field."""
        el = self.wait_for_element_clickable(self.YIELD_USABLE)
        el.clear()
        el.send_keys(str(value))

    def fill_yield_trim_waste(self, value: float) -> None:
        """Fill trim waste percent field."""
        el = self.wait_for_element_clickable(self.YIELD_TRIM_WASTE)
        el.clear()
        el.send_keys(str(value))

    def get_yield_table_text(self) -> str:
        """Return the full text of the yield metrics table."""
        table = self.wait_for_element(self.QUALITY_TABLE)
        return table.text

    # -- Tab 3: Edit --------------------------------------------------------

    def get_edit_harvester_value(self) -> str:
        """Return the current value of the harvester field in the edit form."""
        el = self.wait_for_element(self.EDIT_HARVESTER)
        return el.get_attribute("value") or ""

    def fill_edit_harvester(self, name: str) -> None:
        """Set the harvester field in the edit form."""
        el = self.wait_for_element_clickable(self.EDIT_HARVESTER)
        el.clear()
        el.send_keys(name)

    def fill_edit_wet_weight(self, weight: float) -> None:
        """Set the wet weight field in the edit form."""
        el = self.wait_for_element_clickable(self.EDIT_WET_WEIGHT)
        el.clear()
        el.send_keys(str(weight))

    def fill_edit_estimated_dry(self, weight: float) -> None:
        """Set the estimated dry weight field."""
        el = self.wait_for_element_clickable(self.EDIT_ESTIMATED_DRY)
        el.clear()
        el.send_keys(str(weight))

    def fill_edit_actual_dry(self, weight: float) -> None:
        """Set the actual dry weight field."""
        el = self.wait_for_element_clickable(self.EDIT_ACTUAL_DRY)
        el.clear()
        el.send_keys(str(weight))

    def fill_edit_notes(self, notes: str) -> None:
        """Fill the notes textarea in the edit tab."""
        el = self.wait_for_element_clickable(self.EDIT_NOTES)
        el.clear()
        el.send_keys(notes)

    def select_edit_option(self, field_testid: str, value_text: str) -> None:
        """Open an MUI Select in the edit form and pick an option.

        Routed through the shared, verified select helpers -- see
        ``BotanicalFamilyListPage.select_option`` for the rationale.
        """
        self.open_select(field_testid)
        self.select_option_by_label(value_text)

    def is_submit_disabled(self) -> bool:
        """Return True if the submit/save button is disabled."""
        btn = self.wait_for_element(self.FORM_SUBMIT)
        return not btn.is_enabled()

    # -- Shared form actions ------------------------------------------------

    def submit_form(self) -> None:
        """Click the submit button."""
        self.wait_and_click(self.FORM_SUBMIT)

    def cancel_form(self) -> None:
        """Click the cancel button."""
        self.wait_and_click(self.FORM_CANCEL)

    # -- Validation errors --------------------------------------------------

    def get_validation_error(self, field_name: str) -> str:
        """Return the validation error text for a form field, waiting for it to render.

        All three call sites read this (or :meth:`has_validation_error`) as the
        sole assertion straight after ``submit_form()`` +
        ``wait_for_loading_complete()`` -- which is a no-op here, since a
        client-side zod validation error never touches the page-level loading
        skeleton this method used to be silently unguarded against. Genuinely
        waits rather than anchoring on a page container, because there is no
        broader "settled" region to anchor on: the error surface itself, or
        its absence once the wait is spent, is the only signal.

        Bounded on the short `IMPLICIT_WAIT_EQUIVALENT` budget, not the full
        default: one call site reads this as one arm of ``has_validation_error(
        ...) or is_submit_disabled()``, where the field going the other way is
        a legitimate, expected outcome -- a full-length wait there would be
        charged on every run that takes that branch.
        """
        locator = (
            By.CSS_SELECTOR,
            f"[data-testid='form-field-{field_name}'] .MuiFormHelperText-root.Mui-error",
        )
        if not self.is_visible_within(locator, timeout=IMPLICIT_WAIT_EQUIVALENT):
            return ""
        elements = self.driver.find_elements(*locator)
        return elements[0].text if elements else ""

    def has_validation_error(self, field_name: str) -> bool:
        """Return True if a validation error is visible for *field_name*."""
        return bool(self.get_validation_error(field_name))

    # -- Error display ------------------------------------------------------

    def is_error_displayed(self) -> bool:
        """Return True if an error display component is visible.

        Deliberately instantaneous, not anchored: its one call site
        (``test_detail_page_404_for_unknown_key``) reads it right after
        ``open()``, which itself waits for ``self.PAGE or self.ERROR_DISPLAY``
        -- for a 404 key, `batch` never resolves, so ``open()`` can only have
        returned via the ``ERROR_DISPLAY`` branch. The readiness this method
        reports has already been bought by the caller.
        """
        elements = self.driver.find_elements(*self.ERROR_DISPLAY)
        return len(elements) > 0 and elements[0].is_displayed()

    # -- Snackbar -----------------------------------------------------------

    def is_snackbar_visible(self) -> bool:
        """Return True if a success snackbar is visible."""
        els = self.driver.find_elements(*self.SNACKBAR)
        return any(el.is_displayed() for el in els) if els else False

    def is_form_submit_visible(self, timeout: int = DEFAULT_TIMEOUT) -> bool:
        """Return True if the form submit button is present, waiting for it to render.

        Its one call site (``test_edit_tab_shows_prefilled_form``) reads this
        right after ``click_tab(3)`` -- a plain ``setTab`` flip with no fetch
        of its own, so ``wait_for_loading_complete()`` does not cover the
        render commit. Genuinely waits rather than sampling once.
        """
        return self.is_visible_within(self.FORM_SUBMIT, timeout=timeout)
