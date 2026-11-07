"""Page objects for the care and history surfaces of the bed view (REQ-053 WP 4.4 / 4.5).

Three objects, one per surface the wave 4 tests drive:

* :class:`BedCareTab` - the "Pflege" tab of ``/standorte/locations/:key#care``: create a task on the bed, find
  its row, open its completion dialog;
* :class:`CompletionDialog` - the short, category-specific completion form (``CareCompletionDialog``);
* :class:`HistoryTab` - the "Historie" tab: category filter, "Mehr laden", the corrections switch, the list rows
  and the planting timeline (``BedHistoryTab`` / ``HistoryList`` / ``PlantingTimeline``).

Wave 8 (WP 8.30) adds the area dose and the material lists of the completion form (``CareFormFields``), the care log
dialog (``CareLogDialog``), the suggestions section (``SuggestionList``), the follow-up crop recommendation under the
timeline (``SuccessionRecommendationPanel``), the CSV download of the history (``HistoryExportButton``, read through
:class:`DownloadCapture`) and the tenant-wide history page (:class:`CareHistoryPage`).

Every hook is a ``data-testid`` that exists in ``src/frontend/src/features/gardenPlanner/`` - none is guessed.
State-changing helpers read their effect back and fail loudly when it never arrives (`e2e-test-stability` §D);
there is no retry loop and no sleep: a wait is a condition on the page (a row, a closed dialog, a list count, the
live-region text).
"""

from __future__ import annotations

import re

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

from .base_page import BasePage


def _tid(testid: str) -> tuple[str, str]:
    return (By.CSS_SELECTOR, f"[data-testid='{testid}']")


def _text(element: WebElement) -> str:
    return " ".join((element.get_attribute("textContent") or "").split())


#: The options of an open MUI listbox (Select menu or Autocomplete popup).
OPTIONS = (By.CSS_SELECTOR, "li[role='option']")


def option_texts(page: BasePage) -> list[str]:
    """The visible labels of the open listbox's options, in the order shown."""
    return [_text(option) for option in page.driver.find_elements(*OPTIONS)]


_HELPER_LINE = (
    "var root = arguments[0].closest('.MuiFormControl-root');"
    "var line = root && root.querySelector('.MuiFormHelperText-root');"
    "return line ? {text: line.textContent, error: line.classList.contains('Mui-error')} : {text: '', error: false};"
)


def _helper_line(page: BasePage, testid: str) -> tuple[str, bool]:
    field = page.wait_for_element(_tid(testid))
    line = page.driver.execute_script(_HELPER_LINE, field) or {}
    return " ".join((line.get("text") or "").split()), bool(line.get("error"))


def field_helper_text(page: BasePage, testid: str) -> str:
    """The helper/error line under the text field whose input carries *testid* (``''`` when it has none)."""
    return _helper_line(page, testid)[0]


def wait_for_field_error(page: BasePage, testid: str, message: str, what: str) -> None:
    """Wait until the helper line of the field *testid* is in its error state and reads exactly *message*.

    The error state is read from the helper line (``Mui-error``), which MUI sets for a text field and a select
    alike - a select's hidden native input carries no ``aria-invalid``.
    """
    try:
        page.poll().until(lambda _d: _helper_line(page, testid) == (message, True))
    except TimeoutException as exc:
        raise AssertionError(
            f"{what}: the field {testid!r} should show the error {message!r}; its helper line reads "
            f"{_helper_line(page, testid)!r} (text, error state)"
        ) from exc


def choose_autocomplete_option(page: BasePage, testid: str, typed: str, label: str) -> None:
    """Type *typed* into the Autocomplete input *testid* and pick the option labelled exactly *label*.

    The option is clicked coordinate-free (an option activates from its ``onClick``); the committed input value is
    read back, so a pick the component did not take fails here.
    """
    field = page.wait_for_element_clickable(_tid(testid))
    page.clear_and_fill(field, typed)

    def _option():
        for option in page.driver.find_elements(*OPTIONS):
            if _text(option) == label:
                return option
        return False

    try:
        option = page.poll().until(lambda _d: _option())
    except TimeoutException as exc:
        raise AssertionError(
            f"the field {testid!r} offers no option {label!r} for {typed!r}; options: {option_texts(page)}"
        ) from exc
    page.click_menu_option(option)
    try:
        page.poll().until(lambda _d: (field.get_attribute("value") or "") == label)
    except TimeoutException as exc:
        raise AssertionError(
            f"picking {label!r} in {testid!r} did not commit; the field reads {field.get_attribute('value')!r}"
        ) from exc


