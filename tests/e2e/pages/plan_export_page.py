"""Page objects for the REQ-053 wave 9 export, renderer and site surfaces (WP 9.7-9.14; tested in WP 9.16).

* :class:`PlanExportDialog` - the export dialog (``io/ExportDialog.tsx``) beyond the CSV of wave 8: the PNG drawn in
  the browser (format, factor, the size line, the download) and the PDF with the parcel page and its assignment
  opt-in. Downloads are read through :class:`~.bed_care_page.DownloadCapture` (the blob ``saveBlob`` hands to its
  anchor); binary files come back as bytes here (base64 over the WebDriver wire).
* :class:`Wave9PlanPage` - the plan editor's wave 9 parts: template export/import in the template tool
  (``templates/TemplatePanel.tsx`` / ``TemplateImportDialog.tsx``), "Regen — übersprungen" in the watering round
  (``zones/WateringRoundDialog.tsx``), the bed list's water column (``bed/BedListSection.tsx``), the renderer.
* :class:`BedHeadWave9` - the bed head's water distance and site-flags chip (``bed/BedHeader.tsx``).

Every hook is a ``data-testid`` that exists in ``src/frontend/src/features/gardenPlanner/`` - none is guessed.
Checkboxes and switches are switched with the keyboard (focus + Space on the native input MUI draws over the
control); toggle buttons and plain buttons get a real click. Every state change is read back and a helper fails
loudly when its effect never arrives (`e2e-test-stability` §D); there is no retry loop and no sleep.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from .bed_care_page import DownloadCapture
from .bed_list_csv_page import BedListExportDialog
from .bed_site_page import press_space_on
from .bed_view_page import BedViewPage
from .garden_plan_page import GardenPlanPage


def _tid(testid: str) -> tuple[str, str]:
    return (By.CSS_SELECTOR, f"[data-testid='{testid}']")


def _text(element: WebElement) -> str:
    return " ".join((element.get_attribute("textContent") or "").split())


#: The bytes of saved download *n* as base64, with its name and MIME type (the probe of ``DownloadCapture``).
_DOWNLOAD_BYTES = """
var done = arguments[arguments.length - 1];
var entry = window.__kpDownloadProbe && window.__kpDownloadProbe.saved[arguments[0]];
if (!entry) { done(null); return; }
var reader = new FileReader();
reader.onload = function () {
  var url = String(reader.result);
  done({name: entry.name, type: entry.blob.type, size: entry.blob.size, base64: url.slice(url.indexOf(',') + 1)});
};
reader.onerror = function () { done({error: String(reader.error)}); };
reader.readAsDataURL(entry.blob);
"""

#: Every request URL the page made to *fragment* so far (resource timing keeps the full URL with its query).
_REQUEST_URLS = """
var fragment = arguments[0];
return performance.getEntriesByType('resource').map(function (e) { return e.name; })
  .filter(function (name) { return name.indexOf(fragment) >= 0; });
