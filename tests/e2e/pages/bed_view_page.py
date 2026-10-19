"""Page objects for the bed view (REQ-053 WP 3.5-3.7, ``/standorte/locations/:key#<tab>``).

The bed view is the location page of a bed: its head (``BedHeader``) and the
tabs Plan, Bepflanzung, Pflege, Boden, Historie, Details (``BedView``). Three
component objects sit on top of it, one per surface wave 3 drives:

* :class:`PlantingDialog` - "Bepflanzen" (``PlantingDialog`` / ``EntryCard`` /
  ``HintsPanel`` / ``LayoutCanvas``);
* :class:`PositionDialog` - "Position korrigieren" (``PositionCorrectionDialog``);
* the plan tab's plant markers, the hover bubble and the legend live on
  :class:`BedViewPage` itself, next to the network probe that proves the bubble
  needs no request (GP-FR-191).

Every hook used here is a ``data-testid`` (or the renderer's ``data-plan-*``
attributes) that exists in ``src/frontend/src/features/gardenPlanner/`` - none
is guessed. State-changing helpers read their effect back and fail loudly when
it never arrives (`e2e-test-stability` §D); there is no retry loop anywhere.

COORDINATES
-----------
Both canvases draw in model metres with y negated (SVG y grows downward). A
model point goes to the screen through the SVG's own ``getScreenCTM()`` - the
browser's real rendering transform - so a pointer gesture aims where the user
would aim, independently of how the component maps back.
"""

from __future__ import annotations

import re

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.mouse_button import MouseButton
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import DEFAULT_TIMEOUT, BasePage
from .garden_plan_page import ScreenPoint


def _tid(testid: str) -> tuple[str, str]:
    return (By.CSS_SELECTOR, f"[data-testid='{testid}']")


#: Model point -> CSS viewport pixels through the SVG's rendering transform.
_TO_SCREEN = (
    "var svg = arguments[0]; var p = svg.createSVGPoint();"
    "p.x = arguments[1]; p.y = -arguments[2];"
    "var q = p.matrixTransform(svg.getScreenCTM()); return [q.x, q.y];"
)

#: What the element at a viewport point belongs to: the nearest ``data-plan-key``
#: / ``data-testid`` ancestor, and the element stack for a loud miss.
_HIT = (
    "var x = arguments[0], y = arguments[1];"
    "var el = document.elementFromPoint(x, y);"
    "if (!el) { return {key: null, testid: null, stack: []}; }"
    "var obj = el.closest('[data-plan-key]'); var tid = el.closest('[data-testid]');"
    "var stack = document.elementsFromPoint(x, y).slice(0, 6).map(function (e) {"
    "  return e.tagName + (e.getAttribute('data-testid') ? '[' + e.getAttribute('data-testid')"
    "  + ']' : '') + (e.getAttribute('data-plan-key') ? '{' + e.getAttribute('data-plan-key')"
    "  + '}' : ''); });"
    "return {key: obj ? obj.getAttribute('data-plan-key') : null,"
    " testid: tid ? tid.getAttribute('data-testid') : null, stack: stack};"
)

#: Installs (or resets) the request probe. Records at request **start** - every
#: ``XMLHttpRequest.send`` and ``fetch`` - plus every resource the browser
#: loads (a lazily imported chunk, an image) via a ``PerformanceObserver``.
_NET_PROBE_INSTALL = """
if (!window.__kpNetProbe) {
  var log = [];
  var open = XMLHttpRequest.prototype.open, send = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open = function (method, url) {
    this.__kpUrl = String(url); return open.apply(this, arguments);
  };
  XMLHttpRequest.prototype.send = function () {
    log.push('xhr ' + this.__kpUrl); return send.apply(this, arguments);
  };
  var fetchImpl = window.fetch;
  window.fetch = function (input) {
    log.push('fetch ' + (typeof input === 'string' ? input : (input && input.url)));
    return fetchImpl.apply(this, arguments);
  };
  new PerformanceObserver(function (list) {
    list.getEntries().forEach(function (e) { log.push('resource ' + e.name); });
  }).observe({type: 'resource', buffered: false});
  window.__kpNetProbe = {log: log};
}
window.__kpNetProbe.log.length = 0;
return true;
"""

#: The probe's positive control: one XHR and one fetch to a marker URL. Both
#: must show up, or the probe is blind and "no request" would prove nothing.
_NET_PROBE_CONTROL = """
var x = new XMLHttpRequest(); x.open('GET', '/__kp_net_probe_control'); x.send();
window.fetch('/__kp_net_probe_control').catch(function () {});
return true;
"""

