"""Page objects for the care and history surfaces of the bed view (REQ-053 WP 4.4 / 4.5).

Three objects, one per surface the wave 4 tests drive:

* :class:`BedCareTab` - the "Pflege" tab of ``/standorte/locations/:key#care``: create a task on the bed, find
  its row, open its completion dialog;
* :class:`CompletionDialog` - the short, category-specific completion form (``CareCompletionDialog``);
* :class:`HistoryTab` - the "Historie" tab: category filter, "Mehr laden", the corrections switch, the list rows
  and the planting timeline (``BedHistoryTab`` / ``HistoryList`` / ``PlantingTimeline``).

Every hook is a ``data-testid`` that exists in ``src/frontend/src/features/gardenPlanner/`` - none is guessed.
State-changing helpers read their effect back and fail loudly when it never arrives (`e2e-test-stability` §D);
there is no retry loop and no sleep: a wait is a condition on the page (a row, a closed dialog, a list count, the
live-region text).
"""

from __future__ import annotations

import re

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from .base_page import BasePage


def _tid(testid: str) -> tuple[str, str]:
    return (By.CSS_SELECTOR, f"[data-testid='{testid}']")


def _text(element: WebElement) -> str:
    return " ".join((element.get_attribute("textContent") or "").split())


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


class CompletionDialog(BasePage):
    """ "Erledigen: <Kategorie>" - the short form of one task; ``care-complete-*`` ids."""

    DIALOG = _tid("care-complete-dialog")
    SUBMIT = _tid("care-complete-submit")

    def _fill(self, testid: str, value: str) -> None:
        field = self.wait_for_element_clickable(_tid(testid))
        self.clear_and_fill(field, value)
        self.poll().until(lambda _d: (field.get_attribute("value") or "") == value)

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


# ── Historie tab ────────────────────────────────────────────────────────────


class HistoryTab(BasePage):
    """The history tab of one bed: filter bar, rows, "Mehr laden", the planting timeline."""

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

    def wait_for_timeline_family(self, year: int, family_key: str, what: str) -> None:
        try:
            self.poll().until(lambda _d: family_key in self.timeline_years().get(year, []))
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the timeline of {year} should show family {family_key!r}; it shows "
                f"{self.timeline_years()}"
            ) from exc


__all__ = ["BedCareTab", "CompletionDialog", "HistoryTab", "choose_from_native_select"]
