"""Page objects for the bed list as CSV - export and import (REQ-053 WP 8.25, 8.27; tested in WP 8.31).

* :class:`BedListExportDialog` - the export dialog of the plan (``ExportDialog``) with the format "Beetliste (CSV)":
  the column checkboxes, the Excel switch, the assignment opt-in (SR-024) and the download, read through
  :class:`~.bed_care_page.DownloadCapture` (the blob ``saveBlob`` hands to its anchor - the Selenium grid's download
  folder is out of the runner's reach).
* :class:`BedCsvImportPanel` - "Beetliste importieren (CSV)" inside the import wizard (``BedCsvImportPanel``): the
  file, the check report, the confirmation and "Zum Plan".

Both dialogs are opened through :class:`~.garden_plan_page.GardenPlanPage` ("Export & Import"). Every hook is a
``data-testid`` of ``src/frontend/src/features/gardenPlanner/io/`` - none is guessed. Checkboxes and switches are
switched with the keyboard (focus + Space on the native input MUI draws at opacity 0 over the control: the element
that receives the activation, and Space is its own activation key). Every state change is read back.
"""

from __future__ import annotations

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from .base_page import BasePage
from .bed_care_page import DownloadCapture
from .bed_site_page import press_space_on
from .garden_plan_page import GardenPlanPage


def _tid(testid: str) -> tuple[str, str]:
    return (By.CSS_SELECTOR, f"[data-testid='{testid}']")


def _text(element: WebElement) -> str:
    return " ".join((element.get_attribute("textContent") or "").split())


class BedListExportDialog(DownloadCapture):
    """The export dialog switched to "Beetliste (CSV)"."""

    DIALOG = _tid("plan-export-dialog")
    FORMAT_CSV = _tid("plan-export-format-csv")
    EXCEL = _tid("plan-export-csv-excel")
    ASSIGNMENT = _tid("plan-export-csv-assignment")
    ASSIGNMENT_HINT = _tid("plan-export-csv-assignment-hint")
    NO_COLUMNS = _tid("plan-export-csv-no-columns")
    SUMMARY = _tid("plan-export-csv-summary")
    PRIVACY = _tid("plan-export-privacy")
    DOWNLOAD = _tid("plan-export-download")
    ERROR = _tid("plan-export-error")
    COLUMN_INPUTS = (By.CSS_SELECTOR, "[data-testid^='plan-export-csv-column-']")

    def open_from(self, plan: GardenPlanPage) -> BedListExportDialog:
        """ "Export & Import" -> "Plan exportieren …" -> format "Beetliste (CSV)"; verified on ``aria-pressed``."""
        plan.open_export()
        self.wait_and_click(self.FORMAT_CSV)
        try:
            self.poll().until(
                lambda d: (
                    d.find_element(*self.FORMAT_CSV).get_attribute("aria-pressed") == "true"
                    and d.find_elements(*self.SUMMARY)
                )
            )
        except TimeoutException as exc:
            raise AssertionError(
                "the export format 'Beetliste (CSV)' did not become active"
            ) from exc
        return self

    def offers_csv(self) -> bool:
        self.wait_for_element(self.DIALOG)
        return self.is_present(self.FORMAT_CSV)

    def columns(self) -> dict[str, bool]:
        """column id -> ticked, for every column checkbox of the dialog."""
        return {
            (box.get_attribute("data-testid") or "")[
                len("plan-export-csv-column-") :
            ]: box.is_selected()
            for box in self.driver.find_elements(*self.COLUMN_INPUTS)
        }

    def column_label(self, column: str) -> str:
        box = self.wait_for_element(_tid(f"plan-export-csv-column-{column}"))
        return self.driver.execute_script(
            "var label = arguments[0].closest('label'); return label ? label.textContent.trim() : '';",
            box,
        )

    def set_column(self, column: str, ticked: bool) -> None:
        box = self.wait_for_element(_tid(f"plan-export-csv-column-{column}"))
        if box.is_selected() is ticked:
            raise AssertionError(
                f"column {column!r} is already {'ticked' if ticked else 'unticked'}"
            )
        press_space_on(self, box, f"column {column!r}")
        try:
            self.poll().until(lambda _d: box.is_selected() is ticked)
        except TimeoutException as exc:
            raise AssertionError(
                f"column {column!r} did not become {'ticked' if ticked else 'unticked'}"
            ) from exc

    def _switch(self, locator: tuple[str, str], on: bool, what: str) -> None:
        switch = self.wait_for_element(locator)
        if switch.is_selected() is on:
            raise AssertionError(f"{what} is already {'on' if on else 'off'}")
        press_space_on(self, switch, what)
        try:
            self.poll().until(lambda _d: switch.is_selected() is on)
        except TimeoutException as exc:
            raise AssertionError(f"{what} did not switch {'on' if on else 'off'}") from exc

    def set_excel(self, on: bool) -> None:
        self._switch(self.EXCEL, on, "'Excel-Variante'")

    def is_assignment_on(self) -> bool:
        return self.wait_for_element(self.ASSIGNMENT).is_selected()

    def set_assignment(self, on: bool) -> None:
        self._switch(self.ASSIGNMENT, on, "'Zuweisungen einschließen'")

    def assignment_label(self) -> str:
        switch = self.wait_for_element(self.ASSIGNMENT)
        return self.driver.execute_script(
            "var label = arguments[0].closest('label'); return label ? label.textContent.trim() : '';",
            switch,
        )

    def text_of(self, locator: tuple[str, str]) -> str:
        return _text(self.wait_for_element(locator))

    def is_download_enabled(self) -> bool:
        return self.wait_for_element(self.DOWNLOAD).is_enabled()

    def download(self, what: str) -> dict:
        """ "Herunterladen"; the saved file once the dialog closed (it closes only after the request succeeded)."""
        seen = self.start_download_capture()
        self.wait_and_click(self.DOWNLOAD)
        try:
            self.wait_for_element_hidden(self.DIALOG)
        except TimeoutException as exc:
            error = self.text_of(self.ERROR) if self.is_present(self.ERROR) else None
            raise AssertionError(
                f"{what}: the export dialog did not close (error: {error!r})"
            ) from exc
        return self.wait_for_download(seen, what)

    def close(self) -> None:
        """ "Abbrechen" - the first action of the dialog; return once it is gone."""
        self.wait_and_click(
            (
                By.CSS_SELECTOR,
                "[data-testid='plan-export-dialog'] .MuiDialogActions-root button:first-of-type",
            )
        )
        self.wait_for_element_hidden(self.DIALOG)


