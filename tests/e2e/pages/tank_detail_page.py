"""Page object for the Tank detail page (REQ-014)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


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
    STATE_DIALOG = (By.CSS_SELECTOR, "div[role='dialog']")
    STATE_FORM_PH = (By.CSS_SELECTOR, "[data-testid='form-field-ph'] input")
    STATE_FORM_EC = (By.CSS_SELECTOR, "[data-testid='form-field-ec_ms'] input")
    STATE_FORM_TEMP = (By.CSS_SELECTOR, "[data-testid='form-field-water_temp_celsius'] input")
    STATE_FORM_FILL_PERCENT = (By.CSS_SELECTOR, "[data-testid='form-field-fill_level_percent'] input")
    STATE_FORM_FILL_LITERS = (By.CSS_SELECTOR, "[data-testid='form-field-fill_level_liters'] input")
    STATE_FORM_TDS = (By.CSS_SELECTOR, "[data-testid='form-field-tds_ppm'] input")
    STATE_FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    STATE_FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    # ── Tab 2 – Maintenance ────────────────────────────────────────────
    LOG_MAINTENANCE_BUTTON = (By.CSS_SELECTOR, "[data-testid='tank-log-maintenance-button']")
    MAINTENANCE_TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    MAINTENANCE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")

    # ── MaintenanceLogDialog ───────────────────────────────────────────
    MAINTENANCE_DIALOG = (By.CSS_SELECTOR, "div[role='dialog']")
    MAINT_FORM_TYPE = (By.CSS_SELECTOR, "[data-testid='form-field-maintenance_type'] .MuiSelect-select")
    MAINT_FORM_PERFORMED_BY = (By.CSS_SELECTOR, "[data-testid='form-field-performed_by'] input")
    MAINT_FORM_DURATION = (By.CSS_SELECTOR, "[data-testid='form-field-duration_minutes'] input")
    MAINT_FORM_PRODUCTS = (By.CSS_SELECTOR, "[data-testid='form-field-products_used'] input")
    MAINT_FORM_NOTES = (By.CSS_SELECTOR, "[data-testid='form-field-notes'] textarea")
    MAINT_FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    MAINT_FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    # ── Tab 3 – Schedules ─────────────────────────────────────────────
    SCHEDULES_TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    SCHEDULES_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")

    # ── Tab 4 – Fills ────────────────────────────────────────────────────
    # (Tab for tank fill events – no specific locators needed beyond data-table)

    # ── Tab 5 – Edit form ──────────────────────────────────────────────
    EDIT_FORM_NAME = (By.CSS_SELECTOR, "[data-testid='form-field-name'] input")
    EDIT_FORM_TANK_TYPE = (By.CSS_SELECTOR, "[data-testid='form-field-tank_type'] .MuiSelect-select")
    EDIT_FORM_VOLUME = (By.CSS_SELECTOR, "[data-testid='form-field-volume_liters'] input")
    EDIT_FORM_MATERIAL = (By.CSS_SELECTOR, "[data-testid='form-field-material'] .MuiSelect-select")
    EDIT_FORM_HAS_LID = (By.CSS_SELECTOR, "[data-testid='form-field-has_lid'] .MuiSwitch-root")
    EDIT_FORM_NOTES = (By.CSS_SELECTOR, "[data-testid='form-field-notes'] textarea")
    EDIT_FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    EDIT_FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    # Alert banner rendered with MUI Alert
    ALERTS = (By.CSS_SELECTOR, ".MuiAlert-root")

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
        """Return the tank name from the page title."""
        el = self.wait_for_element((By.CSS_SELECTOR, "[data-testid='page-title']"))
        return el.text

    # ── Tab navigation ─────────────────────────────────────────────────

    def get_tab_labels(self) -> list[str]:
        """Return the labels of all visible tabs."""
        tabs = self.driver.find_elements(*self.TABS)
        return [t.text for t in tabs]

    def click_tab(self, index: int) -> None:
        """Click the tab at *index* (0-based)."""
        tabs = self.driver.find_elements(*self.TABS)
        if index < len(tabs):
            self.scroll_and_click(tabs[index])
        else:
            raise ValueError(f"Tab index {index} out of range (found {len(tabs)} tabs)")

    def get_active_tab_index(self) -> int:
        """Return the index of the currently selected tab."""
        tabs = self.driver.find_elements(*self.TABS)
        for i, tab in enumerate(tabs):
            if tab.get_attribute("aria-selected") == "true":
                return i
        return -1

    # ── Details tab (tab=0) ────────────────────────────────────────────

    def get_detail_cards_text(self) -> str:
        """Return combined text of all detail cards."""
        cards = self.driver.find_elements(*self.DETAIL_TABLES)
        return " ".join(c.text for c in cards)

    def get_alert_count(self) -> int:
        """Return the number of alert banners currently visible."""
        return len(self.driver.find_elements(*self.ALERTS))

    def get_alert_messages(self) -> list[str]:
        """Return the text of all visible alert banners."""
        alerts = self.driver.find_elements(*self.ALERTS)
        return [a.text for a in alerts if a.is_displayed()]

    # ── States tab (tab=1) ─────────────────────────────────────────────

    def click_record_state(self) -> None:
        """Click 'Record State' and wait for the dialog to open."""
        btn = self.wait_for_element_clickable(self.RECORD_STATE_BUTTON)
        self.scroll_and_click(btn)
        self.wait_for_element_visible(self.STATE_DIALOG)

    def is_state_dialog_open(self) -> bool:
        """Return True if the TankStateCreateDialog is open."""
        return len(self.driver.find_elements(*self.STATE_DIALOG)) > 0

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
        self.wait_for_element_clickable(self.STATE_FORM_SUBMIT).click()

    def cancel_state_form(self) -> None:
        """Cancel the TankState dialog."""
        self.wait_for_element_clickable(self.STATE_FORM_CANCEL).click()

    def get_states_row_count(self) -> int:
        """Return the number of state rows in the States table."""
        rows = self.driver.find_elements(*self.STATES_ROWS)
        return len(rows)

    def get_states_row_texts(self) -> list[list[str]]:
        """Return all cell texts for every visible state row."""
        rows = self.driver.find_elements(*self.STATES_ROWS)
        result = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            result.append([c.text for c in cells])
        return result

    # ── Maintenance tab (tab=2) ────────────────────────────────────────

    def click_log_maintenance(self) -> None:
        """Click 'Log Maintenance' and wait for the dialog."""
        btn = self.wait_for_element_clickable(self.LOG_MAINTENANCE_BUTTON)
        self.scroll_and_click(btn)
        self.wait_for_element_visible(self.MAINTENANCE_DIALOG)

    def is_maintenance_dialog_open(self) -> bool:
        """Return True if the MaintenanceLogDialog is open."""
        return len(self.driver.find_elements(*self.MAINTENANCE_DIALOG)) > 0

    def select_maintenance_type(self, label_text: str) -> None:
        """Select a maintenance type by its visible label."""
        import time
        from selenium.webdriver.common.keys import Keys

        field = self.wait_for_element_clickable(self.MAINT_FORM_TYPE)
        self.scroll_and_click(field)
        option = self.wait_for_element_clickable(
            (By.XPATH, f"//li[@role='option' and contains(text(), '{label_text}')]")
        )
        option.click()
        # Dismiss MUI Select backdrop/popover
        time.sleep(0.3)
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            pass
        time.sleep(0.3)

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
        """Submit the maintenance log form."""
        self.wait_for_element_clickable(self.MAINT_FORM_SUBMIT).click()

    def cancel_maintenance_form(self) -> None:
        """Cancel the maintenance dialog."""
        self.wait_for_element_clickable(self.MAINT_FORM_CANCEL).click()

    def get_maintenance_row_count(self) -> int:
        """Return the number of rows in the maintenance history table."""
        rows = self.driver.find_elements(*self.MAINTENANCE_ROWS)
        return len(rows)

    def get_maintenance_row_texts(self) -> list[list[str]]:
        """Return all cell texts for every visible maintenance row."""
        rows = self.driver.find_elements(*self.MAINTENANCE_ROWS)
        result = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            result.append([c.text for c in cells])
        return result

    # ── Schedules tab (tab=3) ──────────────────────────────────────────

    def get_schedules_row_count(self) -> int:
        """Return the number of rows in the schedules table."""
        rows = self.driver.find_elements(*self.SCHEDULES_ROWS)
        return len(rows)

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
        """Open an MUI Select in the edit form and pick an option."""
        import time
        from selenium.webdriver.common.keys import Keys

        field = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='form-field-{field_testid}'] .MuiSelect-select")
        )
        self.scroll_and_click(field)
        option = self.wait_for_element_clickable(
            (By.XPATH, f"//li[@role='option' and contains(text(), '{value_text}')]")
        )
        option.click()
        # Dismiss MUI Select backdrop/popover
        time.sleep(0.3)
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            pass
        time.sleep(0.3)

    def toggle_edit_has_lid(self) -> None:
        el = self.wait_for_element_clickable(self.EDIT_FORM_HAS_LID)
        self.scroll_and_click(el)

    def submit_edit_form(self) -> None:
        """Submit the edit form."""
        self.wait_for_element_clickable(self.EDIT_FORM_SUBMIT).click()

    def cancel_edit_form(self) -> None:
        """Cancel the edit form (resets to last saved values)."""
        self.wait_for_element_clickable(self.EDIT_FORM_CANCEL).click()

    # ── Delete ─────────────────────────────────────────────────────────

    def click_delete(self) -> None:
        """Click the Delete button and wait for the ConfirmDialog."""
        btn = self.wait_for_element_clickable(self.DELETE_BUTTON)
        self.scroll_and_click(btn)
        self.wait_for_element_visible(self.CONFIRM_DIALOG)

    def confirm_delete(self) -> None:
        """Confirm deletion in the ConfirmDialog."""
        self.wait_for_element_clickable(self.CONFIRM_BUTTON).click()

    def cancel_delete(self) -> None:
        """Cancel the delete confirmation dialog."""
        self.wait_for_element_clickable(self.CONFIRM_CANCEL).click()

    def is_confirm_dialog_open(self) -> bool:
        return len(self.driver.find_elements(*self.CONFIRM_DIALOG)) > 0

    # ── Error display ──────────────────────────────────────────────────

    def is_error_displayed(self) -> bool:
        """Return True if an error display component is visible."""
        elements = self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='error-display']"
        )
        return len(elements) > 0 and elements[0].is_displayed()

    # ── Validation errors ──────────────────────────────────────────────

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
