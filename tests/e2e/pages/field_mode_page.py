"""Page object for field mode of the garden plan (REQ-053 WP 5.1, tested in WP 5.4).

:class:`FieldModePage` - ``/standorte/sites/:key/plan?mode=field``: the bed list, the bed sheet, "Erledigt" and its
dialog, the quick-protocol chips and the undo snackbar (``FieldModeView`` / ``FieldBedSheet``), plus
:func:`set_phone_viewport`, which puts the browser at exactly 390 x 844 CSS px.

Every hook is a ``data-testid`` that exists in ``src/frontend/src/features/gardenPlanner/field/`` - none is guessed.
State-changing helpers read their effect back and fail loudly when it never arrives (`e2e-test-stability` §D);
there is no retry loop and no sleep: a wait is a condition on the page (the sheet's task section, a closed dialog,
a gone row, the snackbar's own appear/disappear stamps).
"""

from __future__ import annotations

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from .base_page import BasePage


def _tid(testid: str) -> tuple[str, str]:
    return (By.CSS_SELECTOR, f"[data-testid='{testid}']")


def _text(element: WebElement) -> str:
    return " ".join((element.get_attribute("textContent") or "").split())


#: Counts every ``click`` the page receives on a button (a tap is a click on a touch device) from the moment it is
#: installed; ``window.__kpTapProbe`` is read back by :meth:`FieldModePage.taps_since_reset`.
_TAP_COUNTER = """
if (!window.__kpTapProbe) {
  window.__kpTapProbe = { count: 0, targets: [] };
  document.addEventListener('click', function (event) {
    var button = event.target && event.target.closest ? event.target.closest('button, [role="button"]') : null;
    if (button && event.isTrusted) {
      window.__kpTapProbe.count += 1;
      window.__kpTapProbe.targets.push(button.getAttribute('data-testid') || button.textContent.trim());
    }
  }, true);
}
window.__kpTapProbe.count = 0;
window.__kpTapProbe.targets = [];
return true;
"""


#: Stamps ``shown`` / ``hidden`` (``performance.now()``) of the first "Rückgängig" button that comes and goes.
_UNDO_LIFETIME_PROBE = """
window.__kpUndoLife = { shown: null, hidden: null };
var check = function () {
  var present = !!document.querySelector("[data-testid='care-undo']");
  var now = performance.now();
  var life = window.__kpUndoLife;
  if (present && life.shown === null) { life.shown = now; }
  if (!present && life.shown !== null && life.hidden === null) { life.hidden = now; }
};
new MutationObserver(check).observe(document.body, { childList: true, subtree: true });
check();
return true;
"""