def open_autocomplete_options(page: BasePage, testid: str) -> list[str]:
    """Open the Autocomplete *testid* with the keyboard (ArrowDown) and return the labels it offers.

    Loud when the popup never shows an option: "the list is empty" and "the list never opened" are different
    findings and neither may read as an empty list.
    """
    field = page.wait_for_element_clickable(_tid(testid))
    page.driver.execute_script("arguments[0].focus();", field)
    field.send_keys(Keys.ARROW_DOWN)
    try:
        page.poll().until(lambda d: d.find_elements(*OPTIONS))
    except TimeoutException as exc:
        raise AssertionError(f"the Autocomplete {testid!r} opened no option list") from exc
    return option_texts(page)


def close_autocomplete(page: BasePage, testid: str) -> None:
    """Close the open popup of the Autocomplete *testid* with Escape on its own input (never a body-level ESC).

    Only while the popup is open: MUI's Autocomplete stops an Escape that closes its popup, but an Escape on a closed
    Autocomplete bubbles to the surrounding dialog and would close the dialog instead.
    """
    if not page.driver.find_elements(*OPTIONS):
        return
    field = page.wait_for_element(_tid(testid))
    field.send_keys(Keys.ESCAPE)
    try:
        page.poll().until(lambda d: not d.find_elements(*OPTIONS))
    except TimeoutException as exc:
        raise AssertionError(f"the option list of {testid!r} did not close") from exc


def choose_from_native_select(page: BasePage, testid: str, value: str) -> None:
    """Pick *value* in the MUI select whose hidden native input carries *testid*; read the value back.

    The care and history forms put their ``data-testid`` on the select's ``htmlInput``, which MUI renders as the
    hidden native input. The visible control is the ``combobox`` next to it; it opens on ``mousedown`` only, so
    the open is dispatched the way a pointer would (see ``BasePage.dispatch_menu_trigger_open``).
    """
    native = page.wait_for_element(_tid(testid))
    if native.get_attribute("value") == value:
        return
    trigger = page.driver.execute_script(
        "return arguments[0].closest('.MuiInputBase-root').querySelector(\"[role='combobox']\");",
        native,
    )
    if trigger is None:
        raise AssertionError(f"the select {testid!r} has no combobox")
    page.scroll_into_view(trigger)
    page.dispatch_menu_trigger_open(trigger)
    page._settle_listbox()
    page.select_option_by_value(value)
    page.poll().until(lambda _d: native.get_attribute("value") == value)


# ── Pflege tab ──────────────────────────────────────────────────────────────


