"""Page object for the Tank detail page (REQ-014)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from .base_page import DEFAULT_TIMEOUT, IMPLICIT_WAIT_EQUIVALENT, BasePage


class TankDetailPage(BasePage):
    """Interact with the Tank detail page (``/standorte/tanks/:key``)."""

    # ── Page-level locators ────────────────────────────────────────────
    PAGE = (By.CSS_SELECTOR, "[data-testid='tank-detail-page']")

    # Delete button (always visible)
    DELETE_BUTTON = (By.CSS_SELECTOR, "[data-testid='tank-delete-button']")

    # ── Tab locators ───────────────────────────────────────────────────
    TABS = (By.CSS_SELECTOR, "button[role='tab']")

    # ── ConfirmDialog ──────────────────────────────────────────────────
    CONFIRM_DIALOG = (By.CSS_SELECTOR, "[data-testid='confirm-dialog']")
    CONFIRM_BUTTON = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-confirm']")
    CONFIRM_CANCEL = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-cancel']")

    # ── Tab 0 – Details: info tables ──────────────────────────────────
    DETAIL_TABLES = (By.CSS_SELECTOR, "[data-testid='tank-detail-page'] .MuiCard-root")

    # ── Tab 1 – States ─────────────────────────────────────────────────
    RECORD_STATE_BUTTON = (By.CSS_SELECTOR, "[data-testid='tank-record-state-button']")
    STATES_TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    STATES_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")

    # ── TankStateCreateDialog ──────────────────────────────────────────
    STATE_DIALOG = (By.CSS_SELECTOR, ".MuiDialog-root [role='dialog']")
    STATE_FORM_PH = (By.CSS_SELECTOR, "[data-testid='form-field-ph'] input")
    STATE_FORM_EC = (By.CSS_SELECTOR, "[data-testid='form-field-ec_ms'] input")
    STATE_FORM_TEMP = (By.CSS_SELECTOR, "[data-testid='form-field-water_temp_celsius'] input")
    STATE_FORM_FILL_PERCENT = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-fill_level_percent'] input",
    )
    STATE_FORM_FILL_LITERS = (By.CSS_SELECTOR, "[data-testid='form-field-fill_level_liters'] input")
    STATE_FORM_TDS = (By.CSS_SELECTOR, "[data-testid='form-field-tds_ppm'] input")
    # Scoped to the dialog: MUI portals a Dialog to the end of <body>, so an
    # unscoped `[data-testid='form-submit-button']` resolves to whichever
    # button with that testid comes FIRST in document order -- the in-page
    # Edit tab's own submit button (Tab 5, below), not this dialog's. See #778
    # A5.
    STATE_FORM_SUBMIT = (
        By.CSS_SELECTOR,
        ".MuiDialog-root [role='dialog'] [data-testid='form-submit-button']",
    )
    STATE_FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    # ── Tab 2 – Maintenance ────────────────────────────────────────────
    LOG_MAINTENANCE_BUTTON = (By.CSS_SELECTOR, "[data-testid='tank-log-maintenance-button']")
    MAINTENANCE_TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    MAINTENANCE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")

    # ── MaintenanceLogDialog ───────────────────────────────────────────
    MAINTENANCE_DIALOG = (By.CSS_SELECTOR, ".MuiDialog-root [role='dialog']")
    MAINT_FORM_TYPE = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-maintenance_type'] .MuiSelect-select",
    )
    MAINT_FORM_PERFORMED_BY = (By.CSS_SELECTOR, "[data-testid='form-field-performed_by'] input")
    MAINT_FORM_DURATION = (By.CSS_SELECTOR, "[data-testid='form-field-duration_minutes'] input")
    MAINT_FORM_PRODUCTS = (By.CSS_SELECTOR, "[data-testid='form-field-products_used'] input")
    MAINT_FORM_NOTES = (By.CSS_SELECTOR, "[data-testid='form-field-notes'] textarea")
    # Scoped to the dialog -- see STATE_FORM_SUBMIT above for the rationale.
    MAINT_FORM_SUBMIT = (
        By.CSS_SELECTOR,
        ".MuiDialog-root [role='dialog'] [data-testid='form-submit-button']",
    )
    MAINT_FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    # ── Tab 3 – Schedules ─────────────────────────────────────────────
    SCHEDULES_TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    SCHEDULES_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")

    # ── Tab 4 – Fills ────────────────────────────────────────────────────
    # (Tab for tank fill events – no specific locators needed beyond data-table)

    # ── Tab 5 – Edit form ──────────────────────────────────────────────
    EDIT_FORM_NAME = (By.CSS_SELECTOR, "[data-testid='form-field-name'] input")
    EDIT_FORM_TANK_TYPE = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-tank_type'] .MuiSelect-select",
    )
    EDIT_FORM_VOLUME = (By.CSS_SELECTOR, "[data-testid='form-field-volume_liters'] input")
    EDIT_FORM_MATERIAL = (By.CSS_SELECTOR, "[data-testid='form-field-material'] .MuiSelect-select")
    EDIT_FORM_HAS_LID = (By.CSS_SELECTOR, "[data-testid='form-field-has_lid'] .MuiSwitch-root")
    EDIT_FORM_NOTES = (By.CSS_SELECTOR, "[data-testid='form-field-notes'] textarea")
    # This is genuinely the *in-page* submit button (no dialog wraps this tab),
    # left unscoped on purpose: it is the element STATE_FORM_SUBMIT and
    # MAINT_FORM_SUBMIT above used to collide with (see #778 A5).
    EDIT_FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    EDIT_FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    # Alert banner rendered with MUI Alert. Scoped to the page root: an
    # unscoped ``.MuiAlert-root`` also matches MainLayout's light-mode warning
    # banner, which renders as a sibling of this page's root, not a
    # descendant. See #778 A11.
    ALERTS = (By.CSS_SELECTOR, "[data-testid='tank-detail-page'] .MuiAlert-root")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self, tank_key: str) -> TankDetailPage:
        """Navigate to the tank detail page for *tank_key*."""
        self.navigate(f"/standorte/tanks/{tank_key}")
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        return self

    # ── Page info ──────────────────────────────────────────────────────

    def get_page_title(self) -> str:
        """Return the tank name from the page title.

        Waits for the detail page container first to avoid reading
        the list page title during client-side navigation.
        """
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        return self.get_text_stable(
            (By.CSS_SELECTOR, "[data-testid='tank-detail-page'] [data-testid='page-title']")
        )

    # ── Tab navigation ─────────────────────────────────────────────────

    def _tabs(self) -> list[WebElement]:
        """Every tab of this detail page, waiting for the route to render first.

        The tank tests reach this page by clicking a list row and then waiting
        on the URL only, so every reader below used to run while React was still
        committing the destination route. A bare ``find_elements`` answers ``[]``
        there and cannot tell that from "this page has no tabs" — which is how
        ten tank tests reported "found 0 tabs" on run 31113673507 once #835
        removed the implicit wait that had been granting them 3 s.

        Keyed on the tabs themselves rather than only on the page root: the root
        mounts one commit before the `Tabs` do.
        """
        return self.await_presence(self.TABS)

    def get_tab_labels(self) -> list[str]:
        """Return the labels of all visible tabs."""
        return [t.text for t in self._tabs()]

    def click_tab(self, index: int) -> None:
        """Click the tab at *index* (0-based)."""
        tabs = self._tabs()
        if index < len(tabs):
            self.scroll_and_click(tabs[index])
        else:
            raise ValueError(f"Tab index {index} out of range (found {len(tabs)} tabs)")

    def get_active_tab_index(self) -> int:
        """Return the index of the currently selected tab."""
        for i, tab in enumerate(self._tabs()):
            if tab.get_attribute("aria-selected") == "true":
                return i
        return -1

    # ── Details tab (tab=0) ────────────────────────────────────────────

    def get_detail_cards_text(self) -> str:
        """Return combined text of all detail cards.

        Waits for the first card, for the same reason :meth:`_tabs` does: an
        empty read one render too early is indistinguishable from a page that
        renders no cards, and TC-REQ-014-020 asserted on it (``assert ''``).
        """
        cards = self.await_presence(self.DETAIL_TABLES)
        return " ".join(c.text for c in cards)

    def get_alert_count(self) -> int:
        """Return the number of alert banners currently visible.

        No call site in this suite as of #946 wave 5 -- left unanchored
        rather than speculatively converted, since there is no caller whose
        polarity or timing this reader's fix could be verified against.
        """
        return len(self.driver.find_elements(*self.ALERTS))

    def get_alert_messages(self) -> list[str]:
        """Return the text of all visible alert banners.

        No call site in this suite as of #946 wave 5 -- see
        :meth:`get_alert_count`.
        """
        alerts = self.driver.find_elements(*self.ALERTS)
        return [a.text for a in alerts if a.is_displayed()]

    # ── States tab (tab=1) ─────────────────────────────────────────────

    def click_record_state(self) -> None:
        """Click 'Record State' and wait for the dialog to open."""
        btn = self.wait_for_element_clickable(self.RECORD_STATE_BUTTON)
        self.scroll_and_click(btn)
        self.wait_for_element_visible(self.STATE_DIALOG)

    def is_state_dialog_open(self) -> bool:
        """Return True if the TankStateCreateDialog is open.

        Deliberately instantaneous, not anchored: its *presence* call site
        reads it right after ``click_record_state()``, which already runs
        ``wait_for_element_visible(self.STATE_DIALOG)``. For the *dismissal*
        check, use :meth:`wait_for_state_dialog_closed` instead -- see
        :meth:`is_maintenance_dialog_open` for why a raw negated read of a
        MUI Dialog's presence is a guarded-dismissal gap, not a genuine
        "closed" check.
        """
        return len(self.driver.find_elements(*self.STATE_DIALOG)) > 0

    def wait_for_state_dialog_closed(self, timeout: int = DEFAULT_TIMEOUT) -> bool:
        """Wait for the TankStateCreateDialog to actually leave the DOM.

        See :meth:`wait_for_maintenance_dialog_closed` for the exit-transition
        rationale; same shape, different dialog.
        """
        return self.is_absent_within(self.STATE_DIALOG, timeout=timeout)

    def fill_state_ph(self, value: float) -> None:
        el = self.wait_for_element_clickable(self.STATE_FORM_PH)
        el.clear()
        el.send_keys(str(value))

    def fill_state_ec(self, value: float) -> None:
        el = self.wait_for_element_clickable(self.STATE_FORM_EC)
        el.clear()
        el.send_keys(str(value))

    def fill_state_temp(self, value: float) -> None:
        el = self.wait_for_element_clickable(self.STATE_FORM_TEMP)
        el.clear()
        el.send_keys(str(value))

    def fill_state_fill_percent(self, value: float) -> None:
        el = self.wait_for_element_clickable(self.STATE_FORM_FILL_PERCENT)
        el.clear()
        el.send_keys(str(value))

    def fill_state_fill_liters(self, value: float) -> None:
        el = self.wait_for_element_clickable(self.STATE_FORM_FILL_LITERS)
        el.clear()
        el.send_keys(str(value))

    def fill_state_tds(self, value: int) -> None:
        el = self.wait_for_element_clickable(self.STATE_FORM_TDS)
        el.clear()
        el.send_keys(str(value))

    def submit_state_form(self) -> None:
        """Submit the TankState create form."""
        self.wait_and_click(self.STATE_FORM_SUBMIT)

    def cancel_state_form(self) -> None:
        """Cancel the TankState dialog."""
        self.wait_and_click(self.STATE_FORM_CANCEL)

    def wait_for_states_table(self) -> None:
        """Wait for the states table to be back on screen; never raises.

        The same gap :meth:`wait_for_maintenance_table` closes, on the sibling
        tab: ``TankStateCreateDialog``'s ``onCreated`` also calls the parent's
        ``load()`` (``TankDetailPage.tsx``), which re-runs the same
        ``if (loading) return <LoadingSkeleton variant="form" />`` gate that
        unmounts the whole page -- tab strip, table and rows -- for the length
        of the refetch. Neither of the two current call sites reads this right
        after a `load()`-triggering submit today, but the two readers below are
        a public, reusable pair with the maintenance ones, so they get the same
        anchor rather than staying vacuous for whichever call site reaches them
        next.
        """
        self.await_presence(self.STATES_TABLE, IMPLICIT_WAIT_EQUIVALENT)

    def get_states_row_count(self) -> int:
        """Return the number of state rows in the States table."""
        self.wait_for_states_table()
        rows = self.driver.find_elements(*self.STATES_ROWS)
        return len(rows)

    def get_states_row_texts(self) -> list[list[str]]:
        """Return the readable text fragments of every visible state row."""
        self.wait_for_states_table()
        return [
            self.get_row_text_fragments(row) for row in self.driver.find_elements(*self.STATES_ROWS)
        ]

    # ── Maintenance tab (tab=2) ────────────────────────────────────────

    def click_log_maintenance(self) -> None:
        """Click 'Log Maintenance' and wait for the dialog."""
        btn = self.wait_for_element_clickable(self.LOG_MAINTENANCE_BUTTON)
        self.scroll_and_click(btn)
        self.wait_for_element_visible(self.MAINTENANCE_DIALOG)

    def is_maintenance_dialog_open(self) -> bool:
        """Return True if the MaintenanceLogDialog is open.

        Deliberately instantaneous, not anchored: its *presence* call site
        reads it right after ``click_log_maintenance()``, which already runs
        ``wait_for_element_visible(self.MAINTENANCE_DIALOG)``. For the
        *dismissal* check ("the dialog closed"), use
        :meth:`wait_for_maintenance_dialog_closed` instead: MUI's Dialog
        unmounts only after its exit transition finishes, so a raw negated
        read sampled right after clicking Cancel can still see the dialog
        mid-fade-out and report it as open -- a guarded-dismissal gap, not a
        data-fetch one.
        """
        return len(self.driver.find_elements(*self.MAINTENANCE_DIALOG)) > 0

    def wait_for_maintenance_dialog_closed(self, timeout: int = DEFAULT_TIMEOUT) -> bool:
        """Wait for the MaintenanceLogDialog to actually leave the DOM.

        Returns ``False`` (rather than raising) once the budget is spent, so a
        dialog that genuinely never closes still fails the caller's own
        assertion.
        """
        return self.is_absent_within(self.MAINTENANCE_DIALOG, timeout=timeout)

    def select_maintenance_type(self, label_text: str) -> None:
        """Select a maintenance type by its visible label.

        Routed through the shared, verified select helpers -- see
        ``BotanicalFamilyListPage.select_option`` for the rationale.
        """
        self.open_select("maintenance_type")
        self.select_option_by_label(label_text)

    def fill_maintenance_performed_by(self, name: str) -> None:
        el = self.wait_for_element_clickable(self.MAINT_FORM_PERFORMED_BY)
        el.clear()
        el.send_keys(name)

    def fill_maintenance_duration(self, minutes: int) -> None:
        el = self.wait_for_element_clickable(self.MAINT_FORM_DURATION)
        el.clear()
        el.send_keys(str(minutes))

    def fill_maintenance_products(self, products: str) -> None:
        """Fill the products_used field (comma-separated)."""
        el = self.wait_for_element_clickable(self.MAINT_FORM_PRODUCTS)
        el.clear()
        el.send_keys(products)

    def fill_maintenance_notes(self, notes: str) -> None:
        el = self.wait_for_element_clickable(self.MAINT_FORM_NOTES)
        el.clear()
        el.send_keys(notes)

    def submit_maintenance_form(self) -> None:
        """Submit the maintenance log form and wait for the dialog to close.

        The dialog closing is an exact post-condition:
        ``MaintenanceLogDialog.onSubmit`` calls ``onCreated()`` -- which the
        parent implements as ``setMaintenanceDialogOpen(false); load()`` -- only
        after ``await api.logMaintenance(...)`` resolves.

        Checked before adding it, per the lesson of the cultivar submit: this
        helper has **one** caller and it expects success, so the success
        post-condition is a property of every current use. A caller expecting a
        rejected submit must not use it.
        """
        self.wait_and_click(self.MAINT_FORM_SUBMIT)
        self.wait_for_element_hidden(self.MAINTENANCE_DIALOG)

    def cancel_maintenance_form(self) -> None:
        """Cancel the maintenance dialog."""
        self.wait_and_click(self.MAINT_FORM_CANCEL)

    def wait_for_maintenance_table(self) -> None:
        """Wait for the maintenance table to be back on screen; never raises.

        The anchor both readers below need, and the one the weak
        ``wait_for_loading_complete()`` cannot give them. Logging a maintenance
        entry runs the parent's ``load()``, and this page answers
        ``if (loading) return <LoadingSkeleton variant="form" />`` -- so for the
        length of that refetch there is no tab strip, no table and no row at
        all. An absence poll on the skeleton cannot tell "not mounted yet" from
        "already gone", which is why TC-REQ-014-027 read **0** rows where it had
        read 5 a moment earlier, once in six runs.

        Anchored on the *table*, not on rows: a tank with no maintenance history
        renders the table and no rows, and that has to stay readable as 0 rather
        than cost a budget. The two are mutually exclusive here -- skeleton or
        content -- so the table's presence is exactly "the refetch landed".
        """
        self.await_presence(self.MAINTENANCE_TABLE, IMPLICIT_WAIT_EQUIVALENT)

    def get_maintenance_row_count(self) -> int:
        """Return the number of rows in the maintenance history table."""
        self.wait_for_maintenance_table()
        rows = self.driver.find_elements(*self.MAINTENANCE_ROWS)
        return len(rows)

    def get_maintenance_row_texts(self) -> list[list[str]]:
        """Return the readable text fragments of every visible maintenance row."""
        self.wait_for_maintenance_table()
        return [
            self.get_row_text_fragments(row)
            for row in self.driver.find_elements(*self.MAINTENANCE_ROWS)
        ]

    # ── Schedules tab (tab=3) ──────────────────────────────────────────

    def get_schedules_row_count(self) -> int:
        """Return the number of rows in the schedules table.

        No call site in this suite as of #946 wave 5 -- left unanchored
        rather than speculatively converted, since there is no caller whose
        polarity or timing this reader's fix could be verified against.
        """
        rows = self.driver.find_elements(*self.SCHEDULES_ROWS)
        return len(rows)

    def has_schedules_table(self) -> bool:
        """Return True if the Schedules tab rendered a DataTable component.

        Deliberately instantaneous, not anchored: its one call site reads it
        right after ``click_tab(3)``, and ``click_tab`` resolves its tabs
        through :meth:`_tabs`, which itself waits for the route to have
        rendered. Schedules data is fetched together with everything else in
        the same ``load()`` before the page-level loading gate clears
        (``TankDetailPage.tsx``), so a settled tab strip means the schedules
        table has settled too.
        """
        return len(self.driver.find_elements(*self.SCHEDULES_TABLE)) > 0

    # ── Edit tab (tab=5) ───────────────────────────────────────────────

    def get_edit_name_value(self) -> str:
        """Return the current value of the Name field in the edit form."""
        el = self.wait_for_element(self.EDIT_FORM_NAME)
        return el.get_attribute("value") or ""

    def fill_edit_name(self, name: str) -> None:
        """Set the Name field in the edit form."""
        el = self.wait_for_element_clickable(self.EDIT_FORM_NAME)
        el.clear()
        el.send_keys(name)

    def fill_edit_volume(self, volume: float) -> None:
        """Set the volume field in the edit form."""
        el = self.wait_for_element_clickable(self.EDIT_FORM_VOLUME)
        el.clear()
        el.send_keys(str(volume))

    def fill_edit_notes(self, notes: str) -> None:
        el = self.wait_for_element_clickable(self.EDIT_FORM_NOTES)
        el.clear()
        el.send_keys(notes)

    def select_edit_option(self, field_testid: str, value_text: str) -> None:
        """Open an MUI Select in the edit form and pick an option.

        Routed through the shared, verified select helpers -- see
        ``BotanicalFamilyListPage.select_option`` for the rationale.
        """
        self.open_select(field_testid)
        self.select_option_by_label(value_text)

    def toggle_edit_has_lid(self) -> None:
        el = self.wait_for_element_clickable(self.EDIT_FORM_HAS_LID)
        self.scroll_and_click(el)

    def submit_edit_form(self) -> None:
        """Submit the in-page edit form (coordinate-free; see BasePage)."""
        self.wait_and_click_coordinate_free(self.EDIT_FORM_SUBMIT)

    def cancel_edit_form(self) -> None:
        """Cancel the edit form (resets to last saved values)."""
        self.wait_and_click(self.EDIT_FORM_CANCEL)

    # ── Delete ─────────────────────────────────────────────────────────

    def click_delete(self) -> None:
        """Click the Delete button and wait for the ConfirmDialog."""
        btn = self.wait_for_element_clickable(self.DELETE_BUTTON)
        self.scroll_and_click(btn)
        self.wait_for_element_visible(self.CONFIRM_DIALOG)

    def confirm_delete(self) -> None:
        """Confirm deletion in the ConfirmDialog."""
        self.wait_and_click(self.CONFIRM_BUTTON)

    def cancel_delete(self) -> None:
        """Cancel the delete confirmation dialog."""
        self.wait_and_click(self.CONFIRM_CANCEL)

    def is_confirm_dialog_open(self) -> bool:
        """Return True if the delete ConfirmDialog is currently visible.

        Deliberately instantaneous, not anchored: its *presence* call site
        reads it right after ``click_delete()``, which already runs
        ``wait_for_element_visible(self.CONFIRM_DIALOG)``. For the
        *dismissal* check, use :meth:`wait_for_confirm_dialog_closed` instead
        -- see :meth:`is_maintenance_dialog_open` for the exit-transition
        rationale.
        """
        return len(self.driver.find_elements(*self.CONFIRM_DIALOG)) > 0

    def wait_for_confirm_dialog_closed(self, timeout: int = DEFAULT_TIMEOUT) -> bool:
        """Wait for the delete ConfirmDialog to actually leave the DOM."""
        return self.is_absent_within(self.CONFIRM_DIALOG, timeout=timeout)

    # ── Error display ──────────────────────────────────────────────────

    def is_error_displayed(self) -> bool:
        """Return True if an error display component is visible.

        Deliberately instantaneous, not anchored: its one call site
        (``test_nonexistent_tank_key_shows_error``) reads it right after
        ``wait_for_any_present((ERROR_DISPLAY, PAGE), ...)`` -- the readiness
        this method reports has already been bought by the caller.
        """
        elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='error-display']")
        return len(elements) > 0 and elements[0].is_displayed()

    def is_page_present(self) -> bool:
        """Return True if the tank detail page container rendered.

        See :meth:`is_error_displayed` -- same call site, same anchor.
        """
        return len(self.driver.find_elements(*self.PAGE)) > 0

    # ── Validation errors ──────────────────────────────────────────────

    def get_validation_error(self, field_name: str) -> str:
        """Return the validation error text for a form field.

        No call site in this suite as of #946 wave 5 -- left unanchored
        rather than speculatively converted, since there is no caller whose
        polarity or timing this reader's fix could be verified against.
        """
        locator = (
            By.CSS_SELECTOR,
            f"[data-testid='form-field-{field_name}'] .MuiFormHelperText-root.Mui-error",
        )
        elements = self.driver.find_elements(*locator)
        return elements[0].text if elements else ""

    def has_validation_error(self, field_name: str) -> bool:
        """See :meth:`get_validation_error`: no call site in this suite as of #946 wave 5."""
        return bool(self.get_validation_error(field_name))