"""


def read_download_bytes(page: DownloadCapture, seen_before: int, what: str) -> dict:
    """Wait for download number *seen_before* and return ``{name, type, size, data: bytes}``."""
    try:
        page.poll(timeout=60).until(
            lambda d: (
                d.execute_script("return window.__kpDownloadProbe.saved.length;") > seen_before
            )
        )
    except TimeoutException as exc:
        raise AssertionError(f"{what}: the page saved no download") from exc
    saved = page.driver.execute_async_script(_DOWNLOAD_BYTES, seen_before)
    if not isinstance(saved, dict) or "error" in saved or "base64" not in saved:
        raise AssertionError(f"{what}: the saved download could not be read: {saved!r}")
    data = base64.b64decode(saved["base64"])
    if len(data) != int(saved["size"]):
        raise AssertionError(
            f"{what}: read {len(data)} of {saved['size']} bytes of {saved['name']!r}"
        )
    return {"name": saved["name"], "type": saved["type"], "size": len(data), "data": data}


class PlanExportDialog(BedListExportDialog):
    """The export dialog: PNG and PDF (the CSV half is :class:`BedListExportDialog`)."""

    PNG_SUMMARY = _tid("plan-export-png-summary")
    PNG_CAPPED = _tid("plan-export-png-capped")
    PARCEL_LIST = _tid("plan-export-parcel-list")
    PARCEL_ASSIGNMENT = _tid("plan-export-parcel-assignment")
    PARCEL_ASSIGNMENT_HINT = _tid("plan-export-parcel-assignment-hint")

    def open_with_format(self, plan: GardenPlanPage, fmt: str) -> PlanExportDialog:
        """ "Export & Import" -> "Plan exportieren …" -> format *fmt* (``pdf``/``png``/…); verified on ``aria-pressed``."""
        # Resource timing keeps 250 entries by default; a long session of chunks and API reads fills it, and a full
        # buffer drops the export requests :meth:`request_urls` reads. Raised before the dialog's first request.
        self.driver.execute_script("performance.setResourceTimingBufferSize(10000);")
        plan.open_export()
        locator = _tid(f"plan-export-format-{fmt}")
        button = self.wait_for_element(locator)
        if button.get_attribute("aria-pressed") != "true":
            self.wait_and_click(locator)
        try:
            self.poll().until(
                lambda d: d.find_element(*locator).get_attribute("aria-pressed") == "true"
            )
        except TimeoutException as exc:
            raise AssertionError(f"the export format {fmt!r} did not become active") from exc
        return self

    # ── PNG ────────────────────────────────────────────────────────────

    PNG_WATERMARK = _tid("plan-export-png-watermark")

    def png_factor_chosen(self) -> int:
        """The factor whose toggle is pressed; loud when none or several are."""
        pressed = [
            factor
            for factor in (1, 2, 4)
            if self.wait_for_element(_tid(f"plan-export-png-resolution-{factor}")).get_attribute(
                "aria-pressed"
            )
            == "true"
        ]
        if len(pressed) != 1:
            raise AssertionError(f"exactly one PNG factor should be pressed, pressed are {pressed}")
        return pressed[0]

    def is_png_watermark_on(self) -> bool:
        return self.wait_for_element(self.PNG_WATERMARK).is_selected()

    def choose_png_factor(self, factor: int) -> None:
        locator = _tid(f"plan-export-png-resolution-{factor}")
        self.wait_and_click(locator)
        try:
            self.poll().until(
                lambda d: d.find_element(*locator).get_attribute("aria-pressed") == "true"
            )
        except TimeoutException as exc:
            raise AssertionError(f"the PNG factor {factor}x did not become active") from exc

    def wait_for_png_summary(self, expected: str, what: str) -> str:
        try:
            self.poll().until(lambda _d: self.text_of(self.PNG_SUMMARY) == expected)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the size line should read {expected!r}, it reads {self.text_of(self.PNG_SUMMARY)!r}"
            ) from exc
        return expected

    def is_png_capped(self) -> bool:
        self.wait_for_element(self.PNG_SUMMARY)
        return self.is_present(self.PNG_CAPPED)

    # ── PDF: parcel page ───────────────────────────────────────────────

    def is_parcel_list_on(self) -> bool:
        return self.wait_for_element(self.PARCEL_LIST).is_selected()

    def set_parcel_list(self, on: bool) -> None:
        box = self.wait_for_element(self.PARCEL_LIST)
        if box.is_selected() is on:
            raise AssertionError(
                f"'Parzellenliste als Zusatzseite' is already {'on' if on else 'off'}"
            )
        press_space_on(self, box, "'Parzellenliste als Zusatzseite'")
        try:
            self.poll().until(lambda _d: box.is_selected() is on)
        except TimeoutException as exc:
            raise AssertionError(
                f"'Parzellenliste als Zusatzseite' did not switch {'on' if on else 'off'}"
            ) from exc

    def has_parcel_assignment(self) -> bool:
        """Whether the assignment opt-in is offered (only under a ticked parcel list); read after the dialog settled."""
        self.wait_for_element(self.PARCEL_LIST)
        return self.is_present(self.PARCEL_ASSIGNMENT)

    def is_parcel_assignment_on(self) -> bool:
        return self.wait_for_element(self.PARCEL_ASSIGNMENT).is_selected()

    def set_parcel_assignment(self, on: bool) -> None:
        self._switch(self.PARCEL_ASSIGNMENT, on, "'Zuweisungen in die Parzellenliste aufnehmen'")

    # ── Download ───────────────────────────────────────────────────────

    def download_file(self, what: str) -> dict:
        """ "Herunterladen"; the saved file as bytes once the dialog closed (it closes after the file is saved)."""
        seen = self.start_download_capture()
        self.wait_and_click(self.DOWNLOAD)
        try:
            self.wait_for_element_hidden(self.DIALOG, timeout=60)
        except TimeoutException as exc:
            error = self.text_of(self.ERROR) if self.is_present(self.ERROR) else None
            raise AssertionError(
                f"{what}: the export dialog did not close (error: {error!r})"
            ) from exc
        return read_download_bytes(self, seen, what)

    def request_urls(self, fragment: str) -> list[str]:
        """The URLs the page requested containing *fragment*, oldest first (with their query strings)."""
        return list(self.driver.execute_script(_REQUEST_URLS, fragment))


class Wave9PlanPage(GardenPlanPage):
    """The plan editor's wave 9 parts."""

    # ── Template exchange (GP-FR-173, WP 9.9) ──────────────────────────

    TEMPLATE_SELECT = _tid("garden-plan-template-select")
    TEMPLATE_EXPORT = _tid("garden-plan-template-export")
    TEMPLATE_IMPORT = _tid("garden-plan-template-import")
    TEMPLATE_NOTICE = _tid("garden-plan-template-exchange-notice")
    IMPORT_DIALOG = _tid("garden-plan-template-import-dialog")
    IMPORT_FILE = _tid("garden-plan-template-import-file")
    IMPORT_REPORT = _tid("garden-plan-template-import-report")
    IMPORT_ERROR = _tid("garden-plan-template-import-error")
    IMPORT_NAME = _tid("garden-plan-template-import-name")
    IMPORT_RECHECK = _tid("garden-plan-template-import-recheck")
    IMPORT_CONFIRM = _tid("garden-plan-template-import-confirm")

    def picked_template(self) -> str:
        """The committed value of the template picker (its native input)."""
        return self.wait_for_element(self.TEMPLATE_SELECT).get_attribute("value") or ""

    def wait_for_picked_template(self, template_key: str, what: str) -> None:
        """Wait until the picker holds *template_key* (it shows a key only once the reloaded catalogue lists it)."""
        try:
            self.poll(timeout=30).until(lambda _d: self.picked_template() == template_key)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the picker should hold {template_key!r}, it holds {self.picked_template()!r}"
            ) from exc

    def wait_for_template_notice(self, expected: str, what: str) -> str:
        try:
            self.poll(timeout=30).until(lambda _d: self.is_present(self.TEMPLATE_NOTICE))
        except TimeoutException as exc:
            raise AssertionError(f"{what}: the template panel shows no notice") from exc
        text = self.text_of(self.TEMPLATE_NOTICE)
        if text != expected:
            raise AssertionError(f"{what}: the notice should read {expected!r}, it reads {text!r}")
        return text

    def export_picked_template(self, what: str) -> dict:
        """ "Exportieren" of the picked template; the saved file parsed as JSON, with its file name."""
        capture = DownloadCapture(self.driver, self.base_url)
        seen = capture.start_download_capture()
        button = self.wait_for_element(self.TEMPLATE_EXPORT)
        if button.get_attribute("aria-disabled") == "true":
            raise AssertionError(f"{what}: 'Exportieren' is disabled - no template picked")
        self.wait_and_click(self.TEMPLATE_EXPORT)
        saved = read_download_bytes(capture, seen, what)
        try:
            document = json.loads(saved["data"].decode("utf-8"))
        except ValueError as exc:
            raise AssertionError(
                f"{what}: the template file is no JSON: {saved['data'][:120]!r}"
            ) from exc
        return {"name": saved["name"], "document": document}

    def open_template_import(self) -> None:
        self.wait_and_click(self.TEMPLATE_IMPORT)
        self.wait_for_element_visible(self.IMPORT_DIALOG)

    def choose_template_file(self, path: Path, what: str) -> str:
        """Hand *path* to the dialog's hidden file input; return the branch the check settled on (report/error)."""
        file_input = self.find_present(self.IMPORT_FILE)
        self.driver.execute_script(
            "arguments[0].removeAttribute('hidden'); arguments[0].style.display = 'block';"
            "arguments[0].style.width = '1px'; arguments[0].style.height = '1px'; arguments[0].style.opacity = '0.01';",
            file_input,
        )
        file_input.send_keys(str(path))
        state = self.wait_for_settled(
            {"report": self.IMPORT_REPORT, "error": self.IMPORT_ERROR},
            f"{what}: the import check",
            require_no_skeleton=False,
        )
        return state.branch

    def import_error_text(self) -> str:
        return self.text_of(self.IMPORT_ERROR)

    def import_report_text(self) -> str:
        return self.text_of(self.IMPORT_REPORT)

    def import_name(self) -> str:
        return self.wait_for_element(self.IMPORT_NAME).get_attribute("value") or ""

    def recheck_import(self, what: str) -> None:
        """ "Erneut prüfen" with the name in the field; return once the report is back."""
        self.wait_and_click(self.IMPORT_RECHECK)
        try:
            self.poll(timeout=30).until(
                lambda d: (
                    d.find_elements(*self.IMPORT_REPORT) and not d.find_elements(*self.IMPORT_ERROR)
                )
            )
        except TimeoutException as exc:
            error = self.import_error_text() if self.is_present(self.IMPORT_ERROR) else None
            raise AssertionError(
                f"{what}: the second check brought no report (error: {error!r})"
            ) from exc

    def confirm_import(self, what: str) -> None:
        """ "Importieren"; return once the dialog closed (``onImported`` after the write)."""
        self.wait_and_click(self.IMPORT_CONFIRM)
        try:
            self.wait_for_element_hidden(self.IMPORT_DIALOG, timeout=30)
        except TimeoutException as exc:
            error = self.import_error_text() if self.is_present(self.IMPORT_ERROR) else None
            raise AssertionError(
                f"{what}: the import dialog did not close (error: {error!r})"
            ) from exc

    # ── Watering round: "Regen — übersprungen" (GP-FR-117, WP 9.13) ────

    ROUND_RAIN_SKIPPED = _tid("garden-plan-round-rain-skipped")
    ROUND_RAIN_RESULT = _tid("garden-plan-round-rain-result")
    ROUND_RAIN_BEDS = _tid("garden-plan-round-rain-result-beds")
    ROUND_ERROR = _tid("garden-plan-round-error")

    def write_round_note(self, note: str) -> None:
        """Type the round's note (the hand-over line the rain skip takes over); verified."""
        field = self.wait_for_element_clickable(self.ROUND_SUMMARY)
        self.clear_and_fill(field, note)
        if (field.get_attribute("value") or "") != note:
            raise AssertionError(
                f"the round note should read {note!r}, it reads {field.get_attribute('value')!r}"
            )

    def skip_round_for_rain(self, what: str) -> str:
        """ "Regen — übersprungen" in the open round dialog; the result's bed line once the server answered."""
        self.wait_and_click(self.ROUND_RAIN_SKIPPED)
        state = self.wait_for_settled(
            {"result": self.ROUND_RAIN_RESULT, "error": self.ROUND_ERROR},
            f"{what}: the rain-skipped answer",
            require_no_skeleton=False,
        )
        if state.branch != "result":
            raise AssertionError(
                f"{what}: the round was refused: {self.text_of(self.ROUND_ERROR)!r}"
            )
        return self.text_of(self.ROUND_RAIN_BEDS)

    def rain_result_text(self) -> str:
        return self.text_of(self.ROUND_RAIN_RESULT)

    # ── Bed list: water column (GP-FR-167, WP 9.12) ────────────────────

    BED_LIST_ROWS = (
        By.CSS_SELECTOR,
        "[data-testid='data-table'][data-table-section='bed-list'] [data-testid='data-table-row']",
    )

    def bed_list_cell(self, bed_key: str, column: str, what: str) -> str:
        """The text of *column* in the bed list row of *bed_key* (desktop table); loud when the row is missing."""
        link = _tid(f"bed-list-link-{bed_key}")
        try:
            self.wait_for_element(link)
        except TimeoutException as exc:
            raise AssertionError(f"{what}: the bed list has no row for {bed_key}") from exc

        def _read() -> str | None:
            for row in self.driver.find_elements(*self.BED_LIST_ROWS):
                if row.find_elements(*link):
                    return self.get_row_cell_text(row, column)
            return None

        value = self.retry_on_stale(_read)
        if value is None:
            raise AssertionError(
                f"{what}: the row of {bed_key} left the bed list while it was read"
            )
        return " ".join(value.split())

    def has_bed_list_column(self, column: str) -> bool:
        """Whether the bed list's header carries *column* (``sort-<id>``), read after a row is on screen."""
        self.wait_for_element(self.BED_LIST_ROWS)
        return self.is_present(
            (By.CSS_SELECTOR, f"[data-table-section='bed-list'] [data-testid='sort-{column}']")
        )

    # ── Renderer (WP 9.7) ──────────────────────────────────────────────

    def wait_for_renderer(self, expected: str, what: str, timeout: int = 90) -> str:
        """Wait until the plan surface is drawn by *expected* (``svg`` / ``konva``, ``data-renderer``)."""
        try:
            self.poll(timeout).until(lambda _d: self.current_renderer() == expected)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the plan should be drawn by {expected!r}, it is drawn by {self.current_renderer()!r}"
            ) from exc
        return expected

    def canvas_count(self) -> int:
        """``<canvas>`` elements inside the editor (Konva draws on canvases; the SVG renderer draws none)."""
        editor = self.wait_for_element(self.EDITOR)
        return int(
            self.driver.execute_script(
                "return arguments[0].querySelectorAll('canvas').length;", editor
            )
        )


class BedHeadWave9(BedViewPage):
    """The bed head's wave 9 facts."""

    HEADER_WATER = _tid("bed-header-water-source")
    SITE_FLAGS_BADGE = _tid("bed-site-flags-badge")

    def head_water_source(self) -> str | None:
        """ "Nächste Wasserquelle" of the head, ``None`` without the fact (read after the head is anchored)."""
        self.wait_for_element(self.HEADER)
        return self._fact_text(self.HEADER_WATER)

    def wait_for_site_flags_badge(self, expected: str, what: str) -> str:
        try:
            self.poll().until(lambda _d: self._fact_text(self.SITE_FLAGS_BADGE) == expected)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the head chip should read {expected!r}, it reads {self._fact_text(self.SITE_FLAGS_BADGE)!r}"
            ) from exc
        return expected

    def site_flags_badge(self) -> str | None:
        self.wait_for_element(self.HEADER)
        return self._fact_text(self.SITE_FLAGS_BADGE)


__all__ = ["BedHeadWave9", "PlanExportDialog", "Wave9PlanPage", "read_download_bytes"]