class BedCareTab(BasePage):
    """The care tab of one bed: the task list and the "Neue Aufgabe" dialog."""

    TAB = _tid("bed-care-tab")
    CREATE = _tid("care-create")
    TASK_DIALOG = _tid("care-task-dialog")
    TASK_SUBMIT = _tid("care-task-submit")
    #: A task row is the ``li`` below the section lists; ``care-task-due-<key>`` / ``care-task-dialog`` are not.
    TASK_ROWS = (By.CSS_SELECTOR, "li[data-testid^='care-task-']")

    def create_task(self, category: str, name: str) -> str:
        """ "Neue Aufgabe" for the whole bed (the default scope): returns the new task's key.

        The row is awaited by its name - the dialog's ``onCreated`` reloads the list, so the row is the proof the
        server accepted the task.
        """
        self.wait_and_click(self.CREATE)
        self.wait_for_element(self.TASK_DIALOG)
        choose_from_native_select(self, "care-task-category", category)
        field = self.wait_for_element_clickable(_tid("care-task-name"))
        self.clear_and_fill(field, name)
        self.poll().until(lambda _d: (field.get_attribute("value") or "") == name)
        self.wait_and_click(self.TASK_SUBMIT)
        self.wait_for_element_hidden(self.TASK_DIALOG)
        return self.wait_for_task(name)

    def task_keys_by_name(self) -> dict[str, str]:
        """``{visible name: task key}`` of the rows shown now."""
        rows = {}
        for row in self.driver.find_elements(*self.TASK_ROWS):
            key = (row.get_attribute("data-testid") or "")[len("care-task-") :]
            rows[_text(row)] = key
        return rows

    def wait_for_task(self, name: str) -> str:
        """Wait until a row whose text contains *name* is listed; return its key."""

        def _row():
            for text, key in self.task_keys_by_name().items():
                if name in text:
                    return key
            return False

        try:
            return self.poll().until(lambda _d: _row())
        except TimeoutException as exc:
            raise AssertionError(
                f"the care tab lists no task named {name!r}; rows: {list(self.task_keys_by_name())}"
            ) from exc

    def wait_for_task_gone(self, task_key: str, what: str) -> None:
        try:
            self.wait_for_element_hidden(_tid(f"care-task-{task_key}"))
        except TimeoutException as exc:
            raise AssertionError(f"{what}: the task {task_key} is still listed as open") from exc

    def open_completion(self, task_key: str) -> CompletionDialog:
        self.wait_and_click(_tid(f"care-done-{task_key}"))
        dialog = CompletionDialog(self.driver, self.base_url)
        dialog.wait_for_element(dialog.DIALOG)
        return dialog

    # ── Wave 8: care log, suggestions ──────────────────────────────────

    LOG = _tid("care-log")
    SUGGESTED = _tid("care-section-suggested")
    OPEN_SECTION = _tid("care-section-open")

    def open_care_log(self) -> CareLogDialog:
        """ "Pflege protokollieren": the care log without a task."""
        self.wait_and_click(self.LOG)
        dialog = CareLogDialog(self.driver, self.base_url)
        dialog.wait_for_element(dialog.DIALOG)
        return dialog

    def has_suggestions_section(self) -> bool:
        """Whether the "Vorschläge" section is rendered now (call after the tab settled)."""
        return bool(self.driver.find_elements(*self.SUGGESTED))

    def suggestion_keys(self) -> list[str]:
        """Keys of the tasks listed in the "Vorschläge" section, in the order shown."""
        return [
            (row.get_attribute("data-testid") or "")[len("care-task-") :]
            for row in self.driver.find_elements(
                By.CSS_SELECTOR,
                "[data-testid='care-section-suggested'] li[data-testid^='care-task-']",
            )
        ]

    def open_task_keys(self) -> list[str]:
        """Keys of the tasks in the "Offen" section (not overdue, not suggested)."""
        return [
            (row.get_attribute("data-testid") or "")[len("care-task-") :]
            for row in self.driver.find_elements(
                By.CSS_SELECTOR, "[data-testid='care-section-open'] li[data-testid^='care-task-']"
            )
        ]

    def wait_for_suggestion(self, task_key: str, what: str) -> str:
        """Wait until *task_key* is listed under "Vorschläge"; return the section's heading and the row's text."""
        try:
            self.poll().until(lambda _d: task_key in self.suggestion_keys())
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the suggestion {task_key} is not listed; suggestions: {self.suggestion_keys()}"
            ) from exc
        return _text(self.wait_for_element(self.SUGGESTED))

    def suggestion_reason(self, task_key: str) -> str:
        return _text(self.wait_for_element(_tid(f"care-reason-{task_key}")))

    def suggestion_has_decisions(self, task_key: str) -> tuple[bool, bool]:
        """``(accept shown, dismiss shown)`` for the suggestion row of *task_key*."""
        return (
            bool(self.driver.find_elements(*_tid(f"care-accept-{task_key}"))),
            bool(self.driver.find_elements(*_tid(f"care-dismiss-{task_key}"))),
        )

    def _decide(self, testid: str, task_key: str, what: str) -> None:
        """Press "Annehmen"/"Verwerfen" and wait until the row left the "Vorschläge" section (the server answered)."""
        self.wait_and_click(_tid(testid))
        try:
            self.poll().until(lambda _d: task_key not in self.suggestion_keys())
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: {task_key} is still listed under 'Vorschläge' after the decision"
            ) from exc

    def accept_suggestion(self, task_key: str, what: str) -> None:
        """ "Annehmen": the task leaves "Vorschläge" and is awaited as an ordinary open task."""
        self._decide(f"care-accept-{task_key}", task_key, what)
        try:
            self.poll().until(lambda _d: task_key in self.open_task_keys())
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the accepted task {task_key} is not listed under 'Offen'; open: {self.open_task_keys()}"
            ) from exc

    def dismiss_suggestion(self, task_key: str, what: str) -> None:
        """ "Verwerfen": the task leaves "Vorschläge"; the caller asserts where it (does not) show up."""
        self._decide(f"care-dismiss-{task_key}", task_key, what)


