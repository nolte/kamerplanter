"""Page objects for the rotation matrix of a site (REQ-053 WP 8.17, GP-FR-135, ``/standorte/sites/:key/rotation-matrix``).

* :class:`RotationMatrixPage` - beds x years (``RotationMatrixPage``): the column years, a cell's family swatches and
  its text, the "Fruchtfolge aus" mark of a bed, the legend, the jump to a bed;
* :class:`BackfillDialog` - "Was stand hier {Jahr}?" (``BackfillDialog``), opened from a past cell.

Every hook is a ``data-testid`` that exists in ``src/frontend/src/features/gardenPlanner/history/`` - none is
guessed. State-changing helpers read their effect back and fail loudly when it never arrives (`e2e-test-stability`
§D); there is no retry loop and no sleep.
"""

from __future__ import annotations

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from .base_page import BasePage


def _tid(testid: str) -> tuple[str, str]:
    return (By.CSS_SELECTOR, f"[data-testid='{testid}']")


def _text(element: WebElement) -> str:
    return " ".join((element.get_attribute("textContent") or "").split())


class RotationMatrixPage(BasePage):
    """The rotation matrix of one site."""

    PATH = "/standorte/sites/{key}/rotation-matrix"
    PAGE = _tid("rotation-matrix-page")
    TABLE = _tid("rotation-matrix-table")
    LEGEND = _tid("matrix-legend")

    def open(self, site_key: str) -> RotationMatrixPage:
        self.navigate(self.PATH.format(key=site_key))
        self.wait_for_content(self.PAGE, f"rotation matrix of site {site_key}")
        try:
            self.wait_for_element(self.TABLE)
        except TimeoutException as exc:
            raise AssertionError(f"the rotation matrix of {site_key} shows no table") from exc
        return self

    def column_years(self) -> list[int]:
        """The year columns of the head row, left to right (the first head cell is "Beet")."""
        heads = self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='rotation-matrix-table'] thead th"
        )
        return [int(_text(head)) for head in heads[1:] if _text(head).isdigit()]

    def _cell(self, bed_key: str, year: int) -> WebElement:
        try:
            return self.wait_for_element(_tid(f"matrix-cell-{bed_key}-{year}"))
        except TimeoutException as exc:
            raise AssertionError(f"the matrix has no cell for bed {bed_key} in {year}") from exc

    def cell_text(self, bed_key: str, year: int) -> str:
        return _text(self._cell(bed_key, year))

    def cell_families(self, bed_key: str, year: int) -> list[str]:
        """The family keys whose swatch the cell shows, in the order listed."""
        cell = self._cell(bed_key, year)
        return [
            (swatch.get_attribute("data-testid") or "")[len("matrix-swatch-") :]
            for swatch in cell.find_elements(By.CSS_SELECTOR, "[data-testid^='matrix-swatch-']")
        ]

    def swatch_pattern(self, bed_key: str, year: int, family_key: str) -> str:
        """The computed ``background-image`` of a family swatch in the cell: the greyscale-safe fill pattern."""
        cell = self._cell(bed_key, year)
        swatches = cell.find_elements(
            By.CSS_SELECTOR, f"[data-testid='matrix-swatch-{family_key}']"
        )
        if not swatches:
            raise AssertionError(f"cell {bed_key}/{year} shows no swatch of {family_key!r}")
        return str(
            self.driver.execute_script(
                "return getComputedStyle(arguments[0]).backgroundImage;", swatches[0]
            )
        )

    def wait_for_cell_family(self, bed_key: str, year: int, family_key: str, what: str) -> None:
        try:
            self.poll().until(lambda _d: family_key in self.cell_families(bed_key, year))
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: cell {bed_key}/{year} should show {family_key!r}; it shows "
                f"{self.cell_families(bed_key, year)} ({self.cell_text(bed_key, year)!r})"
            ) from exc

    def off_mark(self, bed_key: str) -> str | None:
        """The "Fruchtfolge-Prüfung aus" line under a bed's name, or ``None`` when the bed takes part."""
        found = self.driver.find_elements(*_tid(f"matrix-off-{bed_key}"))
        return _text(found[0]) if found else None

    def legend_text(self) -> str:
        try:
            return _text(self.wait_for_element(self.LEGEND))
        except TimeoutException as exc:
            raise AssertionError("the rotation matrix shows no legend") from exc

    def open_backfill(self, bed_key: str, year: int) -> BackfillDialog:
        """Tap the past cell *bed_key*/*year* (a button for a grower); the backfill dialog for that year opens."""
        self.wait_and_click(_tid(f"matrix-cell-button-{bed_key}-{year}"))
        dialog = BackfillDialog(self.driver, self.base_url)
        try:
            dialog.wait_for_element_visible(dialog.DIALOG)
        except TimeoutException as exc:
            raise AssertionError(f"tapping {bed_key}/{year} opened no backfill dialog") from exc
        return dialog

    def jump_to_bed(self, bed_key: str) -> None:
        """Follow the bed's name link; return once the address names the bed and its bed view rendered."""
        self.wait_and_click(_tid(f"matrix-bed-link-{bed_key}"))
        try:
            self.wait_for_url_contains(f"/standorte/locations/{bed_key}")
        except TimeoutException as exc:
            raise AssertionError(f"the bed link did not open the bed view of {bed_key}") from exc
        self.wait_for_content(
            _tid("bed-view"), f"bed view of {bed_key} after the jump", require_no_skeleton=False
        )


class BackfillDialog(BasePage):
    """ "Was stand hier {Jahr}?": year, role, species or family, season."""

    DIALOG = _tid("backfill-dialog")
    SUBMIT = _tid("backfill-submit")

    def title(self) -> str:
        return _text(self.wait_for_element((By.CSS_SELECTOR, "#backfill-title")))

    def choose_family(self, family_key: str) -> None:
        """Pick the family in "Pflanzenfamilie" and read the committed value back.

        The dialog loads the family and the species catalogue together, so the option can arrive after the menu
        opened; the open menu re-renders with it. The wait is on that option (full budget), not on the generic
        3-second option probe of ``select_option_by_value``.
        """
        native = self.wait_for_element(_tid("backfill-family"))
        trigger = self.driver.execute_script(
            "return arguments[0].closest('.MuiInputBase-root').querySelector(\"[role='combobox']\");",
            native,
        )
        if trigger is None:
            raise AssertionError("the family select has no combobox")
        self.scroll_into_view(trigger)
        self.dispatch_menu_trigger_open(trigger)
        option_locator = (By.CSS_SELECTOR, f"li[role='option'][data-value='{family_key}']")
        try:
            option = self.wait_for_element_visible(option_locator)
        except TimeoutException as exc:
            raise AssertionError(f"'Pflanzenfamilie' offers no family {family_key!r}") from exc
        self.click_menu_option(option)
        self.close_mui_dropdown()
        try:
            self.poll().until(lambda _d: native.get_attribute("value") == family_key)
        except TimeoutException as exc:
            raise AssertionError(
                f"picking {family_key!r} did not commit; 'Pflanzenfamilie' reads {native.get_attribute('value')!r}"
            ) from exc

    def submit_and_wait_closed(self, what: str) -> None:
        self.wait_and_click(self.SUBMIT)
        try:
            self.wait_for_element_hidden(self.DIALOG)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the backfill dialog did not close after 'Speichern'"
            ) from exc


__all__ = ["BackfillDialog", "RotationMatrixPage"]