class BedCsvImportPanel(BasePage):
    """ "Beetliste importieren (CSV)" in the import wizard."""

    PANEL = _tid("plan-csv-import")
    FILE = _tid("plan-csv-file")
    SUMMARY = _tid("plan-csv-summary")
    REPORT = _tid("plan-csv-report")
    ERRORS = _tid("plan-csv-errors")
    WARNINGS = _tid("plan-csv-warnings")
    FAILURE = _tid("plan-csv-failure")
    FILE_ERROR = _tid("plan-csv-file-error")
    APPLY = _tid("plan-csv-apply")
    DONE = _tid("plan-csv-done")
    CLOSE = _tid("plan-csv-close")
    CANCEL = _tid("plan-import-cancel")
    WIZARD = _tid("plan-import-wizard")

    def open_from(self, plan: GardenPlanPage) -> BedCsvImportPanel:
        plan.open_csv_import()
        return self

    def choose_file(self, path: str) -> None:
        """Hand the file to the hidden input; return once the server's check report is shown (or fail with its refusal)."""
        file_input = self.find_present(self.FILE)
        self.driver.execute_script(
            "arguments[0].removeAttribute('hidden');"
            "arguments[0].style.display = 'block';"
            "arguments[0].style.width = '1px';"
            "arguments[0].style.height = '1px';"
            "arguments[0].style.opacity = '0.01';",
            file_input,
        )
        file_input.send_keys(path)

        def _report() -> bool:
            for failure in (self.FAILURE, self.FILE_ERROR):
                if self.is_present(failure):
                    raise AssertionError(
                        f"the CSV {path!r} was refused: {_text(self.driver.find_element(*failure))!r}"
                    )
            return self.is_present(self.REPORT)

        try:
            self.poll(timeout=30).until(lambda _d: _report())
        except TimeoutException as exc:
            raise AssertionError(f"no check report appeared for {path!r}") from exc

    def summary(self) -> str:
        return _text(self.wait_for_element(self.SUMMARY))

    def _items(self, container: tuple[str, str]) -> list[str]:
        found = self.driver.find_elements(*container)
        if not found:
            return []
        return [_text(item) for item in found[0].find_elements(By.CSS_SELECTOR, "li")]

    def error_lines(self) -> list[str]:
        return self._items(self.ERRORS)

    def warning_lines(self) -> list[str]:
        return self._items(self.WARNINGS)

    def bed_lines(self) -> list[str]:
        """The beds the report would create (the list after "N Beete werden angelegt")."""
        report = self.wait_for_element(self.REPORT)
        lists = [
            ul
            for ul in report.find_elements(By.CSS_SELECTOR, "ul")
            if not ul.find_elements(
                By.XPATH,
                "ancestor::*[@data-testid='plan-csv-errors' or @data-testid='plan-csv-warnings']",
            )
        ]
        return [_text(li) for ul in lists for li in ul.find_elements(By.CSS_SELECTOR, "li")]

    def apply_label(self) -> str:
        return _text(self.wait_for_element(self.APPLY))

    def apply(self, what: str) -> str:
        """ "N Beete anlegen"; return the success line once the server wrote the valid lines."""
        self.wait_and_click(self.APPLY)

        def _done() -> str | bool:
            if self.is_present(self.FAILURE):
                raise AssertionError(
                    f"{what}: the import failed: {_text(self.driver.find_element(*self.FAILURE))!r}"
                )
            return (
                _text(self.driver.find_element(*self.DONE)) if self.is_present(self.DONE) else False
            )

        try:
            return self.poll(timeout=30).until(lambda _d: _done())
        except TimeoutException as exc:
            raise AssertionError(f"{what}: the import was never confirmed as written") from exc

    def cancel(self) -> None:
        """ "Abbrechen" of the wizard; return once it is closed."""
        self.wait_and_click(self.CANCEL)
        self.wait_for_element_hidden(self.WIZARD)

    def to_editor(self) -> None:
        """ "Zum Plan" after the write; return once the wizard is closed."""
        self.wait_and_click(self.CLOSE)
        self.wait_for_element_hidden(self.WIZARD)
