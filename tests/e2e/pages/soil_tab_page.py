"""Page objects for the soil tab of the bed view (REQ-053 WP 8.7 / 8.8 / 8.14, ``/standorte/locations/:key#soil``).

Two objects, one per surface the wave 8 part A tests drive:

* :class:`SoilTab` - the tab itself: the switch "Fruchtfolge für dieses Beet" (``RotationSwitch``), the soil
  analyses section with its "Kalkbedarf" line (``SoilAnalysisSection``) and the pH/EC/humus history with its table
  (``SoilAnalysisChart``);
* :class:`SoilAnalysisDialog` - "Bodenanalyse erfassen" (``SoilAnalysisDialog``): date, source, depth and one
  fieldset per measured value.

Every hook is a ``data-testid`` that exists in ``src/frontend/src/features/gardenPlanner/bed/`` - none is guessed;
the one exception is the dialog's "Abbrechen" button, which has no test id and is addressed by its role and its
label inside the dialog's action bar (locator hierarchy: test hook first, role/semantic next).
State-changing helpers read their effect back and fail loudly when it never arrives (`e2e-test-stability` §D);
there is no retry loop and no sleep.
"""

from __future__ import annotations

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

from .base_page import BasePage
from .bed_care_page import choose_from_native_select, field_helper_text, wait_for_field_error


def _tid(testid: str) -> tuple[str, str]:
    return (By.CSS_SELECTOR, f"[data-testid='{testid}']")


def _text(element: WebElement) -> str:
    return " ".join((element.get_attribute("textContent") or "").split())


#: Writes a ``datetime-local`` value *days* days from the browser's now (its own local time, minute precision)
#: through the native value setter and an ``input`` event - the event React's ``onChange`` listens to - and returns
#: the value written. Typing into a ``datetime-local`` field is locale-dependent in Chrome (the segment order follows
#: the browser locale), so the value is set the way the field itself would set it; the caller reads it back.
_SET_DATETIME_LOCAL = """
var el = arguments[0], days = arguments[1];
var d = new Date(Date.now() + days * 86400000);
function p(n) { return String(n).padStart(2, '0'); }
var value = d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) + 'T' + p(d.getHours()) + ':'
  + p(d.getMinutes());
var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
setter.call(el, value);
el.dispatchEvent(new Event('input', {bubbles: true}));
return value;
"""