#: Requests that are not the page's business and run on their own clock: the
#: notification bell's 60 s poll, the token refresh, and the probe's control.
_NET_BACKGROUND = ("/notifications", "/auth/", "__kp_net_probe_control")


class BedViewPage(BasePage):
    """One bed: head, tabs, the planting list, the plan tab, the history list."""

    PATH = "/standorte/locations/{key}"

    BED_VIEW = _tid("bed-view")
    ROTATION_BADGE = _tid("bed-rotation-badge")

    # ── Planting tab (WP 3.6) ──────────────────────────────────────────
    PLANTING_TAB = _tid("bed-planting-tab")
    PLANT_BUTTON = _tid("bed-plant-button")
    PLANNED_LIST = _tid("bed-planting-planned")
    ACTIVE_LIST = _tid("bed-planting-active")

    # ── Plan tab (WP 3.5 / 3.7) ────────────────────────────────────────
    PLAN_TAB = _tid("bed-plan-tab")
    PLAN_CANVAS = _tid("bed-plan-canvas")
    PLAN_LINK = _tid("bed-plan-open-garden")
    POPOVER = _tid("plant-info-popover")
    LEGEND = _tid("plant-state-legend")
    #: The bubble's element id; a marker points at it with ``aria-describedby``.
    PLANT_INFO_ID = "gp-plant-info"

    # ── History tab (WP 4.5) ───────────────────────────────────────────
    HISTORY_TAB = _tid("bed-history-tab")
    HISTORY_LIST = _tid("history-list")
    HISTORY_CORRECTIONS = _tid("history-corrections")

    #: The tab is part of the URL hash (``useTabUrl``).
    TAB_CONTENT = {
        "plan": PLAN_TAB,
        "planting": PLANTING_TAB,
        "history": HISTORY_TAB,
    }

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    # ── Navigation ─────────────────────────────────────────────────────

    def open(self, bed_key: str, tab: str) -> BedViewPage:
        """Open the bed view on *tab* and return once that tab's content settled.

        The summary decides whether the location page becomes a bed view, so
        the plain location page or an error surface is a failure here, named.

        Always a full document load, so the tab reads what the server holds
        *now*: a ``get`` that differs from the current URL only in the hash is a
        same-document navigation and would keep the data loaded before. A marker
        on ``window`` tells the two apart; a surviving marker forces a reload.
        """
        if tab not in self.TAB_CONTENT:
            raise AssertionError(f"open(): no settle locator for tab {tab!r}")
        self.driver.execute_script("window.__kpBedViewDocument = true;")
        self.navigate(f"{self.PATH.format(key=bed_key)}#{tab}")
        if self.driver.execute_script("return window.__kpBedViewDocument === true;"):
            self.driver.refresh()
        self.wait_for_content(self.BED_VIEW, f"bed view of {bed_key}", require_no_skeleton=False)
        self.wait_for_content(self.TAB_CONTENT[tab], f"tab {tab!r} of bed {bed_key}")
        return self

    # ── Head ───────────────────────────────────────────────────────────

    def wait_for_rotation_badge(self, what: str) -> str:
        try:
            badge = self.wait_for_element(self.ROTATION_BADGE)
        except TimeoutException as exc:
            raise AssertionError(f"{what}: the bed head carries no rotation badge") from exc
        return " ".join((badge.get_attribute("textContent") or "").split())

    # ── Planting tab ───────────────────────────────────────────────────

    def open_planting_dialog(self) -> PlantingDialog:
        self.wait_and_click(self.PLANT_BUTTON)
        dialog = PlantingDialog(self.driver, self.base_url)
        dialog.wait_until_ready()
        return dialog

    def planned_slot_keys(self) -> list[str]:
        """Slot keys of the "Geplant" list, in the order shown (empty when the list is absent)."""
        return self._row_keys("planting-planned-")

    def active_plant_keys(self) -> list[str]:
        """Plant keys of the "Im Beet" list, in the order shown (empty when the list is absent)."""
        return self._row_keys("planting-active-")

    def _row_keys(self, prefix: str) -> list[str]:
        self.wait_for_element(self.PLANTING_TAB)
        return [
            (el.get_attribute("data-testid") or "")[len(prefix) :]
            for el in self.driver.find_elements(By.CSS_SELECTOR, f"[data-testid^='{prefix}']")
        ]

    def planned_row_text(self, slot_key: str) -> str:
        row = self.wait_for_element(_tid(f"planting-planned-{slot_key}"))
        return " ".join((row.get_attribute("textContent") or "").split())

    def wait_for_planting_lists(self, planned: int, active: int, what: str) -> None:
        """Wait until the planting tab lists *planned* planned positions and *active* plants."""

        def _counts() -> tuple[int, int]:
            return len(self.planned_slot_keys()), len(self.active_plant_keys())

        try:
            self.poll().until(lambda _d: _counts() == (planned, active))
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: expected {planned} planned position(s) and {active} plant(s), the "
                f"planting tab lists {_counts()}"
            ) from exc

    def open_position_dialog(self, plant_key: str) -> PositionDialog:
        """Click "Position korrigieren" of *plant_key*; the caller reads which branch loaded."""
        self.wait_and_click(_tid(f"planting-correct-{plant_key}"))
        dialog = PositionDialog(self.driver, self.base_url)
        dialog.wait_for_element(dialog.DIALOG)
        return dialog

    # ── Plan tab: markers ──────────────────────────────────────────────

    def marker_locator(self, plant_key: str) -> tuple[str, str]:
        return (
            By.CSS_SELECTOR,
            f"[data-testid='bed-plan-canvas'] [data-plan-key='{plant_key}'][role='button']",
        )

    def wait_for_marker(self, plant_key: str):
        return self.wait_for_element(self.marker_locator(plant_key))

    def plant_marker_keys(self) -> list[str]:
        self.wait_for_element(self.PLAN_CANVAS)
        return [
            el.get_attribute("data-plan-key") or ""
            for el in self.driver.find_elements(
                By.CSS_SELECTOR,
                "[data-testid='bed-plan-canvas'] [data-plan-kind='plant'][role='button']",
            )
        ]

    def tab_stop_plant(self) -> str:
        """The plant marker that is the canvas' one tab stop (roving tabindex, GP-NFR-068)."""
        self.wait_for_element(self.PLAN_CANVAS)
        stops = self.driver.find_elements(
            By.CSS_SELECTOR,
            "[data-testid='bed-plan-canvas'] [data-plan-kind='plant'][role='button'][tabindex='0']",
        )
        if len(stops) != 1:
            raise AssertionError(
                f"the bed plan must have exactly one plant tab stop, has {len(stops)}"
            )
        return stops[0].get_attribute("data-plan-key") or ""

    def marker_aria_label(self, plant_key: str) -> str:
        return self.wait_for_marker(plant_key).get_attribute("aria-label") or ""

    def marker_described_by(self, plant_key: str) -> str | None:
        return self.wait_for_marker(plant_key).get_attribute("aria-describedby")

    def marker_lifecycle(self, plant_key: str) -> str | None:
        """The ring style the marker draws (``data-plan-lifecycle``), ``None`` for a plain marker."""
        node = self.wait_for_marker(plant_key)
        shapes = node.find_elements(By.CSS_SELECTOR, ".gp-shape[data-plan-lifecycle]")
        return shapes[0].get_attribute("data-plan-lifecycle") if shapes else None

    def marker_badges(self, plant_key: str) -> list[str]:
        """The attention badges drawn on the marker (``data-plan-badge-reason``)."""
        node = self.wait_for_marker(plant_key)
        return [
            el.get_attribute("data-plan-badge-reason") or ""
            for el in node.find_elements(By.CSS_SELECTOR, "[data-plan-badge-reason]")
        ]

    def wait_for_plant_states(self, plant_key: str, what: str) -> None:
        """Wait until the marker draws its state - the ``plant-states`` answer arrived."""
        try:
            self.poll().until(lambda _d: self.marker_lifecycle(plant_key) is not None)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: plant {plant_key!r} is still drawn without its state (no "
                "data-plan-lifecycle): the plant-states request never answered"
            ) from exc
        self.wait_for_element(self.LEGEND)

    def marker_centre(self, plant_key: str) -> ScreenPoint:
        box = self.driver.execute_script(
            "var s = arguments[0].querySelector('.gp-shape');"
            "if (!s) { return null; } var r = s.getBoundingClientRect();"
            "return [r.left + r.width / 2, r.top + r.height / 2];",
            self.wait_for_marker(plant_key),
        )
        if not box:
            raise AssertionError(f"plant marker {plant_key!r} has no drawn shape (.gp-shape)")
        return ScreenPoint(float(box[0]), float(box[1]))

    def _require_hit(self, point: ScreenPoint, key: str, what: str) -> None:
        """The `elementFromPoint` guard: the point must resolve to plant *key*, else loud."""
        found = self.driver.execute_script(_HIT, point.x, point.y)
        if found["key"] != key:
            raise AssertionError(
                f"{what}: the point ({point.x:.1f}, {point.y:.1f}) does not hit plant {key!r}; "
                f"elementFromPoint resolves to key={found['key']!r}, testid={found['testid']!r}, "
                f"stack={found['stack']}"
            )

    def move_pointer_to(self, point: ScreenPoint) -> None:
        """A trusted mouse move to *point* (W3C pointer actions, ``pointerType`` mouse)."""
        builder = ActionBuilder(self.driver, duration=50)
        builder.pointer_action.move_to_location(round(point.x), round(point.y))
        builder.perform()

    def hover_plant(self, plant_key: str) -> None:
        """Rest the mouse on the plant's marker (the bubble's 300 ms dwell runs in the app)."""
        self.scroll_into_view(self.wait_for_element(self.PLAN_CANVAS))
        point = self.marker_centre(plant_key)
        self._require_hit(point, plant_key, f"hovering plant {plant_key!r}")
        self.move_pointer_to(point)

    def move_pointer_into_bubble(self) -> None:
        box = self.driver.execute_script(
            "var r = arguments[0].getBoundingClientRect();"
            "return [r.left + r.width / 2, r.top + r.height / 2];",
            self.wait_for_element(self.POPOVER),
        )
        point = ScreenPoint(float(box[0]), float(box[1]))
        hit = self.driver.execute_script(
            "var el = document.elementFromPoint(arguments[0], arguments[1]);"
            "return !!(el && el.closest(\"[data-testid='plant-info-popover']\"));",
            point.x,
            point.y,
        )
        if not hit:
            raise AssertionError(f"the bubble's centre {point} is covered by another element")
        self.move_pointer_to(point)

    def focus_before_canvas(self) -> None:
        """Put the keyboard focus on the control just before the plan (the "garden plan" link).

        ``focus()`` is the precondition of a keyboard flow, not the action under
        test; verified, because a focus that did not land would send the Tab to
        ``<body>``.
        """
        link = self.wait_for_element(self.PLAN_LINK)
        self.driver.execute_script("arguments[0].focus();", link)
        if not self.driver.execute_script("return document.activeElement === arguments[0];", link):
            raise AssertionError("the garden-plan link did not take the keyboard focus")

    def tab_to_plant(self, max_presses: int = 6) -> str:
        """Tab forward until a plant marker has the focus; return its key (bounded, loud)."""
        for _ in range(max_presses):
            self.press(Keys.TAB)
            key = self.driver.execute_script(
                "var a = document.activeElement;"
                "return a && a.getAttribute && a.getAttribute('data-plan-kind') === 'plant'"
                " ? a.getAttribute('data-plan-key') : null;"
            )
            if key:
                return key
        raise AssertionError(f"Tab never reached a plant marker within {max_presses} presses")

    def press(self, *keys: str) -> None:
        chain = ActionChains(self.driver)
        for key in keys:
            chain.send_keys(key)
        chain.perform()

    # ── Plan tab: the info bubble ──────────────────────────────────────

    def is_bubble_shown(self) -> bool:
        bubbles = self.driver.find_elements(*self.POPOVER)
        return bool(bubbles) and bubbles[0].value_of_css_property("visibility") != "hidden"

    def wait_for_bubble(self, plant_key: str, what: str) -> str:
        """Wait until the bubble is shown **for** *plant_key*; return its text.

        "For" is read from the marker's ``aria-describedby``: the renderer points
        exactly the plant whose bubble is open at the bubble (GP-UX-058).
        """
        try:
            self.poll().until(
                lambda _d: (
                    self.is_bubble_shown()
                    and self.marker_described_by(plant_key) == self.PLANT_INFO_ID
                )
            )
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: no info bubble for plant {plant_key!r} (bubble shown: "
                f"{self.is_bubble_shown()}, aria-describedby="
                f"{self.marker_described_by(plant_key)!r})"
            ) from exc
        return self.bubble_text()

    def wait_for_bubble_gone(self, what: str) -> None:
        try:
            self.poll().until(lambda _d: not self.driver.find_elements(*self.POPOVER))
        except TimeoutException as exc:
            raise AssertionError(f"{what}: the info bubble is still open") from exc

    def bubble_text(self) -> str:
        content = self.wait_for_element(_tid("plant-info-content"))
        return " ".join((content.get_attribute("textContent") or "").split())

    def bubble_lines(self) -> dict[str, str]:
        """The bubble's lines by their ``data-line`` key (``phase``, ``age``, ``attention-overdue`` ...)."""
        content = self.wait_for_element(_tid("plant-info-content"))
        return {
            el.get_attribute("data-line") or "": " ".join(
                (el.get_attribute("textContent") or "").split()
            )
            for el in content.find_elements(By.CSS_SELECTOR, "[data-line]")
        }

    def bubble_survives(self, window_ms: int) -> bool:
        """Whether the bubble is still in the DOM, unremoved, after *window_ms* (in-page observation).

        A *negative* property - "it does not close" - can only be observed over
        a window; this is that window, not a wait for a state change. The
        ``MutationObserver`` records any removal of the bubble during it, so a
        bubble that closes and reopens within the window still counts as closed.
        """
        return bool(
            self.driver.execute_async_script(
                "var done = arguments[arguments.length - 1], ms = arguments[0];"
                "var removed = false;"
                "var obs = new MutationObserver(function () {"
                "  if (!document.querySelector(\"[data-testid='plant-info-popover']\")) removed = true;"
                "});"
                "obs.observe(document.body, {childList: true, subtree: true});"
                "setTimeout(function () { obs.disconnect();"
                "  done(!removed && !!document.querySelector(\"[data-testid='plant-info-popover']\"));"
                "}, ms);",
                window_ms,
            )
        )

    # ── Plan tab: the legend ───────────────────────────────────────────

    def open_legend(self) -> None:
        legend = self.wait_for_element(self.LEGEND)
        if legend.get_attribute("open") is not None:
            raise AssertionError("the plant-state legend is already open")
        summary = legend.find_element(By.CSS_SELECTOR, "summary")
        self.scroll_and_click(summary)
        self.poll().until(lambda _d: legend.get_attribute("open") is not None)

    def legend_rows(self) -> list[dict]:
        """Per legend row: its text and the non-colour channels of the drawn sample.

        ``dash`` (ring dash pattern), ``rings`` (circles drawn), ``cross`` (a
        path through the disc) for a ring row; ``shape`` for a badge row.
        """
        return self.driver.execute_script(
            "return Array.from(arguments[0].querySelectorAll('li')).map(function (li) {"
            "  var shape = li.querySelector('.gp-shape');"
            "  var badge = li.querySelector('[data-plan-badge-shape]');"
            "  return {text: li.textContent.trim(),"
            "    lifecycle: shape ? shape.getAttribute('data-plan-lifecycle') : null,"
            "    dash: shape ? (shape.getAttribute('stroke-dasharray') || '') : null,"
            "    rings: li.querySelectorAll('svg circle').length,"
            "    cross: shape ? li.querySelectorAll('svg > path').length : 0,"
            "    shape: badge ? badge.getAttribute('data-plan-badge-shape') : null};"
            "});",
            self.wait_for_element(self.LEGEND),
        )

    # ── Network probe (GP-FR-191) ──────────────────────────────────────

    def start_network_probe(self) -> None:
        """Install the request probe, prove it sees an XHR and a fetch, then empty it."""
        self.driver.execute_script(_NET_PROBE_INSTALL)
        self.driver.execute_script(_NET_PROBE_CONTROL)
        try:
            self.poll().until(
                lambda d: (
                    {
                        entry.split(" ", 1)[0]
                        for entry in d.execute_script("return window.__kpNetProbe.log.slice();")
                        if "__kp_net_probe_control" in entry
                    }
                    >= {"xhr", "fetch"}
                )
            )
        except TimeoutException as exc:
            raise AssertionError(
                "the network probe did not record its own control XHR and fetch; it would "
                "report 'no request' for any page"
            ) from exc
        self.driver.execute_script("window.__kpNetProbe.log.length = 0; return true;")

    def requests_since_probe(self) -> list[str]:
        """Requests the page made since the probe was (re)set, without the background ones."""
        log = self.driver.execute_script("return window.__kpNetProbe.log.slice();")
        return [entry for entry in log if not any(skip in entry for skip in _NET_BACKGROUND)]

    # ── History tab ────────────────────────────────────────────────────

    def show_corrections(self) -> None:
        switch = self.wait_for_element(self.HISTORY_CORRECTIONS)
        if switch.is_selected():
            raise AssertionError("'Korrekturen anzeigen' is already on")
        self.driver.execute_script("arguments[0].focus();", switch)
        self.press(Keys.SPACE)
        self.poll().until(lambda _d: switch.is_selected())

    def wait_for_history_entry(self, fragment: str, what: str) -> str:
        """Wait until a history entry contains *fragment*; return that entry's text."""

        def _entries() -> list[str]:
            return [
                " ".join((el.get_attribute("textContent") or "").split())
                for el in self.driver.find_elements(
                    By.CSS_SELECTOR, "[data-testid='history-list'] [data-testid^='history-item-']"
                )
            ]

        try:
            self.poll().until(lambda _d: any(fragment in entry for entry in _entries()))
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: no history entry contains {fragment!r}; entries: {_entries()}"
            ) from exc
        return next(entry for entry in _entries() if fragment in entry)