class CompletionDialog(BasePage):
    """ "Erledigen: <Kategorie>" - the short form of one task; ``care-complete-*`` ids."""

    DIALOG = _tid("care-complete-dialog")
    SUBMIT = _tid("care-complete-submit")
    #: Test-id prefix of the shared form fields (``CareFormFields testId``).
    PREFIX = "care-complete"

    def _fill(self, testid: str, value: str) -> None:
        field = self.wait_for_element_clickable(_tid(testid))
        self.clear_and_fill(field, value)
        try:
            self.poll().until(lambda _d: (field.get_attribute("value") or "") == value)
        except TimeoutException as exc:
            raise AssertionError(
                f"the field {testid!r} should read {value!r}; it reads {field.get_attribute('value')!r}"
            ) from exc

    def set_product(self, label: str) -> None:
        """Type a product name into the free-solo field (no catalogue entry is needed)."""
        self._fill("care-complete-product", label)

    def set_quantity(self, quantity: str, unit: str) -> None:
        self._fill("care-complete-quantity", quantity)
        choose_from_native_select(self, "care-complete-unit", unit)

    def set_note(self, note: str) -> None:
        self._fill("care-complete-note", note)

    def submit_and_wait_closed(self, what: str) -> None:
        """Press the submit button; the dialog closes only after the server answered."""
        self.wait_and_click(self.SUBMIT)
        try:
            self.wait_for_element_hidden(self.DIALOG)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the completion dialog did not close after the submit"
            ) from exc

    # ── Wave 8: area dose, materials, liming hint (GP-FR-123/124) ──────

    def choose_product(self, label: str) -> None:
        """Pick the catalogue product *label* in the product Autocomplete (its data-sheet rate is pre-filled)."""
        choose_autocomplete_option(self, f"{self.PREFIX}-product", label, label)

    def set_quantity_only(self, quantity: str) -> None:
        self._fill(f"{self.PREFIX}-quantity", quantity)

    def set_unit(self, unit: str) -> None:
        choose_from_native_select(self, f"{self.PREFIX}-unit", unit)

    def quantity_value(self) -> str:
        return self.wait_for_element(_tid(f"{self.PREFIX}-quantity")).get_attribute("value") or ""

    def unit_value(self) -> str:
        return self.wait_for_element(_tid(f"{self.PREFIX}-unit")).get_attribute("value") or ""

    def wait_for_total(self, expected: str, what: str) -> str:
        """Wait until the live total line contains *expected* (``"288 g"``); return the whole line."""
        locator = _tid(f"{self.PREFIX}-total")

        def _line() -> str:
            found = self.driver.find_elements(*locator)
            return _text(found[0]) if found else ""

        try:
            self.poll().until(lambda _d: expected in _line())
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the total line should name {expected!r}; it reads {_line()!r}"
            ) from exc
        return _line()

    def has_total(self) -> bool:
        return bool(self.driver.find_elements(*_tid(f"{self.PREFIX}-total")))

    def text_of(self, part: str) -> str:
        """The text of ``<prefix>-<part>`` (``rate-source``, ``nitrogen``, ``liming-hint``, ``no-area-hint``); loud when absent."""
        try:
            return _text(self.wait_for_element(_tid(f"{self.PREFIX}-{part}")))
        except TimeoutException as exc:
            raise AssertionError(f"the form shows no {part!r} line") from exc

    def has_part(self, part: str) -> bool:
        return bool(self.driver.find_elements(*_tid(f"{self.PREFIX}-{part}")))

    def unit_options_disabled(self) -> dict[str, bool]:
        """Open the unit select, read ``{unit: disabled}`` of every option, close it again (Escape on the listbox)."""
        native = self.wait_for_element(_tid(f"{self.PREFIX}-unit"))
        trigger = self.driver.execute_script(
            "return arguments[0].closest('.MuiInputBase-root').querySelector(\"[role='combobox']\");",
            native,
        )
        if trigger is None:
            raise AssertionError("the unit select has no combobox")
        self.scroll_into_view(trigger)
        self.dispatch_menu_trigger_open(trigger)
        self._settle_listbox()
        prefix = f"{self.PREFIX}-unit-"
        rows = self.driver.find_elements(By.CSS_SELECTOR, f"li[data-testid^='{prefix}']")
        if not rows:
            raise AssertionError("the unit select opened no option")
        states = {
            (row.get_attribute("data-testid") or "")[len(prefix) :]: row.get_attribute(
                "aria-disabled"
            )
            == "true"
            for row in rows
        }
        self.close_mui_dropdown()
        return states

    def material_options(self) -> list[str]:
        """The labels the material Autocomplete offers (opened by keyboard, closed again)."""
        labels = open_autocomplete_options(self, f"{self.PREFIX}-material")
        close_autocomplete(self, f"{self.PREFIX}-material")
        return labels

    def choose_material(self, label: str) -> None:
        choose_autocomplete_option(self, f"{self.PREFIX}-material", label, label)

    def submit_expecting_field_error(self, field: str, message: str, what: str) -> None:
        """Press submit and wait for the field error *message* on ``<prefix>-<field>``; the dialog must stay open."""
        self.wait_and_click(self.SUBMIT)
        wait_for_field_error(self, f"{self.PREFIX}-{field}", message, what)
        if not self.driver.find_elements(*self.DIALOG):
            raise AssertionError(f"{what}: the dialog closed although the form was refused")