class FieldModePage(BasePage):
    """Field mode of the garden plan at phone size: bed list, bed sheet, chips, undo."""

    PATH = "/standorte/sites/{key}/plan?mode=field"
    ROOT = _tid("garden-plan-field-mode")
    BED_LIST = _tid("field-bed-list")
    SHEET = _tid("field-bed-sheet")
    TASKS = _tid("field-tasks")
    SNACKBAR_UNDO = _tid("care-undo")
    COMPLETE_DIALOG = _tid("care-complete-dialog")
    COMPLETE_SUBMIT = _tid("care-complete-submit")
    #: Notistack renders the message and the action in one snackbar; the message is the text before the button.
    SNACKBAR = (
        By.CSS_SELECTOR,
        "#notistack-snackbar, .notistack-SnackbarContainer .MuiSnackbarContent-message",
    )

    def open(self, site_key: str) -> FieldModePage:
        """Open the plan of *site_key* in field mode and return once the bed list is on screen."""
        self.navigate(self.PATH.format(key=site_key))
        self.wait_for_content(
            self.ROOT, f"field mode of site {site_key}", require_no_skeleton=False
        )
        self.wait_for_content(self.BED_LIST, f"bed list of site {site_key}")
        return self

    # ── Bed list and sheet ─────────────────────────────────────────────

    def bed_row_keys(self) -> list[str]:
        return [
            (row.get_attribute("data-testid") or "")[len("field-bed-row-") :]
            for row in self.driver.find_elements(By.CSS_SELECTOR, "[data-testid^='field-bed-row-']")
        ]

    def tap_bed(self, bed_key: str) -> None:
        """Tap a bed row; return once its sheet shows the task section (the data arrived)."""
        self.wait_and_click(_tid(f"field-bed-row-{bed_key}"))
        self.wait_for_element(self.SHEET)
        self.wait_for_element(self.TASKS)

    def close_sheet(self) -> None:
        self.wait_and_click(_tid("field-sheet-close"))
        self.wait_for_element_hidden(self.SHEET)

    # ── Taps ───────────────────────────────────────────────────────────

    def start_counting_taps(self) -> None:
        """Count the button clicks from now on (the bed was chosen before this call)."""
        self.driver.execute_script(_TAP_COUNTER)

    def taps_since_reset(self) -> tuple[int, list[str]]:
        probe = self.driver.execute_script("return window.__kpTapProbe;")
        return int(probe["count"]), list(probe["targets"])

    # ── Done ───────────────────────────────────────────────────────────

    def done_button(self, task_key: str) -> WebElement:
        return self.wait_for_element(_tid(f"field-done-{task_key}"))

    def element_size(self, element: WebElement) -> tuple[float, float]:
        """The rendered size of *element* in CSS px."""
        size = self.driver.execute_script(
            "var r = arguments[0].getBoundingClientRect(); return [r.width, r.height];", element
        )
        return float(size[0]), float(size[1])

    def computed_font_px(self, element: WebElement) -> float:
        return float(
            self.driver.execute_script(
                "return parseFloat(getComputedStyle(arguments[0]).fontSize);", element
            )
        )

    def tap_done(self, task_key: str) -> None:
        """First tap: "Erledigt" - opens the short dialog."""
        self.scroll_into_view(self.done_button(task_key))
        self.wait_and_click(_tid(f"field-done-{task_key}"))
        self.wait_for_element(self.COMPLETE_DIALOG)

    def double_tap_done(self, task_key: str) -> None:
        """Two clicks on "Erledigt" inside the 300 ms guard (GP-UX-023): one dialog, never two."""
        button = self.done_button(task_key)
        self.scroll_into_view(button)
        ActionChains(self.driver).move_to_element(button).click().click().perform()
        self.wait_for_element(self.COMPLETE_DIALOG)

    def dialogs_open(self) -> int:
        return len(self.driver.find_elements(*self.COMPLETE_DIALOG))

    def tap_finish(self, what: str) -> None:
        """Second tap: "Fertig" - the dialog closes after the server accepted the completion."""
        self.wait_and_click(self.COMPLETE_SUBMIT)
        try:
            self.wait_for_element_hidden(self.COMPLETE_DIALOG)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the completion dialog did not close after 'Fertig'"
            ) from exc

    def double_tap_finish(self, what: str) -> None:
        """Two clicks on "Fertig" inside the 300 ms guard: one completion, and the dialog closes."""
        button = self.wait_for_element(self.COMPLETE_SUBMIT)
        ActionChains(self.driver).move_to_element(button).click().click().perform()
        try:
            self.wait_for_element_hidden(self.COMPLETE_DIALOG)
        except TimeoutException as exc:
            raise AssertionError(f"{what}: the completion dialog did not close") from exc

    def wait_for_task_gone(self, task_key: str, what: str) -> None:
        try:
            self.wait_for_element_hidden(_tid(f"field-task-{task_key}"))
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: task {task_key} is still listed in the bed sheet"
            ) from exc

    # ── Quick protocol and undo ────────────────────────────────────────

    def tap_chip(self, chip_id: str) -> None:
        self.wait_and_click(_tid(f"field-chip-{chip_id}"))

    def wait_for_undo_offer(self, what: str) -> str:
        """Wait until the snackbar with "Rückgängig" is up; return its message."""
        try:
            self.wait_for_element(self.SNACKBAR_UNDO)
        except TimeoutException as exc:
            raise AssertionError(f"{what}: no 'Rückgängig' snackbar appeared") from exc
        return self.snackbar_text()

    def snackbar_text(self) -> str:
        for candidate in self.driver.find_elements(*self.SNACKBAR):
            text = _text(candidate)
            if text:
                return text
        return ""

    def is_undo_offered(self) -> bool:
        return bool(self.driver.find_elements(*self.SNACKBAR_UNDO))

    def watch_undo_lifetime(self) -> None:
        """Install an in-page observer that stamps when the "Rückgängig" button appears and when it is gone.

        The stamps are ``performance.now()`` values taken by the page itself, so the 8 s of GP-FR-149 is measured
        where it happens, and the test waits for a *state* (the button is gone) instead of for a duration.
        """
        self.driver.execute_script(_UNDO_LIFETIME_PROBE)

    def undo_lifetime_ms(self, what: str) -> float:
        """Wait until the watched snackbar button is gone again; return how long it was on screen."""

        def _life():
            probe = self.driver.execute_script("return window.__kpUndoLife;")
            if probe and probe.get("shown") is not None and probe.get("hidden") is not None:
                return float(probe["hidden"]) - float(probe["shown"])
            return False

        try:
            return self.poll(timeout=20).until(lambda _d: _life())
        except TimeoutException as exc:
            raise AssertionError(f"{what}: the 'Rückgängig' snackbar never went away") from exc

    def tap_undo(self) -> None:
        self.wait_and_click(self.SNACKBAR_UNDO)
        self.wait_for_element_hidden(self.SNACKBAR_UNDO)

    # ── Plants ─────────────────────────────────────────────────────────

    def open_plant_groups(self) -> None:
        """Expand every plant group of the sheet (a plant row exists only in an expanded group)."""
        for toggle in self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid^='field-plant-group-toggle-']"
        ):
            if toggle.get_attribute("aria-expanded") != "true":
                self.scroll_and_click(toggle)
                self.poll().until(lambda _d, t=toggle: t.get_attribute("aria-expanded") == "true")

    def correct_position(self, plant_key: str) -> None:
        """ "Position korrigieren" of one plant; return once its dialog is open."""
        self.wait_and_click(_tid(f"field-plant-correct-{plant_key}"))
        self.wait_for_element(_tid("position-dialog"))

    # ── Sun window chips (GP-FR-158/159, GP-UX-057, WP 7.20) ────────────
    #
    # ``SunWindowFields`` draws each chip as a ``<label>`` whose native radio covers it
    # completely at opacity 0 (``inset: 0``): a tap on the chip lands on that radio. The
    # tap is a real pointer click at the chip's centre, guarded by ``elementFromPoint``
    # resolving to the chip's own radio - not a script click, and not the label's text.

    SUN_SECTION = _tid("field-mode-sun-section")
    SUN_HOURS = _tid("field-mode-sun-profile-hours")

    def sun_chip(self, window: str) -> WebElement:
        return self.wait_for_element(_tid(f"field-mode-sun-profile-window-{window}"))

    def sun_chip_input(self, window: str) -> WebElement:
        return self.wait_for_element(_tid(f"field-mode-sun-profile-window-{window}-input"))

    def checked_sun_window(self) -> str | None:
        """The window whose radio is checked, read from the radios themselves."""
        self.wait_for_element(self.SUN_SECTION)
        checked = [
            radio.get_attribute("value")
            for radio in self.driver.find_elements(
                By.CSS_SELECTOR, "[data-testid='field-mode-sun-section'] input[type='radio']"
            )
            if radio.is_selected()
        ]
        if len(checked) > 1:
            raise AssertionError(f"more than one sun window is checked: {checked}")
        return checked[0] if checked else None

    def sun_chip_sizes(self) -> dict[str, tuple[float, float]]:
        """window -> rendered size (CSS px) of every chip of the section."""
        chips = self.driver.find_elements(
            By.CSS_SELECTOR,
            "[data-testid='field-mode-sun-section'] [data-testid^='field-mode-sun-profile-window-']",
        )
        sizes: dict[str, tuple[float, float]] = {}
        for chip in chips:
            testid = chip.get_attribute("data-testid") or ""
            if testid.endswith("-input"):
                continue
            sizes[testid[len("field-mode-sun-profile-window-") :]] = self.element_size(chip)
        if not sizes:
            raise AssertionError("the sun section shows no chip")
        return sizes

    def tap_sun_chip(self, window: str) -> None:
        """Tap a chip with a real pointer; return once its radio is checked."""
        chip = self.sun_chip(window)
        radio = self.sun_chip_input(window)
        self.scroll_into_view(chip)
        centre = self.driver.execute_script(
            "var r = arguments[0].getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2];",
            chip,
        )
        hit = self.driver.execute_script(
            "return document.elementFromPoint(arguments[0], arguments[1]) === arguments[2];",
            centre[0],
            centre[1],
            radio,
        )
        if not hit:
            raise AssertionError(
                f"the centre {centre} of the chip {window!r} does not hit its radio"
            )
        ActionChains(self.driver).move_to_element(chip).click().perform()
        try:
            self.poll().until(lambda _d: radio.is_selected())
        except TimeoutException as exc:
            raise AssertionError(f"the chip {window!r} is not checked after the tap") from exc

    def sun_hours_text(self) -> str:
        return self.wait_for_element(self.SUN_HOURS).get_attribute("value") or ""

    def enter_sun_hours(self, text: str) -> None:
        """Type the summer sun hours and commit with Enter (the field commits on Enter or blur)."""
        field = self.wait_for_element(self.SUN_HOURS)
        self.scroll_into_view(field)
        field.click()
        field.send_keys(Keys.CONTROL, "a")
        field.send_keys(text)
        if field.get_attribute("value") != text:
            raise AssertionError(
                f"the hours field should hold {text!r}, it holds {field.get_attribute('value')!r}"
            )
        field.send_keys(Keys.ENTER)


def set_phone_viewport(driver: WebDriver, width: int = 390, height: int = 844) -> tuple[int, int]:
    """Resize the browser so the page's *inner* viewport is exactly ``width`` x ``height`` CSS px.

    A window size is the outer size; the difference to ``window.innerWidth`` / ``innerHeight`` (scrollbars, any
    browser chrome) is measured and added, then the result is read back. Raises when the browser would not
    take the size - a "390 px" test that ran at another width would certify nothing.
    """
    driver.set_window_size(width, height)
    inner = driver.execute_script("return [window.innerWidth, window.innerHeight];")
    driver.set_window_size(width + (width - int(inner[0])), height + (height - int(inner[1])))
    inner = driver.execute_script("return [window.innerWidth, window.innerHeight];")
    actual = (int(inner[0]), int(inner[1]))
    if actual != (width, height):
        raise AssertionError(
            f"the browser would not take a {width}x{height} viewport, it has {actual}"
        )
    return actual


__all__ = ["FieldModePage", "set_phone_viewport"]