class PlantingDialog(BasePage):
    """The "Bepflanzen" dialog of one bed; entry *n* is ``planting-entry-<n>`` (0-based)."""

    DIALOG = _tid("planting-dialog")
    HINTS = _tid("planting-hints")
    OVERRIDE_CHECK = _tid("planting-override-check")
    OVERRIDE_REASON = _tid("planting-override-reason")
    SUBMIT = _tid("planting-submit")
    CANVAS = _tid("planting-canvas")
    OPTIONS = (By.CSS_SELECTOR, "li[role='option']")

    def wait_until_ready(self) -> None:
        """The dialog is open and its species catalogue arrived (the first entry is shown)."""
        self.wait_for_element(self.DIALOG)
        self.wait_for_element(_tid("planting-entry-0"))

    def _entry(self, index: int, part: str) -> tuple[str, str]:
        return _tid(f"planting-entry-{index}-{part}")

    # ── Species ────────────────────────────────────────────────────────

    def choose_species(self, scientific_name: str, index: int = 0) -> str:
        """Type the scientific name into the species picker and pick its option; return the label.

        The option is the one whose label ends in ``(<scientific name>)`` -
        exactly that species, not a variety that shares the prefix. The committed
        input value is read back.
        """
        field = self.wait_for_element(
            (By.CSS_SELECTOR, f"[data-testid='planting-entry-{index}-species'] input")
        )
        self.clear_and_fill(field, scientific_name)
        suffix = f"({scientific_name})"

        def _option():
            for option in self.driver.find_elements(*self.OPTIONS):
                text = " ".join((option.get_attribute("textContent") or "").split())
                if text.endswith(suffix):
                    return option
            return False

        try:
            option = self.poll().until(lambda _d: _option())
        except TimeoutException as exc:
            rendered = [
                o.get_attribute("textContent") for o in self.driver.find_elements(*self.OPTIONS)
            ]
            raise AssertionError(
                f"the species picker offers no option for {scientific_name!r}; options: {rendered}"
            ) from exc
        label = " ".join((option.get_attribute("textContent") or "").split())
        self.click_menu_option(option)
        self.poll().until(lambda _d: (field.get_attribute("value") or "") == label)
        return label

    # ── Count, layout, spacings ────────────────────────────────────────

    def set_count(self, count: int, index: int = 0) -> None:
        toggle = self.wait_for_element_clickable(self._entry(index, "count-number"))
        if toggle.get_attribute("aria-pressed") != "true":
            self.scroll_and_click(toggle)
            self.poll().until(lambda _d: toggle.get_attribute("aria-pressed") == "true")
        self._fill(self._entry(index, "count"), str(count))

    def choose_layout(self, value: str, index: int = 0) -> None:
        """Pick a layout (``rows`` ...) in the entry's "Anordnung" select; verified."""
        native = self.wait_for_element(self._entry(index, "layout"))
        if native.get_attribute("value") == value:
            return
        trigger = self.driver.execute_script(
            "return arguments[0].closest('.MuiInputBase-root').querySelector(\"[role='combobox']\");",
            native,
        )
        if trigger is None:
            raise AssertionError(f"the layout select of entry {index} has no combobox")
        self.dispatch_menu_trigger_open(trigger)
        self._settle_listbox()
        self.select_option_by_value(value)
        self.poll().until(lambda _d: native.get_attribute("value") == value)

    def set_spacing(self, cm: float, index: int = 0) -> None:
        self._fill(self._entry(index, "spacing"), f"{cm:g}")

    def set_row_spacing(self, cm: float, index: int = 0) -> None:
        self._fill(self._entry(index, "row-spacing"), f"{cm:g}")

    def _fill(self, locator: tuple[str, str], value: str) -> None:
        element = self.wait_for_element_clickable(locator)
        self.clear_and_fill(element, value)
        self.poll().until(lambda _d: (element.get_attribute("value") or "") == value)

    def field_label(self, part: str, index: int = 0) -> str:
        """The visible label of an entry field (``spacing``, ``row-spacing``)."""
        native = self.wait_for_element(self._entry(index, part))
        return self.driver.execute_script(
            "var root = arguments[0].closest('.MuiFormControl-root');"
            "var label = root ? root.querySelector('label') : null;"
            "return label ? label.textContent.replace(/[\\s*]+$/, '').trim() : '';",
            native,
        )

    # ── Preview ────────────────────────────────────────────────────────

    def result_text(self, index: int = 0) -> str:
        found = self.driver.find_elements(*self._entry(index, "result"))
        return " ".join((found[0].get_attribute("textContent") or "").split()) if found else ""

    def wait_for_server_preview(self, count: int, what: str, index: int = 0) -> int:
        """Wait until the server confirmed a preview of *count* plants; return "at most N fit".

        The local port answers first and the line then reads "… · wird geprüft";
        only the server's answer drops that suffix, so the exact line is the
        state anchor for "the preview the server is authoritative for".
        """
        pattern = re.compile(rf"^{count} Pflanzen, höchstens (\d+) passen$")
        try:
            self.poll().until(lambda _d: pattern.match(self.result_text(index)))
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the preview never settled on {count} server-confirmed plants; it "
                f"reads {self.result_text(index)!r}"
            ) from exc
        match = pattern.match(self.result_text(index))
        assert match is not None
        return int(match.group(1))

    def preview_positions(self, layer: str = "e1") -> list[tuple[float, float]]:
        """The positions the preview draws for entry layer *layer*, bed frame (metres, y up)."""
        points = self.driver.execute_script(
            'return Array.from(arguments[0].querySelectorAll("g[data-layer=\'" + arguments[1]'
            ' + "\'] > g")).map(function (g) {'
            "  var c = g.querySelector('circle'); if (!c) { return null; }"
            "  return [parseFloat(c.getAttribute('cx')), -parseFloat(c.getAttribute('cy'))];"
            "});",
            self.wait_for_element(self.CANVAS),
            layer,
        )
        if any(point is None for point in points):
            raise AssertionError(f"a preview position of layer {layer!r} draws no circle: {points}")
        return [(round(x, 3), round(y, 3)) for x, y in points]

    # ── Hints and "Trotzdem pflanzen" ──────────────────────────────────

    def wait_for_hint(self, species_key: str, what: str) -> tuple[str, str]:
        """Wait for the rotation hint of *species_key*; return ``(severity class, text)``."""
        locator = _tid(f"planting-hint-{species_key}")
        try:
            hint = self.wait_for_element(locator)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: no crop-rotation hint for species {species_key!r}"
            ) from exc
        classes = hint.get_attribute("class") or ""
        match = re.search(r"MuiAlert-color(\w+)", classes)
        return (
            match.group(1).lower() if match else "",
            " ".join((hint.get_attribute("textContent") or "").split()),
        )

    def hints_precede_layout(self, index: int = 0) -> bool:
        """Whether the hints section comes before the entry's layout field in reading order."""
        return bool(
            self.driver.execute_script(
                "return !!(arguments[0].compareDocumentPosition(arguments[1])"
                " & Node.DOCUMENT_POSITION_FOLLOWING);",
                self.wait_for_element(self.HINTS),
                self.wait_for_element(self._entry(index, "layout")),
            )
        )

    def check_plant_anyway(self) -> None:
        box = self.wait_for_element(self.OVERRIDE_CHECK)
        if box.is_selected():
            raise AssertionError("'Trotzdem pflanzen' is already checked")
        self.driver.execute_script("arguments[0].focus();", box)
        ActionChains(self.driver).send_keys(Keys.SPACE).perform()
        self.poll().until(lambda _d: box.is_selected())
        self.wait_for_element(self.OVERRIDE_REASON)

    def set_reason(self, text: str) -> None:
        self._fill(self.OVERRIDE_REASON, text)

    def reason_helper_text(self) -> str:
        reason = self.wait_for_element(self.OVERRIDE_REASON)
        return self.driver.execute_script(
            "var root = arguments[0].closest('.MuiFormControl-root');"
            "var help = root ? root.querySelector('.MuiFormHelperText-root') : null;"
            "return help ? help.textContent.trim() : '';",
            reason,
        )

    def reason_is_invalid(self) -> bool:
        reason = self.wait_for_element(self.OVERRIDE_REASON)
        return reason.get_attribute("aria-invalid") == "true"

    # ── Submit ─────────────────────────────────────────────────────────

    def submit_button_text(self) -> str:
        return " ".join(
            (self.wait_for_element(self.SUBMIT).get_attribute("textContent") or "").split()
        )

    def click_submit(self) -> None:
        """Click the submit button once it is enabled (the hint checks have answered)."""
        button = self.wait_for_element(self.SUBMIT)
        try:
            self.poll().until(lambda _d: button.is_enabled())
        except TimeoutException as exc:
            raise AssertionError(
                "the planting dialog's submit button never became enabled (hint checks pending?)"
            ) from exc
        self.click_coordinate_free(button)

    def submit_and_wait_closed(self, what: str) -> None:
        """Submit and return once the dialog closed - it closes only on a fulfilled submit."""
        self.click_submit()
        try:
            self.wait_for_element_hidden(self.DIALOG)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the planting dialog did not close after submitting; it shows "
                f"{' '.join((self.wait_for_element(self.DIALOG).get_attribute('textContent') or '').split())[:400]!r}"
            ) from exc

    def is_open(self) -> bool:
        return bool(self.driver.find_elements(*self.DIALOG))