class CareLogDialog(CompletionDialog):
    """ "Pflege protokollieren" - a care line without a task (``CareLogDialog``); the same form, ``care-log-*`` ids."""

    DIALOG = _tid("care-log-dialog")
    SUBMIT = _tid("care-log-submit")
    PREFIX = "care-log"

    def choose_category(self, category: str) -> None:
        choose_from_native_select(self, "care-log-category", category)


# ── Downloads ───────────────────────────────────────────────────────────────

#: Records every blob the page hands to a download anchor (``saveBlob``): the object URL's blob and the anchor's
#: ``download`` name. The original ``createObjectURL`` and ``click`` still run, so the page behaves exactly as for a
#: user; the probe only keeps a reference to what was saved.
_DOWNLOAD_PROBE_INSTALL = """
if (!window.__kpDownloadProbe) {
  window.__kpDownloadProbe = {blobs: {}, saved: []};
  var create = URL.createObjectURL.bind(URL);
  URL.createObjectURL = function (obj) {
    var url = create(obj);
    if (obj instanceof Blob) { window.__kpDownloadProbe.blobs[url] = obj; }
    return url;
  };
  var click = HTMLAnchorElement.prototype.click;
  HTMLAnchorElement.prototype.click = function () {
    var blob = window.__kpDownloadProbe.blobs[this.href];
    if (this.download && blob) { window.__kpDownloadProbe.saved.push({name: this.download, blob: blob}); }
    return click.apply(this, arguments);
  };
}
return window.__kpDownloadProbe.saved.length;
"""

#: The bytes of saved download *n*: name, size, the first three bytes and the text (UTF-8, BOM kept as U+FEFF).
_DOWNLOAD_READ = """
var done = arguments[arguments.length - 1];
var entry = window.__kpDownloadProbe && window.__kpDownloadProbe.saved[arguments[0]];
if (!entry) { done(null); return; }
entry.blob.arrayBuffer().then(function (buffer) {
  var bytes = new Uint8Array(buffer);
  done({name: entry.name, size: bytes.length, head: Array.from(bytes.slice(0, 3)),
        type: entry.blob.type, text: new TextDecoder('utf-8', {ignoreBOM: true}).decode(bytes)});
}, function (error) { done({error: String(error)}); });
"""


