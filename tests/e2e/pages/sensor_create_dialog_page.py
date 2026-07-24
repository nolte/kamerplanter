"""Page object for the SensorCreateDialog (REQ-005 Hybrid-Sensorik).

The SensorCreateDialog is opened from a parent page (Site detail, Location detail
or Tank detail) via its ``[data-testid='add-sensor-button']``.  It allows
operators to register a new sensor that the hybrid sensor pipeline (REQ-005
4-source fallback chain: automatic IoT/MQTT -> semi-automatic Home Assistant
-> weather API -> manual) will subsequently feed.

This page object only encapsulates dialog-level interactions.  Navigation to
the parent page itself is the test's responsibility (reuse ``SiteListPage`` or
``SiteDetailPage`` for that).
"""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class SensorCreateDialogPage(BasePage):
    """Interact with the SensorCreateDialog opened from a Site/Location/Tank detail."""

    # ── Trigger button (lives on the parent page) ─────────────────────────
    ADD_SENSOR_BUTTON = (By.CSS_SELECTOR, "[data-testid='add-sensor-button']")

    # ── Dialog itself ──────────────────────────────────────────────────────
    DIALOG = (By.CSS_SELECTOR, "[data-testid='sensor-create-dialog']")
    DIALOG_TITLE = (By.CSS_SELECTOR, "#sensor-create-dialog-title")

    # ── Form fields ───────────────────────────────────────────────────────
    NAME_INPUT = (By.CSS_SELECTOR, "[data-testid='form-field-name'] input")
    METRIC_TYPE_SELECT = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-metric_type'] .MuiSelect-select",
    )
    HA_ENTITY_INPUT = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-ha_entity_id'] input",
    )
    MQTT_TOPIC_INPUT = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-mqtt_topic'] input",
    )

    # ── Action buttons ────────────────────────────────────────────────────
    SUBMIT_BUTTON = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    CANCEL_BUTTON = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    # ── Open / close ───────────────────────────────────────────────────────

    def click_add_sensor(self) -> None:
        """Click the ``Sensor hinzufügen`` button on the parent page."""
        btn = self.wait_for_element_clickable(self.ADD_SENSOR_BUTTON)
        self.scroll_and_click(btn)
        self.wait_for_element_visible(self.DIALOG)

    def is_open(self) -> bool:
        """Return True iff the SensorCreateDialog is visible."""
        elements = self.driver.find_elements(*self.DIALOG)
        return bool(elements) and elements[0].is_displayed()

    def close_via_cancel(self) -> None:
        self.wait_for_element_clickable(self.CANCEL_BUTTON).click()
        self.wait_for_element_hidden(self.DIALOG)

    # ── Form interactions ─────────────────────────────────────────────────

    def get_dialog_title(self) -> str:
        return self.wait_for_element_visible(self.DIALOG_TITLE).text

    def set_name(self, value: str) -> None:
        el = self.wait_for_element_clickable(self.NAME_INPUT)
        self.clear_and_fill(el, value)

    def select_metric_type(self, value_text: str) -> None:
        """Open the metric_type MUI Select and pick an option by visible text.

        Uses partial text match so callers can pass either the enum key
        (``ph``) or the localised label fragment (``pH``, ``Temperatur``).
        """
        select_el = self.wait_for_element_clickable(self.METRIC_TYPE_SELECT)
        self.scroll_and_click(select_el)
        option = self.wait_for_element_clickable(
            (By.XPATH, f"//li[@role='option' and contains(text(), '{value_text}')]")
        )
        option.click()
        # MUI auto-closes on option click; ensure the popover is fully gone
        self.close_mui_dropdown()

    def has_field(self, locator: tuple[str, str]) -> bool:
        """Return True iff a form field exists in the DOM (visibility ignored)."""
        return bool(self.driver.find_elements(*locator))

    def submit(self) -> None:
        self.wait_for_element_clickable(self.SUBMIT_BUTTON).click()

    # ── Trigger button state (on the parent page) ──────────────────────────

    def is_add_sensor_button_present(self) -> bool:
        """Return True iff the add-sensor-button exists in the DOM (visibility ignored)."""
        return bool(self.driver.find_elements(*self.ADD_SENSOR_BUTTON))

    def scroll_add_sensor_button_into_view(self) -> None:
        """Scroll the add-sensor-button into the viewport without clicking it."""
        button = self.driver.find_element(*self.ADD_SENSOR_BUTTON)
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", button
        )

    def is_add_sensor_button_visible(self) -> bool:
        """Return True iff the add-sensor-button is present and displayed."""
        elements = self.driver.find_elements(*self.ADD_SENSOR_BUTTON)
        return bool(elements) and elements[0].is_displayed()

    # ── Post-save verification ────────────────────────────────────────────

    def wait_until_closed(self, timeout: int = 15) -> None:
        """Wait until the dialog closes (signals successful save / cancel)."""
        self.wait_for_element_hidden(self.DIALOG, timeout=timeout)

    def find_row_by_name(self, sensor_name: str):
        """Return the data-table row element whose first cell text equals *sensor_name*.

        Returns None when no row matches.  Used to verify the new sensor
        appears in the parent page's sensor table after save.
        """
        rows = self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='data-table-row']"
        )
        for row in rows:
            if sensor_name in row.text:
                return row
        return None

    def wait_for_row_containing(self, text: str, timeout: int = 15) -> bool:
        """Wait until any ``data-table-row`` on the page contains *text*.

        Returns True once found; raises TimeoutException if *timeout* elapses.
        Used to verify a newly created sensor appears in the parent page's
        table after a save + refresh, without a raw lookup in the test body.
        """
        from selenium.webdriver.support.ui import WebDriverWait

        def _row_present(driver: WebDriver) -> bool:
            return self.find_row_by_name(text) is not None

        return WebDriverWait(self.driver, timeout).until(_row_present)