class PositionDialog(BasePage):
    """ "Position korrigieren" for one plant: canvas, stepper, the two cm fields, save."""

    DIALOG = _tid("position-dialog")
    CANVAS = _tid("position-canvas")
    MARKER = _tid("position-canvas-point-0")
    X = _tid("position-x")
    Y = _tid("position-y")
    SAVE = _tid("position-save")
    ZONE_NOTE = _tid("position-zone-note")

    def wait_until_loaded(self) -> str:
        """Wait until the dialog shows the plant's position or the zone note; return which."""
        state = self.wait_for_settled(
            {"position": self.X, "zone": self.ZONE_NOTE},
            "position dialog",
            require_no_skeleton=False,
        )
        return state.branch

    def fields_cm(self) -> tuple[float, float]:
        def read(locator: tuple[str, str]) -> float:
            raw = self.wait_for_element(locator).get_attribute("value") or ""
            try:
                return float(raw.replace(",", "."))
            except ValueError as exc:
                raise AssertionError(f"position field holds no number: {raw!r}") from exc

        return read(self.X), read(self.Y)

    def wait_for_fields(self, expected: tuple[float, float], what: str, tolerance: float = 1e-6):
        try:
            self.poll().until(
                lambda _d: all(abs(a - b) <= tolerance for a, b in zip(self.fields_cm(), expected))
            )
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the position fields should read {expected} cm (±{tolerance}), they read "
                f"{self.fields_cm()}"
            ) from exc

    def drag_marker_to(self, x_m: float, y_m: float) -> None:
        """Drag the plant marker to the bed-frame point (*x_m*, *y_m*) with real pointer input."""
        svg = self.wait_for_element(self.CANVAS)
        self.scroll_into_view(svg)
        start_box = self.driver.execute_script(
            "var r = arguments[0].getBoundingClientRect();"
            "return [r.left + r.width / 2, r.top + r.height / 2];",
            self.wait_for_element(self.MARKER),
        )
        start = ScreenPoint(float(start_box[0]), float(start_box[1]))
        hit = self.driver.execute_script(
            "var el = document.elementFromPoint(arguments[0], arguments[1]);"
            "return el ? el.getAttribute('data-testid') : null;",
            start.x,
            start.y,
        )
        if hit != "position-canvas-point-0":
            raise AssertionError(f"the marker's centre {start} hits {hit!r}, not the marker")
        end_xy = self.driver.execute_script(_TO_SCREEN, svg, x_m, y_m)
        end = ScreenPoint(float(end_xy[0]), float(end_xy[1]))
        builder = ActionBuilder(self.driver)
        builder.pointer_action.move_to_location(round(start.x), round(start.y))
        builder.pointer_action.pointer_down(MouseButton.LEFT)
        for fraction in (0.34, 0.67, 1.0):
            builder.pointer_action.move_to_location(
                round(start.x + (end.x - start.x) * fraction),
                round(start.y + (end.y - start.y) * fraction),
            )
        builder.pointer_action.pointer_up(MouseButton.LEFT)
        builder.perform()

    def step(self, direction: str) -> None:
        """One stepper press (``up``/``down``/``left``/``right``) and its effect on the fields."""
        before = self.fields_cm()
        self.wait_and_click(_tid(f"position-{direction}"))
        self.poll().until(lambda _d: self.fields_cm() != before)

    def is_save_enabled(self) -> bool:
        return self.wait_for_element(self.SAVE).is_enabled()

    def save(self, what: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Save and return once the dialog closed - it closes only after the server accepted."""
        button = self.wait_for_element(self.SAVE)
        if not button.is_enabled():
            raise AssertionError(f"{what}: 'Position speichern' is disabled")
        self.click_coordinate_free(button)
        try:
            self.wait_for_element_hidden(self.DIALOG, timeout=timeout)
        except TimeoutException as exc:
            raise AssertionError(f"{what}: the position dialog did not close after saving") from exc

    def close_with_escape(self) -> None:
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        self.wait_for_element_hidden(self.DIALOG)