class DownloadCapture(BasePage):
    """Reads what the page saved as a download: the blob ``saveBlob`` hands to its anchor (no file system access).

    The Selenium grid's browser writes downloads into its own container, out of the test's reach; the blob is the
    exact content of that file. :meth:`start_download_capture` must run before the click; :meth:`wait_for_download`
    then waits for the next saved blob and fails loudly when none arrives, so "the probe saw nothing" can never read
    as an empty file.
    """

    def start_download_capture(self) -> int:
        """Install the probe (idempotent); return how many downloads it has seen so far."""
        return int(self.driver.execute_script(_DOWNLOAD_PROBE_INSTALL))

    def wait_for_download(self, seen_before: int, what: str) -> dict:
        """Wait for download number *seen_before* (0-based) and return ``{name, size, head, type, text}``."""
        try:
            self.poll().until(
                lambda d: (
                    d.execute_script("return window.__kpDownloadProbe.saved.length;") > seen_before
                )
            )
        except TimeoutException as exc:
            raise AssertionError(f"{what}: the page saved no download") from exc
        saved = self.driver.execute_async_script(_DOWNLOAD_READ, seen_before)
        if not isinstance(saved, dict) or "error" in saved:
            raise AssertionError(f"{what}: the saved download could not be read: {saved!r}")
        return saved

    def export_csv(self, prefix: str, delimiter: str, what: str) -> dict:
        """ "CSV exportieren" → *delimiter* (``comma``/``semicolon``) of the export button *prefix*; the saved file."""
        seen = self.start_download_capture()
        self.wait_and_click(_tid(f"{prefix}-export"))
        try:
            item = self.wait_for_element_visible(_tid(f"{prefix}-export-{delimiter}"))
        except TimeoutException as exc:
            raise AssertionError(f"{what}: the export menu offers no {delimiter!r} entry") from exc
        self.click_menu_option(item)
        return self.wait_for_download(seen, what)


class CareHistoryPage(DownloadCapture):
    """ "Historie aller Beete" (``/standorte/historie``, ``CareHistoryPage``)."""

    PATH = "/standorte/historie"
    PAGE = _tid("care-history-page")

    def open(self) -> CareHistoryPage:
        self.navigate(self.PATH)
        self.wait_for_content(self.PAGE, "the tenant-wide care history")
        return self

    def export_csv_comma(self, what: str) -> dict:
        return self.export_csv("care-history", "comma", what)


# ── Historie tab ────────────────────────────────────────────────────────────