class SoilTab(BasePage):
    """The soil tab of one bed: rotation switch, soil analyses, liming line, history chart/table."""

    TAB = _tid("bed-soil-analyses")
    RECORD = _tid("soil-analysis-record")
    EMPTY_ACTION = _tid("empty-state-action")
    LIMING = _tid("soil-liming-hint")
    CHART = _tid("soil-history-chart")
    AS_TABLE_INPUT = (
        By.CSS_SELECTOR,
        "[data-testid='soil-history-as-table'] input[type='checkbox']",
    )

    ROTATION = _tid("rotation-switch")
    ROTATION_SAVED = _tid("rotation-switch-saved")
    ROTATION_REFUSAL = _tid("rotation-switch-refusal")
    EXEMPT_INPUT = _tid("rotation-exempt-switch")

    # ── Soil analyses ──────────────────────────────────────────────────

    def open_record_dialog(self) -> SoilAnalysisDialog:
        """ "Bodenanalyse erfassen": the head button once the bed has an analysis, the empty state's action before."""
        if self.driver.find_elements(*self.RECORD):
            self.wait_and_click(self.RECORD)
        else:
            self.wait_and_click(
                (
                    By.CSS_SELECTOR,
                    "[data-testid='bed-soil-analyses'] [data-testid='empty-state-action']",
                )
            )
        dialog = SoilAnalysisDialog(self.driver, self.base_url)
        try:
            dialog.wait_for_element_visible(dialog.DIALOG)
        except TimeoutException as exc:
            raise AssertionError("'Bodenanalyse erfassen' opened no dialog") from exc
        return dialog

    def liming_hint(self) -> tuple[str, str]:
        """``(data-status, text)`` of the "Kalkbedarf" line; loud when the section shows none."""
        try:
            line = self.wait_for_element(self.LIMING)
        except TimeoutException as exc:
            raise AssertionError("the soil analyses section shows no liming line") from exc
        return line.get_attribute("data-status") or "", _text(line)

    def show_as_table(self) -> None:
        """Switch "Als Tabelle anzeigen" on (keyboard: Space on the focused switch); verify it is on."""
        switch = self.wait_for_element(self.AS_TABLE_INPUT)
        if switch.is_selected():
            raise AssertionError("'Als Tabelle anzeigen' is already on")
        self.driver.execute_script("arguments[0].focus();", switch)
        switch.send_keys(Keys.SPACE)
        try:
            self.poll().until(lambda _d: switch.is_selected())
        except TimeoutException as exc:
            raise AssertionError("'Als Tabelle anzeigen' did not switch on") from exc

    def chart_drawn(self, parameter: str) -> bool:
        """Whether the panel of *parameter* draws its chart (recharts' wrapper) rather than only the table."""
        return bool(
            self.driver.find_elements(
                By.CSS_SELECTOR, f"[data-testid='soil-history-{parameter}'] .recharts-wrapper"
            )
        )

    def history_rows(self, parameter: str) -> list[list[str]]:
        """The rows of the history table of *parameter* (date, method, value, source, depth), oldest first.

        The table is always in the DOM (visually hidden under the chart, for screen readers), so this reads the same
        rows in both views. Loud when the parameter has no panel: "no table" is not "no rows".
        """
        try:
            table = self.wait_for_element(_tid(f"soil-history-table-{parameter}"))
        except TimeoutException as exc:
            raise AssertionError(f"the soil history has no table for {parameter!r}") from exc
        return [
            [_text(cell) for cell in row.find_elements(By.CSS_SELECTOR, "td")]
            for row in table.find_elements(By.CSS_SELECTOR, "tbody tr")
        ]

    def wait_for_history_rows(self, parameter: str, count: int, what: str) -> list[list[str]]:
        try:
            self.poll().until(lambda _d: len(self._rows_or_empty(parameter)) == count)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the {parameter} history should list {count} rows; it lists "
                f"{self._rows_or_empty(parameter)}"
            ) from exc
        return self.history_rows(parameter)

    def _rows_or_empty(self, parameter: str) -> list[list[str]]:
        tables = self.driver.find_elements(*_tid(f"soil-history-table-{parameter}"))
        if not tables:
            return []
        return [
            [_text(cell) for cell in row.find_elements(By.CSS_SELECTOR, "td")]
            for row in tables[0].find_elements(By.CSS_SELECTOR, "tbody tr")
        ]

    # ── Rotation switch (GP-FR-137) ────────────────────────────────────

    def _radio(self, value: str) -> WebElement:
        return self.wait_for_element(
            (By.CSS_SELECTOR, f"[data-testid='rotation-enabled-{value}'] input[type='radio']")
        )

    def rotation_check(self) -> str:
        """The checked value of "Fruchtfolge-Prüfung": ``default``, ``on`` or ``off``; loud when none is checked."""
        self.wait_for_element(self.ROTATION)
        checked = [value for value in ("default", "on", "off") if self._radio(value).is_selected()]
        if len(checked) != 1:
            raise AssertionError(
                f"the rotation check should have exactly one checked value: {checked}"
            )
        return checked[0]

    def exempt_on(self) -> bool:
        return self.wait_for_element(self.EXEMPT_INPUT).is_selected()

    def _wait_saved(self, what: str) -> None:
        """The switch section is ``aria-busy`` while it writes; "Gespeichert." appears only after the server answered."""
        section = self.wait_for_element(self.ROTATION)
        try:
            self.poll().until(
                lambda d: (
                    section.get_attribute("aria-busy") == "false"
                    and d.find_elements(*self.ROTATION_SAVED)
                )
            )
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the rotation switch never reported 'Gespeichert.'"
            ) from exc

    def set_rotation_check(self, value: str, what: str) -> None:
        """Choose *value* in "Fruchtfolge-Prüfung" by keyboard (Space on the focused radio) and wait for the save."""
        radio = self._radio(value)
        self.driver.execute_script("arguments[0].focus();", radio)
        radio.send_keys(Keys.SPACE)
        self._wait_saved(what)
        if self.rotation_check() != value:
            raise AssertionError(
                f"{what}: 'Fruchtfolge-Prüfung' should read {value!r}, it reads {self.rotation_check()!r}"
            )

    def toggle_exempt_expecting_refusal(self, what: str) -> str:
        """Switch "Dauerkultur" with Space; the server refuses it - wait for the refusal alert and return its text."""
        switch = self.wait_for_element(self.EXEMPT_INPUT)
        self.driver.execute_script("arguments[0].focus();", switch)
        switch.send_keys(Keys.SPACE)
        try:
            alert = self.wait_for_element_visible(self.ROTATION_REFUSAL)
        except TimeoutException as exc:
            raise AssertionError(f"{what}: switching 'Dauerkultur' on showed no refusal") from exc
        section = self.wait_for_element(self.ROTATION)
        self.poll().until(lambda _d: section.get_attribute("aria-busy") == "false")
        return _text(alert)


class SoilAnalysisDialog(BasePage):
    """ "Bodenanalyse für <Beet> erfassen": the ``soil-analysis-*`` fields; row *n* is 1-based."""

    DIALOG = _tid("soil-analysis-dialog")
    SUBMIT = _tid("soil-analysis-submit")
    ADD_ROW = _tid("soil-analysis-add-row")
    PERFORMED_AT = "soil-analysis-performed-at"
    #: The dialog's own "Abbrechen" (``common.cancel``); it carries no test id.
    CANCEL = (
        By.XPATH,
        "//*[@data-testid='soil-analysis-dialog']//div[contains(@class, 'MuiDialogActions-root')]"
        "//button[normalize-space()='Abbrechen']",
    )

    #: Every form field's label: MUI's ``InputLabel`` carries ``MuiInputLabel-root`` whatever element it renders as.
    #: A select ``TextField`` has no labelable ``<input>``, so its label is not a ``<label>`` bound to one - reading
    #: only ``label`` elements missed "Herkunft", "Messgröße", "Einheit" and "Methode". The outlined border's
    #: ``<legend>`` repeats the label text and is deliberately not matched.
    FIELD_LABELS = (By.CSS_SELECTOR, ".MuiInputLabel-root")

    def labels(self) -> list[str]:
        """The labels of every form field in the dialog (text fields and selects), in document order."""
        dialog = self.wait_for_element(self.DIALOG)
        return [_text(label) for label in dialog.find_elements(*self.FIELD_LABELS) if _text(label)]

    def set_performed_days_from_now(self, days: float) -> str:
        """Set "Probe genommen am" to now + *days* (negative = back) in the browser's local time; read it back."""
        field = self.wait_for_element(_tid(self.PERFORMED_AT))
        self.require_interactable(field, "soil analysis date")
        value = self.driver.execute_script(_SET_DATETIME_LOCAL, field, days)
        try:
            self.poll().until(lambda _d: field.get_attribute("value") == value)
        except TimeoutException as exc:
            raise AssertionError(
                f"the analysis date should read {value!r}; it reads {field.get_attribute('value')!r}"
            ) from exc
        return value

    def set_source(self, source: str) -> None:
        choose_from_native_select(self, "soil-analysis-source", source)

    def set_parameter(self, row: int, parameter: str) -> None:
        choose_from_native_select(self, f"soil-analysis-parameter-{row}", parameter)

    def set_method(self, row: int, method: str) -> None:
        choose_from_native_select(self, f"soil-analysis-method-{row}", method)

    def set_value(self, row: int, value: str) -> None:
        field = self.wait_for_element_clickable(_tid(f"soil-analysis-value-{row}"))
        self.clear_and_fill(field, value)
        try:
            self.poll().until(lambda _d: (field.get_attribute("value") or "") == value)
        except TimeoutException as exc:
            raise AssertionError(
                f"value {row} should read {value!r}; it reads {field.get_attribute('value')!r}"
            ) from exc

    def add_row(self, expected_rows: int) -> None:
        """ "Weiteren Wert hinzufügen"; wait until the dialog holds *expected_rows* fieldsets."""
        self.wait_and_click(self.ADD_ROW)
        try:
            self.wait_for_element(_tid(f"soil-analysis-row-{expected_rows}"))
        except TimeoutException as exc:
            raise AssertionError(
                f"'Weiteren Wert hinzufügen' added no row {expected_rows}"
            ) from exc

    def has_content_class(self, row: int) -> bool:
        """Whether row *row* offers "Gehaltsklasse" now (call after the choice that decides it was read back)."""
        return bool(self.driver.find_elements(*_tid(f"soil-analysis-class-{row}")))

    def wait_for_content_class(self, row: int, shown: bool, what: str) -> None:
        try:
            self.poll().until(lambda _d: self.has_content_class(row) == shown)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: 'Gehaltsklasse' of row {row} should be {'shown' if shown else 'absent'}"
            ) from exc

    def submit_and_wait_closed(self, what: str) -> None:
        """ "Analyse speichern"; the dialog closes only after the server stored the analysis."""
        self.wait_and_click(self.SUBMIT)
        try:
            self.wait_for_element_hidden(self.DIALOG)
        except TimeoutException as exc:
            errors = [
                text
                for text in (
                    field_helper_text(self, tid)
                    for tid in (
                        self.PERFORMED_AT,
                        "soil-analysis-value-1",
                        "soil-analysis-method-1",
                    )
                )
                if text
            ]
            raise AssertionError(
                f"{what}: the soil analysis dialog did not close; field lines: {errors}"
            ) from exc

    def submit_expecting_field_error(self, testid: str, message: str, what: str) -> None:
        """ "Analyse speichern" with a refused field: wait for *message* on *testid*; the dialog stays open."""
        self.wait_and_click(self.SUBMIT)
        wait_for_field_error(self, testid, message, what)
        if not self.driver.find_elements(*self.DIALOG):
            raise AssertionError(f"{what}: the dialog closed although the analysis was refused")

    def cancel(self) -> None:
        self.wait_and_click(self.CANCEL)
        try:
            self.wait_for_element_hidden(self.DIALOG)
        except TimeoutException as exc:
            raise AssertionError("'Abbrechen' did not close the soil analysis dialog") from exc


__all__ = ["SoilAnalysisDialog", "SoilTab"]