class HistoryTab(DownloadCapture):
    """The history tab of one bed: filter bar, rows, "Mehr laden", the planting timeline, the CSV download and the
    follow-up crop recommendation below the timeline."""

    TAB = _tid("bed-history-tab")
    LIST = _tid("history-list")
    MORE = _tid("history-more")
    TIMELINE = _tid("bed-timeline")
    ITEMS = (By.CSS_SELECTOR, "[data-testid='history-list'] [data-testid^='history-item-']")
    #: ``role=status`` line under the list: "<n> Einträge angezeigt" (``pages.bed.history.shown``).
    COUNT_LINE = (
        By.CSS_SELECTOR,
        "[data-testid='bed-history-tab'] [role='status'][aria-live='polite']",
    )

    def item_texts(self) -> list[str]:
        return [_text(item) for item in self.driver.find_elements(*self.ITEMS)]

    def item_instants(self) -> list[str]:
        """The ``datetime`` of every row's ``<time>``, in the order shown."""
        return [
            time.get_attribute("datetime") or ""
            for time in self.driver.find_elements(
                By.CSS_SELECTOR, "[data-testid='history-list'] [data-testid^='history-item-'] time"
            )
        ]

    def item_has_button(self) -> bool:
        """Whether any history row carries an action (edit, delete): the list is read-only by design."""
        return bool(
            self.driver.find_elements(
                By.CSS_SELECTOR,
                "[data-testid='history-list'] [data-testid^='history-item-'] button, "
                "[data-testid='history-list'] [data-testid^='history-item-'] [role='button']",
            )
        )

    def shown_count(self) -> int | None:
        """The count the live region announces ("50 Einträge angezeigt"), or ``None`` while it names none."""
        for line in self.driver.find_elements(*self.COUNT_LINE):
            match = re.search(r"(\d+)\s+Eintr", _text(line))
            if match:
                return int(match.group(1))
        return None

    def wait_for_shown(self, expected: int, what: str) -> None:
        """Wait until the live region announces exactly *expected* entries and the list holds that many rows."""

        def _settled() -> bool:
            return self.shown_count() == expected and len(self.item_texts()) == expected

        try:
            self.poll().until(lambda _d: _settled())
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: expected {expected} history entries, the live region says "
                f"{self.shown_count()} and the list holds {len(self.item_texts())}"
            ) from exc

    #: Per history row: whether its box lies inside the viewport, and whether it renders with a size.
    _ROW_IN_VIEW = (
        "return arguments[0].map(function (el) { var r = el.getBoundingClientRect();"
        " return r.height > 0 && r.width > 0 && r.top < window.innerHeight && r.bottom > 0; });"
    )

    def reveal_entries(self, expected: int, what: str) -> int:
        """Wait for exactly *expected* rows, scroll the first one into view, return how many rows are on screen.

        The list sits below the timeline and the recommendation panel, so a screenshot taken right after the tab
        settled shows the reserved area above it, not the entries. Loud when the first row is not on screen after
        the scroll (zero size or outside the viewport): the checkpoint would again show no entry.
        """
        self.wait_for_shown(expected, what)
        items = self.driver.find_elements(*self.ITEMS)
        self.scroll_into_view(items[0])
        in_view = self.driver.execute_script(self._ROW_IN_VIEW, items)
        if not in_view or not in_view[0]:
            raise AssertionError(
                f"{what}: the first history entry is not on screen after scrolling to it"
            )
        return sum(1 for flag in in_view if flag)

    def filter_category(self, category: str) -> None:
        """Pick a category in the filter bar (``''`` is "Alle Kategorien")."""
        choose_from_native_select(self, "history-category", category)

    def load_more(self) -> None:
        """ "Mehr laden": the next page; returns once the button was pressed (the caller awaits the count)."""
        self.wait_and_click(self.MORE)

    def has_more(self) -> bool:
        return bool(self.driver.find_elements(*self.MORE))

    def timeline_years(self) -> dict[int, list[str]]:
        """``{year: [family key, ...]}`` of the timeline rows; a fallow chip is ``fallow``."""
        years: dict[int, list[str]] = {}
        for row in self.driver.find_elements(By.CSS_SELECTOR, "[data-testid^='timeline-year-']"):
            year = int((row.get_attribute("data-testid") or "").rsplit("-", 1)[1])
            years[year] = [
                (chip.get_attribute("data-testid") or "").split(f"timeline-planting-{year}-", 1)[1]
                for chip in row.find_elements(
                    By.CSS_SELECTOR, "[data-testid^='timeline-planting-']"
                )
            ]
        return years

    # ── Wave 8: CSV download, follow-up crop recommendation ────────────

    SUCCESSION = _tid("succession-panel")

    def export_csv_comma(self, what: str) -> dict:
        """ "CSV exportieren" → "CSV (Komma)": the saved file as :meth:`DownloadCapture.wait_for_download` reads it."""
        return self.export_csv("history", "comma", what)

    def wait_for_succession(self, what: str) -> dict[str, object]:
        """Wait until the recommendation panel answered (no longer ``aria-busy``); return what it shows.

        ``{"basis": str | None, "status": str | None, "families": [family key, ...]}`` - ``basis`` is the "Nach …
        passt als Nächstes …" line, ``status`` the info line of a non-``ok`` answer. Loud when the panel stays busy
        or shows its load error.
        """
        try:
            panel = self.wait_for_element(self.SUCCESSION)
            self.poll().until(lambda _d: panel.get_attribute("aria-busy") == "false")
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the follow-up crop recommendation never finished loading"
            ) from exc
        if self.driver.find_elements(*_tid("succession-error")):
            raise AssertionError(f"{what}: the recommendation shows its load error")

        def _optional(testid: str) -> str | None:
            found = self.driver.find_elements(*_tid(testid))
            return _text(found[0]) if found else None

        return {
            "basis": _optional("succession-basis"),
            "status": _optional("succession-status"),
            "families": [
                (row.get_attribute("data-testid") or "")[len("succession-family-") :]
                for row in self.driver.find_elements(
                    By.CSS_SELECTOR, "[data-testid^='succession-family-']"
                )
            ],
            "text": _text(panel),
        }

    def wait_for_timeline_family(self, year: int, family_key: str, what: str) -> None:
        try:
            self.poll().until(lambda _d: family_key in self.timeline_years().get(year, []))
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the timeline of {year} should show family {family_key!r}; it shows "
                f"{self.timeline_years()}"
            ) from exc


__all__ = [
    "BedCareTab",
    "CareHistoryPage",
    "CareLogDialog",
    "CompletionDialog",
    "DownloadCapture",
    "HistoryTab",
    "choose_autocomplete_option",
    "choose_from_native_select",
    "field_helper_text",
    "wait_for_field_error",
]
